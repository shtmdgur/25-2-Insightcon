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
from src.utils.time_series_processor import TimeSeriesProcessor
from src.utils.neo4j_client import Neo4jClient

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
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        # 필수 키 확인
        required_keys = ["entities", "relations"]
        for key in required_keys:
            if key not in data:
                self.logger.warning(f"Missing key: {key}")
                return False
        
        # Metric 또는 Trend 엔티티가 있는지 확인
        has_metric_or_trend = any(
            e.get("type") in [NodeType.METRIC.value, NodeType.TREND.value]
            for e in data["entities"]
        )
        
        if not has_metric_or_trend:
            self.logger.warning("No Metric or Trend entities found")
            return False
        
        return True
    
    def _extract_ticker(self, filename: str) -> str:
        """
        파일명에서 Ticker 추출
        
        Args:
            filename: 파일명 (예: 005930.KS_prices.csv, NVDA_prices.csv)
        
        Returns:
            Ticker 코드
        """
        # _prices.csv 제거
        name = filename.replace("_prices.csv", "")
        name = name.replace(".csv", "")
        
        # .KS, .KQ 등 제거
        name = name.split(".")[0]
        
        return name
    
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """
        CSV 필수 컬럼 검증
        
        Args:
            df: DataFrame
        
        Raises:
            ValueError: 필수 컬럼 누락 시
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
    
    def _create_knowledge_graph(
        self,
        df: pd.DataFrame,
        ticker: str,
        file_path: Path
    ) -> KnowledgeGraph:
        """
        DataFrame을 Knowledge Graph로 변환
        
        Args:
            df: 주가 DataFrame
            ticker: Ticker 코드
            file_path: 원본 파일 경로
        
        Returns:
            KnowledgeGraph 객체
        """
        entities = []
        relations = []
        
        # 컬럼명 소문자로 정규화
        df.columns = [col.lower() for col in df.columns]
        
        # 날짜 정렬
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # SAX 패턴 변환 (TimeSeriesProcessor 사용)
        sax_result = self._calculate_sax_pattern(df['close'].values, ticker)
        
        # 1. Trend 노드 생성 (동적 KG)
        trend_entity = Entity(
            name=f"Trend_{ticker}",
            type=NodeType.TREND,
            properties={
                "ticker": ticker,
                "period": f"{df['date'].min().strftime('%Y-%m-%d')}_{df['date'].max().strftime('%Y-%m-%d')}",
                "pattern": sax_result.get("pattern", "unknown"),
                "trend_type": sax_result.get("trend_type", "Unknown"),
                "data_points": len(df)
            },
            confidence=1.0
        )
        entities.append(trend_entity)
        
        # 2. 주가 Metric 노드 생성 (샘플링)
        from src.config.parser_config import get_config
        config = get_config('price')
        
        sample_size = min(
            config.sample_size,
            max(config.min_samples, int(len(df) * config.sample_ratio))
        )
        recent_df = df.tail(sample_size)
        
        for idx, row in recent_df.iterrows():
            metric_entity = Entity(
                name=f"StockPrice_{ticker}_{row['date'].strftime('%Y%m%d')}",
                type=NodeType.METRIC,
                properties={
                    "ticker": ticker,
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "close": float(row['close']),
                    "volume": int(row.get('volume', 0))  if 'volume' in df.columns else 0,
                    "open": float(row.get('open', row['close'])) if 'open' in df.columns else None,
                    "high": float(row.get('high', row['close'])) if 'high' in df.columns else None,
                    "low": float(row.get('low', row['close'])) if 'low' in df.columns else None,
                },
                confidence=1.0
            )
            entities.append(metric_entity)
            
            # 관계: Company-[:HAS_METRIC]->Metric
            # (Company 노드는 이미 존재한다고 가정)
            relation = Relation(
                subject=ticker,  # Company name
                predicate=RelationType.HAS_METRIC,
                object=metric_entity.name,
                weight=1.0,
                source=str(file_path)
            )
            relations.append(relation)
        
        # 3. Company-[:HAS_TREND]->Trend 관계
        trend_relation = Relation(
            subject=ticker,
            predicate=RelationType.HAS_TREND,
            object=trend_entity.name,
            weight=1.0,
            source=str(file_path)
        )
        relations.append(trend_relation)
        
        # Knowledge Graph 생성
        kg = KnowledgeGraph(
            entities=entities,
            relations=relations,
            metadata={
                "source_file": str(file_path),
                "file_type": "price_csv",
                "ticker": ticker,
                "start_date": df['date'].min().strftime('%Y-%m-%d'),
                "end_date": df['date'].max().strftime('%Y-%m-%d'),
                "total_data_points": len(df),
                "sampled_data_points": sample_size
            }
        )
        
        return kg
    
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
                ts=np.array(prices),
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
