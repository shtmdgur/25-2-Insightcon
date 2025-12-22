# 반도체 섹터 투자 분석을 위한 하이브리드 지식 그래프 아키텍처
## Master Design Document v2.0

**작성일**: 2025-12-22  
**작성자**: Hybrid KG Architecture Team  
**버전**: 2.0 (BFO 기반 → 실용 하이브리드 모델)

---

## 📋 목차

1. [개요](#1-개요)
2. [설계 변경 요약](#2-설계-변경-요약)
3. [T-Box 재설계](#3-t-box-재설계)
4. [R-Box 재설계](#4-r-box-재설계)
5. [데이터 적재 파이프라인](#5-데이터-적재-파이프라인)
6. [시스템 아키텍처](#6-시스템-아키텍처)
7. [구현 가이드](#7-구현-가이드)
8. [PoC 예제](#8-poc-예제)
9. [기대 효과](#9-기대-효과)

---

## 1. 개요

본 문서는 **반도체 산업의 복잡한 밸류체인**과 **금융 시계열 데이터**를 AI(LLM)가 이해하고 추론할 수 있도록 하는 **Graph-Vector Hybrid System**의 설계를 기술합니다.

### 1.1. 설계 철학

초기 BFO(Basic Formal Ontology) 기반의 엄격한 온톨로지를 **검색 효율성**과 **인과 추론(Causal Reasoning)** 중심으로 경량화 및 고도화하였습니다.

```
학문적 정밀성 (BFO 58 classes)
              ↓
실용적 효율성 (Hybrid Model)
              ↓
AI 추론 가능성 (Causal + Semantic)
```

### 1.2. 핵심 가치

- **논리적 시뮬레이션**: "환율 상승 → 수출 기업 실적 개선" 경로 자동 추적
- **정밀 인과 분석**: "주가 급등 원인" → 특정 공시 문서 자동 연결
- **환각 최소화**: 통계적 검증된 관계만 사용하여 신뢰도 확보

---

## 2. 설계 변경 요약

### 2.1. AS-IS vs TO-BE 비교표

| 구분 | AS-IS (기존 BFO 설계) | TO-BE (하이브리드 실용 모델) |
|---|---|---|
| **철학** | BFO 기반 정밀 온톨로지 (58 Classes) | Graph Logic + Vector Search 하이브리드 |
| **데이터 구조** | 모든 데이터 → `Observation` 노드 생성 | **이원화**: 상태(Snapshot) = 속성, 사건(Story) = 노드 |
| **추론 방식** | 단순 연결 관계 (`RelatedTo`) | 함수적 역학 관계 (`correlation: DIRECT/INVERSE`) |
| **저장소** | Graph DB + Vector DB 분리 고려 | **Neo4j All-in-One** (노드 내 Vector 내장) |
| **LLM 역할** | 단순 Entity 추출 | **구조화 + 가중치 학습 + 인과관계 추론** |

### 2.2. 주요 변경 사항

#### 변경 1: 데이터 이원화
```
[기존] 모든 시계열 데이터 → Observation 노드
[신규] 상태(Snapshot) → Agent 속성 / 사건(Event) → Signal 노드
```

#### 변경 2: 관계의 함수화
```
[기존] (A)-[:RelatedTo]->(B)
[신규] (A)-[:AFFECTS {correlation: "DIRECT", sensitivity: 0.8, lag: "1Q"}]->(B)
```

#### 변경 3: Vector 통합
```
[기존] Neo4j (Graph) + Pinecone (Vector) 분리
[신규] Neo4j Vector Index 활용 → 단일 DB로 Hybrid Search
```

---

## 3. T-Box 재설계

불필요한 계층을 제거하고, **AI가 추론할 수 있는 메타데이터가 풍부한 노드** 중심으로 재편.

### 3.1. Agent (핵심 엔티티)

**정의**: 고정된 산업의 주체. 변하지 않는 정보와 **현재 상태값**을 속성으로 가진다.

```cypher
CREATE (s:IDM {
  name: "Samsung Electronics",
  ticker: "005930",
  fundamental_stats: {
    per: 15.2,
    pbr: 1.4,
    market_cap: "400T"
  },
  description_embedding: [0.123, -0.456, ...]  // Vector
})
```

**Subtypes** (Label):
- `IDM`: 삼성전자, SK하이닉스, Intel
- `Fabless`: NVIDIA, Qualcomm, AMD
- `Foundry`: TSMC, 삼성 파운드리
- `Supplier`: ASML, 동진쎄미켐, 솔브레인
- `Organization`: 일반 조직

**핵심 속성** (Properties):
- `name` (string): 정규화된 기업명
- `ticker` (string): 증권 코드
- `fundamental_stats` (JSON): PER, PBR, Market Cap 등 (검색 필터링용)
- `description_embedding` (vector): 유사 기업 검색용 (Neo4j Vector Index)

---

### 3.2. Signal (사건 및 변화) ⭐ 핵심 변경

**정의**: 단순 시계열 데이터가 아닌, **AI가 분석한 "의미 있는 이벤트 패킷"**.

```cypher
CREATE (sig:Earnings {
  summary: "삼성전자 4Q24 어닝 서프라이즈",
  direction: "UP",
  magnitude: 15.5,  // 변화폭 (%)
  sentiment: "POSITIVE",
  date: datetime("2024-10-31"),
  confidence: 0.9
})
```

**Subtypes** (Label):
- `Earnings`: 실적 발표
- `PriceMovement`: 주가 급등/급락
- `Disclosure`: 공시 (M&A, 증설 등)
- `Issue`: 이슈 (리콜, 소송 등)

**핵심 속성** (Properties):
- `summary` (string): 사건 요약
- `direction` (enum): `"UP"` | `"DOWN"` | `"NEUTRAL"`
- `magnitude` (float): 변화폭 (예: 15.5%)
- `sentiment` (enum): `"POSITIVE"` | `"NEGATIVE"` | `"NEUTRAL"`
- `date` (datetime): 발생 시점
- `confidence` (float): AI 판단 신뢰도 (0.0~1.0)

---

### 3.3. MacroMetric (거시 경제 지표)

**정의**: 시장 전체에 영향을 주는 외부 변수.

```cypher
CREATE (m:EconomicIndicator {
  name: "USD/KRW 환율",
  current_trend: "RISING",
  current_value: 1350.0,
  last_updated: datetime()
})
```

**핵심 속성**:
- `name`: 지표명
- `current_trend`: `"RISING"` | `"FALLING"` | `"STABLE"`
- `current_value`: 현재 값
- `last_updated`: 마지막 업데이트 시점

---

### 3.4. Document (근거 문서)

**정의**: RAG 벡터 검색을 위한 원문 저장소.

```cypher
CREATE (d:News {
  title: "삼성전자, HBM3E 공급 계약 체결",
  content: "...",
  url: "https://...",
  published_date: datetime("2024-03-05"),
  embedding: [0.789, -0.234, ...]  // Vector
})
```

**Subtypes**:
- `News`: 뉴스 기사
- `Report`: 애널리스트 리포트

**핵심 속성**:
- `title`, `content`, `url`
- `published_date`
- `embedding` (vector): Semantic Search용

---

## 4. R-Box 재설계

단순 연결이 아닌, **시뮬레이션이 가능한 함수적 관계(Logic Layer)**를 정의.

### 4.1. Logic Layer (정적 역학 관계)

#### AFFECTS ⭐ 핵심 관계

**정의**: 한 변수가 다른 변수에 미치는 영향을 **함수적으로** 표현.

```cypher
CREATE (usd:EconomicIndicator {name: "USD/KRW"})
CREATE (samsung:IDM {name: "Samsung Electronics"})
CREATE (usd)-[:AFFECTS {
  correlation: "DIRECT",        // 정비례 (+)
  sensitivity: "HIGH",           // 민감도: 0.8~1.0
  lag: "1Q",                     // 시차: 1분기 후
  confidence: 0.85               // 통계적 검증 신뢰도
}]->(samsung)
```

**Properties (학습 대상)**:
- `correlation` (enum): 
  - `"DIRECT"`: 정비례 (USD↑ → Export↑)
  - `"INVERSE"`: 반비례 (Interest↑ → Stock↓)
- `sensitivity` (enum): `"HIGH"` (0.8~1.0) | `"MEDIUM"` (0.4~0.7) | `"LOW"` (0.0~0.3)
- `lag` (enum): `"IMMEDIATE"` | `"1Q"` | `"2Q"` | `"1Y"`
- `confidence` (float): 0.0 ~ 1.0 (통계적 검증 결과)

**학습 방법**:
1. **초기값**: LLM이 리포트에서 추출 ("환율 상승 시 수출 실적 개선 예상")
2. **통계 검증**: 과거 데이터로 Pearson 상관계수 계산
3. **보정**: LLM 값과 통계 값 차이가 크면 `confidence` 하향 조정

---

### 4.2. Causal Layer (동적 인과 관계)

#### TRIGGERED_BY

**정의**: 한 사건이 다른 사건을 **직접 유발**했음을 나타냄.

```cypher
CREATE (disclosure:Disclosure {summary: "HBM3E 공급 계약 공시"})
CREATE (priceUp:PriceMovement {direction: "UP", magnitude: 12.3})
CREATE (priceUp)-[:TRIGGERED_BY {
  confidence: 0.92,
  reasoning: "공급 계약 공시 직후 주가 급등, 시간적/의미적 인과성 확인"
}]->(disclosure)
```

**Properties**:
- `confidence`: AI가 판단한 인과관계 신뢰도
- `reasoning`: 근거 요약 (Explainability용)

---

### 4.3. Structural Layer (밸류체인)

```cypher
// 소재 공급
(Supplier)-[:SUPPLIES]->(IDM)

// 제품 제조
(IDM)-[:MANUFACTURES]->(Semiconductor)

// 사건 발생
(Agent)-[:HAS_SIGNAL]->(Signal)

// 문서 언급
(Agent)-[:MENTIONED_IN]->(Document)
```

---

## 5. 데이터 적재 파이프라인

리포트와 뉴스에서 **수치(가중치/방향)**를 뽑고 DB에 저장하는 구체적 프로세스.

### 5.1. Dual-Path Pipeline (이원화 처리)

```
                   ┌─────────────────┐
                   │  뉴스/리포트 수집  │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │   텍스트 전처리   │
                   └────────┬────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
       ┌──────▼───────┐           ┌──────▼───────┐
       │ Path A:      │           │ Path B:      │
       │ Vector       │           │ Structure    │
       │ Embedding    │           │ Extraction   │
       └──────┬───────┘           └──────┬───────┘
              │                           │
       ┌──────▼───────┐           ┌──────▼───────┐
       │ Chunking +   │           │ LLM Prompt:  │
       │ OpenAI/SBERT │           │ T-Box 기반   │
       │ Embedding    │           │ Entity/Rel   │
       └──────┬───────┘           │ 추출         │
              │                   └──────┬───────┘
              │                           │
              │                   ┌──────▼───────┐
              │                   │ Learning &   │
              │                   │ Validation   │
              │                   │ (통계 보정)   │
              │                   └──────┬───────┘
              │                           │
              └─────────────┬─────────────┘
                            │
                   ┌────────▼────────┐
                   │  Neo4j Upsert   │
                   │ (Graph + Vector)│
                   └─────────────────┘
```

### 5.2. Path A: Vector Embedding

```python
# 1. 텍스트 청킹
chunks = text_splitter.split_text(document.content, chunk_size=500)

# 2. 임베딩 생성
embeddings = openai.Embedding.create(
    model="text-embedding-3-small",
    input=chunks
)

# 3. Neo4j 저장
for chunk, embedding in zip(chunks, embeddings):
    session.run("""
        CREATE (d:DocumentChunk {
            content: $content,
            embedding: $embedding
        })
    """, content=chunk, embedding=embedding)
```

### 5.3. Path B: Structure Extraction (LLM)

```python
# 1. LLM Prompt (T-Box 스키마 포함)
prompt = f"""
다음 뉴스에서 정보를 추출하세요.

[T-Box 스키마]
- Agent: IDM, Fabless, Foundry
- Signal: Earnings, PriceMovement, Disclosure
- Relation: AFFECTS(correlation, sensitivity, lag)

[뉴스]
{news_text}

[추출 형식]
{{
  "signals": [
    {{"type": "Earnings", "summary": "...", "direction": "UP", "magnitude": 15.5}}
  ],
  "relations": [
    {{"from": "USD/KRW", "to": "Samsung", "type": "AFFECTS", 
      "correlation": "DIRECT", "sensitivity": "HIGH", "lag": "1Q"}}
  ]
}}
"""

response = llm.generate(prompt)
extracted_data = json.loads(response)
```

### 5.4. Learning & Validation (수치 보정)

```python
# 1. LLM이 추출한 관계
llm_correlation = "DIRECT"
llm_sensitivity = "HIGH"  # 0.8으로 매핑

# 2. 통계 검증 (과거 데이터)
historical_usd = [1200, 1250, 1300, 1350, ...]
historical_revenue = [60T, 62T, 65T, 68T, ...]
pearson_r = calculate_correlation(historical_usd, historical_revenue)  # 0.72

# 3. 신뢰도 계산
if abs(llm_sensitivity - pearson_r) > 0.2:
    confidence = 0.6  # LLM 값과 통계 차이 크면 신뢰도 하향
else:
    confidence = 0.9  # 일치하면 높은 신뢰도

# 4. Neo4j 저장
session.run("""
    MATCH (a:EconomicIndicator {name: 'USD/KRW'})
    MATCH (b:IDM {name: 'Samsung Electronics'})
    MERGE (a)-[:AFFECTS {
        correlation: $correlation,
        sensitivity: $sensitivity,
        lag: $lag,
        confidence: $confidence
    }]->(b)
""", correlation="DIRECT", sensitivity=pearson_r, lag="1Q", confidence=confidence)
```

---

## 6. 시스템 아키텍처

### 6.1. Neo4j All-in-One 전략

**핵심 결정**: Vector DB를 별도로 구축하지 않고, **Neo4j의 Vector Index** 기능을 사용.

```
    ┌─────────────────────────────────────────┐
    │            Neo4j Database               │
    │                                         │
    │  ┌──────────────┐   ┌──────────────┐   │
    │  │ Graph Nodes  │   │Vector Indexes│   │
    │  │              │   │              │   │
    │  │ • Agent      │   │ •description │   │
    │  │ • Signal     │   │  _embedding  │   │
    │  │ • Document   │   │ •content     │   │
    │  │              │   │  _embedding  │   │
    │  └──────────────┘   └──────────────┘   │
    │                                         │
    │  ┌─────────────────────────────┐       │
    │  │   Cypher + Vector Search    │       │
    │  │   (Hybrid Query Engine)     │       │
    │  └─────────────────────────────┘       │
    └─────────────────────────────────────────┘
                     ▲
                     │
           ┌─────────┴─────────┐
           │   LangChain RAG   │
           │   Orchestrator    │
           └───────────────────┘
```

### 6.2. Vector Index 생성

```cypher
// Document 임베딩 인덱스
CREATE VECTOR INDEX document_embedding IF NOT EXISTS
FOR (d:Document)
ON d.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

// Agent 설명 임베딩 인덱스
CREATE VECTOR INDEX agent_embedding IF NOT EXISTS
FOR (a:Agent)
ON a.description_embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};
```

### 6.3. Hybrid Search Query

```cypher
// 1단계: Graph Filter (밸류체인)
MATCH (samsung:IDM {name: 'Samsung Electronics'})
MATCH (samsung)<-[:SUPPLIES]-(supplier:Supplier)

// 2단계: Vector Search (유사도)
CALL db.index.vector.queryNodes(
  'document_embedding', 
  10,  // top-k
  $query_embedding
)
YIELD node AS doc, score

// 3단계: 결합 필터
WHERE (doc)-[:MENTIONED_IN]->(supplier)

RETURN doc.title, doc.content, score
ORDER BY score DESC
LIMIT 3
```

---

## 7. 구현 가이드

### 7.1. nodes.py 재설계

```python
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    # Agent
    IDM = "IDM"
    FABLESS = "Fabless"
    FOUNDRY = "Foundry"
    SUPPLIER = "Supplier"
    
    # Signal
    EARNINGS = "Earnings"
    PRICE_MOVEMENT = "PriceMovement"
    DISCLOSURE = "Disclosure"
    ISSUE = "Issue"
    
    # MacroMetric
    ECONOMIC_INDICATOR = "EconomicIndicator"
    
    # Document
    NEWS = "News"
    REPORT = "Report"

class RelationType(str, Enum):
    # Logic Layer
    AFFECTS = "AFFECTS"
    
    # Causal Layer
    TRIGGERED_BY = "TRIGGERED_BY"
    
    # Structural Layer
    SUPPLIES = "SUPPLIES"
    MANUFACTURES = "MANUFACTURES"
    HAS_SIGNAL = "HAS_SIGNAL"
    MENTIONED_IN = "MENTIONED_IN"

class Agent(BaseModel):
    name: str
    ticker: Optional[str] = None
    fundamental_stats: Dict[str, Any] = Field(default_factory=dict)
    description_embedding: Optional[list[float]] = None

class Signal(BaseModel):
    summary: str
    direction: str  # "UP" | "DOWN" | "NEUTRAL"
    magnitude: float
    sentiment: str  # "POSITIVE" | "NEGATIVE" | "NEUTRAL"
    date: str  # ISO timestamp
    confidence: float

class AffectsRelation(BaseModel):
    correlation: str  # "DIRECT" | "INVERSE"
    sensitivity: str  # "HIGH" | "MEDIUM" | "LOW"
    lag: str  # "IMMEDIATE" | "1Q" | "2Q" | "1Y"
    confidence: float
```

### 7.2. LLM 프롬프트 템플릿

```yaml
# prompts.yaml
structure_extraction:
  role: "Financial Knowledge Graph Specialist"
  instruction: |
    다음 뉴스/리포트에서 정보를 추출하여 Knowledge Graph로 변환하세요.
    
    [T-Box 스키마]
    - Agent: IDM (삼성전자, SK하이닉스), Fabless (NVIDIA), Foundry (TSMC)
    - Signal: Earnings (실적), PriceMovement (주가), Disclosure (공시)
    - Relation: AFFECTS (영향 관계)
    
    [중요 규칙]
    1. Signal의 magnitude는 반드시 숫자로 추출 (예: "15% 상승" → 15.0)
    2. AFFECTS의 correlation은 "DIRECT" (정비례) 또는 "INVERSE" (반비례)
    3. sensitivity는 "HIGH" (강력한 영향) | "MEDIUM" | "LOW"
    
    [출력 형식]
    ```json
    {
      "signals": [...],
      "relations": [...]
    }
    ```
```

### 7.3. 데이터 수집기 (Crawler)

```python
from dataclasses import dataclass
from typing import List
import openai

@dataclass
class NewsArticle:
    title: str
    content: str
    url: str
    published_date: str

class KGExtractor:
    def __init__(self, llm_client, neo4j_session):
        self.llm = llm_client
        self.session = neo4j_session
    
    def process_news(self, article: NewsArticle):
        # 1. Vector Embedding
        embedding = openai.Embedding.create(
            model="text-embedding-3-small",
            input=article.content
        ).data[0].embedding
        
        # 2. Structure Extraction (LLM)
        prompt = self._build_prompt(article.content)
        extracted = self.llm.generate(prompt)
        
        # 3. Learning & Validation
        validated = self._validate_relations(extracted)
        
        # 4. Neo4j Upsert
        self._save_to_neo4j(article, embedding, validated)
    
    def _validate_relations(self, extracted_data):
        # 통계 검증 로직
        for rel in extracted_data['relations']:
            statistical_corr = self._calculate_correlation(
                rel['from'], rel['to']
            )
            rel['confidence'] = self._compute_confidence(
                llm_value=rel['sensitivity'],
                stat_value=statistical_corr
            )
        return extracted_data
```

---

## 8. PoC 예제

### 8.1. 시나리오: "환율 상승이 삼성전자에 미치는 영향"

#### Step 1: 데이터 주입

```cypher
// Agent 생성
CREATE (usd:EconomicIndicator {
  name: "USD/KRW",
  current_trend: "RISING",
  current_value: 1350.0
})

CREATE (samsung:IDM {
  name: "Samsung Electronics",
  ticker: "005930",
  fundamental_stats: {per: 15.2, pbr: 1.4}
})

// AFFECTS 관계 (통계 검증 완료)
CREATE (usd)-[:AFFECTS {
  correlation: "DIRECT",
  sensitivity: 0.72,  // Pearson r
  lag: "1Q",
  confidence: 0.89
}]->(samsung)
```

#### Step 2: 시뮬레이션 쿼리

```cypher
// 질문: "USD/KRW 환율 상승 시 영향받는 기업은?"
MATCH (indicator:EconomicIndicator {name: "USD/KRW"})
      -[r:AFFECTS {correlation: "DIRECT"}]->(affected)
WHERE r.confidence > 0.8
RETURN affected.name AS company, 
       r.sensitivity AS impact_strength,
       r.lag AS time_lag
ORDER BY r.sensitivity DESC
```

**결과**:
```
company               | impact_strength | time_lag
Samsung Electronics   | 0.72           | 1Q
```

### 8.2. 시나리오: "주가 급등 원인 분석"

#### Step 1: Signal 및 Document 저장

```cypher
// Document
CREATE (news:News {
  title: "삼성전자, HBM3E 공급 계약 체결",
  content: "...",
  published_date: datetime("2024-03-05"),
  embedding: [...]
})

// Signal
CREATE (priceUp:PriceMovement {
  summary: "삼성전자 주가 12.3% 급등",
  direction: "UP",
  magnitude: 12.3,
  date: datetime("2024-03-05")
})

// Causal Relation
CREATE (priceUp)-[:TRIGGERED_BY {
  confidence: 0.92,
  reasoning: "공시 직후 동일 시점 주가 급등"
}]->(news)
```

#### Step 2: 인과관계 추적

```cypher
// 질문: "2024-03-05 주가 급등 원인은?"
MATCH (sig:PriceMovement {date: datetime("2024-03-05")})
      -[:TRIGGERED_BY]->(cause)
RETURN sig.summary AS event,
       cause.title AS root_cause,
       cause.url AS source
```

**결과**:
```
event                    | root_cause                          | source
삼성전자 주가 12.3% 급등   | 삼성전자, HBM3E 공급 계약 체결       | https://...
```

### 8.3. Hybrid Search 예제

```cypher
// 질문: "삼성전자 밸류체인에서 '수율 개선' 관련 리포트는?"

// 1. Graph Filter: 밸류체인
MATCH (samsung:IDM {name: 'Samsung Electronics'})
MATCH (samsung)<-[:SUPPLIES]-(supplier)

// 2. Vector Search: 의미 유사도
CALL db.index.vector.queryNodes(
  'document_embedding',
  10,
  $query_embedding  // "수율 개선" 임베딩
) YIELD node AS doc, score

// 3. 결합 필터
WHERE (doc)-[:MENTIONED_IN]->(supplier)
  AND score > 0.7

RETURN doc.title, supplier.name, score
ORDER BY score DESC
LIMIT 3
```

---

## 9. 기대 효과

### 9.1. AI 추론 능력

| 추론 유형 | 쿼리 예시 | 메커니즘 |
|---|---|---|
| **논리적 시뮬레이션** | "환율 상승 시 영향?" | `AFFECTS(DIRECT)` 관계 추적 |
| **정밀 인과 분석** | "주가 급등 원인?" | `TRIGGERED_BY` 역방향 추적 |
| **다중 홉 추론** | "소재 기업 → IDM → 반도체 제품" 경로 | 그래프 순회 (3-hop) |
| **의미 검색** | "유사한 이슈 사례는?" | Vector Similarity + Graph Filter |

### 9.2. 비즈니스 가치

1. **투자 의사결정 지원**: 인과관계 기반 시나리오 분석
2. **리스크 조기 경보**: 밸류체인 전파 경로 실시간 모니터링
3. **애널리스트 업무 자동화**: LLM이 리포트에서 자동으로 KG 구축

### 9.3. 기술적 우수성

- **단일 DB 운영**: Neo4j만으로 Graph + Vector 통합 → 운영 비용 절감
- **통계 검증**: LLM 환각 방지 → 신뢰도 높은 추론
- **확장 가능**: 새로운 NodeType/RelationType 추가 용이

---

## 부록 A: 참고 문헌

1. Neo4j Vector Index Documentation (2024)
2. GraphRAG: Knowledge Graph + RAG Integration (Microsoft Research)
3. FinCARE: Financial Causal Reasoning Framework (arXiv 2024)
4. TimeMKG: Multivariate Time Series with Knowledge Graphs (MIT)

---

**[문서 끝]**
