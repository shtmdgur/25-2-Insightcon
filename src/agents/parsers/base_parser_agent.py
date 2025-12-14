"""
Base Parser Agent

모든 Parser Agent의 공통 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging

from src.models.nodes import KnowledgeGraph, NodeType

logger = logging.getLogger(__name__)


class BaseParserAgent(ABC):
    """
    Parser Agent 추상 클래스
    
    모든 데이터 소스별 Parser는 이 클래스를 상속받아 구현합니다.
    """
    
    def __init__(self, name: str):
        """
        Args:
            name: Parser 이름 (로깅용)
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def parse(self, file_path: Path) -> KnowledgeGraph:
        """
        파일을 파싱하여 Knowledge Graph 추출
        
        Args:
            file_path: 파싱할 파일 경로
        
        Returns:
            KnowledgeGraph 객체
        
        Raises:
            ValueError: 파일 형식이 잘못되었거나 파싱 실패 시
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        pass
    
    def classify_layer(self, node_type: NodeType) -> str:
        """
        엔티티 타입 기반 레이어 분류 (정적 vs 동적)
        
        Args:
            node_type: 노드 타입
        
        Returns:
            'static' 또는 'dynamic'
        """
        static_types = {
            NodeType.COMPANY,
            NodeType.PRODUCT,
            NodeType.TECHNOLOGY,
            NodeType.PERSON
        }
        
        if node_type in static_types:
            return "static"
        else:
            return "dynamic"
    
    def to_json(
        self,
        kg: KnowledgeGraph,
        output_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Knowledge Graph를 JSON 파일로 저장 (공통 로직)
        
        Args:
            kg: Knowledge Graph 객체
            output_path: 저장할 파일 경로
            metadata: 추가 메타데이터
        """
        try:
            # 메타데이터 추가
            if metadata:
                kg.metadata.update(metadata)
            
            # 파서 정보 추가
            kg.metadata.update({
                "parser": self.name,
                "created_at": self._get_current_timestamp()
            })
            
            # JSON 저장
            kg.save_to_json(str(output_path))
            
            self.logger.info(
                f"Saved KG to {output_path}: "
                f"{len(kg.entities)} entities, {len(kg.relations)} relations"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save KG to JSON: {str(e)}")
            raise
    
    def batch_parse(
        self,
        file_paths: List[Path],
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        여러 파일을 배치 처리
        
        Args:
            file_paths: 파일 경로 리스트
            output_dir: 출력 디렉토리
        
        Returns:
            배치 처리 결과 통계
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "total": len(file_paths),
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for file_path in file_paths:
            try:
                # 파싱
                kg = self.parse(file_path)
                
                # JSON 저장
                output_file = output_dir / f"{file_path.stem}_kg.json"
                self.to_json(kg, output_file)
                
                stats["success"] += 1
                
            except Exception as e:
                self.logger.error(f"Failed to parse {file_path}: {str(e)}")
                stats["failed"] += 1
                stats["errors"].append({
                    "file": str(file_path),
                    "error": str(e)
                })
        
        return stats
    
    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환 (ISO 8601 형식)"""
        from datetime import datetime
        return datetime.now().isoformat()
