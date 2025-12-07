# 온톨로지 (Ontology) 완전 정리 가이드

## 📖 목차
1. [온톨로지란 무엇인가?](#온톨로지란-무엇인가)
2. [금융 도메인 온톨로지](#금융-도메인-온톨로지)
3. [LLM 기반 온톨로지 자동 생성](#llm-기반-온톨로지-자동-생성)
4. [온톨로지 개발 방법론](#온톨로지-개발-방법론)
5. [실전 적용 예시](#실전-적용-예시)

---

## 온톨로지란 무엇인가?

### 기본 개념

**온톨로지(Ontology)**는 특정 도메인에서 존재하는 객체, 개념, 엔티티와 그들 간의 관계를 명시적으로 정의한 구조화된 지식 표현입니다.

#### 간단한 비유
- **사전(Dictionary)**: 단어의 의미만 정의
- **온톨로지(Ontology)**: 단어의 의미 + 단어 간의 관계 + 구조화된 계층

예를 들어:
- 사전: "삼성전자 = 한국의 전자제품 제조 회사"
- 온톨로지: "삼성전자 → (isA) → Company → (belongsTo) → Semiconductor Sector → (hasRelationship) → SK하이닉스 (competesWith)"

### 수학적 정의

온톨로지는 다음과 같이 정의할 수 있습니다:

```
O = (C, R, I)
```

- **C (Concepts)**: 개념 집합 (예: Company, Product, Metric)
- **R (Relationships)**: 관계 집합 (예: manufactures, hasMetric, competesWith)
- **I (Instances)**: 인스턴스 집합 (예: 삼성전자, HBM, Revenue)

### 온톨로지의 구성 요소

#### 1. TBox (Terminology Box)
- **개념(Concepts)**: 도메인의 추상적 개념들
  - 예: `Company`, `Product`, `FinancialMetric`
- **속성(Properties)**: 개념의 특성
  - 예: `hasMarketCap`, `hasRevenue`, `hasIndustry`

#### 2. ABox (Assertion Box)
- **개체(Individuals)**: 실제 존재하는 구체적인 인스턴스
  - 예: `삼성전자`, `SK하이닉스`, `HBM3`
- **명제(Statements)**: 개체 간의 관계
  - 예: `(삼성전자, manufactures, HBM3)`

### 온톨로지의 장점

1. **구조화된 지식 표현**: 복잡한 도메인 지식을 체계적으로 조직
2. **재사용성**: 한 번 정의하면 여러 애플리케이션에서 재사용 가능
3. **추론 가능**: 관계를 통해 새로운 지식 추론
4. **표준화**: 도메인 전문가들이 공통으로 이해할 수 있는 표준 제공

---

## 금융 도메인 온톨로지

### FIBO (Financial Industry Business Ontology)

**FIBO**는 금융 산업을 위한 표준 온톨로지로, 금융 비즈니스의 개념과 관계를 체계적으로 정의합니다.

#### FIBO의 구조
- **36,344개 개념**
- **7가지 주요 관계 타입**:
  - `subClassOf`: 하위 클래스 관계
  - `isProvidedBy`: 제공 관계
  - `type`: 타입 관계
  - `isUsedBy`: 사용 관계
  - `isMemberOf`: 멤버 관계
  - `hasJurisdiction`: 관할권 관계
  - `isPartOf`: 부분 관계

#### FIBO 활용 예시

```
FinancialInstrument
  └─ Stock
      └─ CommonStock
          └─ 삼성전자주식

Organization
  └─ Company
      └─ 삼성전자
          ├─ hasStock: 삼성전자주식
          ├─ hasIndustry: Semiconductor
          └─ hasMetric: Revenue, OperatingProfit
```

### FinKario의 이중 스키마 설계

FinKario 논문에서는 금융 지식 그래프를 두 가지 스키마로 나누어 설계했습니다.

#### 1. Attribute Graph Schema (속성 그래프 스키마)

**목적**: 상대적으로 안정적인 엔티티 수준의 속성을 저장

**포함 내용**:
- 기업 정보: 산업, 거래소, 코드, 제품 라인
- 재무 지표: 시가총액, 매출, 이익
- 리스크 요인: 규제 리스크, 경쟁 리스크

**예시**:
```
Company: 삼성전자
  ├─ Industry: Semiconductor
  ├─ Exchange: KOSPI
  ├─ MarketCap: 500조원
  ├─ ProductLines: [Memory, Foundry, Display]
  └─ RiskFactors: [반도체 사이클, 규제 리스크]
```

#### 2. Event Graph Schema (이벤트 그래프 스키마)

**목적**: 시간에 민감한 이벤트와 동적 정보를 저장

**포함 내용**:
- 실적 발표: 분기별 실적, 가이던스
- 전략적 행동: M&A, 해외 진출, 스핀오프
- 기술 혁신: 신제품 출시, 공정 개선
- 규제 변화: 정부 정책, 규제 조치

**계층 구조**:
```
Event
├─ Supply
│   ├─ Capacity Adjustment
│   └─ Market Action
├─ Demand
│   ├─ Sales
│   └─ Consumption
├─ Revenue
│   ├─ Earning
│   └─ Profit
├─ Strategic Action
│   ├─ Merger / Acquisition
│   ├─ Overseas expansion
│   └─ Spin-off
├─ Technology Innovation
│   ├─ New product
│   └─ Iteration
└─ Policy Regulation
    ├─ Regulatory action
    └─ License
```

---

## LLM 기반 온톨로지 자동 생성

### 왜 자동 생성이 필요한가?

전통적인 온톨로지 구축은:
- **시간 소모적**: 수개월에서 수년 소요
- **전문가 의존**: 도메인 전문가와 온톨로지 엔지니어 필요
- **유지보수 어려움**: 도메인 변화에 따라 지속적 업데이트 필요

LLM을 활용하면:
- **빠른 생성**: 수일 내 기본 스키마 생성 가능
- **자동화**: 전문 템플릿 기반 자동 추출
- **확장 용이**: 새로운 개념 추가가 쉬움

### FinKario의 자동 생성 방법

#### Step 1: Attribute Graph Schema 생성

**입력**: 전문 증권 리포트 템플릿
- CFA Institute 템플릿
- J.P. Morgan 리포트 구조
- 한국 증권사 리포트 샘플

**프롬프트 예시**:
```
당신은 금융 도메인 온톨로지 설계 전문가입니다.

다음 증권 리포트 템플릿들을 분석하여:
1. 핵심 엔티티 타입 (Company, Product, Metric 등)
2. 관계 유형 (manufactures, hasMetric, belongsTo 등)
3. 속성 타입 (MarketCap, Revenue, RiskLevel 등)

을 추출하고 JSON 형식으로 반환하세요.

템플릿:
[CFA 템플릿 내용]
[J.P. Morgan 템플릿 내용]
[한국 반도체 리포트 샘플]

출력 형식:
{
  "entities": [
    {"name": "Company", "description": "기업 엔티티"},
    {"name": "Product", "description": "제품 엔티티"}
  ],
  "relations": [
    {"name": "manufactures", "from": "Company", "to": "Product"},
    {"name": "hasMetric", "from": "Company", "to": "Metric"}
  ],
  "properties": [
    {"name": "marketCap", "type": "number", "unit": "원"},
    {"name": "revenue", "type": "number", "unit": "원"}
  ]
}
```

**출력**: `S_A = {Industry, RiskFactors, Exchange, MarketCap, ...}`

#### Step 2: Event Graph Schema 생성 (Top-Down 접근)

**Level 1: 고수준 카테고리 추출**

University of Wisconsin 템플릿 기반:
```
C = LLM(Prompt_cat; θ_WIS)
C = {Supply, Demand, Revenue, StrategicAction, TechInnovation, PolicyRegulation, Macro}
```

**Level 2: FIBO 기반 세부 온톨로지 생성**

각 카테고리별로 FIBO를 참조하여 세부 이벤트 타입 생성:
```
O_ci = LLM(Prompt_event; ci, FIBO)

예시:
StrategicAction 카테고리:
  ├─ Merger / Acquisition
  ├─ Overseas expansion
  └─ Spin-off

TechInnovation 카테고리:
  ├─ New product
  ├─ Process improvement
  └─ Iteration
```

**최종 스키마**:
```
S_E = ∪_{i=1}^m {(ci, o) | o ∈ O_ci}
```

### neo4j-graphrag 활용 방법

`neo4j-graphrag` 라이브러리는 LLM을 사용하여 텍스트에서 자동으로 온톨로지 스키마를 추출합니다.

#### 기본 사용법

```python
from neo4j_graphrag import SchemaFromTextExtractor
from langchain_openai import ChatOpenAI

# 1. LLM 모델 설정
llm = ChatOpenAI(model="gpt-4o")

# 2. 증권 리포트 템플릿 문서 준비
templates = [
    "CFA Institute equity research template...",
    "J.P. Morgan report structure...",
    "한국 반도체 섹터 리포트 샘플..."
]

# 3. 스키마 추출기 생성
extractor = SchemaFromTextExtractor(
    llm=llm,
    documents=templates
)

# 4. 스키마 추출
schema = extractor.extract_schema()

# 5. Neo4j GraphSchema 생성
neo4j_schema = schema.to_neo4j_schema()
```

#### 추출 결과 예시

```python
{
    "node_types": [
        {
            "name": "Company",
            "properties": [
                {"name": "name", "type": "string"},
                {"name": "marketCap", "type": "number"},
                {"name": "industry", "type": "string"}
            ]
        },
        {
            "name": "Product",
            "properties": [
                {"name": "name", "type": "string"},
                {"name": "category", "type": "string"}
            ]
        }
    ],
    "relationship_types": [
        {
            "name": "MANUFACTURES",
            "from": "Company",
            "to": "Product"
        },
        {
            "name": "HAS_METRIC",
            "from": "Company",
            "to": "Metric"
        }
    ]
}
```

---

## 온톨로지 개발 방법론

### MOMA (Methodology for Ontology-based Multi-agent Applications)

FinBuilder 논문에서 제시한 5단계 온톨로지 개발 방법론입니다.

#### Step 1: Knowledge Acquisition (지식 획득)

**목적**: 온톨로지의 범위, 도메인, 목적 결정

**활동**:
- 도메인 전문가와 협업
- 증권 리포트, 공시 문서, 전문가 인터뷰 수집
- 기존 온톨로지 (FIBO 등) 재사용 검토

**예시 (반도체 섹터)**:
```
범위: 한국 반도체 섹터 (상장/비상장)
도메인: 반도체 산업, 금융 분석
목적: 증권 리포트 자동 생성 지원

수집 자료:
- 증권사 반도체 섹터 리포트
- DART 공시 자료
- 반도체 산업 백서
- FIBO 온톨로지
```

#### Step 2: Conceptualisation (개념화)

**목적**: 원시 지식을 명확한 개념으로 변환

**활동**:
- 개념 식별: 키워드나 구문으로 도메인 개념 추출
- 사실 정의: 개념의 인스턴스 예시
- Grounded Theory (GT) 활용: 체계적 비교를 통한 개념 도출

**반도체 섹터 개념 예시**:
```
Concepts:
- Portfolio: 포트폴리오
- Stock: 주식
- Company: 기업
- MacroEvent: 거시경제 이벤트
  ├─ LossEvent: 손실 발표
  ├─ TakeOverEvent: 인수합병
  └─ ProfitDropEvent: 이익 하락

Facts:
- TLS = TELSTRA CORPORATION (주식 코드 예시)
- 삼성전자 = 한국 반도체 기업
```

#### Step 3: Semantic Modelling (의미 모델링)

**목적**: 개념의 의미를 체계적으로 모델링

**활동**:
- 관계 정의: 개념 간 의존성과 연결
- 제약 조건: 속성의 카디널리티 제약
- 에이전트 아키텍처 고려: BDI (Belief-Desire-Intention) 에이전트

**의미 모델 예시**:
```
Portfolio
  ├─ containsStock: Stock (1:N)
  └─ belongsTo: Trader (N:1)

Stock
  ├─ isIssuedBy: Company (N:1)
  └─ isPartOfPortfolio: Portfolio (N:M)

Company
  ├─ hasEvent: MacroEvent (1:N)
  └─ ownsStock: Stock (1:N)

MacroEvent
  └─ eventBelongsTo: Company (N:1)
```

**그래픽 표현**:
```
        Portfolio
            │
            │ containsStock
            │
            ▼
           Stock ──isIssuedBy──► Company
            │                      │
            │                      │ hasEvent
            │                      │
            │                      ▼
            │                  MacroEvent
            │                      │
            │                      │ eventBelongsTo
            │                      │
            └──────────────────────┘
```

#### Step 4: Knowledge Representation (지식 표현)

**목적**: 의미 모델을 형식적으로 인코딩

**활동**:
- Protégé 사용: 온톨로지 편집 도구
- RDF/OWL 형식으로 저장
- Neo4j 스키마로 변환

**Protégé 사용 이유**:
1. 직관적이고 사용자 친화적 인터페이스
2. 다양한 플러그인 지원 (OntoViz, XML Tab 등)
3. Java Ontology Bean Generator로 FIPA/JADE 호환 온톨로지 자동 생성

**변환 프로세스**:
```
Protégé (OWL)
    ↓
Java Ontology Bean Generator
    ↓
FIPA/JADE Compliant Ontology
    ↓
Neo4j Schema (Cypher)
```

#### Step 5: Validation (검증)

**목적**: 온톨로지의 일관성과 정확성 검증

**활동**:
- OWL/DL 자동 일관성 검사
- 도메인 전문가 검토
- 반복적 개선

**검증 항목**:
- 개념 중복 여부
- 관계 일관성
- 제약 조건 위반
- 실용성 검증

**개선 사이클**:
```
Validation
    ↓ (문제 발견)
Conceptualisation
    ↓
Semantic Modelling
    ↓
Knowledge Representation
    ↓
Validation (재검증)
```

---

## 실전 적용 예시

### 한국 반도체 섹터 온톨로지 설계

#### 1. 개념 정의

```python
# 반도체 섹터 핵심 개념
concepts = {
    "Company": {
        "subtypes": ["Foundry", "IDM", "Fabless", "Equipment"],
        "properties": ["name", "marketCap", "revenue", "industry"]
    },
    "ProductLine": {
        "subtypes": ["Memory", "Logic", "FoundryService"],
        "properties": ["name", "category", "technology"]
    },
    "ProcessNode": {
        "subtypes": ["FrontEnd", "BackEnd", "Packaging"],
        "properties": ["name", "generation", "nm"]
    },
    "Equipment": {
        "subtypes": ["EUV", "DUV", "Etching"],
        "properties": ["name", "manufacturer", "specification"]
    },
    "Metric": {
        "subtypes": ["Revenue", "OperatingProfit", "CapEx", "RD"],
        "properties": ["value", "unit", "period"]
    },
    "Event": {
        "subtypes": ["Earnings", "Guidance", "Regulation", "MA"],
        "properties": ["type", "date", "description"]
    }
}
```

#### 2. 관계 정의

```python
relationships = [
    {
        "name": "manufactures",
        "from": "Company",
        "to": "ProductLine",
        "description": "기업이 제품을 제조함"
    },
    {
        "name": "usesTechnology",
        "from": "Company",
        "to": "ProcessNode",
        "description": "기업이 공정 기술을 사용함"
    },
    {
        "name": "supplies",
        "from": "Supplier",
        "to": "Company",
        "description": "공급업체가 기업에 공급함"
    },
    {
        "name": "competesWith",
        "from": "Company",
        "to": "Company",
        "symmetric": True,
        "description": "기업 간 경쟁 관계"
    },
    {
        "name": "hasMetric",
        "from": "Company",
        "to": "Metric",
        "description": "기업이 재무 지표를 보유함"
    },
    {
        "name": "affectedByPolicy",
        "from": "Company",
        "to": "Policy",
        "description": "기업이 정책의 영향을 받음"
    }
]
```

#### 3. Neo4j Cypher 스키마 생성

```cypher
// 노드 타입 생성
CREATE CONSTRAINT company_name IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT product_name IF NOT EXISTS
FOR (p:ProductLine) REQUIRE p.name IS UNIQUE;

// 관계 타입 정의
// Company -[MANUFACTURES]-> ProductLine
// Company -[USES_TECHNOLOGY]-> ProcessNode
// Company -[COMPETES_WITH]-> Company
// Company -[HAS_METRIC]-> Metric
// Company -[AFFECTED_BY_POLICY]-> Policy
```

#### 4. LLM 프롬프트 예시

```python
KOREAN_SEMICONDUCTOR_ONTOLOGY_PROMPT = """
한국 반도체 섹터 증권 리포트를 위한 온톨로지를 설계하세요.

필수 포함 개념:
1. 기업 계층: Company → Foundry, IDM, Fabless, Equipment
2. 제품 계층: ProductLine → Memory (DRAM, NAND, HBM), Logic, Foundry Service
3. 공정 계층: ProcessNode → Front-end, Back-end, Packaging
4. 설비 계층: Equipment → EUV, DUV, Etching Equipment
5. 재무 계층: Metric → Revenue, OperatingProfit, CapEx, R&D
6. 이벤트 계층: Event → Earnings, Guidance, Regulation, M&A

관계 유형:
- manufactures: Company → ProductLine
- usesTechnology: Company → ProcessNode
- supplies: Supplier → Company
- competesWith: Company ↔ Company
- hasMetric: Company → Metric
- affectedByPolicy: Company → Policy

FIBO 온톨로지의 다음 개념을 재사용하세요:
- FinancialInstrument, Organization, LegalEntity
- Market, Exchange, Sector

JSON 형식으로 반환하세요.
"""
```

---

## 요약

### 핵심 포인트

1. **온톨로지는 구조화된 지식 표현**: 개념, 관계, 인스턴스로 구성
2. **이중 스키마 설계**: 정적(Attribute) + 동적(Event) 그래프
3. **LLM 자동 생성**: 전문 템플릿 기반으로 빠른 스키마 생성 가능
4. **5단계 개발 방법론**: Acquisition → Conceptualisation → Modelling → Representation → Validation
5. **기존 온톨로지 재사용**: FIBO 등 표준 온톨로지 활용

### 다음 단계

- [다음 문서: 지식 그래프 (Knowledge Graph)](02_지식그래프_Knowledge_Graph.md)
- [다음 문서: 멀티에이전트 시스템](03_멀티에이전트_Multi_Agent.md)

---

**참고 논문**:
- FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph
- Design and Development of Financial Applications Using Ontology-Based Multi-Agent Systems
- A Framework for Market State Prediction with Ontological Asset Selection
- Sentiment Classification by Incorporating Background Knowledge from Financial Ontologies

