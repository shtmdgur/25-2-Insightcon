"""
변증법 토론 워크플로우 (LangGraph 기반)
"""
from typing import Dict, Any, Literal, List, Optional
from langgraph.graph import StateGraph, END
from src.pipeline.state import ReportState, DebateState
from src.agents.bull_agent import BullAgent
from src.agents.bear_agent import BearAgent
from src.agents.judge_agent import JudgeAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.agents.validator_agent import ValidatorAgent


def create_debate_workflow(
    bull_agent: BullAgent, 
    bear_agent: BearAgent, 
    synthesizer_agent: SynthesizerAgent,
    judge_agent: JudgeAgent = None,
    validator_agent: ValidatorAgent = None
):
    """
    변증법 토론 워크플로우 생성 (v3.1)
    
    구조: initialize -> bull -> bear -> (loop x3) -> judge -> synthesizer -> validator -> END
    """
    
    workflow = StateGraph(ReportState)
    
    # 노드 추가
    workflow.add_node("initialize", initialize_debate)
    workflow.add_node("bull", lambda state: bull_node(state, bull_agent))
    workflow.add_node("bear", lambda state: bear_node(state, bear_agent))
    
    if judge_agent:
        workflow.add_node("judge", lambda state: judge_node(state, judge_agent))
    
    workflow.add_node("synthesizer", lambda state: synthesizer_node(state, synthesizer_agent))
    
    if validator_agent:
        workflow.add_node("validator", lambda state: validator_node(state, validator_agent))

    # 에지 정의
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "bull")
    workflow.add_edge("bull", "bear")
    
    # 루프 조건 (3라운드까지)
    def should_continue(state: ReportState):
        count = state["debate_state"]["debate_count"]
        if count >= 3:
            return "judge" if judge_agent else "synthesizer"
        return "bull"
    
    workflow.add_conditional_edges("bear", should_continue, {
        "bull": "bull",
        "judge": "judge" if judge_agent else "synthesizer",
        "synthesizer": "synthesizer"
    })
    
    if judge_agent:
        workflow.add_edge("judge", "synthesizer")
        
    if validator_agent:
        workflow.add_edge("synthesizer", "validator")
        workflow.add_edge("validator", END)
    else:
        workflow.add_edge("synthesizer", END)
    
    return workflow.compile()


# ============================================================
# Node Functions (v3.1)
# ============================================================

def initialize_debate(state: ReportState) -> ReportState:
    """토론 상태 초기화, 자연어 쿼리 파싱, Document 처리"""
    from datetime import datetime
    from pathlib import Path
    from src.utils.query_intent_parser import QueryIntentParser
    
    # 0. Document 내용 로드 (파일 경로인 경우)
    query = state.get("query", "")
    document = state.get("document")
    document_content = None
    
    if document:
        doc_path = Path(document)
        if doc_path.exists() and doc_path.is_file():
            try:
                # 텍스트 파일 읽기
                if doc_path.suffix in ['.txt', '.md', '.csv']:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        document_content = f.read()
                    print(f"📄 문서 로드 완료: {doc_path.name} ({len(document_content)} chars)")
                # PDF는 별도 파서 필요 (여기서는 경로만 표시)
                elif doc_path.suffix == '.pdf':
                    print(f"📄 PDF 문서: {doc_path.name} (Gemini PDF 파서 필요)")
                    document_content = f"[PDF 문서: {doc_path.name}]"
            except Exception as e:
                print(f"⚠️ 문서 로드 실패: {e}")
        else:
            # document가 텍스트 내용 자체일 수 있음
            if len(document) > 50:  # 최소 50자 이상이면 텍스트로 간주
                document_content = document
    
    # 1. 자연어 쿼리 파싱 (기업명, 날짜, 의도 추출)
    if query and not state.get("target_companies"):
        parser = QueryIntentParser()
        intent = parser.parse(query, document)
        
        # 파싱 결과로 state 업데이트 (없는 경우만)
        if intent["target_companies"] and not state.get("target_companies"):
            state["target_companies"] = intent["target_companies"]
            print(f"🏢 분석 대상 추출: {intent['target_companies']}")
        
        if intent["target_date"] and not state.get("target_date"):
            state["target_date"] = intent["target_date"]
        
        print(f"💡 쿼리 의도: {intent['intent']}")
    
    # 2. Document 요약 (LLM 사용, document_content가 있는 경우)
    if document_content and len(document_content) > 100:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from src.config.llm_config import get_model
            
            llm = ChatGoogleGenerativeAI(model=get_model("debate"), temperature=0.3)
            parser = QueryIntentParser(llm)
            doc_analysis = parser.parse_document(document_content)
            
            if doc_analysis and not doc_analysis.get("error"):
                print(f"📋 문서 분석 완료: {doc_analysis.get('main_topic', 'N/A')}")
                # Document 요약을 state에 저장 (Debate에서 활용)
                state["document_summary"] = doc_analysis
        except Exception as e:
            print(f"⚠️ 문서 분석 스킵: {e}")
    
    # 3. target_date 기본값 설정
    if not state.get("target_date"):
        state["target_date"] = datetime.now().strftime("%Y-%m-%d")
        print(f"📅 분석 기준일 자동 설정: {state['target_date']}")
    else:
        print(f"📅 분석 기준일: {state['target_date']}")
    
    # 4. Debate 상태 초기화
    debate_state: DebateState = {
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
    }
    
    state["debate_state"] = debate_state
    return state


