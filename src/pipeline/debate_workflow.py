"""
변증법 토론 워크플로우 (LangGraph 기반)
"""
from typing import Dict, Any, Literal, List, Optional
from langgraph.graph import StateGraph, END
from src.pipeline.state import ReportState, DebateState
from src.agents.bull_agent import BullAgent
from src.agents.bear_agent import BearAgent
from src.agents.judge_agent import JudgeAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.agents.validator_agent import ValidatorAgent


def create_debate_workflow(
    bull_agent: BullAgent, 
    bear_agent: BearAgent, 
    synthesizer_agent: SynthesizerAgent,
    judge_agent: JudgeAgent = None,
    validator_agent: ValidatorAgent = None
):
    """
    변증법 토론 워크플로우 생성 (v3.1)
    
    구조: initialize -> bull -> bear -> (loop x3) -> judge -> synthesizer -> validator -> END
    """
    
    workflow = StateGraph(ReportState)
    
    # 노드 추가
    workflow.add_node("initialize", initialize_debate)
    workflow.add_node("bull", lambda state: bull_node(state, bull_agent))
    workflow.add_node("bear", lambda state: bear_node(state, bear_agent))
    
    if judge_agent:
        workflow.add_node("judge", lambda state: judge_node(state, judge_agent))
    
    workflow.add_node("synthesizer", lambda state: synthesizer_node(state, synthesizer_agent))
    
    if validator_agent:
        workflow.add_node("validator", lambda state: validator_node(state, validator_agent))

    # 에지 정의
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "bull")
    workflow.add_edge("bull", "bear")
    
    # 루프 조건 (3라운드까지)
    def should_continue(state: ReportState):
        count = state["debate_state"]["debate_count"]
        if count >= 3:
            return "judge" if judge_agent else "synthesizer"
        return "bull"
    
    workflow.add_conditional_edges("bear", should_continue, {
        "bull": "bull",
        "judge": "judge" if judge_agent else "synthesizer",
        "synthesizer": "synthesizer"
    })
    
    if judge_agent:
        workflow.add_edge("judge", "synthesizer")
        
    if validator_agent:
        workflow.add_edge("synthesizer", "validator")
        workflow.add_edge("validator", END)
    else:
        workflow.add_edge("synthesizer", END)
    
    return workflow.compile()


# ============================================================
# Node Functions (v3.1)
# ============================================================

def initialize_debate(state: ReportState) -> ReportState:
    """토론 상태 초기화"""
    debate_state: DebateState = {
        "bull_history": "",
        "bear_history": "",
        "full_history": "",
        "current_bull_arg": None,
        "current_bear_arg": None,
        "debate_count": 0,
        "should_continue": True,
        "cached_paths": {},
        "debate_trace": [],
        "judge_result": None,
        "validation_result": None
    }
    
    state["debate_state"] = debate_state
    return state


def bull_node(state: ReportState, agent: BullAgent) -> Dict:
    """Bull Agent 주장 생성 노드"""
    opponent_arg = state["debate_state"].get("current_bear_arg")
    round_num = state["debate_state"]["debate_count"] + 1
    
    print(f"\n{'='*80}\n🔴 ROUND {round_num} - Bull Agent 주장 생성 중...\n{'='*80}")
    
    result = agent.argue(state, opponent_last_arg=opponent_arg)
    
    # State 업데이트
    debate_state = state["debate_state"]
    debate_state["current_bull_arg"] = result["argument"]
    debate_state["bull_history"] += f"\n\n## Round {round_num} - Bull\n{result['argument']}"
    debate_state["full_history"] += f"\n\n[Round {round_num} - Bull]\n{result['argument']}"
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Bull Round {round_num} 완료")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


def bear_node(state: ReportState, agent: BearAgent) -> Dict:
    """Bear Agent 주장 생성 노드"""
    opponent_arg = state["debate_state"].get("current_bull_arg")
    round_num = state["debate_state"]["debate_count"] + 1
    
    print(f"\n{'='*80}\n🔵 ROUND {round_num} - Bear Agent 주장 생성 중...\n{'='*80}")
    
    result = agent.argue(state, opponent_last_arg=opponent_arg)
    
    # State 업데이트
    debate_state = state["debate_state"]
    debate_state["current_bear_arg"] = result["argument"]
    debate_state["bear_history"] += f"\n\n## Round {round_num} - Bear\n{result['argument']}"
    debate_state["full_history"] += f"\n\n[Round {round_num} - Bear]\n{result['argument']}"
    
    # 라운드 증가
    debate_state["debate_count"] += 1
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Bear Round {debate_state['debate_count']} 완료")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


def judge_node(state: ReportState, agent: JudgeAgent) -> Dict:
    """토론 결과를 판결하는 노드"""
    print(f"\n{'='*80}\n⚖️  Judge - Rendering Verdict...\n{'='*80}")
    
    result = agent.judge(state)
    
    debate_state = state["debate_state"]
    debate_state["judge_result"] = result
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Judge: Rated {result.get('decision')} (Score: {result.get('score')})")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


def synthesizer_node(state: ReportState, agent: SynthesizerAgent) -> Dict:
    """최종 리포트를 합성하는 노드"""
    print(f"\n{'='*80}\n🧠 Synthesizer - 최종 리포트 생성 중...\n{'='*80}")
    
    final_report = agent.synthesize(state)
    
    debate_state = state["debate_state"]
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append("Synthesizer 리포트 완료")
    debate_state["debate_trace"] = debate_trace
    
    return {
        "debate_state": debate_state,
        "synthesis_report": final_report,
        "final_report": final_report
    }


def validator_node(state: ReportState, agent: ValidatorAgent) -> Dict:
    """리포트 품질을 검수하는 노드"""
    print(f"\n{'='*80}\n🔍 Validator - Quality Control...\n{'='*80}")
    
    result = agent.validate(state)
    
    debate_state = state["debate_state"]
    debate_state["validation_result"] = result
    
    debate_trace = debate_state.get("debate_trace", [])
    debate_trace.append(f"Validator: {result.get('decision', 'fail')}")
    debate_state["debate_trace"] = debate_trace
    
    return {"debate_state": debate_state}


# ========================================
# 헬퍼 함수 (확장 가능)
# ========================================

def update_cached_paths(state: ReportState, round_num: int, paths: list) -> ReportState:
    """
    Progressive Path Expansion: 캐시 업데이트
    
    Note: 현재는 Agent 내부에서 처리하지만, 
    향후 Workflow 레벨로 이동 가능
    """
    if "debate_state" not in state:
        state["debate_state"] = {}
    
    if "cached_paths" not in state["debate_state"]:
        state["debate_state"]["cached_paths"] = {}
    
    state["debate_state"]["cached_paths"][round_num] = paths
    return state
