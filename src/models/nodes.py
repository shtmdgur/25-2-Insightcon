"""
Seed Ontology 기반 Entity 및 Relation 모델 정의

환각(Hallucination)을 방지하기 위해 허용된 타입만 Enum으로 강제합니다.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class NodeType(str, Enum):
    """허용된 노드 타입 (Semiconductor Ontology T-Box 2.0 based)"""
    # 0. Root
    SEMICONDUCTOR_ENTITY = "SemiconductorEntity"

    # 1. Continuant - IndependentContinuant
    # Agent
    AGENT = "Agent"
    ORGANIZATION_TYPE = "OrganizationType"
    FABLESS = "Fabless"
    IDM = "IDM"
    FOUNDRY = "Foundry"
    OSAT = "OSAT"
    SUPPLIER_ORGANIZATION = "SupplierOrganization"
    # PhysicalObject
    PHYSICAL_OBJECT = "PhysicalObject"
    SEMICONDUCTOR = "Semiconductor"
    MEMORY_SEMICONDUCTOR = "MemorySemiconductor"
    SYSTEM_SEMICONDUCTOR = "SystemSemiconductor"
    ANALOG_DEVICE = "AnalogDevice"
    PROCESS_NODE = "ProcessNode"
    PACKAGING_TECHNOLOGY = "PackagingTechnology"
    # Location
    LOCATION = "Location"
    
    # 1. Continuant - Quality
    QUALITY = "Quality"
    FINANCIAL_METRIC = "FinancialMetric"
    TECHNICAL_METRIC = "TechnicalMetric"
    MARKET_METRIC = "MarketMetric"
    
    # 1. Continuant - Role & Info
    ROLE = "Role"
    VALUE_CHAIN_STAGE = "ValueChainStage"
    INFORMATION_OBJECT = "InformationObject"
    FINANCIAL_REPORT = "FinancialReport"
    PATENT = "Patent"
    POLICY = "Policy"
    TECHNICAL_SPECIFICATION = "TechnicalSpecification"
    
    # 2. Occurrent
    OCCURRENT = "Occurrent"
    PROCESS = "Process"
    MANUFACTURING_PROCESS = "ManufacturingProcess"
    FRONT_END_PROCESS = "FrontEndProcess"
    BACK_END_PROCESS = "BackEndProcess"
    
    EVENT = "Event"
    STRATEGIC_ACTION = "StrategicAction"
    CORPORATE_EVENT = "CorporateEvent"
    MARKET_ENVIRONMENT = "MarketEnvironment"
    POLICY_EVENT = "PolicyEvent"
    
    OBSERVATION = "Observation"  # [NEW] Context-less Data Hub
    TEMPORAL_REGION = "TemporalRegion"
    
    # 3. Risk & Opportunity
    RISK_FACTOR = "RiskFactor"
    GEOPOLITICAL_RISK = "GeopoliticalRisk"
    SUPPLY_CHAIN_RISK = "SupplyChainRisk"
    OPPORTUNITY_FACTOR = "OpportunityFactor"
    
    # 4. Other
    PERSON = "Person"
    TECHNOLOGY = "Technology"  # Compatibility
    COMPANY = "Company"        # Compatibility (mapped to IDM/Fabless/etc ideally)
    PRODUCT = "Product"        # Compatibility (mapped to Semiconductor/PhysicalObject)
    METRIC = "Metric"          # Compatibility (mapped to Financial/Technical/MarketMetric)
    TREND = "Trend"            # Compatibility (mapped to Pattern if needed)


class RelationType(str, Enum):
    """허용된 관계 타입 (Semiconductor Ontology R-Box 2.0 based)"""
    # A. Participation & Role
    PARTICIPATES_IN = "participatesIn"
    HAS_ROLE = "hasRole"
    REALIZED_BY = "realizedBy"
    
    # B. Production & Supply
    PRODUCED_BY = "producedBy"
    MANUFACTURES = "manufactures"
    SUPPLIES = "supplies"
    DEPENDS_ON = "dependsOn"
    IN_VALUE_CHAIN_STAGE = "inValueChainStage"
    
    # C. Structure & Quality
    HAS_PART = "hasPart"
    PART_OF = "partOf"
    HAS_QUALITY = "hasQuality"
    LOCATED_AT = "locatedAt"
    
    # D. Temporal & Causal
    PRECEDED_BY = "precededBy"
    OCCURS_DURING = "occursDuring"
    AFFECTS = "affects"
    
    # E. Info & Risk
    IS_ABOUT = "isAbout"
    EXPOSED_TO = "exposedTo"
    BENEFITS_FROM = "benefitsFrom"
    
    # F. Observation & Measurement [NEW]
    RECORDED_AT = "recordedAt"
    OBSERVES = "observes"
    HAS_VALUE = "hasValue"

    # G. Legacy/Compatibility (For existing code/parsers)
    COMPETITOR_OF = "COMPETITOR_OF"  # -> competesWith (if not in R-Box, maybe treat as symmetric dependsOn?) - Keeping for now
    SUPPLIER_OF = "SUPPLIER_OF"      # -> supplies
    CUSTOMER_OF = "CUSTOMER_OF"      # -> supplies (inverse)
    HAS_METRIC = "HAS_METRIC"        # -> hasQuality
    HAS_FINANCIAL = "HAS_FINANCIAL"  # -> hasQuality
    HAS_TREND = "HAS_TREND"          # -> hasQuality or affects
    OCCURRED_AT = "OCCURRED_AT"      # -> occursDuring
    RELATED_TO = "RELATED_TO"        # Generic fallback
    PRODUCES = "PRODUCES"            # -> manufactures
    COMPETES_WITH = "COMPETES_WITH"  # -> competesWith logic (will map to dependsOn or new relation?)
    SUPPLIES_TO = "SUPPLIES_TO"      # -> supplies
    AFFECTED_BY = "AFFECTED_BY"      # -> affects (inverse)
    DEVELOPS = "DEVELOPS"            # -> manufactures or participatesIn
    LEADS = "LEADS"                  # -> participatesIn or hasRole


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


# 엔티티 타입별 기본 속성 정의 (Updated for T-Box 2.0)
ENTITY_TYPE_PROPERTIES = {
    # 1. IndependentContinuant - Agent
    NodeType.FABLESS: ["ticker", "major_products", "customer"],
    NodeType.IDM: ["ticker", "fab_capacity", "memory_types"],
    NodeType.FOUNDRY: ["process_nodes", "capacity", "major_clients"],
    NodeType.OSAT: ["packaging_tech", "capacity"],
    NodeType.SUPPLIER_ORGANIZATION: ["equipment_type", "materials"],
    NodeType.AGENT: ["type", "role"],
    
    # 1. IndependentContinuant - PhysicalObject
    NodeType.MEMORY_SEMICONDUCTOR: ["density", "speed", "generation"],
    NodeType.SYSTEM_SEMICONDUCTOR: ["architecture", "node", "application"],
    NodeType.ANALOG_DEVICE: ["application", "voltage"],
    NodeType.PROCESS_NODE: ["nm_size", "transistor_type"],
    NodeType.PACKAGING_TECHNOLOGY: ["stack_height", "interposer"],
    NodeType.SEMICONDUCTOR: ["category", "tech_node"],
    
    # 1. IndependentContinuant - Location
    NodeType.LOCATION: ["country", "region", "function"],
    
    # 1. IndependentContinuant - Quality
    NodeType.FINANCIAL_METRIC: ["value", "unit", "period", "yoy_growth"],
    NodeType.TECHNICAL_METRIC: ["value", "unit", "spec_name"],
    NodeType.MARKET_METRIC: ["value", "unit", "period", "consensus_gap"],
    
    # 1. IndependentContinuant - Role & Info
    NodeType.VALUE_CHAIN_STAGE: ["stage_name", "description"],
    NodeType.FINANCIAL_REPORT: ["period", "report_type", "date"],
    NodeType.PATENT: ["patent_number", "assignee", "filing_date"],
    NodeType.POLICY: ["country", "status", "effective_date"],
    
    # 2. Occurrent - Process
    NodeType.MANUFACTURING_PROCESS: ["yield_rate", "throughput"],
    
    # 2. Occurrent - Event
    NodeType.STRATEGIC_ACTION: ["investment_size", "purpose"],
    NodeType.CORPORATE_EVENT: ["date", "impact_level"],
    NodeType.MARKET_ENVIRONMENT: ["indicator", "trend"],
    NodeType.POLICY_EVENT: ["impact_scope", "severity"],
    
    # 2. Occurrent - Observation [NEW]
    NodeType.OBSERVATION: ["value", "unit", "date", "confidence", "source_text"],
    
    # 2. Occurrent - TemporalRegion
    NodeType.TEMPORAL_REGION: ["date", "quarter", "year"],
    
    # 3. Risk & Opportunity
    NodeType.RISK_FACTOR: ["risk_level", "probability"],
    NodeType.GEOPOLITICAL_RISK: ["region", "impact_severity", "event_reference"],
    NodeType.SUPPLY_CHAIN_RISK: ["component", "delay_time", "alternative"],
    NodeType.OPPORTUNITY_FACTOR: ["potential_size", "timeframe"],
    
    # Missing Types (Abstract & Others)
    NodeType.SEMICONDUCTOR_ENTITY: ["description"],
    NodeType.ORGANIZATION_TYPE: ["type_name"],
    NodeType.INFORMATION_OBJECT: ["title", "source"],
    NodeType.OCCURRENT: ["date"],
    NodeType.PROCESS: ["status"],
    NodeType.FRONT_END_PROCESS: ["step_name", "equipment"],
    NodeType.BACK_END_PROCESS: ["packaging_type", "test_result"],
    NodeType.QUALITY: ["value"],
    NodeType.ROLE: ["role_name"],
    NodeType.PHYSICAL_OBJECT: ["material"],
    
    # Legacy/Compatibility
    NodeType.COMPANY: ["ticker", "industry", "country"],
    NodeType.PRODUCT: ["category", "launch_date"],
    NodeType.EVENT: ["date", "event_type", "importance"],
    NodeType.METRIC: ["value", "unit", "period"],
    NodeType.TREND: ["pattern", "period", "trend_type"],
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
