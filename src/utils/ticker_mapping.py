"""
Ticker → Company Name 매핑 테이블

preprocessed 데이터의 Ticker를 정규화된 회사명으로 변환합니다.
국내 기업은 한글명을 사용합니다.
"""

from src.models.nodes import NodeType

# Ticker → 회사명 매핑 (국내 기업은 한글)
TICKER_TO_COMPANY = {
    # 한국 기업 (한글명)
    "005930.KS": "삼성전자",
    "005930": "삼성전자",
    "000660.KS": "SK하이닉스",
    "000660": "SK하이닉스",
    "000990.KS": "DB하이텍",
    "000990": "DB하이텍",
    "042700.KS": "한미반도체",
    "042700": "한미반도체",
    
    # 한국 지수
    "^KS11": "KOSPI",
    "^KQ11": "KOSDAQ",
    
    # 글로벌 기업 (영문명 - NodeType 키와 일치)
    "NVDA": "NVIDIA Corporation",
    "TSM": "Taiwan Semiconductor",
    "INTC": "Intel Corporation",
    "MU": "Micron Technology",
    "ASML": "ASML Holding",
    "AMAT": "Applied Materials",
    "LRCX": "Lam Research",
    "AVGO": "Broadcom",
    "AMD": "Advanced Micro Devices",
    "QCOM": "Qualcomm",
    "TXN": "Texas Instruments",
    
    # 글로벌 지수
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    
    # 환율
    "USDKRW=X": "USD/KRW",
    "USDJPY=X": "USD/JPY",
}

# 이름 별칭(Alias) → 표준명(Canonical Name) 매핑 (확장됨)
ALIAS_TO_STANDARD = {
    # === 한국 기업 ===
    "삼성": "삼성전자",
    "삼전": "삼성전자",
    "Samsung": "삼성전자",
    "Samsung Electronics": "삼성전자",
    
    "하이닉스": "SK하이닉스",
    "SK 하이닉스": "SK하이닉스",
    "SK Hynix": "SK하이닉스",
    "SK하이": "SK하이닉스",
    
    "디비하이텍": "DB하이텍",
    "DB하이": "DB하이텍",
    "디비하이텍": "DB하이텍",
    "DB하이": "DB하이텍",
    "디비하이": "DB하이텍",

    "Hanmi Semiconductor": "한미반도체",
    "Hanmi": "한미반도체",
    "Hanmi Semi": "한미반도체",
    
    # === 미국 기업 ===
    "엔비디아": "NVIDIA Corporation",
    "엔비디아코리아": "NVIDIA Corporation",
    "NVIDIA": "NVIDIA Corporation",
    "Nvidia": "NVIDIA Corporation",
    
    "인텔": "Intel Corporation",
    "Intel": "Intel Corporation",
    "인텔코리아": "Intel Corporation",
    
    "마이크론": "Micron Technology",
    "Micron": "Micron Technology",
    "마이크론테크놀로지": "Micron Technology",
    
    "퀄컴": "Qualcomm",
    "QCOM": "Qualcomm",
    "퀄컴코리아": "Qualcomm",
    
    "브로드컴": "Broadcom",
    "AVGO": "Broadcom",
    
    "AMD": "Advanced Micro Devices",
    "Amd": "Advanced Micro Devices",
    "에이엠디": "Advanced Micro Devices",
    
    # === 아시아 기업 ===
    "TSMC": "Taiwan Semiconductor",
    "티에스엠씨": "Taiwan Semiconductor",
    "대만반도체": "Taiwan Semiconductor",
    "타이완세미컨덕터": "Taiwan Semiconductor",
    "TSMC홀딩스": "Taiwan Semiconductor",
    
    "키옥시아": "Kioxia",
    "KIOXIA": "Kioxia",
    "키오시아": "Kioxia",
    "도시바메모리": "Kioxia",
    
    "웨스턴디지털": "Western Digital",
    "WD": "Western Digital",
    "웨스턴 디지털": "Western Digital",
    
    "난야": "Nanya Technology",
    "난야테크": "Nanya Technology",
    "Nanya": "Nanya Technology",
    
    # === 장비/소재 기업 ===
    "ASML": "ASML Holding",
    "에이에스엠엘": "ASML Holding",
    
    "어플라이드": "Applied Materials",
    "어플라이드머티리얼즈": "Applied Materials",
    "AMAT": "Applied Materials",
    
    "램리서치": "Lam Research",
    "LRCX": "Lam Research",
    
    "텍사스인스트루먼트": "Texas Instruments",
    "텍사스 인스트루먼트": "Texas Instruments",
    "TI": "Texas Instruments",
    
    # === 지표 별칭 ===
    "원달러 환율": "USD/KRW",
    "USD/KRW 환율": "USD/KRW",
    "달러 환율": "USD/KRW",
    "원/달러": "USD/KRW",
    "미국 10년물 국채 금리": "10-Year Treasury Yield",
    "필라델피아 반도체 지수": "PHLX Semiconductor Sector",
    "SOX": "PHLX Semiconductor Sector",
    "반도체지수": "PHLX Semiconductor Sector",
}

