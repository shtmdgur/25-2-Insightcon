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
    """전체 PDF 파일 목록을 스캔하고 정렬하여 반환"""
    raw_dir = project_root / "data" / "raw" / "reports"
    ir_dir = project_root / "data" / "raw" / "ir"
    
    pdf_files = []
    if raw_dir.exists():
        pdf_files.extend(list(raw_dir.glob("**/*.pdf")))
    if ir_dir.exists():
        pdf_files.extend(list(ir_dir.glob("**/*.pdf")))
        
    # 파일 경로순 정렬 (모든 참여자가 동일한 정렬 결과를 가져야 함)
    pdf_files.sort(key=lambda x: str(x.relative_to(project_root)))
    return pdf_files

def split_work(pdf_files, bucket_idx, total_buckets=3):
    """파일 목록을 N개의 버킷으로 나누고 해당 인덱스의 목록 반환"""
    total_files = len(pdf_files)
    bucket_size = (total_files + total_buckets - 1) // total_buckets
    
    start_idx = bucket_idx * bucket_size
    end_idx = min(start_idx + bucket_size, total_files)
    
    return pdf_files[start_idx:end_idx], start_idx, end_idx

def main():
    parser = argparse.ArgumentParser(description="PDF Processing Work Splitter")
    parser.add_argument("--bucket", type=int, required=True, help="Bucket index (0, 1, or 2)")
    parser.add_argument("--total", type=int, default=3, help="Total number of workers (default: 3)")
    parser.add_argument("--skip-existing", action="store_true", default=True, help="Skip already processed JSON files")
    
    args = parser.parse_args()
    
    # 0. 환경 환경 체크 (API 키 등)
    if not check_environment():
        return
    
    print("\n" + "=" * 80)
    print(f"🚀 PDF 분산 처리 시작 (Worker: {args.bucket}/{args.total-1})")
    print("=" * 80 + "\n")
    
    # 1. 파일 목록 확보
    all_pdfs = get_pdf_files()
    target_pdfs, start, end = split_work(all_pdfs, args.bucket, args.total)
    
    logger.info(f"전체 PDF 수: {len(all_pdfs)}개")
    logger.info(f"담당 범위: {start} ~ {end-1} (총 {len(target_pdfs)}개)")
    
    if not target_pdfs:
        logger.warning("처리할 파일이 없습니다.")
        return

    # 2. 에이전트 초기화
    try:
        agent = KGConstructionAgent(
            data_dir=project_root / "data"
        )
        logger.info("✅ KGConstructionAgent 초기화 완료")
    except Exception as e:
        logger.error(f"❌ Agent 초기화 실패: {e}")
        return

    # 3. 파싱 실행 (PDF만)
    start_time = datetime.now()
    logger.info(f"⏰ 시작 시각: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # data_sources에 담당 구역 PDF 목록만 전달
        data_sources = {'pdf': target_pdfs}
        
        # construct_knowledge_graph를 실행하되, PDF 파싱 단계만 집중
        # load_to_neo4j=False로 설정 (나중에 한꺼번에 주입)
        result = agent.construct_knowledge_graph(
            data_sources=data_sources,
            auto_scan=False,
            load_to_neo4j=False,
            skip_existing=args.skip_existing
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "-" * 80)
        print(f"✅ 처리 완료!")
        print(f"⏱️  소요 시간: {duration:.2f}초")
        print(f"📊 성공: {result['parser_results']['pdf']['success']}개")
        print(f"📊 실패: {result['parser_results']['pdf']['failed']}개")
        print("-" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ 작업 도중 오류 발생: {e}")

if __name__ == "__main__":
    main()
