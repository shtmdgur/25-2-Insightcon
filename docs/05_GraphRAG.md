# GraphRAG 완전 정리 가이드

## 📖 목차
1. [GraphRAG란 무엇인가?](#graphrag란-무엇인가)
2. [전통적인 RAG vs GraphRAG](#전통적인-rag-vs-graphrag)
3. [FinKario-RAG 구현](#finkario-rag-구현)
4. [Microsoft GraphRAG 패턴](#microsoft-graphrag-패턴)
5. [Cypher 쿼리 생성](#cypher-쿼리-생성)
6. [실전 구현 가이드](#실전-구현-가이드)

---

## GraphRAG란 무엇인가?

### 기본 개념

**GraphRAG (Graph-based Retrieval Augmented Generation)**는 지식 그래프를 활용한 검색 증강 생성 기법입니다.

#### RAG의 한계

**전통적인 RAG**:
```
사용자 질의 → 벡터 검색 → 문서 청크 → LLM → 답변
```

**문제점**:
1. **의미적 일관성 부족**: 관련 없는 문서 청크가 섞일 수 있음
2. **관계 정보 손실**: 문서 간 관계 정보가 없음
3. **다단계 추론 어려움**: 복잡한 관계 탐색 불가
4. **컨텍스트 품질**: 단순 텍스트만 제공

#### GraphRAG의 해결책

**GraphRAG**:
```
사용자 질의 → 그래프 검색 → 관련 서브그래프 → LLM → 답변
```

**장점**:
1. **구조화된 컨텍스트**: 노드와 관계로 명확한 구조 제공
2. **관계 정보 보존**: 엔티티 간 관계 유지
3. **다단계 추론**: 그래프 탐색으로 복잡한 관계 파악
4. **의미적 일관성**: 관련 엔티티만 선택적으로 검색

### GraphRAG의 구성 요소

```
┌─────────────────────────────────────────┐
│         GraphRAG 시스템                 │
├─────────────────────────────────────────┤
│                                         │
│  1. Knowledge Graph (지식 그래프)      │
│     - 노드: 엔티티                      │
│     - 엣지: 관계                        │
│     - 속성: 메타데이터                  │
│                                         │
│  2. Graph Embedding (그래프 임베딩)    │
│     - Entity Embedding                  │
│     - Relation Embedding                │
│     - Graph-level Embedding             │
│                                         │
│  3. Retrieval (검색)                   │
│     - Coarse-grained (거친 검색)       │
│     - Fine-grained (세밀한 검색)       │
│                                         │
│  4. Subgraph Construction (서브그래프) │
│     - 관련 노드 선택                    │
│     - 관계 경로 추적                    │
│                                         │
│  5. LLM Generation (생성)              │
│     - 서브그래프 → 텍스트 변환          │
│     - 답변 생성                         │
│                                         │
└─────────────────────────────────────────┘
```

---

## 전통적인 RAG vs GraphRAG

### 비교 예시

#### 시나리오: "HBM 관련 매출이 높은 한국 기업 찾기"

**전통적인 RAG**:
```
1. 질의 벡터화
   query_vector = embed("HBM 관련 매출이 높은 한국 기업")

2. 문서 청크 벡터 검색
   - "삼성전자는 HBM을 제조합니다..."
   - "SK하이닉스의 메모리 사업..."
   - "한국 반도체 산업 동향..."

3. LLM에 전달
   "다음 문서들을 참고하여 답변하세요:
    [문서 1] [문서 2] [문서 3]"

4. 문제점
   - 문서 간 관계 불명확
   - HBM과 매출의 연결이 모호
   - 한국 기업 필터링 어려움
```

**GraphRAG**:
```
1. 그래프에서 관련 노드 검색
   - HBM (ProductLine)
   - 삼성전자 (Company, country="Korea")
   - SK하이닉스 (Company, country="Korea")
   - Revenue (Metric)

2. 관계 경로 추적
   (삼성전자) -[MANUFACTURES]-> (HBM)
   (삼성전자) -[HAS_METRIC]-> (Revenue: 50조원, product="HBM")
   (SK하이닉스) -[MANUFACTURES]-> (HBM)
   (SK하이닉스) -[HAS_METRIC]-> (Revenue: 30조원, product="HBM")

3. 서브그래프 구성
   G_sub = {
       nodes: [삼성전자, SK하이닉스, HBM, Revenue_삼성, Revenue_SK],
       edges: [MANUFACTURES, HAS_METRIC]
   }

4. 구조화된 컨텍스트 생성
   "다음 그래프 구조를 참고하여 답변하세요:
    Company: 삼성전자
      - Country: Korea
      - MANUFACTURES: HBM
      - HAS_METRIC: Revenue (50조원, product=HBM)
    
    Company: SK하이닉스
      - Country: Korea
      - MANUFACTURES: HBM
      - HAS_METRIC: Revenue (30조원, product=HBM)"

5. 장점
   - 명확한 관계 구조
   - 정확한 필터링 (한국 기업만)
   - 매출과 HBM의 직접 연결
```

---

## FinKario-RAG 구현

### 1단계: Knowledge Graph Vectorization & Ingestion

#### 목적

그래프를 벡터로 변환하여 검색 가능하게 만들기

#### 3가지 수준의 임베딩

**1. Entity-level Embedding (엔티티 수준 임베딩)**

각 엔티티를 벡터로 변환:

```python
from langchain_community.embeddings import OpenAIEmbeddings

class GraphEmbedder:
    def __init__(self, embedding_model):
        self.embedder = embedding_model
    
    def embed_entity(self, entity):
        """엔티티를 벡터로 변환"""
        
        # 엔티티 정보를 텍스트로 변환
        entity_text = f"""
        Entity: {entity['name']}
        Type: {entity['type']}
        Properties: {entity.get('properties', {})}
        """
        
        # 임베딩 생성
        embedding = self.embedder.embed_query(entity_text)
        
        return {
            'entity_id': entity['id'],
            'embedding': embedding,
            'metadata': entity
        }
```

**2. Relation-level Embedding (관계 수준 임베딩)**

각 관계를 벡터로 변환:

```python
def embed_relation(self, relation):
    """관계를 벡터로 변환"""
    
    relation_text = f"""
    Relation: {relation['type']}
    From: {relation['from_entity']}
    To: {relation['to_entity']}
    Properties: {relation.get('properties', {})}
    """
    
    embedding = self.embedder.embed_query(relation_text)
    
    return {
        'relation_id': relation['id'],
        'embedding': embedding,
        'metadata': relation
    }
```

**3. Graph-level Embedding (그래프 수준 임베딩)**

전체 그래프를 하나의 벡터로 변환:

```python
def embed_graph(self, graph):
    """전체 그래프를 벡터로 변환"""
    
    # 그래프 요약 생성
    graph_summary = self._generate_graph_summary(graph)
    
    # 임베딩 생성
    embedding = self.embedder.embed_query(graph_summary)
    
    return {
        'graph_id': graph['id'],
        'embedding': embedding,
        'summary': graph_summary
    }

def _generate_graph_summary(self, graph):
    """그래프 요약 생성"""
    
    # 노드 타입별 집계
    node_types = {}
    for node in graph['nodes']:
        node_type = node['type']
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    # 관계 타입별 집계
    relation_types = {}
    for edge in graph['edges']:
        rel_type = edge['type']
        relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
    
    summary = f"""
    Graph Summary:
    - Total Nodes: {len(graph['nodes'])}
    - Node Types: {node_types}
    - Total Edges: {len(graph['edges'])}
    - Relation Types: {relation_types}
    """
    
    return summary
```

#### 벡터 DB 저장

```python
from langchain_community.vectorstores import Chroma

class GraphVectorStore:
    def __init__(self, embedding_model, persist_directory):
        self.embedder = GraphEmbedder(embedding_model)
        self.vectorstore = Chroma(
            embedding_function=embedding_model,
            persist_directory=persist_directory
        )
    
    def index_graph(self, graph):
        """그래프를 벡터 DB에 인덱싱"""
        
        # 엔티티 임베딩 및 저장
        for entity in graph['nodes']:
            entity_embedding = self.embedder.embed_entity(entity)
            
            self.vectorstore.add_texts(
                texts=[f"Entity: {entity['name']}"],
                embeddings=[entity_embedding['embedding']],
                metadatas=[{
                    'type': 'entity',
                    'entity_id': entity['id'],
                    'entity_type': entity['type'],
                    **entity.get('properties', {})
                }]
            )
        
        # 관계 임베딩 및 저장
        for relation in graph['edges']:
            relation_embedding = self.embedder.embed_relation(relation)
            
            self.vectorstore.add_texts(
                texts=[f"Relation: {relation['type']}"],
                embeddings=[relation_embedding['embedding']],
                metadatas=[{
                    'type': 'relation',
                    'relation_id': relation['id'],
                    'relation_type': relation['type'],
                    'from_entity': relation['from_entity'],
                    'to_entity': relation['to_entity']
                }]
            )
        
        # 그래프 수준 임베딩
        graph_embedding = self.embedder.embed_graph(graph)
        
        self.vectorstore.add_texts(
            texts=[graph_embedding['summary']],
            embeddings=[graph_embedding['embedding']],
            metadatas=[{
                'type': 'graph',
                'graph_id': graph['id']
            }]
        )
```

### 2단계: Two-stage Retrieval (2단계 검색)

#### Coarse-grained Retrieval (거친 검색)

**목적**: 거시적인 의미 앵커 식별

**과정**:
1. 사용자 질의를 벡터로 변환
2. 주식, 날짜 등 거친 후보 검색
3. 상위 k개 후보 반환

```python
def coarse_grained_retrieval(self, query, k=10):
    """거친 검색 수행"""
    
    # 질의 벡터화
    query_embedding = self.embedder.embed_query(query)
    
    # 벡터 검색 (주식, 날짜 등만 필터링)
    results = self.vectorstore.similarity_search_with_score(
        query_embedding,
        k=k,
        filter={
            'type': {'$in': ['entity']},
            'entity_type': {'$in': ['Stock', 'Date', 'Company']}
        }
    )
    
    # 후보 추출
    candidates = []
    for doc, score in results:
        metadata = doc.metadata
        candidates.append({
            'entity_id': metadata['entity_id'],
            'entity_name': metadata.get('name', ''),
            'entity_type': metadata['entity_type'],
            'score': score
        })
    
    return candidates
```

**예시**:
```
질의: "BYD의 다음 주 주가 예측"

Coarse-grained 결과:
[
    {'entity_name': 'BYD', 'entity_type': 'Company', 'score': 0.95},
    {'entity_name': 'Sep 1st 2024', 'entity_type': 'Date', 'score': 0.87}
]
```

#### Fine-grained Retrieval (세밀한 검색)

**목적**: 관련 엔티티의 세부 정보 수집

**과정**:
1. 거친 결과를 기반으로 주변 엔티티 검색
2. 관련 관계 추적
3. 상위 k개 세부 엔티티 반환

```python
def fine_grained_retrieval(self, query, coarse_candidates, k=50):
    """세밀한 검색 수행"""
    
    # 질의 벡터화
    query_embedding = self.embedder.embed_query(query)
    
    # 거친 후보와 관련된 엔티티 검색
    candidate_ids = [c['entity_id'] for c in coarse_candidates]
    
    # 관련 엔티티 찾기 (그래프에서)
    related_entities = self._find_related_entities(candidate_ids)
    
    # 관련 엔티티 중에서 질의와 유사한 것 선택
    fine_candidates = []
    for entity in related_entities:
        entity_embedding = self.embedder.embed_entity(entity)['embedding']
        
        # 코사인 유사도 계산
        similarity = cosine_similarity(
            [query_embedding],
            [entity_embedding]
        )[0][0]
        
        fine_candidates.append({
            'entity': entity,
            'similarity': similarity
        })
    
    # 상위 k개 선택
    fine_candidates.sort(key=lambda x: x['similarity'], reverse=True)
    return fine_candidates[:k]

def _find_related_entities(self, entity_ids, max_hops=2):
    """그래프에서 관련 엔티티 찾기"""
    
    related = set()
    
    for entity_id in entity_ids:
        # 직접 연결된 엔티티
        neighbors = self.graph.get_neighbors(entity_id)
        related.update(neighbors)
        
        # 2-hop 이웃
        if max_hops >= 2:
            for neighbor in neighbors:
                second_neighbors = self.graph.get_neighbors(neighbor)
                related.update(second_neighbors)
    
    return [self.graph.get_entity(eid) for eid in related]
```

**예시**:
```
Fine-grained 결과:
[
    {'entity': Industry(Electric Vehicles), 'similarity': 0.92},
    {'entity': Metric(MarketCap: 8000억), 'similarity': 0.89},
    {'entity': Metric(Price: 293.19-290.31), 'similarity': 0.87},
    {'entity': Event(Overseas expansion), 'similarity': 0.85},
    {'entity': Company(Seres), 'similarity': 0.82},  # 경쟁사
    {'entity': Company(Changan), 'similarity': 0.80}  # 경쟁사
]
```

### 3단계: Subgraph Construction (서브그래프 구성)

**목적**: 검색된 엔티티로 의미적으로 일관된 서브그래프 구성

```python
def construct_subgraph(self, fine_candidates, original_graph):
    """서브그래프 구성"""
    
    subgraph = {
        'nodes': [],
        'edges': []
    }
    
    # 노드 추가
    entity_ids = set()
    for candidate in fine_candidates:
        entity = candidate['entity']
        entity_ids.add(entity['id'])
        subgraph['nodes'].append(entity)
    
    # 관련 엣지 추가
    for edge in original_graph['edges']:
        if (edge['from_entity'] in entity_ids and 
            edge['to_entity'] in entity_ids):
            subgraph['edges'].append(edge)
    
    return subgraph
```

**예시 서브그래프**:
```
Subgraph:
  Nodes:
    - BYD (Company)
    - Electric Vehicles (Industry)
    - MarketCap: 8000억 (Metric)
    - Price: 293.19-290.31 (Metric)
    - Overseas expansion (Event)
    - Seres (Company)
    - Changan (Company)
  
  Edges:
    - (BYD) -[HAS_INDUSTRY]-> (Electric Vehicles)
    - (BYD) -[HAS_METRIC]-> (MarketCap: 8000억)
    - (BYD) -[HAS_METRIC]-> (Price: 293.19-290.31)
    - (BYD) -[TRIGGERED_BY]-> (Overseas expansion)
    - (BYD) -[COMPETES_WITH]-> (Seres)
    - (BYD) -[COMPETES_WITH]-> (Changan)
```

### 4단계: Investment Guidance (투자 가이드 생성)

**목적**: 서브그래프를 기반으로 투자 가이드 생성

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class InvestmentGuidanceGenerator:
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문 투자 분석가입니다.
            주어진 그래프 정보를 바탕으로 투자 가이드를 생성하세요."""),
            ("human", """질의: {query}
            
            관련 정보:
            {subgraph_info}
            
            다음 형식으로 답변하세요:
            - 예측: 상승/하락/중립
            - 신뢰도: 1-10
            - 이유:
              1. 재무 지표: ...
              2. 주요 제품 및 산업: ...
              3. 이벤트: ...
            """)
        ])
    
    def generate(self, query, subgraph):
        """투자 가이드 생성"""
        
        # 서브그래프를 텍스트로 변환
        subgraph_text = self._format_subgraph(subgraph)
        
        # 프롬프트 생성
        prompt = self.prompt_template.format_messages(
            query=query,
            subgraph_info=subgraph_text
        )
        
        # LLM 호출
        response = self.llm.invoke(prompt)
        
        return response.content
    
    def _format_subgraph(self, subgraph):
        """서브그래프를 읽기 쉬운 텍스트로 변환"""
        
        text = "Graph Structure:\n\n"
        
        # 노드 정보
        text += "Entities:\n"
        for node in subgraph['nodes']:
            text += f"- {node['type']}: {node['name']}\n"
            if 'properties' in node:
                for key, value in node['properties'].items():
                    text += f"  {key}: {value}\n"
        
        # 엣지 정보
        text += "\nRelationships:\n"
        for edge in subgraph['edges']:
            text += f"- {edge['from_entity']} --[{edge['type']}]--> {edge['to_entity']}\n"
        
        return text
```

**출력 예시**:
```
예측: 상승
신뢰도: 8

이유:
1. 재무 지표: BYD의 현재 주가는 293.19-290.31 위안이며, 
   목표가가 438 위안으로 설정되어 있습니다. 
   시가총액은 8000억 위안입니다.
   
2. 주요 제품 및 산업: BYD는 전기차 제조업에 종사하며, 
   주요 경쟁사는 Seres와 Changan입니다. 
   이들 대비 수익성과 현금 흐름이 우수합니다.
   
3. 이벤트: BYD의 해외 시장 투자 증가는 
   이익 증가를 기대할 수 있습니다 (전략적 행동).
```

---

## Microsoft GraphRAG 패턴

### 글로벌 커뮤니티 요약 (Global Community Summary)

**목적**: 대규모 그래프 구조의 상위 수준 이해

#### 커뮤니티 탐지

```python
import networkx as nx
from community import community_louvain

def detect_communities(graph):
    """그래프를 커뮤니티로 분할"""
    
    # NetworkX 그래프 생성
    G = nx.Graph()
    for edge in graph['edges']:
        G.add_edge(edge['from_entity'], edge['to_entity'])
    
    # Louvain 알고리즘으로 커뮤니티 탐지
    communities = community_louvain.best_partition(G)
    
    # 커뮤니티별 노드 그룹화
    community_dict = {}
    for node, comm_id in communities.items():
        if comm_id not in community_dict:
            community_dict[comm_id] = []
        community_dict[comm_id].append(node)
    
    return community_dict
```

#### 커뮤니티 요약 생성

```python
def summarize_community(community_nodes, graph, llm):
    """커뮤니티를 요약"""
    
    # 커뮤니티 내 노드 정보 수집
    node_info = []
    for node_id in community_nodes:
        node = graph.get_node(node_id)
        node_info.append(f"{node['type']}: {node['name']}")
    
    # 커뮤니티 내 관계 정보
    relations = []
    for edge in graph['edges']:
        if (edge['from_entity'] in community_nodes and 
            edge['to_entity'] in community_nodes):
            relations.append(
                f"{edge['from_entity']} --[{edge['type']}]--> {edge['to_entity']}"
            )
    
    # LLM으로 요약 생성
    prompt = f"""
    다음 커뮤니티를 요약하세요:
    
    노드:
    {chr(10).join(node_info)}
    
    관계:
    {chr(10).join(relations)}
    
    이 커뮤니티의 주요 특징과 의미를 설명하세요.
    """
    
    summary = llm.invoke(prompt)
    return summary.content
```

**예시**:
```
커뮤니티 1: Memory 반도체 기업들
  노드: 삼성전자, SK하이닉스, 마이크론, HBM, DRAM, NAND
  관계: MANUFACTURES, COMPETES_WITH, SUPPLIES
  
  요약:
  "한국과 미국의 주요 메모리 반도체 기업들이 
   HBM 시장에서 경쟁하고 있으며, 
   삼성전자와 SK하이닉스가 시장을 주도하고 있습니다. 
   이들 기업은 DRAM과 NAND 플래시 메모리를 제조하며, 
   서로 경쟁 관계에 있습니다."
```

### 로컬 세부 검색 (Local Detailed Search)

**목적**: 특정 엔티티와 직접 연결된 노드 검색

```python
def local_detailed_search(entity_name, graph, max_depth=1):
    """로컬 세부 검색"""
    
    # 엔티티 찾기
    entity = graph.find_entity_by_name(entity_name)
    if not entity:
        return None
    
    # 직접 연결된 노드 검색
    local_subgraph = {
        'center': entity,
        'neighbors': [],
        'edges': []
    }
    
    # 1-hop 이웃
    for edge in graph['edges']:
        if edge['from_entity'] == entity['id']:
            neighbor = graph.get_node(edge['to_entity'])
            local_subgraph['neighbors'].append(neighbor)
            local_subgraph['edges'].append(edge)
        elif edge['to_entity'] == entity['id']:
            neighbor = graph.get_node(edge['from_entity'])
            local_subgraph['neighbors'].append(neighbor)
            local_subgraph['edges'].append(edge)
    
    # 2-hop 이웃 (선택적)
    if max_depth >= 2:
        second_neighbors = []
        for neighbor in local_subgraph['neighbors']:
            for edge in graph['edges']:
                if (edge['from_entity'] == neighbor['id'] or 
                    edge['to_entity'] == neighbor['id']):
                    if edge['from_entity'] != entity['id'] and \
                       edge['to_entity'] != entity['id']:
                        second_neighbor_id = (
                            edge['to_entity'] 
                            if edge['from_entity'] == neighbor['id']
                            else edge['from_entity']
                        )
                        second_neighbor = graph.get_node(second_neighbor_id)
                        if second_neighbor not in second_neighbors:
                            second_neighbors.append(second_neighbor)
        
        local_subgraph['second_neighbors'] = second_neighbors
    
    return local_subgraph
```

**예시**:
```
질의: "삼성전자의 HBM 관련 정보"

로컬 검색 결과:
  Center: 삼성전자 (Company)
  
  Neighbors:
    - HBM3 (ProductLine)
    - HBM Revenue: 50조원 (Metric)
    - SK하이닉스 (Company) - 경쟁 관계
    - Semiconductor Industry
  
  Edges:
    - (삼성전자) -[MANUFACTURES]-> (HBM3)
    - (삼성전자) -[HAS_METRIC]-> (HBM Revenue: 50조원)
    - (삼성전자) -[COMPETES_WITH]-> (SK하이닉스)
    - (삼성전자) -[BELONGS_TO]-> (Semiconductor Industry)
```

---

## Cypher 쿼리 생성

### 자연어 → Cypher 변환

**목적**: 사용자 질의를 Neo4j Cypher 쿼리로 자동 변환

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class CypherQueryGenerator:
    def __init__(self, llm, graph_schema):
        self.llm = llm
        self.graph_schema = graph_schema
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """당신은 Neo4j Cypher 쿼리 전문가입니다.
            자연어 질의를 정확한 Cypher 쿼리로 변환하세요."""),
            ("human", """다음 자연어 질의를 Cypher 쿼리로 변환하세요.

질의: {query}

사용 가능한 노드 타입:
{node_types}

사용 가능한 관계 타입:
{relation_types}

Cypher 쿼리만 반환하세요. 설명은 필요 없습니다.""")
        ])
    
    def generate(self, query):
        """Cypher 쿼리 생성"""
        
        prompt = self.prompt_template.format_messages(
            query=query,
            node_types=self._format_node_types(),
            relation_types=self._format_relation_types()
        )
        
        response = self.llm.invoke(prompt)
        cypher_query = response.content.strip()
        
        # Cypher 쿼리 검증
        if not cypher_query.startswith('MATCH'):
            # MATCH가 없으면 추가
            cypher_query = f"MATCH {cypher_query}"
        
        return cypher_query
    
    def _format_node_types(self):
        """노드 타입 포맷팅"""
        return "\n".join([
            f"- {nt['name']}: {nt['description']}"
            for nt in self.graph_schema['node_types']
        ])
    
    def _format_relation_types(self):
        """관계 타입 포맷팅"""
        return "\n".join([
            f"- {rt['name']}: {rt['from']} → {rt['to']}"
            for rt in self.graph_schema['relation_types']
        ])
```

**예시**:
```
자연어: "HBM 관련 매출이 높은 상위 5개 한국 기업"

생성된 Cypher:
MATCH (c:Company)-[:MANUFACTURES]->(p:ProductLine)
WHERE p.name CONTAINS "HBM" 
  AND c.country = "Korea"
MATCH (c)-[:HAS_METRIC]->(m:Metric)
WHERE m.type = "Revenue" AND m.product = "HBM"
RETURN c.name, m.value
ORDER BY m.value DESC
LIMIT 5
```

### 쿼리 실행 및 결과 처리

```python
from langchain_neo4j import Neo4jGraph

class GraphQueryExecutor:
    def __init__(self, neo4j_uri, username, password):
        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=username,
            password=password
        )
    
    def execute(self, cypher_query):
        """Cypher 쿼리 실행"""
        try:
            result = self.graph.query(cypher_query)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def execute_natural_language(self, query, cypher_generator):
        """자연어 질의 실행"""
        # Cypher 쿼리 생성
        cypher = cypher_generator.generate(query)
        
        # 쿼리 실행
        result = self.execute(cypher)
        
        return {
            'cypher_query': cypher,
            'result': result
        }
```

---

## 실전 구현 가이드

### 완전한 GraphRAG 파이프라인

```python
class CompleteGraphRAG:
    def __init__(self, 
                 neo4j_graph,
                 embedding_model,
                 llm,
                 vectorstore):
        self.neo4j_graph = neo4j_graph
        self.embedder = GraphEmbedder(embedding_model)
        self.llm = llm
        self.vectorstore = vectorstore
        self.cypher_generator = CypherQueryGenerator(
            llm, 
            self._load_schema()
        )
        self.guidance_generator = InvestmentGuidanceGenerator(llm)
    
    def query(self, user_query, use_cypher=True):
        """GraphRAG 쿼리 실행"""
        
        if use_cypher:
            # Cypher 기반 검색
            result = self._cypher_based_search(user_query)
        else:
            # 벡터 기반 검색
            result = self._vector_based_search(user_query)
        
        # 서브그래프 구성
        subgraph = self._construct_subgraph(result)
        
        # 투자 가이드 생성
        guidance = self.guidance_generator.generate(
            user_query,
            subgraph
        )
        
        return {
            'subgraph': subgraph,
            'guidance': guidance,
            'cypher_query': result.get('cypher_query') if use_cypher else None
        }
    
    def _cypher_based_search(self, query):
        """Cypher 기반 검색"""
        executor = GraphQueryExecutor(
            self.neo4j_graph.uri,
            self.neo4j_graph.username,
            self.neo4j_graph.password
        )
        
        return executor.execute_natural_language(
            query,
            self.cypher_generator
        )
    
    def _vector_based_search(self, query):
        """벡터 기반 검색"""
        # Coarse-grained 검색
        coarse = self._coarse_grained_retrieval(query)
        
        # Fine-grained 검색
        fine = self._fine_grained_retrieval(query, coarse)
        
        return {
            'coarse_candidates': coarse,
            'fine_candidates': fine
        }
    
    def _construct_subgraph(self, search_result):
        """서브그래프 구성"""
        if 'result' in search_result:
            # Cypher 결과에서 서브그래프 구성
            return self._cypher_result_to_subgraph(search_result['result'])
        else:
            # 벡터 검색 결과에서 서브그래프 구성
            return self._vector_result_to_subgraph(search_result)
```

### 사용 예시

```python
# 초기화
graphrag = CompleteGraphRAG(
    neo4j_graph=neo4j_graph,
    embedding_model=OpenAIEmbeddings(),
    llm=ChatOpenAI(model="gpt-4o"),
    vectorstore=vectorstore
)

# 질의 실행
query = "HBM 관련 매출이 높은 상위 5개 한국 기업은?"

result = graphrag.query(query, use_cypher=True)

# 결과 출력
print("Cypher Query:")
print(result['cypher_query'])

print("\nSubgraph:")
print(result['subgraph'])

print("\nInvestment Guidance:")
print(result['guidance'])
```

---

## 요약

### 핵심 포인트

1. **GraphRAG는 구조화된 검색**: 그래프 기반으로 의미적으로 일관된 컨텍스트 제공
2. **2단계 검색 전략**: Coarse-grained → Fine-grained
3. **서브그래프 구성**: 관련 엔티티만 선택적으로 검색
4. **Cypher 쿼리 생성**: 자연어를 자동으로 Cypher로 변환
5. **글로벌/로컬 검색**: 대규모 구조 이해 + 세부 정보 탐색

### 다음 단계

- [이전 문서: 금융 도메인](04_금융_도메인_Finance.md)
- [다음 문서: LLM 활용](06_LLM_활용.md)

---

**참고 논문**:
- FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph
- Knowledge graphs as tools for explainable machine learning: A survey

