import os
import time
import urllib.request
import urllib.parse
import json
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==========================================
# [설정] 환경 변수 및 날짜 로드
# ==========================================
load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

SAVE_DIR = "data/raw/news"
SEEN_PATH = os.path.join(SAVE_DIR, "seen_links.txt")

# 기간 설정: 2020.01.01 ~ 2025.09.14
TARGET_START_DATE = datetime(2020, 1, 1)
TARGET_END_DATE = datetime(2025, 9, 14, 23, 59, 59)

def make_session():
    """연결 재시도(Retry) 로직이 포함된 세션 생성"""
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=1, # 대기 시간 (1초, 2초, 4초...)
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

class NaverNewsCrawler:
    def __init__(self, client_id, client_secret, save_dir=SAVE_DIR):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        self.cleaner = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

        self.session = make_session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        }

        # 중복 방지용 기록 로드
        self.seen_links = self._load_seen_links()

    def _load_seen_links(self):
        if os.path.exists(SEEN_PATH):
            with open(SEEN_PATH, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _append_seen_link(self, link):
        with open(SEEN_PATH, "a", encoding="utf-8") as f:
            f.write(link + "\n")

    def clean_html(self, text):
        if not text: return ""
        text = re.sub(self.cleaner, "", text)
        return text

    def parse_naver_date(self, naver_date_str):
        try:
            return datetime.strptime(naver_date_str, "%a, %d %b %Y %H:%M:%S +0900")
        except:
            return None

    def get_news(self, keyword, display=100, start=1, sort="date"):
        encText = urllib.parse.quote(keyword)
        url = f"{self.base_url}?query={encText}&display={display}&start={start}&sort={sort}"

        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", self.client_id)
        req.add_header("X-Naver-Client-Secret", self.client_secret)

        try:
            res = urllib.request.urlopen(req)
            if res.getcode() == 200:
                return json.loads(res.read().decode("utf-8"))
            return None
        except Exception as e:
            print(f"   [API Error] {e}")
            return None

    def _extract_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        # 다양한 뉴스 본문 선택자 대응
        selectors = [
            "#dic_area", "#newsct_article", "article#dic_area", 
            "div#articleBodyContents", "div#articeBody"
        ]

        content = None
        for sel in selectors:
            content = soup.select_one(sel)
            if content: break

        if not content: return None

        # 불필요 요소 제거
        for tag in content.select(".img_desc, .end_photo_org, .nbd_a, .media_end_head_autosummary, script, style"):
            tag.decompose()

        text = content.get_text(separator=" ", strip=True)
        if len(text) < 30: return None # 너무 짧으면 실패 처리
        return text

    def get_full_content(self, url):
        if "news.naver.com" not in url: return None
        try:
            r = self.session.get(url, headers=self.headers, timeout=10)
            if r.status_code != 200: return None
            return self._extract_text(r.text)
        except Exception:
            return None

    def crawl_keyword(self, keyword, max_count=1000):
        print(f"\n>>> '{keyword}' 수집 시작 (기간: 2020~2025.09)...")
        
        all_news = []
        collected = 0
        start = 1
        
        # 중단 및 통계 변수
        miss_count = 0
        skip_count = 0

        while collected < max_count:
            if start > 1000:
                print("   [Info] API 한계(1000건) 도달. 다음 키워드.")
                break

            res = self.get_news(keyword, display=100, start=start, sort="date")
            if not res or not res.get("items"): break

            for item in res["items"]:
                # 1. 날짜 필터링
                pub_date = self.parse_naver_date(item.get("pubDate", ""))
                if pub_date:
                    if pub_date > TARGET_END_DATE: continue
                    if pub_date < TARGET_START_DATE:
                        print(f"   [Stop] 2020년 이전 데이터 도달({pub_date.date()}). 수집 종료.")
                        return all_news

                link = item.get("link", "")
                
                # 2. 중복 확인 (seen_links)
                if link in self.seen_links:
                    skip_count += 1
                    continue
                
                # 3. 본문 수집
                full_content = self.get_full_content(link)
                
                # 4. 저장 및 기록
                if full_content:
                    self.seen_links.add(link)
                    self._append_seen_link(link)
                    
                    news_item = {
                        "keyword": keyword,
                        "title": self.clean_html(item.get("title", "")),
                        "date": pub_date.strftime("%Y-%m-%d %H:%M") if pub_date else "",
                        "link": link,
                        "content": full_content
                    }
                    all_news.append(news_item)
                    collected += 1
                else:
                    miss_count += 1

                if collected >= max_count: break

            print(f"   수집: {collected}건 | 본문실패: {miss_count} | 중복스킵: {skip_count}", end="\r")
            start += 100
            time.sleep(0.5)

        return all_news

    def save_to_csv(self, data, filename):
        if not data: return
        df = pd.DataFrame(data)
        df = df.drop_duplicates(subset=["link"])
        
        today = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = os.path.join(self.save_dir, f"{filename}_{today}.csv")
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        
        print(f"\n   ✅ 저장 완료: {filepath} (총 {len(df)}건)")

def main():
    if not CLIENT_ID:
        print("🚨 오류: .env 파일 확인 필요")
        return

    crawler = NaverNewsCrawler(CLIENT_ID, CLIENT_SECRET)

    # =========================================================
    # 🔑 [최종 복구] 시장 지표 + 5대 핵심 기업 정밀 키워드
    # =========================================================
    keywords = [
        # [Group A] 시장 지표 (숲)
        "반도체 수출 데이터", "DRAM 고정가", "NAND 플래시 가격", 
        "DXI 지수", "WSTS 시장 전망", "필라델피아 반도체 지수",
        "미국 반도체 지원법", "중국 반도체 규제",

        # [Group B] 차세대 기술 (길)
        "HBM4 개발", "CXL 반도체", "온디바이스 AI", 
        "어드밴스드 패키징", "글라스 기판",

        # [Group C] 5대 핵심 기업 (나무) - 상세 버전
        # 1. 한미반도체
        "한미반도체 TC본더", "한미반도체 마이크로 쏘", 
        "한미반도체 HBM 수주", "한미반도체 자사주",
        
        # 2. 삼성전자
        "삼성전자 HBM3E", "삼성전자 3나노 GAA", 
        "삼성전자 평택 캠퍼스", "삼성전자 파운드리 수율", "삼성전자 감산",
        
        # 3. SK하이닉스
        "SK하이닉스 HBM3 독점", "SK하이닉스 청주 M15X", 
        "SK하이닉스 인디애나", "SK하이닉스 솔리다임",
        
        # 4. 엔비디아
        "엔비디아 H100", "엔비디아 블랙웰", "엔비디아 실적",
        
        # 5. TSMC
        "TSMC CoWoS", "TSMC 2나노", "TSMC 구마모토"
    ]

    print(f"🔥 스마트 크롤러 가동 (안정성 강화 + 정밀 키워드)")
    all_data = []
    
    for kw in keywords:
        # 키워드당 최대 800개 (2020년까지 충분히 커버됨)
        all_data.extend(crawler.crawl_keyword(kw, max_count=800))

    crawler.save_to_csv(all_data, "Semiconductor_Final_Integrated")

if __name__ == "__main__":
    main()