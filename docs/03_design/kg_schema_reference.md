# Knowledge Graph Schema Reference

> **작성일**: 2025-12-23  
> **버전**: Hybrid KG Architecture 1.0  
> **기준**: 실제 코드 구현 기반

이 문서는 프로젝트의 Knowledge Graph 스키마와 각 Parser별 데이터 구조를 **실제 코드**를 기반으로 정의합니다.

---

## 1. Core Schema (`nodes.py`)

### 1.1 NodeType Enum

| Enum 값 | Value | 레이어 | Neo4j 전략 | 설명 |
|---------|-------|--------|-----------|------|
| `IDM` | "IDM" | Agent | MERGE | 종합 반도체 기업 (삼성전자, Intel) |
| `FABLESS` | "Fabless" | Agent | MERGE | 설계 전문 (NVIDIA, Qualcomm) |
| `FOUNDRY` | "Foundry" | Agent | MERGE | 수탁 생산 (TSMC) |
| `SUPPLIER` | "Supplier" | Agent | MERGE | 장비/소재 공급 (ASML, 한미반도체) |
| `ORGANIZATION` | "Organization" | Agent | MERGE | 정부, 협회 등 |
| `EARNINGS` | "Earnings" | Signal | CREATE | 실적 발표, 펀더멘탈 스냅샷 |
| `PRICE_MOVEMENT` | "PriceMovement" | Signal | CREATE | 주가 급등/급락 (±5% 이상) |
| `DISCLOSURE` | "Disclosure" | Signal | CREATE | 공시 (합병, 투자, 수주) |
| `ISSUE` | "Issue" | Signal | CREATE | 뉴스, 이슈, 트렌드 |
| `ECONOMIC_INDICATOR` | "EconomicIndicator" | MacroMetric | MERGE | 환율, 금리, 유가 등 |
| `NEWS` | "News" | Document | CREATE | 뉴스 문서 |
| `REPORT` | "Report" | Document | CREATE | 리서치 리포트 |

### 1.2 RelationType Enum

| Enum 값 | Value | 레이어 | 용도 |
|---------|-------|--------|------|
| `AFFECTS` | "AFFECTS" | Logic | 거시 지표 → Agent 역학 관계 |
| `TRIGGERED_BY` | "TRIGGERED_BY" | Causal | Signal → Signal 인과 관계 |
| `SUPPLIES` | "SUPPLIES" | Structural | 공급망 관계 |
| `MANUFACTURES` | "MANUFACTURES" | Structural | 생산 관계 |
| `HAS_SIGNAL` | "HAS_SIGNAL" | Structural | Agent → Signal 연결 |
| `MENTIONED_IN` | "MENTIONED_IN" | Document | Document 내 언급 |

### 1.3 Relation 클래스 메타데이터 필드

```python
class Relation(BaseModel):
    subject: str
    predicate: RelationType
    object: str
    properties: Dict[str, Any]
    
    # 공통
    confidence: Optional[float]     # 0.0~1.0
    source: Optional[str]           # 데이터 출처
    
    # AFFECTS 전용
    correlation: Optional[str]      # "DIRECT" / "INVERSE"
    sensitivity: Optional[float]    # 0.0~1.0
    lag: Optional[str]              # "IMMEDIATE", "1Q", "1Y" 등
    
    # TRIGGERED_BY 전용
    reasoning: Optional[str]        # 인과관계 설명
    impact_duration: Optional[str]  # "SHORT" / "LONG"
    
    # SUPPLIES 전용
    dependency: Optional[float]     # 0.0~1.0
    is_critical: Optional[bool]     # 대체 불가능 여부
    supply_type: Optional[str]      # "EQUIPMENT" / "MATERIAL"
    
    # HAS_SIGNAL 전용
    importance: Optional[float]     # 0.0~1.0
    is_official: Optional[bool]     # 공식 공시 여부
```

---

## 2. Parser별 상세 스키마

### 2.1 DARTParserAgent

**소스 파일**: `src/agents/parsers/dart_parser_agent.py`  
**입력**: `data/preprocessed/dart/` 디렉토리

#### 입력 CSV 파일

| 파일 | 용도 |
|------|------|
| `companies.csv` | 기업 마스터 데이터 |
| `disclosure_states.csv` | 공시 이력 |
| `financial_states.csv` | 분기별 재무 데이터 |

#### 출력 Entity: Agent (Company)

```python
# dart_parser_agent.py L201-212
Entity(
    name=normalized_name,              # 정규화된 회사명
    type=node_type,                    # IDM/Fabless/Foundry/Supplier
    properties={
        "corp_code": str,              # DART 고유 코드
        "corp_name": str,              # 원본 회사명
        "ceo_nm": str,                 # 대표이사
        "est_dt": str,                 # 설립일
        "adres": str                   # 주소
    },
    confidence=1.0
)
```

