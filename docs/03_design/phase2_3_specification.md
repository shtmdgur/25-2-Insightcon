# Phase 2.3 변증법 토론 에이전트 아키텍처 명세

> **작성일**: 2025-12-21  
> **참고**: TradingAgents 코드베이스 분석 기반  
> **목표**: 스파게티 코드 방지, 2.4 확장 최소 비용

---

## 📐 설계 원칙

### 1. 계층 분리 (Layered Architecture)

```
┌─────────────────────────────────────┐
│  Workflow Layer (LangGraph)         │  ← 실행 흐름 관리
├─────────────────────────────────────┤
│  Agent Layer (Business Logic)       │  ← 에이전트 로직(순수)
├─────────────────────────────────────┤
│  Data Access Layer (GraphRAG)       │  ← 데이터 접근 추상화
├─────────────────────────────────────┤
│  State Layer (TypedDict)            │  ← 중앙 상태 관리
└─────────────────────────────────────┘
```

**원칙**:
- **Agent는 State만 읽고 씀** → GraphRAG 직접 호출 금지
- **Workflow가 Agent 호출** → Agent가 다른 Agent 호출 금지
- **State is Immutable pattern** → 직접 수정 금지, 복사 후 반환

### 2. TradingAgents 패턴 차용

**TradingAgents의 장점**:
1. ✅ **State 중심 설계**: `InvestDebateState`로 토론 상태 캡슐화
2. ✅ **재귀 토론 제어**: `count` 필드로 무한 루프 방지
3. ✅ **History 누적**: `bull_history`, `bear_history` 분리 저장

**우리가 차용할 것**:
- State 구조 (history, count)
- 조건부 분기 패턴 (`should_continue_debate`)
- Manager 패턴 (Synthesizer = Research Manager 역할)

---

## 🗂️ State 설계 (기존 확장)

### ReportState 확장 (src/pipeline/state.py)

```python
class DebateState(TypedDict):
    """변증법 토론 상태 (TradingAgents InvestDebateState 참고)"""
    
    # 토론 이력
    bull_history: str  # Bull 주장 누적 (Markdown)
    bear_history: str  # Bear 주장 누적
    full_history: str  # 전체 토론 흐름 (타임라인)
    
    # 현재 라운드
    current_bull_arg: Optional[str]  # 현재 라운드 Bull 주장
    current_bear_arg: Optional[str]  # 현재 라운드 Bear 주장
    
    # 제어
    debate_count: int  # 토론 라운드 (max 3)
    should_continue: bool  # 토론 계속 여부

class GraphRAGResult(TypedDict):
    """GraphRAG 검색 결과 표준 포맷 (Mock/Real 공통)"""
    subgraph: Dict[str, Any]  # {"nodes": [...], "edges": [...]}
    text_context: str  # 노드 설명 요약 텍스트
    metadata: Dict[str, Any]  # {"query": ..., "execution_time": ...}

class ReportState(TypedDict):
    # ... 기존 필드 유지
    
    # ===== Phase 2.3: Debate 추가 =====
    debate_state: Optional[DebateState]  # 토론 상태 (통합 관리)
    synthesis_report: Optional[str]  # Synthesizer 최종 리포트
    graphrag_results: Optional[GraphRAGResult]  # 구조화된 검색 결과 ⭐
    
    # ===== Phase 2.4: Analyst 추가 (확장용) =====
    analyst_reports: Optional[Dict[str, str]]  # {"fundamentals": "...", "technical": "...", "event": "..."}
```

**설계 이유**:
- `DebateState` **분리** → 토론 관련 필드만 캡슐화
- `debate_count` → 무한 루프 방지 (TradingAgents 패턴)
- `analyst_reports` → 2.4 추가 시 기존 코드 변경 최소화

---

## 🤖 Agent 인터페이스 정의

### 1. BaseDebateAgent (추상 클래스)

