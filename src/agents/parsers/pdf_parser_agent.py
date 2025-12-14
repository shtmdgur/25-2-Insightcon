"""
PDF Parser Agent

GeminiPDFParser를 래핑하여 PDF 파일을 Knowledge Graph로 변환합니다.
"""

from pathlib import Path
from typing import Dict, Any
import logging

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph
from src.parsers.gemini_pdf import GeminiPDFParser

logger = logging.getLogger(__name__)


class PDFParserAgent(BaseParserAgent):
    """
    PDF 파싱 전담 Sub-Agent
    
    GeminiPDFParser를 사용하여 PDF에서 Knowledge Graph를 추출합니다.
    """
    
    def __init__(self, use_batch: bool = False):
        """
        Args:
            use_batch: Batch API 사용 여부 (대량 PDF 처리 시)
        """
        super().__init__(name="PDFParserAgent")
        self.use_batch = use_batch
        self.parser = GeminiPDFParser(use_batch=use_batch)
    
    def parse(self, file_path: Path) -> KnowledgeGraph:
        """
        PDF 파일을 파싱하여 Knowledge Graph 추출
        
        Args:
            file_path: PDF 파일 경로
        
        Returns:
            KnowledgeGraph 객체
        
        Raises:
            ValueError: PDF 파싱 실패 시
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.pdf':
            raise ValueError(f"Not a PDF file: {file_path}")
        
        try:
            self.logger.info(f"Parsing PDF: {file_path}")
            
            # GeminiPDFParser 호출
            kg = self.parser.parse_pdf_to_kg(str(file_path))
            
            # 메타데이터 추가
            kg.metadata.update({
                "source_file": str(file_path),
                "file_type": "pdf"
            })
            
            self.logger.info(
                f"PDF parsed successfully: {len(kg.entities)} entities, "
                f"{len(kg.relations)} relations"
            )
            
            return kg
            
        except Exception as e:
            self.logger.error(f"Failed to parse PDF {file_path}: {str(e)}")
            raise ValueError(f"PDF parsing failed: {str(e)}")
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        # 기본 검증: entities와 relations 키 존재 여부
        if "entities" not in data or "relations" not in data:
            self.logger.warning("Missing entities or relations in data")
            return False
        
        # 최소 엔티티 수 확인
        if len(data["entities"]) == 0:
            self.logger.warning("No entities extracted from PDF")
            return False
        
        return True
