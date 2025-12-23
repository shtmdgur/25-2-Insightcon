"""
Preprocessed 데이터 Neo4j 로딩 스크립트

모든 preprocessed 폴더의 데이터를 파싱하여 Neo4j에 주입합니다.

실행 방법:
    # .env 파일에 NEO4J_PASSWORD 설정 후
    poetry run python scripts/load_preprocessed_to_neo4j.py
    
    # 또는 명령줄에서
    poetry run python scripts/load_preprocessed_to_neo4j.py --neo4j-password YOUR_PASSWORD

진행 순서:
    1. Agent Layer (정적): DART companies + Fund fundamentals
    2. Signal Layer (동적): Price movements + DART financials
    3. Document Layer: News
    4. PDF Reports: IR + Reports (샘플 5개씩, --pdf-limit으로 조절)
    5. Temporal Linking: 주가 변동 ↔ 뉴스/공시 연결
"""

import argparse
import logging
from pathlib import Path
from typing import List
import sys
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.parsers.dart_parser_agent import DARTParserAgent
# from src.agents.parsers.price_parser_agent import PriceParserAgent  # 사용 안 함
from src.agents.parsers.fund_parser_agent import FundParserAgent
from src.agents.parsers.news_parser_agent import NewsParserAgent
from src.agents.parsers.macro_parser_agent import MacroParserAgent  # ✅ 추가
from src.dataflows.neo4j_loader import Neo4jKGLoader, load_kg_from_gemini_pdf
from src.models.nodes import KnowledgeGraph

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_dart_data(data_dir: Path) -> KnowledgeGraph:
    """
    DART 데이터 로딩 (기업 정보 + 재무 데이터)
    
    Args:
        data_dir: preprocessed/dart 경로
    
    Returns:
        통합 KnowledgeGraph
    """
    logger.info("=" * 60)
    logger.info("Phase 1: DART 데이터 로딩 (Agent Layer)")
    logger.info("=" * 60)
    
    parser = DARTParserAgent()
    
    # DART 디렉토리 파싱 (companies + financial 통합)
    kg = parser.parse(data_dir)
    
    logger.info(f"✅ DART 데이터 파싱 완료:")
    logger.info(f"   - Entities: {len(kg.entities)}개")
    logger.info(f"   - Relations: {len(kg.relations)}개")
    
    return kg


def load_fund_data(file_path: Path) -> KnowledgeGraph:
    """
    펀더멘탈 데이터 로딩 (글로벌 기업)
    
    Args:
        file_path: global_semis_fundamentals.csv 경로
    
    Returns:
        KnowledgeGraph
    """
    logger.info("=" * 60)
    logger.info("Phase 2: 펀더멘탈 데이터 로딩 (Agent Layer)")
    logger.info("=" * 60)
    
    parser = FundParserAgent(save_as_snapshot=False)  # Agent 속성 업데이트 모드
    kg = parser.parse(file_path)
    
    logger.info(f"✅ 펀더멘탈 데이터 파싱 완료:")
    logger.info(f"   - Entities: {len(kg.entities)}개")
    logger.info(f"   - Relations: {len(kg.relations)}개")
    
    return kg


def load_news_data(file_path: Path) -> KnowledgeGraph:
    """
    뉴스 데이터 로딩 (NEWS Document)
    
    Args:
        file_path: News_processed.csv 경로
    
    Returns:
        KnowledgeGraph
    """
    logger.info("=" * 60)
    logger.info("Phase 4: 뉴스 데이터 로딩 (Document Layer)")
    logger.info("=" * 60)
    
    # LLM 초기화 (중앙 설정에서 모델명 가져오기)
    from langchain_google_genai import ChatGoogleGenerativeAI
    from src.config.llm_config import get_model
    llm = ChatGoogleGenerativeAI(model=get_model("news_parsing"))
    
    # 뉴스 샘플 수를 10개로 임시 하향 조정
    from src.config.parser_config import update_config
    update_config('news', sample_size=5)  # 테스트용
    
    parser = NewsParserAgent(llm=llm)  # LLM 전달
    kg = parser.parse(file_path)
    
    logger.info(f"✅ 뉴스 데이터 파싱 완료:")
    logger.info(f"   - Entities: {len(kg.entities)}개")
    logger.info(f"   - Relations: {len(kg.relations)}개")
    
    return kg