```python
# src/agents/base_debate_agent.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseDebateAgent(ABC):
    """
    변증법 토론 에이전트 베이스 클래스 (Cognitive Filtering 적용)
    
    설계 철학:
    - Rule-based Filtering 지양 (단순 키워드 매칭 X)
    - Broad Search & Cognitive Filtering 지향:
      1. 범용 경로 탐색 (Broad Search) -> 모든 가능성 열어둠
      2. 인지적 필터링 (Cognitive Filtering) -> LLM이 맥락에 맞춰 선별
    """
    
    def __init__(self, llm, neo4j_connection=None, strategy: str = "deep"):
        self.llm = llm
        self.neo4j = neo4j_connection  # [Hybrid Access] Direct Cypher용
        self.strategy = strategy
    
    @abstractmethod
    def argue(
        self, 
        state: Dict[str, Any], 
        opponent_last_arg: Optional[str] = None
    ) -> Dict[str, str]:
        """
        주장 생성 (Cognitive Filtering 방식)
        
        Process:
        1. Context & Logic Access:
           - GraphRAG Subgraph (문맥)
           - Direct Cypher -> `_find_impact_paths` (범용 인과 경로)
        
        2. Cognitive Filtering (LLM):
           - 수집된 다양한 경로 중 자신의 관점(Role)에 부합하는 경로 식별.
           - 예: Bull은 "투자->성장" 경로 선택, Bear는 "투자->비용" 경로 선택.
        
        3. Argument Generation:
           - 선택된 경로를 근거(Provenance)로 제시하며 논리 구성.
        """
        pass
    
    def _extract_data_from_state(self, state: Dict) -> Dict:
        """
        State에서 데이터 추출 (Hybrid Access)
        1. GraphRAG 결과 파싱
        2. 범용 영향 경로(Impact Paths) 탐색 결과 병합
        """
        return {
            "events": self._extract_events(state),
            "trends": self._extract_trends(state),
            "metrics": self._extract_metrics(state),
            # [New] 호재/악재 구분 없이 모든 연관 경로 추출 -> LLM이 필터링
            "impact_paths": self._find_impact_paths(state) 
        }

    def _find_impact_paths(self, target: Any) -> List[Dict]:
        """
        [Broad Search]
        기업에 영향을 주는 모든 '사건'과 '변화'의 경로를 범용적으로 추출
        (Bull/Bear 구분 없이 탐색)
        """
        # Cypher: (Event|Trend)-[*1..2]-(Company)
        pass
    
    def _extract_events(self, state: Dict) -> List[Dict]:
        """
        이벤트 추출 (단순 수집, 판단은 LLM에게 위임)
        """
        graphrag = state.get("graphrag_results", {})
        nodes = graphrag.get("subgraph", {}).get("nodes", [])
        
        events = [
            n for n in nodes
            if n.get("type") == "Event"
        ]
        return events

    def _extract_trends(self, state: Dict) -> List[Dict]:
        """
        트렌드 추출 (단순 수집, 판단은 LLM에게 위임)
        """
        graphrag = state.get("graphrag_results", {})
        nodes = graphrag.get("subgraph", {}).get("nodes", [])
        
        trends = [
            n for n in nodes
            if n.get("type") == "Trend"
        ]
        return trends

    def _extract_metrics(self, state: Dict) -> List[Dict]:
        """
        재무 지표 추출 (단순 수집, 판단은 LLM에게 위임)
        """
        # Placeholder for actual metric extraction logic
        return []
    
    def _build_prompt(self, query: str, data: Dict, opponent_arg: Optional[str], history: str) -> str:
        """
        프롬프트 생성 (YAML 템플릿 활용)
        
        Note:
        - 하드코딩된 문자열 대신 `src/templates/prompts.yaml`을 참조합니다.
        - Cognitive Filtering 지침은 YAML 파일 내 `instruction` 필드에 정의되어 있습니다.
        """
        # 1. 템플릿 로드 (self.prompts는 __init__에서 로드됨)
        agent_key = self.role.lower()  # "bull" or "bear"
        template = self.prompts.get("debate_agents", {}).get(agent_key, {}).get("instruction", "")
        
        # 2. 데이터 컨텍스트 포맷팅 (Cognitive Filtering용 Impact Paths 포함)
        data_context = self._format_data_context(data)
        
        # 3. 템플릿 채우기
        prompt = template.format(
            ticker=query,
            data_context=data_context,
            # 추가적으로 history, opponent_arg 등은 
            # YAML 구조에 따라 유동적으로 삽입 (또는 별도 섹션으로 결합)
        )
        
        # [옵션] 상대방 반박 및 히스토리 추가 (YAML 구조에 따라 달라질 수 있음)
        if opponent_arg:
            prompt += f"\n\n[상대방의 주장]\n{opponent_arg}\n반박 논리를 포함하세요."
            
        return prompt

    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        LLM 응답 파싱 (예: JSON 또는 특정 포맷)
        """
        # 실제 구현에서는 JSON 파싱 또는 정규식 매칭이 필요합니다.
        return {"argument": response}

```

**설계 포인트**:
- `argue()` 메서드 **단일 책임**: State → 주장
- GraphRAG 접근은 `_extract_data_from_state`로 캡슐화
- **2.4 확장**: `_extract_data_from_state`만 수정하면 Analyst 연동

---

### 2. BullAgent 구현

```python
# src/agents/bull_agent.py

from .base_debate_agent import BaseDebateAgent
from typing import Dict, Any, Optional

class BullAgent(BaseDebateAgent):
    """
    강세론 에이전트 (High-Conviction Alpha Seeker)
    
    전략:
    - **Variant View**: 시장이 간과한 가치(Dislocation)를 찾아 Re-rating 주장
    - **5가지 Cognitive Filtering 프레임워크**:
      1. Variant View (Market Misperception)
      2. Top-line Expansion (P & Q Logic)
      3. Operating Leverage (J-Curve Profitability)
      4. Strategic Moat & Reflexivity
      5. Capital Efficiency & Allocation
    - **Catalyst-Driven**: 주가를 움직일 구체적 이벤트와 타임라인 연결
    """
    
    def argue(self, state: Dict[str, Any], opponent_last_arg: Optional[str] = None) -> Dict[str, str]:
        # 1. Broad Search & 하이브리드 데이터 추출
        data = self._extract_data_from_state(state)
        data["query"] = state.get("query", "")
        
        # 2. 프롬프팅 (YAML 지침 + 인지적 필터링)
        # src/templates/prompts.yaml의 bull 섹션에서 로드
        prompt = self._build_prompt(
            query=state.get("query", ""),
            data=data,  # impact_paths 포함
            opponent_arg=opponent_last_arg,
            history=state.get("debate_state", {}).get("bull_history", "")
        )
        
        # 3. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 4. 응답 파싱
        return self._parse_response(response)
    
    def _extract_events(self, state: Dict) -> List[Dict]:
        """
        이벤트 추출 (단순 수집, 판단은 LLM에게 위임)
        *기존의 _is_positive 같은 Rule-based 필터링 제거*
        """
        # GraphRAG에서 Event 노드만 리스트업
        graphrag = state.get("graphrag_results", {})
        nodes = graphrag.get("subgraph", {}).get("nodes", [])
        
        events = [
            n for n in nodes
            if n.get("type") == "Event"
        ]
        return events
```

