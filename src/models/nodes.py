"""
Seed Ontology 기반 Entity 및 Relation 모델 정의

환각(Hallucination)을 방지하기 위해 허용된 타입만 Enum으로 강제합니다.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class NodeType(str, Enum):
    """허용된 노드 타입 (Unified Schema - YAML prompts 동기화)"""
    COMPANY = "Company"
    PRODUCT = "Product"
    EVENT = "Event"
    METRIC = "Metric"
    TREND = "Trend"
    FINANCIAL = "Financial"
    TECHNOLOGY = "Technology"  # graph_schema에서 추가
    PERSON = "Person"          # graph_schema에서 추가


class RelationType(str, Enum):
    """허용된 관계 타입 (Unified Schema - YAML prompts 동기화)"""
    # 기존 nodes.py 관계
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
    
    # graph_schema 및 YAML prompts에서 추가
    PRODUCES = "PRODUCES"              # Company -> Product
    COMPETES_WITH = "COMPETES_WITH"    # Company <-> Company
    SUPPLIES_TO = "SUPPLIES_TO"        # Company -> Company
    AFFECTED_BY = "AFFECTED_BY"        # Entity -> Event/Trend
    DEVELOPS = "DEVELOPS"              # Company -> Technology
    LEADS = "LEADS"                    # Person -> Company


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
        use_enum_values = False  # Enum을 유지하여 JSON 로드 시 자동 변환
    
    def to_gemini_dict(self) -> Dict[str, Any]:
        """
        Gemini API 출력 포맷으로 변환 (커스텀 스키마 버전)
        
        Returns:
            {'name': str, 'type': str, 'confidence': float}
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_gemini_dict(cls, data: Dict[str, Any]) -> "Entity":
        """
        Gemini API 출력을 Entity로 변환 (커스텀 스키마 버전)
        
        Args:
            data: {'name': str, 'type': str, 'confidence': float}
        
        Returns:
            Entity 객체
        """
        return cls(
            name=data["name"],
            type=NodeType(data["type"]),
            properties={},  # 커스텀 스키마에서는 properties 제외
            confidence=data.get("confidence", 1.0)
        )


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
        use_enum_values = False  # Enum을 유지하여 JSON 로드 시 자동 변환
    
    def to_gemini_dict(self) -> Dict[str, Any]:
        """
        Gemini API 출력 포맷으로 변환 (커스텀 스키마 버전)
        
        Returns:
            {'subject': str, 'predicate': str, 'object': str, 'weight': float}
        """
        return {
            "subject": self.subject,
            "predicate": self.predicate.value,
            "object": self.object,
            "weight": self.weight
        }
    
    @classmethod
    def from_gemini_dict(cls, data: Dict[str, Any]) -> "Relation":
        """
        Gemini API 출력을 Relation으로 변환 (커스텀 스키마 버전)
        
        Args:
            data: {'subject': str, 'predicate': str, 'object': str, 'weight': float}
        
        Returns:
            Relation 객체
        """
        return cls(
            subject=data["subject"],
            predicate=RelationType(data["predicate"]),
            object=data["object"],
            weight=data.get("weight", 1.0),
            source=None  # 커스텀 스키마에서는 source 제외
        )


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
    
    def save_to_json(self, file_path: str) -> None:
        """
        Knowledge Graph를 JSON 파일로 저장
        
        Args:
            file_path: 저장할 파일 경로
        """
        import json
        from pathlib import Path
        
        # 디렉토리 생성
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Pydantic model_dump로 직렬화
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_json(cls, file_path: str) -> "KnowledgeGraph":
        """
        JSON 파일에서 Knowledge Graph 로드
        
        Args:
            file_path: 로드할 파일 경로
        
        Returns:
            KnowledgeGraph 객체
        """
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.model_validate(data)
    
    def to_gemini_dict(self) -> Dict[str, Any]:
        """
        Gemini API 출력 포맷으로 변환 (커스텀 스키마 버전)
        
        Returns:
            {'entities': [...], 'relations': [...]}
        """
        return {
            "entities": [e.to_gemini_dict() for e in self.entities],
            "relations": [r.to_gemini_dict() for r in self.relations]
        }
    
    @classmethod
    def from_gemini_dict(cls, data: Dict[str, Any]) -> "KnowledgeGraph":
        """
        Gemini API 출력을 KnowledgeGraph로 변환 (커스텀 스키마 버전)
        
        Args:
            data: {'entities': [...], 'relations': [...]}
        
        Returns:
            KnowledgeGraph 객체
        """
        entities = [Entity.from_gemini_dict(e) for e in data.get("entities", [])]
        relations = [Relation.from_gemini_dict(r) for r in data.get("relations", [])]
        
        return cls(
            entities=entities,
            relations=relations,
            metadata={}  # 커스텀 스키마에서는 metadata 제외
        )


# 엔티티 타입별 기본 속성 정의
ENTITY_TYPE_PROPERTIES = {
    NodeType.COMPANY: ["ticker", "industry", "country"],
    NodeType.PRODUCT: ["category", "launch_date"],
    NodeType.EVENT: ["date", "event_type", "importance"],
    NodeType.METRIC: ["value", "unit", "period"],
    NodeType.TREND: ["pattern", "period", "trend_type"],
    NodeType.FINANCIAL: ["period", "revenue", "profit", "debt"],
    NodeType.TECHNOLOGY: ["generation", "status", "description"],
    NodeType.PERSON: ["role", "company", "expertise"]
}


# Gemini API용 JSON Schema 생성 함수# Gemini API용 JSON Schema 생성 함수
def get_kg_json_schema() -> dict:
    """
    Gemini Structured Output용 커스텀 JSON Schema 반환
    
    Gemini API 제약사항:
    - additionalProperties 불가
    - 빈 properties 객체 불가
    - Dict[str, Any] 타입은 제외하거나 명시적 정의 필요
    
    Returns:
        Gemini API 호환 JSON Schema
    """
    return {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "description": "엔티티 목록",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "엔티티 이름"
                        },
                        "type": {
                            "type": "string",
                            "enum": [e.value for e in NodeType],
                            "description": "엔티티 타입"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "추출 신뢰도 (0.0~1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["name", "type"]
                }
            },
            "relations": {
                "type": "array",
                "description": "관계 목록",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "주어 엔티티 이름"
                        },
                        "predicate": {
                            "type": "string",
                            "enum": [r.value for r in RelationType],
                            "description": "관계 타입"
                        },
                        "object": {
                            "type": "string",
                            "description": "목적어 엔티티 이름"
                        },
                        "weight": {
                            "type": "number",
                            "description": "관계 가중치 (0.0~1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["subject", "predicate", "object"]
                }
            }
        },
        "required": ["entities", "relations"]
    }
