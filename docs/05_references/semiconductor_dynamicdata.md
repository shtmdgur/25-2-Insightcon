# GraphRAG 기반 대한민국 반도체 섹터 분석: 동적 데이터 온톨로지 구축 가이드

**작성일**: 2025년 12월  
**대상**: 반도체 섹터 GraphRAG/온톨로지 구축 프로젝트  
**기술 스택**: Neo4j, LLM (Gemini/GPT), Palantir-inspired ontology patterns

---

## 목차

1. [개요](#개요)
2. [팔란티어 동적 데이터 패턴 심층 분석](#팔란티어-동적-데이터-패턴-심층-분석)
3. [GraphRAG 환경에서의 동적 데이터 구현](#graphrag-환경에서의-동적-데이터-구현)
4. [대한민국 반도체 섹터 온톨로지 설계](#대한민국-반도체-섹터-온톨로지-설계)
5. [구현 가이드 및 모범 사례](#구현-가이드-및-모범-사례)
6. [핵심 과제 및 해결책](#핵심-과제-및-해결책)

---

## 개요

### 문제 정의

동적 데이터(시계열 정보, 이벤트, 상태 변화)를 온톨로지에 통합할 때 발생하는 핵심 어려움:

- **정적 스키마의 한계**: 전통적 RDF/온톨로지는 "현재 상태"만 모델링
- **시간축 손실**: 이벤트나 변화 과정을 제대로 표현하지 못함
- **질의 복잡성**: "2024년 Q3에 Samsung의 HBM 생산량은?"같은 시간 제약 질의가 어려움
- **데이터 신선도**: 스트리밍 데이터(주가, 공급망 상태 등)를 실시간 반영하기 어려움

### 솔루션 구조

Palantir Foundry의 접근법을 기반으로 GraphRAG/Neo4j에 맞게 **4계층 모델** 제시:

```
┌─────────────────────────────────────────────┐
│ 애플리케이션 계층 (RAG 쿼리, 대시보드)      │
├─────────────────────────────────────────────┤
│ 의미론적 계층 (Semantic Layer - 정적 그래프)│
│  • 엔티티 타입: Company, Fab, Product      │
│  • 관계: "manufactures", "supplies"       │
├─────────────────────────────────────────────┤
│ 동적 계층 (Kinetic Layer - 시간 정보)     │
│  • Event 노드, TimeSeries 속성            │
│  • 비교(temporal) 관계 추적               │
├─────────────────────────────────────────────┤
│ 데이터 레이어 (타임스탬프 데이터)          │
│  • 원본: 뉴스, SEC filing, 매출 데이터    │
└─────────────────────────────────────────────┘
```

---

## 팔란티어 동적 데이터 패턴 심층 분석

### 1. 객체 중심 디지털 트윈 (Object-Centric Digital Twin)

Palantir Foundry의 핵심 철학:

#### 패턴 A: Object Type + Properties + Links

**기본 구조:**
```
Object Type: Company (Samsung, SK Hynix, TSMC)
├─ Properties:
│  ├─ Static: name, country, founded_year
│  ├─ TimeSeries: revenue, market_cap, employee_count (시간 축 포함)
│  └─ DerivedProperties: profitability_ratio (계산)
├─ Links:
│  ├─ supplies → Fab
│  ├─ manufactures → Chip
│  ├─ partners_with → Company
│  └─ competes_with → Company
└─ Actions:
   ├─ announceProductLine()
   ├─ adjustCapacity()
   └─ formPartnership()
```

**핵심**: 객체는 단순 데이터 저장소가 아니라, **상태 변화 히스토리 + 가능한 행동**을 모두 포함.

#### 패턴 B: Time Series Properties (시계열 속성)

**개념**: 특정 속성이 시간에 따라 변하는 것을 명시적으로 모델링.

**예시:**
```
Company(Samsung)
  ├─ name = "Samsung Electronics" (static)
  └─ revenue (TimeSeries)
      ├─ 2023-Q1: 63.7T KRW
      ├─ 2023-Q2: 70.8T KRW
      ├─ 2023-Q3: 78.9T KRW
      └─ 2024-Q1: 59.4T KRW (반도체 부진)
  
  └─ hbm_production_volume (TimeSeries)
      ├─ 2024-Q1: 5,000 wafers/month
      ├─ 2024-Q2: 12,000 wafers/month
      ├─ 2024-Q3: 25,000 wafers/month
      └─ 2024-Q4: 40,000 wafers/month (AI 붐)
```

**이점**:
- 현재 값 + 전체 히스토리를 한 노드에서 관리
- 시계열 분석 가능 (추세, 변동율, 예측)
- 과거 데이터 손실 없음

#### 패턴 C: 이벤트 vs 상태 변화 구분

**Palantir의 이원 모델:**

| 구분 | 상태 변화 (State Change) | 비즈니스 이벤트 (Event) |
|------|-------------------------|--------------------------|
| 모델링 | 기존 노드에 TimeSeries 속성 | 별도 Event Object Type |
| 예시 | `Company.revenue` 시계열 | `ProductLaunchEvent` 노드 |
| 저장 | 스칼라 값들의 시계열 | 풍부한 메타데이터 포함 |
| 활용 | 추세 분석, 성능 지표 | 인과관계, 네트워크 영향 분석 |

**반도체 사례:**
```
# 상태 변화: TimeSeries 속성 사용
Fab(Samsung_Pyeongtak)
  └─ utilization_rate (TimeSeries)
      ├─ 2024-01-01: 65%
      ├─ 2024-06-01: 78%
      ├─ 2024-09-01: 92% (AI 칩 수요 증가)
      └─ 2025-01-01: 88%

# 비즈니스 이벤트: Event Object Type
FABExpansionEvent
  ├─ fab: Samsung_Pyeongtak
  ├─ announced_date: 2024-04-15
  ├─ type: "capacity_expansion"
  ├─ target_capacity: "200K wafers/month"
  ├─ investment_amount: "13.1T KRW"
  └─ expected_completion: 2026-Q4
  
  ├─ TRIGGERED_BY → [ChipDemandSurge]
  ├─ WILL_AFFECT → [EquipmentSuppliers, MaterialSuppliers]
  └─ PART_OF → [AIInfrastructureRace]
```

### 2. 동적 오브젝트셋 (Dynamic Object Sets)

**개념**: 필터 조건을 저장했다가, 신규 데이터가 들어올 때 자동으로 집합 갱신.

**구현 예:**
```
DynamicObjectSet: "HBM3E_Producers_Active_2024"
  condition: Company.manufactures(HBM3E) AND 
            Company.operational_fabs > 0 AND
            Company.production_started >= 2024-01-01
  
  members (자동 갱신):
  ├─ SK Hynix (2024-Q2부터)
  ├─ Samsung (2024-Q3부터)
  └─ (향후 YMTC가 조건 충족 시 자동 추가)
```

**RAG 응용:**
```
쿼리: "2024년에 HBM3E를 생산하기 시작한 회사들은?"
응답: DynamicObjectSet을 조회 → 조건 만족 회사들 검색
결과: SK Hynix, Samsung
근거: TimeSeries 데이터 (production_started) + Event logs
```

### 3. 키네틱 레이어 (Kinetic Layer): 행동과 프로세스

Palantir는 **의미론적 계층(semantic)**과 **동작 계층(kinetic)**을 분리:

**의미론적 계층**: "무엇이 존재하는가?" → 정적 그래프
**동작 계층**: "무엇이 일어나는가?" → 프로세스, 이벤트, 액션

**반도체 사례:**

```
의미론적: Company → manufactures → Fab → produces → Chip

동작적:
├─ Process: SupplyChainReset
│  ├─ trigger: GeopoliticalSanction (US export control)
│  ├─ actions:
│  │  ├─ Samsung.requestAlternativeSupplier()
│  │  ├─ SK_Hynix.diversifyEquipmentPartners()
│  │  └─ LocalSupplier.increaseProduction()
│  └─ monitoring: 실시간 완료 추적

├─ Action: ProductionCapacityAdjustment
│  ├─ Company: SK Hynix
│  ├─ before: 300K wafers/month
│  ├─ after: 450K wafers/month
│  ├─ executed_date: 2024-07-15
│  └─ cost: 2.5T KRW
│
└─ Workflow: HBM4DevelopmentCycle
   ├─ R&D Phase (6 months)
   ├─ Pilot Production (3 months)
   ├─ Certification (NVIDIA validation)
   ├─ Mass Production Ramp
   └─ Market Launch Event
```

---

## GraphRAG 환경에서의 동적 데이터 구현

### 1. Temporal GraphRAG (T-GRAG) 프레임워크

최신 연구(2024-2025)에서 제시한 **시간 인식 GraphRAG**:

#### A. 시간 정렬 규칙 그래프 (Time-Aligned Rule Graph)

**목표**: 이벤트 카테고리 간 시간적 인과관계를 사전에 구성.

**구성 요소:**

```python
# 규칙 노드 (Rule Nodes)
RuleNode: "US_Export_Control" → "EquipmentSupplyConstraint"
  ├─ start_event_category: "Geopolitical Sanction"
  ├─ end_event_category: "Supply Chain Disruption"
  ├─ typical_lag: 30-60 days
  ├─ confidence: 0.85
  └─ supporting_examples:
      ├─ SMIC supply disruption (2023)
      ├─ Huawei chip shortage (2020)
      └─ SK Hynix China fab impact (2024)

# 규칙 엣지 (Rule Edges) - 인과 체인
RuleEdge: "US_Export_Control" -[FOLLOWS_FROM]-> "AI_Demand_Surge"
  ├─ typical_sequence: AI demand ↓ chip shortage ↓ price surge ↓ export control
  ├─ observation_count: 3
  └─ time_window: 60-180 days
```

**시간 쿼리 적용:**

```
질의: "2024년 9월 SK Hynix HBM 생산 제약의 원인은?"

1. 시간 필터: events between 2024-07-01 and 2024-09-30
2. 규칙 그래프 매칭: 
   - US export control 규칙 검색
   - 60일 전(7월-8월) 관련 이벤트 찾기
   - 인과 경로 구성
3. 결과: 
   ├─ 근인(Root cause): 2024-08-07 US CFIUS 심사 강화
   ├─ 영향(Impact): 2024-09-15 고급 장비 납품 지연
   └─ 귀결(Outcome): 2024-09월 생산 일정 조정
```

#### B. Bi-temporal Model (이중 시간 모델)

**개념**: 각 데이터 포인트가 2개의 시간 축을 가짐.

```
(Company {
  name: "SK Hynix",
  
  # 비즈니스 시간 (Event Time)
  hbm_production_volume: {
    value: 450K,
    event_time: 2024-11-01  # 실제 생산 시점
  },
  
  # 시스템 시간 (System Time / Ingestion Time)
  ingestion_time: 2024-11-05,  # 데이터 수집/입력 시점
  
  # 유효 기간
  valid_from: 2024-11-01,
  valid_until: NULL (현재 유효)
})
```

**용도:**
- 데이터 수정/정정 시 기존 값 보존
- "2024-11-01 기준으로는 어떤 정보였나?"와 "2024-11-05 우리가 알았던 정보는?"을 구분
- 뉴스 정정, 공시 수정 추적

#### C. Seeded Personalized PageRank (시간 정렬 검색)

전통 GraphRAG: semantic similarity 기반 → 시간 순서 무시  
T-GRAG: **시간 제약을 먼저** → 그 범위 내에서 semantic 검색

```python
def temporal_search(query, time_constraint):
  """
  Step 1: 질의의 시간 제약 추출
  """
  time_range = extract_temporal_reference(query)
  # 예: "2024년 9월" → [2024-09-01, 2024-09-30]
  
  """
  Step 2: 시간 정렬 부분그래프 구성
  """
  temporal_subgraph = build_temporal_subgraph(
    time_window=time_range,
    expand_window=60  # 전후 60일 관련 이벤트도 포함
  )
  
  """
  Step 3: Seeded PPR - 시간 정렬 부분그래프에서만 실행
  """
  seed_entities = semantic_match(query, temporal_subgraph)
  scores = personalized_pagerank(
    seeds=seed_entities,
    graph=temporal_subgraph  # 전체 그래프 아닌 부분만
  )
  
  return top_k_results(scores)
```

**반도체 사례:**

```
Query: "2024년 상반기 SK Hynix 주가 하락의 원인은?"

1. 시간 제약: [2024-01-01, 2024-06-30] + 확장 윈도우
2. 부분그래프:
   - Nodes: SK Hynix, Samsung, NVIDIA, Chip demand, Fab incidents, ...
   - 2023-11월~2024-09월 범위의 이벤트만
3. PPR 시작점: 
   - SK Hynix stock_price decline (semantic match)
4. 확산:
   - DRAM oversupply (경쟁사 공격 정보)
   - China chip production ramp (위협 요소)
   - Fab maintenance incident (2024-Q1)
   - AI demand delay (2024-Q1 약세)
5. 결과: stock decline의 주요 원인 상위 3개 항목
```

### 2. Neo4j에서의 구체적 구현

#### A. 노드 설계: Bitemporal Versioning

```cypher
# 노드 생성 패턴
CREATE (c:Company {
  id: 'SK_Hynix_001',         # 안정적 primary key
  name: 'SK Hynix Inc.',
  country: 'South Korea',
  
  # 비즈니스 시간
  valid_from: date('2024-11-01'),
  valid_until: NULL,           # 현재 버전
  
  # 시스템 시간
  ingested_at: datetime('2024-11-05T14:30:00Z'),
  last_updated: datetime('2024-11-05T14:30:00Z'),
  
  # 버전 추적
  version: 2,                  # 이전 버전 1에서 수정
  is_deleted: false,
  source_document: 'SK_Hynix_ER_2024Q3'
})

# 시계열 속성을 별도 노드로 (복수 버전 지원)
CREATE (ts:TimeSeries {
  id: 'SK_Hynix_revenue_ts',
  entity_id: 'SK_Hynix_001',
  property_name: 'revenue',
  unit: 'KRW (Trillions)'
})

# 시계열 데이터 포인트
CREATE (point:DataPoint {
  value: 70.8,
  timestamp: date('2024-06-30'),      # 데이터 시점
  ingested_at: datetime('2024-08-15'), # 입력 시점
  source: 'SK_Hynix_ER_2024Q2',
  confidence: 0.99
})

# 관계
CREATE (ts)-[:HAS_POINT]->(point)
CREATE (c)-[:HAS_TIMESERIES]->(ts)
```

#### B. 이벤트 노드 (Event Nodes)

```cypher
# 이벤트는 별도 타입으로 풍부한 정보 저장
CREATE (evt:Event:ProductLaunchEvent {
  id: 'SK_Hynix_HBM4_Launch_001',
  entity_id: 'SK_Hynix_001',
  event_type: 'PRODUCT_LAUNCH',
  
  # 이벤트 시간
  announced_date: date('2024-09-15'),
  effective_date: date('2024-12-01'),
  
  # 이벤트 내용
  product_name: 'HBM4 (12 layers)',
  target_customer: 'NVIDIA',
  spec_bandwidth: '10 Gbps',
  power_efficiency_improvement: 0.40,  # 40% vs HBM3E
  
  # 중요도
  impact_level: 'HIGH',
  news_mentions: 45,  # 언론 보도 수
  analyst_rating: 'POSITIVE'
})

# 관련 관계
CREATE (evt)-[:ANNOUNCED_BY]->(c:Company)
CREATE (evt)-[:IMPACTS]->(market:Market {name: 'Memory Chips'})
CREATE (evt)-[:TRIGGERED_BY]->(demand:Event {name: 'AI Infrastructure Boom'})
```

#### C. 시간 범위 쿼리

```cypher
# 쿼리 1: "2024년 3분기 SK Hynix의 주요 사건들"
MATCH (c:Company {name: 'SK Hynix Inc.'})
      -[:HAS_TIMESERIES|:EXPERIENCES]->(evt:Event)
WHERE evt.announced_date >= date('2024-07-01')
  AND evt.announced_date <= date('2024-09-30')
  AND evt.impact_level IN ['HIGH', 'CRITICAL']
RETURN evt.event_type, evt.announced_date, evt.impact_level
ORDER BY evt.announced_date DESC

# 쿼리 2: "Samsung HBM3E 인증 이후 생산 능력 변화"
MATCH (samsung:Company {name: 'Samsung Electronics'})
      -[:HAS_TIMESERIES]->(ts:TimeSeries {property_name: 'hbm3e_production_volume'})
      -[:HAS_POINT]->(p1:DataPoint),
      (evt:Event {product_name: 'HBM3E Certification'})
      -[:ANNOUNCED_BY]->(samsung)
WHERE p1.timestamp >= evt.effective_date
  AND p1.timestamp <= evt.effective_date + duration('P90D')
RETURN p1.timestamp, p1.value
ORDER BY p1.timestamp ASC

# 쿼리 3: "US 수출 통제 이후 60-90일 내에 공급망 교란이 발생한 회사들"
MATCH (evt1:Event {event_type: 'EXPORT_CONTROL'})
      -[:AFFECTS]->(entity:Entity)
MATCH (evt2:Event {event_type: 'SUPPLY_DISRUPTION'})
      -[:IMPACTS]->(entity)
WHERE evt2.announced_date > evt1.announced_date
  AND evt2.announced_date <= evt1.announced_date + duration('P90D')
  AND duration.between(evt1.announced_date, evt2.announced_date).days <= 90
RETURN entity.name, evt1.announced_date, evt2.announced_date
```

### 3. LLM 기반 온톨로지 자동 구축 (Entity Linking)

**문제**: LLM만으로는 "Samsung의 주가 하락"을 구체적 노드(id='SAMSUNG_001')에 매핑하기 어려움.

**솔루션**: **Entity Linking + Knowledge Graph Augmentation**

```python
from langchain.llms import ChatGemini
from langchain.chains import LLMChain

def entity_linking_pipeline(text_chunk):
  """
  자동 온톨로지 구축 파이프라인
  """
  
  # Step 1: LLM이 텍스트에서 멘션 추출
  mention_extraction_prompt = """
  다음 텍스트에서 반도체 회사 관련 멘션을 추출하세요:
  
  Text: {text}
  
  Format:
  - Company: [회사명]
  - Event: [사건]
  - Relationship: [관계]
  - Time: [시점]
  
  Output as JSON.
  """
  
  mentions = llm.invoke(mention_extraction_prompt.format(text=text_chunk))
  # 결과: {"Company": ["SK Hynix", "Samsung"], "Event": ["HBM4 launch"], ...}
  
  # Step 2: 멘션을 그래프 노드에 매핑 (Entity Disambiguation)
  disambiguation_prompt = """
  다음 회사 멘션들을 우리 그래프의 노드 ID로 매핑하세요:
  
  Mentions: {mentions}
  Existing nodes: 
  - SK_Hynix_001 (SK Hynix Inc., 2024 현재)
  - Samsung_001 (Samsung Electronics, 2024 현재)
  - SMES_001 (Seoul Microelectronics, 소부장)
  
  Mapping: JSON format with node_id, confidence score
  """
  
  mapping = llm.invoke(disambiguation_prompt.format(mentions=mentions))
  # 결과: [{"mention": "SK하이닉스", "node_id": "SK_Hynix_001", "confidence": 0.98}, ...]
  
  # Step 3: 이벤트 타입 분류
  event_classification = llm.invoke("""
  다음 이벤트들을 분류하세요:
  - PRODUCT_LAUNCH, CAPACITY_EXPANSION, PARTNERSHIP, SUPPLY_DISRUPTION, ...
  
  Events: {events}
  """.format(events=mentions.get('Event', [])))
  
  # Step 4: 그래프 구축 (Neo4j 쿼리 자동 생성)
  for mapped_entity in mapping:
    if mapped_entity['confidence'] > 0.85:
      create_cypher_queries(mapped_entity, event_data)
  
  return neo4j_graph  # 갱신된 그래프

def create_cypher_queries(entity_mapping, event_data):
  """
  LLM이 생성한 멘션 기반으로 Cypher 쿼리 자동 생성
  """
  
  # 신규 이벤트 노드 생성
  create_event = f"""
  CREATE (evt:Event:{entity_mapping['event_type']} {{
    id: '{entity_mapping['event_id']}',
    announced_date: date('{entity_mapping['date']}'),
    description: '{entity_mapping['description']}',
    ingested_from: 'LLM_extraction',
    source_text: '{entity_mapping['source_text'][:100]}...'
  }})
  CREATE (evt)-[:ANNOUNCED_BY]->(:Company {{id: '{entity_mapping['node_id']}'}})
  """
  
  # 시계열 데이터 포인트 추가
  if 'numeric_value' in entity_mapping:
    add_timeseries = f"""
    MATCH (ts:TimeSeries {{property_name: '{entity_mapping['metric_name']}'}})
    CREATE (point:DataPoint {{
      value: {entity_mapping['numeric_value']},
      timestamp: date('{entity_mapping['date']}'),
      ingested_at: datetime(),
      source: 'LLM_extracted_from_news'
    }})
    CREATE (ts)-[:HAS_POINT]->(point)
    """
    neo4j_graph.query(add_timeseries)
  
  neo4j_graph.query(create_event)
```

**실제 예시:**

```
원문 (뉴스): "SK Hynix가 9월 15일 HBM4 신제품 공개... 
            NVIDIA용으로 12층 구조, 10Gbps 대역폭..."

LLM 추출:
{
  "Company": ["SK Hynix"],
  "Event": ["Product Launch"],
  "Product": ["HBM4"],
  "Date": ["2024-09-15"],
  "Specs": [{"bandwidth": "10 Gbps", "layers": 12}]
}

멘션 매핑:
[
  {"mention": "SK Hynix", "node_id": "SK_Hynix_001", "confidence": 0.99},
  {"mention": "HBM4", "product_id": "HBM4_Gen", "confidence": 0.95}
]

그래프 쿼리:
CREATE (evt:Event:ProductLaunchEvent {
  id: 'SK_Hynix_HBM4_20240915',
  announced_date: date('2024-09-15'),
  product_name: 'HBM4',
  spec_bandwidth: '10 Gbps'
})
CREATE (evt)-[:ANNOUNCED_BY]->(SK_Hynix_001)
```

---

## 대한민국 반도체 섹터 온톨로지 설계

### 1. 엔티티 타입 정의 (Object Types)

#### A. 핵심 엔티티

```
Core Entities:
├─ Company
│  ├─ memory_type: [DRAM, NAND, HBM, ...]
│  ├─ market_position: [Leader, Challenger, Emerging]
│  ├─ geographic_presence: [Seoul, Icheon, Pyeongtak, ...]
│  └─ TimeSeries: revenue, profit, r&d_spend, headcount, patent_count
│
├─ Fab (Manufacturing Facility)
│  ├─ location: Pyeongtak, Icheon, Gumi, ...
│  ├─ wafer_size: [200mm, 300mm]
│  ├─ technology_node: [3nm, 5nm, 7nm, ...]
│  ├─ product_type: [Memory, Logic, ...]
│  └─ TimeSeries: capacity, utilization_rate, yield
│
├─ Chip (Product)
│  ├─ product_line: HBM4, HBM3E, DRAM, NAND, ...
│  ├─ target_market: [DataCenter, Consumer, ...] 
│  ├─ specs: bandwidth, latency, power_consumption
│  └─ TimeSeries: unit_sales, unit_price, market_share
│
├─ Equipment & Materials Supplier
│  ├─ category: [Lithography, Deposition, Etching, ...]
│  ├─ tier: [Tier-1 global, Tier-2 Korean, ...]
│  └─ TimeSeries: order_volume, delivery_time, quality_score
│
└─ Event
   ├─ ProductLaunchEvent
   ├─ CapacityExpansionEvent
   ├─ PartnershipEvent
   ├─ SupplyChainDisruptionEvent
   ├─ RegulationEvent (수출 규제 등)
   └─ MarketShiftEvent (수요 변화)
```

#### B. 관계 정의 (Link Types)

```
Relationships:

Core Relationships:
  Company -[:manufactures]-> Fab
  Company -[:produces]-> Chip
  Fab -[:can_produce]-> Chip
  Fab -[:requires]-> Equipment
  Fab -[:uses]-> Material
  Company -[:supplies]-> Equipment/Material
  Company -[:partners_with]-> Company
  Company -[:competes_with]-> Company

Temporal Relationships:
  Company -[:experiences]-> Event
  Event -[:triggered_by]-> RootCause
  Event -[:impacts]-> AffectedEntity
  Event -[:follows]-> PrecedingEvent (인과 관계)

Supply Chain:
  Chip -[:requires]-> Equipment
  Chip -[:depends_on]-> Material
  Equipment -[:supplied_by]-> EquipmentMaker
  Material -[:supplied_by]-> MaterialSupplier

Market:
  Chip -[:targets]-> Market
  Company -[:operates_in]-> GeographicRegion
  Company -[:subject_to]-> Regulation
```

### 2. 동적 데이터 속성 (Time Series + Events)

#### A. 주요 시계열 메트릭

```
Company-level TimeSeries:
├─ Financial:
│  ├─ revenue (분기별)
│  ├─ operating_profit
│  ├─ r&d_spending
│  └─ capex (설비 투자)
│
├─ Operational:
│  ├─ employee_count
│  ├─ patent_filings
│  ├─ production_capacity (wafer/month)
│  └─ market_share_percent
│
└─ Market:
   ├─ stock_price
   ├─ market_cap
   └─ analyst_rating

Fab-level TimeSeries:
├─ capacity (300mm eq wafers/month)
├─ utilization_rate (%)
├─ yield (%)
├─ product_mix (% HBM, DRAM, etc.)
└─ equipment_investment

Chip-level TimeSeries:
├─ unit_price ($/GB or $/chip)
├─ unit_sales (million units/quarter)
├─ market_share (%)
└─ competitor_benchmark
```

#### B. 주요 이벤트 타입

```
반도체 섹터 특화 이벤트:

Product Events:
  - ProductLaunchEvent: 신제품 출시
  - SpecUpgradeEvent: 성능 업그레이드
  - ProductDiscontinuationEvent: 단종

Capacity Events:
  - FabExpansionEvent: 신규 FAB 또는 확장
  - CapacityAdjustmentEvent: 생산 능력 조정
  - ProductionLineUpgradeEvent: 장비 개선

Market Events:
  - PriceWarEvent: 칩 가격 전쟁
  - MarketShareShiftEvent: 점유율 변화
  - DemandSurgeEvent: 수요 급증 (e.g., AI)

Supply Chain Events:
  - EquipmentShortageEvent: 장비 부족
  - MaterialSupplyDisruptionEvent: 원자재 공급 차질
  - SupplierDiversificationEvent: 공급처 다원화

Regulatory Events:
  - ExportControlEvent: 수출 규제 (US CFIUS, etc)
  - SubsidyAnnouncementEvent: 정부 지원금
  - TariffEvent: 관세 부과

Strategic Events:
  - MergerAcquisitionEvent: 인수합병
  - JointVentureEvent: 합작회사 설립
  - PartnershipEvent: 전략적 제휴
```

### 3. 대한민국 반도체 생태계 구체 사례

#### Case 1: SK Hynix HBM4 개발 (2024-2025)

```cypher
# 주요 엔티티
CREATE (skh:Company {
  id: 'SK_Hynix_001',
  name: 'SK Hynix Inc.',
  country: 'South Korea',
  founded_year: 1983,
  headquarter: 'Icheon, Gyeonggi'
})

# 시계열 속성
CREATE (skh)-[:HAS_TIMESERIES]->(hbm_vol:TimeSeries {
  property_name: 'hbm_production_volume',
  unit: 'wafers/month'
})

# 시계열 데이터 포인트
CREATE (hbm_vol)-[:HAS_POINT]->
  (p1:DataPoint {value: 5000, timestamp: date('2024-01-01')}),
  (p2:DataPoint {value: 12000, timestamp: date('2024-06-01')}),
  (p3:DataPoint {value: 25000, timestamp: date('2024-09-01')}),
  (p4:DataPoint {value: 45000, timestamp: date('2024-12-01')})

# HBM4 출시 이벤트
CREATE (evt:Event:ProductLaunchEvent {
  id: 'SKH_HBM4_Launch_20240915',
  product_name: 'HBM4 (12-layer)',
  announced_date: date('2024-09-15'),
  effective_date: date('2024-12-01'),
  spec_bandwidth: '10 Gbps',
  power_efficiency: '+40%',
  target_customer: 'NVIDIA',
  investment_amount: 2500  # billion KRW
})

# 이벤트 관계
CREATE (evt)-[:ANNOUNCED_BY]->(skh)
CREATE (evt)-[:TRIGGERED_BY]->(aiBoom:Event {name: 'AI Infrastructure Boom'})

# TSMC와의 협력 (기본 다이용)
CREATE (tsmc:Company {id: 'TSMC_001', name: 'Taiwan Semiconductor'})
CREATE (evt)-[:USES_TECHNOLOGY_FROM]->(tsmc)
CREATE (skh)-[:PARTNERS_WITH {type: 'HBM4 CoWoS'}]->(tsmc)
```

**시간별 분석 쿼리:**

```cypher
# 쿼리: HBM4 출시가 SK Hynix 생산량에 미친 영향
MATCH (skh:Company {name: 'SK Hynix Inc.'})
      -[:HAS_TIMESERIES]-> (ts:TimeSeries {property_name: 'hbm_production_volume'})
      -[:HAS_POINT]->(p:DataPoint),
      (evt:Event {id: 'SKH_HBM4_Launch_20240915'})
      -[:ANNOUNCED_BY]->(skh)
WHERE p.timestamp >= evt.announced_date - duration('P3M')
  AND p.timestamp <= evt.announced_date + duration('P3M')
RETURN p.timestamp, p.value, 
       CASE 
         WHEN p.timestamp = evt.announced_date THEN 'LAUNCH_DATE'
         WHEN p.timestamp < evt.announced_date THEN 'PRE_LAUNCH'
         ELSE 'POST_LAUNCH'
       END as phase
ORDER BY p.timestamp

# 결과:
# timestamp     | value | phase
# 2024-06-01    | 12000 | PRE_LAUNCH
# 2024-09-15    | 12000 | LAUNCH_DATE (공지)
# 2024-12-01    | 45000 | POST_LAUNCH (양산 시작)
```

#### Case 2: Samsung HBM3E 인증 및 경쟁 (2024)

```cypher
# Samsung의 HBM 포지셔닝 변화
CREATE (samsung:Company {
  id: 'Samsung_001',
  name: 'Samsung Electronics'
})

# 이벤트 1: NVIDIA 인증
CREATE (cert_evt:Event:CertificationEvent {
  id: 'Samsung_HBM3E_Cert_20240601',
  announced_date: date('2024-06-01'),
  product: 'HBM3E',
  certifier: 'NVIDIA',
  significance: 'NVIDIA 공식 승인 → 공급처 다원화'
})
CREATE (cert_evt)-[:ANNOUNCED_BY]->(samsung)

# 이벤트 2: 경쟁 심화
CREATE (competition_evt:Event:MarketCompetitionEvent {
  id: 'HBM_Competition_Intensifies_20240601-20241231',
  description: 'SK Hynix vs Samsung HBM market share battle',
  competitors: ['SK_Hynix_001', 'Samsung_001'],
  period_start: date('2024-06-01'),
  period_end: date('2024-12-31'),
  winner_trend: 'SK Hynix (volume leadership)',
  impact: 'Price pressure, aggressive expansion'
})

# Samsung의 대응 (Action)
CREATE (response:Event:CapacityExpansionEvent {
  id: 'Samsung_HBM_Expansion_20240815',
  announced_date: date('2024-08-15'),
  target_capacity: '+150% over 12 months',
  investment: 7300  # billion KRW
  expected_completion: date('2025-Q4')
})
CREATE (response)-[:IN_RESPONSE_TO]->(competition_evt)

# 시계열: 단가 추이
CREATE (samsung)-[:HAS_TIMESERIES]->(price:TimeSeries {
  property_name: 'hbm3e_unit_price',
  unit: '$/chip'
})
CREATE (price)-[:HAS_POINT]->
  (pr1:DataPoint {value: 850, timestamp: date('2024-03-01')}),
  (pr2:DataPoint {value: 720, timestamp: date('2024-06-01')}),
  (pr3:DataPoint {value: 580, timestamp: date('2024-09-01')}),
  (pr4:DataPoint {value: 420, timestamp: date('2024-12-01')})
# 가격 전쟁: 6개월간 50% 하락
```

#### Case 3: 정부 규제 및 공급망 영향

```cypher
# 규제 이벤트
CREATE (regulation:Event:RegulationEvent {
  id: 'US_CFIUS_Review_20240708',
  announced_date: date('2024-07-08'),
  type: 'EXPORT_CONTROL',
  affected_countries: ['South Korea', 'China', 'Japan'],
  description: 'US CFIUS strengthens AI chip export screening'
})

# SK Hynix의 직접 영향
CREATE (direct_impact:Event:SupplyChainDisruptionEvent {
  id: 'SKH_Equipment_Delay_20240815',
  announced_date: date('2024-08-15'),
  root_cause: regulation,
  impact_company: 'SK_Hynix_001',
  type: 'EQUIPMENT_DELIVERY_DELAY',
  delayed_equipment: 'Advanced packaging tools (CoWoS related)',
  delay_duration_days: 45,
  production_impact_wafers: 15000
})
CREATE (direct_impact)-[:TRIGGERED_BY]->(regulation)

# 연쇄 효과: 소부장 업체
CREATE (supplier:Company {
  id: 'SEMES_001',
  name: 'SEMES Co., Ltd',
  category: 'Semiconductor Equipment Supplier',
  exports_to: ['SK_Hynix_001', 'Samsung_001']
})

CREATE (supply_adjust:Event:OrderAdjustmentEvent {
  id: 'SEMES_Order_Reduction_20240901',
  announced_date: date('2024-09-01'),
  reason: 'SK Hynix와 Samsung의 생산 일정 조정',
  order_reduction_percent: 25,
  revenue_impact: -35  # billion KRW estimate
})
CREATE (supply_adjust)-[:CAUSED_BY]->(direct_impact)
CREATE (supply_adjust)-[:AFFECTS]->(supplier)
```

---

## 구현 가이드 및 모범 사례

### 1. 데이터 수집 및 정규화 파이프라인

#### A. 데이터 소스 계층화

```python
# 우선순위별 데이터 소스
DATA_SOURCES = {
  '1st_tier': {
    'official': [
      'SK_Hynix_ER',          # 공식 ER (반기보고서)
      'Samsung_ER',
      'SEC_Filings',          # US listed companies
      'KRX_Disclosures'       # 한국거래소 공시
    ],
    'reliability': 0.99
  },
  
  '2nd_tier': {
    'semi_official': [
      'Company_Press_Release',
      'Investor_Conference',
      'Analyst_Reports'       # Gartner, IC Insights, etc
    ],
    'reliability': 0.88
  },
  
  '3rd_tier': {
    'news': [
      'Korea_JoonAng_Daily',
      'The_Investor',
      'Korea_Economic_Daily',
      'Bloomberg',
      'Reuters'
    ],
    'reliability': 0.75
  },
  
  '4th_tier': {
    'specialized': [
      'SemiEngineering',
      'EE_Times',
      'TechNode',
      'Company_Forums'
    ],
    'reliability': 0.60
  }
}
```

#### B. 정규화 프로세스

```python
def normalize_and_ingest_timeseries(raw_data, entity_id, property_name):
  """
  원본 데이터 → 정규화 → Neo4j 저장
  """
  
  # Step 1: 데이터 유효성 검증
  validate_result = validate_data({
    'entity_id': entity_id,
    'property_name': property_name,
    'value': raw_data['value'],
    'timestamp': raw_data['timestamp'],
    'source': raw_data['source'],
    'confidence': raw_data.get('confidence', 0.75)
  })
  
  if not validate_result.is_valid:
    log_and_flag_anomaly(raw_data, validate_result.errors)
    return None
  
  # Step 2: 중복 제거 (Upsert 로직)
  existing = neo4j.query(f"""
    MATCH (ts:TimeSeries {{entity_id: '{entity_id}', property_name: '{property_name}'}})
          -[:HAS_POINT]->(p:DataPoint {{timestamp: {raw_data['timestamp']}}})
    RETURN p
  """)
  
  if existing:
    # 기존 데이터 vs 신규 데이터 비교
    if existing[0].confidence < raw_data['confidence']:
      # 신규가 더 신뢰도 높음 → 업데이트
      update_datapoint(existing[0], raw_data)
    else:
      # 기존 데이터 유지
      log_duplicate_ignored(raw_data, existing[0])
      return existing[0]
  
  # Step 3: 신규 데이터 포인트 생성
  new_point = DataPoint(
    value=normalize_value(raw_data['value'], property_name),
    timestamp=parse_timestamp(raw_data['timestamp']),
    ingested_at=datetime.now(),
    source=raw_data['source'],
    source_confidence=raw_data['confidence'],
    source_document_id=raw_data.get('document_id')
  )
  
  # Step 4: Neo4j에 저장
  neo4j.create_datapoint(new_point)
  
  # Step 5: 이상치 감지 (Anomaly Detection)
  anomaly_check = detect_anomalies(entity_id, property_name, new_point)
  if anomaly_check.is_anomalous:
    flag_for_manual_review(new_point, anomaly_check.reason)
  
  return new_point
```

### 2. 온톨로지 유지보수 및 버전 관리

#### A. 스키마 진화 (Schema Evolution)

```cypher
# 새로운 관계 타입 추가 시:
# Before: Company -[:supplies]-> Equipment
# After: Company -[:supplies {since_date, contract_type}]-> Equipment

# 마이그레이션 쿼리:
MATCH (c:Company)-[r:supplies]->(e:Equipment)
WITH c, e, r
DELETE r
CREATE (c)-[new_r:supplies {
  since_date: date('2024-01-01'),  # 기본값 또는 추론
  contract_type: 'ongoing',
  original_rel_created: datetime()
}]->(e)
```

#### B. 버전 추적

```python
# 온톨로지 버전 관리
ONTOLOGY_VERSION = {
  'version': '2.1.3',
  'release_date': '2024-12-15',
  'changes': [
    'Added TimeSeries support for equipment delivery time',
    'New event type: SupplyChainOptimizationEvent',
    'Extended Company properties: esg_score, government_subsidies'
  ],
  'breaking_changes': [],
  'migration_scripts': ['migrate_v2.0_to_v2.1.cypher']
}

# 각 노드에 버전 추적
CREATE (c:Company {
  id: 'SK_Hynix_001',
  ontology_version_created: '2.0.0',
  ontology_version_updated: '2.1.3',
  last_updated: datetime()
})
```

### 3. 쿼리 최적화 및 성능

#### A. 인덱스 전략

```cypher
# 시계열 쿼리가 많으므로:
CREATE INDEX ON :DataPoint(timestamp)
CREATE INDEX ON :DataPoint(entity_id, timestamp)
CREATE COMPOSITE INDEX ON :DataPoint(property_name, timestamp)

# 이벤트 필터링 자주:
CREATE INDEX ON :Event(announced_date)
CREATE INDEX ON :Event(event_type)

# 회사 조회:
CREATE INDEX ON :Company(id)
CREATE INDEX ON :Company(country)
CREATE INDEX ON :Company(name)
```

#### B. 캐싱 전략 (시계열 데이터)

```python
# 자주 조회되는 시계열은 Redis 캐싱
CACHE_TTL_SECONDS = {
  'company_timeseries': 86400,      # 1일 (자주 바뀌지 않음)
  'fab_utilization': 3600,          # 1시간 (거의 실시간)
  'chip_prices': 7200,              # 2시간 (일일 업데이트)
  'events_recent': 1800,            # 30분 (새 이벤트 감지)
}

def get_timeseries_with_cache(entity_id, property_name, time_range):
  cache_key = f"ts:{entity_id}:{property_name}:{time_range}"
  
  cached = redis_cache.get(cache_key)
  if cached:
    return cached
  
  result = neo4j.query(f"""
    MATCH (c)-[:HAS_TIMESERIES]->(ts:TimeSeries)
    WHERE c.id = '{entity_id}' AND ts.property_name = '{property_name}'
    MATCH (ts)-[:HAS_POINT]->(p:DataPoint)
    WHERE p.timestamp >= {time_range.start} AND p.timestamp <= {time_range.end}
    RETURN p ORDER BY p.timestamp
  """)
  
  ttl = CACHE_TTL_SECONDS.get(property_name, 3600)
  redis_cache.set(cache_key, result, ex=ttl)
  return result
```

---

## 핵심 과제 및 해결책

### 1. 데이터 일관성 문제

**문제:**
- 뉴스: "SK Hynix, HBM 생산량 2배 증가" (정성적)
- ER: "HBM 생산 25,000 wafers/month" (정량적)
- 어느 것을 그래프에 저장할 것인가?

**솔루션:**

```python
def reconcile_conflicting_data(source1, source2):
  """
  서로 다른 소스의 데이터 조정
  """
  
  # Step 1: 신뢰도 점수 비교
  if source1.confidence > source2.confidence:
    primary = source1
    secondary = source2
  else:
    primary = source2
    secondary = source1
  
  # Step 2: Primary 데이터 저장
  store_primary_data(primary)
  
  # Step 3: Secondary 데이터를 검증 정보로 저장
  CREATE (primary_point:DataPoint {value: ..., ...})
  CREATE (validation:ValidationRecord {
    primary_source: primary.source,
    secondary_source: secondary.source,
    agreement: similarity_score(primary, secondary),
    discrepancy_reason: determine_cause(primary, secondary)
  })
  CREATE (primary_point)-[:HAS_VALIDATION]->(validation)
  
  # Step 4: 큰 불일치 → 수동 검토 플래그
  if discrepancy > 0.20:  # 20% 이상 차이
    flag_for_manual_review()
```

### 2. 실시간 데이터 업데이트

**문제:** FAB 가동률, 칩 가격 등이 시시각각 변함.

**솔루션:**

```python
# 이벤트 기반 수신처리 (Event-driven Architecture)
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
  'semiconductor-data-stream',
  bootstrap_servers=['kafka-broker:9092'],
  group_id='ontology-ingestion'
)

def stream_ingest_realtime():
  for message in consumer:
    event_data = json.loads(message.value)
    
    # 타입별 처리
    if event_data['type'] == 'timeseries_update':
      normalize_and_ingest_timeseries(
        entity_id=event_data['entity_id'],
        property_name=event_data['property'],
        value=event_data['value'],
        timestamp=event_data['timestamp']
      )
    
    elif event_data['type'] == 'news_event':
      # LLM이 뉴스 → Entity + Event로 변환
      extract_and_create_event(event_data['news_text'])
    
    # 캐시 무효화
    invalidate_cache(event_data['entity_id'])
```

### 3. 온톨로지 복잡도 관리

**문제:** 반도체 산업이 복잡 → 무한정 엔티티/관계 추가 가능?

**솔루션:** **계층적 온톨로지 설계**

```
Level 1 (핵심): Company, Fab, Chip, Event
├─ 필수 실행
├─ 모든 쿼리 지원

Level 2 (중요): Equipment, Material, RegulationEvent, ...
├─ 대부분의 분석에 필요
├─ 점진적 추가

Level 3 (선택): DetailedProductSpec, EquipmentPartNumber, ...
├─ 특정 심화 분석에만 필요
├─ 온디맨드 확장

Level 4 (미래): SupplierESGScore, CarbonFootprint, ...
├─ 향후 추가 가능
├─ 현재 MVP에는 불포함
```

### 4. GraphRAG 쿼리 성능

**문제:** 시간 범위 + 시맨틱 검색 + 그래프 순회 = 느린 응답.

**솔루션:**

```python
def optimized_temporal_graphrag_query(query_text, time_constraint):
  """
  3단계 최적화
  """
  
  # Step 1: 시간 범위로 먼저 좁히기 (가장 선택적)
  time_filtered_nodes = neo4j.query(f"""
    MATCH (n:Event|DataPoint)
    WHERE n.timestamp >= {time_constraint.start}
      AND n.timestamp <= {time_constraint.end}
    RETURN id(n) as node_ids
  """)  # 전체 노드의 5% 정도로 축소
  
  # Step 2: 축소된 그래프에서 embedding 기반 검색
  semantic_matches = semantic_search(
    query_text,
    within_node_ids=time_filtered_nodes
  )
  
  # Step 3: 상위 노드들의 이웃만 트래버스
  final_subgraph = traverse_neighborhood(
    seed_nodes=semantic_matches[:20],
    max_depth=2
  )
  
  return final_subgraph
```

### 5. LLM 기반 자동화의 한계

**문제:** LLM의 환각(hallucination) → 잘못된 엔티티 매핑.

**솔루션:** **Human-in-the-Loop**

```python
def entity_linking_with_human_review(text, confidence_threshold=0.80):
  """
  높은 신뢰도 → 자동 승인
  낮은 신뢰도 → 인간 검토
  """
  
  llm_predictions = extract_entities_with_confidence(text)
  
  auto_approved = []
  needs_review = []
  
  for prediction in llm_predictions:
    if prediction['confidence'] >= confidence_threshold:
      # 자동 승인
      create_in_graph(prediction)
      auto_approved.append(prediction)
    else:
      # 인간 검토 큐에 추가
      add_to_review_queue(prediction)
      needs_review.append(prediction)
  
  # 검토 대기 중인 것들: 사용자 수동 승인까지 임시 저장
  return {
    'auto_approved': len(auto_approved),
    'pending_review': len(needs_review),
    'review_queue_id': generate_queue_id()
  }
```

---

## 구현 로드맵

### Phase 1: MVP (2-3주)

```
Scope:
├─ Core entities: Company (Samsung, SK Hynix, TSMC, ...) 
├─ Core TimeSeries: revenue, production_volume, market_cap
├─ Basic events: ProductLaunch, CapacityExpansion
├─ Neo4j schema setup
└─ LLM entity extraction (높은 신뢰도만)

Deliverables:
├─ Neo4j graph with 50+ companies
├─ 2024년 주요 100개 이벤트
├─ 기본 GraphRAG 쿼리 작동
└─ Jupyter 데모 노트북
```

### Phase 2: Enhancement (3-4주)

```
Scope:
├─ Equipment & Material suppliers 추가
├─ Fab-level details
├─ Temporal constraint handling
├─ Bitemporal versioning
├─ 뉴스 자동 수집 + LLM 처리
└─ 대시보드 구축 시작

Deliverables:
├─ 전체 공급망 그래프
├─ 실시간 이벤트 스트림
├─ T-GRAG 시간 제약 쿼리
└─ 웹 대시보드 (기본)
```

### Phase 3: Production (4-6주)

```
Scope:
├─ 성능 최적화 (인덱싱, 캐싱)
├─ 규제 이벤트 + 지정학적 분석
├─ 시뮬레이션/예측 기능
├─ 다국어 지원
└─ 엔터프라이즈급 관리 도구

Deliverables:
├─ Production-ready Neo4j 인프라
├─ 실시간 대시보드
├─ GraphRAG 기반 보고서 자동 생성
├─ API 문서
└─ 운영 가이드
```

---

## 핵심 요약

### 동적 데이터 처리의 3가지 핵심 패턴

| 패턴 | 팔란티어 용어 | GraphRAG 구현 | 반도체 예시 |
|------|------------|------------|----------|
| **상태 변화** | TimeSeries Properties | Neo4j DataPoint + timestamp | Company.revenue (분기별) |
| **비즈니스 이벤트** | Event Object Type | Event 노드 + 풍부한 메타 | ProductLaunch, CapacityExpansion |
| **인과 관계** | Rule Graph (동적 객체셋) | Temporal constraint + PPR | US export control → Supply disruption |

### 4계층 온톨로지 구조

```
Application (RAG 쿼리, 대시보드)
    ↓
Semantic Layer (정적 그래프: Company, Fab, Chip)
    ↓
Kinetic Layer (동적: Events, TimeSeries, Actions)
    ↓
Data Layer (원본: 뉴스, SEC filing, 시계열 API)
```

### 구현 우선순위

1. **Core entities** (Company, Fab, Chip) + **TimeSeries** 속성
2. **Event nodes** (ProductLaunch, CapacityExpansion) + **Temporal constraints**
3. **LLM 자동화** (Entity linking) + **Human review**
4. **성능 최적화** (Indexing, Caching, T-GRAG)

---

## 참고 자료

**팔란티어 온톨로지:**
- [Palantir Foundry Ontology Overview](https://palantir.com/docs/foundry/ontology/overview/)
- [Palantir Time Series Properties](https://palantir.com/docs/foundry/time-series/time-series-overview/)
- [Palantir Workshop: Time Series](https://palantir.com/docs/foundry/workshop/time-series-properties/)

**GraphRAG & 시간 제약:**
- [STAR-RAG: Temporal GraphRAG Framework](https://openreview.net/pdf/a15c74e81da7cf907c5076fbc500ba18aea41350.pdf)
- [T-GRAG: Dynamic GraphRAG Framework (arXiv:2508.01680)](https://arxiv.org/abs/2508.01680)
- [Neo4j Temporal Patterns](https://dev.to/satyam_shree_087caef77512/a-practical-guide-to-temporal-versioning-in-neo4j-nodes-relationships-and-historical-gr)

**대한민국 반도체 산업:**
- [Samsung & SK Hynix: AI Supply Chain (2025)](https://www.ainvest.com/news/samsung-sk-hynix-strategic-supply-chain-powerhouses-ai-chip-ecosystem-2510/)
- [SK Hynix 공식 경영설명회 (2024)](https://www.skhynix.com)
- [Samsung Electronics ER (2024)](https://www.samsung.com/ir)
- [한국경제신문, 대한민국 반도체 섹터 분석](https://www.hankyung.com)

---

**이 문서는 2025년 12월 21일 기준의 최신 정보를 반영하며, Palantir Foundry 패턴, 최신 GraphRAG 논문, 그리고 한국 반도체 산업 현황을 통합한 실무 가이드입니다.**