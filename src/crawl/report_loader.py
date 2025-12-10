"""
[Final Date-Range] 증권사 리포트 수집기
- 대상 기간: 2020.01.01 ~ 2025.09.14 (엄격 제한)
- 범위 밖의 최신 자료는 스킵하고, 범위 밖의 과거 자료를 만나면 종료합니다.
"""

import os
import time
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ----------------------------
# 설정
# ----------------------------
BASE_URL = "https://finance.naver.com/research"
SAVE_DIR = "data/raw/reports"

# [중요] 수집 기간 설정
START_DATE = "20200101"
END_DATE = "20250914"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finance.naver.com/research/"
}

KOREA_COMPANIES = {
    "005930": "Samsung",
    "000660": "SKHynix",
    "000990": "DBHiTek",
    "042700": "HanmiSemi"
}

GLOBAL_COMPANIES = {
    "NVIDIA": "NVDA", "엔비디아": "NVDA",
    "TSMC": "TSM",
    "Intel": "INTC", "인텔": "INTC",
    "Micron": "MU", "마이크론": "MU",
    "ASML": "ASML",
    "Applied": "AMAT", "어플라이드": "AMAT",
    "Lam": "LRCX", "램리서치": "LRCX",
    "Broadcom": "AVGO", "브로드컴": "AVGO"
}

def download_pdf(url, title, source, date, category):
    try:
        if url.startswith("/"): url = f"https://finance.naver.com{url}"
        
        # 파일명 정제
        clean_title = "".join(x for x in title if x.isalnum() or x in " -_")[:50]
        filename = f"{date}_{category}_{source}_{clean_title}.pdf"
        filepath = os.path.join(SAVE_DIR, filename)
        
        if os.path.exists(filepath): return True

        response = requests.get(url, headers=HEADERS, stream=True, timeout=20)
        if response.status_code != 200:
            print(f"  [Fail] 다운로드 실패: {url}")
            return False

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if os.path.getsize(filepath) < 100:
            os.remove(filepath)
            return False

        print(f"  [Save] {filename}")
        return True
    except Exception as e:
        print(f"  [Error] {e}")
        return False

def check_date_range(date_str):
    """날짜가 범위 내인지 확인 (0: 범위내, 1: 너무최신, -1: 너무과거)"""
    if date_str > END_DATE: return 1  # 스킵
    if date_str < START_DATE: return -1 # 종료
    return 0 # 다운로드

def crawl_korea_companies(max_pages):
    print(f"\n>>> [Domestic] 국내 4대장 리포트 ({START_DATE}~{END_DATE})")
    target_page = 20 if max_pages == -1 else max_pages
    
    for code, eng_name in KOREA_COMPANIES.items():
        print(f"--- {eng_name} ({code}) ---")
        for page in range(1, target_page + 1):
            try:
                url = f"{BASE_URL}/company_list.naver?searchType=itemCode&itemCode={code}&page={page}"
                res = requests.get(url, headers=HEADERS)
                res.encoding = 'cp949'
                
                soup = BeautifulSoup(res.text, "html.parser")
                rows = soup.select("table.type_1 tr")
                valid_rows = [r for r in rows if len(r.select("td")) >= 3]
                
                if not valid_rows: break

                stop_flag = False
                for row in valid_rows:
                    cols = row.select("td")
                    try:
                        date = cols[4].text.strip()
                        date_str = datetime.strptime(date, "%y.%m.%d").strftime("%Y%m%d")
                        
                        status = check_date_range(date_str)
                        if status == 1: continue # 2025.09.15 이후 -> 스킵
                        if status == -1: # 2019.12.31 이전 -> 종료
                            print(f"  [Stop] 수집 기간 종료 도달 ({date_str})")
                            stop_flag = True
                            break

                        title = cols[1].select_one("a").text.strip()
                        broker = cols[2].text.strip()
                        file_link_tag = cols[3].find('a') 
                        if not file_link_tag or 'href' not in file_link_tag.attrs: continue
                        
                        download_pdf(file_link_tag['href'], title, broker, date_str, eng_name)
                    except: continue
                
                if stop_flag: break
                time.sleep(0.1)
            except: break

