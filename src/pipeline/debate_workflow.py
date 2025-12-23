"""
변증법 토론 워크플로우 (LangGraph 기반)

Bull → Bear → 반복 → Synthesizer 순서로 실행되는 토론 워크플로우
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from src.pipeline.state import ReportState, DebateState


def create_debate_workflow(bull_agent, bear_agent, judge_agent, synthesizer_agent, validator_agent=None):
    """
    변증법 토론 워크플로우 생성
    
    Args:
        bull_agent: BullAgent 인스턴스
        bear_agent: BearAgent 인스턴스
        judge_agent: JudgeAgent 인스턴스
        synthesizer_agent: SynthesizerAgent 인스턴스
        validator_agent: ValidatorAgent 인스턴스 (Optional)
    """
    
    # ... (Keep existing inner functions) ...
    # Re-declare inner functions to capture new argument if needed, or just add new one.
    # Since inner functions capture closure, we need to add validate_report inside.
    
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
            "debate_trace": []
        }
        state["debate_state"] = debate_state
        return state
    
    def bull_argue(state: ReportState) -> ReportState:
        # ... (Same as before, implicit capture)
        opponent_arg = state["debate_state"].get("current_bear_arg")
        round_num = state["debate_state"]["debate_count"] + 1
        print(f"\n{'='*80}")
        print(f"🔴 ROUND {round_num} - Bull Agent 주장 생성 중...")
        print('='*80)
        
        result = bull_agent.argue(state, opponent_last_arg=opponent_arg)
        
        state["debate_state"]["current_bull_arg"] = result["argument"]
        state["debate_state"]["bull_history"] += f"\n\n## Round {round_num} - Bull\n{result['argument']}"
        state["debate_state"]["full_history"] += f"\n\n[Round {round_num} - Bull]\n{result['argument']}"
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + [f"Bull Round {round_num} 완료"]
        return state
    
    def bear_argue(state: ReportState) -> ReportState:
        opponent_arg = state["debate_state"].get("current_bull_arg")
        round_num = state["debate_state"]["debate_count"] + 1
        print(f"\n{'='*80}")
        print(f"🔵 ROUND {round_num} - Bear Agent 주장 생성 중...")
        print('='*80)
        
        result = bear_agent.argue(state, opponent_last_arg=opponent_arg)
        
        state["debate_state"]["current_bear_arg"] = result["argument"]
        state["debate_state"]["bear_history"] += f"\n\n## Round {round_num} - Bear\n{result['argument']}"
        state["debate_state"]["full_history"] += f"\n\n[Round {round_num} - Bear]\n{result['argument']}"
        state["debate_state"]["debate_count"] += 1
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + [f"Bear Round {state['debate_state']['debate_count']} 완료"]
        return state
    
    def judge_debate(state: ReportState) -> ReportState:
        print(f"\n{'='*80}")
        print("⚖️ Judge Agent - 토론 판결 중...")
        print('='*80)
        verdict = judge_agent.judge(state)
        print(f"\n👨‍⚖️ 판결 (Verdict): {verdict.get('decision')} (Score: {verdict.get('score')})")
        print(f"👉 승자: {verdict.get('winning_side')}")
        state["judge_verdict"] = verdict
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + ["Judge 판결 완료"]
        return state

    def synthesize_report(state: ReportState) -> ReportState:
        print(f"\n{'='*80}")
        print("🧠 Synthesizer - 최종 Investment Memo 생성 중...")
        print('='*80)
        final_report = synthesizer_agent.synthesize(state)
        state["synthesis_report"] = final_report
        state["final_report"] = final_report
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + ["Synthesizer 리포트 생성 완료"]
        return state

    def validate_report(state: ReportState) -> ReportState:
        """Validator로 리포트 검수"""
        if not validator_agent:
            print("\n⚠️ Validator Agent가 설정되지 않아 검수를 건너뜁니다.")
            return state
            
        print(f"\n{'='*80}")
        print("🛡️ Validator - 리포트 품질 및 팩트 체크 중...")
        print('='*80)
        
        validation_result = validator_agent.validate(state)
        decision = validation_result.get("validation_decision", "fail")
        feedback = validation_result.get("validation_feedback", "")
        
        print(f"\n🔍 검수 결과: {decision.upper()}")
        print(f"📝 피드백:\n{feedback}")
        
        # State에 검수 결과 저장 (나중에 LOOP 등 확장 가능)
        state["validation_result"] = validation_result
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + [f"Validator 검수 완료 ({decision})"]
        
        return state

    def should_continue_debate(state: ReportState) -> Literal["continue", "judge"]:
        debate_count = state["debate_state"].get("debate_count", 0)
        if debate_count < 3:
            return "continue"
        else:
            return "judge"
    
    workflow = StateGraph(ReportState)
    
    workflow.add_node("initialize", initialize_debate)
    
    # Note: graphrag_search, price_load 노드 제거됨
    # → LLM Tool Calling (explore_graph, get_price_context)로 대체
    
    workflow.add_node("bull", bull_argue)
    workflow.add_node("bear", bear_argue)
    workflow.add_node("judge", judge_debate)
    workflow.add_node("synthesizer", synthesize_report)
    workflow.add_node("validator", validate_report)
    
    workflow.set_entry_point("initialize")
    
    # 초기화 후 바로 토론 시작 (데이터는 Tool Calling으로 동적 조회)
    workflow.add_edge("initialize", "bull")
    
    # 순환 토론 (Bull <-> Bear) -> Synthesizer
    workflow.add_edge("bull", "bear")
    
    workflow.add_conditional_edges(
        "bear",
        should_continue_debate,
        {
            "continue": "bull",
            "judge": "judge"
        }
    )
    
    workflow.add_edge("judge", "synthesizer")
    workflow.add_edge("synthesizer", "validator") # Validate after synthesis
    workflow.add_edge("validator", END)
    
    return workflow.compile()


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
