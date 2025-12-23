"""
Price Parser Agent

주가 시계열 CSV 파일을 Knowledge Graph로 변환합니다.
"""

from pathlib import Path
from typing import Dict, Any, List
import logging
import pandas as pd
from datetime import datetime

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph, Entity, Relation, NodeType, RelationType
from src.dataflows.time_series_processor import TimeSeriesProcessor
from src.utils.neo4j_client import Neo4jClient
from src.utils.ticker_mapping import get_company_name, get_node_type

logger = logging.getLogger(__name__)


class PriceParserAgent(BaseParserAgent):
    """
    주가 시계열 CSV 파싱 Agent
    
    데이터 레이어: 100% 동적 (Metric, Trend)
    Neo4j 전략: CREATE (시계열 생성)
    """
    
    def __init__(self, neo4j_uri: str = None, use_neo4j: bool = False):
        """
        Args:
            neo4j_uri: Neo4j 연결 URI (직접 주입 시)
            use_neo4j: Neo4j 직접 주입 여부 (False면 JSON만 생성)
        """
        super().__init__(name="PriceParserAgent")
        self.use_neo4j = use_neo4j
        
        if use_neo4j and neo4j_uri:
            self.neo4j_client = Neo4jClient(uri=neo4j_uri)
            self.ts_processor = TimeSeriesProcessor(self.neo4j_client)
        else:
            self.neo4j_client = None
            self.ts_processor = None
    
    def parse(self, file_path: Path) -> KnowledgeGraph:
        """
        주가 CSV를 파싱하여 Knowledge Graph 추출
        
        Args:
            file_path: CSV 파일 경로 (예: 005930.KS_prices.csv)
        
        Returns:
            KnowledgeGraph 객체 (Metric + Trend 노드)
        
        Raises:
            ValueError: CSV 파싱 실패 또는 필수 컬럼 누락 시
        """
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.csv':
            raise ValueError(f"Not a CSV file: {file_path}")
        
        try:
            self.logger.info(f"Parsing price CSV: {file_path}")
            
            # Ticker 추출 (파일명에서)
            ticker = self._extract_ticker(file_path.name)
            
            # CSV 로드
            df = pd.read_csv(file_path)
            
            # 필수 컬럼 검증
            self._validate_columns(df)
            
            # Knowledge Graph 생성
            kg = self._create_knowledge_graph(df, ticker, file_path)
            
            self.logger.info(
                f"Price CSV parsed: {len(kg.entities)} entities, "
                f"{len(kg.relations)} relations"
            )
            
            return kg
            
        except Exception as e:
            self.logger.error(f"Failed to parse price CSV {file_path}: {str(e)}")
            raise ValueError(f"Price CSV parsing failed: {str(e)}")

    def _extract_ticker(self, filename: str) -> str:
        """
        파일명에서 Ticker 추출
        """
        # _prices.csv 제거
        name = filename.replace("_prices.csv", "")
        name = name.replace(".csv", "")
        
        # .KS, .KQ 등 제거
        name = name.split(".")[0]
        
        # KR 주식의 경우 6자리 숫자로 패딩 (leading zero 보존)
        if name.isdigit() and len(name) < 6:
            name = name.zfill(6)
            
        return name
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        CSV 필수 컬럼 검증
        """
        # 소문자로 변환하여 검증 (대소문자 무시)
        columns_lower = [col.lower() for col in df.columns]
        
        required = ["date", "close"]
        missing = [col for col in required if col not in columns_lower]
        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # 데이터가 비어있는지 확인
        if len(df) == 0:
            raise ValueError("CSV file is empty")
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        """
        if "entities" not in data or "relations" not in data:
            return False
        
        entity_types = set(e.get("type") for e in data["entities"])
        # Hybrid KG 모델에 맞는 타입 체크 (TREND → ISSUE로 대체)
        required_types = {
            NodeType.PRICE_MOVEMENT.value,
            NodeType.ISSUE.value  # Trend는 Issue로 저장됨 (is_trend=True)
        }
        
        if not any(t in entity_types for t in required_types):
            self.logger.warning(f"No Price Signal types found: {entity_types}")
            return False
        
        return True

    def _create_knowledge_graph(
        self,
        df: pd.DataFrame,
        ticker: str,
        file_path: Path
    ) -> KnowledgeGraph:
        """
        DataFrame을 Knowledge Graph로 변환
        """
        entities = []
        relations = []
        
        df.columns = [col.lower() for col in df.columns]
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 1. 전체 기간 트렌드를 Issue로 저장 (SAX 패턴 요약)
        sax_result = self._calculate_sax_pattern(df['close'].values, ticker)
        trend_issue = Entity(
            name=f"Trend_{ticker}_{df['date'].max().strftime('%Y%m%d')}",
            type=NodeType.ISSUE,
            properties={
                "ticker": ticker,
                "pattern": sax_result.get("pattern"),
                "trend_type": sax_result.get("trend_type"),
                "is_trend": True  # Issue 중 Trend 구분용
            },
            confidence=1.0
        )
        entities.append(trend_issue)
        
        # 1.5 Agent 노드 생성 (ticker_mapping 활용)
        agent_name = get_company_name(ticker)
        agent_type = get_node_type(agent_name)
        
        agent_entity = Entity(
            name=agent_name,
            type=agent_type,
            properties={"ticker": ticker},
            confidence=1.0
        )
        entities.append(agent_entity)
        
        # 2. Price Movement Signals (±5% 이상 변동 탐지)
        movements = self._detect_price_movements(df, ticker)
        entities.extend(movements)
        
        # 3. 관계 생성
        # TODO: 실제 Agent 이름을 알 수 없는 경우 Ticker 유지
        # 3. 관계 생성
        # Agent 이름 사용
        for m in movements:
            relations.append(Relation(
                subject=agent_name,
                predicate=RelationType.HAS_SIGNAL,
                object=m.name,
                date=m.properties.get("date"),
                source=str(file_path),
                properties={
                    "weight": 1.0
                }
            ))
            
        relations.append(Relation(
            subject=agent_name,
            predicate=RelationType.HAS_SIGNAL,  # HAS_TREND → HAS_SIGNAL (v3.0)
            object=trend_issue.name,  # trend_entity → trend_issue
            date=df['date'].max().strftime('%Y-%m-%d'),
            source=str(file_path),
            properties={
                "weight": 1.0,
                "is_trend": True
            }
        ))
        
        return KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={"ticker": ticker}
        )

    def _detect_price_movements(self, df: pd.DataFrame, ticker: str, threshold: float = 5.0) -> List[Entity]:
        """주가 급등/급락 탐지 (±5% 이상 변동만)"""
        signals = []
        df['pct_change'] = df['close'].pct_change() * 100
        
        for idx, row in df.iterrows():
            # NaN 값 건너뛰기 (첫 번째 행은 항상 NaN)
            if pd.isna(row['pct_change']):
                continue
            
            # ±5% 이상 변동만 감지
            if abs(row['pct_change']) >= threshold:
                signal = Entity(
                    name=f"PriceMovement_{ticker}_{row['date'].strftime('%Y%m%d')}",
                    type=NodeType.PRICE_MOVEMENT,
                    direction="UP" if row['pct_change'] > 0 else "DOWN",
                    magnitude=abs(row['pct_change']),
                    sentiment="POSITIVE" if row['pct_change'] > 0 else "NEGATIVE",
                    properties={
                        "date": row['date'].strftime('%Y-%m-%d'),
                        "close": float(row['close']),
                        "pct_change": float(row['pct_change'])
                    },
                    confidence=1.0
                )
                signals.append(signal)
        
        self.logger.info(f"Detected {len(signals)} price movements for {ticker} (threshold={threshold}%)")
        return signals
    
    def _calculate_sax_pattern(
        self,
        prices: List[float],
        ticker: str
    ) -> Dict[str, Any]:
        """
        SAX 패턴 계산 (TimeSeriesProcessor 사용 or Fallback)
        
        Args:
            prices: 주가 리스트
            ticker: Ticker 코드
        
        Returns:
            SAX 결과 {'pattern': str, 'trend_type': str}
        """
        try:
            # saxpy 사용 시도
            from saxpy.sax import sax_via_window
            import numpy as np
            from src.config.parser_config import get_config
            
            config = get_config('price')
            
            sax_string = sax_via_window(
                np.array(prices),
                win_size=config.sax_window_size,
                paa_size=config.sax_paa_size,
                alphabet_size=config.sax_alphabet_size,
                nr_strategy='normal'
            )
            
            # 트렌드 분류
            trend_type = self._classify_trend_simple(prices)
            
            return {
                "pattern": str(sax_string),
                "trend_type": trend_type
            }
            
        except ImportError:
            self.logger.warning("saxpy not installed. Using simple classification.")
            return {
                "pattern": "simple",
                "trend_type": self._classify_trend_simple(prices)
            }
        except Exception as e:
            self.logger.warning(f"SAX calculation failed: {str(e)}")
            return {
                "pattern": "unknown",
                "trend_type": "Unknown"
            }
    
    def _classify_trend_simple(self, prices: List[float]) -> str:
        """
        간단한 트렌드 분류
        
        Args:
            prices: 주가 리스트
        
        Returns:
            트렌드 타입 (Upward/Downward/Stable/Volatile)
        """
        if len(prices) < 2:
            return "Stable"
        
        import numpy as np
        from src.config.parser_config import get_config
        
        config = get_config('price')
        
        # 변동성 계산
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        
        # 방향성 계산
        trend = (prices[-1] - prices[0]) / prices[0]
        
        # 분류
        if volatility > config.volatility_threshold:
            return "Volatile"
        elif trend > config.upward_threshold:
            return "Upward"
        elif trend < config.downward_threshold:
            return "Downward"
        else:
            return "Stable"
