
from src.pipeline.state import ReportState
from src.utils.price_data_loader import PriceDataLoader
from pathlib import Path
import logging

# Logger 설정
logger = logging.getLogger(__name__)

# PriceDataLoader 싱글톤 인스턴스 (모듈 레벨 캐싱 활용)
_price_loader = None

def _get_price_loader() -> PriceDataLoader:
    global _price_loader
    if _price_loader is None:
        # 워크스페이스 루트 기준으로 경로 설정
        # 가정: 실행 위치가 프로젝트 루트라고 가정
        data_dir = Path("data/preprocessed/price")
        _price_loader = PriceDataLoader(str(data_dir))
    return _price_loader

def load_price_context_node(state: ReportState) -> ReportState:
    """
    [LangGraph Node] 가격 데이터 로드 및 문맥 주입
    
    1. State에서 'query'와 'target_companies' 추출
    2. PriceDataLoader를 통해 날짜별/종목별 시장 상황(Trend, Volatility) 조회
    3. 자연어 요약문을 생성하여 state['market_context']에 저장
    """
    try:
        # 1. 입력 추출
        target_companies = state.get("target_companies", [])
        # TODO: 쿼리에서 날짜를 추출하는 로직이 필요하지만, 
        # 현재는 graphrag_results나 news_events에 포함된 날짜를 우선적으로 참고한다고 가정
        # 임시: 가장 최근 뉴스 날짜나, 쿼리에 명시된 날짜를 찾아야 함
        # 여기서는 간단히 '2023-01-05'와 같은 특정 날짜가 있다고 가정하거나 Context에 포함
        
        # 더 나은 전략: GraphRAG 결과에서 'event_date'들을 수집해서 그 날짜의 주가를 조회
        # 현재는 POC 레벨이므로, GraphRAG 결과에 있는 첫 번째 이벤트 날짜를 사용해봅니다.
        target_date = None
        
        # GraphRAG 결과에서 날짜 탐색 시도
        graph_results = state.get("graphrag_results", {})
        if graph_results and "events" in graph_results:
            first_event = graph_results["events"][0]
            if "date" in first_event:
                target_date = first_event["date"]
                
        # 기본값 (테스트용)
        if not target_date:
            # TODO: 실제 운영 시에는 오늘 날짜 또는 쿼리 기반 날짜 추출 필요
            # 일단 None이면 빈 컨텍스트 반환
            pass

        if not target_companies:
            return {"market_context": "분석 대상 기업이 지정되지 않아 시장 데이터를 로드하지 못했습니다."}

        # 2. 데이터 로드
        loader = _get_price_loader()
        context_lines = []
        
        for ticker in target_companies:
            # 티커 매핑 필요 (기업명 -> 티커)
            # 여기서는 편의상 target_companies가 티커라고 가정하거나, 
            # 별도의 매핑 로직이 필요함. (일단 그대로 시도)
            # 실제로는 'Samsung Electronics' -> '005930.KS' 변환 필요
            
            # (임시) 만약 심볼이 아니면 로드 실패할 수 있음. 
            # 추후 Company Metadata Store에서 매핑 가져와야 함.
            
            if target_date:
                context = loader.get_context(ticker, target_date)
                if context:
                    context_lines.append(context)
            else:
                # 날짜가 없으면 로드 스킵 (또는 최근 데이터 로드)
                pass

        # 3. 결과 저장
        if not context_lines:
            market_context = "관련된 날짜의 시장 데이터(주가/추세)를 찾을 수 없습니다."
        else:
            market_context = "\n\n".join(context_lines)
            
        # 기존 값을 덮어쓰거나 추가 (여기서는 덮어쓰기)
        return {"market_context": market_context}

    except Exception as e:
        logger.error(f"Price Node Error: {e}")
        return {"errors": [f"Price DB Load Error: {str(e)}"]}
