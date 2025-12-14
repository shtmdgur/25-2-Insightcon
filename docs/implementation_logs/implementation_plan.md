# 금융 Knowledge Graph RAG 시스템 v1.0.0 구현 계획

LangGraph 기반 멀티 에이전트 시스템을 금융 특화 Knowledge Graph RAG 시스템으로 고도화합니다.

## User Review Required

> [!IMPORTANT]
> **구현 우선순위 확인 필요**
> 
> 이 계획은 Phase 0부터 Phase 3까지 총 4단계로 구성되어 있습니다. 모든 단계를 한 번에 구현하면 작업량이 많으므로, 먼저 어떤 단계부터 시작할지 확인이 필요합니다.
> 
> **추천 순서:**
> 1. **Phase 0** (Foundation) - 기반 구조 설정
> 2. **Phase 1** (Knowledge Graph Update) - 핵심 기능
> 3. **Phase 2** (Multi-Agent Intelligence) - 고급 기능
> 4. **Phase 3** (Robustness) - 안정화

> [!WARNING]
> **Breaking Changes**
> 
> 다음 변경사항은 기존 코드의 동작을 변경합니다:
> - `ReportState` 스키마 확장 (새로운 필드 추가)
> - LLM 모델명 변경 (`gemini-2.5-flash-lite` → `gemini-2.5-flash`, `gemini-3-pro-preview` 추가)
> - 노드 간 데이터 흐름 변경 (Debate 에이전트 추가)

## Architecture Overview

### Knowledge Graph 이중 레이어 설계

본 시스템은 **정적 KG**와 **동적 KG**의 이중 구조로 데이터를 관리합니다.

#### 핵심 분류 기준

| 분류 | 정적 KG | 동적 KG |
|------|---------|---------|
| **노드 타입** | Company, Product, Technology, Person | Metric, Event, Trend, TimeSeries |
| **시간 속성** | 불필요/생성일만 | **필수** (date, period) |
| **변화 빈도** | 낮음 (연 1~2회) | 높음 (일/주/월) |
| **주입 전략** | `MERGE` (UPSERT) | `CREATE` (시계열 생성) |

#### 구현 위치

- **분류 로직**: `src/dataflows/parsers/gemini_pdf.py::classify_entity_layer()`
- **정적 주입**: `src/dataflows/neo4j_loader.py::_upsert_static_entity()`
- **동적 주입**: `src/dataflows/neo4j_loader.py::_create_dynamic_entity()`
- **Time-decay**: `src/utils/time_decay.py::calculate_time_decay()`

#### 예시

```python
# 정적: Company 노드 (MERGE)
MERGE (n:Company {id: "005930"})
SET n.name = "삼성전자", n.updated_at = datetime()

# 동적: Metric 노드 (CREATE, period 포함)
CREATE (m:Metric {
    id: "Revenue_005930_2024Q4",
    period: "2024Q4",
    value: 77780000000000
})
```

**자세한 내용**: `docs/11_시스템_고도화_계획.md` - "Knowledge Graph 이중 레이어 아키텍처" 섹션 참조

---

### Phase 0: Foundation (Parser & Ontology)

기본 인프라를 구축하고 설정을 중앙화합니다.

---

#### [NEW] [llm_config.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/utils/llm_config.py)

**목적**: LLM 모델 선택 전략을 중앙에서 관리

Quick/Deep 모델 매핑을 정의하고 Batch API 설정을 포함합니다.

```python
# Quick 모델: gemini-2.5-flash (빠르고 저렴)
# Deep 모델: gemini-3-pro-preview (복잡한 추론)
# Batch API 활용: 비용 50% 절감
```

---

#### [NEW] [parser_interface.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/dataflows/parser_interface.py)

**목적**: Vendor-agnostic Parser Interface 및 Fallback 메커니즘

Primary parser 실패 시 자동으로 Secondary/Fallback parser로 전환합니다.

```python
# Primary: VLM (Gemini Vision)
# Secondary: PyMuPDF (텍스트 추출)
# Fallback: OCR (Tesseract)
```

---

#### [NEW] [gemini_files.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/utils/gemini_files.py)

**목적**: Gemini Files API 통합 (대용량 PDF 효율 처리)

