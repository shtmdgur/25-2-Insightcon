"""
Macro Parser Agent

FRED 거시경제 지표 CSV 파일을 Knowledge Graph로 변환합니다.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
import pandas as pd

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph, Entity, Relation, NodeType, RelationType

logger = logging.getLogger(__name__)


class MacroParserAgent(BaseParserAgent):
    """
    FRED 거시경제 지표 파싱 Agent
    
    데이터 레이어: 100% 동적 (Metric)
    Neo4j 전략: CREATE (시간 속성 필수)
    """
    
    def __init__(self):
        super().__init__(name="MacroParserAgent")
    
    def parse(self, file_path: Path) -> KnowledgeGraph:
        """
        FRED CSV를 파싱하여 Knowledge Graph 추출
        
        Args:
            file_path: CSV 파일 경로 (fred_rates.csv)
        
        Returns:
            KnowledgeGraph 객체 (Metric 노드)
        
        Raises:
            ValueError: CSV 파싱 실패 시
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.csv':
            raise ValueError(f"Not a CSV file: {file_path}")
        
        try:
            self.logger.info(f"Parsing macro CSV: {file_path}")
            
            # CSV로드
            df = pd.read_csv(file_path)
            
            # 필수 컬럼 검증
            self._validate_columns(df)
            
            # Knowledge Graph 생성
            kg = self._create_knowledge_graph(df, file_path)
            
            self.logger.info(
                f"Macro CSV parsed: {len(kg.entities)} entities, "
                f"{len(kg.relations)} relations"
            )
            
            return kg
            
        except Exception as e:
            self.logger.error(f"Failed to parse macro CSV {file_path}: {str(e)}")
            raise ValueError(f"Macro CSV parsing failed: {str(e)}")
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        if "entities" not in data or "relations" not in data:
            self.logger.warning("Missing entities or relations")
            return False
        
        # Metric 엔티티 확인
        has_metrics = any(
            e.get("type") == NodeType.METRIC.value
            for e in data["entities"]
        )
        
        if not has_metrics:
            self.logger.warning("No Metric entities found")
            return False
        
        return True
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        CSV 필수 컬럼 검증
        
        Args:
            df: DataFrame
        
        Raises:
            ValueError: 필수 컬럼 누락 시
        """
        columns_lower = [col.lower() for col in df.columns]
        
        required = ["date", "value", "series"]
        missing = [col for col in required if col not in columns_lower]
        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        if len(df) == 0:
            raise ValueError("CSV file is empty")
    
    def _create_knowledge_graph(
        self,
        df: pd.DataFrame,
        file_path: Path
    ) -> KnowledgeGraph:
        """
        DataFrame을 Knowledge Graph로 변환
        
        Args:
            df: FRED DataFrame
            file_path: 원본 파일 경로
        
        Returns:
            KnowledgeGraph 객체
        """
        entities = []
        relations = []
        
        # 컬럼명 소문자로 정규화
        df.columns = [col.lower() for col in df.columns]
        
        # 날짜 파싱
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df[df['date'].notna()]  # 날짜 없는 행 제거
        df = df.sort_values('date', ascending=False)
        
        # 지표별 그룹화
        series_groups = df.groupby('series')
        
        self.logger.info(f"Found {len(series_groups)} unique indicators")
        
        for series_name, group_df in series_groups:
            # 샘플링 (config에서 가져옴)
            from src.config.parser_config import get_config
            config = get_config('macro')
            
            sample_size = min(config.sample_per_series, len(group_df))
            sampled = group_df.head(sample_size)
            
            for idx, row in sampled.iterrows():
                # Metric 엔티티 생성 (동적 KG)
                date_str = row['date'].strftime('%Y-%m-%d')
                
                metric_entity = Entity(
                    name=f"MacroMetric_{series_name}_{date_str}",
                    type=NodeType.METRIC,
                    properties={
                        "series": str(series_name),
                        "date": date_str,
                        "value": float(row['value']),
                        "indicator_type": "macro"
                    },
                    confidence=1.0
                )
                entities.append(metric_entity)
        
        # Knowledge Graph 생성
        kg = KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={
                "source_file": str(file_path),
                "file_type": "macro_csv",
                "total_indicators": len(series_groups),
                "total_data_points": len(df),
                "sampled_data_points": len(entities)
            }
        )
        
        return kg
