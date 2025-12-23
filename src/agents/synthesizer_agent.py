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
        토론 종합 및 최종 리포트 생성 (Judge의 판결 기반)
        
        Args:
            state: ReportState containing:
                   - debate_state: bull_history, bear_history
                   - judge_verdict: Dict (from JudgeAgent)
        
        Returns:
            최종 투자 판단 리포트 (Markdown)
        """
        # 1. State에서 데이터 추출
        debate_state = state.get("debate_state", {})
        bull_history = debate_state.get("bull_history", "")
        bear_history = debate_state.get("bear_history", "")
        judge_verdict = state.get("judge_verdict", {})
        
        # 2. 템플릿 로드
        template = self.prompts.get("debate_agents", {}).get("synthesizer", {}).get("instruction", "")
        
        # 3. 프롬프트 구성
        # Judge Verdict가 딕셔너리이므로 보기 좋게 JSON 문자열이나 포맷팅된 문자열로 변환
        import json
        verdict_str = json.dumps(judge_verdict, indent=2, ensure_ascii=False)
        
        # 안전한 get을 위해 기본값 설정
        decision = judge_verdict.get("decision", "HOLD")
        score = judge_verdict.get("score", 50)
        confidence = judge_verdict.get("confidence_level", "Medium")
        rationale = judge_verdict.get("rationale", "No rationale provided.")
        winning_side = judge_verdict.get("winning_side", "Neutral")
        
        # 템플릿 채우기 (나머지 변수들도 포맷팅에 사용될 수 있도록 준비)
        prompt = template.format(
            ticker=state.get("query", ""),
            bull_history=bull_history,
            bear_history=bear_history,
            judge_verdict=verdict_str,
            decision=decision,
            score=score,
            confidence_level=confidence,
            rationale_summary=rationale[:100] + "..." if len(rationale) > 100 else rationale, # 요약용
            rationale=rationale, # Full text for reference in instructions
            winning_side=winning_side,
            bull_outcome="Winner" if winning_side == "Bull" else "Loser",
            bear_outcome="Winner" if winning_side == "Bear" else "Loser",
            history=f"Bull History:\n{bull_history}\n\nBear History:\n{bear_history}"
        )
        
        # 4. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 5. 응답 파싱
        result = self._parse_response(response)
        return result["argument"]
