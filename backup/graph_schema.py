"""
Knowledge Graph Schema for Gemini Structured Output

Gemini PDF Native Parser가 출력할 JSON 스키마 정의
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class NodeLabel(str, Enum):
    """Neo4j 노드 라벨"""
    COMPANY = "Company"
    PRODUCT = "Product"
    METRIC = "Metric"
    EVENT = "Event"
    TREND = "Trend"
    PERSON = "Person"
    TECHNOLOGY = "Technology"


class RelationType(str, Enum):
    """Neo4j 관계 타입"""
    PRODUCES = "PRODUCES"
    COMPETES_WITH = "COMPETES_WITH"
    SUPPLIES_TO = "SUPPLIES_TO"
    HAS_METRIC = "HAS_METRIC"
    AFFECTED_BY = "AFFECTED_BY"
    DEVELOPS = "DEVELOPS"
    LEADS = "LEADS"


class Entity(BaseModel):
    """그래프 엔티티 (노드)"""
    id: str = Field(description="고유 식별자 (예: '삼성전자', 'DRAM_2024Q1')")
    label: NodeLabel = Field(description="노드 라벨 (Company, Product 등)")
    name: str = Field(description="엔티티 이름")
    properties: Optional[str] = Field(
        default=None,
        description="추가 속성 JSON 문자열 (예: '{\"revenue\": 100, \"year\": 2024}')"
    )
    
    class Config:
        use_enum_values = True


class Relation(BaseModel):
    """그래프 관계 (엣지)"""
    source_id: str = Field(description="출발 노드 ID")
    target_id: str = Field(description="도착 노드 ID")
    type: RelationType = Field(description="관계 타입")
    properties: Optional[str] = Field(
        default=None,
        description="관계 속성 JSON 문자열 (예: '{\"since\": 2020, \"strength\": 0.9}')"
    )
    
    class Config:
        use_enum_values = True


class KnowledgeGraph(BaseModel):
    """전체 Knowledge Graph 구조"""
    entities: List[Entity] = Field(
        description="추출된 모든 엔티티(노드) 목록"
    )
    relations: List[Relation] = Field(
        description="추출된 모든 관계(엣지) 목록"
    )
    metadata: Optional[str] = Field(
        default=None,
        description="메타데이터 JSON 문자열 (문서 제목, 날짜, 출처 등)"
    )
    
    class Config:
        use_enum_values = True


# JSON Schema 생성 함수 (Gemini API 호환)
def get_kg_json_schema() -> dict:
    """
    Gemini Structured Output용 JSON Schema 반환
    (additionalProperties 제거 버전)
    
    Returns:
        KnowledgeGraph의 JSON Schema
    """
    schema = KnowledgeGraph.model_json_schema()
    
    # Gemini API는 additionalProperties를 지원하지 않으므로 제거
    def remove_additional_properties(obj):
        if isinstance(obj, dict):
            if 'additionalProperties' in obj:
                del obj['additionalProperties']
            for value in obj.values():
                remove_additional_properties(value)
        elif isinstance(obj, list):
            for item in obj:
                remove_additional_properties(item)
    
    remove_additional_properties(schema)
    return schema