---

### 3. BearAgent 구현

```python
# src/agents/bear_agent.py

from .base_debate_agent import BaseDebateAgent
from typing import Dict, Any, Optional, List

class BearAgent(BaseDebateAgent):
    """
    약세론 에이전트 (Forensic Risk Analyst)
    
    전략:
    - **Skeptical Bear**: 과도한 낙관론을 경계하며 Hidden Risks & Overvaluation 경고
    - **5가지 Cognitive Filtering 프레임워크**:
      1. Margin Squeeze (Profitability Risk) - 외형은 커지지만 내실 악화
      2. Cycle Peak & Inventory Glut - 사이클 고점 징후, 재고 축적 위험
      3. Macro & Geopolitical Headwinds - 통제 불가능한 외부 충격
      4. Governance & Allocation Risk - 오너 리스크, 무리한 Capex/M&A
      5. Valuation Trap - 과도한 프리미엄, 호재 선반영(Priced-in)
    - **Downside Risk 강조**: Bull Catalyst가 실패했을 때의 하방 위험 부각
    """
    
    def argue(self, state: Dict[str, Any], opponent_last_arg: Optional[str] = None) -> Dict[str, str]:
        # 1. Broad Search & 하이브리드 데이터 추출
        data = self._extract_data_from_state(state)
        data["query"] = state.get("query", "")
        
        # 2. 프롬프팅 (YAML 지침 + 인지적 필터링)
        # src/templates/prompts.yaml의 bear 섹션에서 로드
        prompt = self._build_prompt(
            query=state.get("query", ""),
            data=data,
            opponent_arg=opponent_last_arg,
            history=state.get("debate_state", {}).get("bear_history", "")
        )
        
        # 3. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 4. 응답 파싱
        return self._parse_response(response)

    def _extract_events(self, state: Dict) -> List[Dict]:
        """
        이벤트 추출 (단순 수집, 판단은 LLM에게 위임)
        """
        graphrag = state.get("graphrag_results", {})
        nodes = graphrag.get("subgraph", {}).get("nodes", [])
        
        events = [
            n for n in nodes
            if n.get("type") == "Event"
        ]
        return events
```

---

### 4. SynthesizerAgent 구현

```python
# src/agents/synthesizer_agent.py

class SynthesizerAgent:
    """
    중재자 에이전트 (TradingAgents Research Manager 참고)
    
    역할:
    - Bull/Bear 토론 종합
    - 한화투자증권 스타일 리포트 생성
    - Provenance (Graph 경로) 명시
    """
    
    def __init__(self, llm, strategy: str = "deep"):
        """Deep LLM 사용 (품질 우선)"""
        self.llm = llm
        self.strategy = strategy
    
    def synthesize(
        self,
        state: Dict,
        bull_history: str,
        bear_history: str
    ) -> str:
        """
        변증법 통합
        
        Returns:
            Markdown 리포트
        """
        # 1. Prompt 구성 (한화투자증권 스타일)
        prompt = self._build_synthesis_prompt(
            query=state["query"],
            bull_arguments=bull_history,
            bear_arguments=bear_history,
            graph_paths=state.get("critical_paths", [])
        )
        
        # 2. Deep LLM 호출
        report = self.llm.invoke(prompt)
        
        # 3. Markdown 포맷팅 검증
        return self._format_report(report)
    
    def _build_synthesis_prompt(self, ...) -> str:
        """
        System Prompt 예시:
        
        당신은 한화투자증권의 시니어 애널리스트입니다.
        
        [톤 앤 매너]
        - 객관적, 신뢰감 있는 어조
        - 근거 기반 분석 (Knowledge Graph 경로 명시)
        - 양측 의견 균형 있게 반영
        
        [구조]
        # Executive Summary
        - 핵심 요약 (3-4개)
        
        ## Bullish View
        - Bull 주요 논거 정리
        
        ## Bearish View
        - Bear 주요 논거 정리
        
        ## Investment Thesis (종합 판단)
        - 변증법적 통합
        - Knowledge Graph 근거: [경로]
        
        ## Recommendation
        - Buy/Hold/Sell
        - Target Price (선택적)
        """
        # ...
```

---

## 🔄 LangGraph 워크플로우 통합

### Workflow 정의 (src/pipeline/debate_workflow.py)

