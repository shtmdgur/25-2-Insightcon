"""
Pipeline Service Layer

Streamlit/FastAPI에서 호출 가능한 서비스 클래스.
사용자 인터랙션 checkpoint를 지원하여 단계별 실행 가능.

사용 예시:
    # Streamlit에서
    service = PipelineService()
    
    # Step 1: 모드 선택
    mode = st.selectbox("모드 선택", ["full", "query_only", "document_query"])
    
    # Step 2: 설정 및 실행
    config = service.create_config(mode=mode, target_company="삼성전자")
    
    # Step 3: 실행 (checkpoint 콜백으로 중간 결과 수신)
    result = service.run(config, on_checkpoint=my_callback)
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class PipelineMode(str, Enum):
    """파이프라인 실행 모드"""
    FULL = "full"                    # KG 구축 + Debate
    QUERY_ONLY = "query_only"        # 기존 KG로 Debate만
    DOCUMENT_QUERY = "document_query"  # 새 문서 + 기존 KG + Debate


class CheckpointType(str, Enum):
    """사용자 인터랙션 checkpoint 타입"""
    MODE_SELECTION = "mode_selection"        # 모드 선택
    TARGET_SELECTION = "target_selection"    # 타겟 기업 선택
    KG_COMPLETE = "kg_complete"              # KG 구축 완료
    DEBATE_ROUND = "debate_round"            # 각 토론 라운드 종료
    JUDGE_RESULT = "judge_result"            # 판결 결과
    FINAL_REPORT = "final_report"            # 최종 리포트


@dataclass
class PipelineConfig:
    """파이프라인 실행 설정"""
    mode: PipelineMode = PipelineMode.QUERY_ONLY
    target_company: str = "삼성전자"
    ticker: Optional[str] = None
    target_date: Optional[str] = None
    document_path: Optional[str] = None  # DOCUMENT_QUERY 모드에서 사용
    
    # KG 구축 옵션
    skip_existing: bool = True
    test_mode: bool = True
    
    # Debate 옵션
    max_debate_rounds: int = 3
    
    # 출력 옵션
    output_dir: str = "data/outputs"
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON 직렬화용 딕셔너리 변환"""
        result = asdict(self)
        result['mode'] = self.mode.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """딕셔너리에서 복원"""
        data['mode'] = PipelineMode(data.get('mode', 'query_only'))
        return cls(**data)


@dataclass
class CheckpointData:
    """Checkpoint에서 전달되는 데이터"""
    checkpoint_type: CheckpointType
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    requires_input: bool = False  # 사용자 입력이 필요한지
    options: Optional[List[str]] = None  # 선택지 (requires_input=True일 때)


@dataclass 
class PipelineResult:
    """파이프라인 실행 결과"""
    success: bool
    mode: PipelineMode
    target_company: str
    
    # 단계별 결과
    kg_stats: Optional[Dict[str, int]] = None
    debate_rounds: int = 0
    judge_decision: Optional[str] = None
    judge_score: Optional[int] = None
    
    # 최종 출력
    final_report_path: Optional[str] = None
    final_report_content: Optional[str] = None
    
    # 실행 정보
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['mode'] = self.mode.value
        return result


# Checkpoint 콜백 타입
CheckpointCallback = Callable[[CheckpointData], Optional[Any]]


