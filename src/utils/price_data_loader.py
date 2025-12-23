
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
    3. NLP Formatting: Converts raw price rows into LLM-friendly context strings.
    """
    
    def __init__(self, data_dir: str = "data/preprocessed/price"):
        self.data_dir = Path(data_dir)
        self._cache: Dict[str, pd.DataFrame] = {}
        
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
            
        # Try finding the file
        # Pattern 1: {ticker}_states.csv (Standard)
        file_path = self.data_dir / f"{ticker}_states.csv"
        
        if not file_path.exists():
            # Pattern 2: Maybe hidden file or slightly different name?
            # Creating a fallback search if needed, but strict naming is better for now.
            logger.warning(f"Price file not found: {file_path}")
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
        
        trend_kr = {
            "Uptrend": "상승 추세(Uptrend)",
            "Downtrend": "하락 추세(Downtrend)", 
            "Sideways": "보합세(Sideways)",
            "Unknown": "추세 불명"
        }.get(trend, trend)
        
        vol_kr = {
            "High": "높음(High)",
            "Medium": "보통(Medium)",
            "Low": "낮음(Low)",
            "Unknown": "불명"
        }.get(volatility, volatility)
        
        context = (
            f"{date} 기준, {ticker}의 시장 상황 요약:\n"
            f"- 추세: {trend_kr}가 지속되고 있었습니다.\n"
            f"- 변동성: 시장 변동성은 {vol_kr} 수준이었습니다.\n"
            f"- 등락: 전일 대비 약 {return_pct:.2f}% 변동했습니다."
        )
        
        return context
