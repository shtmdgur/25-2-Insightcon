"""
E2E Full Pipeline Test

KG 구축부터 Debate Workflow까지 전체 파이프라인을 테스트합니다.

Flow:
1. KGConstructionAgent → Neo4j 주입
2. Debate Workflow → 타겟 기업 분석 리포트 생성
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 외부 라이브러리 로그 숨기기
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)


def print_banner(text: str):
    """배너 출력"""
    print("\n" + "=" * 80)
    print(f"🚀 {text}")
    print("=" * 80 + "\n")


def print_section(text: str):
    """섹션 헤더 출력"""
    print("\n" + "-" * 60)
    print(f"📌 {text}")
    print("-" * 60)


def run_e2e_pipeline(
    target_company: str = "삼성전자",
    skip_kg_construction: bool = False,
    test_mode: bool = True
):
    """
    E2E 파이프라인 실행
    
    Args:
        target_company: 분석 대상 기업
        skip_kg_construction: True면 KG 구축 스킵 (이미 Neo4j에 데이터가 있는 경우)
        test_mode: True면 소량 데이터만 처리
    """
    print_banner("E2E Full Pipeline Test")
    print(f"🎯 Target Company: {target_company}")
    print(f"⚙️  Skip KG Construction: {skip_kg_construction}")
    print(f"🧪 Test Mode: {test_mode}")
    
    start_time = datetime.now()
    
    # =============================================
    # Phase 1: KG Construction (선택적)
    # =============================================
    if not skip_kg_construction:
        print_section("Phase 1: Knowledge Graph Construction")
        
        from src.agents.kg_construction import KGConstructionAgent
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config.llm_config import get_model
        
        try:
            llm = ChatGoogleGenerativeAI(model=get_model("news_parsing"))
            
            agent = KGConstructionAgent(
                data_dir=project_root / "data",
                neo4j_uri=os.getenv("NEO4J_URI"),
                llm=llm
            )
            
            # 테스트 모드: 소량 데이터만 처리
            if test_mode:
                from src.config.parser_config import update_config
                update_config('news', sample_size=5)
            
            result = agent.construct_knowledge_graph(
                auto_scan=True,
                use_batch=False,
                load_to_neo4j=True,
                skip_existing=True
            )
            
            print(f"✅ KG Construction 완료")
            print(f"   - Entities: {len(result.get('merged_kg', {}).entities) if result.get('merged_kg') else 0}")
            print(f"   - Relations: {len(result.get('merged_kg', {}).relations) if result.get('merged_kg') else 0}")
            
        except Exception as e:
            logger.error(f"❌ KG Construction 실패: {e}")
            print(f"⚠️  KG Construction 에러 발생, Debate로 계속 진행...")
    else:
        print_section("Phase 1: Skipped (using existing data)")
        
        # Phase 1.5: 기존 JSON → Neo4j 주입 (skip_kg일 때 선택적)
        print_section("Phase 1.5: JSON Merge & Neo4j Injection")
        try:
            from src.dataflows.kg_merger import KGMerger
            from src.dataflows.neo4j_loader import Neo4jKGLoader
            from src.models.nodes import KnowledgeGraph
            from pathlib import Path
            
            processed_dir = project_root / "data" / "processed"
            json_files = list(processed_dir.glob("**/*_kg.json"))  # 하위 폴더까지 검색
            
            if json_files:
                print(f"📂 {len(json_files)} JSON 파일 발견")
                
                # 머지
                merger = KGMerger()
                kgs = []
                for jf in json_files:
                    try:
                        kg = KnowledgeGraph.load_from_json(str(jf))
                        kgs.append(kg)
                    except Exception as e:
                        logger.warning(f"Failed to load {jf.name}: {e}")
                
                if kgs:
                    merged_kg = merger.merge_knowledge_graphs(kgs)
                    print(f"   - Merged: {len(merged_kg.entities)} entities, {len(merged_kg.relations)} relations")
                    
                    # Neo4j 주입
                    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
                    
                    loader = Neo4jKGLoader(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
                    stats = loader.load_knowledge_graph(merged_kg)
                    loader.close()
                    
                    print(f"✅ Neo4j 주입 완료: {stats.get('static_nodes', 0)} static, {stats.get('dynamic_nodes', 0)} dynamic nodes")
                    
                    # Phase 1.6: Neo4j Quality Check
                    print_section("Phase 1.6: Neo4j Quality Check")
                    try:
                        import sys
                        sys.path.insert(0, str(project_root / "scripts"))
                        from neo4j_quality_check import Neo4jQualityChecker
                        
                        checker = Neo4jQualityChecker(neo4j_uri, neo4j_user, neo4j_password)
                        qc_results = checker.run_all_checks()
                        checker.close()
                        
                        if qc_results.get("issues"):
                            print(f"⚠️  {len(qc_results['issues'])}개 품질 이슈 발견, Debate 계속 진행...")
                        else:
                            print("✅ 데이터 품질 양호")
                    except Exception as qc_e:
                        print(f"⚠️  Quality Check 스킵: {qc_e}")
            else:
                print("⚠️  data/processed에 JSON 파일이 없습니다.")
                
        except Exception as e:
            logger.error(f"❌ JSON 주입 실패: {e}")
            print(f"⚠️  JSON 주입 에러: {e}")
    
    # =============================================
    # Phase 2: Debate Workflow
    # =============================================
    print_section("Phase 2: Debate Workflow")
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config.llm_config import get_model
        from src.agents.bull_agent import BullAgent
        from src.agents.bear_agent import BearAgent
        from src.agents.judge_agent import JudgeAgent
        from src.agents.synthesizer_agent import SynthesizerAgent
        from src.pipeline.debate_workflow import create_debate_workflow
        from src.dataflows.neo4j_loader import Neo4jKGLoader
        
        # LLM 초기화
        llm = ChatGoogleGenerativeAI(
            model=get_model("debate"),
            temperature=0.7
        )
        
        # Neo4j 연결 (Debate Agent가 Impact Paths 쿼리에 사용)
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        neo4j_conn = None
        try:
            neo4j_conn = Neo4jKGLoader(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password
            )
            print(f"✅ Neo4j 연결 성공")
        except Exception as e:
            print(f"⚠️  Neo4j 연결 실패 ({e}), Debate는 캐시 데이터 없이 진행")
        
        # Debate Agents 초기화
        bull = BullAgent(llm=llm, neo4j_connection=neo4j_conn)
        bear = BearAgent(llm=llm, neo4j_connection=neo4j_conn)
        judge = JudgeAgent(llm=llm)
        synthesizer = SynthesizerAgent(llm=llm)
        
        # Workflow 생성
        workflow = create_debate_workflow(
            bull_agent=bull,
            bear_agent=bear,
            synthesizer_agent=synthesizer,
            judge_agent=judge
        )
        
        # 초기 상태 준비
        from src.pipeline.state import ReportState, DebateState
        
        initial_state: ReportState = {
            "query": target_company,
            "ticker": None,  # 필요시 ticker 매핑
            "target_companies": [target_company],
            "report_type": "deep",
            "target_date": datetime.now().strftime("%Y-%m-%d"),
            "document": None,
            "impact_paths": None,  # Debate Agent가 동적으로 조회
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
            "debate_state": {
                "bull_history": "",
                "bear_history": "",
                "full_history": "",
                "current_bull_arg": None,
                "current_bear_arg": None,
                "debate_count": 0,
                "should_continue": True,
                "cached_paths": {},
                "debate_trace": [],
                "judge_result": None,
                "validation_result": None
            },
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
        
        print(f"🎭 Debate 시작: {target_company}")
        
        # Workflow 실행
        final_state = workflow.invoke(initial_state)
        
        print(f"✅ Debate 완료")
        print(f"   - Rounds: {final_state['debate_state']['debate_count']}")
        
        # 결과 저장
        output_dir = project_root / "data" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / f"e2e_report_{target_company}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        
        if final_state.get("final_report"):
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(final_state["final_report"])
            print(f"📄 Markdown Report saved: {report_path}")
            
            # PDF 변환 시도
            try:
                from src.utils.report_exporter import ReportExporter
                exporter = ReportExporter(output_dir=str(output_dir))
                pdf_filename = f"e2e_report_{target_company}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                pdf_path = exporter.export_to_pdf(
                    final_state["final_report"], 
                    pdf_filename,
                    f"{target_company} Investment Analysis"
                )
                if pdf_path:
                    print(f"📕 PDF Report saved: {pdf_path}")
            except Exception as pdf_e:
                print(f"⚠️  PDF 변환 실패: {pdf_e}")
        else:
            print("⚠️  Final report가 생성되지 않았습니다.")
        
        # Neo4j 연결 종료
        if neo4j_conn:
            neo4j_conn.close()
            
    except Exception as e:
        logger.error(f"❌ Debate Workflow 실패: {e}", exc_info=True)
        print(f"❌ Debate Workflow 에러: {e}")
        return None
    
    # =============================================
    # 완료
    # =============================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_banner("E2E Pipeline Complete ✅")
    print(f"⏱️  Total Duration: {duration:.2f}초")
    print(f"📄 Report: {report_path if final_state.get('final_report') else 'N/A'}")
    
    return final_state


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="E2E Full Pipeline Test")
    parser.add_argument("--target", default="삼성전자", help="분석 대상 기업")
    parser.add_argument("--skip-kg", action="store_true", help="KG 구축 스킵")
    parser.add_argument("--full", action="store_true", help="전체 데이터 처리 (테스트 모드 해제)")
    
    args = parser.parse_args()
    
    run_e2e_pipeline(
        target_company=args.target,
        skip_kg_construction=args.skip_kg,
        test_mode=not args.full
    )