Files API를 사용하여 Base64 인코딩 없이 URI 기반 처리를 구현합니다.

---

#### [NEW] [vlm.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/dataflows/parsers/vlm.py)

**목적**: VLM Parser (Media-First Strategy)

PDF 차트와 이미지를 분석하여 텍스트로 변환합니다.

---

#### [MODIFY] [state.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/pipeline/state.py)

**변경사항**: `ReportState` 확장

새로운 필드 추가:
- `parsed_text`: PDF 파싱 결과
- `file_uri`: Gemini Files API URI
- `extracted_charts`: VLM 차트 분석 결과
- `news_events`: 뉴스 이벤트 목록
- `fundamental_analysis`, `trend_analysis`, `event_analysis`: Analyst 결과
- `bull_argument`, `bear_argument`, `synthesis_verdict`: Debate 결과
- `debate_turn_count`, `retry_count`: 루프 제어
- `critical_paths`: Provenance 추적

---

### Phase 1: Knowledge Graph Update

정확한 엔티티 추출과 시계열 데이터 통합을 구현합니다.

---

#### [NEW] [nodes.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/models/nodes.py)

**목적**: Pydantic 기반 Entity/Relation 모델 정의

Seed Ontology를 Enum으로 강제하여 환각(Hallucination)을 방지합니다.

```python
class NodeType(str, Enum):
    COMPANY = "Company"
    PRODUCT = "Product"
    EVENT = "Event"
    METRIC = "Metric"
    TREND = "Trend"

class RelationType(str, Enum):
    COMPETITOR_OF = "COMPETITOR_OF"
    SUPPLIER_OF = "SUPPLIER_OF"
    AFFECTS = "AFFECTS"
    HAS_METRIC = "HAS_METRIC"
```

---

#### [MODIFY] [kg_construction.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/kg_construction.py)

**변경사항**: Multi-Agent Orchestrator로 전면 리팩토링

기존 텍스트 → KG 추출 로직을 제거하고, 다음 기능으로 재설계:

**새로운 역할**:
1. **데이터 소스 자동 스캔** (`_scan_data_sources`)
2. **Parser Agent 오케스트레이션** (`_orchestrate_parsers`)
3. **JSON 수집 및 병합** (`_collect_json_files`, `_merge_and_refine`)
4. **Entity 정규화** (EntityNormalizer 통합)
5. **Neo4j 주입** (`_load_to_neo4j`)
6. **결과 리포트 생성** (`_generate_report`)

**Sub-Agents 관리**:
```python
class KGConstructionAgent:
    def __init__(self):
        # Parser Agents
        self.pdf_parser_agent = PDFParserAgent()  # 완료 ✅
        self.price_parser_agent = PriceParserAgent()  # 구현 예정
        self.dart_parser_agent = DARTParserAgent()  # 구현 예정
        
        # 유틸리티
        self.merger = KGMerger()
        self.normalizer = EntityNormalizer()
        self.loader = Neo4jKGLoader()
```

**Main API**:
```python
def construct_knowledge_graph(
    data_sources: Optional[Dict] = None,
    auto_scan: bool = True
) -> Dict
```

---

#### [NEW] [pdf_parser_agent.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/parsers/pdf_parser_agent.py)

**목적**: PDF 파싱 전담 Sub-Agent (GeminiPDFParser 래핑)

배치 처리 및 에러 핸들링을 담당합니다.

---

#### [NEW] [price_parser_agent.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/parsers/price_parser_agent.py)

**목적**: 주가 CSV 파싱 Sub-Agent

시계열 데이터를 Neo4j에 직접 주입하거나 JSON으로 저장합니다.

---

#### [NEW] [dart_parser_agent.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/parsers/dart_parser_agent.py)

**목적**: DART 공시 CSV 파싱 Sub-Agent

복잡한 이벤트 관계를 추출하여 JSON으로 저장합니다.

---

#### [MODIFY] [neo4j_client.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/utils/neo4j_client.py)

**변경사항**: 속성 매핑 강화 및 새로운 메서드 추가

`inject_subgraph` 메서드를 추가하여 복잡한 서브그래프 주입을 지원합니다.

---

#### [NEW] [entity_normalizer.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/utils/entity_normalizer.py)

