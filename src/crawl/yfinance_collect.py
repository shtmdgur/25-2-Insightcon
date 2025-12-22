"""
yfinance 기반 시계열 및 재무 데이터 수집기 (통합 버전)

- 가격 시계열 수집: get_price_history
- 파생값 계산: 일간 수익률, z-score, 변동성
- SAX-DM 변환: sax_dm
- TimeSeriesState 생성: build_states
- 재무 데이터 수집: get_fundamentals (강화됨: PER, ROE, 마진 등 포함)

사용 예시:
python -m src.crawl.yfinance_collect --preset global_semis --start 2020-01-01 --end 2024-12-31 \
  --out-prices-dir data/raw/price --out-states-dir data/raw/states \
  --fundamentals-out data/raw/fund/global_semis_fundamentals.csv
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf


# ----------------------------
# 데이터 클래스
# ----------------------------
@dataclass
class TimeSeriesState:
    ticker: str
    date: str
    price: float
    sax_symbol: str
    trend: str
    volatility: str
    daily_return: float
    zscore: float


# ----------------------------
# 핵심 기능
# ----------------------------
def get_price_history(ticker: str, start: str, end: Optional[str] = None, interval: str = "1d") -> pd.DataFrame:
    """
    yfinance에서 가격 시계열 수집.
    """
    data = yf.Ticker(ticker).history(start=start, end=end, interval=interval, auto_adjust=False)
    if data.empty:
        raise ValueError(f"No data returned for {ticker} in [{start}, {end}]")

    data = (
        data.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        .reset_index()
    )
    data["date"] = pd.to_datetime(data["Date"]).dt.date.astype(str)
    data = data[["date", "open", "high", "low", "close", "volume"]]
    return data


def get_fundamentals(ticker: str) -> Dict[str, Optional[float]]:
    """
    yfinance info 기반 재무 데이터 추출 (상세 항목 수집).
    """
    info = yf.Ticker(ticker).info
    
    total_debt = info.get("totalDebt")
    interest_expense = info.get("interestExpense")
    
    cost_of_debt_est = None
    if interest_expense and total_debt and total_debt > 0:
        cost_of_debt_est = interest_expense / total_debt

    return {
        "ticker": ticker,
        "shortName": info.get("shortName"),
        "sector": info.get("sector"),
        "country": info.get("country"),
        "currency": info.get("currency"),
        
        # --- 규모 및 안정성 ---
        "marketCap": info.get("marketCap"),
        "totalDebt": total_debt,
        "totalCash": info.get("totalCash"),
        "debtToEquity": info.get("debtToEquity"),
        "currentRatio": info.get("currentRatio"),
        "quickRatio": info.get("quickRatio"),
        "cost_of_debt_est": cost_of_debt_est,

        # --- 수익성 ---
        "totalRevenue": info.get("totalRevenue"),
        "revenueGrowth": info.get("revenueGrowth"),
        "ebitda": info.get("ebitda"),
        "ebitdaMargins": info.get("ebitdaMargins"),
        "grossMargins": info.get("grossMargins"),
        "operatingMargins": info.get("operatingMargins"),
        "profitMargins": info.get("profitMargins"),
        "returnOnEquity": info.get("returnOnEquity"),
        "returnOnAssets": info.get("returnOnAssets"),

        # --- 밸류에이션 ---
        "trailingPE": info.get("trailingPE"),
        "forwardPE": info.get("forwardPE"),
        "pegRatio": info.get("pegRatio"),
        "priceToBook": info.get("priceToBook"),
        
        # --- 현금 흐름 ---
        "freeCashflow": info.get("freeCashflow"),
        "operatingCashflow": info.get("operatingCashflow"),
        "interestExpense": interest_expense,
    }


def sax_dm(values: pd.Series) -> List[str]:
    """
    SAX-DM 심볼 생성.
    """
    vals = values.to_numpy(dtype=float)
    if len(vals) < 2:
        return ["Unknown"] * len(vals)

    z = (vals - vals.mean()) / (vals.std() + 1e-9)
    mu = z.mean()
    lower = z[z <= mu]
    upper = z[z > mu]
    mu_lower = lower.mean() if len(lower) else mu
    mu_upper = upper.mean() if len(upper) else mu

    symbols: List[str] = []
    for v in z:
        if v <= mu_lower:
            symbols.append("D2")
        elif v <= mu:
            symbols.append("D1")
        elif v <= mu_upper:
            symbols.append("U1")
        else:
            symbols.append("U2")
    return symbols


def _label_trend(symbol: str) -> str:
    return "Uptrend" if symbol in ("U1", "U2") else "Downtrend"


def _label_volatility(ret_series: pd.Series) -> List[str]:
    sigma = ret_series.rolling(20).std()
    labels = []
    for v in sigma:
        if pd.isna(v):
            labels.append("Unknown")
        elif v < 0.01:
            labels.append("Low")
        elif v < 0.03:
            labels.append("Medium")
        else:
            labels.append("High")
    return labels


def build_states(df: pd.DataFrame, ticker: str, zscore_window: int = 60) -> List[TimeSeriesState]:
    """
    가격 DataFrame을 받아 TimeSeriesState 리스트 반환.
    """
    df = df.copy()
    df["return"] = df["close"].pct_change()
    df["zscore"] = (df["close"] - df["close"].rolling(zscore_window).mean()) / (df["close"].rolling(zscore_window).std() + 1e-9)
    df["sax_symbol"] = sax_dm(df["close"])
    df["trend"] = df["sax_symbol"].apply(_label_trend)
    df["volatility"] = _label_volatility(df["return"])

    states: List[TimeSeriesState] = []
    for _, row in df.dropna(subset=["return"]).iterrows():
        states.append(
            TimeSeriesState(
                ticker=ticker,
                date=str(row["date"]),
                price=float(row["close"]),
                sax_symbol=row["sax_symbol"],
                trend=row["trend"],
                volatility=row["volatility"],
                daily_return=float(row["return"]),
                zscore=float(row["zscore"]) if not pd.isna(row["zscore"]) else 0.0,
            )
        )
    return states


# ----------------------------
# 티커 프리셋 (모두 유지)
# ----------------------------
PRESET_TICKERS: Dict[str, List[str]] = {
    "samsung_related": [
        "005930.KS", "000660.KS", "000990.KS", "091160.KS", "102110.KS",
    ],
    "global_semis": [
        "NVDA", "TSM", "INTC", "MU", "ASML", "AMAT", "LRCX", "AVGO", "AMD", "QCOM", "TXN"
    ],
    "macro": [
        "^KS11", "^KQ11", "091160.KS", "102110.KS",
        "^GSPC", "^IXIC", "^DJI", "SOXX", "SMH",
        "USDKRW=X", "USDJPY=X", "USDCNH=X", "EURUSD=X",
        "^IRX", "^FVX", "^TNX", "^TYX",
        "000300.SS", "000001.SS",
    ],
}


# ----------------------------
# CLI 유틸
# ----------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch price data and build TimeSeriesState.")
    parser.add_argument("--ticker", help="단일 티커")
    parser.add_argument("--tickers", help="콤마구분 티커 목록")
    parser.add_argument("--preset", choices=list(PRESET_TICKERS.keys()), help="미리 정의된 티커 세트 사용")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD")
    parser.add_argument("--out-prices-dir", default=None, help="개별 주가 저장 폴더")
    parser.add_argument("--out-states-dir", default=None, help="개별 상태 저장 폴더")
    parser.add_argument("--fundamentals-out", default=None, help="재무제표 통합 CSV 저장 경로")
    
    args = parser.parse_args()

    tickers: List[str] = []
    if args.tickers:
        tickers.extend([t.strip() for t in args.tickers.split(",") if t.strip()])
    if args.ticker:
        tickers.append(args.ticker)
    if args.preset:
        tickers.extend(PRESET_TICKERS[args.preset])
    
    if not tickers:
        print("Error: 티커를 지정해야 합니다. (--ticker, --tickers, --preset)")
        return

    # 폴더 생성
    if args.out_prices_dir and not os.path.exists(args.out_prices_dir):
        os.makedirs(args.out_prices_dir)
    if args.out_states_dir and not os.path.exists(args.out_states_dir):
        os.makedirs(args.out_states_dir)
    if args.fundamentals_out:
        fund_dir = os.path.dirname(args.fundamentals_out)
        if fund_dir and not os.path.exists(fund_dir):
            os.makedirs(fund_dir)

    fundamentals: List[Dict[str, Optional[float]]] = []

    for t in tickers:
        print(f"Processing {t}...")
        try:
            # 1. 가격 데이터 수집
            if args.out_prices_dir or args.out_states_dir:
                prices = get_price_history(t, start=args.start, end=args.end)
                
                if args.out_prices_dir:
                    price_path = os.path.join(args.out_prices_dir, f"{t}_prices.csv")
                    prices.to_csv(price_path, index=False)
                    print(f"  -> Saved prices: {price_path}")

                if args.out_states_dir:
                    states = build_states(prices, ticker=t)
                    state_path = os.path.join(args.out_states_dir, f"{t}_states.csv")
                    pd.DataFrame([s.__dict__ for s in states]).to_csv(state_path, index=False)
                    print(f"  -> Saved states: {state_path}")
            
            # 2. 재무 데이터 수집
            if args.fundamentals_out:
                try:
                    fund_data = get_fundamentals(t)
                    fundamentals.append(fund_data)
                    print(f"  -> Fetched fundamentals")
                except Exception as e:
                    print(f"  [Warn] Failed to fetch fundamentals for {t}: {e}")

        except Exception as e:
            print(f"  [Error] Failed processing {t}: {e}")
            continue

    if args.fundamentals_out and fundamentals:
        fund_df = pd.DataFrame(fundamentals)
        fund_df.to_csv(args.fundamentals_out, index=False)
        print(f"\nSaved ALL fundamentals to -> {args.fundamentals_out}")

if __name__ == "__main__":
    main()