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
from src.dataflows.entity_normalizer import get_entity_normalizer

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

    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        """
        CSV 파일 로드
        """
        if not file_path.exists():
            self.logger.warning(f"CSV not found: {file_path}, returning empty DataFrame")
            return pd.DataFrame()
        
        try:
            # Ticker와 Corp Code는 문자열로 강제 변환하여 앞자리 0 유지
            df = pd.read_csv(file_path, dtype={'ticker': str, 'corp_code': str})
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
        """
        entities = []
        relations = []
        
        # 1. Company 노드 생성 (정적 KG)
        companies = self._create_company_entities(companies_df)
        entities.extend(companies)
        
        # 2. Disclosure 노드 생성 (Signal Layer)
        disclosures, disclosure_relations = self._create_event_entities(
            disclosure_df,
            companies_df,
            str(source_dir)
        )
        entities.extend(disclosures)
        relations.extend(disclosure_relations)
        
        # 3. Earnings 노드 생성 (Signal Layer)
        earnings, earnings_relations = self._create_metric_entities(
            financial_df,
            companies_df,
            str(source_dir)
        )
        entities.extend(earnings)
        relations.extend(earnings_relations)
        
        # Knowledge Graph 생성
        kg = KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={
                "source_dir": str(source_dir),
                "file_type": "dart_csv"
            }
        )
        
        return kg
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        """
        if "entities" not in data or "relations" not in data:
            return False
        
        entity_types = set(e.get("type") for e in data["entities"])
        # Hybrid KG 모델에 맞는 타입 체크
        required_types = {
            NodeType.ORGANIZATION.value,
            NodeType.DISCLOSURE.value,
            NodeType.EARNINGS.value
        }
        
        # 최소한 하나 이상의 필수 타입이 있는지 확인 (엄격 모드 아님)
        if not any(t in entity_types for t in required_types):
            self.logger.warning(f"No Hybrid KG core entity types found in DART output: {entity_types}")
            return False
        
        return True

    def _create_company_entities(
        self,
        companies_df: pd.DataFrame
    ) -> List[Entity]:
        """
        Company 엔티티 생성 (정적 KG)
        """
        entities = []
        
        if companies_df.empty:
            return entities
        
        for idx, row in companies_df.iterrows():
            ticker = str(row.get('ticker', '')).strip().zfill(6)
            corp_name = str(row.get('corp_name', '')).strip()
            
            if not ticker or not corp_name:
                continue
            
            normalized_name_dict = self.normalizer.normalize_entity(corp_name)
            normalized_name = normalized_name_dict["canonical_name"]
            
            # TODO: 섹터 분류 기반으로 NodeType 결정 로직 추가 필요
            # 현재는 기본적으로 ORGANIZATION 또는 IDM 시도
            node_type = NodeType.IDM
            
            entity = Entity(
                name=normalized_name,
                type=node_type,
                properties={
                    "ticker": ticker,
                    "corp_code": str(row.get('corp_code', '')),
                    "corp_name": corp_name
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
        Disclosure 엔티티 생성 (Signal Layer)
        """
        entities = []
        relations = []
        
        if disclosure_df.empty:
            return entities, relations
        
        ticker_map = {}
        if not companies_df.empty:
            for idx, row in companies_df.iterrows():
                ticker = str(row.get('ticker', '')).strip().zfill(6)
                corp_name = str(row.get('corp_name', '')).strip()
                if ticker and corp_name:
                    norm_res = self.normalizer.normalize_entity(corp_name)
                    ticker_map[ticker] = norm_res["canonical_name"]
        
        for idx, row in disclosure_df.iterrows():
            ticker = str(row.get('ticker', '')).strip().zfill(6)
           
            if not ticker:
                continue
            
            date = self._parse_date(row.get('date', ''))
            if not date:
                continue
            
            report_nm = str(row.get('report_nm', row.get('title', '')))
            event_name = f"Disclosure_{ticker}_{date}"
            
            signal_entity = Entity(
                name=event_name,
                type=NodeType.DISCLOSURE,
                sentiment=self._classify_sentiment(report_nm),
                properties={
                    "ticker": ticker,
                    "date": date,
                    "report_nm": report_nm,
                    "disclosure_type": str(row.get('disclosure_type', row.get('type', '')))
                },
                confidence=1.0
            )
            entities.append(signal_entity)
            
            company_name = ticker_map.get(ticker, ticker)
            relation = Relation(
                subject=company_name,
                predicate=RelationType.HAS_SIGNAL,
                object=event_name,
                properties={"date": date}
            )
            relations.append(relation)
        
        return entities, relations

    def _classify_sentiment(self, report_name: str) -> str:
        """공시 유형별 Sentiment 분류"""
        positive_keywords = ["증설", "투자", "배당", "계약", "수주", "흑자", "특허"]
        negative_keywords = ["소송", "적자", "파산", "정정", "해고", "손실", "지연"]
        
        for keyword in positive_keywords:
            if keyword in report_name: return "POSITIVE"
        for keyword in negative_keywords:
            if keyword in report_name: return "NEGATIVE"
        return "NEUTRAL"
    
    def _create_metric_entities(
        self,
        financial_df: pd.DataFrame,
        companies_df: pd.DataFrame,
        source: str
    ) -> tuple[List[Entity], List[Relation]]:
        """
        Earnings 엔티티 생성 (Signal Layer)
        """
        entities = []
        relations = []
        
        if financial_df.empty:
            return entities, relations
        
        ticker_map = {}
        if not companies_df.empty:
            for idx, row in companies_df.iterrows():
                ticker = str(row.get('ticker', '')).strip().zfill(6)
                corp_name = str(row.get('corp_name', '')).strip()
                if ticker and corp_name:
                    norm_res = self.normalizer.normalize_entity(corp_name)
                    ticker_map[ticker] = norm_res["canonical_name"]
        
        for idx, row in financial_df.iterrows():
            ticker = str(row.get('ticker', '')).strip().zfill(6)
            period = str(row.get('period', '')).strip()
            
            if not ticker or not period:
                continue
            
            metric_name = f"Earnings_{ticker}_{period}"
            revenue = float(row.get('revenue', 0)) if pd.notna(row.get('revenue')) else 0
            op_profit = float(row.get('operating_profit', 0)) if pd.notna(row.get('operating_profit')) else 0
            
            sentiment = "POSITIVE" if op_profit > 0 else "NEGATIVE"
            
            metric_entity = Entity(
                name=metric_name,
                type=NodeType.EARNINGS,
                sentiment=sentiment,
                properties={
                    "ticker": ticker,
                    "period": period,
                    "revenue": revenue,
                    "operating_profit": op_profit,
                },
                confidence=1.0
            )
            entities.append(metric_entity)
            
            company_name = ticker_map.get(ticker, ticker)
            relation = Relation(
                subject=company_name,
                predicate=RelationType.HAS_SIGNAL,
                object=metric_name,
                properties={"period": period}
            )
            relations.append(relation)
        
        return entities, relations
    
    def _parse_date(self, date_str: Any) -> Optional[str]:
        """
        날짜 문자열 파싱
        
        Args:
            date_str: 날짜 문자열 (str, int, float)
        
        Returns:
            YYYY-MM-DD 형식 또는 None
        """
        if pd.isna(date_str):
            return None
            
        try:
            # 1. 입력값을 문자열로 변환 (int, float 대응)
            s = str(date_str).strip()
            
            # 1970-01-01 이슈 방지 (빈 문자열이나 0)
            if not s or s == '0' or s == '0.0':
                return None
                
            # 2. YYYYMMDD 형식 처리 (8자리 숫자)
            if len(s) == 8 and s.isdigit():
                return f"{s[:4]}-{s[4:6]}-{s[6:]}"
                
            # 3. pandas 파싱 시도
            dt = pd.to_datetime(s)
            
            # 1970-01-01 (Epoch 0) 체크 - 입력이 1970-01-01이 아닌데 결과가 그렇다면 무시
            if dt.year == 1970 and dt.month == 1 and dt.day == 1:
                # 원본이 '19700101'이 아니었다면 파싱 실패로 간주
                if '1970' not in s: 
                    return None
                    
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return None
