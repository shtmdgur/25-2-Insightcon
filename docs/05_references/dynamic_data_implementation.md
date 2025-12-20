# 동적 데이터 처리: 코드 구현 예제

## 1. Neo4j Bitemporal Model 구현

### 1.1 기본 노드 생성 (스크립트)

```cypher
# 회사 노드 생성 (SK Hynix 예시)
CREATE (c:Company {
  id: 'SK_Hynix_001',
  name: 'SK Hynix Inc.',
  country: 'South Korea',
  founded_year: 1983,
  headquarters: 'Icheon, Gyeonggi',
  
  # Bitemporal 속성
  valid_from: date('2024-01-01'),
  valid_until: NULL,
  ingested_at: datetime('2024-12-15T10:00:00Z'),
  last_updated: datetime('2024-12-15T10:00:00Z'),
  version: 1,
  source_document: 'SK_Hynix_2024_ER',
  is_deleted: false
})

# FAB 노드 생성
CREATE (fab:Fab {
  id: 'SK_Hynix_Icheon_001',
  name: 'SK Hynix Icheon Fab 1',
  company_id: 'SK_Hynix_001',
  location: 'Icheon, Gyeonggi',
  wafer_size: '300mm',
  technology_nodes: ['7nm', '10nm', '14nm'],
  
  valid_from: date('1987-01-01'),
  valid_until: NULL,
  ingested_at: datetime('2024-12-15T10:00:00Z')
})

# 관계 생성
CREATE (c)-[:OPERATES]->(fab)

# 인덱스 생성 (성능 최적화)
CREATE INDEX idx_company_id ON :Company(id)
CREATE INDEX idx_fab_id ON :Fab(id)
CREATE INDEX idx_valid_temporal ON :Company(valid_from, valid_until)
```

### 1.2 TimeSeries 속성 및 DataPoint

```cypher
# 시계열 메타데이터 노드
CREATE (ts:TimeSeries {
  id: 'SK_Hynix_revenue_ts_001',
  entity_id: 'SK_Hynix_001',
  property_name: 'revenue',
  unit: 'KRW (Trillions)',
  data_type: 'float',
  granularity: 'quarterly',
  calculation_method: 'official_earnings_report'
})

# 시계열 데이터 포인트들
CREATE (p1:DataPoint {
  id: 'SKH_revenue_2024Q1',
  value: 50.8,
  timestamp: date('2024-03-31'),
  ingested_at: datetime('2024-05-10T14:30:00Z'),
  source: 'SK_Hynix_Q1_2024_ER',
  source_confidence: 0.99,
  is_revised: false
})

CREATE (p2:DataPoint {
  id: 'SKH_revenue_2024Q2',
  value: 70.8,
  timestamp: date('2024-06-30'),
  ingested_at: datetime('2024-08-15T10:00:00Z'),
  source: 'SK_Hynix_Q2_2024_ER',
  source_confidence: 0.99,
  is_revised: false
})

CREATE (p3:DataPoint {
  id: 'SKH_revenue_2024Q3',
  value: 78.9,
  timestamp: date('2024-09-30'),
  ingested_at: datetime('2024-11-12T09:00:00Z'),
  source: 'SK_Hynix_Q3_2024_ER',
  source_confidence: 0.99,
  is_revised: false
})

# 시계열과 포인트 연결
CREATE (ts)-[:HAS_POINT]->(p1)
CREATE (ts)-[:HAS_POINT]->(p2)
CREATE (ts)-[:HAS_POINT]->(p3)

# 회사와 시계열 연결
CREATE (c)-[:HAS_TIMESERIES]->(ts)

# 인덱스 (시계열 쿼리 최적화)
CREATE INDEX idx_datapoint_timestamp ON :DataPoint(timestamp)
CREATE INDEX idx_datapoint_entity ON :DataPoint(entity_id, timestamp)
```

### 1.3 이벤트 노드 (Event Nodes)

