from typing import Dict, Any, List, Optional
import json
from .base_debate_agent import BaseDebateAgent

class ValidatorAgent(BaseDebateAgent):
    """
    품질 검수 에이전트 (Compliance & Quality Control)
    
    역할:
    - 최종 리포트의 사실 관계 검증 (Hallucination 체크)
    - 논리적 일관성 및 전문적 톤앤매너 검수
    - Mermaid 다이어그램 등 기술적 문법 확인
    """
    
    def __init__(self, llm, neo4j_connection=None):
        super().__init__(llm, neo4j_connection, role="validator")

    def argue(self, state: Dict[str, Any], opponent_last_arg: Optional[str] = None) -> Dict[str, str]:
        # Validator는 토론에 참여하지 않음
        return {"argument": "저는 검수자입니다. 최종 결과물만 검수합니다."}

    def validate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        생성된 리포트의 사실성 및 스타일 검증
        """
        report_content = state.get("synthesis_report", "") or state.get("final_report", "")
        debate_state = state.get("debate_state", {})
        bull_history = debate_state.get("bull_history", "")
        bear_history = debate_state.get("bear_history", "")
        context_data = f"Bull Arguments: {bull_history}\nBear Arguments: {bear_history}"

        # 1. 템플릿 로드
        template = self.prompts.get("validator", {}).get("instruction", "")
        
        if not template:
            # Fallback (YAML 로드 실패 시)
            return {"decision": "pass", "feedback": "Validator template not found, skipping validation."}

        # 2. 프롬프트 구성
        prompt = template.format(
            query=state.get("query", "알 수 없음"),
            report_content=report_content,
            context_data=context_data
        )
        
        # 3. LLM 실행
        response = self.llm.invoke(prompt)
        
        # 4. JSON 파싱
        return self._parse_json_response(response)

    def _parse_json_response(self, response: Any) -> Dict[str, Any]:
        """JudgeAgent와 동일한 방식의 JSON 파싱 로직 (필요시 Base로 이동 가능)"""
        text = response.content if hasattr(response, "content") else str(response)
        
        # Handle list/dict content
        if isinstance(text, list):
            text = "".join([item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in text])
        elif isinstance(text, dict):
            text = text.get("text", str(text))
            
        text = str(text)
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback
            return {
                "decision": "fail",
                "feedback": f"JSON Parsing Failed. Raw: {text[:200]}"
            }