class PipelineService:
    """
    멀티에이전트 파이프라인 서비스
    
    Streamlit/FastAPI에서 사용 가능한 인터페이스 제공.
    """
    
    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        data_dir: Optional[Path] = None
    ):
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        self.data_dir = data_dir or Path("data")
        
        self._neo4j_conn = None
        self._llm = None
    
    def create_config(
        self,
        mode: str = "query_only",
        target_company: str = "삼성전자",
        **kwargs
    ) -> PipelineConfig:
        """설정 객체 생성"""
        return PipelineConfig(
            mode=PipelineMode(mode),
            target_company=target_company,
            target_date=kwargs.get('target_date', datetime.now().strftime("%Y-%m-%d")),
            **{k: v for k, v in kwargs.items() if k != 'target_date'}
        )
    
    def run(
        self,
        config: PipelineConfig,
        on_checkpoint: Optional[CheckpointCallback] = None
    ) -> PipelineResult:
        """
        파이프라인 실행
        
        Args:
            config: 실행 설정
            on_checkpoint: checkpoint 콜백 (Streamlit/FastAPI에서 중간 결과 처리)
        
        Returns:
            PipelineResult: 실행 결과
        """
        start_time = datetime.now()
        errors = []
        
        # 기본 콜백 (로깅)
        if on_checkpoint is None:
            on_checkpoint = self._default_checkpoint_handler
        
        try:
            # 1. 초기화
            self._initialize()
            
            # 2. 모드별 실행
            if config.mode == PipelineMode.FULL:
                kg_stats = self._run_kg_construction(config, on_checkpoint)
                debate_result = self._run_debate(config, on_checkpoint)
            
            elif config.mode == PipelineMode.QUERY_ONLY:
                kg_stats = None
                debate_result = self._run_debate(config, on_checkpoint)
            
            elif config.mode == PipelineMode.DOCUMENT_QUERY:
                kg_stats = self._run_document_parsing(config, on_checkpoint)
                debate_result = self._run_debate(config, on_checkpoint)
            
            else:
                raise ValueError(f"Unknown mode: {config.mode}")
            
            # 3. 결과 저장
            report_path = self._save_report(config, debate_result)
            
            # 4. 최종 checkpoint
            on_checkpoint(CheckpointData(
                checkpoint_type=CheckpointType.FINAL_REPORT,
                message="최종 리포트가 생성되었습니다.",
                data={"path": report_path}
            ))
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return PipelineResult(
                success=True,
                mode=config.mode,
                target_company=config.target_company,
                kg_stats=kg_stats,
                debate_rounds=debate_result.get("rounds", 0),
                judge_decision=debate_result.get("decision"),
                judge_score=debate_result.get("score"),
                final_report_path=report_path,
                final_report_content=debate_result.get("report"),
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            errors.append(str(e))
            
            return PipelineResult(
                success=False,
                mode=config.mode,
                target_company=config.target_company,
                errors=errors,
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )
        
        finally:
            self._cleanup()
    
    def _initialize(self):
        """리소스 초기화"""
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config.llm_config import get_model
        from src.dataflows.neo4j_loader import Neo4jKGLoader
        
        # LLM 초기화 (Task에 맞는 모델 사용)
        self._llm = ChatGoogleGenerativeAI(
            model=get_model("bull_argument"), # 토론용 고성능 모델
            temperature=0.2
        )
        
        # Neo4j 연결
        try:
            self._neo4j_conn = Neo4jKGLoader(
                uri=self.neo4j_uri,
                user=self.neo4j_user,
                password=self.neo4j_password
            )
        except Exception as e:
            logger.warning(f"Neo4j 연결 실패: {e}")
            self._neo4j_conn = None
    
    def _cleanup(self):
        """리소스 정리"""
        if self._neo4j_conn:
            try:
                self._neo4j_conn.close()
            except:
                pass
    
    def _run_kg_construction(
        self,
        config: PipelineConfig,
        on_checkpoint: CheckpointCallback
    ) -> Dict[str, int]:
        """KG 구축 실행"""
        from src.agents.kg_construction import KGConstructionAgent
        
        if config.test_mode:
            from src.config.parser_config import update_config
            update_config('news', sample_size=5)
        
        agent = KGConstructionAgent(
            data_dir=self.data_dir,
            neo4j_uri=self.neo4j_uri,
            llm=self._llm
        )
        
        result = agent.construct_knowledge_graph(
            auto_scan=True,
            use_batch=False,
            load_to_neo4j=True,
            skip_existing=config.skip_existing
        )
        
        merged_kg = result.get('merged_kg')
        stats = {
            "entities": len(merged_kg.entities) if merged_kg else 0,
            "relations": len(merged_kg.relations) if merged_kg else 0
        }
        
        # Checkpoint 발행
        on_checkpoint(CheckpointData(
            checkpoint_type=CheckpointType.KG_COMPLETE,
            message=f"KG 구축 완료: {stats['entities']} entities, {stats['relations']} relations",
            data=stats
        ))
        
        return stats
    
    def _run_document_parsing(
        self,
        config: PipelineConfig,
        on_checkpoint: CheckpointCallback
    ) -> Dict[str, int]:
        """단일 문서 파싱 및 KG 추가"""
        if not config.document_path:
            return {"entities": 0, "relations": 0}
        
        from src.agents.parsers.gemini_pdf_parser import GeminiPDFParser
        from src.config.llm_config import get_model
        
        parser = GeminiPDFParser(model_name=get_model("pdf_parsing"))
        result = parser.parse(config.document_path)
        
        kg = result.get("knowledge_graph")
        if kg and self._neo4j_conn:
            self._neo4j_conn.load_knowledge_graph(kg)
        
        stats = {
            "entities": len(kg.entities) if kg else 0,
            "relations": len(kg.relations) if kg else 0
        }
        
        on_checkpoint(CheckpointData(
            checkpoint_type=CheckpointType.KG_COMPLETE,
            message=f"문서 파싱 완료: {config.document_path}",
            data=stats
        ))
        
        return stats
    
    def _run_debate(
        self,
        config: PipelineConfig,
        on_checkpoint: CheckpointCallback
    ) -> Dict[str, Any]:
        """Debate 워크플로우 실행 (Streaming 지원)"""
        from src.pipeline.debate_workflow import create_debate_workflow_for_studio
        
        # 스튜디오 용 팩토리 함수를 사용하여 모든 에이전트 도구 연동 보장
        workflow = create_debate_workflow_for_studio()
        
        # 초기 상태 생성
        initial_state = self._create_initial_state(config)
        
        # 결과 저장을 위한 변수들
        final_state = initial_state
        judge_result = None
        
        # 스트리밍 실행으로 사용자 인터랙션 지원
        for event in workflow.stream(initial_state, stream_mode="updates"):
            for node_name, output in event.items():
                final_state.update(output)
                
                # 노드별 체크포인트 발행
                message = f"에이전트 실행 중: {node_name}"
                cp_type = CheckpointType.DEBATE_ROUND
                
                if node_name == "judge":
                    judge_result = output.get("debate_state", {}).get("judge_result")
                    cp_type = CheckpointType.JUDGE_RESULT
                    message = f"판결 완료: {judge_result.get('decision') if judge_result else 'N/A'}"
                elif node_name == "synthesizer":
                    cp_type = CheckpointType.FINAL_REPORT
                    message = "리포트 생성 완료"
                
                on_checkpoint(CheckpointData(
                    checkpoint_type=cp_type,
                    message=message,
                    data={"node": node_name, "output": output}
                ))
        
        debate_state = final_state.get("debate_state", {})
        judge_result = judge_result or debate_state.get("judge_result", {})
        
        return {
            "rounds": debate_state.get("debate_count", 0),
            "decision": judge_result.get("decision"),
            "score": judge_result.get("score"),
            "report": final_state.get("final_report")
        }
    
    def _create_initial_state(self, config: PipelineConfig) -> Dict:
        """ReportState 초기화"""
            "query": config.target_company,
            "ticker": config.ticker,
            "target_companies": [config.target_company],
            "target_date": config.target_date,
            "document": config.document_path,
            "document_summary": None,  # [NEW] 문서 요약 정보
            "impact_paths": None,
            "parsed_text": None,
            "file_uri": None,
            "extracted_charts": None,
            "ontology_schema": None,
            "schema_issues": None,
            "kg_data": None,
            "kg_updates": [],
            "graphrag_results": None,
            "news_events": None,
            "fundamental_analysis": None,
            "trend_analysis": None,
            "event_analysis": None,
            "analyst_reports": None,
            "debate_state": None,  # initialize_debate 노드에서 생성하도록 None 설정
            "synthesis_report": None,
            "sector_analysis": None,
            "company_analysis": None,
            "final_report": None,
            "retry_count": 0,
            "critical_paths": None,
            "errors": [],
            "execution_trace": [],
            "execution_times": []
        }
    
    def _save_report(self, config: PipelineConfig, debate_result: Dict) -> Optional[str]:
        """리포트 저장"""
        report = debate_result.get("report")
        if not report:
            return None
        
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"report_{config.target_company}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        path = output_dir / filename
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        
        return str(path)
    
    def _default_checkpoint_handler(self, checkpoint: CheckpointData) -> None:
        """기본 checkpoint 핸들러 (로깅)"""
        logger.info(f"[{checkpoint.checkpoint_type.value}] {checkpoint.message}")
    
    # ==========================================
    # 상태 직렬화/복원 (중단된 작업 재개용)
    # ==========================================
    
    def save_state(self, config: PipelineConfig, state: Dict, path: str):
        """현재 상태 저장 (JSON)"""
        data = {
            "config": config.to_dict(),
            "state": state,
            "saved_at": datetime.now().isoformat()
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def load_state(self, path: str) -> tuple[PipelineConfig, Dict]:
        """저장된 상태 복원"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        config = PipelineConfig.from_dict(data["config"])
        state = data["state"]
        
        return config, state


# ==========================================
# 사용 예시 (Streamlit용)
# ==========================================

def example_streamlit_usage():
    """Streamlit 연동 예시 코드"""
    # import streamlit as st
    
    service = PipelineService()
    
    # UI에서 모드 선택
    # mode = st.selectbox("분석 모드", ["query_only", "full", "document_query"])
    # target = st.text_input("분석 대상 기업", "삼성전자")
    
    mode = "query_only"
    target = "삼성전자"
    
    config = service.create_config(
        mode=mode,
        target_company=target,
        test_mode=True
    )
    
    # Checkpoint 콜백 (Streamlit에 중간 결과 표시)
    def on_checkpoint(cp: CheckpointData):
        print(f"[{cp.checkpoint_type.value}] {cp.message}")
        # st.info(cp.message)
        # if cp.data:
        #     st.json(cp.data)
    
    # 실행
    result = service.run(config, on_checkpoint=on_checkpoint)
    
    if result.success:
        print(f"✅ 완료: {result.judge_decision}")
        # st.success(f"분석 완료: {result.judge_decision}")
        # st.markdown(result.final_report_content)
    else:
        print(f"❌ 실패: {result.errors}")
        # st.error(f"오류 발생: {result.errors}")


if __name__ == "__main__":
    example_streamlit_usage()
