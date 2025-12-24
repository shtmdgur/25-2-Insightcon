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
        password: str = "password",
        batch_size: int = 1000,  # 배치 크기 설정
        store_null_properties: bool = True  # null 속성 저장 여부
    ):
        """
        Args:
            uri: Neo4j URI
            user: 사용자명
            password: 비밀번호
            batch_size: 배치 처리 크기 (기본 1000)
            store_null_properties: null 속성 저장 여부 (True=모든 속성, False=값 있는 것만)
        """
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.batch_size = batch_size
            self.store_null_properties = store_null_properties
            
            # Aura 인스턴스 Wake-up 대기 및 연결 검증
            self._verify_connection_with_retry(max_retries=3, delay=2)
            
            logger.info(f"Connected to Neo4j at {uri} (batch_size={batch_size}, store_null={store_null_properties})")
            
            # 성능 최적화: name 인덱스 생성
            self._ensure_indexes()
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise
    
    def _verify_connection_with_retry(self, max_retries: int = 3, delay: int = 2):
        """Aura 인스턴스 연결 검증 (Wake-up 대기 포함)"""
        import time
        
        for attempt in range(max_retries):
            try:
                with self.driver.session() as session:
                    result = session.run("RETURN 1 as test")
                    result.single()
                    return  # 성공
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Neo4j connection attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"Neo4j connection failed after {max_retries} attempts: {e}")
                    raise
    
    def _ensure_indexes(self):
        """필수 인덱스 생성 (성능 최적화)"""
        with self.driver.session() as session:
            try:
                # 모든 노드 타입에 대해 name 인덱스 생성
                node_types = ["IDM", "Fabless", "Foundry", "OSAT", "Supplier", "Organization", "ETC",
                             "Earnings", "PriceMovement", "Disclosure", "Issue", "EconomicIndicator"]
                
                for node_type in node_types:
                    query = f"CREATE INDEX {node_type}_name IF NOT EXISTS FOR (n:`{node_type}`) ON (n.name)"
                    session.run(query)
                
                logger.info("✅ Indexes created/verified for all node types")
            except Exception as e:
                logger.warning(f"Index creation failed (may already exist): {e}")
        
        # Vector Index 생성 (gemini-embedding-001: 768차원)
        self._ensure_vector_index()
    
    def _ensure_vector_index(self):
        """
        Neo4j Vector Index 생성 (gemini-embedding-001: 768차원)
        
        이 인덱스는 embedding 속성에 대한 벡터 검색을 지원합니다.
        """
        with self.driver.session() as session:
            try:
                # 모든 노드에 대한 범용 Vector Index 생성 시도
                # Neo4j 5.x+ 필요
                vector_query = """
                    CREATE VECTOR INDEX entity_embedding_index IF NOT EXISTS
                    FOR (n:Issue)
                    ON (n.embedding)
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 768,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                """
                session.run(vector_query)
                
                # 주요 노드 타입별 Vector Index 생성
                for node_type in ["Earnings", "PriceMovement", "Disclosure", "EconomicIndicator"]:
                    try:
                        query = f"""
                            CREATE VECTOR INDEX {node_type.lower()}_embedding_index IF NOT EXISTS
                            FOR (n:{node_type})
                            ON (n.embedding)
                            OPTIONS {{
                                indexConfig: {{
                                    `vector.dimensions`: 768,
                                    `vector.similarity_function`: 'cosine'
                                }}
                            }}
                        """
                        session.run(query)
                    except Exception:
                        pass  # 개별 인덱스 실패는 무시
                
                logger.info("✅ Vector indexes created/verified")
            except Exception as e:
                logger.warning(f"Vector index creation failed (requires Neo4j 5.x+): {e}")
    
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
                created_count = self._batch_create_relations(session, predicate, relations)
                stats["relationships_created"] += created_count
            
            return stats

    def _batch_upsert_static_entities(self, session, node_type: str, entities: List[Entity]):
        """정적 엔티티 배치 MERGE (null로 기존값 덮어쓰기 방지, 청킹 적용)"""
        
        query = f"""
        UNWIND $batch as row
        MERGE (n:`{node_type}` {{id: row.name}})
        ON CREATE SET 
            n.name = row.name,
            n.confidence = row.confidence,
            n.embedding = row.embedding,
            n.created_at = datetime()
        ON CREATE SET n += row.properties
        ON MATCH SET 
            n.confidence = COALESCE(row.confidence, n.confidence),
            n.embedding = COALESCE(row.embedding, n.embedding),
            n.last_updated = datetime()
        ON MATCH SET n += row.properties
        """
        all_data = [
            {
                "name": e.name,
                "confidence": e.confidence,
                "properties": self._filter_null_properties({
                    **e.properties,
                    **(e.fundamental_stats or {})
                }),
                "embedding": e.embedding
            } for e in entities
        ]
        
        # 청킹 처리: batch_size 단위로 분할 주입
        for i in range(0, len(all_data), self.batch_size):
            chunk = all_data[i:i + self.batch_size]
            session.run(query, batch=chunk)
            if len(all_data) > self.batch_size:
                logger.debug(f"Static {node_type}: chunk {i//self.batch_size + 1}/{(len(all_data)-1)//self.batch_size + 1}")
    
    def _filter_null_properties(self, props: dict) -> dict:
        """null 값을 필터링하여 기존 값을 보호"""
        return {k: v for k, v in props.items() if v is not None}

    def _batch_create_dynamic_entities(self, session, node_type: str, entities: List[Entity]):
        """동적 엔티티 배치 MERGE (v3.0: 날짜 기반 갱신, 청킹 적용)"""
        from datetime import datetime as dt
        now = dt.now().isoformat()
        
        # 날짜 기반 갱신: 최신 데이터만 반영
        query = f"""
        UNWIND $batch as row
        MERGE (n:`{node_type}` {{name: row.name}})
        ON CREATE SET 
            n.created_at = datetime($now),
            n.data_date = row.date,
            n.first_source = row.source,
            n.confidence = row.confidence,
            n.embedding = row.embedding
        ON CREATE SET n += row.properties
        ON MATCH SET 
            n.confidence = CASE WHEN row.date IS NULL OR row.date >= COALESCE(n.data_date, '1970-01-01') 
                           THEN row.confidence ELSE n.confidence END,
            n.embedding = CASE WHEN row.date IS NULL OR row.date >= COALESCE(n.data_date, '1970-01-01') 
                          THEN row.embedding ELSE n.embedding END,
            n.data_date = CASE WHEN row.date IS NULL OR row.date >= COALESCE(n.data_date, '1970-01-01') 
                          THEN row.date ELSE n.data_date END,
            n.last_updated = datetime($now)
        """
        all_data = [
            {
                "name": e.name,
                "date": e.date,
                "source": e.source,
                "confidence": e.confidence,
                "properties": self._build_entity_properties(e),
                "embedding": e.embedding
            } for e in entities
        ]
        
        # 청킹 처리: batch_size 단위로 분할 주입
        for i in range(0, len(all_data), self.batch_size):
            chunk = all_data[i:i + self.batch_size]
            session.run(query, batch=chunk, now=now)
            if len(all_data) > self.batch_size:
                logger.debug(f"Dynamic {node_type}: chunk {i//self.batch_size + 1}/{(len(all_data)-1)//self.batch_size + 1}")
    
    def _build_entity_properties(self, e: Entity) -> dict:
        """엔티티 속성 dict 생성 (null 필터링 옵션 적용)"""
        base_props = {
            "direction": e.direction,
            "magnitude": e.magnitude,
            "sentiment": e.sentiment,
            "source": e.source,
            "is_significant": e.is_significant,
            "relative_performance": e.relative_performance,
            "trigger": e.trigger,
            "description": e.description,
            **e.properties,
        }
        
        # null 필터링 옵션 확인
        if not self.store_null_properties:
            return {k: v for k, v in base_props.items() if v is not None}
        return base_props

    def _batch_create_relations(self, session, predicate: str, relations: List[Relation]) -> int:
        """관계 배치 MERGE (v3.0: 히스토리 누적 + 최신값 저장, 청킹 적용)"""
        query = f"""
        UNWIND $batch as row
        MATCH (source {{name: row.subject}})
        MATCH (target {{name: row.object}})
        MERGE (source)-[r:`{predicate}`]->(target)
        ON CREATE SET 
            r.created_at = row.date,
            r.first_source = row.source
        SET r.history = COALESCE(r.history, []) + [row.history_entry]
        SET r += row.latest_props
        RETURN count(r) as created
        """
        all_data = [
            {
                "subject": r.subject,
                "object": r.object,
                "date": r.date,
                "source": r.source,
                "history_entry": self._build_history_entry(r),
                "latest_props": self._build_latest_props(r)
            } for r in relations
        ]
        
        # 청킹 처리: batch_size 단위로 분할 주입
        total_created = 0
        for i in range(0, len(all_data), self.batch_size):
            chunk = all_data[i:i + self.batch_size]
            result = session.run(query, batch=chunk)
            created = result.single()["created"]
            total_created += created
            if len(all_data) > self.batch_size:
                logger.debug(f"Relations {predicate}: chunk {i//self.batch_size + 1}/{(len(all_data)-1)//self.batch_size + 1}")
        
        requested = len(relations)
        logger.info(f"Created/merged {total_created}/{requested} {predicate} relationships")
        
        # MATCH 실패 감지
        if total_created < requested:
            logger.warning(f"⚠️ {requested - total_created} {predicate} relationships failed - source/target nodes may not exist")
            if len(relations) > 0:
                logger.debug(f"Sample subjects: {[r.subject for r in relations[:3]]}")
        
        return total_created
    
    def _build_relation_properties(self, r: Relation) -> dict:
        """관계 속성 dict 생성 (null 필터링 옵션 적용)"""
        base_props = {
            "confidence": r.confidence,
            "source": r.source,
            "correlation": r.correlation,
            "sensitivity": r.sensitivity,
            "lag": r.lag,
            "reasoning": r.reasoning,
            "impact": r.impact,
            "dependency": r.dependency,
            "is_critical": r.is_critical,
            "supply_type": r.supply_type,
            "product": r.product,
            "importance": r.importance,
            "is_official": r.is_official,
            "market_segment": r.market_segment,
            "competitive_dynamic": r.competitive_dynamic,
            "partnership_type": r.partnership_type,
            "scope": r.scope,
            "investment_type": r.investment_type,
            "amount": r.amount,
            "stake_percentage": r.stake_percentage,
            **r.properties,
        }
        
        # null 필터링 옵션 확인
        if not self.store_null_properties:
            return {k: v for k, v in base_props.items() if v is not None}
        return base_props
    
    def _build_history_entry(self, r: Relation) -> str:
        """
        관계 히스토리 엔트리 생성 (날짜별 변경 이력 기록)
        
        히스토리 전략 (final_schema_v3.md 기준):
        - AFFECTS: correlation, sensitivity, lag → 변화 추적
        - TRIGGERED_BY: reasoning, impact → 변화 추적
        - 공통: date, source, confidence → 모든 히스토리에 포함
        
        Returns:
            JSON 문자열 (Neo4j는 Map을 속성으로 저장 불가)
        """
        import json
        
        entry = {
            "date": r.date,
            "source": r.source,
            "confidence": r.confidence
        }
        
        # 관계 타입별 히스토리 추적 필드
        if r.correlation is not None:
            entry["correlation"] = r.correlation
        if r.sensitivity is not None:
            entry["sensitivity"] = r.sensitivity
        if r.lag is not None:
            entry["lag"] = r.lag
        if r.reasoning is not None:
            entry["reasoning"] = r.reasoning
        if r.impact is not None:
            entry["impact"] = r.impact
            
        # null 필터링 적용
        if not self.store_null_properties:
            entry = {k: v for k, v in entry.items() if v is not None}
        
        # JSON 문자열로 변환 (Neo4j 저장용)
        return json.dumps(entry, ensure_ascii=False)
    
    def _build_latest_props(self, r: Relation) -> dict:
        """
        최신 속성값만 저장 (동적 갱신 필드)
        
        동적 전략 (final_schema_v3.md 기준):
        - confidence: 최신값 우선
        - correlation, sensitivity, lag: 최신값 우선
        - reasoning, impact: 최신값 우선
        """
        latest = {
            "confidence": r.confidence,
            "last_updated_date": r.date,
            "last_updated_source": r.source
        }
        
        # 관계별 동적 속성 (최신값만)
        relation_props = self._build_relation_properties(r)
        
        # date, source는 이미 처리했으므로 제외
        exclude_keys = {"date", "source"}
        for k, v in relation_props.items():
            if k not in exclude_keys:
                latest[k] = v
        
        return latest

    def _classify_entity_layer(self, entity: Entity) -> str:
        """
        Entity를 정적/동적 레이어로 분류
        
        Hybrid KG Architecture v3.0 기준:
        - **Static (MERGE)**: Agent Layer + MacroMetric Layer
        - **Dynamic (CREATE)**: Signal Layer
        """
        from ..models.nodes import NodeType
        
        STATIC_TYPES = {
            NodeType.IDM,
            NodeType.FABLESS,
            NodeType.FOUNDRY,
            NodeType.OSAT,  # v3.0 신규
            NodeType.SUPPLIER,
            NodeType.ORGANIZATION,
            NodeType.ETC,  # v3.1 신규: 반도체 외 기업
            NodeType.ECONOMIC_INDICATOR,
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
            # 디버깅: PriceMovement와 다른 Signal의 개수 확인
            debug_query = """
            MATCH (pm:PriceMovement)
            OPTIONAL MATCH (e:Earnings)
            OPTIONAL MATCH (d:Disclosure)
            RETURN count(DISTINCT pm) as pm_count, 
                   count(DISTINCT e) as earnings_count,
                   count(DISTINCT d) as disclosure_count
            """
            debug_result = session.run(debug_query)
            debug_data = debug_result.single()
            logger.info(f"Available signals - PriceMovement: {debug_data['pm_count']}, "
                       f"Earnings: {debug_data['earnings_count']}, "
                       f"Disclosure: {debug_data['disclosure_count']}")
            
            # 1. PriceMovement -> Earnings/Disclosure (TRIGGERED_BY)
            # properties 객체의 date 필드 접근
            query = f"""
            MATCH (company)-[:HAS_SIGNAL]->(pm:PriceMovement)
            MATCH (company)-[:HAS_SIGNAL]->(signal)
            WHERE (signal:Earnings OR signal:Disclosure)
              AND pm.properties IS NOT NULL
              AND signal.properties IS NOT NULL
              AND pm.properties.date IS NOT NULL 
              AND signal.properties.date IS NOT NULL
              AND abs(duration.between(
                  date(toString(pm.properties.date)), 
                  date(toString(signal.properties.date))
              ).days) <= $window
            MERGE (pm)-[r:TRIGGERED_BY]->(signal)
            SET r.reasoning = 'Temporal correlation',
                r.source = 'TemporalLinker',
                r.date_diff = abs(duration.between(
                  date(toString(pm.properties.date)), 
                  date(toString(signal.properties.date))
                ).days)
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
    
    # 1. PDF 파싱 (중앙 설정에서 모델명 가져오기)
    logger.info(f"Parsing PDF: {pdf_path}")
    from src.config.llm_config import get_model
    parser = GeminiPDFParser(model_name=get_model("pdf_parsing"))
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
