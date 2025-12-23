import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

from src.agents.parsers.price_parser_agent import PriceParserAgent
from src.agents.parsers.news_parser_agent import NewsParserAgent
from src.agents.parsers.pdf_parser_agent import GeminiPDFParser
from src.dataflows.neo4j_loader import Neo4jKGLoader
from src.config.parser_config import update_config
from src.models.nodes import KnowledgeGraph

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration_poc():
    # 1. 환경 변수 로드
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    # 2. 테스트용 설정 변경 (샘플링 제한)
    update_config('price', sample_size=10) # 가격 데이터 최근 10일만
    update_config('news', sample_size=5)   # 뉴스 최근 5건만
    
    # 3. Neo4j 로더 초기화
    logger.info("Connecting to Neo4j...")
    loader = Neo4jKGLoader(uri=uri, user=username, password=password)
    loader.clear_database() # 검증을 위해 한 번 더 초기화
    
    try:
        # 4. 파서 에이전트들 초기화
        price_agent = PriceParserAgent()
        news_agent = NewsParserAgent() # LLM 없이 키워드 기반으로 우선 수행 (속도/비용 절감)
        from src.config.llm_config import get_model
        pdf_parser = GeminiPDFParser(model_name=get_model("pdf_parsing"))
        
        # --- [A] Price 데이터 파싱 ---
        logger.info("Parsing Price data (Samsung)...")
        price_kg = price_agent.parse(Path("data/raw/price/005930.KS_prices.csv"))
        loader.load_knowledge_graph(price_kg)
        
        # --- [C] News 데이터 파싱 (샘플링) ---
        logger.info("Parsing News data (Sampling 5 items)...")
        news_path = Path("data/raw/news/Semiconductor_News_Raw_20250225.csv")
        if news_path.exists():
            news_kg = news_agent.parse(news_path)
            loader.load_knowledge_graph(news_kg)
        
        # --- [D] Reports 데이터 파싱 (1개 샘플) ---
        logger.info("Parsing Report data (1 Sampling)...")
        reports_dir = Path("data/raw/reports")
        report_files = list(reports_dir.glob("*.pdf"))
        if report_files:
            sample_report = report_files[0]
            logger.info(f"Using sample report: {sample_report.name}")
            # parse() 결과가 Dict이므로 KnowledgeGraph로 변환
            report_raw = pdf_parser.parse(str(sample_report))
            # GeminiPDFParser.parse()는 {"knowledge_graph": KG, "metadata": ...} 형태를 반환함
            if isinstance(report_raw, dict) and "knowledge_graph" in report_raw:
                report_kg = report_raw["knowledge_graph"]
                loader.load_knowledge_graph(report_kg)
        
        # 5. Temporal Linking (가격 - 시그널 연결)
        logger.info("Running Temporal Linking...")
        loader.link_temporal_signals(days_window=3) # 전후 3일치 매칭
        
        # 6. 최종 통계 출력
        final_stats = loader.get_graph_stats()
        logger.info(f"Final Hybrid KG Stats: {final_stats}")
        
    finally:
        loader.close()

if __name__ == "__main__":
    run_migration_poc()
