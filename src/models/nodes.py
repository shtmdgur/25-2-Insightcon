"""
Seed Ontology 기반 Entity 및 Relation 모델 정의

환각(Hallucination)을 방지하기 위해 허용된 타입만 Enum으로 강제합니다.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class NodeType(str, Enum):
    """허용된 노드 타입 (Hybrid KG Architecture v3.0)"""
    # Agent Layer (정적)
    IDM = "IDM"
    FABLESS = "Fabless"
    FOUNDRY = "Foundry"
    OSAT = "OSAT"  # ✨ 신규: 후공정 (ASE, Amkor, 하나마이크론)
    SUPPLIER = "Supplier"
    ORGANIZATION = "Organization"
    
    # Signal Layer (동적)
    EARNINGS = "Earnings"
    PRICE_MOVEMENT = "PriceMovement"
    DISCLOSURE = "Disclosure"
    ISSUE = "Issue"  # 정책/리스크/기회 통합 (자유형식)
    
    # MacroMetric Layer
    ECONOMIC_INDICATOR = "EconomicIndicator"


class RelationType(str, Enum):
    """허용된 관계 타입 (Hybrid KG Architecture v3.0)"""
    # Logic Layer (영향 관계)
    AFFECTS = "AFFECTS"  # 메타데이터: correlation, sensitivity, lag
    
    # Causal Layer (인과 관계)
    TRIGGERED_BY = "TRIGGERED_BY"  # 메타데이터: reasoning, impact
    
    # Structural Layer (밸류체인)
    SUPPLIES = "SUPPLIES"  # 메타데이터: dependency, is_critical, supply_type, product
    MANUFACTURES = "MANUFACTURES"
    HAS_SIGNAL = "HAS_SIGNAL"
    
    # Agent↔Agent 관계 ✨ 신규
    COMPETES_WITH = "COMPETES_WITH"  # 경쟁 관계
    PARTNERS_WITH = "PARTNERS_WITH"  # 협력/파트너
    INVESTS_IN = "INVESTS_IN"  # 투자/인수/지분


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
    
    # 신규 추가 필드 (Hybrid KG v3.0)
    date: Optional[str] = Field(default=None, description="데이터 발생/추출 날짜 (YYYY-MM-DD)")
    embedding: Optional[List[float]] = Field(default=None, description="Vector Index용 임베딩 (PDF/News만)")
    source: Optional[str] = Field(default=None, description="출처 문서명")
    
    # === Agent Layer 전용 ===
    fundamental_stats: Optional[Dict[str, float]] = Field(default=None, description="재무 통계")
    technical_metric: Optional[Dict[str, Any]] = Field(default=None, description="기술 지표 (수율, 대역폭 등)")
    market_metric: Optional[Dict[str, Any]] = Field(default=None, description="시장 지표 (점유율, PER/PBR 등)")
    value_chain_stage: Optional[str] = Field(default=None, description="설계/전공정/후공정/테스트")
    location: Optional[str] = Field(default=None, description="물리적 위치")
    
    # === Signal Layer 전용 ===
    direction: Optional[str] = Field(default=None, description="UP/DOWN/NEUTRAL")
    magnitude: Optional[float] = Field(default=None, description="변동 크기 (%)")
    sentiment: Optional[str] = Field(default=None, description="POSITIVE/NEGATIVE/NEUTRAL")
    
    # === PriceMovement 전용 ===
    is_significant: Optional[bool] = Field(default=None, description="의미있는 변동 여부")
    relative_performance: Optional[str] = Field(default=None, description="시장 대비 성과")
    trigger: Optional[str] = Field(default=None, description="원인 이벤트")
    
    # === Issue 전용 (자유형식) ===
    description: Optional[str] = Field(default=None, description="LLM 자유형식 기술")

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
    
    # === 공통 메타데이터 ===
    date: Optional[str] = Field(default=None, description="관계 발생/추출 날짜 (YYYY-MM-DD)")
    confidence: Optional[float] = Field(default=None, description="관계 신뢰도 (0.0~1.0)")
    source: Optional[str] = Field(default=None, description="데이터 출처")
    
    # === AFFECTS 전용 ===
    correlation: Optional[str] = Field(default=None, description="DIRECT/INVERSE")
    sensitivity: Optional[float] = Field(default=None, description="민감도 (0-1)")
    lag: Optional[str] = Field(default=None, description="지연 시간 (자유형식)")
    
    # === TRIGGERED_BY 전용 ===
    reasoning: Optional[str] = Field(default=None, description="인과관계 설명")
    impact: Optional[str] = Field(default=None, description="영향 기간+시차 통합 (자유형식)")
    
    # === SUPPLIES 전용 (소부장) ===
    dependency: Optional[float] = Field(default=None, description="의존도 (0-1)")
    is_critical: Optional[bool] = Field(default=None, description="핵심 공급망 여부")
    supply_type: Optional[str] = Field(default=None, description="장비/소재/부품/설계IP 등")
    product: Optional[str] = Field(default=None, description="공급 품목명")
    
    # === HAS_SIGNAL 전용 ===
    importance: Optional[float] = Field(default=None, description="중요도 (0-1)")
    is_official: Optional[bool] = Field(default=None, description="공식 공시 여부")
    
    # === COMPETES_WITH 전용 ===
    market_segment: Optional[str] = Field(default=None, description="경쟁 시장 (HBM, 파운드리 등)")
    competitive_dynamic: Optional[str] = Field(default=None, description="경쟁 양상 설명")
    
    # === PARTNERS_WITH 전용 ===
    partnership_type: Optional[str] = Field(default=None, description="기술협력/생산위탁/JV 등")
    scope: Optional[str] = Field(default=None, description="협력 범위")
    
    # === INVESTS_IN 전용 ===
    investment_type: Optional[str] = Field(default=None, description="M&A/지분투자/시설투자 등")
    amount: Optional[str] = Field(default=None, description="투자 규모")
    stake_percentage: Optional[float] = Field(default=None, description="지분율")
    
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


# 관계별 도메인/레인지 스키마 (v3.0)
RELATION_SCHEMA: Dict[RelationType, Dict[str, List[NodeType]]] = {
    RelationType.AFFECTS: {
        "domain": [NodeType.ECONOMIC_INDICATOR, NodeType.ISSUE, NodeType.EARNINGS, NodeType.DISCLOSURE],
        "range": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER],
    },
    RelationType.TRIGGERED_BY: {
        "domain": [NodeType.EARNINGS, NodeType.PRICE_MOVEMENT, NodeType.DISCLOSURE, NodeType.ISSUE],
        "range": [NodeType.EARNINGS, NodeType.PRICE_MOVEMENT, NodeType.DISCLOSURE, NodeType.ISSUE, NodeType.ECONOMIC_INDICATOR],
    },
    RelationType.SUPPLIES: {
        "domain": [NodeType.SUPPLIER],
        "range": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT],
    },
    RelationType.MANUFACTURES: {
        "domain": [NodeType.IDM, NodeType.FOUNDRY, NodeType.OSAT],
        "range": [NodeType.ISSUE],  # 제품도 Issue로 표현 가능
    },
    RelationType.HAS_SIGNAL: {
        "domain": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER, NodeType.ORGANIZATION],
        "range": [NodeType.EARNINGS, NodeType.PRICE_MOVEMENT, NodeType.DISCLOSURE, NodeType.ISSUE],
    },
    # ✨ 신규 Agent↔Agent 관계
    RelationType.COMPETES_WITH: {
        "domain": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER],
        "range": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER],
    },
    RelationType.PARTNERS_WITH: {
        "domain": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER, NodeType.ORGANIZATION],
        "range": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER, NodeType.ORGANIZATION],
    },
    RelationType.INVESTS_IN: {
        "domain": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER, NodeType.ORGANIZATION],
        "range": [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.OSAT, NodeType.SUPPLIER, NodeType.ISSUE, NodeType.ORGANIZATION],
    },
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


# 엔티티 타입별 기본 속성 정의 (v3.0)
ENTITY_TYPE_PROPERTIES = {
    NodeType.IDM: ["ticker", "value_chain_stage", "location"],
    NodeType.FABLESS: ["ticker", "value_chain_stage"],
    NodeType.FOUNDRY: ["ticker", "value_chain_stage"],
    NodeType.OSAT: ["ticker", "value_chain_stage"],
    NodeType.SUPPLIER: ["ticker", "supply_type"],
    NodeType.ORGANIZATION: ["description"],
    NodeType.ECONOMIC_INDICATOR: ["unit", "source"],
    NodeType.EARNINGS: ["direction", "magnitude", "sentiment"],
    NodeType.PRICE_MOVEMENT: ["direction", "magnitude", "is_significant", "trigger"],
    NodeType.DISCLOSURE: ["direction", "sentiment"],
    NodeType.ISSUE: ["description"],
}

# 관계 타입별 의미 있는 속성 정의 (v3.0)
# BaseDebateAgent가 동적으로 참조하여 하드코딩 없이 속성 추출
RELATION_PROPERTIES_BY_TYPE: Dict[str, List[str]] = {
    "AFFECTS": ["correlation", "sensitivity", "lag"],
    "TRIGGERED_BY": ["reasoning", "impact"],
    "SUPPLIES": ["dependency", "is_critical", "supply_type", "product"],
    "HAS_SIGNAL": ["importance", "is_official"],
    "COMPETES_WITH": ["market_segment", "competitive_dynamic"],
    "PARTNERS_WITH": ["partnership_type", "scope"],
    "INVESTS_IN": ["investment_type", "amount", "stake_percentage"],
    "MANUFACTURES": [],
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
