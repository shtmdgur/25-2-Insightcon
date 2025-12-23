"""
변증법 토론 워크플로우 (LangGraph 기반)

Bull → Bear → 반복 → Synthesizer 순서로 실행되는 토론 워크플로우
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from src.pipeline.state import ReportState, DebateState


def create_debate_workflow(bull_agent, bear_agent, synthesizer_agent):
    """
    변증법 토론 워크플로우 생성
    
    Args:
        bull_agent: BullAgent 인스턴스
        bear_agent: BearAgent 인스턴스
        synthesizer_agent: SynthesizerAgent 인스턴스
    
    Returns:
        Compiled LangGraph workflow
    """
    
    # ========================================
    # Node Functions
    # ========================================
    
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
            "cached_paths": {},  # Progressive Path Expansion 캐시
            "debate_trace": []   # Debate 전용 trace
        }
        
        state["debate_state"] = debate_state
        return state
    
    def bull_argue(state: ReportState) -> ReportState:
        """Bull Agent 주장 생성"""
        # Bear의 이전 주장 (있으면)
        opponent_arg = state["debate_state"].get("current_bear_arg")
        
        round_num = state["debate_state"]["debate_count"] + 1
        print(f"\n{'='*80}")
        print(f"🔴 ROUND {round_num} - Bull Agent 주장 생성 중...")
        print('='*80)
        
        # Bull 주장 생성
        result = bull_agent.argue(state, opponent_last_arg=opponent_arg)
        
        # 실시간 출력
        lines = result["argument"].split('\n')
        preview = '\n'.join(lines)
        print(f"\n📝 Bull 주장:\n{preview}")
        
        # State 직접 업데이트 (참조 복사 문제 해결)
        state["debate_state"]["current_bull_arg"] = result["argument"]
        state["debate_state"]["bull_history"] += f"\n\n## Round {round_num} - Bull\n{result['argument']}"
        state["debate_state"]["full_history"] += f"\n\n[Round {round_num} - Bull]\n{result['argument']}"
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + [f"Bull Round {round_num} 완료"]
        
        return state
    
    def bear_argue(state: ReportState) -> ReportState:
        """Bear Agent 주장 생성"""
        # Bull의 현재 주장
        opponent_arg = state["debate_state"].get("current_bull_arg")
        
        round_num = state["debate_state"]["debate_count"] + 1
        print(f"\n{'='*80}")
        print(f"🔵 ROUND {round_num} - Bear Agent 주장 생성 중...")
        print('='*80)
        
        # Bear 주장 생성
        result = bear_agent.argue(state, opponent_last_arg=opponent_arg)
        
        # 실시간 출력
        lines = result["argument"].split('\n')
        preview = '\n'.join(lines)
        print(f"\n📝 Bear 주장:\n{preview}")
        
        # State 직접 업데이트 (참조 복사 문제 해결)
        state["debate_state"]["current_bear_arg"] = result["argument"]
        state["debate_state"]["bear_history"] += f"\n\n## Round {round_num} - Bear\n{result['argument']}"
        state["debate_state"]["full_history"] += f"\n\n[Round {round_num} - Bear]\n{result['argument']}"
        
        # 라운드 증가
        state["debate_state"]["debate_count"] += 1
        
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + [f"Bear Round {state['debate_state']['debate_count']} 완료"]
        return state
    
    def synthesize_report(state: ReportState) -> ReportState:
        """Synthesizer로 최종 리포트 생성"""
        print(f"\n{'='*80}")
        print("🧠 Synthesizer - 최종 Investment Memo 생성 중...")
        print('='*80)
        
        # Synthesizer 실행
        final_report = synthesizer_agent.synthesize(state)
        
        # 실시간 출력
        report_preview = final_report[:400] + "..." if len(final_report) > 400 else final_report
        print(f"\n📝 최종 리포트 Preview:\n{report_preview}")
        
        # State 직접 업데이트 (참조 복사 문제 해결)
        state["synthesis_report"] = final_report
        state["final_report"] = final_report  # 최종 리포트로도 저장
        state["debate_state"]["debate_trace"] = state["debate_state"].get("debate_trace", []) + ["Synthesizer 리포트 생성 완료"]
        
        return state
    
    # ========================================
    # Conditional Logic
    # ========================================
    
    def should_continue_debate(state: ReportState) -> Literal["continue", "synthesize"]:
        """
        토론 계속 여부 판단
        
        조건:
        - debate_count < 3: 계속
        - debate_count >= 3: Synthesizer로 이동
        """
        debate_state = state["debate_state"]
        debate_count = debate_state.get("debate_count", 0)
        
        if debate_count < 3:
            return "continue"
        else:
            return "synthesize"
    
    # ========================================
    # Workflow 구성
    # ========================================
    
    workflow = StateGraph(ReportState)
    
    # 노드 추가
    workflow.add_node("initialize", initialize_debate)
    from src.pipeline.price_nodes import load_price_context_node  # Dynamic Import to avoid circular deps
    workflow.add_node("price_load", load_price_context_node)
    
    workflow.add_node("bull", bull_argue)
    workflow.add_node("bear", bear_argue)
    workflow.add_node("synthesizer", synthesize_report)
    
    # 엣지 연결
    workflow.set_entry_point("initialize")
    
    # [Price DB Integration] 초기화 후 가격 데이터 로드
    workflow.add_edge("initialize", "price_load")
    workflow.add_edge("price_load", "bull")
    
    # 순환 토론 (Bull <-> Bear) -> Synthesizer
    workflow.add_edge("bull", "bear")
    
    # 조건부 분기: Bear → Bull (계속) 또는 Synthesizer (종료)
    workflow.add_conditional_edges(
        "bear",
        should_continue_debate,
        {
            "continue": "bull",      # 3라운드 미만: Bull로 돌아감
            "synthesize": "synthesizer"  # 3라운드 완료: Synthesizer로
        }
    )
    
    # Synthesizer → END
    workflow.add_edge("synthesizer", END)
    
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
