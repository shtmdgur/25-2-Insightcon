
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class PriceDataLoader:
    """
    Price DB (CSV) Loader & Natural Language Formatter
    
    Roles:
    1. Lazy Load: Reads CSVs from `data/preprocessed/price/` only when needed.
    2. Caching: Stores loaded DataFrames in memory to minimize I/O.
    3. NLP Formatting: Converts raw price rows (Reviewing SAX patterns) into LLM-friendly context strings.
    """
    
    def __init__(self, data_dir: str = "data/preprocessed/price"):
        self.data_dir = Path(data_dir)
        self._cache: Dict[str, pd.DataFrame] = {}
        self._entity_matcher = None  # Lazy load
    
    def _resolve_ticker(self, name_or_ticker: str) -> str:
        """
        기업명 또는 ticker를 실제 ticker로 변환
        
        Args:
            name_or_ticker: 기업명(삼성전자) 또는 ticker(005930.KS)
            
        Returns:
            ticker (005930.KS)
        """
        # 이미 ticker 형식인 경우 그대로 반환
        if any(c.isdigit() for c in name_or_ticker) or name_or_ticker.startswith('^'):
            return name_or_ticker
        
        # EntityMatcher로 기업명 → ticker 변환
        try:
            if self._entity_matcher is None:
                from src.utils.entity_matcher import get_entity_matcher
                self._entity_matcher = get_entity_matcher()
            
            entity_info = self._entity_matcher.get_entity_info(name_or_ticker)
            if entity_info and entity_info.get('ticker'):
                ticker = entity_info['ticker']
                # .KS 확장자 추가 (한국 주식의 경우)
                if ticker.isdigit():
                    ticker = f"{ticker}.KS"
                return ticker
        except Exception as e:
            logger.debug(f"EntityMatcher failed for {name_or_ticker}: {e}")
        
        return name_or_ticker
        
    def get_context(self, ticker: str, date: str) -> str:
        """
        Retrieves market context for a specific ticker and date in natural language.
        
        Args:
            ticker (str): Ticker symbol (e.g., "005930.KS", "^KQ11")
            date (str): Date string in "YYYY-MM-DD" format
            
        Returns:
            str: Natural language summary of the market state.
                 Returns empty string if data is missing or not found.
        """
        try:
            # 1. Load Data (Lazy)
            df = self._load_data(ticker)
            if df is None:
                return ""
                
            # 2. Filter by Date
            row = df[df['date'] == date]
            if row.empty:
                return f"No price data available for {ticker} on {date}."
                
            # 3. Format to Natural Language
            return self._format_row(ticker, date, row.iloc[0])
            
        except Exception as e:
            logger.error(f"Error retrieving price context for {ticker} on {date}: {e}")
            return ""

    def _load_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Loads and caches dataframe for the given ticker."""
        if ticker in self._cache:
            return self._cache[ticker]
        
        # 기업명 → ticker 변환 시도 (삼성전자 → 005930.KS)
        actual_ticker = self._resolve_ticker(ticker)
            
        # Try finding the file
        # Pattern 1: {ticker}_states.csv (Standard)
        file_path = self.data_dir / f"{actual_ticker}_states.csv"
        
        if not file_path.exists():
            # Pattern 2: {ticker} only (without extension like .KS)
            base_ticker = actual_ticker.split('.')[0]
            file_path = self.data_dir / f"{base_ticker}_states.csv"
        
        if not file_path.exists():
            logger.debug(f"Price file not found: {file_path}")
            return None
            
        try:
            df = pd.read_csv(file_path)
            # Ensure date column is string for matching
            if 'date' in df.columns:
                df['date'] = df['date'].astype(str)
            self._cache[ticker] = df
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV {file_path}: {e}")
            return None

    def _format_row(self, ticker: str, date: str, row: pd.Series) -> str:
        """Converts a single DataFrame row into a descriptive string."""
        trend = row.get('trend', 'Unknown')
        volatility = row.get('volatility', 'Unknown')
        daily_return = row.get('daily_return', 0.0)
        
        # Format Return percentage
        try:
            return_pct = float(daily_return) * 100
            if return_pct > 0:
                price_move_desc = f"rose by {return_pct:.2f}%"
            elif return_pct < 0:
                price_move_desc = f"fell by {abs(return_pct):.2f}%"
            else:
                price_move_desc = "remained flat"
        except (ValueError, TypeError):
            price_move_desc = "showed unknown movement"

        # Build Description (Korean)
        # Using Korean as the primary language for the agent context as requested by user rules.
        
        # SAX Symbol Mapping
        sax_symbol = row.get('sax_symbol', 'Unknown')
        zscore = row.get('zscore', 0.0)
        price = row.get('price', 0.0)
        
        sax_desc_map = {
            "U2": "강한 상승 (Strong Uptrend)",
            "U1": "상승 (Uptrend)",
            "D1": "하락 (Downtrend)",
            "D2": "강한 하락 (Strong Downtrend)",
            "S": "횡보 (Sideways)",
            "Unknown": "불명"
        }
        sax_kr = sax_desc_map.get(sax_symbol, sax_symbol)
        
        # Z-Score Context
        try:
            z_val = float(zscore)
            if abs(z_val) > 2.0:
                z_desc = f"통계적으로 매우 유의미한 변동입니다 (Z-Score: {z_val:.2f}, 표준편차 2배 이상)."
            elif abs(z_val) > 1.0:
                z_desc = f"통계적으로 유의미한 변동입니다 (Z-Score: {z_val:.2f}, 표준편차 1배 이상)."
            else:
                z_desc = f"보통 수준의 변동입니다 (Z-Score: {z_val:.2f})."
        except (ValueError, TypeError):
            z_desc = "(Z-Score 정보 없음)"

        trend_kr = {
            "Uptrend": "상승 추세",
            "Downtrend": "하락 추세", 
            "Sideways": "보합세",
            "Unknown": "추세 불명"
        }.get(trend, trend)
        
        vol_kr = {
            "High": "높음(High)",
            "Medium": "보통(Medium)",
            "Low": "낮음(Low)",
            "Unknown": "불명"
        }.get(volatility, volatility)
        
        # Format Price
        try:
            price_val = float(price)
            price_str = f"{price_val:,.0f}원" if price_val > 500 else f"{price_val:,.2f}" # 대략적 통화 구분
        except:
            price_str = "가격 정보 없음"

        context = (
            f"{date} 기준, {ticker} 시장 상황 요약:\n"
            f"- 주가: {price_str} (전일 대비 {return_pct:+.2f}%)\n"
            f"- SAX 패턴: {sax_kr} - {z_desc}\n"
            f"- 추세/변동성: {trend_kr} / 변동성 {vol_kr}"
        )
        
        return context

    def get_context_range(self, ticker: str, start_date: str, end_date: str) -> str:
        """
        Retrieves market context for a date range, summarizing patterns.
        
        Args:
            ticker (str): Ticker symbol
            start_date (str): Start date "YYYY-MM-DD"
            end_date (str): End date "YYYY-MM-DD"
            
        Returns:
            str: Natural language summary of the period's market patterns.
        """
        try:
            df = self._load_data(ticker)
            if df is None:
                return f"No price data available for {ticker}."
            
            # Filter by date range
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            period_df = df[mask]
            
            if period_df.empty:
                return f"No price data for {ticker} between {start_date} and {end_date}."
            
            # Aggregate statistics
            total_days = len(period_df)
            
            # SAX pattern distribution
            sax_counts = period_df['sax_symbol'].value_counts().to_dict() if 'sax_symbol' in period_df.columns else {}
            
            # Trend distribution
            trend_counts = period_df['trend'].value_counts().to_dict() if 'trend' in period_df.columns else {}
            
            # Price change
            first_price = period_df.iloc[0].get('price', 0)
            last_price = period_df.iloc[-1].get('price', 0)
            try:
                period_return = ((float(last_price) - float(first_price)) / float(first_price)) * 100 if first_price else 0
            except:
                period_return = 0
            
            # Z-score extremes
            if 'zscore' in period_df.columns:
                max_z = period_df['zscore'].max()
                min_z = period_df['zscore'].min()
                extreme_z = f"Z-Score 범위: {min_z:.2f} ~ {max_z:.2f}"
            else:
                extreme_z = "(Z-Score 정보 없음)"
            
            # Format summary
            sax_summary = ", ".join([f"{k}: {v}일" for k, v in sax_counts.items()]) if sax_counts else "패턴 정보 없음"
            trend_summary = ", ".join([f"{k}: {v}일" for k, v in trend_counts.items()]) if trend_counts else "추세 정보 없음"
            
            context = (
                f"[{ticker}] {start_date} ~ {end_date} 기간 분석 ({total_days}일):\n"
                f"- 기간 수익률: {period_return:+.2f}%\n"
                f"- SAX 패턴 분포: {sax_summary}\n"
                f"- 추세 분포: {trend_summary}\n"
                f"- {extreme_z}"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error in get_context_range: {e}")
            return f"Error retrieving range data for {ticker}: {e}"

