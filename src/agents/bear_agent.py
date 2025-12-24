from typing import Dict, Any, Optional
from .base_debate_agent import BaseDebateAgent

class BearAgent(BaseDebateAgent):
    """
    부정론 에이전트 (Bear View)
    """
    
    def __init__(self, llm, neo4j_connection=None):
        super().__init__(llm, neo4j_connection, role="bear")
        

    def argue(
        self, 
        state: Dict[str, Any], 
        opponent_last_arg: Optional[str] = None
    ) -> Dict[str, str]:
        # 1. Broad Search & 하이브리드 데이터 추출
        data = self._extract_data_from_state(state)
        data["query"] = state.get("query", "")
        
        # 2. 프롬프팅 (YAML 지침 + 인지적 필터링)
        prompt = self._build_prompt(
            query=state.get("query", ""),
            data=data,
            opponent_arg=opponent_last_arg,
            history=state.get("debate_state", {}).get("bear_history", "")
        )
        
        # 3. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 4. 응답 파싱
        result = self._parse_response(response)
        result["retrieved_data"] = data
        return result
