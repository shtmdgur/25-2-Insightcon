"""
Fund Parser Agent

펀더멘탈 데이터 CSV 파일을 Knowledge Graph로 변환합니다.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
import pandas as pd

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph, Entity, Relation, NodeType, RelationType
from src.utils.entity_matcher import get_entity_matcher
from src.utils.ticker_mapping import get_company_name, get_node_type

logger = logging.getLogger(__name__)


class FundParserAgent(BaseParserAgent):
    """
    펀더멘탈 데이터 파싱 Agent
    
    데이터 레이어: 정적(Company 속성) + 동적(Metric 스냅샷)
    Neo4j 전략: Company=MERGE, Metric=CREATE
    """
    
    def __init__(self, save_as_snapshot: bool = False):
        """
        Args:
            save_as_snapshot: True면 Metric 노드로 저장 (동적), False면 Company 속성 업데이트 (정적)
        """
        super().__init__(name="FundParserAgent")
        self.save_as_snapshot = save_as_snapshot
        self.entity_matcher = get_entity_matcher()
    
    def parse(self, file_path: Path) -> KnowledgeGraph:
        """
        펀더멘탈 CSV를 파싱하여 Knowledge Graph 추출
        
        Args:
            file_path: CSV 파일 경로 (fund/*.csv)
        
        Returns:
            KnowledgeGraph 객체 (Company 또는 Metric 노드)
        
        Raises:
            ValueError: CSV 파싱 실패 시
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.csv':
            raise ValueError(f"Not a CSV file: {file_path}")
        
        try:
            self.logger.info(f"Parsing fund CSV: {file_path}")
            
            # CSV 로드
            df = pd.read_csv(file_path)
            
            # 필수 컬럼 검증
            self._validate_columns(df)
            
            # Knowledge Graph 생성
            kg = self._create_knowledge_graph(df, file_path)
            
            self.logger.info(
                f"Fund CSV parsed: {len(kg.entities)} entities, "
                f"{len(kg.relations)} relations"
            )
            
            return kg
            
        except Exception as e:
            self.logger.error(f"Failed to parse fund CSV {file_path}: {str(e)}")
            raise ValueError(f"Fund CSV parsing failed: {str(e)}")
    
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
        
        # Agent 또는 Earnings 엔티티 확인 (현재 스키마)
        agent_types = {NodeType.IDM.value, NodeType.FABLESS.value, NodeType.FOUNDRY.value, NodeType.SUPPLIER.value}
        has_entities = any(
            e.get("type") in agent_types or e.get("type") == NodeType.EARNINGS.value
            for e in data["entities"]
        )
        
        if not has_entities:
            self.logger.warning("No Agent or Earnings entities found")
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
        
        required = ["ticker"]
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
            df: Fund DataFrame
            file_path: 원본 파일 경로
        
        Returns:
            KnowledgeGraph 객체
        """
        entities = []
        relations = []
        
        # 컬럼명 소문자로 정규화
        df.columns = [col.lower() for col in df.columns]
        
        for idx, row in df.iterrows():
            ticker = str(row.get('ticker', '')).strip()
            # KR 주식의 경우 6자리 숫자로 패딩 (leading zero 보존)
            if ticker.isdigit() and len(ticker) < 6:
                ticker = ticker.zfill(6)
            short_name = str(row.get('shortname', '')).strip()
            
            if not ticker:
                continue
            
            # 회사명 결정 (shortName 우선, 없으면 ticker→회사명 매핑)
            company_name = short_name if short_name else get_company_name(ticker)
            
            # NodeType 자동 분류
            node_type = get_node_type(company_name)
            
            # 옵션 A: Company 노드 속성 업데이트 (정적 KG) - Hybrid KG 권장
            if not self.save_as_snapshot:
                company_entity = Entity(
                    name=company_name,
                    type=node_type,
                    properties={
                        "ticker": ticker,
                        "sector": str(row.get('sector', '')) if pd.notna(row.get('sector')) else None,
                        "country": str(row.get('country', '')) if pd.notna(row.get('country')) else None,
                    },
                    fundamental_stats={
                        "market_cap": float(row.get('marketcap', 0)) if pd.notna(row.get('marketcap')) else None,
                        "total_revenue": float(row.get('totalrevenue', 0)) if pd.notna(row.get('totalrevenue')) else None,
                        "total_debt": float(row.get('totaldebt', 0)) if pd.notna(row.get('totaldebt')) else None,
                        "ebitda_margins": float(row.get('ebitdamargins', 0)) if pd.notna(row.get('ebitdamargins')) else None,
                        "gross_margins": float(row.get('grossmargins', 0)) if pd.notna(row.get('grossmargins')) else None,
                        "profit_margins": float(row.get('profitmargins', 0)) if pd.notna(row.get('profitmargins')) else None,
                        "roe": float(row.get('returnonequity', 0)) if pd.notna(row.get('returnonequity')) else None,
                        "roa": float(row.get('returnonassets', 0)) if pd.notna(row.get('returnonassets')) else None,
                        "pe_ratio": float(row.get('trailingpe', 0)) if pd.notna(row.get('trailingpe')) else None,
                        "pb_ratio": float(row.get('pricetobook', 0)) if pd.notna(row.get('pricetobook')) else None,
                    },
                    confidence=1.0
                )
                entities.append(company_entity)
            
            # 옵션 B: Earnings 노드로 펀더멘탈 스냅샷 저장 (동적 KG)
            else:
                from datetime import datetime
                date_str = datetime.now().strftime('%Y-%m-%d')
                
                # 1. Company 노드 생성 (필수: 관계의 주체가 되어야 함)
                # 정적 정보도 함께 업데이트
                company_entity = Entity(
                    name=company_name,
                    type=node_type,
                    properties={
                        "ticker": ticker,
                        "sector": str(row.get('sector', '')) if pd.notna(row.get('sector')) else None,
                        "country": str(row.get('country', '')) if pd.notna(row.get('country')) else None,
                    },
                    confidence=1.0
                )
                entities.append(company_entity)
                
                # 2. Earnings 노드 생성
                fundamentals_entity = Entity(
                    name=f"Fundamentals_{company_name}_{date_str}",
                    type=NodeType.EARNINGS,  # METRIC → EARNINGS
                    properties={
                        "ticker": ticker,
                        "company_name": company_name,
                        "date": date_str,
                        "metric_type": "fundamentals",
                        "is_fundamentals_snapshot": True,
                        "marketCap": float(row.get('marketcap', 0)) if pd.notna(row.get('marketcap')) else None,
                        "totalDebt": float(row.get('totaldebt', 0)) if pd.notna(row.get('totaldebt')) else None,
                        "profitMargins": float(row.get('profitmargins', 0)) if pd.notna(row.get('profitmargins')) else None,
                        "ROE": float(row.get('returnonequity', 0)) if pd.notna(row.get('returnonequity')) else None,
                    },
                    confidence=1.0
                )
                entities.append(fundamentals_entity)
                
                # 3. 관계 생성
                relation = Relation(
                    subject=company_name,
                    predicate=RelationType.HAS_SIGNAL,
                    object=fundamentals_entity.name,
                    date=date_str,
                    source=str(file_path),
                    properties={
                        "weight": 1.0
                    },
                    confidence=1.0
                )
                relations.append(relation)
        
        # Knowledge Graph 생성
        kg = KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={
                "source_file": str(file_path),
                "file_type": "fund_csv",
                "num_companies": len(entities),
                "save_mode": "snapshot" if self.save_as_snapshot else "property_update"
            }
        )
        
        return kg
