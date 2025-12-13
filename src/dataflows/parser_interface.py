"""
Vendor-Agnostic Parser Interface 및 Fallback 메커니즘

Primary parser 실패 시 자동으로 대체 parser로 전환합니다.
"""
import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class ParserStrategy(str, Enum):
    """파서 전략"""
    PRIMARY = "primary"      # Hybrid (PyMuPDF + VLM) - 추천
    SECONDARY = "secondary"  # PyMuPDF (텍스트 전용)
    FALLBACK = "fallback"    # OCR (Tesseract)


class ParserError(Exception):
    """파서 에러"""
    pass


class ParserInterface:
    """
    파서 인터페이스
    
    모든 파서는 이 인터페이스를 구현해야 합니다.
    """
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        파일 파싱
        
        Args:
            file_path: 파싱할 파일 경로
        
        Returns:
            파싱 결과 딕셔너리
            {
                "text": str,
                "images": List[Dict],
                "metadata": Dict
            }
        """
        raise NotImplementedError


class RobustPDFParser:
    """
    Fallback 메커니즘을 갖춘 견고한 PDF 파서
    
    Primary → Secondary → Fallback 순서로 자동 전환
    """
    
    def __init__(
        self,
        primary_parser: Optional[ParserInterface] = None,
        secondary_parser: Optional[ParserInterface] = None,
        fallback_parser: Optional[ParserInterface] = None
    ):
        """
        Args:
            primary_parser: Hybrid 파서 (PyMuPDF + VLM)
            secondary_parser: PyMuPDF 파서 (텍스트 전용)
            fallback_parser: OCR 파서 (Tesseract)
        """
        self.primary_parser = primary_parser
        self.secondary_parser = secondary_parser
        self.fallback_parser = fallback_parser
    
    def parse(
        self,
        file_path: str,
        strategy: ParserStrategy = ParserStrategy.PRIMARY
    ) -> Dict[str, Any]:
        """
        파일 파싱 (자동 Fallback)
        
        Args:
            file_path: 파싱할 파일 경로
            strategy: 시작 전략 (기본: PRIMARY)
        
        Returns:
            파싱 결과
        
        Raises:
            ParserError: 모든 파서가 실패한 경우
        """
        parsers = {
            ParserStrategy.PRIMARY: self.primary_parser,
            ParserStrategy.SECONDARY: self.secondary_parser,
            ParserStrategy.FALLBACK: self.fallback_parser
        }
        
        # 전략 순서 정의
        strategy_order = [
            ParserStrategy.PRIMARY,
            ParserStrategy.SECONDARY,
            ParserStrategy.FALLBACK
        ]
        
        # 지정된 전략부터 시작
        start_idx = strategy_order.index(strategy)
        
        for current_strategy in strategy_order[start_idx:]:
            parser = parsers[current_strategy]
            
            if parser is None:
                logger.warning(f"Parser not configured: {current_strategy}")
                continue
            
            try:
                logger.info(f"Attempting to parse with {current_strategy} parser")
                result = parser.parse(file_path)
                
                # 성공
                result["parser_strategy"] = current_strategy.value
                logger.info(f"Successfully parsed with {current_strategy} parser")
                return result
                
            except Exception as e:
                logger.warning(
                    f"{current_strategy} parser failed: {str(e)}. "
                    f"Trying next fallback..."
                )
                continue
        
        # 모든 파서 실패
        raise ParserError(f"All parsers failed for file: {file_path}")
    
    def set_primary_parser(self, parser: ParserInterface):
        """Primary 파서 설정"""
        self.primary_parser = parser
    
    def set_secondary_parser(self, parser: ParserInterface):
        """Secondary 파서 설정"""
        self.secondary_parser = parser
    
    def set_fallback_parser(self, parser: ParserInterface):
        """Fallback 파서 설정"""
        self.fallback_parser = parser
