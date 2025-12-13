"""
Neo4j Knowledge Graph Loader

Gemini PDF Parser가 추출한 Knowledge Graph를 Neo4j에 주입합니다.
"""
import logging
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from ..models.graph_schema import KnowledgeGraph, Entity, Relation

logger = logging.getLogger(__name__)


class Neo4jKGLoader:
    """
    Knowledge Graph를 Neo4j에 로드하는 클래스
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ):
        """
        Args:
            uri: Neo4j URI
            user: 사용자명
            password: 비밀번호
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logger.info(f"Connected to Neo4j at {uri}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def load_knowledge_graph(
        self,
        kg: KnowledgeGraph,
        clear_existing: bool = False
    ) -> Dict[str, int]:
        """
        Knowledge Graph를 Neo4j에 로드
        
        Args:
            kg: KnowledgeGraph 객체
            clear_existing: 기존 데이터 삭제 여부
        
        Returns:
            {"nodes_created": N, "relationships_created": M}
        """
        with self.driver.session() as session:
            stats = {"nodes_created": 0, "relationships_created": 0}
            
            # 기존 데이터 삭제 (옵션)
            if clear_existing:
                logger.warning("Clearing existing graph data...")
                session.run("MATCH (n) DETACH DELETE n")
            
            # 1. 엔티티(노드) 생성
            logger.info(f"Loading {len(kg.entities)} entities...")
            for entity in kg.entities:
                self._create_entity(session, entity)
                stats["nodes_created"] += 1
            
            # 2. 관계(엣지) 생성
            logger.info(f"Loading {len(kg.relations)} relations...")
            for relation in kg.relations:
                self._create_relation(session, relation)
                stats["relationships_created"] += 1
            
            logger.info(
                f"Graph loaded successfully: "
                f"{stats['nodes_created']} nodes, "
                f"{stats['relationships_created']} relationships"
            )
            
            return stats
    
    def _create_entity(self, session, entity: Entity):
        """엔티티(노드) 생성"""
        import json
        
        # properties가 JSON 문자열이면 파싱
        props = {}
        if entity.properties:
            try:
                props = json.loads(entity.properties)
            except:
                props = {"raw": entity.properties}
        
        query = f"""
        MERGE (n:`{entity.label}` {{id: $id}})
        SET n.name = $name
        SET n += $properties
        RETURN n
        """
        
        session.run(
            query,
            id=entity.id,
            name=entity.name,
            properties=props
        )
    
    def _create_relation(self, session, relation: Relation):
        """관계(엣지) 생성"""
        import json
        
        # properties가 JSON 문자열이면 파싱
        props = {}
        if relation.properties:
            try:
                props = json.loads(relation.properties)
            except:
                props = {"raw": relation.properties}
        
        query = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        MERGE (source)-[r:`{relation.type}`]->(target)
        SET r += $properties
        RETURN r
        """
        
        session.run(
            query,
            source_id=relation.source_id,
            target_id=relation.target_id,
            properties=props
        )
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """그래프 통계 조회"""
        with self.driver.session() as session:
            # 노드 수
            node_count_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_count_result.single()["count"]
            
            # 관계 수
            rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_count_result.single()["count"]
            
            # 라벨별 노드 수
            label_stats_result = session.run("""
                MATCH (n)
                UNWIND labels(n) as label
                RETURN label, count(*) as count
                ORDER BY count DESC
            """)
            label_stats = {record["label"]: record["count"] for record in label_stats_result}
            
            # 관계 타입별 수
            rel_type_stats_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
            """)
            rel_type_stats = {record["type"]: record["count"] for record in rel_type_stats_result}
            
            return {
                "total_nodes": node_count,
                "total_relationships": rel_count,
                "nodes_by_label": label_stats,
                "relationships_by_type": rel_type_stats
            }


def load_kg_from_gemini_pdf(
    pdf_path: str,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password",
    clear_existing: bool = False
) -> Dict[str, Any]:
    """
    PDF → Gemini 파싱 → Neo4j 주입 전체 파이프라인
    
    Args:
        pdf_path: PDF 파일 경로
        neo4j_uri: Neo4j URI
        neo4j_user: Neo4j 사용자명
        neo4j_password: Neo4j 비밀번호
        clear_existing: 기존 데이터 삭제 여부
    
    Returns:
        {
            "parser_result": {...},
            "load_stats": {...},
            "graph_stats": {...}
        }
    """
    from .parsers.gemini_pdf import GeminiPDFParser
    
    # 1. PDF 파싱
    logger.info(f"Parsing PDF: {pdf_path}")
    parser = GeminiPDFParser(model_name="gemini-2.5-flash")
    parse_result = parser.parse(pdf_path)
    
    kg = parse_result["knowledge_graph"]
    
    # 2. Neo4j 로드
    logger.info("Loading to Neo4j...")
    loader = Neo4jKGLoader(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
    
    try:
        load_stats = loader.load_knowledge_graph(kg, clear_existing=clear_existing)
        graph_stats = loader.get_graph_stats()
    finally:
        loader.close()
    
    return {
        "parser_result": parse_result["metadata"],
        "load_stats": load_stats,
        "graph_stats": graph_stats
    }