#### 출력 Entity: Disclosure

```python
# dart_parser_agent.py L254-265
Entity(
    name=f"Disclosure_{ticker}_{date}_{idx}",  # 고유 ID로 중복 방지
    type=NodeType.DISCLOSURE,
    sentiment="POSITIVE" | "NEGATIVE" | "NEUTRAL",
    properties={
        "ticker": str,                 # 종목코드 (6자리)
        "date": str,                   # YYYY-MM-DD
        "report_nm": str,              # 공시 제목
        "disclosure_type": str         # 공시 유형
    },
    confidence=1.0
)
```

#### 출력 Entity: Earnings

```python
# dart_parser_agent.py L346-361
Entity(
    name=f"Earnings_{corp_code}_{period}",  # 예: Earnings_00126380_2024_Q3
    type=NodeType.EARNINGS,
    sentiment="POSITIVE" | "NEGATIVE",       # net_income > 0 기준
    properties={
        "corp_code": str,              # DART 고유 코드
        "period": str,                 # "2024_Q3"
        "year": str,                   # "2024"
        "quarter": str,                # "Q1"/"Q2"/"Q3"/"Q4"/"Annual"
        "date": str,                   # 분기말 날짜 (Temporal Linking용)
        "revenue": float,              # 매출액
        "operating_income": float,     # 영업이익
        "net_income": float            # 순이익
    },
    confidence=1.0
)
```

#### 출력 Relation: HAS_SIGNAL

```python
# dart_parser_agent.py L269-274, L365-370
Relation(
    subject=company_name,              # Agent 이름
    predicate=RelationType.HAS_SIGNAL,
    object=event_name,                 # Disclosure/Earnings 노드 이름
    properties={"date": str} | {"period": str}
)
```

---

### 2.2 FundParserAgent

**소스 파일**: `src/agents/parsers/fund_parser_agent.py`  
**입력**: `data/preprocessed/fund/global_semis_fundamentals.csv`

#### 모드 A: Property Update (기본, `save_as_snapshot=False`)

Agent 노드의 `fundamental_stats` 속성에 재무 지표를 Map으로 저장합니다.

```python
# fund_parser_agent.py L162-183
Entity(
    name=company_name,                 # 회사명
    type=node_type,                    # IDM/Fabless/Foundry/Supplier
    properties={
        "ticker": str,                 # 종목코드
        "sector": str | None,          # 섹터
        "country": str | None          # 국가
    },
    fundamental_stats={                # ✅ 별도 필드 (Neo4j Map으로 저장)
        "market_cap": float | None,
        "total_revenue": float | None,
        "total_debt": float | None,
        "ebitda_margins": float | None,
        "gross_margins": float | None,
        "profit_margins": float | None,
        "roe": float | None,           # Return on Equity
        "roa": float | None,           # Return on Assets
        "pe_ratio": float | None,      # Trailing P/E
        "pb_ratio": float | None       # Price to Book
    },
    confidence=1.0
)
```

#### 모드 B: Snapshot (`save_as_snapshot=True`)

Earnings 노드로 스냅샷 저장 (동적 KG).

```python
# fund_parser_agent.py L191-206
Entity(
    name=f"Fundamentals_{company_name}_{date_str}",
    type=NodeType.EARNINGS,
    properties={
        "ticker": str,
        "company_name": str,
        "date": str,                   # 생성일
        "metric_type": "fundamentals",
        "is_fundamentals_snapshot": True,  # ✅ Earnings 중 펀더멘탈 구분용
        "marketCap": float | None,
        "totalDebt": float | None,
        "profitMargins": float | None,
        "ROE": float | None
    },
    confidence=1.0
)
```

---

### 2.3 MacroParserAgent

**소스 파일**: `src/agents/parsers/macro_parser_agent.py`  
**입력**: `data/preprocessed/macro/fred_rates.csv`

#### 데이터 처리 방식

- **시계열 저장 안 함**: 각 지표(series)별로 **요약 통계만** 저장
- **1 Series = 1 Node**: FEDFUNDS, DGS10 등 각 지표가 개별 노드

#### 출력 Entity: EconomicIndicator

```python
# macro_parser_agent.py L158-171
Entity(
    name=f"{series_name}",             # "FEDFUNDS", "DGS10", "USD/KRW"
    type=NodeType.ECONOMIC_INDICATOR,
    properties={
        "series": str,                 # series 식별자
        "latest_value": float,         # 최신 값
        "latest_date": str,            # 최신 데이터 날짜 (YYYY-MM-DD)
        "indicator_type": "macro",
        "data_points": int,            # 시계열 데이터 개수
        "min_value": float,            # 전체 기간 최소값
        "max_value": float,            # 전체 기간 최대값
        "mean_value": float            # 전체 기간 평균값
    },
    confidence=1.0
)
```

