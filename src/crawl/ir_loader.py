"""
[Final Date-Range Strict + Content Filter] 기업 IR 자료 수집기
- 대상 기간: 2020년 1월 ~ 2025년 9월 14일
- 필터링 1: 2025년 9월 14일 이후(3Q/4Q) 자료 제외
- 필터링 2: IR과 관련 없는 공고/뉴스/정관 등 제외 (is_valid_ir 적용)
"""

import os
import time
import requests
from bs4 import BeautifulSoup

# ----------------------------
# 설정
# ----------------------------
SAVE_DIR = "data/raw/ir"

# 수집할 연도
TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

# 기업별 검색 키워드
TARGETS = [
    # --- 한국 기업 ---
    {
        "name": "Samsung",
        "keywords": ["경영실적 발표자료 pdf", "사업보고서 pdf"]
    },
    {
        "name": "SKHynix",
        "keywords": ["실적발표 자료 pdf", "지속가능경영보고서 pdf"]
    },
    {
        "name": "DBHiTek",
        "keywords": ["기업설명회 pdf", "분기보고서 pdf"]
    },
    {
        "name": "HanmiSemi",
        "keywords": ["IR자료 pdf"]
    },
    # --- 글로벌 기업 ---
    {
        "name": "NVIDIA",
        "keywords": ["Investor Presentation pdf", "Financial Results pdf"]
    },
    {
        "name": "TSMC",
        "keywords": ["Earnings Conference pdf", "Annual Report pdf"]
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.naver.com/"
}

# -----------------------------------------------------------
# [추가됨] 제목 필터링 함수
# -----------------------------------------------------------
def is_valid_ir(title):
    """
    제목을 보고 이게 '진짜 실적/전망 자료'인지 판별하는 함수
    True면 수집/유지, False면 스킵/삭제
    """
    if not title: return False
    
    # 1. 무조건 포함되어야 하는 키워드 (이 중 하나라도 있으면 합격)
    good_keywords = [
        "실적", "경영", "IR", "설명회", "컨퍼런스", "전망", "발표", "Presentation",
        "Earnings", "Results", "Outlook", "Conference", "Investor", "Guidance",
        "Quarter", "Financial", "Business", "Report", "보고서"
    ]
    
    # 2. 무조건 걸러야 하는 키워드 (이게 있으면 탈락)
    bad_keywords = [
        "소집", "공고", "특수", "정관", "감사", "의결", "임원", "주식", "모집", 
        "Notice", "Meeting", "Governance", "ESG", "Sustainability", "Audit", "Proxy", "Vote"
    ]

    clean_title = title.lower() 

    # 1단계: 나쁜 키워드 검사
    for bad in bad_keywords:
        if bad.lower() in clean_title:
            return False

    # 2단계: 좋은 키워드 검사
    for good in good_keywords:
        if good.lower() in clean_title:
            return True
            
    # 제목이 너무 짧거나(파일명 등) 애매하면 일단 False (엄격하게)
    return False

# -----------------------------------------------------------

def is_valid_for_2025(url):
    """2025년 자료 중 9월 14일 이후(3Q/4Q) 자료인지 검사"""
    lower_url = url.lower()
    
    forbidden_keywords = [
        "3q", "4q", "3분기", "4분기", 
        "oct", "nov", "dec", 
        "10월", "11월", "12월", 
        "third quarter", "fourth quarter"
    ]
    
    for bad in forbidden_keywords:
        if bad in lower_url:
            print(f"      [Skip] 2025년 9월 14일 이후 자료 (키워드: {bad})")
            return False
            
    return True

def download_file(url, company_name, year):
    """파일 다운로드"""
    try:
        # 1. 2025년일 경우 날짜 필터링 적용
        if year == 2025:
            if not is_valid_for_2025(url):
                return False

        if not ".pdf" in url.lower(): return False
        
        # 가짜 링크 제외
        if any(x in url for x in ["viewer", "pre", "search", "blog"]):
            if not url.endswith(".pdf"): return False

        print(f"      [Try] 다운로드 시도: {url.split('/')[-1][:30]}...")
        
        response = requests.get(url, headers=HEADERS, stream=True, timeout=15)
        if response.status_code != 200: return False
        
        filename = url.split("/")[-1]
        if not filename.lower().endswith(".pdf"): filename += ".pdf"
        filename = "".join(x for x in filename if x.isalnum() or x in "._-")[:50]
        
        final_filename = f"{year}_{filename}"
        
        save_path = os.path.join(SAVE_DIR, company_name)
        os.makedirs(save_path, exist_ok=True)
        filepath = os.path.join(save_path, final_filename)
        
        if os.path.exists(filepath):
            print(f"      [Skip] 이미 있음")
            return True

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if os.path.getsize(filepath) < 2000:
            os.remove(filepath)
            return False

        print(f"      ✅ [Save] 성공: {final_filename}")
        return True

    except Exception:
        return False

def crawl_ir_by_year():
    print(f">>> 기업 공식 IR 자료 수집 시작 (2020 ~ 2025.09.14)...")
    os.makedirs(SAVE_DIR, exist_ok=True)
    
    base_url = "https://search.naver.com/search.naver"

    for target in TARGETS:
        name = target["name"]
        print(f"\n[{name}] 연도별 검색 시작...")
        
        # 2025년부터 2020년까지 역순 검색
        for year in reversed(TARGET_YEARS):
            print(f"  📅 {year}년도 자료 검색 중...")
            
            for base_keyword in target["keywords"]:
                if name in ["Samsung", "SKHynix", "DBHiTek", "HanmiSemi"]:
                    query = f"{name} {year}년 {base_keyword}"
                else:
                    query = f"{name} {year} {base_keyword}"
                
                params = {"where": "web", "query": query}
                
                try:
                    res = requests.get(base_url, headers=HEADERS, params=params)
                    soup = BeautifulSoup(res.text, "html.parser")
                    all_links = soup.select("a")
                    
                    count = 0
                    for a_tag in all_links:
                        url = a_tag.get("href")
                        
                        # [중요] 링크의 제목(Text)을 가져옵니다.
                        title_text = a_tag.get_text(strip=True)

                        if not url or not url.startswith("http"): continue
                        
                        # [핵심 수정] 여기서 제목 필터링(is_valid_ir)을 수행합니다!
                        if not is_valid_ir(title_text):
                            # 제목이 IR 자료 같지 않으면 그냥 넘어갑니다.
                            continue

                        if ".pdf" in url.lower():
                            if download_file(url, name, year):
                                count += 1
                        
                        if count >= 1: break 
                    
                    time.sleep(1)

                except Exception as e:
                    print(f"    [Error] {e}")

if __name__ == "__main__":
    crawl_ir_by_year()