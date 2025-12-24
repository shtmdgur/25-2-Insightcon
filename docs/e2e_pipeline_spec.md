# E2E 파이프라인 최종 명세서

> **Version**: 1.0  
> **Date**: 2025-12-24  
> **Status**: ✅ 구현 완료

---

## 1. 시스템 개요

반도체 산업 분석 AI 시스템. Knowledge Graph 기반 변증법 토론을 통해 투자 의견 리포트를 생성합니다.

```
[Raw Data] → [Parser Agents] → [KnowledgeGraph JSON] → [Neo4j] → [Debate Workflow] → [Report]
     │             │                    │                 │              │              │
   PDF/CSV     6개 파서            768차원 임베딩      Vector Index    3라운드 토론    Markdown/PDF
```

---

## 2. 데이터 흐름

### 2.1 KG 구축 단계

| 단계 | 컴포넌트 | 입력 | 출력 |
|-----|---------|-----|------|
| 1 | `KGConstructionAgent` | `data/raw/*` | 파서 오케스트레이션 |
| 2 | `PDFParserAgent` | PDF 파일 | `*_kg.json` |
| 3 | `NewsParserAgent` | 뉴스 CSV | `*_kg.json` |
| 4 | `KGMerger` | 개별 JSON | 통합 KG |
| 5 | `Neo4jKGLoader` | 통합 KG | Neo4j 주입 |

### 2.2 Debate 단계

| 단계 | 컴포넌트 | 입력 | 출력 |
|-----|---------|-----|------|
| 1 | `initialize_debate` | ReportState | debate_state 초기화 |
| 2 | `BullAgent.argue()` x3 | state + opponent_arg | Bull 논지 |
| 3 | `BearAgent.argue()` x3 | state + opponent_arg | Bear 논지 |
| 4 | `JudgeAgent.judge()` | 토론 이력 | 판결 JSON |
| 5 | `SynthesizerAgent.synthesize()` | 판결 + 토론 | 최종 리포트 |
| 6 | `ValidatorAgent.validate()` | 리포트 | pass/fail |

---

## 3. 핵심 컴포넌트 명세

### 3.1 임베딩

| 항목 | 값 |
|-----|-----|
| **모델** | `gemini-embedding-001` |
| **차원** | 768 |
| **생성 시점** | Parser 단계 (PDF/News) |
| **저장 위치** | `entity.embedding` 필드 |

### 3.2 Vector Index

| 인덱스명 | 레이블 | 속성 |
|---------|-------|------|
| `entity_embedding_index` | Issue | embedding |
| `earnings_embedding_index` | Earnings | embedding |
| `pricemovement_embedding_index` | PriceMovement | embedding |
| `disclosure_embedding_index` | Disclosure | embedding |
| `economicindicator_embedding_index` | EconomicIndicator | embedding |

### 3.3 노드 타입 (Schema v3.1)

**정적 레이어 (Agent)**:
- `IDM`, `Fabless`, `Foundry`, `OSAT`, `Supplier`, `Organization`, `ETC`

**동적 레이어 (Signal)**:
- `Earnings`, `PriceMovement`, `Disclosure`, `Issue`

**거시 레이어 (MacroMetric)**:
- `EconomicIndicator`

### 3.4 관계 타입

| 타입 | 설명 | 주요 속성 |
|-----|------|---------|
| `AFFECTS` | 지표→기업 영향 | correlation, sensitivity, lag |
| `TRIGGERED_BY` | 인과 관계 | reasoning, impact |
| `SUPPLIES` | 공급망 | dependency, is_critical, supply_type |
| `HAS_SIGNAL` | 기업↔신호 | importance, is_official |
| `COMPETES_WITH` | 경쟁 | market_segment |
| `PARTNERS_WITH` | 협력 | partnership_type |
| `INVESTS_IN` | 투자 | investment_type, amount |

---

## 4. 서비스 인터페이스

### 4.1 PipelineService

```python
from src.services.pipeline_service import PipelineService

service = PipelineService()
config = service.create_config(
    mode="query_only",      # full, query_only, document_query
    target_company="삼성전자",
    report_type="scan"      # scan, deep
)

result = service.run(config, on_checkpoint=callback)
```

### 4.2 실행 모드

| 모드 | 설명 | KG 구축 | Debate |
|-----|------|--------|--------|
| `FULL` | 전체 파이프라인 | ✅ | ✅ |
| `QUERY_ONLY` | 기존 KG 활용 | ❌ | ✅ |
| `DOCUMENT_QUERY` | 새 문서 + 기존 KG | 부분 | ✅ |

