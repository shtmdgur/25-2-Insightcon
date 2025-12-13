"""
Seed Ontology 기반 Entity 및 Relation 모델 정의

환각(Hallucination)을 방지하기 위해 허용된 타입만 Enum으로 강제합니다.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class NodeType(str, Enum):
    """허용된 노드 타입 (Seed Ontology)"""
    COMPANY = "Company"
    PRODUCT = "Product"
    EVENT = "Event"
    METRIC = "Metric"
    TREND = "Trend"
    FINANCIAL = "Financial"


class RelationType(str, Enum):
    """허용된 관계 타입 (Seed Ontology)"""
    COMPETITOR_OF = "COMPETITOR_OF"
    SUPPLIER_OF = "SUPPLIER_OF"
    CUSTOMER_OF = "CUSTOMER_OF"
    MANUFACTURES = "MANUFACTURES"
    AFFECTS = "AFFECTS"
    HAS_METRIC = "HAS_METRIC"
    HAS_FINANCIAL = "HAS_FINANCIAL"
    HAS_TREND = "HAS_TREND"
    OCCURRED_AT = "OCCURRED_AT"
    RELATED_TO = "RELATED_TO"


class Entity(BaseModel):
    """
    엔티티 모델
    
    Neo4j 노드로 변환됩니다.
    """
    name: str = Field(description="엔티티 이름 (정규화된 이름)")
    type: NodeType = Field(description="엔티티 타입 (Enum으로 제한)")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="추가 속성 (ticker, description 등)"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="추출 신뢰도 (0.0~1.0)"
    )
    
    class Config:
        use_enum_values = True


class Relation(BaseModel):
    """
    관계 모델
    
    Neo4j 엣지로 변환됩니다.
    """
    subject: str = Field(description="주어 엔티티 이름")
    predicate: RelationType = Field(description="관계 타입 (Enum으로 제한)")
    object: str = Field(description="목적어 엔티티 이름")
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="관계 가중치 (0.0~1.0)"
    )
    source: Optional[str] = Field(
        default=None,
        description="출처 (예: 문서명, URL)"
    )
    
    class Config:
        use_enum_values = True


class KnowledgeGraph(BaseModel):
    """
    지식 그래프 모델
    
    LLM이 이 형식으로 구조화된 출력을 생성합니다.
    """
    entities: List[Entity] = Field(description="엔티티 목록")
    relations: List[Relation] = Field(description="관계 목록")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="메타데이터 (예: extraction_date, source_document)"
    )
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """이름으로 엔티티 조회"""
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None
    
    def get_relations_by_subject(self, subject: str) -> List[Relation]:
        """주어로 관계 조회"""
        return [r for r in self.relations if r.subject == subject]
    
    def get_relations_by_object(self, obj: str) -> List[Relation]:
        """목적어로 관계 조회"""
        return [r for r in self.relations if r.object == obj]


# 엔티티 타입별 기본 속성 정의
ENTITY_TYPE_PROPERTIES = {
    NodeType.COMPANY: ["ticker", "industry", "country"],
    NodeType.PRODUCT: ["category", "launch_date"],
    NodeType.EVENT: ["date", "event_type", "importance"],
    NodeType.METRIC: ["value", "unit", "period"],
    NodeType.TREND: ["pattern", "period", "trend_type"],
    NodeType.FINANCIAL: ["period", "revenue", "profit", "debt"]
}
