# 시스템 구현 명세서 (Phase 0-1)

> **작성일**: 2025-12-20  
> **버전**: v0.2.0  
> **대상**: Phase 0 (데이터 파싱) + Phase 1 (KG 구축)

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [Phase 0: 데이터 파싱 파이프라인](#phase-0-데이터-파싱-파이프라인)
3. [Phase 1: Knowledge Graph 구축](#phase-1-knowledge-graph-구축)
4. [사용자 가이드](#사용자-가이드)
5. [API 레퍼런스](#api-레퍼런스)

---

## 시스템 개요

### 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                   Data Sources                           │
│    PDF Reports   │   CSV Price   │   News   │  DART     │
└──────────┬──────────────┬──────────────┬────────────┬───┘
           │              │              │            │
           ▼              ▼              ▼            ▼
    ┌──────────┐   ┌──────────┐  ┌──────────┐  ┌─────────┐
    │  Gemini  │   │  Price   │  │   News   │  │  DART   │
    │  PDF     │   │  Parser  │  │  Parser  │  │ Parser  │
    │  Parser  │   │  Agent   │  │  Agent   │  │ Agent   │
    └────┬─────┘   └────┬─────┘  └────┬─────┘  └────┬────┘
         │              │              │            │
         │          KnowledgeGraph 객체 (Pydantic)  │
         └──────────────┴──────────────┴────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │   KG Merger      │
              │  Entity Normalizer│
              └────────┬──────────┘
                       │
                       ▼
              ┌──────────────────┐
              │   Neo4j Loader   │
              │  (Dual Layer)    │
              └────────┬──────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │      Neo4j Database          │
        │  Static Layer │ Dynamic Layer│
        └──────────────────────────────┘
```

### 핵심 컴포넌트

| 컴포넌트 | 역할 | 위치 |
|:---|:---|:---|
| **GeminiPDFParser** | PDF → KG 직접 추출 | `src/parsers/gemini_pdf.py` |
| **KGConstructionAgent** | 파서 오케스트레이터 | `src/agents/kg_construction.py` |
| **EntityNormalizer** | 엔티티 정규화 | `src/utils/entity_normalizer.py` |
| **Neo4jKGLoader** | KG → Neo4j 주입 | `src/dataflows/neo4j_loader.py` |
| **TimeSeriesProcessor** | SAX-DM 패턴 변환 | `src/utils/time_series_processor.py` |
| **EventExtractor** | 뉴스 이벤트 추출 | `src/utils/event_extractor.py` |

---

## Phase 0: 데이터 파싱 파이프라인

### 0.1 GeminiPDFParser

#### 개요
PDF 파일을 Gemini API를 통해 직접 분석하여 Knowledge Graph를 추출합니다.

#### Input
- **파일**: PDF 파일 경로 (str)
- **파라미터**:
  - `model_name`: Gemini 모델 (기본: `"gemini-2.5-pro"`)
  - `use_batch`: Batch API 사용 여부 (기본: `False`)

#### Output
```python
{
    "entities": [
        {
            "name": "Samsung Electronics",
            "type": "IDM",
            "properties": {"ticker": "005930"},
            "confidence": 0.95
        },
        ...
    ],
    "relations": [
        {
            "subject": "Samsung Electronics",
            "predicate": "manufactures",
            "object": "HBM3E",
            "weight": 1.0
        },
        ...
    ]
}
```

#### 사용 예시
```python
from src.parsers.gemini_pdf import GeminiPDFParser

parser = GeminiPDFParser(
    model_name="gemini-2.5-pro",  # 또는 "gemini-2.5-flash" 
    use_batch=False
)

result = parser.parse("data/raw/reports/samsung_2024Q4.pdf")

print(f"Entities: {len(result['entities'])}")
print(f"Relations: {len(result['relations'])}")
```

#### 주요 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|:---|:---|:---|:---|
| `model_name` | str | `"gemini-2.5-pro"` | Gemini 모델 선택 (gemini-2.5-pro 또는 gemini-2.5-flash) |
| `use_batch` | bool | `False` | Batch API 사용 (50% 비용 절감, 현재 테스트 단계에서는 False) |
| `file_path` | str | - | PDF 파일 절대 경로 |

#### 내부 로직

1. **파일 업로드**: Gemini Files API로 PDF 업로드 → URI 반환
2. **프롬프트 로드**: `prompts.yaml`에서 `gemini_pdf_parser.kg_extraction.instruction` 로드
3. **Structured Output**: Gemini API에 JSON Schema 전달 → KG JSON 반환
4. **파싱**: JSON → `KnowledgeGraph` Pydantic 객체 변환
5. **저장**: `data/processed/{file_id}_{timestamp}.json` 저장

#### 에러 처리
- 프롬프트 누락 시: `RuntimeError` 발생
- API 타임아웃: 재시도 없음 (현재)
- JSON 파싱 실패: 에러 로그 및 빈 KG 반환

---

### 0.2 KGConstructionAgent (오케스트레이터)

#### 개요
모든 파서를 관리하고 KG 병합, 정규화, Neo4j 로드를 총괄합니다.

#### Input
- **데이터 소스** (Optional): 
  ```python
  {
      "pdf": [Path("report1.pdf"), Path("report2.pdf")],
      "price": ["005930", "SK"],
      "news": ["삼성전자"],
      "dart": None  # 자동 스캔
  }
  ```
- **설정**:
  - `auto_scan`: 자동 파일 스캔 (기본: `True`)
  - `use_batch`: Batch API 사용 (기본: `False`)
  -load_to_neo4j`: Neo4j 로드 (기본: `False`)

#### Output
```python
{
    "pdf_results": [...],
    "price_results": [...],
    "merged_kg": KnowledgeGraph,
    "neo4j_stats": {
        "static_nodes": 120,
        "dynamic_nodes": 85,
        "relationships_created": 203
    }
}
```

#### 사용 예시
```python
from src.agents.kg_construction import KGConstructionAgent

agent = KGConstructionAgent()

result = agent.construct_knowledge_graph(
    data_sources={
        "pdf": [Path("samsung.pdf")],
        "price": ["005930"]
    },
    load_to_neo4j=True
)

print(f"Total nodes: {result['neo4j_stats']['static_nodes'] + result['neo4j_stats']['dynamic_nodes']}")
```

#### 처리 Flow

```
1. 데이터 스캔
   └─> auto_scan=True이면 data/raw/* 자동 탐색
   
2. 파서 실행
   ├─> PDFParserAgent (각 PDF별)
   ├─> PriceParserAgent (각 ticker별)
   ├─> NewsParserAgent
   └─> DARTParserAgent
   
3. KG 병합
   └─> KGMerger.merge(all_results)
   
4. 엔티티 정규화
   ├─> Ticker 매핑 (삼성 → 005930)
   ├─> Fuzzy 매칭 (Samsung Electronics ≈ 삼성전자)
   └─> Alias 정규화
   
5. Neo4j 로드 (선택적)
   └─> Neo4jKGLoader.load_knowledge_graph()
```

#### 주요 파라미터

| 파라미터 | 타입 | 기본값 | 설명 |
|:---|:---|:---|:---|
| `data_sources` | Dict[str, List] | None | 파싱할 데이터 소스 |
| `auto_scan` | bool | True | 자동 파일 스캔 |
| `use_batch` | bool | False | Batch API 사용 |
| `load_to_neo4j` | bool | False | Neo4j 자동 로드 |

---

### 0.3 TimeSeriesProcessor

#### 개요
주가 시계열 데이터를 SAX-DM 패턴으로 변환하고 Trend 노드를 생성합니다.

#### Input
- `company_ticker`: 종목 코드 (str)
- `prices`: 주가 리스트 (List[float])
- `period`: 기간 (str, 예: "2024-Q4")
- `window_size`: SAX 윈도우 크기 (int, 기본: 5)

#### Output
```python
{
    "ticker": "005930",
    "period": "2024-Q4",
    "pattern": "abcde",  # SAX-DM 패턴
    "trend_type": "Upward"  # Upward/Downward/Volatile/Stable
}
```

#### SAX-DM 변환 로직

```python
# 1. SAX 패턴 생성
from saxpy.sax import sax_via_window

sax_string = sax_via_window(
    ts=np.array(prices),
    win_size=5,
    paa_size=3,
    alphabet_size=5,
    nr_strategy='normal'
)
# 결과: "abcde" (a=하락, e=상승)

# 2. Trend 분류
if volatility > 0.05:
    trend_type = "Volatile"
elif (prices[-1] - prices[0]) / prices[0] > 0.1:
    trend_type = "Upward"
elif (prices[-1] - prices[0]) / prices[0] < -0.1:
    trend_type = "Downward"
else:
    trend_type = "Stable"

# 3. Neo4j Trend 노드 생성 (CREATE)
CREATE (t:Trend {
    period: "2024-Q4",
    company_ticker: "005930",
    pattern: "abcde",
    trend_type: "Upward",
    last_updated: datetime()
})
```

#### 사용 예시
```python
from src.utils.time_series_processor import TimeSeriesProcessor

processor = TimeSeriesProcessor(neo4j_client)

result = processor.process_stock_price(
    company_ticker="005930",
    prices=[50000, 51000, 52000, 53000, 54000],
    period="2024-Q4"
)
```

---

### 0.4 EventExtractor

#### 개요
뉴스 텍스트에서 이벤트를 추출하고 Time-Decay 가중치를 계산합니다.

#### Input
- `news_text`: 뉴스 본문 (str)
- `date`: 뉴스 날짜 (str, YYYY-MM-DD)
- `source`: 출처 (str)

#### Output
```python
{
    "event": {
        "event_type": "실적 발표",
        "description": "삼성전자 4분기 영업이익 6.5조원",
        "affected_entities": ["삼성전자"],
        "importance": 9,
        "impact": "positive"
    },
    "neo4j_result": {
        "events_created": 1,
        "relations_created": 1
    }
}
```

#### Time-Decay 계산

```python
def calculate_time_decay(event_date: str) -> float:
    """
    시간 감쇠 함수 (90일 반감기)
    
    Returns:
        0.1 ~ 1.0 (최근일수록 1.0)
    """
    days_diff = (현재 - event_date).days
    decay_factor = np.exp(-days_diff / 90)
    return max(decay_factor, 0.1)

# 예시
- 오늘: weight = 1.0
- 30일 전: weight = 0.72
- 90일 전: weight = 0.37
- 180일 전: weight = 0.14
- 365일 전: weight = 0.10 (최소값)
```

#### Neo4j 저장

```cypher
CREATE (e:Event {
    type: "실적 발표",
    description: "...",
    date: date("2024-12-20"),
    importance: 9,
    source: "뉴스",
    weight: 1.0,  # time_decay
    created_at: datetime()
})
WITH e
MATCH (c:Company {name: "삼성전자"})
MERGE (e)-[:AFFECTS {weight: 1.0}]->(c)
```

---

## Phase 1: Knowledge Graph 구축

### 1.1 Neo4jKGLoader (Dual Layer Strategy)

#### 개요
Knowledge Graph를 Neo4j에 이중 레이어 전략으로 주입합니다.

#### 이중 레이어 전략

**Static Layer (MERGE)**:
- **대상**: Company, Product, Technology (44개 타입)
- **전략**: ID 기준 UPSERT (중복 방지)
- **쿼리**:
  ```cypher
  MERGE (n:Company {id: $id})
  SET n.name = $name,
      n += $properties,
      n.confidence = $confidence,
      n.last_updated = datetime()
  ```

**Dynamic Layer (CREATE)**:
- **대상**: Observation, Event, Metric, Trend (14개 타입)
- **전략**: 매번 새 노드 생성 (시계열 누적)
- **쿼리**:
  ```cypher
  CREATE (n:Metric {
      id: "Revenue_Samsung_2024Q4",  # period 포함!
      name: $name,
      period: "2024Q4",  # 필수
      value: 70000000000000,
      unit: "KRW"
  })
  SET n.created_at = datetime()
  ```

#### Input
- `kg`: KnowledgeGraph 객체
- `use_dual_layer`: 이중 레이어 사용 (기본: `True`)

#### Output
```python
{
    "static_nodes": 120,
    "dynamic_nodes": 85,
    "relationships_created": 203
}
```

#### 사용 예시
```python
from src.dataflows.neo4j_loader import Neo4jKGLoader

loader = Neo4jKGLoader(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

stats = loader.load_knowledge_graph(kg, use_dual_layer=True)

print(f"Static nodes: {stats['static_nodes']}")
print(f"Dynamic nodes: {stats['dynamic_nodes']}")
```

#### 타입별 분류 로직

```python
DYNAMIC_TYPES = {
    # Occurrent
    NodeType.OBSERVATION,
    NodeType.TEMPORAL_REGION,
    
    # Event
    NodeType.EVENT,
    NodeType.STRATEGIC_ACTION,
    NodeType.CORPORATE_EVENT,
    NodeType.MARKET_ENVIRONMENT,
    NodeType.POLICY_EVENT,
    
    # Metric
    NodeType.FINANCIAL_METRIC,
    NodeType.TECHNICAL_METRIC,
    NodeType.MARKET_METRIC,
    NodeType.METRIC,
    
    # Trend
    NodeType.TREND,
}

def _classify_entity_layer(entity: Entity) -> str:
    return 'dynamic' if entity.type in DYNAMIC_TYPES else 'static'
```

---

### 1.2 EntityNormalizer

#### 개요
다양한 표기의 엔티티를 단일 표준 형태로 정규화합니다.

#### Normalization 전략

**1) Ticker 기반**:
```python
"삼성" → "005930"
"SK하이닉스" → "000660"
"Samsung Electronics" → "005930"
```

**2) Fuzzy Matching**:
```python
similarity("삼성전자", "Samsung Electronics") = 0.85
→ 같은 엔티티로 병합
```

**3) Alias 매핑**:
```python
{
    "삼성전자": ["삼성", "Samsung", "SEC"],
    "SK하이닉스": ["하이닉스", "SK Hynix"],
}
```

#### Input
- `entities`: List[Entity]
- `ticker_map`: Dict[str, str]

#### Output
```python
# Before Normalization
[
    Entity(name="삼성전자", type="Company"),
    Entity(name="Samsung Electronics", type="Company"),
    Entity(name="삼성", type="Company")
]

# After Normalization
[
    Entity(name="삼성전자", type="Company", properties={"ticker": "005930"})
]
```

---

## 사용자 가이드

### 빠른 시작

#### 1. 단일 PDF 파싱

```python
from src.parsers.gemini_pdf import GeminiPDFParser

parser = GeminiPDFParser()  # 기본: gemini-2.5-pro
result = parser.parse("report.pdf")
```

#### 2. 전체 파이프라인 실행

```python
from src.agents.kg_construction import KGConstructionAgent

agent = KGConstructionAgent()
result = agent.construct_knowledge_graph(
    auto_scan=True,
    load_to_neo4j=True
)
```

#### 3. Neo4j 조회

```cypher
// 삼성전자 노드 찾기
MATCH (c:Company {name: "삼성전자"})
RETURN c

// 최근 이벤트 조회
MATCH (e:Event)-[:AFFECTS]->(c:Company {name: "삼성전자"})
WHERE e.date >= date("2024-01-01")
RETURN e.description, e.date, e.importance
ORDER BY e.date DESC
```

### 설정 파일

#### prompts.yaml
모든 LLM 프롬프트 관리:
```yaml
gemini_pdf_parser:
  kg_extraction:
    instruction: |
      PDF에서 Knowledge Graph 추출...
      
event_extractor:
  news_extraction:
    instruction: |
      뉴스에서 이벤트 추출...
```

#### parser_config.py
파서별 설정:
```python
class ParserConfigs:
    pdf: PdfParserConfig(
        model="gemini-2.5-pro",  # 또는 gemini-2.5-flash
        use_batch=False
    )
    price: PriceParserConfig(
        sample_days=30,
        sax_window_size=5,
        sax_paa_size=3,
        sax_alphabet_size=5
    )
```

### 환경 변수

```bash
GOOGLE_API_KEY=your_gemini_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

---

## API 레퍼런스

### GeminiPDFParser

```python
class GeminiPDFParser:
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        use_batch: bool = False
    ) -> None
    
    def parse(self, file_path: str) -> Dict[str, Any]
```

### KGConstructionAgent

```python
class KGConstructionAgent:
    def construct_knowledge_graph(
        self,
        data_sources: Optional[Dict[str, List[Path]]] = None,
        auto_scan: bool = True,
        use_batch: bool = False,
        load_to_neo4j: bool = False
    ) -> Dict[str, Any]
```

### Neo4jKGLoader

```python
class Neo4jKGLoader:
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "password"
    ) -> None
    
    def load_knowledge_graph(
        self,
        kg: KnowledgeGraph,
        use_dual_layer: bool = True
    ) -> Dict[str, int]
```

### TimeSeriesProcessor

```python
class TimeSeriesProcessor:
    def process_stock_price(
        self,
        company_ticker: str,
        prices: List[float],
        period: str,
        window_size: int = 5
    ) -> Dict[str, Any]
```

### EventExtractor

```python
class EventExtractor:
    def extract_events_from_news(
        self,
        news_text: str,
        date: str,
        source: str = "unknown"
    ) -> Dict[str, Any]
    
    def _calculate_time_decay(
        self,
        event_date: str,
        current_date: str = None
    ) -> float
```

---

**작성자**: AI Copilot  
**최종 수정**: 2025-12-20
