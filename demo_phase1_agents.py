"""
Phase 1 에이전트 통합 데모
=========================

이 스크립트는 Phase 1에서 구현한 모든 에이전트를 테스트합니다:
1. KGConstructionAgent - 문서에서 Knowledge Graph 추출
2. EventExtractor - 뉴스에서 이벤트 추출
3. TimeSeriesProcessor - 주가 패턴 분석

사용법:
    python demo_phase1_agents.py
"""

import os
import sys
from datetime import datetime
import logging

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(__file__))

from src.agents.kg_construction import KGConstructionAgent
from src.utils.event_extractor import EventExtractor
from src.utils.time_series_processor import TimeSeriesProcessor
from src.utils.neo4j_client import Neo4jClient
from src.utils.llm_config import get_llm

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """섹션 구분선 출력"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_kg_construction():
    """1. KG Construction Agent 데모"""
    print_section("📊 1. Knowledge Graph Construction Agent")
    
    # 샘플 문서 (증권사 리포트 발췌)
    sample_document = """
    삼성전자는 2024년 3분기 실적 발표에서 HBM3 메모리 출하량이 전 분기 대비 50% 증가했다고 밝혔다.
    매출액은 67조 원을 기록했으며, 영업이익은 10조 5천억 원으로 시장 예상치를 상회했다.
    
    반도체 업황 회복에 힘입어 SK하이닉스와의 경쟁 구도도 심화되고 있다.
    SK하이닉스는 AI 서버용 HBM3E 메모리를 생산하며 맞불을 놓고 있다.
    """
    
    try:
        # LLM 초기화
        llm = get_llm("quick")  # Gemini 2.5 Flash 사용
        
        # Neo4j 클라이언트 초기화
        neo4j_client = Neo4jClient()
        
        # KGConstructionAgent 초기화
        kg_agent = KGConstructionAgent(llm, neo4j_client)
        
        print("📄 입력 문서:")
        print("-" * 80)
        print(sample_document)
        print("-" * 80)
        
        # 지식 그래프 추출
        print("\n🔍 엔티티 및 관계 추출 중...")
        result = kg_agent.process_document(
            document=sample_document,
            source="demo_report.pdf"
        )
        
        # 결과 출력
        print("\n✅ 추출 완료!")
        print(f"\n📊 통계:")
        print(f"  - 엔티티: {result['stats']['entities']}개")
        print(f"  - 관계: {result['stats']['relations']}개")
        print(f"  - 에러: {result['stats']['errors']}개")
        
        # 상세 정보
        kg = result['knowledge_graph']
        print(f"\n🏢 추출된 엔티티:")
        for entity in kg['entities']:
            print(f"  - [{entity['type']}] {entity['name']} (신뢰도: {entity['confidence']:.2f})")
        
        print(f"\n🔗 추출된 관계:")
        for relation in kg['relations']:
            print(f"  - {relation['subject']} -[{relation['predicate']}]-> {relation['object']}")
        
        neo4j_client.close()
        
    except Exception as e:
        logger.error(f"KG Construction 데모 실패: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}")


def demo_event_extraction():
    """2. Event Extractor 데모"""
    print_section("📰 2. Event Extraction from News")
    
    # 샘플 뉴스
    sample_news = """
    [서울=연합뉴스] 한국은행이 14일 금융통화위원회를 열고 기준금리를 현행 3.25%에서 
    3.00%로 0.25%p 인하하기로 결정했다. 이번 금리 인하는 3개월 만이다.
    
    금리 인하로 삼성전자, SK하이닉스 등 반도체 기업들의 자금 조달 비용이 감소할 것으로 
    예상된다. 증권가에서는 IT 섹터 전반에 긍정적 영향을 미칠 것으로 전망하고 있다.
    """
    
    try:
        llm = get_llm("quick")
        neo4j_client = Neo4jClient()
        
        event_extractor = EventExtractor(llm, neo4j_client)
        
        print("📰 입력 뉴스:")
        print("-" * 80)
        print(sample_news)
        print("-" * 80)
        
        # 이벤트 추출
        print("\n🔍 이벤트 추출 중...")
        result = event_extractor.extract_events_from_news(
            news_text=sample_news,
            date="2024-12-14",
            source="연합뉴스"
        )
        
        # 결과 출력
        if 'event' in result and result['event']:
            event = result['event']
            print("\n✅ 이벤트 추출 완료!")
            print(f"\n📌 이벤트 정보:")
            print(f"  - 타입: {event.get('event_type')}")
            print(f"  - 설명: {event.get('description')}")
            print(f"  - 중요도: {event.get('importance')}/10")
            print(f"  - 영향: {event.get('impact')}")
            print(f"  - 영향받는 엔티티: {', '.join(event.get('affected_entities', []))}")
            
            if 'neo4j_result' in result:
                neo4j_result = result['neo4j_result']
                print(f"\n💾 Neo4j 저장:")
                print(f"  - 이벤트 노드: {neo4j_result.get('events_created', 0)}개")
                print(f"  - AFFECTS 관계: {neo4j_result.get('relations_created', 0)}개")
        else:
            print("⚠️ 추출된 이벤트가 없습니다.")
        
        neo4j_client.close()
        
    except Exception as e:
        logger.error(f"Event Extraction 데모 실패: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}")


def demo_time_series_processing():
    """3. Time Series Processor 데모"""
    print_section("📈 3. Time Series Processing (Stock Trends)")
    
    # 샘플 주가 데이터 (삼성전자, 최근 20일)
    sample_prices = [
        71000, 72000, 71500, 73000, 74500,
        75000, 74000, 76000, 77500, 78000,
        77000, 78500, 80000, 79000, 81000,
        82000, 81500, 83000, 84000, 85000
    ]
    
    try:
        neo4j_client = Neo4jClient()
        ts_processor = TimeSeriesProcessor(neo4j_client)
        
        print("📊 입력 주가 데이터 (삼성전자):")
        print("-" * 80)
        print(f"데이터 포인트: {len(sample_prices)}개")
        print(f"시작가: {sample_prices[0]:,}원")
        print(f"종가: {sample_prices[-1]:,}원")
        print(f"수익률: {((sample_prices[-1] - sample_prices[0]) / sample_prices[0] * 100):.2f}%")
        print("-" * 80)
        
        # SAX 변환 및 트렌드 분석
        print("\n🔍 SAX 패턴 변환 및 트렌드 분석 중...")
        result = ts_processor.process_stock_price(
            company_ticker="005930",  # 삼성전자
            prices=sample_prices,
            period="2024-Q4",
            window_size=5
        )
        
        # 결과 출력
        if 'error' not in result:
            print("\n✅ 분석 완료!")
            print(f"\n📈 트렌드 정보:")
            print(f"  - 티커: {result.get('ticker')}")
            print(f"  - 기간: {result.get('period')}")
            print(f"  - SAX 패턴: {result.get('pattern')}")
            print(f"  - 트렌드 타입: {result.get('trend_type')}")
            
            # 트렌드 타입 설명
            trend_type = result.get('trend_type')
            trend_explanation = {
                "Upward": "📈 상승 추세 (10% 이상 상승)",
                "Downward": "📉 하락 추세 (10% 이상 하락)",
                "Volatile": "⚡ 변동성이 큰 구간",
                "Stable": "➡️  안정적인 횡보"
            }
            print(f"\n💡 해석: {trend_explanation.get(trend_type, '알 수 없음')}")
        else:
            print(f"⚠️ 에러 발생: {result['error']}")
        
        neo4j_client.close()
        
    except Exception as e:
        logger.error(f"Time Series Processing 데모 실패: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}")


def demo_data_classification():
    """4. 데이터 분류 로직 설명"""
    print_section("🤖 4. 데이터 자동 분류 로직 설명")
    
    print("""