def load_macro_data(file_path: Path) -> KnowledgeGraph:
    """
    거시 지표 데이터 로딩 (MacroMetric Layer)
    
    Args:
        file_path: fred_rates.csv 경로
    
    Returns:
        KnowledgeGraph
    """
    logger.info("=" * 60)
    logger.info("Phase 5: 거시 지표 데이터 로딩 (MacroMetric Layer)")
    logger.info("=" * 60)
    
    parser = MacroParserAgent()
    kg = parser.parse(file_path)
    
    logger.info(f"✅ 거시 지표 데이터 파싱 완료:")
    logger.info(f"   - Entities: {len(kg.entities)}개")
    logger.info(f"   - Relations: {len(kg.relations)}개")
    
    return kg


def load_pdf_reports(data_dir: Path, limit: int = 5) -> List[KnowledgeGraph]:
    """
    PDF 리포트 로딩 (IR + Reports 샘플)
    
    Args:
        data_dir: preprocessed 폴더 경로
        limit: 각 폴더에서 가져올 PDF 개수
    
    Returns:
        KnowledgeGraph 리스트
    """
    logger.info("=" * 60)
    logger.info(f"Phase 5: PDF 리포트 로딩 (각 폴더에서 {limit}개 샘플)")
    logger.info("=" * 60)
    
    kgs = []
    
    # IR 폴더 (첫 번째 하위 디렉토리에서만)
    ir_dir = data_dir / "ir"
    if ir_dir.exists():
        # 첫 번째 회사 디렉토리에서만 처리
        subdirs = sorted([d for d in ir_dir.iterdir() if d.is_dir()])
        if subdirs:
            first_company_dir = subdirs[0]
            pdf_files = list(first_company_dir.glob("*.pdf"))[:limit]
            logger.info(f"IR 폴더 ({first_company_dir.name}): {len(pdf_files)}개 파일 처리")
        
        for pdf_file in pdf_files:
            try:
                from src.agents.parsers.pdf_parser_agent import GeminiPDFParser
                parser = GeminiPDFParser()
                result = parser.parse(str(pdf_file))
                kg = result["knowledge_graph"]
                kgs.append(kg)
                logger.info(f"   ✓ {pdf_file.name}: {len(kg.entities)}개 엔티티")
            except Exception as e:
                logger.warning(f"   ✗ {pdf_file.name}: {e}")
    
    # Reports 폴더
    reports_dir = data_dir / "reports"
    if reports_dir.exists():
        pdf_files = list(reports_dir.glob("*.pdf"))[:limit]
        logger.info(f"Reports 폴더: {len(pdf_files)}개 파일 처리")
        
        for pdf_file in pdf_files:
            try:
                from src.agents.parsers.pdf_parser_agent import GeminiPDFParser
                parser = GeminiPDFParser()
                result = parser.parse(str(pdf_file))
                kg = result["knowledge_graph"]
                kgs.append(kg)
                logger.info(f"   ✓ {pdf_file.name}: {len(kg.entities)}개 엔티티")
            except Exception as e:
                logger.warning(f"   ✗ {pdf_file.name}: {e}")
    
    logger.info(f"✅ PDF 리포트 파싱 완료: {len(kgs)}개 파일")
    return kgs


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="Preprocessed 데이터를 Neo4j에 로딩"
    )
    parser.add_argument(
        "--data-dir",
        default=os.getenv("DATA_DIR", "data/preprocessed"),
        help="Preprocessed 데이터 디렉토리 (기본: .env의 DATA_DIR 또는 data/preprocessed)"
    )
    parser.add_argument(
        "--neo4j-uri",
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        help="Neo4j URI (기본: .env의 NEO4J_URI 또는 bolt://localhost:7687)"
    )
    parser.add_argument(
        "--neo4j-user",
        default=os.getenv("NEO4J_USER", "neo4j"),
        help="Neo4j 사용자명 (기본: .env의 NEO4J_USER 또는 neo4j)"
    )
    parser.add_argument(
        "--neo4j-password",
        default=os.getenv("NEO4J_PASSWORD"),
        help="Neo4j 비밀번호 (.env의 NEO4J_PASSWORD 또는 명령줄 인자)"
    )
    parser.add_argument(
        "--temporal-window",
        type=int,
        default=int(os.getenv("TEMPORAL_WINDOW", "3")),
        help="Temporal Linking 시간 윈도우 (기본: .env의 TEMPORAL_WINDOW 또는 3일)"
    )
    parser.add_argument(
        "--pdf-limit",
        type=int,
        default=2,  # 테스트용 축소
        help="PDF 파일 처리 개수 제한 (기본: 5개, 0이면 스킵)"
    )
    
    args = parser.parse_args()
    
    # Neo4j 비밀번호 검증
    if not args.neo4j_password:
        logger.error("❌ Neo4j 비밀번호가 설정되지 않았습니다.")
        logger.error("   다음 중 하나를 수행하세요:")
        logger.error("   1. .env 파일에 NEO4J_PASSWORD=your_password 추가")
        logger.error("   2. 명령줄에서 --neo4j-password YOUR_PASSWORD 지정")
        sys.exit(1)
    
    # 경로 설정
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"❌ 데이터 디렉토리가 존재하지 않습니다: {data_dir}")
        return
    
    logger.info("🚀 Preprocessed 데이터 Neo4j 로딩 시작")
    logger.info(f"데이터 디렉토리: {data_dir.absolute()}")
    logger.info(f"Neo4j URI: {args.neo4j_uri}")
    
    try:
        # Neo4j 연결
        loader = Neo4jKGLoader(
            uri=args.neo4j_uri,
            user=args.neo4j_user,
            password=args.neo4j_password
        )
        
        # ============================================
        # Phase 1: LLM 추출 데이터 (먼저 로딩 - 나중에 덮어씀)
        # ============================================
        
        # 1. PDF 리포트 로딩 (LLM 추출 → 먼저 로딩)
        if args.pdf_limit > 0:
            pdf_kgs = load_pdf_reports(data_dir, limit=args.pdf_limit)
            for kg in pdf_kgs:
                loader.load_knowledge_graph(kg, use_dual_layer=True)
        else:
            logger.info("PDF 리포트 로딩 스킵 (--pdf-limit 0)")
        
        # 2. 뉴스 데이터 로딩 (Issue 노드)
        news_file = data_dir / "news" / "News_processed.csv"
        if news_file.exists():
            news_kg = load_news_data(news_file)
            loader.load_knowledge_graph(news_kg, use_dual_layer=True)
        else:
            logger.warning(f"⚠️  뉴스 파일 없음: {news_file}")
        
        # ============================================
        # Phase 2: 정형 데이터 (나중에 로딩 - 정확한 값으로 덮어씀)
        # ============================================
        
        # 3. DART 데이터 로딩 (기업 Master)
        dart_kg = load_dart_data(data_dir / "dart")
        loader.load_knowledge_graph(dart_kg, use_dual_layer=True)
        
        # 4. 펀더멘탈 데이터 로딩 (재무 속성 추가)
        fund_file = data_dir / "fund" / "global_semis_fundamentals.csv"
        if fund_file.exists():
            fund_kg = load_fund_data(fund_file)
            loader.load_knowledge_graph(fund_kg, use_dual_layer=True)
        else:
            logger.warning(f"⚠️  펀더멘탈 파일 없음: {fund_file}")
        
        # 5. 거시 지표 데이터 로딩 (raw 폴더에서 직접 로드)
        macro_file = Path("data/raw/macro/fred_rates.csv")
        if macro_file.exists():
            macro_kg = load_macro_data(macro_file)
            loader.load_knowledge_graph(macro_kg, use_dual_layer=True)
        else:
            logger.warning(f"⚠️  거시지표 파일 없음: {macro_file}")
        
        # 주가 데이터 로딩 (❌ 스킵 - 그래프 복잡도 방지)
        logger.info("⚠️  주가 데이터 로딩 스킵 (그래프 복잡도 방지)")
        
        # 5. Temporal Linking
        logger.info("=" * 60)
        logger.info(f"Phase 5: Temporal Linking (Window: ±{args.temporal_window}일)")
        logger.info("=" * 60)
        
        loader.link_temporal_signals(days_window=args.temporal_window)
        logger.info("✅ Temporal Linking 완료")
        
        # 6. 최종 통계
        logger.info("=" * 60)
        logger.info("📊 Neo4j 그래프 통계")
        logger.info("=" * 60)
        
        stats = loader.get_graph_stats()
        
        logger.info("노드 개수:")
        for label, count in stats.get("nodes_by_label", {}).items():
            logger.info(f"   - {label}: {count}개")
        
        logger.info("\n관계 개수:")
        for rel_type, count in stats.get("relationships_by_type", {}).items():
            logger.info(f"   - {rel_type}: {count}개")
        
        logger.info(f"\n총 노드: {stats.get('total_nodes', 0)}개")
        logger.info(f"총 관계: {stats.get('total_relationships', 0)}개")
        
        logger.info("=" * 60)
        logger.info("🎉 모든 데이터 로딩 완료!")
        logger.info("=" * 60)
        
        loader.close()
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
