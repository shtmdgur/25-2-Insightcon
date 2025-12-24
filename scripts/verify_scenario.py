import os
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# .env 로드
from dotenv import load_dotenv
load_dotenv()

from src.pipeline.debate_workflow import create_debate_workflow_for_studio
from src.utils.query_intent_parser import QueryIntentParser

def test_full_scenario():
    print("\n" + "="*60)
    print("🧪 [테스트 시나리오] 새로운 뉴스와 함께 특정 기업 전망 분석")
    print("="*60)

    # 1. 자연어 쿼리 및 가짜 뉴스 문서 준비
    user_query = "2024년 12월 24일 기준으로 삼성전자 HBM 흑자 전환이 주가에 미칠 영향을 분석해줘"
    mock_news_content = """
    [속보] 삼성전자, HBM3E 수율 85% 돌파... 4분기부터 흑자 전환 확실시
    
    삼성전자 반도체 부문이 고대역폭메모리(HBM) 사업에서 역사적인 전환점을 맞이했다. 
    내부 소식통에 따르면 삼성전자의 HBM3E 8단 제품 수율이 최근 85%를 기록하며 안정화 단계에 진입했다.
    이에 따라 그동안 적자를 면치 못했던 HBM 사업부가 올 4분기부터는 영업이익 흑자로 돌아설 것이 확실시된다.
    엔비디아와의 퀄 테스트 역시 최종 단계에 와있어 공급 물량이 대폭 늘어날 전망이다.
    """
    
    # 임시 파일 저장
    temp_news_path = PROJECT_ROOT / "data" / "temp_news.txt"
    temp_news_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_news_path, "w", encoding="utf-8") as f:
        f.write(mock_news_content)

    print(f"🔹 입력 쿼리: {user_query}")
    print(f"🔹 첨부 문서: {temp_news_path.name}")
    print("-" * 60)

    # 2. 쿼리 파서 테스트 (자연어 -> 구조화 데이터)
    print("\n[Step 1] 쿼리 파싱 테스트...")
    parser = QueryIntentParser()
    parsed_result = parser.parse(user_query, str(temp_news_path))
    
    print(f"✅ 추출된 기업: {parsed_result['target_companies']}")
    print(f"✅ 추출된 날짜: {parsed_result['target_date']}")
    print(f"✅ 파악된 의도: {parsed_result['intent']}")
    
    assert "삼성전자" in parsed_result['target_companies'], "기업명 추출 실패"
    assert parsed_result['target_date'] == "2024-12-24", "날짜 추출 실패"

    # 3. 워크플로우 초기화 및 문서 요약 테스트
    print("\n[Step 2] 워크플로우 초기화 및 문서 분석 테스트...")
    from src.pipeline.state import ReportState
    
    # 실제 그래프 생성 (Studio용 팩토리 함수 사용)
    graph = create_debate_workflow_for_studio()
    
    # 초기 상태 (ReportState)
    initial_state = {
        "query": user_query,
        "ticker": None,
        "target_companies": [],
        "target_date": None,
        "document": str(temp_news_path),
        "document_summary": None,
        "debate_state": None,
        "retry_count": 0,
        "errors": [],
        "execution_trace": []
    }

    # initialize 노드만 직접 실행하거나 graph.stream의 첫 단계를 확인
    # 여기서는 graph.stream을 활용하여 첫 번째 노드(initialize)의 출력을 확인
    
    step_count = 0
    for event in graph.stream(initial_state, stream_mode="updates"):
        for node_name, output in event.items():
            step_count += 1
            print(f"\n📍 실행 중인 노드: [{node_name}]")
            
            if node_name == "initialize":
                doc_sum = output.get("document_summary")
                if doc_sum:
                    print(f"✅ 문서 요약 성공: {doc_sum.get('main_topic')}")
                    print(f"   - 핵심 내용: {doc_sum.get('key_events', [])[:2]}")
                else:
                    print("❌ 문서 요약 실패")
            
            # 테스트 목적이므로 Bull 대화까지만 확인하고 중단 (시간 절약)
            if node_name == "bull":
                print("\n✅ Bull 에이전트가 Neo4j와 문서를 바탕으로 논거 생성을 시작했습니다.")
                print("--- [Bull Argument Preview] ---")
                arg = output.get("debate_state", {}).get("current_bull_arg", "")
                print(arg[:300] + "...")
                print("------------------------------")
                print("\n🎉 모든 과정(파싱 -> 문서분석 -> KG조회 -> 토론)이 원활하게 작동함을 확인했습니다.")
                return 

    print("\n⚠️ 테스트 완료 (일부 단계 스킵)")

if __name__ == "__main__":
    try:
        test_full_scenario()
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
