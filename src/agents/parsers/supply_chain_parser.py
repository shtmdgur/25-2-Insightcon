"""
Supply Chain Parser
PDF 리포트에서 밸류체인 정보 추출 (SUPPLIES, MANUFACTURES 관계)
"""

from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
import json
import logging

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph, Entity, Relation, NodeType, RelationType
from src.config.prompt_loader import get_prompt

logger = logging.getLogger(__name__)

class SupplyChainParser(BaseParserAgent):
    """
    공급망 정보 추출 Parser
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        super().__init__(name="SupplyChainParser")
        self.llm = llm
    
    def parse_from_text(self, text: str) -> KnowledgeGraph:
        """
        텍스트에서 공급망 관계 추출
        """
        prompt_template = """
        다음 리서치 리포트 텍스트에서 반도체 밸류체인 관계(공급, 생산)를 추출하세요.
        
        [지침]
        1. 공급 관계 (SUPPLIES): A사가 B사에게 특정 제품/장비를 공급하는 경우
        2. 생산 관계 (MANUFACTURES): A사가 특정 제품(HBM, 파운드리 등)을 생산하는 경우
        3. 엔티티 타입: IDM, FABLESS, FOUNDRY, SUPPLIER 중 적절한 것을 선택하십시오.
        
        [리포트 텍스트]
        {text}
        
        [출력 형식 (Structured JSON)]
        {{
          "entities": [
            {{ "name": "기업명", "type": "IDM|FABLESS|FOUNDRY|SUPPLIER" }}
          ],
          "relations": [
            {{ "subject": "주어", "predicate": "SUPPLIES|MANUFACTURES", "object": "목적어" }}
          ]
        }}
        """
        
        formatted_prompt = prompt_template.format(text=text[:10000]) # 텍스트 길이 제한
        
        try:
            response = self.llm.invoke(formatted_prompt)
            data = self._parse_json_response(response.content)
            
            entities = [
                Entity(name=e["name"], type=NodeType(e["type"]), confidence=0.9)
                for e in data.get("entities", [])
            ]
            relations = [
                Relation(
                    subject=r["subject"],
                    predicate=RelationType(r["predicate"]),
                    object=r["object"]
                )
                for r in data.get("relations", [])
            ]
            
            return KnowledgeGraph(entities=entities, relations=relations)
            
        except Exception as e:
            logger.error(f"SupplyChainParser failed: {e}")
            return KnowledgeGraph(entities=[], relations=[])

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """LLM 응답에서 JSON 추출"""
        try:
            # 코드 블록 제거
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except Exception:
            return {}
