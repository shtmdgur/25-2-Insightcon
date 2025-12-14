"""
Parser Agent Configuration

모든 Parser Agent의 하이퍼파라미터를 중앙 관리합니다.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class PriceParserConfig:
    """주가 Parser 설정"""
    # 샘플링
    sample_size: int = 30  # 최근 N일
    min_samples: int = 10  # 최소 샘플 수
    sample_ratio: float = 0.1  # 전체의 10%
    
    # SAX 변환
    sax_window_size: int = 5  # 윈도우 크기
    sax_paa_size: int = 3  # PAA 세그먼트 수
    sax_alphabet_size: int = 5  # 알파벳 크기 (a-e)
    
    # 트렌드 분류 임계값
    volatility_threshold: float = 0.05  # 변동성 5%
    upward_threshold: float = 0.1  # 상승 추세 10%
    downward_threshold: float = -0.1  # 하락 추세 -10%


@dataclass
class NewsParserConfig:
    """뉴스 Parser 설정"""
    # 샘플링
    sample_size: int = 100  # 최근 N건
    max_title_length: int = 200  # 제목 최대 길이
    max_desc_length: int = 500  # 설명 최대 길이
    
    # Time-decay 가중치
    time_decay_halflife: int = 90  # 반감기 (일)
    time_decay_min_weight: float = 0.1  # 최소 가중치
    
    # LLM 설정
    use_llm: bool = False  # LLM 사용 여부
    llm_model: str = "gemini-2.5-flash"  # LLM 모델명
    use_batch: bool = False  # Batch API 사용 여부


@dataclass
class MacroParserConfig:
    """거시경제 Parser 설정"""
    sample_per_series: int = 50  # 각 지표당 최근 N개


@dataclass
class DARTParserConfig:
    """DART Parser 설정"""
    # 샘플링 없음 (전체 데이터 사용)
    sample_disclosure: bool = False  # 공시 샘플링 여부
    sample_financial: bool = False  # 재무 샘플링 여부


@dataclass
class FundParserConfig:
    """펀더멘탈 Parser 설정"""
    save_as_snapshot: bool = False  # False: Company 속성, True: Metric 스냅샷


@dataclass
class ParserConfigs:
    """전체 Parser 설정"""
    price: PriceParserConfig = field(default_factory=PriceParserConfig)
    news: NewsParserConfig = field(default_factory=NewsParserConfig)
    macro: MacroParserConfig = field(default_factory=MacroParserConfig)
    dart: DARTParserConfig = field(default_factory=DARTParserConfig)
    fund: FundParserConfig = field(default_factory=FundParserConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            "price": self.price.__dict__,
            "news": self.news.__dict__,
            "macro": self.macro.__dict__,
            "dart": self.dart.__dict__,
            "fund": self.fund.__dict__
        }


# 전역 설정 인스턴스
PARSER_CONFIGS = ParserConfigs()


def get_config(parser_type: str) -> Any:
    """
    Parser 타입별 설정 반환
    
    Args:
        parser_type: 'price', 'news', 'macro', 'dart', 'fund'
    
    Returns:
        해당 Parser의 Config 객체
    """
    return getattr(PARSER_CONFIGS, parser_type.lower())


def update_config(parser_type: str, **kwargs):
    """
    Parser 설정 업데이트
    
    Args:
        parser_type: Parser 타입
        **kwargs: 업데이트할 설정 값
    
    Example:
        update_config('price', sample_size=50, volatility_threshold=0.03)
    """
    config = get_config(parser_type)
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown config key: {key} for {parser_type}")
