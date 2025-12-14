"""
DART Parser Agent

DART 공시 데이터 CSV 파일을 Knowledge Graph로 변환합니다.
3개 CSV (companies, disclosure_states, financial_states)를 통합 처리합니다.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import pandas as pd
from datetime import datetime

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph, Entity, Relation, NodeType, RelationType
from src.utils.entity_normalizer import get_entity_normalizer

logger = logging.getLogger(__name__)


class DARTParserAgent(BaseParserAgent):
    """
    DART 공시 데이터 파싱 Agent
    
    데이터 레이어: 정적(Company) + 동적(Event, Metric)
    Neo4j 전략: Company=MERGE, Event/Metric=CREATE
    """
    
    def __init__(self, dart_dir: Optional[Path] = None):
        """
        Args:
            dart_dir: DART 데이터 디렉토리 (data/raw/DART)
        """
        super().__init__(name="DARTParserAgent")
        self.dart_dir = dart_dir
        self.normalizer = get_entity_normalizer()
    
    def parse(self, file_path: Path) -> KnowledgeGraph:
        """
        DART 디렉토리의 3개 CSV를 통합 파싱
        
        Args:
            file_path: DART 디렉토리 경로 (여기서는 디렉토리를 받음)
        
        Returns:
            KnowledgeGraph 객체 (Company + Event + Metric)
        
        Raises:
            ValueError: CSV 파싱 실패 시
        """
        # file_path가 디렉토리인 경우 처리
        if file_path.is_dir():
            dart_dir = file_path
        elif self.dart_dir:
            dart_dir = self.dart_dir
        else:
            raise ValueError("DART directory not specified")
        
        if not dart_dir.exists():
            raise ValueError(f"DART directory not found: {dart_dir}")
        
        try:
            self.logger.info(f"Parsing DART data from: {dart_dir}")
            
            # 3개 CSV 파일 로드
            companies_df = self._load_csv(dart_dir / "companies.csv")
            disclosure_df = self._load_csv(dart_dir / "disclosure_states.csv")
            financial_df = self._load_csv(dart_dir / "financial_states.csv")
            
            # Knowledge Graph 생성
            kg = self._create_knowledge_graph(
                companies_df,
                disclosure_df,
                financial_df,
                dart_dir
            )
            
            self.logger.info(
                f"DART data parsed: {len(kg.entities)} entities, "
                f"{len(kg.relations)} relations"
            )
            
            return kg
            
        except Exception as e:
            self.logger.error(f"Failed to parse DART data: {str(e)}")
            raise ValueError(f"DART parsing failed: {str(e)}")
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        # 필수 키 확인
        if "entities" not in data or "relations" not in data:
            self.logger.warning("Missing entities or relations")
            return False
        
        # Company, Event, Metric 엔티티가 모두 있는지 확인
        entity_types = set(e.get("type") for e in data["entities"])
        required_types = {
            NodeType.COMPANY.value,
            NodeType.EVENT.value,
            NodeType.METRIC.value
        }
        
        if not required_types.issubset(entity_types):
            missing = required_types - entity_types
            self.logger.warning(f"Missing entity types: {missing}")
            return False
        
        return True
    
    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        """
        CSV 파일 로드
        
        Args:
            file_path: CSV 파일 경로
        
        Returns:
            DataFrame
        """
        if not file_path.exists():
            self.logger.warning(f"CSV not found: {file_path}, returning empty DataFrame")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path)
            self.logger.info(f"Loaded {file_path.name}: {len(df)} rows")
            return df
        except Exception as e:
            self.logger.error(f"Failed to load {file_path}: {str(e)}")
            return pd.DataFrame()
    
    def _create_knowledge_graph(
        self,
        companies_df: pd.DataFrame,
        disclosure_df: pd.DataFrame,
        financial_df: pd.DataFrame,
        source_dir: Path
    ) -> KnowledgeGraph:
        """
        3개 DataFrame을 Knowledge Graph로 변환
        
        Args:
            companies_df: 기업 데이터
            disclosure_df: 공시 데이터
            financial_df: 재무 데이터
            source_dir: 원본 디렉토리
        
        Returns:
            KnowledgeGraph 객체
        """
        entities = []
        relations = []
        
        # 1. Company 노드 생성 (정적 KG)
        companies = self._create_company_entities(companies_df)
        entities.extend(companies)
        
        # 2. Event 노드 생성 (동적 KG - 공시)
        events, event_relations = self._create_event_entities(
            disclosure_df,
            companies_df,
            str(source_dir)
        )
        entities.extend(events)
        relations.extend(event_relations)
        
        # 3. Metric 노드 생성 (동적 KG - 재무)
        metrics, metric_relations = self._create_metric_entities(
            financial_df,
            companies_df,
            str(source_dir)
        )
        entities.extend(metrics)
        relations.extend(metric_relations)
        
        # Knowledge Graph 생성
        kg = KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={
                "source_dir": str(source_dir),
                "file_type": "dart_csv",
                "num_companies": len(companies),
                "num_events": len(events),
                "num_metrics": len(metrics)
            }
        )
        
        return kg
    
    def _create_company_entities(
        self,
        companies_df: pd.DataFrame
    ) -> List[Entity]:
        """
        Company 엔티티 생성 (정적 KG)
        
        Args:
            companies_df: companies.csv DataFrame
        
        Returns:
            Company Entity 리스트
        """
        entities = []
        
        if companies_df.empty:
            return entities
        
        for idx, row in companies_df.iterrows():
            ticker = str(row.get('ticker', '')).strip()
            corp_name = str(row.get('corp_name', '')).strip()
            
            if not ticker or not corp_name:
                continue
            
            # Entity 정규화
            normalized_name = self.normalizer.normalize_entity(corp_name)
            
            entity = Entity(
                name=normalized_name,
                type=NodeType.COMPANY,
                properties={
                    "ticker": ticker,
                    "corp_code": str(row.get('corp_code', '')),
                    "corp_name": corp_name,
                    "original_name": corp_name
                },
                confidence=1.0
            )
            entities.append(entity)
        
        return entities
    
    def _create_event_entities(
        self,
        disclosure_df: pd.DataFrame,
        companies_df: pd.DataFrame,
        source: str
    ) -> tuple[List[Entity], List[Relation]]:
        """
        Event 엔티티 생성 (동적 KG - 공시)
        
        Args:
            disclosure_df: disclosure_states.csv DataFrame
            companies_df: companies.csv DataFrame (ticker 매핑용)
            source: 소스 경로
        
        Returns:
            (Event Entity 리스트, Relation 리스트)
        """
        entities = []
        relations = []
        
        if disclosure_df.empty:
            return entities, relations
        
        # ticker -> corp_name 매핑 생성
        ticker_map = {}
        if not companies_df.empty:
            for idx, row in companies_df.iterrows():
                ticker = str(row.get('ticker', '')).strip()
                corp_name = str(row.get('corp_name', '')).strip()
                if ticker and corp_name:
                    ticker_map[ticker] = self.normalizer.normalize_entity(corp_name)
        
        for idx, row in disclosure_df.iterrows():
            ticker = str(row.get('ticker', '')).strip()
           
            if not ticker:
                continue
            
            # 날짜 파싱
            date = self._parse_date(row.get('date', ''))
            if not date:
                continue
            
            # Event 엔티티
            event_name = f"Disclosure_{ticker}_{date}"
            event_entity = Entity(
                name=event_name,
                type=NodeType.EVENT,
                properties={
                    "ticker": ticker,
                    "date": date,
                    "event_type": "공시",
                    "title": str(row.get('title', ''))[:200],  # 제목 200자 제한
                    "disclosure_type": str(row.get('type', '')),
                },
                confidence=1.0
            )
            entities.append(event_entity)
            
            # Company-[:AFFECTED_BY]->Event 관계
            company_name = ticker_map.get(ticker, ticker)
            relation = Relation(
                subject=company_name,
                predicate=RelationType.AFFECTED_BY,
                object=event_name,
                weight=1.0,
                source=source
            )
            relations.append(relation)
        
        return entities, relations
    
    def _create_metric_entities(
        self,
        financial_df: pd.DataFrame,
        companies_df: pd.DataFrame,
        source: str
    ) -> tuple[List[Entity], List[Relation]]:
        """
        Metric 엔티티 생성 (동적 KG - 재무)
        
        Args:
            financial_df: financial_states.csv DataFrame
            companies_df: companies.csv DataFrame
            source: 소스 경로
        
        Returns:
            (Metric Entity 리스트, Relation 리스트)
        """
        entities = []
        relations = []
        
        if financial_df.empty:
            return entities, relations
        
        # ticker -> corp_name 매핑
        ticker_map = {}
        if not companies_df.empty:
            for idx, row in companies_df.iterrows():
                ticker = str(row.get('ticker', '')).strip()
                corp_name = str(row.get('corp_name', '')).strip()
                if ticker and corp_name:
                    ticker_map[ticker] = self.normalizer.normalize_entity(corp_name)
        
        for idx, row in financial_df.iterrows():
            ticker = str(row.get('ticker', '')).strip()
            period = str(row.get('period', '')).strip()
            
            if not ticker or not period:
                continue
            
            # Metric 엔티티
            metric_name = f"Financial_{ticker}_{period}"
            metric_entity = Entity(
                name=metric_name,
                type=NodeType.METRIC,
                properties={
                    "ticker": ticker,
                    "period": period,
                    "revenue": float(row.get('revenue', 0)) if pd.notna(row.get('revenue')) else None,
                    "operating_profit": float(row.get('operating_profit', 0)) if pd.notna(row.get('operating_profit')) else None,
                    "net_income": float(row.get('net_income', 0)) if pd.notna(row.get('net_income')) else None,
                },
                confidence=1.0
            )
            entities.append(metric_entity)
            
            # Company-[:HAS_METRIC]->Metric 관계
            company_name = ticker_map.get(ticker, ticker)
            relation = Relation(
                subject=company_name,
                predicate=RelationType.HAS_METRIC,
                object=metric_name,
                weight=1.0,
                source=source
            )
            relations.append(relation)
        
        return entities, relations
    
    def _parse_date(self, date_str: Any) -> Optional[str]:
        """
        날짜 문자열 파싱
        
        Args:
            date_str: 날짜 문자열
        
        Returns:
            YYYY-MM-DD 형식 또는 None
        """
        if pd.isna(date_str):
            return None
        
        try:
            # pandas로 파싱 시도
            dt = pd.to_datetime(date_str)
            return dt.strftime('%Y-%m-%d')
        except:
            return None
