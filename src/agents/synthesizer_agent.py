from typing import Dict, Any, Optional
from .base_debate_agent import BaseDebateAgent

class SynthesizerAgent(BaseDebateAgent):
    """
    종합 에이전트 (Synthesizer / CIO Role)
    """
    
    def __init__(self, llm, neo4j_connection=None):
        super().__init__(llm, neo4j_connection, role="synthesizer")
        

    def argue(self, state: Dict[str, Any], opponent_last_arg: Optional[str] = None) -> Dict[str, str]:
        # Synthesizer는 argue를 사용하지 않지만, 인터페이스 호환성을 위해 구현
        return {"argument": "저는 종합 에이전트입니다."}

    def synthesize(self, state: Dict[str, Any]) -> str:
        """
        토론 종합 및 최종 리포트 생성
        
        Args:
            state: ReportState (debate_state에서 bull_history, bear_history 추출)
        
        Returns:
            최종 투자 판단 리포트 (Markdown)
        """
        # 1. State에서 토론 이력 추출
        debate_state = state.get("debate_state", {})
        bull_history = debate_state.get("bull_history", "")
        bear_history = debate_state.get("bear_history", "")
        full_history = debate_state.get("full_history", "")
        
        # 2. Judge 결과 추출 (없으면 기본값)
        judge_result = debate_state.get("judge_result", {})
        rationale = judge_result.get("rationale", "Judge 판결 결과 없음")
        decision = judge_result.get("decision", "HOLD")
        score = judge_result.get("score", 50)
        confidence_level = judge_result.get("confidence_level", "Medium")
        winning_side = judge_result.get("winning_side", "Neutral")
        
        # Broad Search (중요 경로 검증용)
        data = self._extract_data_from_state(state)
        
        # 3. 템플릿 로드
        template = self.prompts.get("debate_agents", {}).get("synthesizer", {}).get("instruction", "")
        
        # 4. 프롬프트 구성 (모든 필요한 변수 포함)
        try:
            prompt = template.format(
                ticker=state.get("query", ""),
                rationale=rationale,
                history=full_history,
                evidence_paths=str(data.get("impact_paths", [])),
                decision=decision,
                score=score,
                confidence_level=confidence_level,
                winning_side=winning_side,
                bull_history=bull_history,
                bear_history=bear_history,
                critical_paths=str(data.get("impact_paths", [])),
                target_date=state.get("target_date", ""),
                risk_profile="중립",
                rationale_summary=rationale[:200] if len(rationale) > 200 else rationale,
                bull_outcome="매수 논지",
                bear_outcome="매도 논지"
            )
        except KeyError as e:
            # 템플릿에 없는 변수가 있으면 간소화된 프롬프트 사용
            print(f"[경고] Synthesizer 템플릿 변수 누락: {e}. 기본 프롬프트 사용.")
            prompt = f"""
            당신은 투자 리서치 애널리스트입니다.
            
            [Judge 판결]
            - Decision: {decision}
            - Score: {score}/100
            - Rationale: {rationale}
            
            [Bull 논거]
            {bull_history}
            
            [Bear 논거]
            {bear_history}
            
            위 토론 내용을 바탕으로 {state.get('query', '')}에 대한 투자 리포트를 작성하세요.
            """
        
        # 5. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 6. 응답 파싱 (signature 제거)
        result = self._parse_response(response)
        return result["argument"]