---

## 5. 파일 구조

```
src/
├── agents/
│   ├── base_debate_agent.py   # _vector_search(), _find_impact_paths()
│   ├── bull_agent.py
│   ├── bear_agent.py
│   ├── judge_agent.py
│   ├── synthesizer_agent.py
│   ├── validator_agent.py
│   └── parsers/
│       ├── pdf_parser_agent.py    # 임베딩 생성
│       └── news_parser_agent.py   # 임베딩 생성
├── dataflows/
│   ├── neo4j_loader.py            # _ensure_vector_index()
│   └── kg_merger.py
├── pipeline/
│   ├── debate_workflow.py         # LangGraph 워크플로우
│   └── state.py                   # ReportState 정의
├── services/
│   └── pipeline_service.py        # PipelineService
├── templates/
│   └── prompts.yaml               # 모든 프롬프트 템플릿
└── utils/
    ├── report_exporter.py         # PDF 변환
    └── price_data_loader.py       # Price DB 직접 조회
```

---

## 6. 실행 방법

### 6.1 Vector Index 생성
```bash
poetry run python scripts/manage_vector_index.py --create
```

### 6.2 E2E 테스트
```bash
# 기본 실행
poetry run python test/e2e/test_full_pipeline.py

# KG 구축 스킵
poetry run python test/e2e/test_full_pipeline.py --skip-kg --target "삼성전자"
```

### 6.3 Streamlit 데모
```bash
poetry add streamlit
poetry run streamlit run app/streamlit_demo.py
```

---

## 7. 정합성 체크리스트

### ✅ 스키마 정합성

| 항목 | 상태 | 파일 |
|-----|------|------|
| `ETC` 타입 in RELATION_SCHEMA | ✅ | `nodes.py` |
| `ETC` 타입 in ENTITY_TYPE_PROPERTIES | ✅ | `nodes.py` |
| `ticker` in ReportState | ✅ | `state.py` |
| `impact_paths` in ReportState | ✅ | `state.py` |

### ✅ 임베딩 정합성

| 항목 | 상태 | 파일 |
|-----|------|------|
| PDF Parser 임베딩 | ✅ | `pdf_parser_agent.py` |
| News Parser 임베딩 | ✅ | `news_parser_agent.py` |
| 쿼리 임베딩 (Vector Search) | ✅ | `base_debate_agent.py` |
| 모델명 통일 | ✅ | `gemini-embedding-001` |

### ✅ 워크플로우 정합성

| 항목 | 상태 | 설명 |
|-----|------|------|
| 토론 3라운드 | ✅ | `should_continue()` |
| Judge 통합 | ✅ | 조건부 연결 |
| Validator 통합 | ✅ | 조건부 연결 |
| 상태 누적 | ✅ | debate_state 업데이트 |

### ✅ 프롬프트 정합성

| Agent | 템플릿 위치 | 주요 변수 |
|-------|-----------|---------|
| Bull | `prompts.yaml:L68-149` | ticker, data_context |
| Bear | `prompts.yaml:L153-208` | ticker, data_context |
| Judge | `prompts.yaml:L212-257` | ticker, bull_history, bear_history, critical_paths, market_context |
| Synthesizer | `prompts.yaml:L262-350` | rationale, history, evidence_paths, ticker, decision, score |
| Validator | `prompts.yaml:L640-661` | report_content, context_data |

---

## 8. 의존성

```toml
[tool.poetry.dependencies]
langgraph = ">=1.0.0"
langchain = ">=1.0.0,<2.0.0"
neo4j = ">=5.0.0"
neo4j-graphrag = ">=1.10.0"
google-genai = ">=x.x.x"
weasyprint = ">=x.x.x"  # PDF 출력용 (옵션)
streamlit = ">=x.x.x"   # 데모 앱용 (옵션)
```

---

## 9. 미구현 항목 (Low Priority)

| 항목 | 우선순위 | 비고 |
|-----|---------|-----|
| FastAPI 엔드포인트 | Low | `PipelineService` 연동만 필요 |
| Community Detection | Low | 현재 요구사항 외 |
| 실시간 스트리밍 | Medium | Debate 진행 상황 실시간 표시 |

---

**명세서 완성**: 2025-12-24 14:00 ✅
