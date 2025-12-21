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
        
        # 2. Broad Search (중요 경로 검증용)
        data = self._extract_data_from_state(state)
        
        # 3. 템플릿 로드
        template = self.prompts.get("debate_agents", {}).get("synthesizer", {}).get("instruction", "")
        
        # 4. 프롬프트 구성
        prompt = template.format(
            ticker=state.get("query", ""),
            bull_history=bull_history,
            bear_history=bear_history,
            critical_paths=str(data.get("impact_paths", []))
        )
        
        # 5. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 6. 콘텐츠 반환 (Markdown 리포트)
        if hasattr(response, "content"):
            return response.content
        return str(response)