**목적**: 엔티티 정규화 (Entity Linking)

"삼성", "삼성전자", "Samsung" → 단일 노드로 통합합니다.

---

#### [NEW] [time_series_processor.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/utils/time_series_processor.py)

**목적**: SAX 기반 시계열 패턴 분석

주가 데이터를 패턴으로 변환하여 Neo4j에 저장합니다.

---

#### [NEW] [event_extractor.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/utils/event_extractor.py)

**목적**: 뉴스에서 이벤트 추출 및 Neo4j 저장

Time-decay 함수를 사용하여 최근 이벤트에 더 높은 가중치를 부여합니다.

---

### Phase 2: Intelligence Upgrade (Multi-Agent)

Analyst 에이전트 세분화 및 Debate 메커니즘을 구현합니다.

---

#### [NEW] [prompts.yaml](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/templates/prompts.yaml)

**목적**: 프롬프트를 코드에서 분리하여 관리

YAML 형식으로 프롬프트 템플릿을 정의합니다.

---

#### [NEW] [fundamentals_analyst.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/analysts/fundamentals_analyst.py)

**목적**: 재무 데이터 분석 에이전트

매출, 영업이익, 부채 등을 분석합니다.

---

#### [NEW] [trend_analyst.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/analysts/trend_analyst.py)

**목적**: 시계열 패턴(SAX) 분석 에이전트

주가 추세와 수급 패턴을 분석합니다.

---

#### [NEW] [event_analyst.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/analysts/event_analyst.py)

**목적**: 이벤트 임팩트 분석 에이전트

뉴스와 이벤트의 영향력을 평가합니다.

---

#### [NEW] [bull_agent.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/debate/bull_agent.py)

**목적**: 긍정적 관점(Bull) 에이전트

투자 기회와 강점을 강조합니다.

---

#### [NEW] [bear_agent.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/debate/bear_agent.py)

**목적**: 부정적 관점(Bear) 에이전트

리스크와 약점을 강조합니다.

---

#### [NEW] [synthesizer.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/debate/synthesizer.py)

**목적**: 변증법적 통합 에이전트

Bull/Bear 주장을 통합하여 최종 판단을 내립니다.

---

#### [MODIFY] [graph.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/pipeline/graph.py)

**변경사항**: LangGraph Flow 재구성

Analysts (병렬) → Bull/Bear Debate (순차, 최대 3라운드) → Synthesizer 흐름을 구현합니다.

---

#### [MODIFY] [nodes.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/pipeline/nodes.py)

**변경사항**: 새로운 노드 래퍼 추가

Analysts, Debate 에이전트를 위한 노드 함수를 추가합니다.

---

#### [MODIFY] [quality_check.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/agents/quality_check.py)

**변경사항**: Fact-checking 및 Relevance Scoring 추가

추출된 Triplet을 원본 문서와 대조하여 검증합니다.

---

#### [NEW] [multi_hop_graphrag.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/pipeline/multi_hop_graphrag.py)

**목적**: Multi-hop Retrieval 구현

그래프 탐색을 통해 간접적인 관계까지 검색합니다.

---

### Phase 3: Robustness & Validation

에러 핸들링과 무한 루프 방지를 구현합니다.

---

#### [NEW] [retry_handler.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/utils/retry_handler.py)

**목적**: Tenacity 기반 Retry Decorator

LLM API 오류 시 자동 재시도를 수행합니다.

---

#### [MODIFY] [graph.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/pipeline/graph.py)

**변경사항**: Loop Control 로직 추가

`retry_count`와 `debate_turn_count`를 체크하여 무한 루프를 방지합니다.

---

## Verification Plan

### Automated Tests

#### Phase 0 Tests

```bash
# Config Setup 테스트
poetry run pytest tests/unit/test_llm_config.py -v

# Parser Fallback 테스트
poetry run pytest tests/unit/test_parser_interface.py -v

# Files API 통합 테스트
poetry run pytest tests/integration/test_gemini_files.py -v

# VLM Parser 테스트
poetry run pytest tests/integration/test_vlm_parser.py -v

# State 정의 테스트 (Pydantic validation)
poetry run pytest tests/unit/test_state.py -v
```

#### Phase 1 Tests

