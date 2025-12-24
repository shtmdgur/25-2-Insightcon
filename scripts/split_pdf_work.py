"""
PDF Processing Work Splitter (3-Person Collaboration)

1,500여 개의 PDF를 3명이서 중복 없이 나눠 작업하기 위한 헬퍼 스크립트입니다.
파일 목록을 정렬한 뒤 지정된 인덱스 범위(Bucket)의 파일만 처리합니다.

사용 방법:
    # 0번 참여자 (첫 번째 500개)
    poetry run python scripts/split_pdf_work.py --bucket 0
    
    # 1번 참여자 (두 번째 500개)
    poetry run python scripts/split_pdf_work.py --bucket 1
    
    # 2번 참여자 (세 번째 500개)
    poetry run python scripts/split_pdf_work.py --bucket 2

참고: test/integration/test_kg_orchestration.py의 오케스트레이션 로직을 따릅니다.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.agents.kg_construction import KGConstructionAgent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 외부 라이브러리 로그 숨기기 (test_kg_orchestration.py와 동일하게 설정)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

load_dotenv()

def check_environment():
    """Gemini API 키 등 필수 환경 변수 확인"""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다.")
        return False
    logger.info(f"✅ API Key 확인됨 (앞자리: {api_key[:10]}...)")
    return True

def get_pdf_files():
    """전체 PDF 파일 목록을 스캔하고 정렬하여 반환 (preprocessed 전용)"""
    processed_root = project_root / "data" / "preprocessed"
    
    target_dirs = [
        processed_root / "reports",
        processed_root / "ir"
    ]
    
    pdf_files = []
    for d in target_dirs:
        if d.exists():
            pdf_files.extend(list(d.glob("**/*.pdf")))
        
    # 파일명순 정렬 (절대적 일관성)
    pdf_files.sort(key=lambda x: x.name)
    return pdf_files

def get_news_files():
    """전체 뉴스 CSV 파일 목록을 스캔하고 정렬하여 반환"""
    news_dir = project_root / "data" / "preprocessed" / "news"
    if not news_dir.exists():
        news_dir = project_root / "data" / "raw" / "news"
        
    news_files = []
    if news_dir.exists():
        news_files.extend(list(news_dir.glob("*.csv")))
    
    # 처리 일관성을 위해 정렬
    news_files.sort(key=lambda x: str(x.relative_to(project_root)))
    return news_files

def split_news_by_rows(bucket_idx, total_buckets=3):
    """뉴스 CSV들의 전체 행을 합산하여 3등분하고 해당 구간의 임시 CSV 생성"""
    import pandas as pd
    news_files = get_news_files()
    if not news_files:
        return [], 0, 0, 0
    
    # 1. 모든 뉴스 로드
    all_dfs = []
    for f in news_files:
        try:
            df = pd.read_csv(f)
            all_dfs.append(df)
        except Exception as e:
            logger.error(f"뉴스 파일 로드 실패 {f.name}: {e}")
            
    if not all_dfs:
        return [], 0, 0, 0
        
    full_df = pd.concat(all_dfs, ignore_index=True)
    total_rows = len(full_df)
    
    # 2. 행 단위 분할 범위 계산
    rows_per_bucket = (total_rows + total_buckets - 1) // total_buckets
    start_row = bucket_idx * rows_per_bucket
    end_row = min(start_row + rows_per_bucket, total_rows)
    
    target_df = full_df.iloc[start_row:end_row]
    
    # 3. 임시 파일 저장 (KGConstructionAgent는 파일 경로를 필요로 함)
    temp_dir = project_root / "data" / "temp_news"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"news_bucket_{bucket_idx}.csv"
    target_df.to_csv(temp_path, index=False)
    
    return [temp_path], start_row, end_row, total_rows

def split_work(files, bucket_idx, total_buckets=3):
    """파일 목록을 N개의 버킷으로 나누고 해당 인덱스의 목록 반환 (PDF용)"""
    if not files:
        return [], 0, 0
    total_files = len(files)
    bucket_size = (total_files + total_buckets - 1) // total_buckets
    
    start_idx = bucket_idx * bucket_size
    end_idx = min(start_idx + bucket_size, total_files)
    
    return files[start_idx:end_idx], start_idx, end_idx

def main():
    parser = argparse.ArgumentParser(description="PDF & News (Row-level) Processing Work Splitter")
    parser.add_argument("--bucket", type=int, help="Bucket index (0, 1, or 2)")
    parser.add_argument("--total", type=int, default=3, help="Total number of workers (default: 3)")
    parser.add_argument("--skip-existing", action="store_true", default=True, help="Skip already processed JSON files")
    
    args = parser.parse_args()
    
    # 0. 환경 환경 체크 (API 키 등)
    if not check_environment():
        return

    # 0.5. 대화형 입력 처리
    if args.bucket is None:
        print("\n" + "*" * 50)
        print("💡 작업 버킷 번호가 지정되지 않았습니다.")
        print("   참여자 1: 0 입력")
        print("   참여자 2: 1 입력")
        print("   참여자 3: 2 입력")
        print("*" * 50)
        try:
            val = input("\n원하는 번호를 입력하세요 (0, 1, 2): ").strip()
            args.bucket = int(val)
        except ValueError:
            logger.error("❌ 숫자를 입력해야 합니다.")
            return

    if args.bucket < 0 or args.bucket >= args.total:
        logger.error(f"❌ 잘못된 범위입니다 (0 ~ {args.total-1}).")
        return
    
    print("\n" + "=" * 80)
    print(f"🚀 분산 처리 시작 (Worker: {args.bucket}/{args.total-1})")
    print("   * PDF: 파일 단위 분할")
    print("   * News: 전체 행(Row) 단위 분할")
    print("=" * 80 + "\n")
    
    # 1. 파일 목록 확보 및 분할
    all_pdfs = get_pdf_files()
    target_pdfs, p_start, p_end = split_work(all_pdfs, args.bucket, args.total)
    
    # 뉴스는 행 단위로 정밀하게 분할
    target_news, n_start, n_end, n_total = split_news_by_rows(args.bucket, args.total)
    
    logger.info(f"PDF: {len(all_pdfs)}개 중 {len(target_pdfs)}개 담당 ({p_start} ~ {p_end-1})")
    logger.info(f"News: {n_total}행 중 {len(range(n_start, n_end))}행 담당 ({n_start} ~ {n_end-1})")
    
    if not target_pdfs and not target_news:
        logger.warning("처리할 데이터가 없습니다.")
        return

    # 2. 에이전트 초기화 (News 파서용 LLM 포함)
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config.llm_config import get_model
        from src.config.parser_config import update_config
        
        # [CRITICAL] 뉴스 샘플링 제한 해제 (지정된 구역 전체를 처리하기 위함)
        update_config('news', sample_size=10000)
        logger.info("⚙️  News Parser 설정 업데이트: sample_size=10000 (분할 데이터 전체 영역)")
        
        # 뉴스 파싱을 위한 LLM 초기화
        llm = ChatGoogleGenerativeAI(model=get_model("news_parsing"))
        
        agent = KGConstructionAgent(
            data_dir=project_root / "data",
            llm=llm
        )
        logger.info("✅ KGConstructionAgent & LLM 초기화 완료")
    except Exception as e:
        logger.error(f"❌ Agent 초기화 실패: {e}")
        return

    # 3. 파싱 실행 (PDF + News)
    start_time = datetime.now()
    logger.info(f"⏰ 시작 시각: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # data_sources에 담당 구역 목록 전달
        data_sources = {
            'pdf': target_pdfs,
            'news': target_news
        }
        
        # 내부적으로 PDF와 News는 ThreadPoolExecutor에 의해 병렬 처리됨
        result = agent.construct_knowledge_graph(
            data_sources=data_sources,
            auto_scan=False,
            load_to_neo4j=False,
            skip_existing=args.skip_existing
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 결과 요약
        p_res = result['parser_results'].get('pdf', {'success': 0, 'failed': 0})
        n_res = result['parser_results'].get('news', {'success': 0, 'failed': 0})
        
        print("\n" + "-" * 80)
        print(f"✅ 작업 완료! (소요 시간: {duration:.2f}초)")
        print(f"📊 PDF  - 성공: {p_res['success']}, 실패: {p_res['failed']}")
        print(f"📊 News - 성공: {n_res['success']}, 실패: {n_res['failed']}")
        print("-" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ 작업 도중 오류 발생: {e}")

if __name__ == "__main__":
    main()
