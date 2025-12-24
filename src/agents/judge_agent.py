from typing import Dict, Any, Optional, List
import json
from .base_debate_agent import BaseDebateAgent

class JudgeAgent(BaseDebateAgent):
    """
    판사 에이전트 (Judge / Decision Maker)
    
    역할:
    - Bull/Bear 토론 내용을 공정하게 평가
    - 증거(Impact Path)의 신뢰도와 논리적 완결성 검증
    - 최종 투자의견(Verdict) 도출 및 근거 제시
    """
    
    def __init__(self, llm, neo4j_connection=None):
        super().__init__(llm, neo4j_connection, role="judge")
        
    def argue(self, state: Dict[str, Any], opponent_last_arg: Optional[str] = None) -> Dict[str, str]:
        # Judge는 토론에 참여하지 않음
        return {"argument": "저는 판사입니다. 판결만 내립니다."}

    def judge(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        토론을 평가하고 최종 판결을 내림
        
        Returns:
            Dict containing:
            - decision: STR (BUY/SELL/HOLD)
            - score: INT (0-100)
            - confidence_level: STR (High/Medium/Low)
            - winning_side: STR (Bull/Bear)
            - key_factors: List[str]
            - rationale: str (Detailed explanation)
        """
        # 1. 토론 이력 및 데이터 추출
        debate_state = state.get("debate_state", {})
        bull_history = debate_state.get("bull_history", "")
        bear_history = debate_state.get("bear_history", "")
        
        # [TOKEN LIMIT FIX] 히스토리 길이 제한 (각 15000자)
        MAX_HISTORY_LEN = 15000
        if len(bull_history) > MAX_HISTORY_LEN:
            bull_history = bull_history[:MAX_HISTORY_LEN] + "\n\n[...이전 내용 생략...]"
        if len(bear_history) > MAX_HISTORY_LEN:
            bear_history = bear_history[:MAX_HISTORY_LEN] + "\n\n[...이전 내용 생략...]"
        
        data = self._extract_data_from_state(state)
        # Impact paths도 길이 제한
        impact_paths = str(data.get("impact_paths", []))[:5000]
        
        # 2. 템플릿 로드
        template = self.prompts.get("debate_agents", {}).get("judge", {}).get("instruction", "")
        
        # 3. 프롬프트 구성
        prompt = template.format(
            ticker=state.get("query", ""),
            bull_history=bull_history,
            bear_history=bear_history,
            critical_paths=impact_paths,
            market_context=state.get("market_context", "No market data available."),
            document_context=self._format_document_summary(data.get("document_summary"))
        )
        
        # 4. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 5. 결과 파싱 (JSON 형태 예상)
        return self._parse_json_response(response)

    def _parse_json_response(self, response: Any) -> Dict[str, Any]:
        """LLM 응답에서 JSON 추출 및 파싱"""
        text = response.content if hasattr(response, "content") else str(response)
        
        # Handle list content (common in some Gemini versions)
        if isinstance(text, list):
            # text = "".join([str(item) for item in text]) # OLD
            text_parts = []
            for item in text:
                if isinstance(item, dict) and "text" in item:
                    text_parts.append(item["text"])
                elif hasattr(item, "text"):
                        text_parts.append(item.text)
                else:
                    text_parts.append(str(item))
            text = "".join(text_parts)
            
        if isinstance(text, dict):
             text = text.get("text", str(text))
        
        # Ensure it is a string
        text = str(text)
        
        # Markdown Code block 제거
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"[JudgeAgent] JSON Parsing Failed. Raw text: {text[:100]}...")
            # Fallback 구조
            return {
                "decision": "HOLD",
                "score": 50,
                "confidence_level": "Low",
                "winning_side": "Neutral",
                "key_factors": ["Parsing Error"],
                "rationale": text
            }