```python
from langgraph.graph import StateGraph, END
from src.pipeline.state import ReportState, DebateState

def create_debate_workflow(
    bull_agent: BullAgent,
    bear_agent: BearAgent,
    synthesizer_agent: SynthesizerAgent
) -> StateGraph:
    """
    변증법 토론 워크플로우
    
    TradingAgents 패턴:
    - Bull → Bear → (조건부 반복) → Synthesizer
    """
    
    workflow = StateGraph(ReportState)
    
    # === 노드 정의 ===
    
    def debate_init_node(state: ReportState) -> ReportState:
        """토론 상태 초기화"""
        state["debate_state"] = DebateState(
            bull_history="",
            bear_history="",
            full_history="",
            current_bull_arg=None,
            current_bear_arg=None,
            debate_count=0,
            should_continue=True
        )
        return state
    
    def bull_node(state: ReportState) -> ReportState:
        """Bull 에이전트 실행"""
        debate = state["debate_state"]
        
        # Bear 이전 주장 가져오기 (반박용)
        opponent_last = debate["current_bear_arg"]
        
        # Bull 주장 생성
        result = bull_agent.argue(state, opponent_last)
        
        # State 업데이트 (Immutable 패턴)
        new_debate = debate.copy()
        new_debate["current_bull_arg"] = result["argument"]
        new_debate["bull_history"] += f"\n\n## Round {debate['debate_count'] + 1}\n{result['argument']}"
        new_debate["full_history"] += f"\n[Bull] {result['argument']}"
        
        state["debate_state"] = new_debate
        return state
    
    def bear_node(state: ReportState) -> ReportState:
        """Bear 에이전트 실행"""
        debate = state["debate_state"]
        opponent_last = debate["current_bull_arg"]
        
        result = bear_agent.argue(state, opponent_last)
        
        new_debate = debate.copy()
        new_debate["current_bear_arg"] = result["argument"]
        new_debate["bear_history"] += f"\n\n## Round {debate['debate_count'] + 1}\n{result['argument']}"
        new_debate["full_history"] += f"\n[Bear] {result['argument']}"
        new_debate["debate_count"] += 1  # 라운드 증가
        
        state["debate_state"] = new_debate
        return state
    
    def should_continue_debate(state: ReportState) -> str:
        """
        토론 계속 여부 판단 (Quick 모델 활용 ⭐)
        
        조기 종료(Early Exit) 조건:
        1. 라운드 제한: debate_count > 3 (Hard Limit)
        2. 내용 충분성: Quick 모델이 "더 이상 새로운 논거가 없다"고 판단할 때
        3. 합의 도달: 양측의 주장이 하나로 수렴될 때
        """
        debate = state["debate_state"]
        
        # 1. Hard Limit 체크
        if debate["debate_count"] > 3:
            return "synthesize"
        
        # 2. Early Exit 체크 (Quick 모델)
        # prompt: "지금까지의 토론 내용을 보고, 새로운 논의가 필요한지 아니면 충분한지 판단하세요."
        # result = judge_llm_quick.invoke(debate["full_history"])
        # if result.is_sufficient:
        #     return "synthesize"
        
        return "continue"
    
    def synthesizer_node(state: ReportState) -> ReportState:
        """Synthesizer 실행"""
        debate = state["debate_state"]
        
        report = synthesizer_agent.synthesize(
            state,
            bull_history=debate["bull_history"],
            bear_history=debate["bear_history"]
        )
        
        state["synthesis_report"] = report
        return state
    
    # === 그래프 구성 ===
    
    workflow.add_node("debate_init", debate_init_node)
    workflow.add_node("bull", bull_node)
    workflow.add_node("bear", bear_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # 시작
    workflow.set_entry_point("debate_init")
    
    # Bull → Bear
    workflow.add_edge("debate_init", "bull")
    workflow.add_edge("bull", "bear")
    
    # Bear → 조건부 분기
    workflow.add_conditional_edges(
        "bear",
        should_continue_debate,
        {
            "continue": "bull",  # 반복
            "synthesize": "synthesizer"  # 종료
        }
    )
    
    # Synthesizer → END
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()
```

**핵심 패턴**:
- `should_continue_debate`: TradingAgents `conditional_logic` 패턴
- Immutable State: `.copy()` 후 수정
- 명확한 진입/종료 지점

---

## 🔌 기존 프레임워크와의 통합

### 1. src/pipeline/workflow.py 확장

```python
# 기존 워크플로우에 Debate 노드 추가

from src.pipeline.debate_workflow import create_debate_workflow

def create_main_workflow():
    workflow = StateGraph(ReportState)
    
    # ... 기존 노드들 (Parser, GraphRAG 등)
    
    # === Phase 2.3: Debate 추가 ===
    debate_graph = create_debate_workflow(bull, bear, synthesizer)
    
    # 서브그래프로 통합
    workflow.add_node("debate", debate_graph)
    
    # GraphRAG → Debate
    workflow.add_edge("graphrag_query", "debate")
    
    # Debate → Report Generation
    workflow.add_edge("debate", "report_generation")
    
    # ...
```

### 2. Phase 2.4 확장 지점

**Analyst Team 추가 시**:

