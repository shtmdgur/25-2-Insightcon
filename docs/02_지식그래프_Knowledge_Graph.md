# 지식 그래프 (Knowledge Graph) 완전 정리 가이드

## 📖 목차
1. [지식 그래프란 무엇인가?](#지식-그래프란-무엇인가)
2. [금융 지식 그래프 구축](#금융-지식-그래프-구축)
3. [GraphRAG 패턴](#graphrag-패턴)
4. [동적 그래프 신경망](#동적-그래프-신경망)
5. [실전 구현 가이드](#실전-구현-가이드)

---

## 지식 그래프란 무엇인가?

### 기본 개념

**지식 그래프(Knowledge Graph)**는 엔티티(실제 존재하는 객체)와 그들 간의 관계를 방향성 그래프로 표현한 데이터 구조입니다.

#### 간단한 비유
- **관계형 데이터베이스**: 표(Table) 형태로 데이터 저장
- **지식 그래프**: 노드(Node)와 엣지(Edge)로 관계를 시각적으로 표현

**예시**:
```
관계형 DB:
Company Table: [id, name, marketCap]
Product Table: [id, name, company_id]

지식 그래프:
(삼성전자) --[manufactures]--> (HBM3)
(삼성전자) --[competesWith]--> (SK하이닉스)
(삼성전자) --[hasMetric]--> (Revenue: 300조원)
```

### 지식 그래프의 구조

#### 기본 구성 요소

1. **노드 (Node)**: 엔티티나 개념
   - 예: `삼성전자`, `HBM3`, `Revenue`

2. **엣지 (Edge)**: 관계
   - 예: `manufactures`, `competesWith`, `hasMetric`

3. **속성 (Properties)**: 노드나 엣지의 특성
   - 예: `삼성전자.marketCap = 500조원`

#### 트리플 (Triple) 표현

지식 그래프의 기본 단위는 **트리플(Triple)**입니다:

```
(주체, 관계, 객체)
(Subject, Predicate, Object)
```

**예시**:
```
(삼성전자, manufactures, HBM3)
(삼성전자, hasMarketCap, 500조원)
(삼성전자, competesWith, SK하이닉스)
```

### 지식 그래프의 장점

1. **관계 중심 탐색**: 복잡한 다단계 관계를 쉽게 탐색
2. **유연한 스키마**: 필요에 따라 스키마 변경 가능
3. **불완전한 지식 처리**: 일부 정보가 없어도 그래프 구성 가능
4. **추론 가능**: 명시적 관계로부터 암묵적 관계 추론

---

## 금융 지식 그래프 구축

### FinKario의 지식 그래프 구조

FinKario 논문에서는 **305,360개 엔티티**, **9,625개 관계 트리플**, **19개 관계 타입**을 가진 대규모 금융 지식 그래프를 구축했습니다.

#### 1. Attribute Subgraph (속성 서브그래프)

**목적**: 상대적으로 안정적인 기본 정보 저장

**구조**:
```
Company (노드)
  ├─ Properties: name, industry, exchange, code
  ├─ Relationships:
  │   ├─ [HAS_INDUSTRY] → Industry
  │   ├─ [LISTED_ON] → Exchange
  │   ├─ [HAS_PRODUCT] → ProductLine
  │   └─ [HAS_METRIC] → Metric
  └─ Instances: 삼성전자, SK하이닉스, ...
```

**예시 데이터**:
```
(삼성전자) --[HAS_INDUSTRY]--> (Semiconductor)
(삼성전자) --[LISTED_ON]--> (KOSPI)
(삼성전자) --[HAS_PRODUCT]--> (HBM3)
(삼성전자) --[HAS_METRIC]--> (Revenue: 300조원, 2024Q3)
```

#### 2. Event Subgraph (이벤트 서브그래프)

**목적**: 시간에 민감한 동적 이벤트 저장

**구조**:
```
Event (노드)
  ├─ Types: Earnings, Guidance, M&A, Regulation, ...
  ├─ Properties: date, description, impact
  └─ Relationships:
      ├─ [TRIGGERED_BY] → Company
      ├─ [AFFECTS] → Metric
      └─ [RELATED_TO] → Policy
```

**예시 데이터**:
```
(2024Q3_Earnings) --[TRIGGERED_BY]--> (삼성전자)
(2024Q3_Earnings) --[AFFECTS]--> (Revenue: 300조원)
(2024Q3_Earnings) --[HAS_TYPE]--> (Earnings)
(2024Q3_Earnings).date = "2024-10-25"
```

#### 3. 통합 그래프

두 서브그래프를 통합하여 종합적인 금융 지식 그래프를 구성:

```
G_FinKario = G_Attribute ∪ G_Event
```

**시각화 예시**:
```
        Company (삼성전자)
            │
            ├─[HAS_METRIC]──► Metric (Revenue: 300조원)
            │                      ▲
            │                      │
            └─[TRIGGERED_BY]──► Event (2024Q3_Earnings)
                                      │
                                      └─[AFFECTS]──► Metric (Revenue: 300조원)
```

### 자동 구축 파이프라인

FinKario는 4단계 파이프라인으로 지식 그래프를 자동 구축합니다.

#### Step 1: Domain Corpus Acquisition (도메인 코퍼스 획득)

**활동**:
1. 증권 리포트 수집 (East Money 웹사이트)
2. PDF → Markdown 변환 (MinerU 사용)
3. 불필요한 내용 제거 (면책 조항, 이미지, 반복 법적 문구)

**예시**:
```python
# PDF를 Markdown으로 변환
from mineru import PDFParser

parser = PDFParser()
markdown_content = parser.parse("samsung_report.pdf")

# 정제
cleaned_content = remove_disclaimers(markdown_content)
cleaned_content = remove_images(cleaned_content)
cleaned_content = remove_legal_statements(cleaned_content)
```

#### Step 2: Schema Construction (스키마 구축)

**활동**:
1. Attribute Graph Schema 생성 (CFA, J.P. Morgan 템플릿 기반)
2. Event Graph Schema 생성 (FIBO 기반)

**자세한 내용은 [온톨로지 문서](01_온톨로지_Ontology.md) 참조**

#### Step 3: Knowledge Population (지식 채우기)

**활동**: 각 문서에서 엔티티와 관계 추출

**프롬프트 기반 추출**:
```python
# LLM을 사용한 엔티티 추출
def extract_knowledge(document, schema, timestamp):
    prompt = f"""
    다음 증권 리포트에서 엔티티와 관계를 추출하세요.
    
    문서: {document}
    스키마: {schema}
    타임스탬프: {timestamp}
    
    출력 형식:
    {{
        "entities": [
            {{"type": "Company", "name": "삼성전자", "properties": {{}}}},
            {{"type": "Metric", "name": "Revenue", "value": "300조원"}}
        ],
        "relations": [
            {{"from": "삼성전자", "relation": "HAS_METRIC", "to": "Revenue"}}
        ]
    }}
    """
    
    result = llm.generate(prompt)
    return parse_json(result)
```

**결과**:
```python
# Attribute Graph
G_A = {
    (삼성전자, HAS_INDUSTRY, Semiconductor, τ),
    (삼성전자, HAS_METRIC, Revenue_300조, τ),
    ...
}

# Event Graph
G_E = {
    (2024Q3_Earnings, TRIGGERED_BY, 삼성전자, τ),
    (2024Q3_Earnings, AFFECTS, Revenue_300조, τ),
    ...
}
```

#### Step 4: Quality Control Refinement (품질 관리 및 정제)

**활동**:
1. 엔티티 정규화: 변형된 이름을 표준 형태로 통일
2. 속성 보완: Tushare 플랫폼으로 누락된 수치 보완
3. 오류 수정: LLM을 사용한 오류 자동 수정

**알고리즘**:
```python
def quality_control_refinement(raw_graph, reference_dict, llm):
    # Step 1: 엔티티 정규화
    for entity in raw_graph.entities:
        if is_name_variant(entity):  # "BYD Inc.", "BYD Auto" 등
            entity = normalize_to_canonical(entity)  # "BYD"
    
    # Step 2: 속성 보완
    for triple in raw_graph.triples:
        if is_numeric_attribute(triple.relation):
            if is_missing_or_incomplete(triple.object):
                # Tushare에서 값 조회
                value = query_tushare(triple.subject, triple.relation)
                triple.object = value
    
    # Step 3: 오류 수정
    for triple in raw_graph.triples:
        if contains_placeholder(triple.object):
            # 원본 문서를 LLM에 다시 입력
            corrected = llm.correct(triple, source_document)
            triple.object = corrected
    
    return refined_graph
```

**예시**:
```
정규화 전:
- "BYD Inc."
- "BYD Auto"
- "BYD Company"

정규화 후:
- "BYD" (표준 형태)

속성 보완 전:
- (삼성전자, HAS_MARKET_CAP, "No information found")

속성 보완 후:
- (삼성전자, HAS_MARKET_CAP, "500조원")
```

---

## GraphRAG 패턴

### GraphRAG란?

**GraphRAG (Graph-based Retrieval Augmented Generation)**는 지식 그래프를 활용한 검색 증강 생성 기법입니다.

#### 전통적인 RAG vs GraphRAG

**전통적인 RAG**:
```
사용자 질의 → 벡터 검색 → 관련 문서 청크 → LLM → 답변
```

**GraphRAG**:
```
사용자 질의 → 그래프 검색 → 관련 서브그래프 → LLM → 답변
```

**장점**:
- 구조화된 관계 정보 활용
- 다단계 관계 탐색 가능
- 의미적으로 일관된 컨텍스트 제공

### FinKario-RAG: 2단계 검색 전략

#### Step 1: Knowledge Graph Vectorization & Ingestion

**목적**: 그래프를 벡터로 변환하여 검색 가능하게 만들기

**3가지 수준의 임베딩**:

1. **Entity-level Embedding**: 각 엔티티를 벡터로 변환
   ```
   e_i = Φ(entity_i)
   ```

2. **Relation-level Embedding**: 각 관계를 벡터로 변환
   ```
   r_j = Φ(relation_j)
   ```

3. **Graph-level Embedding**: 전체 그래프를 하나의 벡터로 변환
   ```
   g_global = ρ(G_FinKario)
   ```

**통합 표현**:
```
Z_FinKario = Z_local ∪ {g_global}
Z_local = {e_i}_{i=1}^{|E|} ∪ {r_j}_{j=1}^{|R|}
```

**벡터 DB 저장**:
```python
# 벡터화 및 저장
vector_store = VectorDB()

for entity in graph.entities:
    embedding = graph_encoder.encode(entity)
    vector_store.index(entity, embedding)

for relation in graph.relations:
    embedding = graph_encoder.encode(relation)
    vector_store.index(relation, embedding)

global_embedding = readout_function(graph)
vector_store.index("global", global_embedding)
```

#### Step 2: Two-stage Retrieval (2단계 검색)

**Coarse-grained Retrieval (거친 검색)**:

**목적**: 거시적인 의미 앵커 식별

**과정**:
```python
# 사용자 질의를 벡터로 변환
h_q = language_model.encode(query)

# 주식과 날짜 등 거친 후보 검색
V_coarse = retrieve_top_k(
    query_vector=h_q,
    vector_store=vector_store,
    k=kc,  # 예: 상위 10개
    filter_types=["Stock", "Date"]
)

# 결과: ["BYD", "Sep 1st 2024"]
```

**Fine-grained Retrieval (세밀한 검색)**:

**목적**: 관련 엔티티의 세부 정보 수집

**과정**:
```python
# 거친 결과를 기반으로 세부 검색
V_fine = retrieve_top_k(
    query_vector=h_q,
    candidate_vectors=V_coarse,
    k=kf,  # 예: 상위 50개
    filter_types=["Industry", "MarketCap", "Price", "Event"]
)

# 벡터를 원래 그래프 컨텍스트로 매핑
G_sub = map_vectors_to_graph(V_fine, G_FinKario)
```

**서브그래프 재구성**:
```python
def map_vectors_to_graph(vectors, original_graph):
    subgraph = Graph()
    
    for vector in vectors:
        # 벡터에서 원본 노드/엣지 찾기
        node = lookup_node(vector, original_graph)
        subgraph.add_node(node)
        
        # 관련 엣지도 추가
        for edge in original_graph.get_edges(node):
            subgraph.add_edge(edge)
    
    return subgraph
```

**예시**:
```
사용자 질의: "BYD의 다음 주 주가 예측"

Coarse-grained 결과:
- Stock: BYD
- Date: Sep 1st 2024

Fine-grained 결과:
- Industry: Electric Vehicles
- MarketCap: 8000억 위안
- Price: 293.19-290.31 위안
- Event: Overseas expansion (Strategic Action)
- Competitors: Seres, Changan

재구성된 서브그래프:
(BYD) --[HAS_INDUSTRY]--> (Electric Vehicles)
(BYD) --[HAS_METRIC]--> (MarketCap: 8000억)
(BYD) --[TRIGGERED_BY]--> (Overseas_expansion_event)
(BYD) --[COMPETES_WITH]--> (Seres)
(BYD) --[COMPETES_WITH]--> (Changan)
```

#### Step 3: Investment Guidance (투자 가이드 생성)

**최종 답변 생성**:
```python
def generate_investment_guidance(query, subgraph, llm):
    prompt = f"""
    다음 정보를 바탕으로 투자 가이드를 생성하세요.
    
    질의: {query}
    관련 정보:
    {format_subgraph(subgraph)}
    
    다음 형식으로 답변하세요:
    - 예측: 상승/하락
    - 신뢰도: 1-10
    - 이유:
      1. 재무 지표: ...
      2. 주요 제품 및 산업: ...
      3. 이벤트: ...
    """
    
    response = llm.generate(prompt)
    return parse_response(response)
```

**출력 예시**:
```
예측: 상승
신뢰도: 8

이유:
1. 재무 지표: BYD의 현재 주가는 293.19-290.31 위안이며, 
   목표가가 438 위안으로 설정되어 있습니다.
   
2. 주요 제품 및 산업: BYD는 전기차 제조업에 종사하며, 
   주요 경쟁사는 Seres와 Changan입니다. 
   이들 대비 수익성과 현금 흐름이 우수합니다.
   
3. 이벤트: BYD의 해외 시장 투자 증가는 
   이익 증가를 기대할 수 있습니다 (전략적 행동).
```

### Microsoft GraphRAG 패턴

#### 글로벌 커뮤니티 요약 (Global Community Summary)

**목적**: 대규모 그래프 구조의 상위 수준 이해

**과정**:
1. 그래프를 커뮤니티로 분할
2. 각 커뮤니티를 요약
3. 커뮤니티 간 관계 요약

**예시**:
```
커뮤니티 1: Memory 반도체 기업들
  - 삼성전자, SK하이닉스, 마이크론
  - 관계: 경쟁, 공급망, 기술 공유
  요약: "한국과 미국의 주요 메모리 반도체 기업들이 
        HBM 시장에서 경쟁하고 있으며, 
        삼성전자와 SK하이닉스가 시장을 주도하고 있습니다."

커뮤니티 2: Foundry 서비스 기업들
  - TSMC, 삼성전자, GlobalFoundries
  - 관계: 경쟁, 고객 공유
  요약: "파운드리 서비스 시장에서 TSMC가 선도하고 있으며,
        삼성전자가 추격하고 있습니다."
```

#### 로컬 세부 검색 (Local Detailed Search)

**목적**: 특정 엔티티나 관계에 대한 세부 정보 검색

**과정**:
1. 사용자 질의에서 엔티티 추출
2. 해당 엔티티와 직접 연결된 노드 검색
3. 관련 관계와 속성 반환

**예시**:
```
질의: "삼성전자의 HBM 관련 정보"

로컬 검색 결과:
- 삼성전자 --[MANUFACTURES]--> HBM3
- 삼성전자 --[HAS_METRIC]--> HBM_Revenue: 50조원
- 삼성전자 --[COMPETES_WITH]--> SK하이닉스 (HBM 시장)
- HBM3 --[USES_TECHNOLOGY]--> 10nm 공정
```

#### Cypher 템플릿 생성

**목적**: 자연어 질의를 Cypher 쿼리로 자동 변환

**프롬프트 예시**:
```python
CYPHER_GENERATION_PROMPT = """
다음 자연어 질의를 Neo4j Cypher 쿼리로 변환하세요.

질의: {user_query}

사용 가능한 노드 타입:
- Company, ProductLine, Metric, Event, Industry

사용 가능한 관계 타입:
- MANUFACTURES, HAS_METRIC, COMPETES_WITH, 
  TRIGGERED_BY, AFFECTS

Cypher 쿼리만 반환하세요.
"""
```

**예시**:
```
자연어: "HBM 관련 매출이 높은 상위 5개 한국 기업"

Cypher:
MATCH (c:Company)-[:MANUFACTURES]->(p:ProductLine)
WHERE p.name CONTAINS "HBM" 
  AND c.country = "Korea"
MATCH (c)-[:HAS_METRIC]->(m:Metric)
WHERE m.type = "Revenue" AND m.product = "HBM"
RETURN c.name, m.value
ORDER BY m.value DESC
LIMIT 5
```

---

## 동적 그래프 신경망

### MDGNN: Multi-Relational Dynamic Graph Neural Network

MDGNN 논문에서는 주식 투자 예측을 위해 다중 관계 동적 그래프 신경망을 제안했습니다.

#### 문제 정의

**기존 방법의 한계**:
1. **단일 관계만 사용**: 주식 간 단일 관계만 고려
2. **정적 그래프**: 시간에 따른 관계 변화 미고려

**MDGNN의 해결책**:
1. **다중 관계**: Industry, Investment Bank, Stock 간 다양한 관계
2. **동적 그래프**: 일일 스냅샷으로 시간적 진화 포착

#### 다중 관계 그래프 구성

**1. Industry Graph (산업 그래프)**

**목적**: 산업-주식 간 관계 모델링

**관계 타입**:
- Supply: 원자재 공급 관계
- Demand: 수요 관계
- Competition: 경쟁 관계
- Regulation: 규제 영향 관계

**구조**:
```
Stock (S) --[E_SI]--> Industry (I)
  - Features: supply, demand, competition, regulatory
```

**예시**:
```
(삼성전자) --[BELONGS_TO]--> (Semiconductor Industry)
  - Features: 
    - supply: "원자재 공급 안정"
    - demand: "HBM 수요 급증"
    - competition: "SK하이닉스와 경쟁"
    - regulatory: "미국 수출 규제 영향"
```

**2. Investment Bank Graph (투자은행 그래프)**

**목적**: 투자은행-주식 간 영향 모델링

**관계 타입**:
- Buy: 매수 관계
- Sell: 매도 관계
- Research: 리서치 리포트 작성
- Advisory: 자문 관계

**구조**:
```
Stock (S) --[E_SB]--> Investment Bank (B)
  - Features: buy_volume, sell_volume, 
              research_rating, advisory_type
```

**예시**:
```
(삼성전자) --[RESEARCHED_BY]--> (미래에셋증권)
  - Features:
    - research_rating: "Buy"
    - target_price: "100,000원"
    - date: "2024-10-25"

(삼성전자) --[BOUGHT_BY]--> (KB증권)
  - Features:
    - volume: "1,000,000주"
    - date: "2024-10-20"
```

**3. Stock Graph (주식 그래프)**

**목적**: 주식 간 직접 관계 모델링

**관계 타입**:
- Sector: 같은 섹터
- Ownership: 공동 소유
- Co-holding: 공동 보유

**구조**:
```
Stock (S1) --[E_SS]--> Stock (S2)
  - Features: sector_similarity, 
              ownership_overlap,
              co_holding_ratio
```

**예시**:
```
(삼성전자) --[SAME_SECTOR]--> (SK하이닉스)
  - Features:
    - sector_similarity: 0.95
    - competition_level: "High"

(삼성전자) --[CO_HELD_BY]--> (SK하이닉스)
  - Features:
    - common_shareholders: ["국민연금", "한국투자공사"]
    - co_holding_ratio: 0.15
```

#### 계층적 다중 관계 그래프 임베딩

**Meta-path 정의**:
```
Meta-path 1: Stock → Stock (S-S)
Meta-path 2: Stock → Bank → Stock (S-B-S)
Meta-path 3: Stock → Industry → Industry → Stock (S-I-I-S)
```

**임베딩 과정**:

**Step 1: Others → Stock (다른 엔티티에서 주식으로)**

```python
# Industry → Stock
h_i1 = aggregate(
    neighbors=industry_nodes,
    relation="BELONGS_TO",
    attention_weights=α_industry
)

# Bank → Stock
h_i2 = aggregate(
    neighbors=bank_nodes,
    relation="RESEARCHED_BY",
    attention_weights=α_bank
)
```

**Step 2: Stock → Others (주식에서 다른 엔티티로)**

```python
# Stock → Stock
h_i3 = aggregate(
    neighbors=stock_nodes,
    relation="SAME_SECTOR",
    attention_weights=α_stock
)
```

**Step 3: Meta-path Aggregation (메타 경로 집계)**

```python
# Attention으로 메타 경로 가중치 학습
α_meta = softmax([
    attention(h_i1, query),
    attention(h_i2, query),
    attention(h_i3, query)
])

# 가중 평균으로 최종 임베딩
h_final = α_meta[0] * h_i1 + α_meta[1] * h_i2 + α_meta[2] * h_i3
```

#### 시간적 진화 인코딩

**Transformer 구조 활용**:

```python
# 일일 그래프 스냅샷 시퀀스
H_v,t-δt:t = {h_vt' | t - δt ≤ t' ≤ t}

# Query, Key, Value 생성
Q = W_Q * H_v,t-δt:t
K = W_K * H_v,t-δt:t
V = W_V * H_v,t-δt:t

# ALIBI 위치 인코딩 (최근 이벤트에 더 큰 가중치)
Z = softmax((Q * K^T) / √d + m * P + M) * V

# P: ALIBI 위치 바이어스
# M: Forward mask (미래 정보 차단)
```

**ALIBI 위치 인코딩**:
- 최근 이벤트에 더 큰 가중치 부여
- 거리가 멀수록 패널티 증가
- 시간적 의존성 모델링

---

## 실전 구현 가이드

### Neo4j를 사용한 지식 그래프 구축

#### 1. 스키마 정의

```cypher
// 노드 타입 및 제약 조건
CREATE CONSTRAINT company_name IF NOT EXISTS
FOR (c:Company) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT product_name IF NOT EXISTS
FOR (p:ProductLine) REQUIRE p.name IS UNIQUE;

// 인덱스 생성
CREATE INDEX company_industry IF NOT EXISTS
FOR (c:Company) ON (c.industry);

CREATE INDEX event_date IF NOT EXISTS
FOR (e:Event) ON (e.date);
```

#### 2. 데이터 삽입

```cypher
// Company 노드 생성
CREATE (samsung:Company {
    name: "삼성전자",
    industry: "Semiconductor",
    exchange: "KOSPI",
    marketCap: 500000000000000
})

// ProductLine 노드 생성
CREATE (hbm3:ProductLine {
    name: "HBM3",
    category: "Memory",
    technology: "10nm"
})

// 관계 생성
CREATE (samsung)-[:MANUFACTURES {
    since: "2022",
    marketShare: 0.5
}]->(hbm3)

// Metric 노드 및 관계
CREATE (revenue:Metric {
    type: "Revenue",
    value: 300000000000000,
    period: "2024Q3",
    unit: "원"
})

CREATE (samsung)-[:HAS_METRIC {
    date: "2024-10-25"
}]->(revenue)
```

#### 3. 쿼리 예시

```cypher
// HBM을 제조하는 기업 찾기
MATCH (c:Company)-[:MANUFACTURES]->(p:ProductLine)
WHERE p.name CONTAINS "HBM"
RETURN c.name, p.name

// 경쟁 관계 탐색
MATCH (c1:Company)-[:COMPETES_WITH]-(c2:Company)
WHERE c1.industry = "Semiconductor"
RETURN c1.name, c2.name

// 이벤트 영향 추적
MATCH (e:Event)-[:AFFECTS]->(m:Metric)<-[:HAS_METRIC]-(c:Company)
WHERE e.type = "Earnings"
RETURN c.name, e.date, m.value
ORDER BY e.date DESC
LIMIT 10
```

### Python 구현 예시

#### GraphRAG 검색 구현

```python
from langchain_neo4j import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.chains import GraphCypherQAChain

# Neo4j 연결
graph = Neo4jGraph(
    url="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# LLM 설정
llm = ChatOpenAI(temperature=0)

# GraphRAG 체인 생성
chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True
)

# 질의 실행
query = "HBM 관련 매출이 높은 상위 5개 한국 기업은?"
result = chain.run(query)
print(result)
```

#### 동적 그래프 업데이트

```python
def update_dynamic_graph(neo4j_client, event_data):
    """
    새로운 이벤트를 그래프에 추가
    """
    # 이벤트 노드 생성
    event_query = """
    CREATE (e:Event {
        type: $event_type,
        date: $date,
        description: $description
    })
    WITH e
    MATCH (c:Company {name: $company_name})
    CREATE (c)-[:TRIGGERED_BY]->(e)
    WITH e, c
    MATCH (c)-[:HAS_METRIC]->(m:Metric {period: $period})
    CREATE (e)-[:AFFECTS]->(m)
    RETURN e, c, m
    """
    
    result = neo4j_client.run(
        event_query,
        event_type=event_data['type'],
        date=event_data['date'],
        description=event_data['description'],
        company_name=event_data['company'],
        period=event_data['period']
    )
    
    return result
```

---

## 요약

### 핵심 포인트

1. **지식 그래프는 관계 중심 데이터 구조**: 노드와 엣지로 복잡한 관계 표현
2. **이중 서브그래프 설계**: 정적(Attribute) + 동적(Event) 정보 분리
3. **GraphRAG 패턴**: 그래프 기반 검색으로 구조화된 컨텍스트 제공
4. **동적 그래프**: 시간에 따른 관계 변화를 스냅샷으로 포착
5. **다중 관계 모델링**: Industry, Bank, Stock 간 다양한 관계 고려

### 다음 단계

- [이전 문서: 온톨로지](01_온톨로지_Ontology.md)
- [다음 문서: 멀티에이전트 시스템](03_멀티에이전트_Multi_Agent.md)

---

**참고 논문**:
- FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph
- MDGNN: Multi-Relational Dynamic Graph Neural Network for Comprehensive and Dynamic Stock Investment Prediction
- Knowledge graphs as tools for explainable machine learning: A survey

