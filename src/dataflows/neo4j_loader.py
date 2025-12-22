"""
Neo4j Knowledge Graph Loader

모든 Parser Agent(PDF, Price, DART, News, Macro, Fund)가 생성한 Knowledge Graph를 Neo4j에 주입합니다.

주요 기능:
- 이중 레이어 전략: 정적 엔티티(MERGE) / 동적 엔티티(CREATE)
- JSON 파일 배치 로드 및 병합
- UPSERT 전략으로 데이터 누적 관리
"""
import logging
from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from ..models.nodes import KnowledgeGraph, Entity, Relation

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
            
    def clear_database(self):
        """데이터베이스의 모든 노드와 관계 삭제 (위험 - 초기화 전용)"""
        with self.driver.session() as session:
            logger.warning("Clearing all data from Neo4j database...")
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared.")
    
    def load_knowledge_graph(
        self,
        kg: KnowledgeGraph,
        use_dual_layer: bool = True
    ) -> Dict[str, int]:
        """
        Knowledge Graph를 Neo4j에 배치 방식으로 로드
        """
        with self.driver.session() as session:
            stats = {
                "static_nodes": 0,
                "dynamic_nodes": 0,
                "relationships_created": 0
            }
            
            # 1. 엔티티 분류 및 배치 처리
            static_groups = {}
            dynamic_groups = {}
            
            for entity in kg.entities:
                layer = self._classify_entity_layer(entity)
                if layer == 'static':
                    static_groups.setdefault(entity.type.value, []).append(entity)
                else:
                    dynamic_groups.setdefault(entity.type.value, []).append(entity)
            
            for node_type, entities in static_groups.items():
                logger.info(f"Batch upserting {len(entities)} static nodes of type {node_type}...")
                self._batch_upsert_static_entities(session, node_type, entities)
                stats["static_nodes"] += len(entities)
                
            for node_type, entities in dynamic_groups.items():
                logger.info(f"Batch creating {len(entities)} dynamic nodes of type {node_type}...")
                self._batch_create_dynamic_entities(session, node_type, entities)
                stats["dynamic_nodes"] += len(entities)
            
            # 2. 관계 분류 및 배치 처리
            rel_groups = {}
            for relation in kg.relations:
                rel_groups.setdefault(relation.predicate.value, []).append(relation)
                
            for predicate, relations in rel_groups.items():
                logger.info(f"Batch creating {len(relations)} relations of type {predicate}...")
                self._batch_create_relations(session, predicate, relations)
                stats["relationships_created"] += len(relations)
            
            return stats

    def _batch_upsert_static_entities(self, session, node_type: str, entities: List[Entity]):
        """정적 엔티티 배치 MERGE"""
        query = f"""
        UNWIND $batch as row
        MERGE (n:`{node_type}` {{id: row.name}})
        SET n.name = row.name,
            n.confidence = row.confidence,
            n.fundamental_stats = row.fundamental_stats,
            n.embedding = row.embedding,
            n.last_updated = datetime()
        SET n += row.properties
        """
        batch_data = [
            {
                "name": e.name,
                "confidence": e.confidence,
                "properties": e.properties,
                "fundamental_stats": e.fundamental_stats,
                "embedding": e.embedding
            } for e in entities
        ]
        session.run(query, batch=batch_data)

    def _batch_create_dynamic_entities(self, session, node_type: str, entities: List[Entity]):
        """동적 엔티티 배치 CREATE"""
        from datetime import datetime as dt
        now = dt.now().isoformat()
        
        query = f"""
        UNWIND $batch as row
        CREATE (n:`{node_type}`)
        SET n.name = row.name,
            n.confidence = row.confidence,
            n.direction = row.direction,
            n.magnitude = row.magnitude,
            n.sentiment = row.sentiment,
            n.embedding = row.embedding,
            n.created_at = datetime($now)
        SET n += row.properties
        """
        batch_data = [
            {
                "name": e.name,
                "confidence": e.confidence,
                "properties": e.properties,
                "direction": e.direction,
                "magnitude": e.magnitude,
                "sentiment": e.sentiment,
                "embedding": e.embedding
            } for e in entities
        ]
        session.run(query, batch=batch_data, now=now)

    def _batch_create_relations(self, session, predicate: str, relations: List[Relation]):
        """관계 배치 MERGE"""
        query = f"""
        UNWIND $batch as row
        MATCH (source {{name: row.subject}})
        MATCH (target {{name: row.object}})
        MERGE (source)-[r:`{predicate}`]->(target)
        SET r += row.properties
        """
        batch_data = [
            {
                "subject": r.subject,
                "object": r.object,
                "properties": {
                    **r.properties,
                    **{k: v for k, v in {
                        "correlation": r.correlation,
                        "sensitivity": r.sensitivity,
                        "lag": r.lag,
                        "confidence": r.confidence,
                        "reasoning": r.reasoning
                    }.items() if v is not None}
                }
            } for r in relations
        ]
        session.run(query, batch=batch_data)

    def _classify_entity_layer(self, entity: Entity) -> str:
        """
        Entity를 정적/동적 레이어로 분류
        
        Hybrid KG Architecture 기준:
        - **Static (MERGE)**: Agent Layer (IDM, Fabless, Foundry, Supplier, Organization)
        - **Dynamic (CREATE)**: Signal, MacroMetric, Document Layer
        """
        from ..models.nodes import NodeType
        
        STATIC_TYPES = {
            NodeType.IDM,
            NodeType.FABLESS,
            NodeType.FOUNDRY,
            NodeType.SUPPLIER,
            NodeType.ORGANIZATION,
            NodeType.AGENT,  # Legacy
            NodeType.COMPANY  # Legacy
        }
        
        return 'static' if entity.type in STATIC_TYPES else 'dynamic'
    
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
    
    def load_from_json_files(self, json_paths: List[str], merge: bool = True) -> Dict[str, int]:
        """
        JSON 파일들을 로드하여 Neo4j에 주입
        
        Args:
            json_paths: JSON 파일 경로 리스트
            merge: True면 병합 후 주입, False면 개별 주입
        
        Returns:
            주입 통계
        """
        from pathlib import Path
        from .kg_merger import KGMerger
        
        if merge and len(json_paths) > 1:
            # 병합 후 주입
            logger.info(f"Merging {len(json_paths)} JSON files...")
            merger = KGMerger()
            kg = merger.merge_knowledge_graphs([Path(p) for p in json_paths])
        else:
            # 단일 파일 로드
            kg = KnowledgeGraph.load_from_json(json_paths[0])
        
        # Neo4j에 주입
        return self.load_knowledge_graph(kg)
    
    def link_temporal_signals(self, days_window: int = 0):
        """
        주가 변동(PriceMovement)과 다른 시그널(Event, Issue 등)을 날짜/기업 기준으로 연결
        
        Args:
            days_window: 날짜 매칭 허용 오차 (0 = 당일 일치)
        """
        logger.info(f"Linking temporal signals (window={days_window} days)...")
        
        with self.driver.session() as session:
            # 1. PriceMovement -> Event/Issue/Earnings/Disclosure (TRIGGERED_BY)
            # 같은 기업(HAS_SIGNAL)에 속하고, 날짜가 같은 경우 연결
            query = f"""
            MATCH (company)-[:HAS_SIGNAL]->(p:PriceMovement)
            MATCH (company)-[:HAS_SIGNAL]->(s)
            WHERE (s:Event OR s:Issue OR s:Earnings OR s:Disclosure)
              AND p.date IS NOT NULL 
              AND s.date IS NOT NULL
              AND abs(duration.between(date(p.date), date(s.date)).days) <= $window
            MERGE (p)-[r:TRIGGERED_BY]->(s)
            SET r.reasoning = 'Temporal correlation (same day or within window)',
                r.source = 'TemporalLinker'
            RETURN count(r) as links
            """
            
            result = session.run(query, window=days_window)
            links = result.single()["links"]
            logger.info(f"Created {links} TRIGGERED_BY links between PriceMovement and Signals.")
            
            return links


def load_kg_from_gemini_pdf(
    pdf_path: str,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password"
) -> Dict[str, Any]:
    """
    PDF → Gemini 파싱 → Neo4j 주입 전체 파이프라인
    
    UPSERT 전략으로 기존 그래프에 데이터 누적
    
    Args:
        pdf_path: PDF 파일 경로
        neo4j_uri: Neo4j URI
        neo4j_user: Neo4j 사용자명
        neo4j_password: Neo4j 비밀번호
    
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
        load_stats = loader.load_knowledge_graph(kg)
        graph_stats = loader.get_graph_stats()
    finally:
        loader.close()
    
    return {
        "parser_result": parse_result["metadata"],
        "load_stats": load_stats,
        "graph_stats": graph_stats
    }
