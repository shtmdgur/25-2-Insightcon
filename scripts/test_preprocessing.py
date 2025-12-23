"""
Preprocessed 데이터 파싱 테스트 (Neo4j 없이)

Neo4j 연결 없이 데이터 파싱만 테스트합니다.

실행 방법:
    python scripts/test_preprocessing.py
"""

import logging
from pathlib import Path
import sys

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.parsers.dart_parser_agent import DARTParserAgent
from src.agents.parsers.price_parser_agent import PriceParserAgent
from src.agents.parsers.fund_parser_agent import FundParserAgent
from src.utils.ticker_mapping import get_company_name, get_node_type

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ticker_mapping():
    """Ticker 매핑 테스트"""
    logger.info("=" * 60)
    logger.info("Ticker 매핑 테스트")
    logger.info("=" * 60)
    
    test_tickers = [
        "005930.KS", "000660.KS", "000990.KS",  # 한국
        "NVDA", "TSM", "INTC", "AMD", "ASML"  # 글로벌
    ]
    
    for ticker in test_tickers:
        company_name = get_company_name(ticker)
        node_type = get_node_type(company_name)
        logger.info(f"{ticker:12} → {company_name:30} → {node_type.value}")
    
    logger.info("✅ Ticker 매핑 테스트 통과\n")


def test_dart_parsing():
    """DART 데이터 파싱 테스트"""
    logger.info("=" * 60)
    logger.info("DART 데이터 파싱 테스트")
    logger.info("=" * 60)
    
    dart_dir = Path("data/preprocessed/dart")
    
    if not dart_dir.exists():
        logger.warning(f"⚠️  DART 디렉토리 없음: {dart_dir}")
        return
    
    parser = DARTParserAgent()
    kg = parser.parse(dart_dir)
    
    logger.info(f"Entities: {len(kg.entities)}개")
    logger.info(f"Relations: {len(kg.relations)}개")
    
    # 엔티티 타입별 개수
    from collections import Counter
    type_counts = Counter(e.type.value for e in kg.entities)
    
    for node_type, count in type_counts.most_common():
        logger.info(f"  - {node_type}: {count}개")
    
    logger.info("✅ DART 파싱 테스트 통과\n")


def test_fund_parsing():
    """펀더멘탈 데이터 파싱 테스트"""
    logger.info("=" * 60)
    logger.info("펀더멘탈 데이터 파싱 테스트")
    logger.info("=" * 60)
    
    fund_file = Path("data/preprocessed/fund/global_semis_fundamentals.csv")
    
    if not fund_file.exists():
        logger.warning(f"⚠️  펀더멘탈 파일 없음: {fund_file}")
        return
    
    parser = FundParserAgent(save_as_snapshot=False)
    kg = parser.parse(fund_file)
    
    logger.info(f"Entities: {len(kg.entities)}개")
    
    # 엔티티 샘플 출력
    for entity in kg.entities[:5]:
        logger.info(f"  - {entity.name} ({entity.type.value})")
        if entity.fundamental_stats:
            logger.info(f"    fundamental_stats: {len(entity.fundamental_stats)} 항목")
    
    # NodeType 분포
    from collections import Counter
    type_counts = Counter(e.type.value for e in kg.entities)
    
    logger.info("\nNodeType 분포:")
    for node_type, count in type_counts.most_common():
        logger.info(f"  - {node_type}: {count}개")
    
    logger.info("✅ 펀더멘탈 파싱 테스트 통과\n")


def test_price_parsing():
    """주가 데이터 파싱 테스트"""
    logger.info("=" * 60)
    logger.info("주가 데이터 파싱 테스트")
    logger.info("=" * 60)
    
    price_dir = Path("data/preprocessed/price")
    
    if not price_dir.exists():
        logger.warning(f"⚠️  주가 디렉토리 없음: {price_dir}")
        return
    
    parser = PriceParserAgent()
    price_files = list(price_dir.glob("*.csv"))[:3]  # 샘플 3개만
    
    logger.info(f"테스트 파일: {len(price_files)}개")
    
    for file_path in price_files:
        try:
            kg = parser.parse(file_path)
            
            # PRICE_MOVEMENT Signal만 카운트
            price_movements = [e for e in kg.entities if e.type.value == "PriceMovement"]
            
            logger.info(f"  ✓ {file_path.name}: {len(price_movements)}개 Signal")
            
            # 첫 번째 Signal 샘플
            if price_movements:
                pm = price_movements[0]
                logger.info(f"    샘플: {pm.name}")
                logger.info(f"    direction={pm.direction}, magnitude={pm.magnitude}, sentiment={pm.sentiment}")
        
        except Exception as e:
            logger.error(f"  ✗ {file_path.name}: {e}")
    
    logger.info("✅ 주가 파싱 테스트 통과\n")


def main():
    """메인 실행 함수"""
    logger.info("🧪 Preprocessed 데이터 파싱 테스트 시작\n")
    
    try:
        test_ticker_mapping()
        test_dart_parsing()
        test_fund_parsing()
        test_price_parsing()
        
        logger.info("=" * 60)
        logger.info("🎉 모든 테스트 통과!")
        logger.info("=" * 60)
        logger.info("\nNeo4j 로딩을 실행하려면:")
        logger.info("  python scripts/load_preprocessed_to_neo4j.py --neo4j-password YOUR_PASSWORD")
        
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