```python
# 변경 전 (Phase 2.3)
workflow.add_edge("graphrag_query", "debate")

# 변경 후 (Phase 2.4)
workflow.add_node("analysts", create_analyst_workflow())  # 병렬 실행
workflow.add_edge("graphrag_query", "analysts")
workflow.add_edge("analysts", "debate")  # Analyst → Debate

# Agent 코드 변경: 없음!
# BaseDebateAgent._extract_data_from_state()만 수정:
def _extract_data_from_state(self, state: Dict) -> Dict:
    # 우선순위 1: Analyst 리포트
    if state.get("analyst_reports"):
        return self._parse_analyst_reports(state["analyst_reports"])
    
    # Fallback: GraphRAG 직접 접근 (Phase 2.3 방식)
    return self._parse_graphrag(state["graphrag_results"])
```

**변경 범위**: **단 1개 메서드** (`_extract_data_from_state`)

---

## 📁 파일 구조

```
src/
├── agents/
│   ├── base_debate_agent.py       # 추상 클래스 ⭐
│   ├── bull_agent.py               # Bull 구현
│   ├── bear_agent.py               # Bear 구현
│   ├── synthesizer_agent.py        # Synthesizer 구현
│   └── (Phase 2.4)
│       ├── fundamentals_analyst.py
│       ├── technical_analyst.py
│       └── event_analyst.py
├── pipeline/
│   ├── state.py                    # State 정의 (확장) ⭐
│   ├── debate_workflow.py          # Debate 워크플로우 ⭐
│   ├── analyst_workflow.py         # (Phase 2.4)
│   └── workflow.py                 # 메인 통합 (수정)
├── config/
│   └── llm_config.py               # LLM 전략 설정
└── templates/
    └── prompts/
        ├── bull_prompt.yaml        # Bull 프롬프트
        ├── bear_prompt.yaml        # Bear 프롬프트
        └── synthesizer_prompt.yaml # Synthesizer 프롬프트
```

---

## 🎨 LLM 전략 (src/config/llm_config.py)

```python
LLM_STRATEGY = {
    "quick": {
        "model": "gemini-2.5-flash",
        "temperature": 0.0,
        "max_tokens": 1500,
        "use_cases": ["entity_extraction", "sentiment_filtering", "termination_check", "analyst_basic"]
    },
    "deep": {
        "model": "gemini-3-pro-preview",
        "temperature": 0.0,
        "max_tokens": 4000,
        "use_cases": ["bull_logic", "bear_logic", "synthesis_report", "quality_check_final"]
    }
}
```

---

## ✅ 스파게티 코드 방지 체크리스트

- [ ] Agent는 State만 읽고 씀 (GraphRAG 직접 호출 금지)
- [ ] Agent 간 직접 호출 금지 (Workflow가 조율)
- [ ] State Immutable 패턴 (`.copy()` 사용)
- [ ] BaseDebateAgent 추상 클래스로 인터페이스 강제
- [ ] Workflow와 Agent 계층 명확히 분리
- [ ] 2.4 확장 시 변경 포인트 1개로 제한 (`_extract_data_from_state`)

---

## 🚀 구현 순서 (Week 1-2)

### Week 1
1. **Day 1**: `base_debate_agent.py`, `state.py` 확장
2. **Day 2**: `BullAgent`, `BearAgent` 구현
3. **Day 3**: `SynthesizerAgent` 구현
4. **Day 4**: Prompt 작성 (YAML)
5. **Day 5**: Mock 데이터로 단위 테스트

### Week 2
6. **Day 1-2**: `debate_workflow.py` 구현
7. **Day 3**: 기존 `workflow.py` 통합
8. **Day 4-5**: E2E 테스트 (Mock GraphRAG)

---

## 📊 검증 기준

**단위 테스트**:
```python
def test_bull_agent():
    mock_state = {
        "query": "삼성전자 HBM 전망",
        "graphrag_results": {
            "subgraph": {"nodes": [], "edges": []},
            "text_context": "Mock Context",
            "metadata": {}
        }
    }
    
    bull = BullAgent(llm)
    result = bull.argue(mock_state)
    
    assert "argument" in result
    assert len(result["key_points"]) >= 3
    assert 0.0 <= result["confidence"] <= 1.0
```

**통합 테스트**:
```python
def test_debate_workflow():
    workflow = create_debate_workflow(bull, bear, synthesizer)
    
    result = workflow.invoke(initial_state)
    
    assert result["synthesis_report"] is not None
    assert result["debate_state"]["debate_count"] <= 3
```

---

**작성자**: AI Assistant  
**다음 단계**: 사용자 승인 후 구현 시작

---

## 🔗 Phase 0/1 기존 시스템과의 통합

### 현재 시스템 구조 (Phase 1 완료)

```
Phase 0: PDF Parsing
  ├─ GeminiPDFParser → data/processed/*.json
  └─ VLM (차트 분석)

Phase 1: KG Construction
  ├─ KGConstructionAgent (Orchestrator)
  │   ├─ PDFParserAgent
  │   ├─ PriceParserAgent
  │   ├─ NewsParserAgent
  │   ├─ MacroParserAgent
  │   ├─ DARTParserAgent
  │   └─ FundParserAgent
  ├─ KGMerger (JSON 병합)
  ├─ EntityNormalizer (엔티티 정규화)
  └─ Neo4jKGLoader (이중 레이어 로딩)
      ├─ Static: MERGE (Company, Product, Technology...)
      └─ Dynamic: CREATE (Event, Metric, Trend...)
```

