# 구현 작업 내역

> **최종 업데이트**: 2025-12-14 (Schema Integration & Data Flow Refactoring 완료)  
> **작업 범위**: Phase 0 (데이터 파싱) + Phase 1 (KG 구축 고도화) + Layer 0.5 (Raw 데이터 파싱)

---

## 📋 목차

- [Phase 0: 데이터 파싱 및 전처리](#phase-0-데이터-파싱-및-전처리)
- [Phase 1: 지식 그래프 구축 고도화](#phase-1-지식-그래프-구축-고도화)
- [Layer 0.5: Raw 데이터 파싱 전략](#layer-05-raw-데이터-파싱-전략)

---

# Phase 0: 데이터 파싱 및 전처리

## 완료된 작업

### 0.1 LLM Config Setup ✅
**파일**: `src/utils/llm_config.py`  
**내용**:
- Quick/Deep 모델 매핑 (gemini-2.5-flash / gemini-3-pro-preview)
- Batch API 설정 (enabled, max_batch_size, polling_interval)
- 작업 유형별 모델 매핑 (`TASK_MODEL_MAPPING`)
- `get_model_config()`, `should_use_batch()`, `get_llm()` 함수

---

### 0.2 Parser Interface ✅
**파일**: `src/dataflows/parser_interface.py`  
**내용**:
- `ParserInterface` 추상 클래스
- `RobustPDFParser` 클래스 (Fallback 메커니즘)
- Primary → Secondary → Fallback 순서 자동 전환
- `ParserStrategy` Enum (PRIMARY, SECONDARY, FALLBACK)

---

### 0.3 Files API Integration ✅
**파일**: `src/utils/gemini_files.py`  
**내용**:
- `GeminiFilesClient` 클래스
- `upload_file()`: 파일 업로드 및 URI 반환
- `get_file_uri()`: 캐시된 URI 조회
- `delete_file()`, `clear_cache()`: 캐시 관리
- 싱글톤 패턴 (`get_gemini_files_client()`)
- 한글 경로 지원 및 MIME 타입 자동 감지

---

### 0.4 Gemini PDF Native Parser ✅ ⭐ **추천 방식**
**파일**: `src/dataflows/parsers/gemini_pdf.py`  
**내용**:
- `GeminiPDFParser` 클래스 - **PDF에서 Knowledge Graph 직접 추출**
- Gemini API Structured Output 활용
- PDF → Knowledge Graph JSON (원스텝 파이프라인)
- Batch API 지원 (`use_batch=True`)
- YAML 기반 프롬프트 관리

**장점**:
- ✅ PDF 전체 문맥 이해
- ✅ 일관성 있는 KG 출력
- ✅ 비용 최적화 (Batch API 50% 절감)

**테스트 결과**:
- 샘플 PDF (6페이지): **154개 엔티티**, **97개 관계** 추출
- Neo4j Aura 그래프 시각화 확인 완료

---

### 0.5 Neo4j Loader ✅
**파일**: `src/dataflows/neo4j_loader.py`  
**내용**:
- `Neo4jKGLoader` 클래스
- `load_knowledge_graph()`: KG를 Neo4j에 **UPSERT 주입**
- `_create_entity()`, `_create_relation()`: MERGE 전략
- `get_graph_stats()`: 그래프 통계 조회
- `load_kg_from_gemini_pdf()`: 전체 파이프라인 함수

**UPSERT 전략 변경사항**:
```python
# 이전: 기존 데이터 삭제 후 재생성
# if clear_existing:
#     session.run("MATCH (n) DETACH DELETE n")

# 현재: MERGE를 통한 데이터 누적 (UPSERT)
query = f"""
MERGE (n:`{entity. label}` {{id: $id}})
SET n.name = $name
SET n += $properties
RETURN n
"""
```

**UPSERT 전략 장점**:
- ✅ 동일한 PDF를 재파싱해도 중복 생성 방지
- ✅ 기존 그래프에 새로운 정보 누적
- ✅ 여러 소스의 데이터를 통합 관리
- ✅ 점진적 KG 구축 가능

---

### 0.6 Graph Schema Models ✅
**파일**: `src/models/graph_schema.py`  
**내용**:
- `NodeLabel` Enum: Company, Product, Metric, Event, Trend, Technology, Person
- `RelationType` Enum: PRODUCES, COMPETES_WITH, SUPPLIES_TO, HAS_METRIC, AFFECTED_BY, DEVELOPS, LEADS
- `Entity`, `Relation`, `KnowledgeGraph` Pydantic 모델
- `get_kg_json_schema()`: Gemini Structured Output용 스키마

---

## 백로그 (향후 옵션)

### VLM Parser (차트 분석 특화)
**파일**: `src/dataflows/parsers/vlm.py`  
**용도**: PDF 차트/그래프 상세 분석 (연구/탐색 단계)  
**현재**: Knowledge Graph 추출은 GeminiPDFParser 사용 권장  
**백로그 사유**: 
- Gemini PDF Parser가 더 정확하고 효율적
- VLM은 차트 세부 분석이 필요한 특수 케이스에만 사용
- Phase 2 이후 필요시 재검토

---

## Phase 0 생성/수정 파일

### 생성된 파일 (9개)
1. `src/utils/llm_config.py`
2. `src/dataflows/__init__.py`
3. `src/dataflows/parsers/__init__.py`
4. `src/dataflows/parser_interface.py`
5. `src/utils/gemini_files.py`
6. **`src/dataflows/parsers/gemini_pdf.py`** ⭐
7. **`src/dataflows/neo4j_loader.py`** ⭐
8. **`src/models/graph_schema.py`** ⭐
9. `src/dataflows/parsers/vlm.py` (백로그)

### 수정된 파일 (2개)
1. `src/pipeline/state.py`
2. `src/utils/llm_config.py` (get_llm 함수 추가)

---

## E2E 데모 및 문서

### 데모 스크립트
1. **`demo_e2e_pipeline.py`** - Phase 0 + Phase 1 통합 파이프라인
   - 옵션 1: VLM Parser → KG Agent → Neo4j (백로그)
   - 옵션 2: Gemini PDF Parser → Neo4j (추천 ⭐)

2. **`demo_phase1_agents.py`** - Phase 1 개별 에이전트 테스트
   - KGConstructionAgent (텍스트 전용)
   - EventExtractor
   - TimeSeriesProcessor

### 문서
1. **`docs/파서_선택_가이드.md`** - GeminiPDFParser vs VLMParser vs KGConstructionAgent 비교
2. **`test/test_phase0.py`** - Phase 0 기능 테스트 스크립트
3. **`test/test_gemini_pdf_neo4j.py`** - Gemini PDF Parser 테스트

---

# Phase 1: 지식 그래프 구축 고도화

## 완료된 작업

### 1.1 Ontology Models ✅
**파일**: `src/models/nodes.py`  
**내용**:
- `NodeType` Enum (Company, Product, Event, Metric, Trend, Financial)
- `RelationType` Enum (COMPETITOR_OF, SUPPLIER_OF, MANUFACTURES 등)
- `Entity`, `Relation`, `KnowledgeGraph` Pydantic 모델
- `ENTITY_TYPE_PROPERTIES` 타입별 속성 정의

---

### 1.2 KG Extract Logic 개선 ✅
**파일**: `src/agents/kg_construction.py` (수정)  
**변경사항**:
- Pydantic `PydanticOutputParser` 사용
- `extract_entities()`: KnowledgeGraph 객체 반환
- `inject_to_neo4j()`: Pydantic 모델 기반 주입
- Seed Ontology 강제 (Enum 사용)
- 관계 추출 개선 (문서에서 명시적으로 언급된 것만)

---

### 1.3 Batch API Job ✅
**파일**: `src/utils/batch_job.py`  
**내용**:
- `BatchJobManager` 클래스
- `create_batch_request_file()`: JSONL 생성
- `submit_batch_job()`: Job 제출 (Placeholder)
- `poll_batch_job()`: 상태 폴링
- `run_batch_job()`: 전체 실행 (생성 → 제출 → 폴링)
- `create_kg_extraction_requests()`: KG 추출용 Batch 요청 생성

---

### 1.4 Neo4j Inject 업데이트 ✅
**파일**: `src/utils/neo4j_client.py` (수정)  
**변경사항**:
- `inject_subgraph()` 메서드 추가
- 복잡한 서브그래프 주입 지원 (nodes + relationships)
- MERGE 전략으로 중복 방지
- 에러 핸들링 및 통계 반환

---

### 1.5 Entity Normalizer ✅
**파일**: `src/utils/entity_normalizer.py`  
**내용**:
- `EntityNormalizer` 클래스
- `normalize_entity()`: 텍스트 → 표준 엔티티 매핑
- `_fuzzy_search()`: Fuzzy Matching (fuzzywuzzy)
- 싱글톤 패턴 (`get_entity_normalizer()`)

---

### 1.6 Time Series Processor ✅
**파일**: `src/utils/time_series_processor.py`  
**내용**:
- `TimeSeriesProcessor` 클래스
- `process_stock_price()`: 주가 → SAX 패턴 변환 및 Neo4j 저장
- `_simple_trend_classification()`: Fallback 트렌드 분류
- `_classify_trend()`: SAX 기반 트렌드 분류 (Upward/Downward/Volatile/Stable)

---

### 1.7 Event Extractor ✅
**파일**: `src/utils/event_extractor.py`  
**내용**:
- `EventExtractor` 클래스
- `extract_events_from_news()`: 뉴스 → 이벤트 추출
- `_save_event_to_neo4j()`: Event 노드 생성 및 AFFECTS 관계 생성
- `_calculate_time_decay()`: Time-decay 가중치 계산 (90일 반감기)

---

### 1.8 Schema Integration & Data Flow Refactoring (New) ✅
**파일**: `src/models/nodes.py`, `src/dataflows/parsers/gemini_pdf.py`, `src/dataflows/kg_merger.py`
**내용**:
- **스키마 통합**: `graph_schema.py`를 `nodes.py`로 통합 (Option A)
  - `NodeType`, `RelationType`을 YAML 프롬프트와 동기화
  - Gemini API 호환 메서드(`to_gemini_dict`/`from_gemini_dict`) 및 JSON 저장/로드 메서드 추가
- **데이터 플로우 개선**: JSON 중간 저장 도입
  - Flow: PDF → Gemini → `nodes.KnowledgeGraph` → JSON 저장(`data/processed/`) → 병합(KGMerger) → Neo4j
- **KGMerger 구현**:
  - 여러 JSON 파일의 KG를 병합하고 중복(Entity/Relation) 제거 로직 구현
- **Neo4j Loader 업데이트**:
  - 통합된 `nodes.py` 스키마 사용
  - JSON 파일 로드 및 병합 후 주입 기능 추가

---

### 1.10 KGConstructionAgent Orchestrator 아키텍처 재설계 ✅
**파일**: `docs/11_시스템_고도화_계획.md`, `docs/12_시스템_설계_명세서.md`, `docs/implementation_logs/implementation_plan.md`
**내용**:
- **Orchestrator 아키텍처 도입**:
  - KGConstructionAgent를 Multi-Agent Orchestrator로 재설계
  - 모든 데이터 소스의 파서를 통합 관리하는 중앙 허브 역할
- **Parser Agent 구조**:
  - PDFParserAgent (완료 ✅) - GeminiPDFParser 래핑
  - PriceParserAgent (구현 예정) - 주가 CSV 파싱
  - DARTParserAgent (구현 예정) - 공시 데이터 파싱
  - MacroParserAgent (구현 예정) - 매크로 지표 파싱
  - NewsParserAgent (구현 예정) - 뉴스 텍스트 파싱
- **핵심 기능**:
  1. 데이터 소스 자동 스캔 (`data/raw/*`)
  2. Parser Agent 선택 및 병렬 실행
  3. JSON 수집 및 병합 (KGMerger)
  4. Entity 정규화 (Entity Normalizer)
  5. Neo4j 주입 및 결과 리포트
- **사용 인터페이스**:
  ```python
  agent = KGConstructionAgent()
  report = agent.construct_knowledge_graph(auto_scan=True)
  ```
- **문서 업데이트**:
  - `orchestrator_architecture.md` 신규 작성
  - `11_시스템_고도화_계획.md` - Parser Agent 아키텍처 섹션 추가
  - `12_시스템_설계_명세서.md` - KGConstructionAgent → Orchestrator로 재정의
  - `implementation_plan.md` - Sub-Agent 리스트 추가
- **Backup 정리**:
  - `demo_e2e_pipeline.py` → `backup/`
  - `demo_phase1_agents.py` → `backup/`
  - Orchestrator가 이 역할들을 통합 수행

---

## Phase 1 생성/수정 파일

### 생성된 파일 (10개)
1. `src/models/__init__.py`
2. `src/models/nodes.py`
3. `src/utils/batch_job.py`
4. `src/utils/entity_normalizer.py`
5. `src/utils/time_series_processor.py`
6. `src/utils/event_extractor.py`
7. `src/dataflows/kg_merger.py`
8. `test/test_integration.py`
9. `test/README.md`
10. `backup/README.md` (New)

### 수정된 파일 (7개)
1. `src/agents/kg_construction.py` (Orchestrator 재설계 예정)
2. `src/utils/neo4j_client.py`
3. `src/dataflows/parsers/gemini_pdf.py`
4. `src/dataflows/neo4j_loader.py`
5. `src/models/nodes.py` (Schema Integration + Gemini API 최적화)
6. `src/templates/prompts.yaml` (Prompt Enhancement)
7. `docs/11_시스템_고도화_계획.md` (Orchestrator Architecture)
8. `docs/12_시스템_설계_명세서.md` (Orchestrator Architecture)
9. `docs/implementation_logs/implementation_plan.md` (Orchestrator Architecture)

---

## 코드 검증 결과 ✅

### 컴파일 테스트
모든 파일이 성공적으로 컴파일되었습니다 (Exit Code: 0)

✅ `src/utils/llm_config.py`  
✅ `src/dataflows/parser_interface.py`  
✅ `src/utils/gemini_files.py`  
✅ `src/dataflows/parsers/vlm.py`  
✅ `src/models/nodes.py`  
✅ `src/agents/kg_construction.py`  
✅ `src/utils/neo4j_client.py`  

### Import 체인 검증
- ✅ Pydantic 모델 → KG Construction 에이전트
- ✅ Neo4j Client → KG Construction 에이전트
- ✅ Parser Interface → VLM Parser
- ✅ Gemini Files API → VLM Parser

### 런타임 의존성
⚠️ 다음 패키지 필요:  
- `google-genai` (Gemini API)  
- `fuzzywuzzy`, `python-Levenshtein` (Entity Normalizer)  
- `saxpy` (Time Series Processor)

→ `pyproject.toml`에 이미 정의되어 있음

---

## 데이터 분류 로직

**현재 (Phase 1)**: 수동 분류

| 입력 타입 | 사용 컴포넌트 | 판단 기준 |
|-----------|---------------|-----------|
| PDF 리포트 | **GeminiPDFParser** ⭐ | Knowledge Graph 추출 |
| 뉴스 기사 | **KGConstructionAgent** | 실시간 텍스트 데이터 |
| 주가 시계열 | **TimeSeriesProcessor** | 수치 배열 + 시간 정보 |

**Phase 2 예정**: LLM 기반 자동 라우터

---

# Layer 0.5: Raw 데이터 파싱 전략

## 📊 수집된 데이터 현황

| 디렉토리 | 내용 | 파일 수 | 데이터 규모 | 주요 컬럼 |
|----------|------|---------|-------------|-----------|
| `data/raw/DART` | 공시 데이터 | 3 CSV | 기업 4개, 공시 3,025건, 재무 92건 | ticker, corp_code, corp_name, revenue, operating_profit |
| `data/raw/reports` | 애널리스트 리포트 | **1,469 PDF** | ~1.5GB (2020-2025) | 증권사 분석 리포트 |
| `data/raw/news` | 뉴스 데이터 | 1 CSV | **7,500건** (3.5MB) | keyword, title, link, date, description |
| `data/raw/price` | 주가 시계열 | 23 CSV | 각 ~5년치 (2020~) | date, open, high, low, close, volume |
| `data/raw/SAX_price` | SAX 패턴 변환 | 23 CSV | 각 ~5년치 | ticker, date, price, sax_symbol, trend, volatility |
| `data/raw/macro` | 거시경제 지표 | 1 CSV | **19,673건** (470KB) | date, value, series (FRED 지표) |
| `data/raw/fund` | 펀더멘탈 데이터 | 3 CSV | 소량 (~2KB) | ticker, marketCap, totalDebt, profitMargins, ROE |
| `data/raw/ir` | IR 자료 | **60 PDF** (6개 기업) | ~50MB | 실적 발표, 지속가능성 보고서, 사업보고서 |

**주요 종목**:
- **한국**: 삼성전자(005930), SK하이닉스(000660), DB하이텍(000990), 한미반도체(091160, 102110)
- **미국**: NVDA, TSM, INTC, AMAT, ASML, LRCX, MU, AVGO
- **지수**: KOSPI, KOSDAQ, S&P500, NASDAQ, Dow
- **환율**: USD/KRW, USD/JPY

---

## 📅 구현 우선순위

| 순서 | 컴포넌트 | 대상 데이터 | 상태 | 예상 시간 |
|------|----------|-------------|------|-----------|
| 1 | PDF Parser | reports (1,469 PDF), ir (60 PDF) | ✅ 완료 | - |
| 2 | CSV Parser | price (23), SAX (23), DART (3) | 🔧 필요 | 1.5일 |
| 3 | News Event Extractor | news (7,500건) | 🔧 필요 | 2일 |
| 4 | SAX TimeSeries | SAX_price (23 CSV) | 🔧 필요 | 0.5일 |
| 5 | Macro/Fund Parser | macro (19,673), fund (3) | 🔧 필요 | 0.5일 |
| 6 | Layer0 통합 Pipeline | 전체 | 🔧 필요 | 1일 |

**총 예상 기간**: 약 5.5일

---

## 💰 비용 추정

- **Gemini Flash (뉴스 이벤트 추출)**: 7,500건 × $0.001 ≈ **$7.5**
- **Gemini Flash (PDF Batch - reports)**: 1,469개 × $0.01 (Batch 50% 할인) ≈ **$7~15**
- **Gemini Flash (IR 문서)**: 60개 × $0.01 ≈ **$0.6**

**총 예상 비용**: **$15~23**

---

## 📈 전체 통계

### Phase 0 + Phase 1 통합
- **생성 파일**: 15개
- **수정 파일**: 4개
- **컴파일 성공**: 100%
- **데모 스크립트**: 2개
- **테스트 스크립트**: 2개

### 핵심 성과
- ✅ Gemini PDF Parser 기반 원스텝 KG 구축
- ✅ Neo4j UPSERT 전략 (데이터 누적 방식)
- ✅ Pydantic 기반 타입 안정성 및 Seed Ontology 강제화
- ✅ Batch API 준비 (비용 50% 절감)
- ✅ Entity Normalization, Time Series, Event Extraction 완료
- ✅ E2E 테스트 가능한 데모 제공

---

## 다음 단계

**Layer 0.5 완료 후** → **Phase 2: 에이전트 지능 강화**

**Phase 2 계획**:
- Entity Linking & Normalization (Master Data 기반)
- 시계열 데이터 통합 (SAX-DM, Time-decay)
- Multi-hop Retrieval (Graph Traversal)
- Batch API 완전 구현 (`use_batch=True`)
- Quality Check Agent 강화