#### 출력 Relation

**없음** - EconomicIndicator는 단독 노드로 생성.  
`AFFECTS` 관계는 **LLM(PDFParser)**에서 추출됩니다.

---

### 2.4 NewsParserAgent

**소스 파일**: `src/agents/parsers/news_parser_agent.py`  
**입력**: `data/preprocessed/news/News_processed.csv`

#### 샘플링 설정

```python
# parser_config.py
sample_size = 200              # 최대 처리 뉴스 수
max_title_length = 200         # 제목 최대 길이
max_desc_length = 500          # 설명 최대 길이
```

#### 출력 Entity: Issue

```python
# news_parser_agent.py L172-185
Entity(
    name=f"Issue_{keyword}_{date_str}",  # 예: Issue_삼성전자_2024-12-01
    type=NodeType.ISSUE,
    sentiment="POSITIVE" | "NEGATIVE" | "NEUTRAL",  # 제목 기반 분류
    properties={
        "date": str,                   # YYYY-MM-DD
        "title": str,                  # 뉴스 제목 (truncated)
        "description": str,            # 뉴스 본문 (truncated)
        "keyword": str,                # 관련 키워드
        "link": str,                   # 원문 링크
        "time_decay_weight": float     # 시간 감쇠 가중치 (0.1~1.0)
    },
    confidence=0.8                     # 뉴스는 신뢰도 낮게 설정
)
```

#### 출력 Relation: HAS_SIGNAL

```python
# news_parser_agent.py L200-208 (LLM 경로)
# news_parser_agent.py L228-236 (Fallback 경로)
Relation(
    subject=company_name | keyword,    # LLM 추출 기업 또는 키워드
    predicate=RelationType.HAS_SIGNAL,
    object=issue_entity.name,
    properties={
        "weight": float,               # time_decay_weight
        "source": str                  # 파일 경로
    }
)
```

---

### 2.5 PriceParserAgent

**소스 파일**: `src/agents/parsers/price_parser_agent.py`  
**입력**: `data/preprocessed/price/*.csv` (Ticker별)

#### 출력 Entity: Agent

```python
# price_parser_agent.py L176-181
Entity(
    name=company_name,                 # ticker_mapping 기반
    type=agent_type,                   # IDM/Fabless/Foundry/Supplier
    properties={"ticker": str},
    confidence=1.0
)
```

#### 출력 Entity: Issue (Trend)

```python
# price_parser_agent.py L159-169
Entity(
    name=f"Trend_{ticker}_{date_str}",  # 예: Trend_005930.KS_20241220
    type=NodeType.ISSUE,
    properties={
        "ticker": str,
        "pattern": str,                # SAX 패턴 문자열
        "trend_type": str,             # "Upward"/"Downward"/"Stable"/"Volatile"
        "is_trend": True               # ✅ Issue 중 Trend 구분용
    },
    confidence=1.0
)
```

#### 출력 Entity: PriceMovement

```python
# price_parser_agent.py L224-236
Entity(
    name=f"PriceMovement_{ticker}_{date_str}",
    type=NodeType.PRICE_MOVEMENT,
    direction="UP" | "DOWN",           # 최상위 필드
    magnitude=float,                   # 변동률 절대값
    sentiment="POSITIVE" | "NEGATIVE",
    properties={
        "date": str,                   # YYYY-MM-DD
        "close": float,                # 종가
        "pct_change": float            # 변동률 (%)
    },
    confidence=1.0
)
```

> **탐지 기준**: `abs(pct_change) >= 5.0%`

#### 출력 Relation: HAS_SIGNAL

```python
# price_parser_agent.py L193-198
Relation(
    subject=agent_name,
    predicate=RelationType.HAS_SIGNAL,
    object=movement.name,
    properties={"date": str}
)
```

---

### 2.6 GeminiPDFParser

**소스 파일**: `src/agents/parsers/pdf_parser_agent.py`  
**입력**: PDF 파일 (IR 자료, 리서치 리포트)

#### LLM 프롬프트 기반 추출

`prompts.yaml`의 `gemini_pdf_parser.kg_extraction` 섹션에 정의된 스키마에 따라 추출.

#### 지원 NodeType (LLM 추출)

| 타입 | 용도 |
|------|------|
| IDM, Fabless, Foundry, Supplier, Organization | Agent Layer |
| Earnings, PriceMovement, Disclosure, Issue | Signal Layer |
| EconomicIndicator | MacroMetric Layer |

#### 지원 RelationType (LLM 추출)

| 타입 | 메타데이터 |
|------|-----------|
| AFFECTS | correlation, sensitivity, lag (필수) |
| TRIGGERED_BY | reasoning (필수), lag, impact_duration |
| SUPPLIES | dependency, is_critical |
| HAS_SIGNAL | importance |

