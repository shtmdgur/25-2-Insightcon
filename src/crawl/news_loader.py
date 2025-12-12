import os
import time
import urllib.request
import urllib.parse
import json
import re
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv  # [추가] .env 로드용

# ==========================================
# [설정] 환경 변수 로드
# ==========================================
# .env 파일 내용을 불러옵니다.
load_dotenv()

# .env에서 가져오기 (없으면 None 반환)
CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 저장 경로
SAVE_DIR = "data/raw/news"

class NaverNewsCrawler:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://openapi.naver.com/v1/search/news.json"
        
        # HTML 태그 제거용 정규표현식
        self.cleaner = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

    def clean_html(self, text):
        """제목/요약문에서 <b>, &quot; 같은 태그 제거"""
        if not text: return ""
        text = re.sub(self.cleaner, '', text)
        return text

    def convert_date(self, naver_date):
        """네이버 날짜 포맷(Tue, 10 Dec 2025...) -> YYYY-MM-DD"""
        try:
            # 포맷: "Wed, 10 Dec 2025 14:00:00 +0900"
            dt = datetime.strptime(naver_date, "%a, %d %b %Y %H:%M:%S +0900")
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return naver_date

    def get_news(self, keyword, display=100, start=1, sort='date'):
        """API 호출 함수"""
        encText = urllib.parse.quote(keyword)
        url = f"{self.base_url}?query={encText}&display={display}&start={start}&sort={sort}"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", self.client_id)
        request.add_header("X-Naver-Client-Secret", self.client_secret)
        
        try:
            response = urllib.request.urlopen(request)
            res_code = response.getcode()
            if res_code == 200:
                response_body = response.read()
                return json.loads(response_body.decode('utf-8'))
            else:
                print(f"Error Code: {res_code}")
                return None
        except Exception as e:
            print(f"Request Failed: {e}")
            return None

    def crawl_keyword(self, keyword, max_count=1000):
        """특정 키워드에 대해 최대 max_count만큼 수집"""
        print(f"\n>>> '{keyword}' 뉴스 수집 시작 (최대 {max_count}건)...")
        
        all_news = []
        page = 1
        start = 1
        
        while len(all_news) < max_count:
            # 네이버 API는 start가 1000을 넘을 수 없음
            if start > 1000:
                print("   [Info] 네이버 API 제한(1000건)에 도달했습니다.")
                break
                
            res = self.get_news(keyword, display=100, start=start, sort='date') 
            
            if not res or not res['items']:
                break
                
            for item in res['items']:
                news_item = {
                    'keyword': keyword,
                    'title': self.clean_html(item['title']),
                    'link': item['originallink'] if item['originallink'] else item['link'],
                    'date': self.convert_date(item['pubDate']),
                    'description': self.clean_html(item['description'])
                }
                all_news.append(news_item)
            
            print(f"   수집 중... {len(all_news)}건 완료", end='\r')
            start += 100
            time.sleep(0.5) 
            
        return all_news

    def save_to_csv(self, data, filename):
        if not data: return
        os.makedirs(SAVE_DIR, exist_ok=True)
        df = pd.DataFrame(data)
        
        today = datetime.now().strftime("%Y%m%d")
        filepath = os.path.join(SAVE_DIR, f"{filename}_{today}.csv")
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"\n   ✅ 저장 완료: {filepath} (총 {len(df)}건)")

# ==========================================
# 실행부
# ==========================================
def main():
    # 1. 키 확인
    if not CLIENT_ID or not CLIENT_SECRET:
        print("🚨 오류: .env 파일을 찾을 수 없거나 키가 없습니다.")
        print("   1. .env 파일을 만들었는지 확인하세요.")
        print("   2. NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 변수가 있는지 확인하세요.")
        return

    print(f"[Info] API Key 로드 성공 (Client ID: {CLIENT_ID[:5]}***)")

    crawler = NaverNewsCrawler(CLIENT_ID, CLIENT_SECRET)
    
    # 2. 수집할 키워드 (최종 확장판)
    keywords = [
        # [1] 시장 전반 & 지표 (가격/재고/수출)
        "반도체 수출 데이터",       
        "DRAM 고정가",             
        "NAND 플래시 가격 동향",
        "반도체 재고 수준",         
        "WSTS 시장 전망",           
        "DXI 지수",                

        # [2] 국내 주요 기업 (삼성/SK 이슈)
        "삼성전자 파운드리 수율",    
        "삼성전자 평택 캠퍼스",      
        "SK하이닉스 HBM3E",        
        "SK하이닉스 청주 M15",      
        "삼성전자 감산",            
        
        # [3] 글로벌 경쟁사 & 빅테크
        "마이크론 실적 가이던스",    
        "TSMC CoWoS",             
        "엔비디아 GPU 공급",        
        "인텔 파운드리",            
        "ASML EUV",                 # [추가] 장비 공급 이슈

        # [4] 차세대 기술 & 소부장
        "HBM4 개발",               
        "CXL 반도체",              
        "DDR5 교체 수요",           
        "온디바이스 AI 칩",         
        "어드밴스드 패키징",         # [추가] 후공정 기술 트렌드

        # [5] 대외 리스크 & 정책 & 투자심리
        "미국 반도체 보조금",       
        "중국 반도체 규제",         
        "반도체 소부장 국산화",       
        "모건스탠리 반도체 보고서"    # [추가] 외국계 투자 심리 확인
    ]
    
    # 3. 수집 실행
    all_data = []
    for kw in keywords:
        news_data = crawler.crawl_keyword(kw, max_count=300)
        all_data.extend(news_data)
    
    # 4. 저장
    crawler.save_to_csv(all_data, "Semiconductor_News_Raw")

if __name__ == "__main__":
    main()