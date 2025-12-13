"""
지식 그래프 구축 에이전트 (Seed Ontology 기반)

Pydantic 모델을 사용하여 구조화된 출력을 강제하고 환각을 방지합니다.
"""
from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
import json
import logging

from ..utils.neo4j_client import Neo4jClient
from ..models.nodes import KnowledgeGraph, Entity, Relation

logger = logging.getLogger(__name__)


class KGConstructionAgent:
    """
    문서에서 엔티티와 관계를 추출하여 지식 그래프를 구축하는 에이전트
    
    Seed Ontology 기반 추출로 환각(Hallucination) 방지
    """
    
    def __init__(self, llm: BaseChatModel, neo4j_client: Neo4jClient):
        """
        KGConstructionAgent 초기화
        
        Args:
            llm: LLM 모델 (엔티티/관계 추출에 사용)
            neo4j_client: Neo4j 클라이언트
        """
        self.llm = llm
        self.neo4j_client = neo4j_client
        self.parser = PydanticOutputParser(pydantic_object=KnowledgeGraph)
    
    def extract_entities(self, document: str, source: Optional[str] = None) -> KnowledgeGraph:
        """
        문서에서 엔티티 및 관계 추출 (Seed Ontology 기반)
        
        Args:
            document: 분석할 문서 텍스트
            source: 출처 (문서명 등)
        
        Returns:
            KnowledgeGraph 객체 (Pydantic 모델)
        """
        prompt = f"""
다음 문서에서 지식 그래프를 추출하세요.

문서:
{document}

지침:
1. 허용된 엔티티 타입만 사용하세요:
   - Company: 기업명
   - Product: 제품/서비스명
   - Event: 중요 이벤트 (실적 발표, M&A 등)
   - Metric: 재무 지표 (매출, 영업이익 등)
   - Trend: 시장 트렌드
   - Financial: 재무 정보 (분기별)

2. 허용된 관계 타입만 사용하세요:
   - COMPETITOR_OF: 경쟁 관계
   - SUPPLIER_OF: 공급 관계
   - MANUFACTURES: 제조 관계
   - AFFECTS: 영향 관계
   - HAS_METRIC: 지표 보유
   - HAS_FINANCIAL: 재무 정보 보유
   - HAS_TREND: 트렌드 보유

3. 엔티티 이름은 정규화하세요 (예: "삼성" → "삼성전자")

4. 관계는 문서에서 **명시적으로 언급된 것만** 추출하세요.

{self.parser.get_format_instructions()}
"""
        
        try:
            response = self.llm.invoke(prompt)
            kg = self.parser.parse(response.content)
            
            # 메타데이터 추가
            kg.metadata = {
                "source": source or "unknown",
                "extraction_method": "seed_ontology"
            }
            
            logger.info(f"Extracted {len(kg.entities)} entities and {len(kg.relations)} relations")
            return kg
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            # Fallback: 빈 KG 반환
            return KnowledgeGraph(
                entities=[],
                relations=[],
                metadata={"error": str(e)}
            )
    
    def inject_to_neo4j(self, kg: KnowledgeGraph) -> Dict[str, int]:
        """
        추출된 Knowledge Graph를 Neo4j에 주입
        
        Args:
            kg: KnowledgeGraph 객체
        
        Returns:
            주입된 엔티티 및 관계 개수
        """
        stats = {
            "entities": 0,
            "relations": 0,
            "errors": 0
        }
        
        # 1. 엔티티 주입
        for entity in kg.entities:
            try:
                # MERGE 쿼리 생성 (중복 방지)
                query = f"""
                MERGE (e:{entity.type.value} {{name: $name}})
                SET e += $properties,
                    e.confidence = $confidence,
                    e.last_updated = datetime()
                """
                
                params = {
                    "name": entity.name,
                    "properties": entity.properties,
                    "confidence": entity.confidence
                }
                
                self.neo4j_client.run(query, params)
                stats["entities"] += 1
                
            except Exception as e:
                logger.error(f"Failed to inject entity {entity.name}: {str(e)}")
                stats["errors"] += 1
        
        # 2. 관계 주입
        for relation in kg.relations:
            try:
                # 주어와 목적어가 존재하는지 확인 후 관계 생성
                query = f"""
                MATCH (s {{name: $subject}})
                MATCH (o {{name: $object}})
                MERGE (s)-[r:{relation.predicate.value}]->(o)
                SET r.weight = $weight,
                    r.source = $source,
                    r.last_updated = datetime()
                """
                
                params = {
                    "subject": relation.subject,
                    "object": relation.object,
                    "weight": relation.weight,
                    "source": relation.source or "unknown"
                }
                
                self.neo4j_client.run(query, params)
                stats["relations"] += 1
                
            except Exception as e:
                logger.error(
                    f"Failed to inject relation "
                    f"{relation.subject} -[{relation.predicate.value}]-> {relation.object}: "
                    f"{str(e)}"
                )
                stats["errors"] += 1
        
        return stats
    
    def process_document(self, document: str, source: Optional[str] = None) -> Dict[str, Any]:
        """
        문서를 처리하여 지식 그래프 구축
        
        Args:
            document: 처리할 문서
            source: 출처
        
        Returns:
            처리 결과 (KG, 통계 등)
        """
        # 엔티티 추출
        kg = self.extract_entities(document, source)
        
        # Neo4j에 주입
        stats = self.inject_to_neo4j(kg)
        
        return {
            "knowledge_graph": kg.dict(),
            "stats": stats
        }
