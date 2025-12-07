"""
지식 그래프 구축 에이전트
문서에서 엔티티와 관계를 추출하여 Neo4j에 주입
"""
from typing import List, Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
import json

from ..utils.neo4j_client import Neo4jClient


class KGConstructionAgent:
    """
    문서에서 엔티티와 관계를 추출하여 지식 그래프를 구축하는 에이전트
    """
    
    def __init__(self, llm: BaseChatModel, neo4j_client: Neo4jClient):
        """
        KGConstructionAgent 초기화
        
        Args:
            llm: LLM 모델 (엔티티/관계 추출에 사용)
            neo4j_client: Neo4j 클라이언트
        """
        self.llm = llm
        self.neo4j_client = neo4j_client
    
    def extract_entities(self, document: str) -> Dict[str, Any]:
        """
        문서에서 엔티티 추출
        
        Args:
            document: 분석할 문서 텍스트
        
        Returns:
            추출된 엔티티 정보
        """
        prompt = f"""
        다음 문서에서 엔티티를 추출하세요.
        
        문서:
        {document}
        
        추출할 엔티티:
        - Company (기업)
        - ProductLine (제품)
        - Metric (재무 지표)
        
        JSON 형식:
        {{
            "companies": [{{"name": "...", "properties": {{}}}}],
            "products": [{{"name": "...", "properties": {{}}}}],
            "metrics": [{{"name": "...", "value": "...", "properties": {{}}}}]
        }}
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content
            
            # JSON 파싱
            entities = json.loads(content)
            return entities
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트에서 수동 추출 시도
            return self._fallback_extraction(content)
        except Exception as e:
            raise RuntimeError(f"엔티티 추출 실패: {str(e)}")
    
    def inject_to_neo4j(self, entities: Dict[str, Any]) -> Dict[str, int]:
        """
        추출된 엔티티를 Neo4j에 주입
        
        Args:
            entities: 추출된 엔티티 정보
        
        Returns:
            주입된 엔티티 개수 통계
        """
        stats = {
            "companies": 0,
            "products": 0,
            "metrics": 0,
            "relationships": 0
        }
        
        try:
            # Company 노드 생성
            for company in entities.get('companies', []):
                company_name = company.get('name')
                if not company_name:
                    continue
                
                company_props = company.get('properties', {})
                # Neo4j 호환성을 위해 SET 구문을 개별 속성으로 설정
                if company_props:
                    # 속성을 개별적으로 설정
                    # 주의: 속성 이름에 특수문자가 있으면 이스케이프 필요
                    set_clauses = ", ".join([f"c.`{k}` = ${k}" for k in company_props.keys()])
                    params = {"name": company_name, **company_props}
                    self.neo4j_client.run(f"""
                        MERGE (c:Company {{name: $name}})
                        SET {set_clauses}
                    """, params)
                else:
                    self.neo4j_client.run("""
                        MERGE (c:Company {name: $name})
                    """, {"name": company_name})
                stats["companies"] += 1
            
            # ProductLine 노드 생성
            for product in entities.get('products', []):
                product_name = product.get('name')
                if not product_name:
                    continue
                
                product_props = product.get('properties', {})
                if product_props:
                    set_clauses = ", ".join([f"p.`{k}` = ${k}" for k in product_props.keys()])
                    params = {"name": product_name, **product_props}
                    self.neo4j_client.run(f"""
                        MERGE (p:ProductLine {{name: $name}})
                        SET {set_clauses}
                    """, params)
                else:
                    self.neo4j_client.run("""
                        MERGE (p:ProductLine {name: $name})
                    """, {"name": product_name})
                stats["products"] += 1
            
            # Metric 노드 생성
            for metric in entities.get('metrics', []):
                metric_name = metric.get('name')
                if not metric_name:
                    continue
                
                metric_props = {
                    **metric.get('properties', {}),
                    "value": metric.get('value', '')
                }
                if metric_props:
                    set_clauses = ", ".join([f"m.`{k}` = ${k}" for k in metric_props.keys()])
                    params = {"name": metric_name, **metric_props}
                    self.neo4j_client.run(f"""
                        MERGE (m:Metric {{name: $name}})
                        SET {set_clauses}
                    """, params)
                else:
                    self.neo4j_client.run("""
                        MERGE (m:Metric {name: $name})
                    """, {"name": metric_name})
                stats["metrics"] += 1
            
            # 관계 생성 (간단한 버전)
            # 주의: 현재는 모든 제품/지표를 모든 기업에 연결하는 단순 로직
            # 실제로는 문서에서 추출한 관계 정보를 사용해야 함
            # 예: company['products'] 리스트에 해당 기업의 제품만 포함
            for company in entities.get('companies', []):
                company_name = company.get('name')
                if not company_name:
                    continue
                
                # Company -[MANUFACTURES]-> ProductLine 관계
                # TODO: company['products'] 같은 속성에서 실제 관계 추출
                for product in entities.get('products', []):
                    product_name = product.get('name')
                    if not product_name:
                        continue
                    
                    try:
                        self.neo4j_client.run("""
                            MATCH (c:Company {name: $company_name})
                            MATCH (p:ProductLine {name: $product_name})
                            MERGE (c)-[:MANUFACTURES]->(p)
                        """, {
                            "company_name": company_name,
                            "product_name": product_name
                        })
                        stats["relationships"] += 1
                    except Exception:
                        # 관계 생성 실패는 무시 (이미 존재하거나 노드가 없을 수 있음)
                        pass
                
                # Company -[HAS_METRIC]-> Metric 관계
                # TODO: company['metrics'] 같은 속성에서 실제 관계 추출
                for metric in entities.get('metrics', []):
                    metric_name = metric.get('name')
                    if not metric_name:
                        continue
                    
                    try:
                        self.neo4j_client.run("""
                            MATCH (c:Company {name: $company_name})
                            MATCH (m:Metric {name: $metric_name})
                            MERGE (c)-[:HAS_METRIC]->(m)
                        """, {
                            "company_name": company_name,
                            "metric_name": metric_name
                        })
                        stats["relationships"] += 1
                    except Exception:
                        # 관계 생성 실패는 무시
                        pass
            
            return stats
        except Exception as e:
            raise RuntimeError(f"Neo4j 주입 실패: {str(e)}")
    
    def process_document(self, document: str) -> Dict[str, Any]:
        """
        문서를 처리하여 지식 그래프 구축
        
        Args:
            document: 처리할 문서
        
        Returns:
            처리 결과 (엔티티, 통계 등)
        """
        # 엔티티 추출
        entities = self.extract_entities(document)
        
        # Neo4j에 주입
        stats = self.inject_to_neo4j(entities)
        
        return {
            "entities": entities,
            "stats": stats
        }
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """JSON 파싱 실패 시 대체 추출 방법"""
        # 간단한 대체 로직 (실제로는 더 정교한 로직 필요)
        return {
            "companies": [],
            "products": [],
            "metrics": []
        }