def bull_node(state: ReportState, agent: BullAgent) -> Dict:
    """Bull Agent 주장 생성 노드"""
    opponent_arg = state["debate_state"].get("current_bear_arg")
    round_num = state["debate_state"]["debate_count"] + 1
    
    print(f"\n{'='*80}\n🔴 ROUND {round_num} - Bull Agent 주장 생성 중...\n{'='*80}")
    
    result = agent.argue(state, opponent_last_arg=opponent_arg)
    
    # 실시간 토론 내용 출력 (10줄 미리보기)
    argument = result["argument"]
    lines = argument.split('\n')
    preview_lines = lines[:]
    print("\n🔴 [Bull 주장]")
    print("-" * 40)
    for line in preview_lines:
        print(line)
    print("-" * 40)
    
    # State 업데이트
    debate_state = state["debate_state"]
    debate_state["current_bull_arg"] = result["argument"]
    debate_state["bull_history"] += f"\n\n## Round {round_num} - Bull\n{result['argument']}"
    debate_state["full_history"] += f"\n\n[Round {round_num} - Bull]\n{result['argument']}"
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Bull Round {round_num} 완료")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


def bear_node(state: ReportState, agent: BearAgent) -> Dict:
    """Bear Agent 주장 생성 노드"""
    opponent_arg = state["debate_state"].get("current_bull_arg")
    round_num = state["debate_state"]["debate_count"] + 1
    
    print(f"\n{'='*80}\n🔵 ROUND {round_num} - Bear Agent 주장 생성 중...\n{'='*80}")
    
    result = agent.argue(state, opponent_last_arg=opponent_arg)
    
    # 실시간 토론 내용 출력 (10줄 미리보기)
    argument = result["argument"]
    lines = argument.split('\n')
    preview_lines = lines[:]
    print("\n🔵 [Bear 주장]")
    print("-" * 40)
    for line in preview_lines:
        print(line)
    print("-" * 40)
    
    # State 업데이트
    debate_state = state["debate_state"]
    debate_state["current_bear_arg"] = result["argument"]
    debate_state["bear_history"] += f"\n\n## Round {round_num} - Bear\n{result['argument']}"
    debate_state["full_history"] += f"\n\n[Round {round_num} - Bear]\n{result['argument']}"
    
    # 라운드 증가
    debate_state["debate_count"] += 1
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Bear Round {debate_state['debate_count']} 완료")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