```cypher
# 제품 출시 이벤트
CREATE (evt1:Event:ProductLaunchEvent {
  id: 'SKH_HBM4_Launch_20240915',
  product_name: 'HBM4 (12-layer)',
  announced_date: date('2024-09-15'),
  effective_date: date('2024-12-01'),
  
  # 스펙
  spec_bandwidth: '10 Gbps',
  spec_power_efficiency_improvement: 0.40,
  spec_memory_capacity: '128GB per stack',
  target_customer: 'NVIDIA',
  
  # 중요도
  impact_level: 'HIGH',
  news_mentions: 45,
  analyst_coverage: 'positive',
  
  # 투자
  r_and_d_investment: 2500,  # billion KRW
  expected_revenue_impact: 8000,  # billion KRW/year
  
  valid_from: date('2024-09-15'),
  valid_until: NULL,
  ingested_at: datetime('2024-09-16T08:00:00Z')
})

# 용량 확장 이벤트
CREATE (evt2:Event:CapacityExpansionEvent {
  id: 'Samsung_HBM_Expansion_20240815',
  announced_date: date('2024-08-15'),
  type: 'PRODUCTION_CAPACITY_EXPANSION',
  
  # 상세
  fab_target: 'Samsung_Pyeongtak_001',
  capacity_increase_percent: 150,
  new_capacity: 150000,  # wafers/month
  investment_amount: 7300,  # billion KRW
  expected_completion: date('2025-Q4'),
  
  driver_event: 'AI_Infrastructure_Boom',  # 원인 이벤트
  expected_impact: 'Double HBM3E/HBM4 production',
  
  valid_from: date('2024-08-15'),
  valid_until: NULL,
  ingested_at: datetime('2024-08-16T10:00:00Z')
})

# 이벤트 관계
CREATE (evt1)-[:ANNOUNCED_BY]->(c:Company {id: 'SK_Hynix_001'})
CREATE (evt2)-[:ANNOUNCED_BY]->(samsung:Company {id: 'Samsung_001'})

# 이벤트 간 인과관계
CREATE (evt1)-[:TRIGGERED_BY]->(market:Event {name: 'AI_Infrastructure_Boom'})
CREATE (evt2)-[:IN_RESPONSE_TO]->(market)

# 이벤트 인덱스
CREATE INDEX idx_event_date ON :Event(announced_date)
CREATE INDEX idx_event_type ON :Event:Event(type)
```

## 2. Python: LLM 기반 Entity Linking