#### 후처리

```python
# pdf_parser_agent.py L178-198
def _normalize_entities(self, kg: KnowledgeGraph):
    """Alias → Standard 이름 변환 및 Ticker 보강"""
```

---

### 2.7 SupplyChainParser

**소스 파일**: `src/agents/parsers/supply_chain_parser.py`  
**입력**: 텍스트 (PDF에서 추출)

#### 출력 Entity

```python
Entity(
    name="기업명",
    type=NodeType.IDM | FABLESS | FOUNDRY | SUPPLIER,
    confidence=0.9
)
```

#### 출력 Relation

```python
Relation(
    subject="공급사",
    predicate=RelationType.SUPPLIES | MANUFACTURES,
    object="수요사 | 제품"
)
```

---

## 3. Neo4j 저장 구조

### 3.1 레이어별 전략

| 레이어 | NodeType | 전략 | Cypher |
|--------|----------|------|--------|
| **Static** | IDM, Fabless, Foundry, Supplier, Organization, EconomicIndicator | `MERGE` | 동일 name 노드 재사용 |
| **Dynamic** | Earnings, PriceMovement, Disclosure, Issue, News, Report | `CREATE` | 항상 새 노드 생성 |

### 3.2 Entity 필드 → Neo4j 속성 매핑

```python
# neo4j_loader.py L106-140
# Entity → Neo4j Node
{
    "name": entity.name,
    "confidence": entity.confidence,
    "direction": entity.direction,        # PriceMovement 전용
    "magnitude": entity.magnitude,        # PriceMovement 전용
    "sentiment": entity.sentiment,        # Signal 전용
    **entity.properties,                  # 모든 properties 병합
    **entity.fundamental_stats            # Agent 전용 재무 통계
}
```

### 3.3 Relation 필드 → Neo4j 속성 매핑

```python
# neo4j_loader.py L172-199
{
    # 공통
    "confidence": r.confidence,
    "source": r.source,
    # AFFECTS
    "correlation": r.correlation,
    "sensitivity": r.sensitivity,
    "lag": r.lag,
    # TRIGGERED_BY
    "reasoning": r.reasoning,
    "impact_duration": r.impact_duration,
    # SUPPLIES
    "dependency": r.dependency,
    "is_critical": r.is_critical,
    "supply_type": r.supply_type,
    # HAS_SIGNAL
    "importance": r.importance,
    "is_official": r.is_official,
    **r.properties
}
```

---

## 4. 데이터 흐름 다이어그램

```
┌───────────────────────────────────────────────────────────────────┐
│                         Raw Data Sources                          │
├─────────────┬─────────────┬─────────────┬─────────────┬──────────┤
│   PDF       │  DART CSV   │  News CSV   │  Price CSV  │  Macro   │
│  Reports    │ (3 files)   │             │ (Ticker별)  │  CSV     │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴────┬─────┘
       │             │             │             │           │
       ▼             ▼             ▼             ▼           ▼
┌────────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐
│  Gemini    │ │   DART    │ │   News    │ │   Price   │ │  Macro   │
│  PDF       │ │  Parser   │ │  Parser   │ │  Parser   │ │  Parser  │
│  Parser    │ │           │ │  (+LLM)   │ │  (SAX)    │ │          │
│  (LLM)     │ │           │ │           │ │           │ │          │
└─────┬──────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └────┬─────┘
      │              │             │             │            │
      │              │             │             │            │
      └──────────────┼─────────────┼─────────────┼────────────┘
                     │             │             │
                     ▼             ▼             ▼
              ┌──────────────────────────────────────┐
              │        KnowledgeGraph (Pydantic)     │
              │  ├── entities: List[Entity]          │
              │  ├── relations: List[Relation]       │
              │  └── metadata: Dict                  │
              └─────────────────┬────────────────────┘
                                │
                                ▼
              ┌──────────────────────────────────────┐
              │           Neo4jKGLoader              │
              │  ├── Static Layer: MERGE             │
              │  ├── Dynamic Layer: CREATE           │
              │  └── link_temporal_signals()         │
              └─────────────────┬────────────────────┘
                                │
                                ▼
              ┌──────────────────────────────────────┐
              │              Neo4j                   │
              │        Hybrid Knowledge Graph        │
              │                                      │
              │  (Agent)─[HAS_SIGNAL]→(Signal)       │
              │  (EconomicIndicator)─[AFFECTS]→(Agent)│
              │  (Agent)─[SUPPLIES]→(Agent)          │
              │  (Signal)─[TRIGGERED_BY]→(Signal)    │
              └──────────────────────────────────────┘
```

---

## 5. 버전 히스토리

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2025-12-23 | 초기 문서 작성 (실제 코드 기반) |