### Phase 2.3 통합 지점

#### 1. 데이터 흐름

```
[사용자 쿼리]
    ↓
┌─────────────────────────────────────┐
│ Phase 0/1: KG 구축 (이미 완료)      │
│ - data/raw → Neo4j                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Phase 2.3: GraphRAG Query ⭐ NEW    │
│ - Neo4j 서브그래프 검색             │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Debate Agents                       │
│ - Bull/Bear/Synthesizer             │
└─────────────────────────────────────┘
    ↓
[최종 리포트]
```

#### 2. Neo4j 연결 (src/pipeline/graphrag_query.py - 신규)

```python
from src.dataflows.neo4j_loader import Neo4jKGLoader
from src.models.nodes import NodeType

class GraphRAGQueryEngine:
    """
    Neo4j에서 서브그래프를 검색하여 ReportState에 저장
    
    Phase 1의 Neo4jKGLoader를 활용하여 연결
    """
    
    def __init__(self, neo4j_uri: str, user: str, password: str):
        # Phase 1에서 사용하던 Neo4j 연결 재사용
        self.loader = Neo4jKGLoader(uri=neo4j_uri, user=user, password=password)
        self.driver = self.loader.driver
    
    def query(self, query: str, max_hops: int = 1) -> Dict:
        """
        사용자 쿼리 → Neo4j 서브그래프 검색
        
        Returns:
            {
                "subgraph": {
                    "nodes": [...],  # NodeType Enum 기반
                    "edges": [...]
                },
                "context": "텍스트 요약",
                "metadata": {...}
            }
        """
        # 1. Entity 추출 (Quick LLM - 속도 및 비용 최적화 ⭐)
        entities = self._extract_entities(query, self.llm_quick)
        
        # 2. Cypher 쿼리 생성
        cypher = self._build_cypher(entities, max_hops)
        
        # 3. Neo4j 실행 (Phase 1 driver 활용)
        with self.driver.session() as session:
            result = session.run(cypher)
            nodes, edges = self._parse_result(result)
        
        # 4. 표준 형식 변환
        return {
            "subgraph": {"nodes": nodes, "edges": edges},
            "subgraph": {"nodes": nodes, "edges": edges},
            # [Risk 1 & 5] Text Serialization & Path Context
            # JSON 토큰 절약 및 LLM 이해도 향상을 위해 "A는 B를 유발했다" 형태의 문장으로 요약
            "context": self._summarize(nodes, edges),
            "metadata": {"query": query, "hops": max_hops}
        }
    
    def _build_cypher(self, entities: List[str], max_hops: int) -> str:
        """
        NodeType Enum 기반 Cypher 쿼리
        
        Phase 1 스키마 활용:
        - Static 노드: Company, Product, Technology
        - Dynamic 노드: Event, Metric, Trend
        """
        # 예: Company 중심 1-hop 검색
        return f"""
        MATCH (anchor:Company)
        WHERE anchor.name IN {entities}
        MATCH (anchor)-[r]-(neighbor)
        MATCH (anchor)-[r]-(neighbor)
        RETURN anchor, r, neighbor
        LIMIT 50  // [Risk 1: Context Explosion] 노드 폭발 방지를 위한 Hard Limit
        """
```

#### 3. State 연결 (src/pipeline/state.py 확장)

```python
# 기존 ReportState에 필드 추가
class ReportState(TypedDict):
    # ... Phase 0/1 기존 필드
    query: str
    target_companies: Optional[List[str]]
    kg_data: Optional[Dict]  # Phase 1에서 이미 정의됨
    
    # ===== Phase 2.3 추가 =====
    graphrag_results: Optional[GraphRAGResult]  # GraphRAG 검색 결과 (TypedDict) ⭐
    debate_state: Optional[DebateState]
    synthesis_report: Optional[str]
```

#### 4. 전체 워크플로우 통합 (src/pipeline/main_workflow.py - 신규)