```python
# file: entity_linking.py

from typing import Dict, List, Tuple
from langchain.llms import ChatGemini
from langchain.prompts import PromptTemplate
import json
import re

class EntityLinkingPipeline:
  def __init__(self, neo4j_driver, llm_model='gemini-pro'):
    self.driver = neo4j_driver
    self.llm = ChatGemini(model_name=llm_model, temperature=0.1)
    
  def extract_mentions_from_text(self, text: str) -> Dict:
    """
    Step 1: LLM으로 텍스트에서 멘션 추출
    """
    prompt = PromptTemplate(
      input_variables=["text"],
      template="""
다음 텍스트에서 반도체 산업 관련 엔티티와 이벤트를 추출하세요.

Text:
{text}

다음 형식의 JSON으로 응답하세요:
{{
  "companies": [
    {{"name": "회사명", "context": "문맥"}},
    ...
  ],
  "events": [
    {{"type": "PRODUCT_LAUNCH|CAPACITY_EXPANSION|...", "description": "설명"}},
    ...
  ],
  "products": [
    {{"name": "제품명", "specs": "스펙"}}
  ],
  "dates": [
    {{"date": "2024-09-15", "context": "문맥"}}
  ]
}}
"""
    )
    
    chain = prompt | self.llm
    response = chain.invoke({"text": text})
    
    try:
      mentions = json.loads(response.content)
    except json.JSONDecodeError:
      # JSON 파싱 실패 시 재시도
      mentions = self._parse_semi_structured(response.content)
    
    return mentions
  
  def disambiguate_entities(self, mentions: Dict) -> List[Dict]:
    """
    Step 2: 멘션을 그래프의 실제 노드 ID로 매핑
    """
    # 기존 그래프에서 회사 목록 조회
    existing_companies = self._get_existing_companies()
    
    prompt = PromptTemplate(
      input_variables=["mention", "existing"],
      template="""
다음 회사 멘션을 우리 그래프의 노드 ID로 매핑하세요:

Mention: {mention}
Existing companies in graph:
{existing}

응답 형식:
{{
  "mapped_node_id": "SK_Hynix_001 또는 None",
  "confidence": 0.95,
  "reasoning": "매핑 이유"
}}
"""
    )
    
    mappings = []
    for company in mentions.get('companies', []):
      existing_str = json.dumps(existing_companies[:10])  # 상위 10개만
      
      chain = prompt | self.llm
      response = chain.invoke({
        "mention": company['name'],
        "existing": existing_str
      })
      
      mapping = json.loads(response.content)
      if mapping.get('mapped_node_id'):
        mappings.append({
          'original_mention': company['name'],
          'node_id': mapping['mapped_node_id'],
          'confidence': mapping['confidence']
        })
    
    return mappings
  
  def classify_events(self, events: List[Dict]) -> List[Dict]:
    """
    Step 3: 이벤트를 올바른 타입으로 분류
    """
    prompt = PromptTemplate(
      input_variables=["event_description"],
      template="""
다음 이벤트를 반도체 산업 이벤트 타입으로 분류하세요:

Event: {event_description}

가능한 타입:
- PRODUCT_LAUNCH: 신제품 출시
- CAPACITY_EXPANSION: 생산 능력 확대
- PARTNERSHIP: 전략적 제휴
- SUPPLY_DISRUPTION: 공급망 차질
- EXPORT_CONTROL: 수출 규제
- PRICE_CHANGE: 가격 변화
- MARKET_SHARE_SHIFT: 시장 점유율 변화
- TECH_ADVANCEMENT: 기술 진전

응답 형식:
{{
  "event_type": "상기 타입 중 하나",
  "confidence": 0.9,
  "key_entities": ["entity1", "entity2"],
  "timeline": "2024-09-15 또는 null"
}}
"""
    )
    
    classified = []
    for event in events:
      chain = prompt | self.llm
      response = chain.invoke({
        "event_description": event.get('description', '')
      })
      
      classification = json.loads(response.content)
      classified.append({
        **event,
        **classification
      })
    
    return classified
  
  def generate_cypher_queries(self, mappings: List[Dict], 
                             events: List[Dict]) -> List[str]:
    """
    Step 4: Neo4j Cypher 쿼리 자동 생성
    """
    queries = []
    
    for event in events:
      if event.get('confidence', 0) > 0.80:
        # 이벤트 노드 생성 쿼리
        event_id = f"{event.get('event_type', 'EVENT')}_{event.get('timeline', '').replace('-', '')}"
        
        query = f"""
CREATE (evt:Event:{event.get('event_type', 'Event')} {{
  id: '{event_id}',
  description: '{event.get('description', '')[:100]}...',
  announced_date: date('{event.get('timeline', '2024-12-01')}'),
  ingested_at: datetime(),
  source: 'LLM_extracted',
  confidence: {event.get('confidence', 0.75)}
}})
"""
        
        # 발표 회사와 연결
        for mapping in mappings:
          if mapping['original_mention'] in event.get('description', ''):
            if mapping['confidence'] > 0.85:
              query += f"""
MATCH (c:Company {{id: '{mapping['node_id']}'}})
CREATE (evt)-[:ANNOUNCED_BY]->(c)
"""
        
        queries.append(query)
    
    return queries
  
  def _get_existing_companies(self) -> List[Dict]:
    """Neo4j에서 기존 회사 목록 조회"""
    query = """
    MATCH (c:Company)
    RETURN c.id as id, c.name as name
    LIMIT 100
    """
    with self.driver.session() as session:
      result = session.run(query)
      return [dict(record) for record in result]
  
  def _parse_semi_structured(self, text: str) -> Dict:
    """JSON 파싱 실패 시 반구조화 텍스트 파싱"""
    # 정규식으로 기본 정보 추출
    companies = re.findall(r'Company:\s*([^,\n]+)', text)
    events = re.findall(r'Event:\s*([^,\n]+)', text)
    
    return {
      'companies': [{'name': c.strip()} for c in companies],
      'events': [{'type': 'UNKNOWN', 'description': e.strip()} for e in events],
      'products': [],
      'dates': []
    }

# 사용 예
if __name__ == '__main__':
  from neo4j import GraphDatabase
  
  driver = GraphDatabase.driver(
    'bolt://localhost:7687',
    auth=('neo4j', 'password')
  )
  
  pipeline = EntityLinkingPipeline(driver)
  
  text = """
  SK Hynix는 9월 15일 HBM4 신제품을 공개했습니다. 
  12층 구조에 10Gbps 대역폭으로 40% 전력 효율 개선을 제공합니다.
  Samsung은 이에 대응하여 8월 15일 Pyeongtak FAB을 150% 확장한다고 발표했습니다.
  """
  
  # Step 1: 멘션 추출
  mentions = pipeline.extract_mentions_from_text(text)
  print("Mentions:", mentions)
  
  # Step 2: 멘션 매핑
  mappings = pipeline.disambiguate_entities(mentions)
  print("Mappings:", mappings)
  
  # Step 3: 이벤트 분류
  events = pipeline.classify_events(mentions.get('events', []))
  print("Classified events:", events)
  
  # Step 4: Cypher 쿼리 생성
  queries = pipeline.generate_cypher_queries(mappings, events)
  
  # 쿼리 실행 (높은 신뢰도만)
  with driver.session() as session:
    for query in queries:
      print(f"\n실행: {query[:100]}...")
      try:
        session.run(query)
        print("✓ 성공")
      except Exception as e:
        print(f"✗ 실패: {e}")
  
  driver.close()
```

