"""
이벤트 추출기

뉴스에서 이벤트를 추출하고 Neo4j에 저장합니다.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import numpy as np

import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

# Prompts YAML 로드
PROMPTS_FILE = Path(__file__).parent.parent / "templates" / "prompts.yaml"
with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
    PROMPTS = yaml.safe_load(f)


class EventExtractor:
    """
    뉴스에서 이벤트 추출 및 Neo4j 저장
    """
    
    def __init__(self, llm, neo4j_client):
        """
        Args:
            llm: LLM 모델
            neo4j_client: Neo4j 클라이언트
        """
        self.llm = llm
        self.neo4j_client = neo4j_client
    
    def extract_events_from_news(
        self,
        news_text: str,
        date: str,
        source: str = "unknown"
    ) -> Dict[str, Any]:
        """
        뉴스에서 이벤트 추출
        
        Args:
            news_text: 뉴스 텍스트
            date: 뉴스 날짜 (YYYY-MM-DD)
            source: 출처
        
        Returns:
            추출된 이벤트 정보
        """
        # YAML에서 프롬프트 로드
        prompt_template = PROMPTS.get('event_extractor', {}).get('news_extraction', {}).get('instruction', '')
        
        if not prompt_template:
            raise RuntimeError(
                "Prompt not found in prompts.yaml at 'event_extractor.news_extraction.instruction'. "
                "Please check the YAML file configuration."
            )
        
        # 템플릿에 news_text 삽입
        prompt = prompt_template.replace('{news_text}', news_text)
        
        try:
            response = self.llm.invoke(prompt)
            
            # JSON 파싱
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                event = json.loads(json_match.group(0))
                
                # Neo4j에 저장
                neo4j_result = self._save_event_to_neo4j(event, date, source)
                
                return {
                    "event": event,
                    "neo4j_result": neo4j_result
                }
            else:
                logger.warning("No event extracted from news")
                return {"event": None}
                
        except Exception as e:
            logger.error(f"Event extraction failed: {str(e)}")
            return {"error": str(e)}
    
    def _save_event_to_neo4j(
        self,
        event: Dict[str, Any],
        date: str,
        source: str
    ) -> Dict[str, int]:
        """
        추출된 이벤트를 Neo4j에 저장
        
        Args:
            event: 이벤트 정보
            date: 날짜
            source: 출처
        
        Returns:
            저장 통계
        """
        try:
            # Time decay 가중치 계산
            weight = self._calculate_time_decay(date)
            
            # Event 노드 생성
            self.neo4j_client.run("""
                CREATE (e:Event {
                    type: $event_type,
                    description: $description,
                    date: date($date),
                    importance: $importance,
                    impact: $impact,
                    source: $source,
                    weight: $weight,
                    created_at: datetime()
                })
                WITH e
                UNWIND $affected_entities AS entity_name
                MATCH (c:Company {name: entity_name})
                MERGE (e)-[:AFFECTS {weight: $weight}]->(c)
            """, {
                "event_type": event.get("event_type", "Unknown"),
                "description": event.get("description", ""),
                "date": date,
                "importance": event.get("importance", 5),
                "impact": event.get("impact", "neutral"),
                "source": source,
                "weight": weight,
                "affected_entities": event.get("affected_entities", [])
            })
            
            logger.info(f"Saved event: {event.get('event_type')} on {date}")
            
            return {
                "events_created": 1,
                "relations_created": len(event.get("affected_entities", []))
            }
            
        except Exception as e:
            logger.error(f"Failed to save event to Neo4j: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_time_decay(
        self,
        event_date: str,
        current_date: str = None
    ) -> float:
        """
        시간 감쇠 가중치 계산
        
        최근 이벤트일수록 가중치 ↑
        
        Args:
            event_date: 이벤트 날짜 (YYYY-MM-DD)
            current_date: 현재 날짜 (기본: 오늘)
        
        Returns:
            감쇠 가중치 (0.1~1.0)
        """
        try:
            event_dt = datetime.strptime(event_date, "%Y-%m-%d")
            current_dt = datetime.strptime(current_date, "%Y-%m-%d") if current_date else datetime.now()
            
            days_diff = (current_dt - event_dt).days
            
            # 90일 반감기
            decay_factor = np.exp(-days_diff / 90)
            
            # 최소 0.1
            return max(decay_factor, 0.1)
            
        except Exception as e:
            logger.warning(f"Time decay calculation failed: {str(e)}")
            return 0.5  # 기본값
