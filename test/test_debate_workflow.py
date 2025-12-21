"""
Debate Workflow 통합 테스트

Neo4j 연결 및 실제 데이터로 토론 워크플로우 테스트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 PYTHONPATH에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
import warnings
import re
import os

# LangChain 디버그/Tracing 완전 비활성화 (signature 출력 방지)
os.environ["LANGCHAIN_VERBOSE"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_CALLBACKS_MANAGER"] = "false"

# 전역 로깅 레벨 설정
logging.basicConfig(level=logging.WARNING)

# 불필요한 로그 억제
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*google-cloud-storage.*')
logging.getLogger('neo4j.notifications').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('google_genai').setLevel(logging.WARNING)
logging.getLogger('langchain_core').setLevel(logging.WARNING)
logging.getLogger('langchain_google_genai').setLevel(logging.WARNING)
logging.getLogger('langchain').setLevel(logging.WARNING)
# 모든 루트 로거의 레벨을 WARNING으로 설정
logging.getLogger().setLevel(logging.WARNING)

from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core import globals as langchain_globals

# LangChain 디버그 모드 완전 비활성화
langchain_globals.set_debug(False)
langchain_globals.set_verbose(False)

from src.pipeline.debate_workflow import create_debate_workflow
from src.agents.bull_agent import BullAgent
from src.agents.bear_agent import BearAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.pipeline.state import ReportState


# ============================================================
# Helper Functions
# ============================================================

def extract_round(history: str, round_num: int, side: str) -> str:
    """특정 라운드의 내용만 추출"""
    pattern = rf"## Round {round_num} - {side}(.*?)(?=## Round \d+ -|$)"
    match = re.search(pattern, history, re.DOTALL)
    return match.group(1).strip() if match else None


def print_debate_by_rounds(bull_history: str, bear_history: str, rounds: int = 3):
    """라운드별로 Bull과 Bear 주장을 교차 출력"""
    for i in range(1, rounds + 1):
        print(f"\n{'='*80}")
        print(f"🔴 ROUND {i} - Bull Argument")
        print('='*80)
        
        bull_section = extract_round(bull_history, i, "Bull")
        if bull_section:
            # 긴 내용은 400자로 제한
            if len(bull_section) > 400:
                print(bull_section[:400] + "...")
            else:
                print(bull_section)
        else:
            print(f"[Round {i} Bull 내용 없음]")
        
        print(f"\n{'='*80}")
        print(f"🔵 ROUND {i} - Bear Argument")
        print('='*80)
        
        bear_section = extract_round(bear_history, i, "Bear")
        if bear_section:
            # 긴 내용은 400자로 제한
            if len(bear_section) > 400:
                print(bear_section[:400] + "...")
            else:
                print(bear_section)
        else:
            print(f"[Round {i} Bear 내용 없음]")


# 환경 변수 로드
load_dotenv()

# ========================================
# 설정
# ========================================

# Neo4j 연결
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Gemini LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ========================================
# Neo4j 연결 클래스 (간단한 래퍼)
# ========================================

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()


# ========================================
# Mock GraphRAG 결과 생성
# ========================================

def create_mock_graphrag_results():
    """Neo4j에서 실제로 조회한 것처럼 보이는 Mock 데이터"""
    return {
        "subgraph": {
            "nodes": [
                {"type": "Event", "name": "HBM 증산", "description": "2024 하반기 HBM 생산 증설"},
                {"type": "Event", "name": "AI 붐", "description": "생성형 AI 시장 급성장"},
                {"type": "Trend", "name": "반도체 수요 증가", "description": "AI 칩 수요 폭발"},
                {"type": "Metric", "name": "영업이익률", "properties": {"value": 10.5}},
                {"type": "Metric", "name": "매출액", "properties": {"value": 50000}},
            ],
            "edges": []
        },
        "text_context": "삼성전자는 HBM 생산을 증설하고 있으며..."
    }


# ========================================
# 메인 테스트
# ========================================

def main():
    print("=" * 60)
    print("Debate Workflow 통합 테스트 시작")
    print("=" * 60)
    
    # 1. Neo4j 연결
    print("\n[1] Neo4j 연결 중...")
    neo4j_conn = Neo4jConnection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    print("✅ Neo4j 연결 성공")
    
    # 2. LLM 초기화
    print("\n[2] Gemini LLM 초기화...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        google_api_key=GEMINI_API_KEY,
        temperature=0.0,
        verbose=False  # 디버그 출력 억제
    )
    print("✅ LLM 초기화 완료")
    
    # 3. Agent 초기화
    print("\n[3] Debate Agents 초기화...")
    bull = BullAgent(llm=llm, neo4j_connection=neo4j_conn)
    bear = BearAgent(llm=llm, neo4j_connection=neo4j_conn)
    synthesizer = SynthesizerAgent(llm=llm, neo4j_connection=neo4j_conn)
    print("✅ Agents 초기화 완료")
    
    # 4. Workflow 생성
    print("\n[4] Debate Workflow 컴파일...")
    workflow = create_debate_workflow(bull, bear, synthesizer)
    print("✅ Workflow 컴파일 완료")
    
    # 5. 초기 State 생성
    print("\n[5] 초기 State 준비...")
    initial_state: ReportState = {
        "query": "삼성전자 투자 판단",
        "target_companies": ["삼성전자"],
        "report_type": "deep",
        "document": None,
        
        # GraphRAG 결과 (Mock)
        "graphrag_results": create_mock_graphrag_results(),
        
        # 필수 초기값
        "parsed_text": None,
        "file_uri": None,
        "extracted_charts": None,
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "kg_updates": [],
        "news_events": None,
        "fundamental_analysis": None,
        "trend_analysis": None,
        "event_analysis": None,
        "analyst_reports": None,
        "debate_state": None,  # Workflow에서 초기화
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
    print("✅ State 준비 완료")
    
    # 6. Workflow 실행
    print("\n[6] Debate Workflow 실행 시작...")
    print("-" * 60)
    
    try:
        final_state = workflow.invoke(initial_state)
        
        print("\n" + "=" * 60)
        print("✅ Workflow 실행 완료!")
        print("=" * 60)
        
        # 7. 결과 출력
        print("\n" + "="*80)
        print("📊 토론 결과 요약")
        print("="*80)
        print(f"총 라운드: {final_state['debate_state']['debate_count']}")
        
        # 실행 추적
        debate_trace = final_state["debate_state"].get("debate_trace", [])
        if debate_trace:
            print(f"\nDebate 실행 추적:")
            for trace in debate_trace:
                print(f"  ✓ {trace}")
        
        # 라운드별 토론 출력
        print_debate_by_rounds(
            final_state["debate_state"]["bull_history"],
            final_state["debate_state"]["bear_history"],
            rounds=3
        )
        
        # 최종 리포트
        print("\n" + "="*80)
        print("📝 Final Investment Memo")
        print("="*80)
        synthesis = final_state.get("synthesis_report", "없음")
        if len(synthesis) > 500:
            print(synthesis[:500] + "...\n[전체 내용은 final_state['synthesis_report']에서 확인 가능]")
        else:
            print(synthesis)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 8. 정리
        print("\n[8] 연결 종료...")
        neo4j_conn.close()
        print("✅ 테스트 완료")


if __name__ == "__main__":
    main()
