"""
시계열 데이터 처리 (SAX 패턴 변환)

주가 데이터를 패턴으로 변환하여 Neo4j에 저장합니다.
"""
import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class TimeSeriesProcessor:
    """
    시계열 데이터를 SAX 패턴으로 변환
    
    SAX (Symbolic Aggregate approXimation)를 사용하여
    시계열 데이터를 문자열 패턴으로 변환합니다.
    """
    
    def __init__(self, neo4j_client):
        """
        Args:
            neo4j_client: Neo4j 클라이언트
        """
        self.neo4j_client = neo4j_client
    
    def process_stock_price(
        self,
        company_ticker: str,
        prices: List[float],
        period: str,
        window_size: int = 5
    ) -> Dict[str, Any]:
        """
        주가 시계열을 SAX로 변환하여 Neo4j에 저장
        
        Args:
            company_ticker: 기업 종목 코드
            prices: 주가 리스트
            period: 기간 (예: "2024-Q4")
            window_size: 윈도우 크기
        
        Returns:
            처리 결과
        """
        if len(prices) < window_size:
            logger.warning(f"Not enough data points: {len(prices)} < {window_size}")
            return {"error": "insufficient_data"}
        
        try:
            # SAX 패턴 변환
            from saxpy.sax import sax_via_window
            
            sax_string = sax_via_window(
                ts=np.array(prices),
                win_size=window_size,
                paa_size=3,
                alphabet_size=5,
                nr_strategy='normal'
            )
            
        except ImportError:
            logger.warning("saxpy not installed. Using simple trend classification.")
            sax_string = self._simple_trend_classification(prices)
        except Exception as e:
            logger.error(f"SAX conversion failed: {str(e)}")
            sax_string = "unknown"
        
        # 트렌드 분류
        trend_type = self._classify_trend(sax_string, prices)
        
        # Neo4j에 Trend 노드 생성
        try:
            self.neo4j_client.run("""
                MATCH (c:Company {ticker: $ticker})
                MERGE (t:Trend {
                    period: $period,
                    company_ticker: $ticker
                })
                SET t.pattern = $sax_string,
                    t.trend_type = $trend_type,
                    t.last_updated = datetime()
                MERGE (c)-[:HAS_TREND]->(t)
            """, {
                "ticker": company_ticker,
                "period": period,
                "sax_string": str(sax_string),
                "trend_type": trend_type
            })
            
            logger.info(f"Saved trend for {company_ticker} ({period}): {trend_type}")
            
            return {
                "ticker": company_ticker,
                "period": period,
                "pattern": str(sax_string),
                "trend_type": trend_type
            }
            
        except Exception as e:
            logger.error(f"Failed to save trend to Neo4j: {str(e)}")
            return {"error": str(e)}
    
    def _simple_trend_classification(self, prices: List[float]) -> str:
        """
        SAX 없이 간단한 트렌드 분류
        
        Args:
            prices: 주가 리스트
        
        Returns:
            간단한 패턴 문자열
        """
        if len(prices) < 2:
            return "flat"
        
        # 시작과 끝 비교
        if prices[-1] > prices[0] * 1.1:
            return "up"
        elif prices[-1] < prices[0] * 0.9:
            return "down"
        else:
            return "flat"
    
    def _classify_trend(self, sax_string: str, prices: List[float]) -> str:
        """
        SAX 패턴 기반 트렌드 분류
        
        Args:
            sax_string: SAX 패턴
            prices: 원본 주가 데이터
        
        Returns:
            트렌드 타입 (Upward, Downward, Volatile, Stable)
        """
        if len(prices) < 2:
            return "Stable"
        
        # 변동성 계산
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns)
        
        # 방향성 계산
        trend = (prices[-1] - prices[0]) / prices[0]
        
        # 분류
        if volatility > 0.05:
            return "Volatile"
        elif trend > 0.1:
            return "Upward"
        elif trend < -0.1:
            return "Downward"
        else:
            return "Stable"
