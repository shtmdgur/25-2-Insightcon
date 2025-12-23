"""
Price Data Tools for LLM Tool Calling

LLM이 동적으로 호출할 수 있는 주가 데이터 조회 도구
"""
from langchain_core.tools import tool
from typing import Optional


@tool
def get_price_context(ticker: str, start_date: str, end_date: Optional[str] = None) -> str:
    """
    특정 종목의 주가 패턴을 조회합니다.
    
    Args:
        ticker: 종목 코드 (예: "005930.KS", "^KQ11")
        start_date: 조회 시작일 (YYYY-MM-DD 형식)
        end_date: 조회 종료일 (선택, YYYY-MM-DD 형식). 없으면 start_date 하루만 조회.
    
    Returns:
        해당 기간의 주가 패턴 요약 (SAX 패턴, 추세, Z-Score 등)
    
    Examples:
        - get_price_context("005930.KS", "2023-01-05") → 단일 날짜 조회
        - get_price_context("005930.KS", "2023-10-01", "2023-12-31") → 4분기 조회
    """
    from src.utils.price_data_loader import PriceDataLoader
    
    loader = PriceDataLoader()
    
    if end_date:
        return loader.get_context_range(ticker, start_date, end_date)
    else:
        return loader.get_context(ticker, start_date)


# Tool list for binding
PRICE_TOOLS = [get_price_context]
