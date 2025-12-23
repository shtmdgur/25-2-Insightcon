from typing import Dict, Any, List
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config.prompt_loader import load_prompts

class ValidatorAgent:
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1)
        self.prompts = load_prompts()
        self.template = self.prompts['validator']['instruction']

    def validate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates the generated report for factuality and style.
        """
        report_initial = state.get("final_report", "")
        debate_state = state.get("debate_state", {})
        bull_history = debate_state.get("bull_history", "")
        bear_history = debate_state.get("bear_history", "")
        context_data = f"Bull Arguments: {bull_history}\nBear Arguments: {bear_history}"

        # 1. Format Prompt (Python str.format)
        prompt = self.template.format(
            report_content=report_initial,
            context_data=context_data
        )
        
        # 2. Invoke LLM
        response = self.llm.invoke(prompt)
        
        # 3. Parse JSON
        parser = JsonOutputParser()
        parsed_result = parser.parse(response.content)
        
        return {
            "validation_decision": parsed_result.get("decision", "fail"),
            "validation_feedback": parsed_result.get("feedback", "")
        }
