"""
yfinance 기반 시계열 수집 및 TimeSeriesState 생성 도우미.

- 가격 시계열 수집: get_price_history
- 파생값 계산: 일간 수익률, z-score, 변동성
- SAX-DM 변환: sax_dm
- TimeSeriesState 생성: build_states

사용 예시 (모듈 실행):
python -m src.crawl.yfinance --preset macro --start 2020-01-01 --end 2025-09-14 \
  --out-prices-dir data/raw/price --out-states-dir data/raw/states \
  --fundamentals-out data/raw/fund/macro_fundamentals.csv
"""

from __future__ import annotations

import argparse
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
    반환 컬럼: date, open, high, low, close, volume
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
    yfinance info 기반 기본 재무/채무 비용 추출.
    cost_of_debt_est는 이자비용 / 총부채로 단순 추정.
    """
    info = yf.Ticker(ticker).info
    total_debt = info.get("totalDebt")
    interest_expense = info.get("interestExpense")
    cost_of_debt_est = None
    if interest_expense and total_debt and total_debt > 0:
        cost_of_debt_est = interest_expense / total_debt

    return {
        "ticker": ticker,
        "currency": info.get("currency"),
        "marketCap": info.get("marketCap"),
        "totalDebt": total_debt,
        "totalCash": info.get("totalCash"),
        "totalRevenue": info.get("totalRevenue"),
        "ebitda": info.get("ebitda"),
        "interestExpense": interest_expense,
        "debtToEquity": info.get("debtToEquity"),
        "freeCashflow": info.get("freeCashflow"),
        "operatingCashflow": info.get("operatingCashflow"),
        "quickRatio": info.get("quickRatio"),
        "currentRatio": info.get("currentRatio"),
        "cost_of_debt_est": cost_of_debt_est,
    }


def sax_dm(values: pd.Series) -> List[str]:
    """
    SAX-DM 심볼 생성 (U2/U1/D1/D2).
    """
    vals = values.to_numpy(dtype=float)
    z = (vals - vals.mean()) / vals.std()
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
    가격 DataFrame(date, close[, volume])을 받아 TimeSeriesState 리스트 반환.
    """
    df = df.copy()
    df["return"] = df["close"].pct_change()
    df["zscore"] = (df["close"] - df["close"].rolling(zscore_window).mean()) / df["close"].rolling(
        zscore_window
    ).std()
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
# 기본 티커 프리셋 (삼성/반도체/거시 확장)
# ----------------------------
PRESET_TICKERS: Dict[str, List[str]] = {
    "samsung_related": [
        "005930.KS",  # 삼성전자
        "000660.KS",  # SK하이닉스
        "000990.KS",  # DB하이텍
        "091160.KS",  # TIGER 반도체 ETF
        "102110.KS",  # KODEX 반도체 ETF
    ],
    "global_semis": [
        "NVDA",
        "TSM",
        "INTC",
        "MU",
        "ASML",
        "AMAT",
        "LRCX",
        "AVGO",
    ],
    "macro": [
        # 한국/섹터/ETF
        "^KS11",     # KOSPI
        "^KQ11",     # KOSDAQ (없다면 건너뜀)
        "091160.KS", # TIGER 반도체 ETF
        "102110.KS", # KODEX 반도체 ETF
        # 미국 지수/섹터
        "^GSPC",     # S&P500
        "^IXIC",     # NASDAQ
        "^DJI",      # Dow
        "SOXX",      # 미국 반도체 ETF
        "SMH",       # 미국 반도체 ETF
        # 환율 (주요국)
        "USDKRW=X",
        "USDJPY=X",
        "USDCNH=X",
        "EURUSD=X",
        # 금리 (미국채)
        "^IRX",      # 13주
        "^FVX",      # 5년
        "^TNX",      # 10년
        "^TYX",      # 30년
        # 중국/수출 관련 지표
        "000300.SS", # CSI 300
        "000001.SS", # SSE Composite
    ],
}


# ----------------------------
# CLI 유틸
# ----------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch price data and build TimeSeriesState via yfinance.")
    parser.add_argument("--ticker", help="단일 티커. 예: 005930.KS")
    parser.add_argument("--tickers", help="콤마구분 티커 목록. 예: 005930.KS,000660.KS,NVDA")
    parser.add_argument(
        "--preset",
        choices=list(PRESET_TICKERS.keys()),
        help=f"미리 정의된 티커 세트 사용. {list(PRESET_TICKERS.keys())}",
    )
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD (optional)")
    parser.add_argument("--out-prices", default=None, help="가격 시계열 CSV 저장 경로(단일 티커용)")
    parser.add_argument("--out-states", default=None, help="상태 CSV 저장 경로(단일 티커용)")
    parser.add_argument(
        "--out-prices-dir",
        default=None,
        help="멀티 티커일 때 각 티커별 가격 CSV를 저장할 디렉터리 (파일명: {ticker}_prices.csv)",
    )
    parser.add_argument(
        "--out-states-dir",
        default=None,
        help="멀티 티커일 때 각 티커별 상태 CSV를 저장할 디렉터리 (파일명: {ticker}_states.csv)",
    )
    parser.add_argument(
        "--fundamentals-out",
        default=None,
        help="기초 재무/채무비용 CSV 저장 경로(멀티 티커 병합 저장)",
    )
    args = parser.parse_args()

    # 티커 목록 결정
    tickers: List[str] = []
    if args.tickers:
        tickers.extend([t.strip() for t in args.tickers.split(",") if t.strip()])
    if args.ticker:
        tickers.append(args.ticker)
    if args.preset:
        tickers.extend(PRESET_TICKERS[args.preset])
    if not tickers:
        parser.error("하나 이상의 --ticker, --tickers 또는 --preset 이 필요합니다.")

    # 단일 티커 모드: 가격/상태 저장
    if len(tickers) == 1:
        t = tickers[0]
        prices = get_price_history(t, start=args.start, end=args.end)
        if args.out_prices:
            pd.DataFrame(prices).to_csv(args.out_prices, index=False)
            print(f"Saved prices -> {args.out_prices}")

        states = build_states(prices, ticker=t)
        if args.out_states:
            pd.DataFrame([s.__dict__ for s in states]).to_csv(args.out_states, index=False)
            print(f"Saved states -> {args.out_states}")

    # 멀티 티커 모드: 가격/상태/펀더멘털 순회 저장
    if len(tickers) > 1:
        fundamentals: List[Dict[str, Optional[float]]] = []
        for t in tickers:
            if args.out_prices_dir:
                prices = get_price_history(t, start=args.start, end=args.end)
                price_path = f"{args.out_prices_dir.rstrip('/')}/{t}_prices.csv"
                pd.DataFrame(prices).to_csv(price_path, index=False)
                print(f"Saved prices -> {price_path}")
                if args.out_states_dir:
                    states = build_states(prices, ticker=t)
                    state_path = f"{args.out_states_dir.rstrip('/')}/{t}_states.csv"
                    pd.DataFrame([s.__dict__ for s in states]).to_csv(state_path, index=False)
                    print(f"Saved states -> {state_path}")
            try:
                fundamentals.append(get_fundamentals(t))
            except Exception as e:  # yfinance info 실패는 무시하고 진행
                print(f"[warn] fundamentals fetch failed for {t}: {e}")
                continue

        if args.fundamentals_out and fundamentals:
            pd.DataFrame(fundamentals).to_csv(args.fundamentals_out, index=False)
            print(f"Saved fundamentals -> {args.fundamentals_out}")


if __name__ == "__main__":
    main()