```python
from langgraph.graph import StateGraph, END
from src.pipeline.state import ReportState
from src.pipeline.graphrag_query import GraphRAGQueryEngine
from src.pipeline.debate_workflow import create_debate_workflow
from src.agents.bull_agent import BullAgent
from src.agents.bear_agent import BearAgent
from src.agents.synthesizer_agent import SynthesizerAgent

def create_full_workflow(
    neo4j_uri: str,
    llm_quick,
    llm_deep
) -> StateGraph:
    """
    Phase 0/1/2.3 통합 워크플로우 (Quick/Deep 하이브리드)
    
    [Risk 4: Latency]
    LangGraph의 `.stream()` 메서드를 지원하도록 설계해야 함.
    """
    workflow = StateGraph(ReportState)
    
    # === Phase 0/1: KG 구축 (이미 완료된 상태 가정) ===
    # KGConstructionAgent는 별도 실행
    # Neo4j에 데이터 이미 로딩됨
    
    # === Phase 2.3: GraphRAG + Debate ===
    
    # 1. GraphRAG Query 노드
    graphrag_engine = GraphRAGQueryEngine(neo4j_uri, "neo4j", "password")
    
    def graphrag_node(state: ReportState) -> ReportState:
        """Neo4j에서 서브그래프 검색"""
        query = state["query"]
        
        # GraphRAG 실행
        results = graphrag_engine.query(query, max_hops=1)
        
        # State 업데이트
        state["graphrag_results"] = results
        return state
    
    # 2. Debate Workflow (Phase 2.3 명세대로)
    bull = BullAgent(llm_deep)
    bear = BearAgent(llm_deep)
    synthesizer = SynthesizerAgent(llm_deep)
    
    debate_graph = create_debate_workflow(bull, bear, synthesizer)
    
    # === 그래프 구성 ===
    workflow.add_node("graphrag_query", graphrag_node)
    workflow.add_node("debate", debate_graph)
    
    # 실행 순서
    workflow.set_entry_point("graphrag_query")
    workflow.add_edge("graphrag_query", "debate")
    workflow.add_edge("debate", END)
    
    return workflow.compile()
```

#### 5. 실행 예시

```python
# main.py

from src.pipeline.main_workflow import create_full_workflow
from src.utils.llm_client import get_llm

# LLM 초기화 (하이브리드 전략)
llm_quick = get_llm(strategy="quick")
llm_deep = get_llm(strategy="deep")

# 워크플로우 생성
workflow = create_full_workflow(
    neo4j_uri="bolt://localhost:7687",
    llm_quick=llm_quick,
    llm_deep=llm_deep
)

# 초기 상태
initial_state = {
    "query": "삼성전자의 HBM 사업 전망은?",
    "target_companies": ["삼성전자"],
    "report_type": "deep"
}

# 실행
result = workflow.invoke(initial_state)

# 결과
print(result["synthesis_report"])
```

---

## 🔄 Phase 1 → Phase 2.3 마이그레이션 체크리스트

### 데이터 준비 (Phase 1 재실행)

- [ ] **Neo4j 초기화**
  ```bash
  # Neo4j Browser
  MATCH (n) DETACH DELETE n
  ```

- [ ] **KG 재구축** (스키마 확정 후)
  ```python
  from src.agents.kg_construction import KGConstructionAgent
  
  agent = KGConstructionAgent()
  result = agent.construct_knowledge_graph(
      auto_scan=True,
      load_to_neo4j=True
  )
  ```

- [ ] **Neo4j 데이터 검증**
  ```cypher
  // 노드 타입 확인
  MATCH (n) RETURN labels(n)[0] as type, count(*) as count
  ORDER BY count DESC
  
  // Dynamic 노드 확인
  MATCH (n:Event) RETURN n.name LIMIT 10
  MATCH (n:Metric) RETURN n.name LIMIT 10
  ```

### Phase 2.3 구현

- [ ] **GraphRAG Query 엔진** (`src/pipeline/graphrag_query.py`)
  - Neo4jKGLoader 활용
  - Cypher 쿼리 작성
  - 서브그래프 파싱

- [ ] **Debate Agents** (명세대로)
  - BullAgent
  - BearAgent
  - SynthesizerAgent

- [ ] **Workflow 통합** (`src/pipeline/main_workflow.py`)
  - GraphRAG → Debate 연결
  - State 전파 확인

### 테스트

- [ ] **Unit Test**: GraphRAG Query
  ```python
  def test_graphrag_query():
      engine = GraphRAGQueryEngine(...)
      result = engine.query("삼성전자")
      assert "subgraph" in result
  ```

- [ ] **Integration Test**: Full Workflow
  ```python
  def test_full_workflow():
      workflow = create_full_workflow(...)
      result = workflow.invoke({"query": "..."})
      assert result["synthesis_report"] is not None
  ```

---

## 📦 파일 구조 (통합 후)

```
src/
├── agents/
│   ├── kg_construction.py           # Phase 1 (기존)
│   ├── parsers/                      # Phase 1 (기존)
│   ├── bull_agent.py                 # Phase 2.3 ⭐
│   ├── bear_agent.py                 # Phase 2.3 ⭐
│   └── synthesizer_agent.py          # Phase 2.3 ⭐
├── dataflows/
│   ├── neo4j_loader.py               # Phase 1 (기존, 재사용)
│   ├── entity_normalizer.py          # Phase 1 (기존)
│   └── kg_merger.py                  # Phase 1 (기존)
├── pipeline/
│   ├── state.py                      # Phase 1 + 2.3 (확장) ⭐
│   ├── nodes.py                      # Phase 1 (기존)
│   ├── graphrag_query.py             # Phase 2.3 (신규) ⭐
│   ├── debate_workflow.py            # Phase 2.3 (신규) ⭐
│   └── main_workflow.py              # Phase 2.3 (신규 통합) ⭐
├── models/
│   └── nodes.py                      # Phase 1 (기존, NodeType Enum)
└── config/
    ├── llm_config.py                 # Phase 2.3 (신규) ⭐
    └── parser_config.py              # Phase 1 (기존)
```

---

## 💡 핵심 통합 포인트 요약