```bash
# Pydantic Models 검증
poetry run pytest tests/unit/test_nodes.py -v

# KG Construction 테스트 (Mock LLM)
poetry run pytest tests/unit/test_kg_construction.py -v

# Batch API Job 테스트
poetry run pytest tests/integration/test_batch_job.py -v

# Neo4j 주입 테스트 (TestContainer 사용)
poetry run pytest tests/integration/test_neo4j_inject.py -v

# Entity Normalizer 테스트
poetry run pytest tests/unit/test_entity_normalizer.py -v

# End-to-End 테스트 (PDF → Neo4j)
poetry run pytest tests/integration/test_phase1_e2e.py -v
```

#### Phase 2 Tests

```bash
# Prompt Template 렌더링 테스트
poetry run pytest tests/unit/test_prompts.py -v

# Analyst Agents 병렬 실행 테스트
poetry run pytest tests/integration/test_analysts.py -v

# Debate Flow 테스트 (Bull → Bear → Synthesizer)
poetry run pytest tests/integration/test_debate_flow.py -v

# Debate Loop Limit 테스트 (최대 3라운드)
poetry run pytest tests/integration/test_debate_loop.py -v

# Quality Check 검증 테스트
poetry run pytest tests/unit/test_quality_check.py -v

# Multi-hop GraphRAG 테스트
poetry run pytest tests/integration/test_multi_hop.py -v
```

#### Phase 3 Tests

```bash
# Retry Decorator 테스트
poetry run pytest tests/unit/test_retry_handler.py -v

# Loop Control 테스트
poetry run pytest tests/integration/test_loop_control.py -v

# 전체 통합 테스트
poetry run pytest tests/integration/test_full_pipeline.py -v
```

### Manual Verification

#### 1. PDF Parsing 검증

1. `data/test/sample_report.pdf` 파일 준비
2. VLM Parser 실행:
   ```bash
   poetry run python scripts/test_vlm_parser.py data/test/sample_report.pdf
   ```
3. 출력된 `parsed_text`와 `extracted_charts`를 확인
4. 차트의 수치가 PDF와 일치하는지 수동 검증

#### 2. Neo4j 데이터 검증

1. Neo4j Browser에서 데이터 확인:
   ```cypher
   MATCH (n) RETURN n LIMIT 100
   ```
2. 중복 엔티티가 있는지 확인:
   ```cypher
   MATCH (n:Company)
   WITH n.name as name, collect(n) as nodes
   WHERE size(nodes) > 1
   RETURN name, nodes
   ```
3. 엔티티 정규화가 제대로 되었는지 확인

#### 3. Debate 품질 검증

1. 샘플 질의 실행:
   ```bash
   poetry run python scripts/run_query.py "삼성전자와 SK하이닉스 중 어느 종목이 더 유망한가?"
   ```
2. 생성된 `final_report`에서 다음 항목 확인:
   - Bull/Bear 주장이 균형있게 제시되었는가?
   - Synthesizer가 양측 주장을 통합했는가?
   - 근거(`critical_paths`)가 명확히 제시되었는가?

#### 4. Hallucination Check

1. 최종 리포트에서 숫자나 사실 확인
2. Neo4j에서 해당 데이터 조회:
   ```cypher
   MATCH (c:Company {name: "삼성전자"})-[:HAS_METRIC]->(m:Metric)
   RETURN m
   ```
3. 리포트의 숫자와 Neo4j 데이터가 일치하는지 확인
4. 없는 사실을 지어내지 않았는지 검증

---

## 추가 고려사항

### 의존성 설치

모든 Phase의 구현을 위해 `pyproject.toml`에 다음 패키지가 이미 정의되어 있습니다:
- `pymupdf4llm`, `google-generativeai` (Phase 0)
- `fuzzywuzzy`, `saxpy`, `numpy` (Phase 1)
- `tenacity` (Phase 3)
- `pyvis`, `networkx` (시각화)

### 테스트 파일 생성

각 Phase의 테스트 파일은 계획서를 기반으로 작성해야 합니다. 기존 `test/test_workflow.py`를 참고하여 구조를 유지합니다.

### 단계별 커밋

각 Step(예: 0.1 완료) 완료 시마다 커밋하여 추적성을 확보합니다.