# 회사명 → NodeType 매핑
COMPANY_TO_NODE_TYPE = {
    # 한국 IDM
    "삼성전자": NodeType.IDM,
    "SK하이닉스": NodeType.IDM,
    
    # 한국 Foundry
    "DB하이텍": NodeType.FOUNDRY,
    
    # 글로벌 Fabless
    "NVIDIA Corporation": NodeType.FABLESS,
    "Advanced Micro Devices": NodeType.FABLESS,
    "Qualcomm": NodeType.FABLESS,
    "Broadcom": NodeType.FABLESS,
    
    # 글로벌 Foundry
    "Taiwan Semiconductor": NodeType.FOUNDRY,
    
    # 글로벌 IDM
    "Intel Corporation": NodeType.IDM,
    "Micron Technology": NodeType.IDM,
    "Texas Instruments": NodeType.IDM,
    
    # 장비 공급사
    "ASML Holding": NodeType.SUPPLIER,
    "Applied Materials": NodeType.SUPPLIER,
    "Lam Research": NodeType.SUPPLIER,
    
    # 지수
    "KOSPI": NodeType.ECONOMIC_INDICATOR,
    "KOSDAQ": NodeType.ECONOMIC_INDICATOR,
    "S&P 500": NodeType.ECONOMIC_INDICATOR,
    "Dow Jones": NodeType.ECONOMIC_INDICATOR,
    "NASDAQ": NodeType.ECONOMIC_INDICATOR,
    
    # 환율
    "USD/KRW": NodeType.ECONOMIC_INDICATOR,
    "USD/JPY": NodeType.ECONOMIC_INDICATOR,
}


def get_company_name(ticker: str) -> str:
    """
    Ticker를 회사명으로 변환
    
    Args:
        ticker: Ticker 코드 (예: "005930.KS", "NVDA")
    
    Returns:
        정규화된 회사명 (국내 기업은 한글)
    """
    return TICKER_TO_COMPANY.get(ticker, ticker)


def get_node_type(company_name: str) -> NodeType:
    """
    회사명에서 NodeType 추론
    
    Args:
        company_name: 회사명 (예: "삼성전자", "NVIDIA Corporation")
    
    Returns:
        NodeType (IDM/FABLESS/FOUNDRY/SUPPLIER/ECONOMIC_INDICATOR)
    """
    # 정확한 매칭
    if company_name in COMPANY_TO_NODE_TYPE:
        return COMPANY_TO_NODE_TYPE[company_name]
    
    # 부분 매칭 (Fallback)
    company_lower = company_name.lower()
    
    if any(keyword in company_lower for keyword in ["nvidia", "amd", "qualcomm", "broadcom"]):
        return NodeType.FABLESS
    elif "tsmc" in company_lower or "taiwan semi" in company_lower:
        return NodeType.FOUNDRY
    elif any(keyword in company_lower for keyword in ["asml", "applied", "lam research"]):
        return NodeType.SUPPLIER
    elif any(keyword in company_lower for keyword in ["삼성", "samsung", "sk", "intel", "micron", "texas"]):
        return NodeType.IDM
    
    # 기본값
    return NodeType.ORGANIZATION


def normalize_company_name(name: str) -> str:
    """
    회사명 정규화 (괄호 제거, 공백 정리)
    
    Args:
        name: 원본 회사명 (예: "삼성전자(주)", "  NVIDIA Corp  ")
    
    Returns:
        정규화된 회사명
    """
    # 괄호 및 내부 텍스트 제거
    import re
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'주식회사', '', name)
    
    # 영문 법인 접미사 제거
    name = re.sub(r'\s+Corp\.?$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+Co\.,?\s*Ltd\.?$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+Inc\.?$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+Corporation$', '', name, flags=re.IGNORECASE)
    
    # 공백 정리
    name = ' '.join(name.split())
    
    return name.strip()


def resolve_entity_name(name: str) -> str:
    """
    엔티티 이름 정규화 (Alias 처리 포함)
    
    1. Alias 매핑 확인 (예: "퀄컴" -> "Qualcomm")
    2. 텍스트 정규화 (괄호 제거 등)
    3. 표준명 반환
    """
    # 1. 원본 그대로 Alias 확인
    if name in ALIAS_TO_STANDARD:
        return ALIAS_TO_STANDARD[name]
    
    # 2. 정규화 후 재확인
    normalized = normalize_company_name(name)
    if normalized in ALIAS_TO_STANDARD:
        return ALIAS_TO_STANDARD[normalized]
        
    return normalized


# 회사명 → Ticker 매핑 (역방향)
COMPANY_TO_TICKER = {v: k for k, v in TICKER_TO_COMPANY.items()}

def get_ticker_from_name(company_name: str) -> str:
    """
    회사명에서 Ticker 조회 (역방향 매핑)
    
    Args:
        company_name: 정규화된 회사명 (예: "삼성전자", "NVIDIA Corporation")
    
    Returns:
        Ticker 코드 (없으면 None)
    """
    return COMPANY_TO_TICKER.get(company_name)