def crawl_global_companies(max_pages):
    print(f"\n>>> [Global] 해외 반도체 리포트 ({START_DATE}~{END_DATE})")
    page = 1
    while True:
        if max_pages != -1 and page > max_pages: break
        try:
            url = f"{BASE_URL}/pro_invest_list.naver?&page={page}" 
            res = requests.get(url, headers=HEADERS)
            res.encoding = 'cp949'
            
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table.type_1 tr")
            valid_rows = [r for r in rows if len(r.select("td")) >= 3]
            if not valid_rows: break

            cnt = 0
            stop_flag = False
            for row in valid_rows:
                cols = row.select("td")
                try:
                    date = cols[4].text.strip()
                    date_str = datetime.strptime(date, "%y.%m.%d").strftime("%Y%m%d")

                    status = check_date_range(date_str)
                    if status == 1: continue # 너무 최신
                    if status == -1: # 너무 과거 (네이버는 최신순 정렬이므로 여기서 멈춰도 됨)
                        print(f"  [Stop] 수집 기간 종료 도달 ({date_str})")
                        stop_flag = True
                        break

                    title = cols[1].select_one("a").text.strip()
                    broker = cols[2].text.strip()
                    
                    matched_ticker = None
                    for keyword, ticker in GLOBAL_COMPANIES.items():
                        if keyword.lower() in title.lower():
                            matched_ticker = ticker
                            break
                    if not matched_ticker: continue

                    file_link_tag = cols[3].find('a')
                    if not file_link_tag: continue
                    
                    if download_pdf(file_link_tag['href'], title, broker, date_str, matched_ticker): cnt += 1
                except: continue
            
            if stop_flag: break
            print(f"  Page {page} 탐색... (저장된 글로벌: {cnt}건)", end="\r")
            page += 1
            time.sleep(0.1)
        except: break

def crawl_industry_reports(max_pages):
    print(f"\n>>> [Industry] 반도체 산업 리포트 ({START_DATE}~{END_DATE})")
    page = 1
    while True:
        if max_pages != -1 and page > max_pages: break
        try:
            url = f"{BASE_URL}/industry_list.naver?&page={page}"
            res = requests.get(url, headers=HEADERS)
            res.encoding = 'cp949'
            
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table.type_1 tr")
            valid_rows = [r for r in rows if len(r.select("td")) >= 3]
            if not valid_rows: break

            cnt = 0
            stop_flag = False
            for row in valid_rows:
                cols = row.select("td")
                try:
                    date = cols[4].text.strip()
                    date_str = datetime.strptime(date, "%y.%m.%d").strftime("%Y%m%d")
                    
                    status = check_date_range(date_str)
                    if status == 1: continue 
                    if status == -1:
                        print(f"  [Stop] 수집 기간 종료 도달 ({date_str})")
                        stop_flag = True
                        break

                    category = cols[0].text.strip()
                    title = cols[1].select_one("a").text.strip()
                    
                    if "반도체" not in category and "반도체" not in title: continue
                    
                    broker = cols[2].text.strip()
                    file_link_tag = cols[3].find('a')
                    if not file_link_tag: continue
                    
                    if download_pdf(file_link_tag['href'], title, broker, date_str, "Semiconductor"): cnt += 1
                except: continue
            
            if stop_flag: break
            print(f"  Page {page} 탐색... (저장된 반도체: {cnt}건)", end="\r")
            page += 1
            time.sleep(0.1)
        except: break

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=2)
    args = parser.parse_args()
    
    abs_path = os.path.abspath(SAVE_DIR)
    os.makedirs(abs_path, exist_ok=True)
    print(f"\n[Info] 저장 경로: {abs_path}")
    print(f"[Info] 대상 기간: {START_DATE} ~ {END_DATE}")
    
    crawl_korea_companies(args.pages)
    crawl_global_companies(args.pages)
    crawl_industry_reports(args.pages)
    
    print("\n\n>>> 수집 완료.")

if __name__ == "__main__":
    main()