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
    
    def load_knowledge_graph(
        self,
        kg: KnowledgeGraph,
        use_dual_layer: bool = True
    ) -> Dict[str, int]:
        """
        Knowledge Graph를 Neo4j에 UPSERT 방식으로 로드
        
        전략:
        - use_dual_layer=True: 정적(MERGE)/동적(CREATE) 분리
        - use_dual_layer=False: 모두 MERGE (기존 방식)
        
        Args:
            kg: KnowledgeGraph 객체
            use_dual_layer: 이중 레이어 전략 사용 여부
        
        Returns:
            {
                "static_nodes": N,
                "dynamic_nodes": M,
                "relationships_created": K
            }
        """
        with self.driver.session() as session:
            stats = {
                "static_nodes": 0,
                "dynamic_nodes": 0,
                "relationships_created": 0
            }
            
            # 1. 엔티티(노드) 생성
            logger.info(f"Loading {len(kg.entities)} entities...")
            for entity in kg.entities:
                if use_dual_layer:
                    # 이중 레이어: 정적/동적 분리
                    layer = self._classify_entity_layer(entity)
                    if layer == 'static':
                        self._upsert_static_entity(session, entity)
                        stats["static_nodes"] += 1
                    else:
                        self._create_dynamic_entity(session, entity)
                        stats["dynamic_nodes"] += 1
                else:
                    # 단일 레이어: 모두 MERGE
                    self._create_entity(session, entity)
                    stats["static_nodes"] += 1
            
            # 2. 관계(엣지) 생성
            logger.info(f"Loading {len(kg.relations)} relations...")
            for relation in kg.relations:
                self._create_relation(session, relation)
                stats["relationships_created"] += 1
            
            logger.info(
                f"Graph loaded successfully: "
                f"{stats.get('static_nodes', 0)} static nodes, "
                f"{stats.get('dynamic_nodes', 0)} dynamic nodes, "
                f"{stats['relationships_created']} relationships"
            )
            
            return stats
    
    def _classify_entity_layer(self, entity: Entity) -> str:
        """
        Entity를 정적/동적 레이어로 분류
        
        T-Box 2.0 기반 분류:
        - **Dynamic (CREATE)**: 시간 종속적 노드 (Observation, Event, Metric 등)
        - **Static (MERGE)**: 시간 불변 노드 (Company, Product, Technology 등)
        
        Args:
            entity: Entity 객체
        
        Returns:
            'static' (MERGE) 또는 'dynamic' (CREATE)
        """
        from ..models.nodes import NodeType
        
        # 동적 타입: 시간 종속적 노드 (T-Box 2.0 기준)
        DYNAMIC_TYPES = {
            # Occurrent (시간 종속)
            NodeType.OBSERVATION,
            NodeType.TEMPORAL_REGION,
            
            # Event 계층
            NodeType.EVENT,
            NodeType.STRATEGIC_ACTION,
            NodeType.CORPORATE_EVENT,
            NodeType.MARKET_ENVIRONMENT,
            NodeType.POLICY_EVENT,
            
            # Quality - Metric 계층 (시계열 데이터)
            NodeType.FINANCIAL_METRIC,
            NodeType.TECHNICAL_METRIC,
            NodeType.MARKET_METRIC,
            NodeType.METRIC,  # Generic
            
            # Trend
            NodeType.TREND,
        }
        
        # 동적 타입이면 'dynamic', 아니면 'static'
        return 'dynamic' if entity.type in DYNAMIC_TYPES else 'static'
    
    def _create_entity(self, session, entity: Entity):
        """엔티티(노드) 생성 (기존 방식 - MERGE)"""
        # properties는 이미 dict로 제공됨 (nodes.py Entity.properties)
        query = f"""
        MERGE (n:`{entity.type.value}` {{id: $id}})
        SET n.name = $name
        SET n += $properties
        SET n.confidence = $confidence
        RETURN n
        """
        
        session.run(
            query,
            id=entity.name,  # nodes.py에서는 name을 id로 사용
            name=entity.name,
            properties=entity.properties,
            confidence=entity.confidence
        )
    
    def _upsert_static_entity(self, session, entity: Entity):
        """
        정적 Entity 주입
        
        전략: MERGE (중복 방지, 업데이트)
        - Company, Product, Technology, Person
        - 같은 id면 기존 노드 업데이트
        """
        query = f"""
        MERGE (n:`{entity.type.value}` {{id: $id}})
        SET n.name = $name
        SET n += $properties
        SET n.confidence = $confidence
        SET n.last_updated = datetime()
        RETURN n
        """
        
        session.run(
            query,
            id=entity.name,
            name=entity.name,
            properties=entity.properties,
            confidence=entity.confidence
        )
    
    def _create_dynamic_entity(self, session, entity: Entity):
        """
        동적 Entity 주입
        
        전략: CREATE (시계열 누적)
        - Observation, TemporalRegion
        - Event, StrategicAction, CorporateEvent, MarketEnvironment
        - FinancialMetric, TechnicalMetric, MarketMetric
        - Trend
        
        매번 새 노드 생성 (시간 속성 필수)
        """
        from datetime import datetime as dt
        
        query = f"""
        CREATE (n:`{entity.type.value}`)
        SET n.name = $name
        SET n += $properties
        SET n.confidence = $confidence
        SET n.created_at = datetime($created_at)
        RETURN n
        """
        
        session.run(
            query,
            name=entity.name,
            properties=entity.properties,
            confidence=entity.confidence,
            created_at=dt.now().isoformat()
        )
    
    def _create_relation(self, session, relation: Relation):
        """관계(엣지) 생성"""
        # properties는 이미 dict로 제공됨
        props = {}
        if relation.weight != 1.0:
            props["weight"] = relation.weight
        if relation.source:
            props["source"] = relation.source
        
        query = f"""
        MATCH (source {{id: $source_id}})
        MATCH (target {{id: $target_id}})
        MERGE (source)-[r:`{relation.predicate.value}`]->(target)
        SET r += $properties
        RETURN r
        """
        
        session.run(
            query,
            source_id=relation.subject,
            target_id=relation.object,
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
