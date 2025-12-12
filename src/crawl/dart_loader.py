"""
[Final] Open DART API 통합 수집기
1. 기업 개요 (Company Info) -> companies.csv (New!)
2. 재무 상태 (Financial State) -> financial_states.csv
3. 공시 상태 (Disclosure State) -> disclosure_states.csv

실행 예시:
python -m src.crawl.dart_loader --preset semis --start 2020-01-01 --end 2025-09-14 --out-states-dir data/raw/states
"""

from __future__ import annotations

import argparse
import io
import os
import time
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

# ----------------------------
# 데이터 클래스
# ----------------------------
@dataclass
class DartCompanyInfo:
    """기업 기본 정보 (Node Property)"""
    ticker: str
    corp_code: str
    corp_name: str
    ceo_nm: str
    jurir_no: str # 법인등록번호
    bizr_no: str  # 사업자등록번호
    est_dt: str   # 설립일
    adres: str    # 주소
    hm_url: str   # 홈페이지
    induty_code: str # 업종코드

@dataclass
class DartFinancialState:
    ticker: str
    corp_code: str
    year: str
    quarter_code: str 
    revenue: float
    operating_income: float
    net_income: float
    profitability_symbol: str
    growth_symbol: str
    margin_level: str

@dataclass
class DartDisclosureState:
    ticker: str
    corp_code: str
    date: str
    rcept_no: str
    report_nm: str
    flr_nm: str
    disclosure_type: str
    importance: str

# ----------------------------
# API 및 로직 클래스
# ----------------------------
class DartAPI:
    BASE_URL = "https://opendart.fss.or.kr/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.corp_code_map = self._load_corp_code_map()

    def _load_corp_code_map(self) -> pd.DataFrame:
        print("Loading Corp Code Map...")
        url = f"{self.BASE_URL}/corpCode.xml"
        params = {"crtfc_key": self.api_key}
        resp = requests.get(url, params=params)
        
        try:
            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                xml_data = zf.read("CORPCODE.xml")
        except zipfile.BadZipFile:
            raise ValueError("Invalid API Key or DART Server Error.")

        tree = ET.fromstring(xml_data)
        records = []
        for child in tree:
            corp_code = child.find("corp_code").text
            stock_code = child.find("stock_code").text
            corp_name = child.find("corp_name").text
            if stock_code and stock_code.strip():
                records.append({"corp_code": corp_code, "stock_code": stock_code, "corp_name": corp_name})
        return pd.DataFrame(records)

    def get_code_by_ticker(self, ticker: str) -> Optional[str]:
        clean_ticker = ticker.replace(".KS", "").replace(".KQ", "")
        row = self.corp_code_map[self.corp_code_map["stock_code"] == clean_ticker]
        if not row.empty:
            return row.iloc[0]["corp_code"]
        return None

    def get_company_info(self, corp_code: str) -> Dict:
        """기업 개요 조회 (New)"""
        url = f"{self.BASE_URL}/company.json"
        params = {"crtfc_key": self.api_key, "corp_code": corp_code}
        resp = requests.get(url, params=params).json()
        if resp.get("status") == "000":
            return resp
        return {}

    def get_financials(self, corp_code: str, year: str, reprt_code: str) -> pd.DataFrame:
        url = f"{self.BASE_URL}/fnlttSinglAcnt.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bsns_year": year,
            "reprt_code": reprt_code,
        }
        try:
            resp = requests.get(url, params=params).json()
            if resp.get("status") == "000":
                return pd.DataFrame(resp.get("list", []))
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def get_disclosure_list(self, corp_code: str, bgn_de: str, end_de: str) -> pd.DataFrame:
        url = f"{self.BASE_URL}/list.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bgn_de": bgn_de.replace("-", ""),
            "end_de": end_de.replace("-", ""),
            "page_count": 100
        }
        resp = requests.get(url, params=params).json()
        if resp.get("status") == "000":
            return pd.DataFrame(resp.get("list", []))
        return pd.DataFrame()

