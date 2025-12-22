"""
Seed Ontology 기반 Entity 및 Relation 모델 정의

환각(Hallucination)을 방지하기 위해 허용된 타입만 Enum으로 강제합니다.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class NodeType(str, Enum):
    """허용된 노드 타입 (Hybrid KG Architecture 1.0 based)"""
    # Agent Layer (정적)
    IDM = "IDM"
    FABLESS = "Fabless"
    FOUNDRY = "Foundry"
    SUPPLIER = "Supplier"
    ORGANIZATION = "Organization"
    
    # Signal Layer (동적)
    EARNINGS = "Earnings"
    PRICE_MOVEMENT = "PriceMovement"
    DISCLOSURE = "Disclosure"
    ISSUE = "Issue"
    
    # MacroMetric Layer
    ECONOMIC_INDICATOR = "EconomicIndicator"
    
    # Document Layer
    NEWS = "News"
    REPORT = "Report"

    # Compatibility/Legacy
    AGENT = "Agent"
    EVENT = "Event"
    OBSERVATION = "Observation"
    METRIC = "Metric"
    TREND = "Trend"
    COMPANY = "Company"


class RelationType(str, Enum):
    """허용된 관계 타입 (Hybrid KG Architecture 1.0 based)"""
    # Logic Layer (정적 역학 관계)
    AFFECTS = "AFFECTS"  # 메타데이터: correlation, sensitivity, lag, confidence
    
    # Causal Layer (동적 인과 관계)
    TRIGGERED_BY = "TRIGGERED_BY"  # 메타데이터: confidence, reasoning
    
    # Structural Layer (밸류체인)
    SUPPLIES = "SUPPLIES"
    MANUFACTURES = "MANUFACTURES"
    HAS_SIGNAL = "HAS_SIGNAL"
    MENTIONED_IN = "MENTIONED_IN"
    
    # 기존 유지 (하위 호환성)
    HAS_METRIC = "HAS_METRIC"
    HAS_TREND = "HAS_TREND"
    AFFECTED_BY = "AFFECTED_BY"
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
    
    # 신규 추가 필드 (Hybrid KG)
    embedding: Optional[List[float]] = Field(default=None, description="Vector Index용 임베딩")
    fundamental_stats: Optional[Dict[str, float]] = Field(default=None, description="Agent 전용 재무 통계")
    direction: Optional[str] = Field(default=None, description="Signal 전용 변동 방향 (UP/DOWN/NEUTRAL)")
    magnitude: Optional[float] = Field(default=None, description="Signal 전용 변동 폭")
    sentiment: Optional[str] = Field(default=None, description="Signal 전용 감성 (POSITIVE/NEGATIVE/NEUTRAL)")

    class Config:
        use_enum_values = False
    
    def to_gemini_dict(self) -> Dict[str, Any]:
        """Gemini API 출력 포맷으로 변환"""
        base = {
            "name": self.name,
            "type": self.type.value,
            "confidence": self.confidence
        }
        if self.direction: base["direction"] = self.direction
        if self.magnitude: base["magnitude"] = self.magnitude
        if self.sentiment: base["sentiment"] = self.sentiment
        return base
    
    @classmethod
    def from_gemini_dict(cls, data: Dict[str, Any]) -> "Entity":
        """Gemini API 출력을 Entity로 변환"""
        return cls(
            name=data["name"],
            type=NodeType(data["type"]),
            confidence=data.get("confidence", 1.0),
            direction=data.get("direction"),
            magnitude=data.get("magnitude"),
            sentiment=data.get("sentiment"),
            properties=data.get("properties", {})
        )


class Relation(BaseModel):
    """
    관계 모델
    
    Neo4j 엣지로 변환됩니다.
    """
    subject: str = Field(description="주어 엔티티 이름")
    predicate: RelationType = Field(description="관계 타입 (Enum으로 제한)")
    object: str = Field(description="목적어 엔티티 이름")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="추가 속성"
    )
    
    # AFFECTS 전용 메타데이터
    correlation: Optional[str] = Field(default=None, description="상관관계 방향 (DIRECT/INVERSE)")
    sensitivity: Optional[float] = Field(default=None, description="민감도 (0.0~1.0)")
    lag: Optional[str] = Field(default=None, description="지연 시간 (IMMEDIATE/1Q/1Y 등)")
    confidence: Optional[float] = Field(default=None, description="관계 신뢰도 (0.0~1.0)")
    
    # TRIGGERED_BY 전용 메타데이터
    reasoning: Optional[str] = Field(default=None, description="인과관계 설명")
    
    # 검증용 타입 정보
    subject_type: Optional[NodeType] = Field(default=None)
    object_type: Optional[NodeType] = Field(default=None)

    class Config:
        use_enum_values = False
    
    def to_gemini_dict(self) -> Dict[str, Any]:
        """Gemini API 출력 포맷으로 변환"""
        res = {
            "subject": self.subject,
            "predicate": self.predicate.value,
            "object": self.object
        }
        if self.correlation: res["correlation"] = self.correlation
        if self.sensitivity: res["sensitivity"] = self.sensitivity
        if self.lag: res["lag"] = self.lag
        if self.confidence: res["confidence"] = self.confidence
        if self.reasoning: res["reasoning"] = self.reasoning
        return res
    
    @classmethod
    def from_gemini_dict(cls, data: Dict[str, Any]) -> "Relation":
        """Gemini API 출력을 Relation으로 변환"""
        return cls(
            subject=data["subject"],
            predicate=RelationType(data["predicate"]),
            object=data["object"],
            correlation=data.get("correlation"),
            sensitivity=data.get("sensitivity"),
            lag=data.get("lag"),
            confidence=data.get("confidence"),
            reasoning=data.get("reasoning"),
            properties=data.get("properties", {})
        )


class KnowledgeGraph(BaseModel):
    """
    지식 그래프 모델
    """
    entities: List[Entity] = Field(description="엔티티 목록")
    relations: List[Relation] = Field(description="관계 목록")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="메타데이터"
    )
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None
    
    def save_to_json(self, file_path: str) -> None:
        import json
        from pathlib import Path
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_json(cls, file_path: str) -> "KnowledgeGraph":
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.model_validate(data)

    @classmethod
    def from_gemini_dict(cls, data: Dict[str, Any]) -> "KnowledgeGraph":
        """Gemini API 출력을 KnowledgeGraph로 변환"""
        entities = [Entity.from_gemini_dict(e) for e in data.get("entities", [])]
        relations = [Relation.from_gemini_dict(r) for r in data.get("relations", [])]
        return cls(entities=entities, relations=relations)


# 관계별 도메인/레인지 스키마
RELATION_SCHEMA: Dict[RelationType, Dict[str, List[NodeType]]] = {
    RelationType.AFFECTS: {
        "domain": [NodeType.ECONOMIC_INDICATOR],
        "range": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.SUPPLIER],
    },
    RelationType.TRIGGERED_BY: {
        "domain": [NodeType.PRICE_MOVEMENT],
        "range": [NodeType.DISCLOSURE, NodeType.EARNINGS, NodeType.ISSUE],
    },
    RelationType.SUPPLIES: {
        "domain": [NodeType.SUPPLIER],
        "range": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY],
    },
    RelationType.HAS_SIGNAL: {
        "domain": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.SUPPLIER, NodeType.ORGANIZATION],
        "range": [NodeType.EARNINGS, NodeType.PRICE_MOVEMENT, NodeType.DISCLOSURE, NodeType.ISSUE],
    },
    RelationType.MENTIONED_IN: {
        "domain": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.SUPPLIER, NodeType.ORGANIZATION, NodeType.ECONOMIC_INDICATOR],
        "range": [NodeType.NEWS, NodeType.REPORT],
    }
}


def validate_relation(relation: Relation) -> bool:
    """관계 검증 (단순 로깅 버전)"""
    schema = RELATION_SCHEMA.get(relation.predicate)
    if not schema:
        return True
    
    # 도메인/레인지 체크 (타입 정보가 있을 경우만)
    if relation.subject_type and relation.subject_type not in schema["domain"]:
        print(f"Warning: Domain mismatch for {relation.predicate}: {relation.subject_type}")
    if relation.object_type and relation.object_type not in schema["range"]:
        print(f"Warning: Range mismatch for {relation.predicate}: {relation.object_type}")
    
    return True


# 엔티티 타입별 기본 속성 정의
ENTITY_TYPE_PROPERTIES = {
    NodeType.IDM: ["ticker", "fab_capacity"],
    NodeType.FABLESS: ["ticker", "major_products"],
    NodeType.FOUNDRY: ["process_nodes"],
    NodeType.SUPPLIER: ["equipment_type"],
    NodeType.ECONOMIC_INDICATOR: ["unit", "source"],
    NodeType.EARNINGS: ["period", "revenue", "op_profit"],
    NodeType.PRICE_MOVEMENT: ["date", "pct_change"],
    NodeType.DISCLOSURE: ["date", "report_nm"],
    NodeType.NEWS: ["title", "date", "url"],
    NodeType.REPORT: ["analyst", "date", "firm"]
}


def get_kg_json_schema() -> dict:
    """Gemini Structured Output용 JSON Schema"""
    return {
        "type": "object",
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": [e.value for e in NodeType]},
                        "confidence": {"type": "number"},
                        "direction": {"type": "string"},
                        "magnitude": {"type": "number"},
                        "sentiment": {"type": "string"},
                        "properties": {
                            "type": "object",
                            "description": "Additional attributes (date, ticker, etc.)",
                            "properties": {
                                "date": {"type": "string", "description": "YYYY-MM-DD"},
                                "ticker": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "required": ["name", "type"]
                }
            },
            "relations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "predicate": {"type": "string", "enum": [r.value for r in RelationType]},
                        "object": {"type": "string"},
                        "correlation": {"type": "string"},
                        "sensitivity": {"type": "number"},
                        "lag": {"type": "string"},
                        "confidence": {"type": "number"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["subject", "predicate", "object"]
                }
            }
        },
        "required": ["entities", "relations"]
    }