1. **Neo4j 재사용**: Phase 1의 `Neo4jKGLoader.driver` 활용
2. **NodeType Enum 기반**: 스키마 중앙화 완료 상태 활용
3. **State 확장**: `ReportState`에 `graphrag_results`, `debate_state` 추가
4. **독립 실행**: Phase 2.3은 Neo4j 데이터만 있으면 독립 실행 가능

**의존성**:
- Phase 2.3은 **Phase 1 실행 완료 후** 작동
- Neo4j에 데이터가 있어야 GraphRAG 동작
- 스키마 확정 후 Phase 1 재실행 → Phase 2.3 테스트

---

## ⚠️ 잠재적 위험 및 대응 방안 (Critical Checkpoints)
> **설계 보완**: 사용자 피드백 기반 현실적 문제 해결 방안

### 1. 컨텍스트 윈도우 폭발 (Context Window Explosion)
- **문제**: 삼성전자와 연결된 노드가 수천 개일 경우, JSON 변환 시 토큰 한도 초과 및 비용 급증.
- **대응**:
    - **Pruning (가지치기)**: `GraphRAGQueryEngine`에서 `LIMIT 50` 또는 PageRank 상위 노드만 추출.
    - **Text Serialization**: JSON 전체 대신 "주어-동사-목적어" 형태의 요약 텍스트로 변환하여 토큰 절약. (`GraphRAGResult.text_context` 적극 활용)

### 2. "데이터 없음"의 함정 (The "No Data" Trap)
- **문제**: 관련 Event나 Trend 노드가 없을 때 Agent가 환각(Hallucination)을 일으키거나 무의미한 답변 반복.
- **대응**:
    - **Honest Agent**: 프롬프트에 **"데이터가 없으면 솔직하게 '판단 불가'라고 답하라"**는 지침 추가.
    - **Fallback**: 향후 Phase 3/4에서 Web Search로 연결하는 Fallback 메커니즘 고려.

### 3. 무한 긍정/부정 루프 (Echo Chamber)
- **문제**: Bull/Bear가 서로 같은 주장을 반복하며 토론이 제자리걸음.
- **대응**:
    - **Prompt Constraint**: **"이전 라운드(`opponent_last_arg`)에서 언급된 내용은 제외하고 새로운 논거를 제시하라"**는 제약 조건 명시.
    - **History Separation**: `bull_history`와 `bear_history`를 분리하여 상호 참조를 제한적으로 허용(긴장감 유지).

### 4. 속도(Latency) 이슈
- **문제**: Deep Model(Gemini-3-Pro)의 다중 턴 실행으로 응답 지연(30초 이상).
- **대응**:
    - **Streaming UX**: LangGraph의 스트리밍 기능을 활용하여 "Bull이 생각 중...", "Bear가 반박 중..." 상태를 실시간 노출.

### 5. LLM의 그래프 이해도 (Graph Understanding)
- **문제**: 복잡한 인과관계(A→B→C)를 Raw JSON만으로 추론하기 어려움.
- **대응**:
    - **Path-based Context**: 단순 노드 나열이 아니라, `GraphRAGQueryEngine`에서 주요 경로(Critical Paths)를 텍스트로 풀어 설명.
    - **Mock Data Test**: Neo4j 연결 전, Mock 데이터를 통해 Agent의 추론 능력을 먼저 검증.

---

## 🛠️ 코드 구현 시 주의사항 (Code-Level Checkpoints)

> **Implementation Guide**: 개발자가 실수하기 쉬운 Mutable State, Null Handling 등의 주요 체크포인트

### 1. Mutable State의 함정 (State Management)
- **위험**: Python Dictionary를 직접 수정하면 LangGraph의 Checkpointing이 깨질 수 있음.
- **해결**: 반드시 `.copy()` 후 수정.
    ```python
    # Bad
    state["debate_state"]["bull_history"] += "..."
    
    # Good
    new_debate = state["debate_state"].copy()
    new_debate["bull_history"] += "..."
    state["debate_state"] = new_debate
    ```

### 2. Null Safety (Empty GraphRAG Results)
- **위험**: 검색 결과가 없을 때(Empty Nodes) 예외 처리가 없으면 Agent 환각 발생.
- **해결**: `_extract_data_from_state`에서 방어 로직 필수.
    ```python
    if not nodes:
        return {"events": [], "warning": "데이터가 없습니다."}
    ```

### 3. Agent 간 "기억" 격리 (Isolation)
- **위험**: Bull이 Bear의 내부 Prompt나 생각(Chain of Thought)을 보면 안 됨.
- **해결**:
    - `argue()` 호출 시 `opponent_last_arg`만 전달.
    - `bull_history`와 `bear_history`는 `Synthesizer`만 모두 볼 수 있음.

### 4. Dependency Injection (Neo4j Driver)
- **위험**: 매 쿼리마다 Connection을 맺고 끊으면 성능 저하(Latency 증가).
- **해결**: Workflow 생성 외부에서 Driver를 초기화하고 주입(Injection)하는 구조 채택.
    ```python
    # main.py
    driver = GraphDatabase.driver(uri, auth=(user, password))
    workflow = create_full_workflow(driver=driver, ...)
    ```