## 3. 시간 범위 쿼리 (Neo4j Cypher)

```cypher
# 쿼리 1: "2024년 SK Hynix의 주요 비즈니스 이벤트"
MATCH (c:Company {id: 'SK_Hynix_001'})
      -[:ANNOUNCED_BY|:EXPERIENCES]->(evt:Event)
WHERE evt.announced_date >= date('2024-01-01')
  AND evt.announced_date <= date('2024-12-31')
  AND evt.impact_level IN ['HIGH', 'CRITICAL']
RETURN 
  evt.id as event_id,
  evt.announced_date as date,
  labels(evt) as event_type,
  evt.description as description
ORDER BY evt.announced_date DESC

# 쿼리 2: "HBM3E 생산량 추이 (2024년 1분기~4분기)"
MATCH (samsung:Company {id: 'Samsung_001'})
      -[:HAS_TIMESERIES]->(ts:TimeSeries {property_name: 'hbm3e_production_volume'})
      -[:HAS_POINT]->(p:DataPoint)
WHERE p.timestamp >= date('2024-01-01')
  AND p.timestamp <= date('2024-12-31')
RETURN 
  p.timestamp as quarter,
  p.value as production_volume_wafers,
  p.source as source
ORDER BY p.timestamp ASC

# 쿼리 3: "US 수출 통제 이후 60일 이내 공급망 영향 (Temporal)"
MATCH (control:Event {event_type: 'EXPORT_CONTROL'})
MATCH (disruption:Event {event_type: 'SUPPLY_DISRUPTION'})
      -[:TRIGGERED_BY]->(control)
WHERE disruption.announced_date > control.announced_date
  AND disruption.announced_date <= control.announced_date + duration('P60D')
RETURN 
  control.announced_date as control_date,
  disruption.announced_date as disruption_date,
  duration.between(control.announced_date, disruption.announced_date).days as days_lag,
  disruption.affected_company as affected_company
ORDER BY days_lag ASC

# 쿼리 4: "특정 회사의 시계열 데이터 + 이벤트 연도별 (Timeline View)"
MATCH (c:Company {id: 'SK_Hynix_001'})
      -[:HAS_TIMESERIES]->(ts:TimeSeries)
      -[:HAS_POINT]->(p:DataPoint)
OPTIONAL MATCH (c)-[:ANNOUNCED_BY|:EXPERIENCES]->(evt:Event)
WITH 
  DISTINCT c,
  p.timestamp as data_date,
  p.value as metric_value,
  ts.property_name as metric_name,
  evt.announced_date as event_date,
  labels(evt) as event_types
WHERE p.timestamp >= date('2024-01-01')
ORDER BY data_date ASC, event_date ASC
RETURN 
  data_date,
  metric_name,
  metric_value,
  event_date,
  event_types
SKIP 0 LIMIT 100
```

## 4. 성능 최적화 인덱스

```cypher
# 시계열 조회 최적화
CREATE INDEX idx_datapoint_timestamp ON :DataPoint(timestamp)
CREATE COMPOSITE INDEX idx_datapoint_lookup 
  ON :DataPoint(entity_id, property_name, timestamp)

# 이벤트 필터링 최적화
CREATE INDEX idx_event_date ON :Event(announced_date)
CREATE INDEX idx_event_type ON :Event(event_type)
CREATE COMPOSITE INDEX idx_event_temporal 
  ON :Event(event_type, announced_date)

# 회사/FAB 조회 최적화
CREATE INDEX idx_company_id ON :Company(id)
CREATE INDEX idx_fab_id ON :Fab(id)
CREATE INDEX idx_company_country ON :Company(country)

# Temporal 쿼리용 복합 인덱스
CREATE COMPOSITE INDEX idx_temporal_versioning
  ON :Company(id, valid_from, valid_until)

# 통계 정보 설정 (Cardinality 최적화)
ANALYZE
```