def judge_node(state: ReportState, agent: JudgeAgent) -> Dict:
    """토론 결과를 판결하는 노드"""
    print(f"\n{'='*80}\n⚖️  Judge - Rendering Verdict...\n{'='*80}")
    
    result = agent.judge(state)
    
    # 실시간 판결 결과 출력
    print("\n📢 [Judge 판결 결과]")
    print("-" * 40)
    print(f"   Decision: {result.get('decision', 'N/A')}")
    print(f"   Score: {result.get('score', 'N/A')}/100")
    print(f"   Confidence: {result.get('confidence_level', 'N/A')}")
    print(f"   Winning Side: {result.get('winning_side', 'N/A')}")
    rationale = result.get('rationale', '')
    if rationale:
        print(f"   Rationale: {rationale[:150]}..." if len(rationale) > 150 else f"   Rationale: {rationale}")
    print("-" * 40)
    
    debate_state = state["debate_state"]
    debate_state["judge_result"] = result
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Judge: Rated {result.get('decision')} (Score: {result.get('score')})")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


def synthesizer_node(state: ReportState, agent: SynthesizerAgent) -> Dict:
    """최종 리포트를 합성하는 노드"""
    print(f"\n{'='*80}\n🧠 Synthesizer - 최종 리포트 생성 중...\n{'='*80}")
    
    final_report = agent.synthesize(state)
    
    debate_state = state["debate_state"]
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append("Synthesizer 리포트 완료")
    debate_state["debate_trace"] = debate_trace
    
    return {
        "debate_state": debate_state,
        "synthesis_report": final_report,
        "final_report": final_report
    }


def validator_node(state: ReportState, agent: ValidatorAgent) -> Dict:
    """리포트 품질을 검수하는 노드"""
    print(f"\n{'='*80}\n🔍 Validator - Quality Control...\n{'='*80}")
    
    result = agent.validate(state)
    
    debate_state = state["debate_state"]
    debate_state["validation_result"] = result
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Validator: {result.get('decision', 'fail')}")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


# ========================================
# 헬퍼 함수 (확장 가능)
# ========================================

def update_cached_paths(state: ReportState, round_num: int, paths: list) -> ReportState:
    """
    Progressive Path Expansion: 캐시 업데이트
    
    Note: 현재는 Agent 내부에서 처리하지만, 
    향후 Workflow 레벨로 이동 가능
    """
    if "debate_state" not in state:
        state["debate_state"] = {}
    
    if "cached_paths" not in state["debate_state"]:
        state["debate_state"]["cached_paths"] = {}
    
    state["debate_state"]["cached_paths"][round_num] = paths
    return state


def create_debate_workflow_for_studio():
    """
    LangGraph Studio/CLI용 워크플로우 생성
    
    langgraph.json에서 이 함수를 진입점으로 사용합니다.
    환경변수에서 Neo4j, LLM 설정을 자동으로 로드합니다.
    
    Returns:
        CompiledStateGraph: 컴파일된 Debate 워크플로우
    """
    import os
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI
    from src.dataflows.neo4j_loader import Neo4jKGLoader
    from src.config.llm_config import get_model
    
    load_dotenv()
    
    # LLM 초기화
    llm = ChatGoogleGenerativeAI(
        model=get_model("debate"),
        temperature=0.7
    )
    
    # Neo4j 연결 (옵션)
    neo4j_conn = None
    try:
        neo4j_uri = os.getenv("NEO4J_URI")
        neo4j_user = os.getenv("NEO4J_USER", os.getenv("NEO4J_USERNAME", "neo4j"))
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if neo4j_uri and neo4j_password:
            neo4j_conn = Neo4jKGLoader(
                uri=neo4j_uri,
                user=neo4j_user,
                password=neo4j_password
            )
    except Exception as e:
        print(f"[경고] Neo4j 연결 실패: {e}")
    
    # Agent 초기화
    bull = BullAgent(llm, neo4j_conn)
    bear = BearAgent(llm, neo4j_conn)
    judge = JudgeAgent(llm, neo4j_conn)
    synthesizer = SynthesizerAgent(llm, neo4j_conn)
    
    # 워크플로우 생성 및 반환
    return create_debate_workflow(
        bull_agent=bull,
        bear_agent=bear,
        judge_agent=judge,
        synthesizer_agent=synthesizer,
        validator_agent=None
    )

