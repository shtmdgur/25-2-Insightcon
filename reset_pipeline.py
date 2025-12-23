import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_pipeline():
    # 1. data/processed 디렉토리 초기화
    processed_dir = Path("data/processed")
    if processed_dir.exists():
        logger.info(f"Cleaning {processed_dir}...")
        for file in processed_dir.glob("*_kg.json"):
            file.unlink()
        for file in processed_dir.glob("merged_kg.json"):
            file.unlink()
    
    # 2. Neo4j 초기화
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, user, password]):
        logger.error("Neo4j connection info missing in environment variables.")
        return

    logger.info("Resetting Neo4j database...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:
            # 모든 노드와 관계 삭제
            session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j database cleared.")
    except Exception as e:
        logger.error(f"Failed to clear Neo4j: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    reset_pipeline()