## 5. 캐싱 전략 (Redis)

```python
# file: temporal_cache.py

import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class TemporalDataCache:
  def __init__(self, redis_url='redis://localhost:6379'):
    self.redis_client = redis.from_url(redis_url)
    
    # 캐시 TTL 설정 (데이터 특성별)
    self.cache_config = {
      'company_timeseries': 86400,      # 1일 (정기보고)
      'fab_utilization': 3600,          # 1시간 (거의 실시간)
      'chip_prices': 7200,              # 2시간 (일일 변동)
      'events_recent': 1800,            # 30분 (새 사건)
      'company_metadata': 604800        # 7일 (정적)
    }
  
  def get_timeseries(self, entity_id: str, property_name: str, 
                     start_date: str, end_date: str) -> Optional[Dict]:
    """
    시계열 데이터 조회 (캐시 먼저, 없으면 DB)
    """
    cache_key = f"ts:{entity_id}:{property_name}:{start_date}:{end_date}"
    
    # 캐시 확인
    cached = self.redis_client.get(cache_key)
    if cached:
      print(f"✓ Cache hit: {cache_key}")
      return json.loads(cached)
    
    print(f"✗ Cache miss: {cache_key} (querying DB...)")
    # DB 조회는 별도 Neo4j 함수에서
    # result = neo4j_query(...)
    # 여기서는 스킵
    
    # 데이터를 받아 캐시 저장
    # self.set_timeseries(cache_key, result)
    
    return None
  
  def set_timeseries(self, entity_id: str, property_name: str,
                     start_date: str, end_date: str, data: Dict):
    """시계열 데이터 캐시 저장"""
    cache_key = f"ts:{entity_id}:{property_name}:{start_date}:{end_date}"
    ttl = self.cache_config.get('company_timeseries', 3600)
    
    self.redis_client.setex(
      cache_key,
      ttl,
      json.dumps(data, default=str)
    )
  
  def invalidate_timeseries(self, entity_id: str):
    """
    특정 엔티티의 모든 시계열 캐시 무효화
    (새 데이터 들어왔을 때)
    """
    pattern = f"ts:{entity_id}:*"
    keys = self.redis_client.keys(pattern)
    
    if keys:
      self.redis_client.delete(*keys)
      print(f"Invalidated {len(keys)} cache entries for {entity_id}")
  
  def get_recent_events(self, days_back: int = 7) -> Optional[Dict]:
    """최근 이벤트 캐시 (자주 접근)"""
    cache_key = f"events:recent:{days_back}d"
    
    cached = self.redis_client.get(cache_key)
    if cached:
      return json.loads(cached)
    
    return None
  
  def set_recent_events(self, days_back: int, data: Dict):
    """최근 이벤트 캐시 저장"""
    cache_key = f"events:recent:{days_back}d"
    ttl = self.cache_config.get('events_recent', 1800)
    
    self.redis_client.setex(
      cache_key,
      ttl,
      json.dumps(data, default=str)
    )
  
  def get_cache_stats(self) -> Dict:
    """캐시 통계"""
    info = self.redis_client.info('stats')
    return {
      'total_connections': info.get('total_connections_received'),
      'total_commands': info.get('total_commands_processed'),
      'memory_used': info.get('used_memory_human')
    }

# 사용 예
if __name__ == '__main__':
  cache = TemporalDataCache()
  
  # 시계열 캐시
  sk_hynix_revenue = {
    'Q1': 50.8,
    'Q2': 70.8,
    'Q3': 78.9
  }
  cache.set_timeseries(
    'SK_Hynix_001',
    'revenue',
    '2024-01-01',
    '2024-09-30',
    sk_hynix_revenue
  )
  
  # 조회 (캐시에서)
  result = cache.get_timeseries(
    'SK_Hynix_001',
    'revenue',
    '2024-01-01',
    '2024-09-30'
  )
  print("Retrieved:", result)
  
  # 캐시 통계
  stats = cache.get_cache_stats()
  print("Cache stats:", stats)
```

---

**이 코드는 Palantir-inspired 동적 데이터 처리를 Neo4j + Python으로 구현한 실무 예제입니다.**
**프로덕션 배포 시 에러 핸들링, 로깅, 트랜잭션 관리를 추가하세요.**