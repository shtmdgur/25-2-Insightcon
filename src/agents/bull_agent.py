from typing import Dict, Any, Optional
from .base_debate_agent import BaseDebateAgent

class BullAgent(BaseDebateAgent):
    """
    긍정론 에이전트 (Bull View)
    """
    
    def __init__(self, llm, neo4j_connection=None):
        super().__init__(llm, neo4j_connection, role="bull")
        

    def argue(
        self, 
        state: Dict[str, Any], 
        opponent_last_arg: Optional[str] = None
    ) -> Dict[str, str]:
        # 1. Broad Search & 하이브리드 데이터 추출
        data = self._extract_data_from_state(state)
        # 프롬프트 포맷팅을 위해 query 명시적 전달
        data["query"] = state.get("query", "")
        
        # 2. 프롬프팅 (YAML 지침 + 인지적 필터링)
        prompt = self._build_prompt(
            query=state.get("query", ""),
            data=data,
            opponent_arg=opponent_last_arg,
            history=state.get("debate_state", {}).get("bull_history", "")
        )
        
        # 3. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 4. 응답 파싱
        return self._parse_response(response)