# ----------------------------
# Helper Logic
# ----------------------------
def split_date_range(start_date: str, end_date: str, chunk_days: int = 90) -> List[Tuple[str, str]]:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    ranges = []
    current = start
    while current <= end:
        next_chunk = current + timedelta(days=chunk_days)
        chunk_end = min(next_chunk, end)
        ranges.append((current.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
        current = chunk_end + timedelta(days=1)
    return ranges

def _categorize_financials(rev: float, op_inc: float, net_inc: float) -> Tuple[str, str]:
    profit_sym = "Profitable" if op_inc > 0 else "Loss"
    if rev == 0: margin_sym = "Unknown"
    else:
        margin = op_inc / rev
        if margin > 0.2: margin_sym = "HighMargin"
        elif margin > 0.05: margin_sym = "NormalMargin"
        else: margin_sym = "LowMargin"
    return profit_sym, margin_sym

def build_financial_states(df: pd.DataFrame, ticker: str, year: str, reprt_code: str) -> List[DartFinancialState]:
    if df.empty: return []
    def get_value(nm):
        rows = df[df["account_nm"].str.contains(nm, na=False)]
        if rows.empty: return 0.0
        val_str = rows.iloc[0]["thstrm_amount"]
        if not val_str or val_str.strip() == "-": return 0.0
        return float(val_str.replace(",", ""))

    rev = get_value("매출액")
    op_inc = get_value("영업이익")
    net_inc = get_value("당기순이익")
    profit_sym, margin_sym = _categorize_financials(rev, op_inc, net_inc)

    return [DartFinancialState(
        ticker=ticker,
        corp_code=df.iloc[0]["corp_code"] if "corp_code" in df.columns else "",
        year=year,
        quarter_code=reprt_code,
        revenue=rev,
        operating_income=op_inc,
        net_income=net_inc,
        profitability_symbol=profit_sym,
        growth_symbol="Unknown",
        margin_level=margin_sym
    )]

def _categorize_disclosure(title: str) -> Tuple[str, str]:
    title = title.replace(" ", "")
    if any(x in title for x in ["분기보고서", "반기보고서", "사업보고서"]): return "PERIODIC", "HIGH"
    if "공급계약" in title or "수주" in title: return "CONTRACT", "HIGH"
    if "유상증자" in title or "무상증자" in title or "전환사채" in title: return "ISSUE", "HIGH"
    if "기업설명회" in title: return "IR", "NORMAL"
    return "OTHER", "NORMAL"

def build_disclosure_states(df: pd.DataFrame, ticker: str) -> List[DartDisclosureState]:
    states = []
    for _, row in df.iterrows():
        d_type, imp = _categorize_disclosure(row["report_nm"])
        states.append(DartDisclosureState(
            ticker=ticker,
            corp_code=row["corp_code"],
            date=row["rcept_dt"],
            rcept_no=row["rcept_no"],
            report_nm=row["report_nm"],
            flr_nm=row["flr_nm"],
            disclosure_type=d_type,
            importance=imp
        ))
    return states

PRESET_TICKERS = {
    "semis": ["005930", "000660", "042700", "000990"],
    "samsung_val": ["005930", "009150", "018260"]
}
REPORT_CODES = ["11013", "11012", "11014", "11011"]

def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=list(PRESET_TICKERS.keys()))
    parser.add_argument("--tickers")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--out-states-dir", required=True)
    
    args = parser.parse_args()
    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        print("Error: DART_API_KEY not set.")
        return

    dart = DartAPI(api_key)
    target_tickers = []
    if args.preset: target_tickers.extend(PRESET_TICKERS[args.preset])
    if args.tickers: target_tickers.extend(args.tickers.split(","))
    
    # 결과 담을 리스트
    all_companies = [] # NEW!
    all_fin_states = []
    all_disc_states = []
    
    start_year = int(args.start[:4])
    end_year = int(args.end[:4])
    years = [str(y) for y in range(start_year, end_year + 1)]
    date_ranges = split_date_range(args.start, args.end)
    
    for ticker in target_tickers:
        clean_ticker = ticker.strip()
        corp_code = dart.get_code_by_ticker(clean_ticker)
        if not corp_code: continue
            
        print(f"\n>>> Processing {clean_ticker}")
        
        # 0. 기업 기본 정보 (New!)
        print("  [Basic Info] Fetching...", end="", flush=True)
        info = dart.get_company_info(corp_code)
        if info:
            all_companies.append(DartCompanyInfo(
                ticker=clean_ticker,
                corp_code=corp_code,
                corp_name=info.get("corp_name"),
                ceo_nm=info.get("ceo_nm"),
                jurir_no=info.get("jurir_no"),
                bizr_no=info.get("bizr_no"),
                est_dt=info.get("est_dt"),
                adres=info.get("adres"),
                hm_url=info.get("hm_url"),
                induty_code=info.get("induty_code")
            ))
        print(" Done.")

        # 1. Financials
        print("  [Financials] Fetching...", end="", flush=True)
        for y in years:
            for rc in REPORT_CODES:
                df_fin = dart.get_financials(corp_code, y, rc)
                if not df_fin.empty:
                    all_fin_states.extend(build_financial_states(df_fin, clean_ticker, y, rc))
                time.sleep(0.05)
        print(" Done.")

        # 2. Disclosures
        print(f"  [Disclosures] Fetching...", end="", flush=True)
        for (s_date, e_date) in date_ranges:
            df_disc = dart.get_disclosure_list(corp_code, s_date, e_date)
            if not df_disc.empty:
                all_disc_states.extend(build_disclosure_states(df_disc, clean_ticker))
            time.sleep(0.05)
        print(" Done.")

    # 저장
    os.makedirs(args.out_states_dir, exist_ok=True)
    
    # 0. 기업 정보 저장 (New!)
    if all_companies:
        pd.DataFrame([asdict(s) for s in all_companies]).to_csv(f"{args.out_states_dir}/companies.csv", index=False)
        print(f"\nSaved Basic Info: {len(all_companies)} companies -> companies.csv")

    if all_fin_states:
        pd.DataFrame([asdict(s) for s in all_fin_states]).to_csv(f"{args.out_states_dir}/financial_states.csv", index=False)
        print(f"Saved Financial States: {len(all_fin_states)}")
    
    if all_disc_states:
        pd.DataFrame([asdict(s) for s in all_disc_states]).to_csv(f"{args.out_states_dir}/disclosure_states.csv", index=False)
        print(f"Saved Disclosure States: {len(all_disc_states)}")

if __name__ == "__main__":
    main()