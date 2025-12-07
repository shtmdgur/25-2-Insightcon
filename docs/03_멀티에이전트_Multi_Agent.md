# 멀티에이전트 시스템 (Multi-Agent Systems) 완전 정리 가이드

## 📖 목차
1. [멀티에이전트 시스템이란?](#멀티에이전트-시스템이란)
2. [TradingAgents 프레임워크](#tradingagents-프레임워크)
3. [에이전트 역할 분화](#에이전트-역할-분화)
4. [통신 프로토콜](#통신-프로토콜)
5. [워크플로우 설계](#워크플로우-설계)
6. [실전 구현 가이드](#실전-구현-가이드)

---

## 멀티에이전트 시스템이란?

### 기본 개념

**멀티에이전트 시스템(Multi-Agent System, MAS)**은 여러 개의 자율적인 에이전트(Agent)가 협력하여 복잡한 문제를 해결하는 시스템입니다.

#### 에이전트(Agent)란?

**에이전트**는 다음 특성을 가진 소프트웨어 엔티티입니다:

1. **자율성(Autonomy)**: 외부 개입 없이 독립적으로 동작
2. **반응성(Reactivity)**: 환경 변화에 반응
3. **능동성(Proactiveness)**: 목표 달성을 위해 능동적으로 행동
4. **사회성(Social Ability)**: 다른 에이전트와 통신 및 협력

#### 간단한 비유

**단일 에이전트 시스템**:
- 한 명의 전문가가 모든 일을 처리
- 예: 한 명의 애널리스트가 모든 분석 수행

**멀티에이전트 시스템**:
- 여러 전문가가 각자의 전문 분야에서 협력
- 예: 펀더멘털 애널리스트, 감성 분석가, 기술 분석가가 협력

### 멀티에이전트 시스템의 장점

1. **전문성 분화**: 각 에이전트가 특정 영역에 전문성 집중
2. **병렬 처리**: 여러 에이전트가 동시에 작업 수행
3. **견고성**: 한 에이전트 실패해도 다른 에이전트가 대체 가능
4. **확장성**: 새로운 에이전트 추가 용이
5. **설명 가능성**: 각 에이전트의 의사결정 과정 추적 가능

### 금융 도메인에서의 활용

**실제 거래 회사의 구조**:
```
거래 회사
├─ 퀀트 팀 (수학자, 데이터 과학자)
├─ 펀더멘털 분석팀
├─ 기술 분석팀
├─ 감성 분석팀
├─ 리스크 관리팀
└─ 트레이더
```

**멀티에이전트 시스템으로 모델링**:
```
TradingAgents 시스템
├─ Fundamental Analyst Agent
├─ Technical Analyst Agent
├─ Sentiment Analyst Agent
├─ Risk Manager Agent
└─ Trader Agent
```

---

## TradingAgents 프레임워크

### 개요

**TradingAgents**는 실제 거래 회사의 협업 구조를 모방한 LLM 기반 멀티에이전트 거래 프레임워크입니다.

#### 핵심 특징

1. **역할 분화**: 7가지 전문 에이전트 역할
2. **구조화된 통신**: 문서 기반 + 자연어 토론
3. **토론 기반 의사결정**: Bullish/Bearish 연구원의 논쟁
4. **리스크 관리**: 전용 리스크 관리 팀

#### 전체 아키텍처

```
┌─────────────────────────────────────────┐
│         TradingAgents Framework         │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │   I. ANALYST TEAM               │  │
│  │   (정보 수집)                    │  │
│  │   - Fundamental Analyst          │  │
│  │   - Sentiment Analyst            │  │
│  │   - News Analyst                 │  │
│  │   - Technical Analyst            │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│  ┌──────────────▼───────────────────┐  │
│  │   II. RESEARCH TEAM              │  │
│  │   (토론 및 평가)                  │  │
│  │   - Bullish Researcher           │  │
│  │   - Bearish Researcher           │  │
│  │   - Debate Facilitator           │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│  ┌──────────────▼───────────────────┐  │
│  │   III. TRADER                    │  │
│  │   (거래 결정)                     │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│  ┌──────────────▼───────────────────┐  │
│  │   IV. RISK MANAGEMENT TEAM      │  │
│  │   (리스크 평가)                  │  │
│  │   - Risk-seeking                 │  │
│  │   - Neutral                      │  │
│  │   - Risk-conservative            │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│  ┌──────────────▼───────────────────┐  │
│  │   V. FUND MANAGER                │  │
│  │   (최종 승인)                     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 에이전트 역할 분화

### I. Analyst Team (분석가 팀)

분석가 팀은 시장 데이터를 수집하고 분석하는 전문가들입니다.

#### 1. Fundamental Analyst (펀더멘털 분석가)

**역할**: 기업의 내재가치 평가

**주요 작업**:
- 재무제표 분석
- 실적 보고서 검토
- 내부자 거래 분석
- 장기 투자 가치 평가

**도구**:
- 재무 데이터 API
- 실적 발표 데이터
- 내부자 거래 데이터베이스

**출력 예시**:
```json
{
  "agent": "Fundamental Analyst",
  "company": "삼성전자",
  "analysis": {
    "intrinsic_value": "85,000원",
    "current_price": "75,000원",
    "valuation": "저평가",
    "key_metrics": {
      "P/E": 12.5,
      "P/B": 1.2,
      "ROE": 15.3,
      "Debt_Ratio": 0.15
    },
    "recommendation": "Buy",
    "reasoning": "현재 주가가 내재가치 대비 저평가되어 있으며, 
                  재무 건전성과 수익성이 우수합니다."
  }
}
```

#### 2. Sentiment Analyst (감성 분석가)

**역할**: 시장 감성과 투자자 심리 분석

**주요 작업**:
- 소셜 미디어 감성 분석 (Reddit, Twitter)
- 뉴스 감성 점수 계산
- 내부자 감성 추출
- 단기 시장 심리 예측

**도구**:
- 웹 검색 엔진
- Reddit 검색 API
- Twitter 검색 도구
- 감성 점수 계산 알고리즘

**출력 예시**:
```json
{
  "agent": "Sentiment Analyst",
  "company": "삼성전자",
  "analysis": {
    "overall_sentiment": 0.72,
    "sentiment_breakdown": {
      "social_media": 0.68,
      "news": 0.75,
      "insider": 0.73
    },
    "key_topics": [
      "HBM 수요 급증",
      "AI 서버 시장 성장",
      "미국 규제 우려"
    ],
    "recommendation": "Positive",
    "reasoning": "소셜 미디어와 뉴스에서 전반적으로 긍정적인 
                  감성이 우세하며, HBM 관련 수요 증가에 대한 
                  기대감이 높습니다."
  }
}
```

#### 3. News Analyst (뉴스 분석가)

**역할**: 뉴스와 거시경제 이벤트 분석

**주요 작업**:
- 뉴스 기사 분석 (Bloomberg, Yahoo, EODHD)
- 정부 발표 및 거시경제 지표 분석
- 주요 기업 변화 식별
- 시장 동향 예측

**도구**:
- 뉴스 API
- 거시경제 데이터 소스
- 이벤트 추출 도구

**출력 예시**:
```json
{
  "agent": "News Analyst",
  "date": "2024-10-25",
  "analysis": {
    "market_state": "Bullish",
    "key_events": [
      {
        "type": "Earnings",
        "company": "삼성전자",
        "impact": "Positive",
        "description": "3분기 실적 시장 기대치 상회"
      },
      {
        "type": "Regulation",
        "impact": "Neutral",
        "description": "미국 반도체 수출 규제 완화 검토"
      }
    ],
    "macro_indicators": {
      "GDP_growth": 2.5,
      "inflation": 2.1,
      "interest_rate": 3.5
    },
    "recommendation": "Market favorable for growth stocks"
  }
}
```

#### 4. Technical Analyst (기술 분석가)

**역할**: 가격 패턴과 기술적 지표 분석

**주요 작업**:
- 기술적 지표 계산 (MACD, RSI, Bollinger Bands 등)
- 가격 패턴 분석
- 거래량 분석
- 진입/청산 시점 결정

**도구**:
- 코드 실행 환경
- 기술적 지표 계산 라이브러리
- 차트 분석 도구

**출력 예시**:
```json
{
  "agent": "Technical Analyst",
  "company": "삼성전자",
  "analysis": {
    "indicators": {
      "MACD": {
        "value": 1250,
        "signal": "Bullish",
        "description": "MACD가 시그널 라인을 상향 돌파"
      },
      "RSI": {
        "value": 58,
        "signal": "Neutral",
        "description": "과매수/과매도 구간 밖"
      },
      "Bollinger_Bands": {
        "position": "Middle",
        "signal": "Neutral"
      }
    },
    "price_pattern": "Ascending Triangle",
    "support_level": 73,000,
    "resistance_level": 78,000,
    "recommendation": "Buy on breakout above 78,000",
    "stop_loss": 72,000
  }
}
```

### II. Researcher Team (연구팀)

연구팀은 분석가들의 결과를 토론하고 평가합니다.

#### 1. Bullish Researcher (강세 연구원)

**역할**: 투자 기회의 긍정적 측면 강조

**주요 작업**:
- 긍정적 지표 하이라이트
- 성장 잠재력 강조
- 유리한 시장 조건 설명
- 매수 논거 구성

**토론 예시**:
```
Bullish Researcher:
"삼성전자의 경우, HBM 시장에서의 시장 점유율이 
지속적으로 증가하고 있으며, AI 서버 수요 급증으로 
인한 수요 증가가 예상됩니다. 또한 기술적 지표상 
상승 추세가 확인되었으며, 펀더멘털 분석 결과 
저평가 상태입니다."
```

#### 2. Bearish Researcher (약세 연구원)

**역할**: 투자 기회의 부정적 측면과 리스크 강조

**주요 작업**:
- 잠재적 하방 리스크 식별
- 불리한 시장 신호 강조
- 경쟁 우위 약화 가능성 제시
- 매도/보유 논거 구성

**토론 예시**:
```
Bearish Researcher:
"그러나 미국의 반도체 수출 규제가 여전히 불확실하며, 
SK하이닉스와의 경쟁이 치열해지고 있습니다. 또한 
최근 RSI가 상승 추세에 있어 단기 조정 가능성도 
배제할 수 없습니다."
```

#### 3. Debate Facilitator (토론 진행자)

**역할**: 토론을 조율하고 최종 관점 선택

**주요 작업**:
- 토론 라운드 수 결정
- 토론 요약
- 우세한 관점 선택
- 구조화된 결론 기록

**토론 결과 예시**:
```json
{
  "facilitator": "Debate Facilitator",
  "rounds": 3,
  "prevailing_perspective": "Bullish",
  "summary": "Bullish 관점이 더 강력한 근거를 제시했습니다. 
              HBM 시장 성장과 기술적 상승 추세가 
              단기 리스크를 상쇄할 것으로 판단됩니다.",
  "confidence": 0.75,
  "structured_entry": {
    "recommendation": "Buy",
    "target_price": 80,000,
    "time_horizon": "1-2 weeks"
  }
}
```

### III. Trader Agents (트레이더)

**역할**: 최종 거래 결정 및 실행

**주요 작업**:
- 분석가 및 연구원의 인사이트 종합
- 거래 타이밍 결정
- 포지션 크기 결정
- 주문 실행

**의사결정 프로세스**:
```
1. Analyst Team 리포트 검토
   ├─ Fundamental Analysis
   ├─ Sentiment Analysis
   ├─ News Analysis
   └─ Technical Analysis

2. Researcher Team 토론 결과 검토
   ├─ Bullish Arguments
   ├─ Bearish Arguments
   └─ Prevailing Perspective

3. 종합 판단
   ├─ Buy / Sell / Hold 결정
   ├─ 포지션 크기 계산
   └─ 진입/청산 가격 설정

4. 거래 실행
   └─ 주문 제출
```

**출력 예시**:
```json
{
  "agent": "Trader",
  "decision": {
    "action": "Buy",
    "company": "삼성전자",
    "quantity": 100,
    "entry_price": 75,500,
    "target_price": 80,000,
    "stop_loss": 73,000,
    "rationale": {
      "fundamental": "저평가 상태, 우수한 재무 건전성",
      "sentiment": "긍정적 시장 감성",
      "technical": "상승 추세 확인",
      "research": "Bullish 관점 우세"
    }
  },
  "report": "종합 분석 결과, 삼성전자는 단기적으로 
             상승 가능성이 높으며, 80,000원 목표가를 
             설정합니다."
}
```

### IV. Risk Management Team (리스크 관리 팀)

**역할**: 포트폴리오 리스크 모니터링 및 관리

**주요 작업**:
- 리스크 노출 평가
- 변동성 분석
- 유동성 리스크 평가
- 대응책 수립

**3가지 관점**:

1. **Risk-seeking (공격적)**:
   - 높은 리스크 허용
   - 높은 수익 추구

2. **Neutral (중립적)**:
   - 균형 잡힌 접근
   - 리스크-수익 균형

3. **Risk-conservative (보수적)**:
   - 낮은 리스크 선호
   - 자본 보존 우선

**토론 예시**:
```
Risk-seeking:
"현재 포트폴리오의 변동성은 허용 범위 내이며, 
삼성전자 추가 매수는 분산 투자 효과를 높일 수 있습니다."

Risk-conservative:
"그러나 현재 포지션이 이미 반도체 섹터에 집중되어 있어, 
추가 매수는 섹터 리스크를 증가시킬 수 있습니다."

Neutral:
"제안: 포지션 크기를 절반으로 줄여 리스크를 완화하면서도 
기회를 포착하는 것이 좋겠습니다."
```

**최종 리스크 조정**:
```json
{
  "risk_management": {
    "original_decision": {
      "action": "Buy",
      "quantity": 100
    },
    "risk_adjustment": {
      "action": "Buy",
      "quantity": 50,  // 절반으로 감소
      "reason": "섹터 집중 리스크 완화"
    },
    "risk_metrics": {
      "portfolio_volatility": 0.25,
      "sector_concentration": 0.35,
      "max_drawdown": 0.15
    }
  }
}
```

### V. Fund Manager (펀드 매니저)

**역할**: 최종 승인 및 거래 실행

**주요 작업**:
- 리스크 관리 팀의 조정 검토
- 최종 거래 승인
- 포트폴리오 상태 업데이트
- 거래 실행

**승인 프로세스**:
```
1. Trader Decision 검토
2. Risk Management Adjustment 검토
3. Portfolio Impact 분석
4. 최종 승인/거부 결정
5. 거래 실행
```

---

## 통신 프로토콜

### 문제점: 전화 게임 효과

**전통적인 자연어 통신의 문제**:
- 긴 대화에서 정보 손실
- 컨텍스트 길이 제한으로 초기 정보 망각
- 불필요한 정보로 인한 노이즈
- 구조화되지 않은 정보 교환

**예시**:
```
Agent A → Agent B: "삼성전자의 실적이 좋아 보이는데..."
Agent B → Agent C: "삼성전자가 좋다고 하던데..."
Agent C → Agent D: "삼성전자 관련해서 뭔가..."
(정보가 점점 손실됨)
```

### 해결책: 구조화된 통신

TradingAgents는 **구조화된 문서**와 **자연어 토론**을 혼합합니다.

#### 1. 구조화된 문서 통신

**Analyst Team → Researcher Team**:
```json
{
  "report_type": "Fundamental Analysis",
  "agent": "Fundamental Analyst",
  "timestamp": "2024-10-25T10:00:00Z",
  "company": "삼성전자",
  "key_metrics": {
    "P/E": 12.5,
    "P/B": 1.2,
    "ROE": 15.3
  },
  "recommendation": "Buy",
  "target_price": 85,000,
  "reasoning": "내재가치 대비 저평가..."
}
```

**장점**:
- 정보 손실 없음
- 구조화되어 파싱 용이
- 쿼리 가능
- 버전 관리 가능

#### 2. 자연어 토론 (제한적 사용)

**Researcher Team 내부 토론**:
```
Bullish Researcher: "HBM 시장 성장이 지속되고 있어..."
Bearish Researcher: "그러나 경쟁이 치열해지고..."
Bullish Researcher: "하지만 기술 우위가..."
(3라운드 토론)
```

**사용 시기**:
- 복잡한 논쟁이 필요한 경우
- 다양한 관점 통합이 필요한 경우
- 창의적 해결책이 필요한 경우

**제한**:
- 토론 라운드 수 제한 (예: 최대 3라운드)
- 토론 결과는 구조화된 형식으로 기록

### ReAct 프레임워크

**ReAct (Reasoning + Acting)**: 추론과 행동을 결합한 프롬프팅 프레임워크

**구조**:
```
Thought: [에이전트의 사고 과정]
Action: [수행할 행동]
Observation: [행동 결과]
... (반복)
```

**예시**:
```
Thought: "삼성전자의 최근 실적을 확인해야 합니다."
Action: search_financial_data(company="삼성전자", period="2024Q3")
Observation: "2024Q3 매출: 300조원, 영업이익: 50조원"

Thought: "매출이 전년 대비 10% 증가했습니다. 
          이는 긍정적인 신호입니다."
Action: update_analysis(recommendation="Buy", confidence=0.8)
Observation: "Analysis updated successfully"
```

---

## 워크플로우 설계

### 전체 워크플로우

```
START
  │
  ├─► Analyst Team (병렬 실행)
  │   ├─► Fundamental Analyst
  │   ├─► Sentiment Analyst
  │   ├─► News Analyst
  │   └─► Technical Analyst
  │
  ├─► 구조화된 리포트 생성
  │
  ├─► Researcher Team
  │   ├─► Bullish Researcher (리포트 검토)
  │   ├─► Bearish Researcher (리포트 검토)
  │   └─► Debate (N 라운드)
  │
  ├─► Debate Facilitator
  │   └─► 우세한 관점 선택 및 구조화
  │
  ├─► Trader
  │   └─► 거래 결정 생성
  │
  ├─► Risk Management Team
  │   ├─► Risk-seeking 관점
  │   ├─► Risk-conservative 관점
  │   ├─► Neutral 관점
  │   └─► 토론 및 리스크 조정
  │
  ├─► Fund Manager
  │   └─► 최종 승인
  │
  └─► 거래 실행
      └─► END
```

### LangGraph를 사용한 구현

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional

class TradingState(TypedDict):
    """거래 워크플로우 상태"""
    # 입력
    company: str
    date: str
    
    # 중간 결과
    fundamental_analysis: Optional[dict]
    sentiment_analysis: Optional[dict]
    news_analysis: Optional[dict]
    technical_analysis: Optional[dict]
    
    # 연구 결과
    bullish_arguments: Optional[List[str]]
    bearish_arguments: Optional[List[str]]
    prevailing_perspective: Optional[str]
    
    # 거래 결정
    trader_decision: Optional[dict]
    risk_adjustment: Optional[dict]
    
    # 최종 결과
    final_decision: Optional[dict]
    execution_status: Optional[str]

# 상태 그래프 생성
workflow = StateGraph(TradingState)

# 노드 추가
workflow.add_node("fundamental_analyst", fundamental_analyst_node)
workflow.add_node("sentiment_analyst", sentiment_analyst_node)
workflow.add_node("news_analyst", news_analyst_node)
workflow.add_node("technical_analyst", technical_analyst_node)

# 병렬 실행을 위한 조건부 엣지
def route_after_analysts(state: TradingState) -> List[str]:
    """모든 분석가가 완료되면 연구팀으로"""
    if all([
        state.get("fundamental_analysis"),
        state.get("sentiment_analysis"),
        state.get("news_analysis"),
        state.get("technical_analysis")
    ]):
        return ["researcher_team"]
    return []

workflow.add_conditional_edges(
    "fundamental_analyst",
    route_after_analysts,
    {"researcher_team": "researcher_team"}
)

# 연구팀 노드
workflow.add_node("researcher_team", researcher_team_node)
workflow.add_node("trader", trader_node)
workflow.add_node("risk_management", risk_management_node)
workflow.add_node("fund_manager", fund_manager_node)

# 엣지 연결
workflow.add_edge("researcher_team", "trader")
workflow.add_edge("trader", "risk_management")
workflow.add_edge("risk_management", "fund_manager")
workflow.add_edge("fund_manager", END)

# 컴파일
app = workflow.compile()
```

---

## 실전 구현 가이드

### 에이전트 클래스 설계

```python
from langchain.agents import AgentExecutor
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

class FundamentalAnalystAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
        self.agent = self._create_agent()
    
    def _create_agent(self):
        """ReAct 에이전트 생성"""
        from langchain.agents import create_react_agent
        from langchain import hub
        
        prompt = hub.pull("hwchase17/react")
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        return AgentExecutor(agent=agent, tools=self.tools)
    
    def analyze(self, company: str, date: str) -> dict:
        """기업 펀더멘털 분석"""
        query = f"""
        {company}의 {date} 기준 펀더멘털을 분석하세요.
        
        다음을 포함하세요:
        1. 재무제표 분석
        2. 주요 재무 지표 (P/E, P/B, ROE 등)
        3. 내재가치 평가
        4. 투자 권장사항
        """
        
        result = self.agent.invoke({"input": query})
        
        # 구조화된 리포트로 변환
        report = self._format_report(result, company)
        return report
    
    def _format_report(self, result: str, company: str) -> dict:
        """결과를 구조화된 리포트로 변환"""
        # LLM을 사용하여 JSON 형식으로 변환
        format_prompt = f"""
        다음 분석 결과를 JSON 형식으로 변환하세요:
        
        {result}
        
        형식:
        {{
            "agent": "Fundamental Analyst",
            "company": "{company}",
            "analysis": {{
                "intrinsic_value": "...",
                "current_price": "...",
                "valuation": "...",
                "key_metrics": {{}},
                "recommendation": "...",
                "reasoning": "..."
            }}
        }}
        """
        
        formatted = self.llm.invoke(format_prompt)
        return json.loads(formatted.content)
```

### 통신 프로토콜 구현

```python
class CommunicationProtocol:
    """에이전트 간 통신 프로토콜"""
    
    def __init__(self):
        self.global_state = {}
        self.message_history = []
    
    def store_report(self, agent_name: str, report: dict):
        """구조화된 리포트 저장"""
        self.global_state[agent_name] = {
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    
    def query_reports(self, agent_names: List[str]) -> dict:
        """특정 에이전트들의 리포트 조회"""
        return {
            name: self.global_state[name]["report"]
            for name in agent_names
            if name in self.global_state
        }
    
    def record_debate(self, participants: List[str], 
                     rounds: List[dict]):
        """토론 기록"""
        debate_entry = {
            "participants": participants,
            "rounds": rounds,
            "timestamp": datetime.now().isoformat()
        }
        self.message_history.append(debate_entry)
        return debate_entry
```

### LLM 선택 전략

```python
class LLMSelector:
    """작업 유형에 따른 LLM 선택"""
    
    def __init__(self):
        # Quick-thinking 모델 (빠른 작업용)
        self.quick_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        
        # Deep-thinking 모델 (추론 집약적 작업용)
        self.deep_llm = ChatOpenAI(
            model="gpt-4o",  # 또는 o1-preview
            temperature=0
        )
    
    def get_llm(self, task_type: str):
        """작업 유형에 따라 LLM 선택"""
        quick_tasks = [
            "summarization",
            "data_retrieval",
            "table_to_text"
        ]
        
        if task_type in quick_tasks:
            return self.quick_llm
        else:
            return self.deep_llm

# 사용 예시
llm_selector = LLMSelector()

# 분석가들은 deep-thinking 모델 사용
fundamental_analyst = FundamentalAnalystAgent(
    llm=llm_selector.get_llm("analysis"),
    tools=tools
)

# 데이터 검색은 quick-thinking 모델 사용
data_retriever = DataRetrieverAgent(
    llm=llm_selector.get_llm("data_retrieval"),
    tools=tools
)
```

---

## 요약

### 핵심 포인트

1. **역할 분화**: 각 에이전트가 전문 영역에 집중
2. **구조화된 통신**: 문서 기반 통신으로 정보 손실 방지
3. **토론 기반 의사결정**: 다양한 관점 통합
4. **리스크 관리**: 전용 팀으로 리스크 모니터링
5. **ReAct 프레임워크**: 추론과 행동의 결합

### 다음 단계

- [이전 문서: 지식 그래프](02_지식그래프_Knowledge_Graph.md)
- [다음 문서: 금융 도메인](04_금융_도메인_Finance.md)

---

**참고 논문**:
- TradingAgents: Multi-Agents LLM Financial Trading Framework
- Design and Development of Financial Applications Using Ontology-Based Multi-Agent Systems

