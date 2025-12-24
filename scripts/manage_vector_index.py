"""
Vector Index 관리 스크립트

Neo4j Vector Index 생성/삭제/확인 기능 제공.

사용법:
    # Vector Index 생성
    poetry run python scripts/manage_vector_index.py --create
    
    # Vector Index 상태 확인
    poetry run python scripts/manage_vector_index.py --status
    
    # Vector Index 삭제
    poetry run python scripts/manage_vector_index.py --delete
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# Vector Index 정의 (gemini-embedding-001: 768차원)
VECTOR_INDEXES = [
    {"name": "entity_embedding_index", "label": "Issue", "property": "embedding"},
    {"name": "earnings_embedding_index", "label": "Earnings", "property": "embedding"},
    {"name": "pricemovement_embedding_index", "label": "PriceMovement", "property": "embedding"},
    {"name": "disclosure_embedding_index", "label": "Disclosure", "property": "embedding"},
    {"name": "economicindicator_embedding_index", "label": "EconomicIndicator", "property": "embedding"},
]

VECTOR_DIMENSION = 768  # gemini-embedding-001


def get_neo4j_connection():
    """Neo4j 연결"""
    from neo4j import GraphDatabase
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver


def create_vector_indexes(driver):
    """Vector Index 생성"""
    print("\n" + "=" * 60)
    print("🔧 Vector Index 생성")
    print("=" * 60)
    
    with driver.session() as session:
        for idx_def in VECTOR_INDEXES:
            try:
                query = f"""
                    CREATE VECTOR INDEX {idx_def['name']} IF NOT EXISTS
                    FOR (n:{idx_def['label']})
                    ON (n.{idx_def['property']})
                    OPTIONS {{
                        indexConfig: {{
                            `vector.dimensions`: {VECTOR_DIMENSION},
                            `vector.similarity_function`: 'cosine'
                        }}
                    }}
                """
                session.run(query)
                print(f"  ✅ {idx_def['name']} (:{idx_def['label']}) - 생성됨")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ⚡ {idx_def['name']} - 이미 존재함")
                else:
                    print(f"  ❌ {idx_def['name']} - 실패: {e}")
    
    print("\n✅ Vector Index 생성 완료")


def check_vector_indexes(driver):
    """Vector Index 상태 확인"""
    print("\n" + "=" * 60)
    print("📊 Vector Index 상태")
    print("=" * 60)
    
    with driver.session() as session:
        try:
            result = session.run("SHOW INDEXES")
            indexes = list(result)
            
            vector_indexes = [idx for idx in indexes if idx.get("type") == "VECTOR"]
            
            if not vector_indexes:
                print("  ⚠️ Vector Index가 없습니다.")
            else:
                for idx in vector_indexes:
                    state = idx.get("state", "UNKNOWN")
                    name = idx.get("name", "UNKNOWN")
                    label = idx.get("labelsOrTypes", ["UNKNOWN"])[0] if idx.get("labelsOrTypes") else "UNKNOWN"
                    
                    status_emoji = "✅" if state == "ONLINE" else "⏳"
                    print(f"  {status_emoji} {name}")
                    print(f"     - Label: {label}")
                    print(f"     - State: {state}")
                    
        except Exception as e:
            print(f"  ❌ 인덱스 조회 실패: {e}")


def delete_vector_indexes(driver):
    """Vector Index 삭제"""
    print("\n" + "=" * 60)
    print("🗑️ Vector Index 삭제")
    print("=" * 60)
    
    with driver.session() as session:
        for idx_def in VECTOR_INDEXES:
            try:
                query = f"DROP INDEX {idx_def['name']} IF EXISTS"
                session.run(query)
                print(f"  ✅ {idx_def['name']} - 삭제됨")
            except Exception as e:
                print(f"  ❌ {idx_def['name']} - 실패: {e}")
    
    print("\n✅ Vector Index 삭제 완료")


def main():
    parser = argparse.ArgumentParser(description="Neo4j Vector Index 관리")
    parser.add_argument("--create", action="store_true", help="Vector Index 생성")
    parser.add_argument("--status", action="store_true", help="Vector Index 상태 확인")
    parser.add_argument("--delete", action="store_true", help="Vector Index 삭제")
    
    args = parser.parse_args()
    
    if not any([args.create, args.status, args.delete]):
        parser.print_help()
        return
    
    try:
        driver = get_neo4j_connection()
        print(f"✅ Neo4j 연결 성공: {os.getenv('NEO4J_URI')}")
        
        if args.create:
            create_vector_indexes(driver)
        
        if args.status:
            check_vector_indexes(driver)
        
        if args.delete:
            delete_vector_indexes(driver)
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Neo4j 연결 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