현재 Phase 1에서는 **수동 분류** 방식을 사용합니다:
사용자가 명시적으로 어떤 에이전트를 호출할지 결정합니다.

📝 현재 분류 방식:
┌─────────────────────────────────────────────────────────────┐
│ 입력 타입              │ 사용 에이전트                       │
├─────────────────────────────────────────────────────────────┤
│ PDF/리포트 문서       │ → KGConstructionAgent            │
│ 뉴스 기사             │ → EventExtractor                 │
│ 주가 시계열 (CSV)     │ → TimeSeriesProcessor            │
└─────────────────────────────────────────────────────────────┘

🚀 Phase 2에서 구현 예정: **자동 분류 라우터**

class DataRouter:
    def classify_and_route(self, data: str) -> str:
        \"\"\"
        데이터 타입 자동 감지 및 라우팅
        \"\"\"
        # LLM으로 데이터 타입 판단
        prompt = f\"\"\"
        다음 데이터의 타입을 분류하세요:
        
        데이터: {data[:500]}
        
        타입:
        - report: 증권사 리포트, 분석 문서
        - news: 뉴스 기사 (실시간 이벤트)
        - timeseries: 수치형 시계열 데이터
        
        JSON 형식으로 답변: {{"type": "...", "confidence": 0.0-1.0}}
        \"\"\"
        
        response = self.llm.invoke(prompt)
        classification = json.loads(response.content)
        
        # 라우팅
        if classification["type"] == "report":
            return self.kg_agent.process_document(data)
        elif classification["type"] == "news":
            return self.event_extractor.extract_events(data)
        elif classification["type"] == "timeseries":
            return self.ts_processor.process(data)

