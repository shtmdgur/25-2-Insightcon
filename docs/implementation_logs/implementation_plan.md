# 금융 특화 Knowledge Graph RAG 시스템 구현 계획서

> **작성일**: 2025-12-20  
> **기준 버전**: Phase 1 (온톨로지 구축) 완료 → Phase 2-4 (고도화) 실행  
> **현재 상태**: Phase 1 완료 (KG Orchestration 안정화, T-Box 2.0 온톨로지 구현 완료)

---

## 📋 목차

1. [현재 상태 체크](#현재-상태-체크)
2. [Phase 2: 에이전트 지능 강화](#phase-2-에이전트-지능-강화)
3. [Phase 3: 설명 가능성 및 가시화](#phase-3-설명-가능성-및-가시화)
4. [Phase 4: RAG 시스템 통합](#phase-4-rag-시스템-통합)
5. [주의사항 및 제약조건](#주의사항-및-제약조건)
6. [우선순위 및 로드맵](#우선순위-및-로드맵)

---

## 현재 상태 체크

### ✅ 완료된 작업 (Phase 0-1)

#### Phase 0: 데이터 파싱 및 전처리
- ✅ **GeminiPDFParser**: PDF → Knowledge Graph 직접 추출 (Gemini 2.5 Flash)
- ✅ **Parser Agent 아키텍처**: 6개 Parser Agent 구현 완료
  - PDFParserAgent, PriceParserAgent, DARTParserAgent
  - NewsParserAgent, MacroParserAgent, FundParserAgent
- ✅ **KGConstructionAgent Orchestrator**: 자동 스캔 및 병렬 처리
- ✅ **Neo4j UPSERT 전략**: 정적/동적 레이어 이중 구조
- ✅ **Entity Normalizer**: Fuzzy Matching, Ticker 정규화
- ✅ **Time Series Processor**: SAX 패턴 변환, Trend 분류
- ✅ **Event Extractor**: 뉴스 이벤트 추출, Time-Decay 가중치

#### Phase 1: 온톨로지 고도화
- ✅ **T-Box 2.0 온톨로지**: 58개 클래스, 21개 관계 (BFO 기반)
  - `Observation`, `TemporalRegion` 추가 (Time-Stitching)
  - Time-Scoped ID 전략 (Context Collapse 해결)
  - Property Extraction 강제화
- ✅ **Schema Validation**: `verify_semiconductor_schema.py` 검증 완료
- ✅ **Data Integration**: 276 entities, 75 relations 병합 성공

### 🟡 현재 제약사항

> **중요**: 온톨로지 스키마(T/R-Box, properties)는 **확장 중**이며 추후 수정 가능성이 있음

**제약조건**:
- **NodeType Enum**: 58개 클래스 정의 완료 (`src/models/nodes.py`)
- **RelationType Enum**: 21개 관계 정의 완료
- **ENTITY_TYPE_PROPERTIES**: 타입별 속성 정의 (하드코딩)

**영향 범위**:
- `src/parsers/gemini_pdf.py` (프롬프트 업데이트 필요)
- `src/dataflows/neo4j_loader.py` (레이어 분류 로직)
- `src/templates/prompts.yaml` (LLM 지시사항)

**대응 전략**:
1. **온톨로지 변경 시 자동 반영**:
   - Enum 변경 → 프롬프트 자동 업데이트 스크립트 작성
   - Property 정의를 YAML로 외부화 고려 (Phase 2.x)
2. **하위 호환성 유지**:
   - Legacy 관계명 (`COMPETITOR_OF`, `SUPPLIER_OF` 등) 매핑 계속 지원
   - 점진적 마이그레이션 전략

---

## Phase 2: 에이전트 지능 강화

> **우선순위**: 🔴 Critical  
> **목표**: GraphRAG 검색 품질 향상 및 에이전트 추론 능력 고도화  
> **예상 기간**: 3-4주

---

### 2.1 Quality Check Agent 강화

#### 목적
- KGP 추출 단계에서 Self-Correction
- GraphRAG 검색 결과의 Relevance Scoring
- Query Rewriting 트리거

#### 구현 작업

**2.1.1 Self-Correction at Ingestion**

- **파일**: `src/agents/quality_check.py` (기존 파일 확장)
- **필요 컴포넌트**:
  - `LLM Client` (src/utils/llm_client.py) - 이미 존재
  - `ParserConfig` (src/config/parser_config.py) - 이미 존재

**구현 내용**:
```python
class QualityCheckAgent:
    def verify_extraction(self, source_text: str, extracted_triplet: dict) -> bool:
        """
        추출된 Triplet이 원문과 일치하는지 검증
        
        Args:
            source_text: 원본 문서 청크
            extracted_triplet: {"subject": "...", "predicate": "...", "object": "..."}
        
        Returns:
            bool: 검증 통과 여부
        """
        # Deep LLM 사용 (품질 검증)
        
    def score_subgraph_relevance(self, query: str, subgraph: dict) -> float:
        """
        검색된 서브그래프의 relevance 점수 (0.0 ~ 1.0)
        
        임계값 0.6 미만 시 Query Rewrite 트리거
        """
```

**활용 지점**:
- `KGConstructionAgent.construct_knowledge_graph()` 호출 후
- GraphRAG Query 결과 평가 후

**주의사항**:
- **LLM 비용**: Deep LLM (Gemini 3.0 Pro) 사용 → 비용 증가
- **대응**: 샘플링 전략 (10% random sampling) 또는 신뢰도 낮은 triplet만 검증

**예상 소요 시간**: 2-3일

---

**2.1.2 캐시 무효화 시스템**

- **파일**: `src/utils/graphrag_cache.py` (신규 생성)

**구현 내용**:
```python
class GraphRAGCache:
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._graph_version: int = 0  # Graph 버전 추적
    
    def get(self, cache_key: str, graph_version: int) -> Optional[Dict]:
        """그래프 버전 확인 후 캐시 조회"""
        
    def invalidate_all(self):
        """그래프 업데이트 시 버전 증가"""
        self._graph_version += 1
```

**수정 파일**:
1. `src/agents/kg_construction.py`:
   - `construct_knowledge_graph()` 완료 후 `cache.invalidate_all()` 호출
2. `src/pipeline/nodes.py`:
   - `graphrag_query_node()`: 캐시 버전 확인 로직 추가

**주의사항**:
- **메모리 관리**: LRU eviction (max_size=100)
- **분산 환경**: Redis 등 외부 캐시 고려 (Phase 4)

**예상 소요 시간**: 1-2일

---

### 2.2 Multi-hop Retrieval

#### 목적
- 단순 1-hop 검색을 넘어 2-hop, 3-hop 경로 탐색
- LLM 기반 관련성 필터링으로 불필요한 경로 제거

#### 구현 작업

**2.2.1 MultiHopGraphRAG 클래스 구현**

- **파일**: `src/pipeline/graphrag_query.py` (신규 생성)
- **필요 컴포넌트**:
  - `Neo4jClient` (src/utils/neo4j_client.py) - 이미 존재
  - `LLMClient` - 이미 존재

**구현 내용**:
```python
class MultiHopGraphRAG:
    def multi_hop_search(self, query: str, max_hops: int = 2) -> List[List[Dict]]:
        """
        1-Hop 확장 → LLM 필터링 → 2-Hop 확장
        
        Returns:
            List of graph paths (each path = list of nodes+edges)
        """
        # 1. Anchor Entity 추출 (LLM or NER)
        # 2. 1-Hop Cypher Query
        # 3. Path Filtering (LLM 기반 relevance)
        # 4. 2-Hop 확장 (필요 시)
        
    def _expand_1hop(self, anchors: List[str]) -> List[Dict]:
        """Cypher: MATCH (anchor)-[r]-(neighbor) RETURN ..."""
        
    def _filter_irrelevant_paths(self, paths: List, query: str) -> List:
        """LLM으로 query 관련 없는 경로 제거"""
```

**Cypher Query 예시**:
```cypher
// 1-Hop
MATCH (anchor {name: $anchor_name})-[r]-(neighbor)
RETURN anchor, type(r) AS rel_type, neighbor

// 2-Hop
MATCH path = (anchor {name: $anchor})-[*1..2]-(target)
WHERE target.type IN ['Event', 'Metric']  // 목적 타입 필터링
RETURN path
LIMIT 50
```

**활용 지점**:
- `src/pipeline/nodes.py` → `graphrag_query_node()` 교체

**주의사항**:
- **성능 이슈**: 2-hop 이상은 조합 폭발 위험
  - **대응**: `LIMIT 50` 강제, 목적 노드 타입 제한
- **LLM 호출 빈도**: 각 경로마다 relevance 판단 → Batch 처리 필요
  - **Batch Prompt**: "다음 10개 경로 중 질문과 관련 있는 것을 선택하라"

**예상 소요 시간**: 3-4일

**테스트 시나리오**:
```python
# Query: "SK하이닉스의 주요 경쟁사와 그들의 최근 이슈는?"
# Expected: SK하이닉스 → COMPETITOR_OF → 삼성전자 → AFFECTED_BY → Event(HBM3 양산)
```

---

### 2.3 변증법적 토론 에이전트

#### 목적
- Bull/Bear 양측 관점 제시
- Synthesizer가 중재하여 최종 판단
- 한화투자증권 스타일 리포트 생성

#### 구현 작업

**2.3.1 Bull/Bear/Synthesizer Agent 구현**

- **파일**: 
  - `src/agents/dialectical_agents.py` (신규 생성)
  - `src/agents/bull_agent.py` (신규)
  - `src/agents/bear_agent.py` (신규)
  - `src/agents/synthesizer_agent.py` (신규)

**구현 내용**:

**BullAgent** (긍정론):
```python
class BullAgent:
    def argue(self, query: str, data: dict) -> dict:
        """
        온톨로지 데이터 기반 긍정 논거 생성
        
        Returns:
            {"argument": "...", "key_points": ["논거1", "논거2", ...]}
        """
        # 1. 긍정적 요소 추출 (Event, Trend, Metric)
        positive_events = self._extract_positive_events(data)
        upward_trends = self._extract_upward_trends(data)
        
        # 2. LLM Prompt (Quick 모델)
        prompt = f"""
        당신은 낙관적 투자 분석가입니다.
        
        데이터:
        - 긍정 이벤트: {positive_events}
        - 상승 트렌드: {upward_trends}
        
        **핵심**: 위 데이터를 근거로 3~5개의 구체적 논거를 생성하세요.
        
        JSON 형식:
        {{"argument": "상세 주장", "key_points": [...]}}
        """
```

**BearAgent** (부정론):
- 구조는 BullAgent와 동일
- 부정적 Event, 하락 Trend, Risk 지표 추출

**SynthesizerAgent** (중재자):
```python
class SynthesizerAgent:
    def synthesize(
        self, 
        query: str,
        bull_result: dict,
        bear_result: dict,
        data: dict,
        graph_paths: Optional[List] = None
    ) -> str:
        """
        한화투자증권 스타일 종합 리포트 생성 (Markdown)
        
        System Prompt:
        - 톤 앤 매너: 객관적, 신뢰감 있는 증권사 애널리스트 어조
        - 변증법적 통합: 양측 의견 중재 및 최종 결론
        - Graph Provenance: 경로 기반 근거 명시
        
        Returns:
            Markdown 형식 리포트
        """
```

**시스템 프롬프트** (한화투자증권 스타일):
- 핵심 요약 (Key Takeaways) 3-4개
- Bullish View / Bearish View / Synthesizer's Verdict
- Knowledge Graph 근거 추적 (Provenance)
- 밸류에이션 및 투자 전략

**활용 지점**:
- `src/pipeline/workflow.py`: 새로운 노드 추가
  - `debate_bull` → `debate_bear` → `debate_synthesizer`

**주의사항**:
- **온톨로지 의존성**: Event/Trend/Metric 노드가 충분히 추출되어야 논거 생성 가능
  - **대응**: 데이터 부족 시 fallback 메시지 ("데이터 부족으로 논거 생성 불가")
- **LLM 모델 선택**:
  - Bull/Bear: Quick 모델 (비용 절감)
  - Synthesizer: Deep 모델 (품질 확보)

**예상 소요 시간**: 4-5일

---

**2.3.2 LangGraph 워크플로우 통합**

- **파일**: `src/pipeline/workflow.py` (기존 파일 확장)

**구현 내용**:
```python
from langgraph.graph import StateGraph, END

def create_debate_workflow() -> StateGraph:
    workflow = StateGraph(ReportState)
    
    # 노드 추가
    workflow.add_node("debate_bull", bull_agent_node)
    workflow.add_node("debate_bear", bear_agent_node)
    workflow.add_node("debate_synthesizer", synthesizer_node)
    
    # 엣지 연결
    workflow.add_edge("sector_analyst", "debate_bull")
    workflow.add_edge("company_analyst", "debate_bull")
    workflow.add_edge("debate_bull", "debate_bear")
    workflow.add_edge("debate_bear", "debate_synthesizer")
    workflow.add_edge("debate_synthesizer", "report_generation")
    
    return workflow.compile()
```

**State 확장** (`src/pipeline/state.py`):
```python
class ReportState(TypedDict):
    # ... 기존 필드
    bull_argument: Optional[str]
    bear_argument: Optional[str]
    synthesis: Optional[str]
    debate_confidence: Optional[float]
```

**예상 소요 시간**: 2일

---

### 2.4 Analyst Team 세분화

#### 목적
- 단일 거대 Analyst 대신 전문 에이전트로 역할 분담
- GraphRAG 데이터를 각 관점에서 해석

#### 구현 작업

**2.4.1 Fundamentals Analyst (재무 분석)**

- **파일**: `src/agents/fundamentals_analyst.py` (신규)

**역할**:
- FinancialMetric, FinancialReport 노드 분석
- YoY 성장률, 밸류에이션 지표 계산

**구현**:
```python
class FundamentalsAnalyst:
    def analyze(self, company_ticker: str, data: dict) -> str:
        """
        재무 데이터 분석
        
        Returns:
            Markdown 형식 섹션 ("## 재무 분석")
        """
        # FinancialMetric 노드 조회
        # YoY, QoQ 성장률 계산
        # P/E, P/B 밴드 분석
```

---

**2.4.2 Technical Analyst (시계열 분석)**

- **파일**: `src/agents/technical_analyst.py` (신규)

**역할**:
- Trend, SAX 패턴 해석
- 가격 반등/하락 시점 예측

**구현**:
```python
class TechnicalAnalyst:
    def analyze(self, company_ticker: str, sax_data: dict) -> str:
        """
        SAX 패턴 분석
        
        Returns:
            Markdown 형식 섹션 ("## 기술적 분석")
        """
        # SAX 패턴 해석 ("abcde" → 상승 패턴)
        # Volatility 판단
        # 지지선/저항선 추정 (간단 로직)
```

---

**2.4.3 Event Impact Analyst (이벤트 분석)**

- **파일**: `src/agents/event_analyst.py` (신규)

**역할**:
- Event 노드 분석
- Time-Decay 가중치 적용
- 이벤트 영향도 스코어링

**구현**:
```python
class EventImpactAnalyst:
    def analyze(self, company_ticker: str, event_data: List[dict]) -> str:
        """
        최근 이벤트 영향도 분석
        
        Returns:
            Markdown 형식 섹션 ("## 이벤트 분석")
        """
        # Event 노드 → AFFECTS → Company 관계 조회
        # Time-Decay 가중치 적용
        # 종합 영향도 스코어 계산
```

---

**2.4.4 통합 Orchestration**

- **파일**: `src/pipeline/workflow.py` (기존 파일 확장)

**수정 내용**:
```python
# 기존: sector_analyst, company_analyst (거대 단일 에이전트)
# 신규: 3개 전문 에이전트 병렬 실행

workflow.add_node("fundamentals_analyst", fundamentals_analyst_node)
workflow.add_node("technical_analyst", technical_analyst_node)
workflow.add_node("event_analyst", event_analyst_node)

# 병렬 실행 후 토론 에이전트로 결과 전달
workflow.add_edge("fundamentals_analyst", "debate_bull")
workflow.add_edge("technical_analyst", "debate_bull")
workflow.add_edge("event_analyst", "debate_bull")
```

**주의사항**:
- **데이터 가용성**: 각 에이전트는 해당 노드가 없으면 "데이터 없음" 반환
  - 예: Event 노드 0개 → EventAnalyst는 "분석 불가" 메시지
- **병렬 처리**: LangGraph `map_reduce` 패턴 활용

**예상 소요 시간**: 3-4일 (3개 에이전트 + 통합)

---

### 2.5 Retry 및 Circuit Breaker

#### 목적
- LLM/Neo4j 호출 실패 시 자동 재시도
- 연속 실패 시 Circuit Breaker로 시스템 보호

#### 구현 작업

**2.5.1 Retry Decorator**

- **파일**: `src/utils/retry_handler.py` (신규)

**구현 내용**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
def call_llm_with_retry(llm, prompt):
    """LLM 호출 (자동 재시도)"""
    response = llm.invoke(prompt)
    return response.content
```

**적용 지점**:
- `src/agents/*.py`: 모든 LLM 호출부
- `src/utils/neo4j_client.py`: Neo4j 쿼리 메서드

**예상 소요 시간**: 1일

---

**2.5.2 Circuit Breaker 패턴**

- **파일**: `src/utils/circuit_breaker.py` (신규)

**구현 내용**:
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.state = CircuitState.CLOSED  # CLOSED/OPEN/HALF_OPEN
        
    def call(self, func, *args, **kwargs):
        """함수 호출 (Circuit Breaker 적용)"""
        # OPEN 상태 → 즉시 에러 반환
        # CLOSED/HALF_OPEN → 함수 실행 시도
        # 실패 누적 → OPEN 전환
```

**전역 인스턴스**:
```python
_neo4j_circuit = CircuitBreaker(failure_threshold=5, timeout=60)
_llm_circuit = CircuitBreaker(failure_threshold=3, timeout=30)
```

**예상 소요 시간**: 1-2일

---

## Phase 3: 설명 가능성 및 가시화

> **우선순위**: 🟠 High  
> **목표**: 리포트 근거 추적 및 시각화, PDF Export  
> **예상 기간**: 2-3주

---

### 3.1 Provenance 추적

#### 목적
- 리포트의 모든 주장에 대해 Graph Path 기반 근거 제시
- 원문 문서 링크 제공

#### 구현 작업

**3.1.1 ExplainableReportGenerator**

- **파일**: `src/agents/explainable_report.py` (신규)

**구현 내용**:
```python
class ExplainableReportGenerator:
    def generate_report_with_provenance(
        self, 
        synthesis: str,
        graph_paths: List[List[Dict]],
        source_documents: List[str]
    ) -> str:
        """
        근거 추적 가능한 리포트 생성
        
        Returns:
            Markdown 리포트 (Provenance 섹션 포함)
        """
        # 1. Graph Path 포맷팅
        formatted_paths = self._format_graph_path(graph_paths)
        
        # 2. 원문 링크 포맷팅
        formatted_sources = self._format_sources(source_documents)
        
        # 3. 템플릿 렌더링
        return f"""
## Knowledge Graph 근거 추적

### 핵심 연결 고리
{formatted_paths}

### 참조 문서
{formatted_sources}
        """
    
    def _format_graph_path(self, paths: List) -> str:
        """
        Example:
        **[Path 1]**: `(삼성전자) --[COMPETITOR_OF]--> (SK하이닉스) --[AFFECTS]--> (HBM3 양산)`
        """
```

**활용 지점**:
- `synthesizer_node()`: 리포트 생성 후 Provenance 섹션 추가

**예상 소요 시간**: 2-3일

---

### 3.2 Graph 시각화

#### 목적
- PyVis/NetworkX로 서브그래프 시각화
- HTML 파일 출력 및 리포트 임베딩

#### 구현 작업

**3.2.1 GraphVisualizer 클래스**

- **파일**: `src/utils/graph_visualizer.py` (신규)

**구현 내용**:
```python
from pyvis.network import Network
import networkx as nx

class GraphVisualizer:
    def visualize_subgraph(
        self, 
        nodes: List[Dict],
        edges: List[Dict],
        output_path: str
    ) -> str:
        """
        PyVis HTML 생성
        
        Returns:
            HTML 파일 경로
        """
        net = Network(height="600px", width="100%")
        
        for node in nodes:
            net.add_node(
                node['name'],
                label=node['name'],
                size=node.get('importance', 20),
                color=self._get_color_by_type(node['type'])
            )
        
        for edge in edges:
            net.add_edge(
                edge['source'],
                edge['target'],
                width=edge['weight'] * 5,
                title=edge['type']
            )
        
        net.save_graph(output_path)
        return output_path
```

**활용 지점**:
- `synthesizer_node()`: 리포트 생성 시 서브그래프 HTML 생성

**주의사항**:
- **대용량 그래프**: 50 nodes 이상 시 렌더링 느림
  - **대응**: Top-K 노드만 선택 (Centrality 기준)

**예상 소요 시간**: 2일

---

### 3.3 PDF Export

#### 목적
- Markdown 리포트를 한화투자증권 스타일 PDF로 변환

#### 구현 작업

**3.3.1 HanwhaSecuritiesReportFormatter**

- **파일**: `src/export/hanwha_formatter.py` (신규)

**구현 내용**:
```python
from jinja2 import Template

class HanwhaSecuritiesReportFormatter:
    def generate_report(
        self,
        company_name: str,
        bull_argument: str,
        bear_argument: str,
        synthesis: str,
        analysis_data: dict
    ) -> str:
        """
        한화투자증권 스타일 Markdown 리포트 생성
        
        Template:
        - 헤더 (섹터, 투자의견, 목표주가)
        - 핵심 요약 (Key Takeaways)
        - Bull/Bear/Synthesis
        - Provenance
        - 밸류에이션
        """
        template = Template(open("templates/hanwha_template.md").read())
        return template.render(
            company_name=company_name,
            bull_argument=bull_argument,
            bear_argument=bear_argument,
            synthesis=synthesis,
            analysis_data=analysis_data
        )
```

---

**3.3.2 PDFExporter**

- **파일**: `src/export/pdf_exporter.py` (신규)

**구현 내용**:
```python
from weasyprint import HTML, CSS

class PDFExporter:
    def export_to_pdf(self, markdown_text: str, output_path: str):
        """Markdown → PDF 변환 (WeasyPrint)"""
        # 1. Markdown → HTML 변환
        from markdown import markdown
        html_text = markdown(markdown_text)
        
        # 2. CSS 스타일 적용 (한화투자증권 브랜딩)
        css = CSS(string="""
        @page {
            margin: 2cm;
        }
        h1 {
            color: #00539F;  /* 한화 블루 */
        }
        """)
        
        # 3. PDF 생성
        HTML(string=html_text).write_pdf(output_path, stylesheets=[css])
```

**예상 소요 시간**: 2-3일

---

## Phase 4: RAG 시스템 통합

> **우선순위**: 🟡 Medium  
> **목표**: 대화형 인터페이스 및 컨텍스트 기반 질의응답  
> **예상 기간**: 3-4주 (선택적)

---

### 4.1 FastAPI 백엔드

#### 구현 작업

**4.1.1 API 서버 구축**

- **파일**: `src/api/main.py` (신규)

**구현 내용**:
```python
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/run-analysis")
async def run_analysis(query: str, target_companies: List[str]):
    """리포트 생성 트리거"""
    # KGConstructionAgent → Debate → Report
    
@app.post("/upload")
async def upload_file(file: UploadFile):
    """PDF/CSV 업로드 및 자동 파싱"""
    # GeminiPDFParser 또는 CSV Parser 실행
    
@app.post("/chat")
async def rag_chat(query: str, context: Optional[str] = None):
    """KG 기반 질의응답"""
    # MultiHopGraphRAG 실행 → LLM 답변 생성
    
@app.get("/stream")
async def stream_thoughts(query: str):
    """SSE (Server-Sent Events) 스트리밍"""
    # 에이전트 실행 과정 실시간 전송
```

**예상 소요 시간**: 4-5일

---

### 4.2 프론트엔드 대시보드

#### 구현 작업 (선택적)

**4.2.1 React/Next.js 대시보드**

**화면 구성**:
1. **Dashboard**: 전체 분석 현황
2. **File Manager**: 문서 업로드 및 파싱 상태
3. **Report Viewer**: 생성된 리포트 조회
4. **Graph Explorer**: PyVis 그래프 인터랙티브 탐색
5. **Chat Interface**: RAG 기반 질의응답

**예상 소요 시간**: 2-3주 (프론트엔드 개발자 필요)

---

## 주의사항 및 제약조건

### 온톨로지 변경 대응

**현재 상황**:
- `NodeType` Enum, `RelationType` Enum은 하드코딩
- 수정 시 영향 파일: `nodes.py`, `prompts.yaml`, `neo4j_loader.py`

**대응 방안**:
1. **자동 프롬프트 생성**:
   ```python
   # scripts/sync_ontology_to_prompt.py
   def generate_prompt_from_enum():
       node_types = [e.value for e in NodeType]
       relation_types = [r.value for r in RelationType]
       # prompts.yaml 자동 업데이트
   ```

2. **Property 외부화** (Phase 2.x):
   - `ENTITY_TYPE_PROPERTIES`를 YAML로 관리
   - `src/config/ontology.yaml` 생성

**예상 소요 시간**: 1-2일

---

### 데이터 품질 이슈

**문제**:
- Parser Agent가 노드/관계를 충분히 추출하지 못할 경우 Analyst 동작 불가

**대응**:
- **Fallback 메시지**: 데이터 부족 시 "분석 불가" 명시
- **테스트 데이터**: 충분한 샘플 PDF/CSV로 검증

---

### LLM 비용 관리

**비용 증가 지점**:
- Quality Check (Deep LLM)
- Multi-hop Filtering (각 경로마다 LLM 호출)
- Debate (Bull/Bear/Synthesizer)

**대응**:
- **Batch API**: 가능한 작업은 Batch로 묶기 (50% 절감)
- **Sampling**: Quality Check는 10% random sampling
- **Quick 모델 우선**: 가능한 곳은 Gemini 2.5 Flash 사용

**예상 비용** (Phase 2-3 전체):
- PDF 1,500개 Batch: ~$15
- Quality Check (10% sampling): ~$2
- Debate (100회 실행): ~$5  
**총 예상**: **$22-30**

---

## 우선순위 및 로드맵

### 🔴 Critical (1-2주)

| 순서 | 작업 | 예상 시간 | 의존성 |
|:---:|:---|:---:|:---|
| 1 | Quality Check Agent 강화 (2.1) | 3-4일 | 없음 |
| 2 | 캐시 무효화 시스템 (2.1.2) | 1-2일 | 없음 |
| 3 | Retry/Circuit Breaker (2.5) | 2-3일 | 없음 |

### 🟠 High (3-4주)

| 순서 | 작업 | 예상 시간 | 의존성 |
|:---:|:---|:---:|:---|
| 4 | Multi-hop Retrieval (2.2) | 3-4일 | (1) 완료 |
| 5 | 변증법 토론 에이전트 (2.3) | 4-5일 | (4) 완료 |
| 6 | LangGraph 통합 (2.3.2) | 2일 | (5) 완료 |
| 7 | Analyst 세분화 (2.4) | 3-4일 | 없음 |

### 🟡 Medium (5-7주)

| 순서 | 작업 | 예상 시간 | 의존성 |
|:---:|:---|:---:|:---|
| 8 | Provenance 추적 (3.1) | 2-3일 | (6) 완료 |
| 9 | Graph 시각화 (3.2) | 2일 | 없음 |
| 10 | PDF Export (3.3) | 2-3일 | (8) 완료 |
| 11 | FastAPI 백엔드 (4.1) | 4-5일 | (10) 완료 |

### 🟢 Low (선택적)

| 순서 | 작업 | 예상 시간 | 의존성 |
|:---:|:---|:---:|:---|
| 12 | 프론트엔드 대시보드 (4.2) | 2-3주 | (11) 완료 |

---

## 다음 단계

### 즉시 착수 (이번 주)
1. **Quality Check Agent 강화** (2.1.1)
   - `src/agents/quality_check.py` 수정
   - Deep LLM 통합
2. **캐시 무효화 시스템** (2.1.2)
   - `src/utils/graphrag_cache.py` 생성

### 다음 주
3. **Multi-hop Retrieval** (2.2)
   - `src/pipeline/graphrag_query.py` 생성
   - Cypher 쿼리 최적화
4. **Retry/Circuit Breaker** (2.5)
   - `src/utils/retry_handler.py`, `circuit_breaker.py` 생성

### 3주차 이후
5. **변증법 토론 에이전트** (2.3)
   - Bull/Bear/Synthesizer 구현
   - LangGraph 워크플로우 통합

---

## 참고 자료

### 코드베이스
- `src/models/nodes.py`: 온톨로지 정의
- `src/agents/kg_construction.py`: Orchestrator
- `src/dataflows/neo4j_loader.py`: 이중 레이어 전략
- `src/templates/prompts.yaml`: LLM 프롬프트

### 문서
- `docs/03_design/11_시스템_고도화_계획.md`: 전체 시스템 계획
- `docs/implementation_logs/sh_implementation_log.md`: 작업 이력
- `docs/01_theory/`: 온톨로지, GraphRAG 이론

### 외부 참고
- **TradingAgents**: 변증법적 토론 에이전트 참고
- **FinDKG**: Seed 온톨로지 강제화 전략
- **Neo4j GraphRAG**: Multi-hop 검색 패턴

---

**작성자**: AI Copilot  
**최종 업데이트**: 2025-12-20  
**버전**: v1.0