📊 판단 기준:

1. **구조적 특징**:
   - 보고서: 장문, 섹션 구조, 표/차트 포함
   - 뉴스: 날짜 명시, 간결한 사실 전달, 인용구
   - 시계열: 수치 배열, 날짜/시간 컬럼

2. **키워드 분석**:
   - 보고서: "전망", "분석", "목표가", "리포트"
   - 뉴스: "오늘", "발표", "밝혔다", "전했다"
   - 시계열: 열 이름에 "date", "price", "volume" 등

3. **시간성**:
   - 정적 (온톨로지): 기업 구조, 제품 라인업
   - 동적 (이벤트): 뉴스, 공시, 이슈
   - 시계열 (트렌드): 주가, 거래량, 재무 지표

현재는 이 분류를 **사용자가 직접 수행**하고,
Phase 2에서 **LLM 기반 자동 라우터**를 추가할 예정입니다.
""")


def main():
    """메인 함수"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   Phase 1 에이전트 통합 데모                         ║
║                                                                      ║
║  이 데모는 Knowledge Graph 구축의 핵심 컴포넌트를 테스트합니다      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  주의사항:")
    print("  1. .env 파일에 GEMINI_API_KEY가 설정되어 있어야 합니다")
    print("  2. Neo4j 인스턴스가 실행 중이어야 합니다")
    print("  3. 필요한 패키지: google-genai, neo4j, saxpy\n")
    
    # 환경 변수 체크
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ 에러: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일을 확인해주세요.\n")
        return
    
    try:
        # 데모 실행
        demo_kg_construction()
        input("\n계속하려면 Enter를 누르세요...")
        
        demo_event_extraction()
        input("\n계속하려면 Enter를 누르세요...")
        
        demo_time_series_processing()
        input("\n계속하려면 Enter를 누르세요...")
        
        demo_data_classification()
        
        print_section("🎉 데모 완료!")
        print("""
다음 단계:
  1. Neo4j Browser에서 그래프 시각화: http://localhost:7474
  2. 실제 데이터로 테스트: test/test_gemini_pdf_neo4j.py 실행
  3. Phase 2 고도화 작업 진행
        """)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 중단했습니다.")
    except Exception as e:
        logger.error(f"데모 실행 중 에러 발생: {str(e)}")
        print(f"\n❌ 에러 발생: {str(e)}")


if __name__ == "__main__":
    main()
