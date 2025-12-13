"""
Neo4j 클라이언트 유틸리티
"""
import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j 그래프 데이터베이스 클라이언트 래퍼"""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        """
        Neo4j 클라이언트 초기화
        
        Args:
            uri: Neo4j URI (기본값: 환경변수 NEO4J_URI)
            username: 사용자명 (기본값: 환경변수 NEO4J_USERNAME)
            password: 비밀번호 (기본값: 환경변수 NEO4J_PASSWORD)
            database: 데이터베이스명 (기본값: 환경변수 NEO4J_DATABASE 또는 "neo4j")
        """
        self.uri = uri or os.getenv("NEO4J_URI")
        self.username = username or os.getenv("NEO4J_USERNAME")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError(
                "Neo4j 연결 정보가 없습니다. "
                "환경변수 또는 생성자 인자로 제공해주세요."
            )
        
        self.graph = Neo4jGraph(
            url=self.uri,
            username=self.username,
            password=self.password,
            database=self.database
        )
    
    def query(self, cypher_query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Cypher 쿼리 실행
        
        Args:
            cypher_query: 실행할 Cypher 쿼리
            parameters: 쿼리 파라미터 (선택)
        
        Returns:
            쿼리 실행 결과
        """
        try:
            if parameters:
                result = self.graph.query(cypher_query, params=parameters)
            else:
                result = self.graph.query(cypher_query)
            return result
        except Exception as e:
            raise RuntimeError(f"Neo4j 쿼리 실행 실패: {str(e)}")
    
    def run(self, cypher_query: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        Cypher 쿼리 실행 (결과 반환 없음)
        
        Args:
            cypher_query: 실행할 Cypher 쿼리
            parameters: 쿼리 파라미터 (선택)
        """
        self.query(cypher_query, parameters)
    
    def get_schema(self) -> Dict:
        """
        현재 그래프 스키마 조회
        
        Returns:
            스키마 정보 (노드 타입, 관계 타입 등)
        """
        try:
            # LangChain Neo4jGraph의 get_schema는 속성일 수 있음
            # 메서드인 경우를 대비해 try-except 사용
            if callable(self.graph.get_schema):
                schema = self.graph.get_schema()
            else:
                schema = self.graph.get_schema
            
            # Neo4jGraph.get_schema는 문자열을 반환하므로 Dict로 변환
            # 문자열인 경우 빈 딕셔너리 반환 (실제 스키마 파싱은 필요시 별도 구현)
            if isinstance(schema, str):
                # 문자열 스키마는 Dict가 아니므로 빈 딕셔너리 반환
                # 실제 사용 시에는 스키마 문자열을 파싱하는 로직이 필요할 수 있음
                return {}
            elif isinstance(schema, dict):
                return schema
            else:
                return {}
        except Exception as e:
            raise RuntimeError(f"스키마 조회 실패: {str(e)}")
    
    def refresh_schema(self) -> None:
        """스키마 정보 새로고침"""
        self.graph.refresh_schema()
    
    def inject_subgraph(
        self,
        nodes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        복잡한 서브그래프를 Neo4j에 주입
        
        Args:
            nodes: 노드 리스트
                [
                    {
                        "type": "Company",
                        "properties": {"name": "삼성전자", "ticker": "005930"}
                    },
                    ...
                ]
            relationships: 관계 리스트
                [
                    {
                        "type": "MANUFACTURES",
                        "from": {"type": "Company", "name": "삼성전자"},
                        "to": {"type": "Product", "name": "반도체"},
                        "properties": {"weight": 0.9}
                    },
                    ...
                ]
        
        Returns:
            주입 통계 {"nodes": int, "relationships": int}
        """
        stats = {"nodes": 0, "relationships": 0, "errors": 0}
        
        # 1. 노드 생성
        for node in nodes:
            try:
                node_type = node.get("type", "Node")
                properties = node.get("properties", {})
                
                # MERGE를 사용하여 중복 방지
                # name 속성이 있으면 name 기준 MERGE, 없으면 모든 속성 기준
                if "name" in properties:
                    query = f"""
                    MERGE (n:{node_type} {{name: $name}})
                    SET n += $properties,
                        n.last_updated = datetime()
                    """
                    params = {
                        "name": properties["name"],
                        "properties": properties
                    }
                else:
                    query = f"""
                    CREATE (n:{node_type})
                    SET n = $properties,
                        n.last_updated = datetime()
                    """
                    params = {"properties": properties}
                
                self.run(query, params)
                stats["nodes"] += 1
                
            except Exception as e:
                logger.error(f"Failed to inject node: {node}. Error: {str(e)}")
                stats["errors"] += 1
        
        # 2. 관계 생성
        for rel in relationships:
            try:
                rel_type = rel.get("type", "RELATED_TO")
                from_node = rel.get("from", {})
                to_node = rel.get("to", {})
                rel_properties = rel.get("properties", {})
                
                # FROM 노드와 TO 노드를 매칭하여 관계 생성
                query = f"""
                MATCH (from:{from_node.get('type', 'Node')} {{name: $from_name}})
                MATCH (to:{to_node.get('type', 'Node')} {{name: $to_name}})
                MERGE (from)-[r:{rel_type}]->(to)
                SET r += $rel_properties,
                    r.last_updated = datetime()
                """
                
                params = {
                    "from_name": from_node.get("name"),
                    "to_name": to_node.get("name"),
                    "rel_properties": rel_properties
                }
                
                self.run(query, params)
                stats["relationships"] += 1
                
            except Exception as e:
                logger.error(f"Failed to inject relationship: {rel}. Error: {str(e)}")
                stats["errors"] += 1
        
        return stats
    
    def close(self) -> None:
        """연결 종료"""
        # Neo4jGraph는 close 메서드가 없을 수 있음
        # 필요시 driver.close() 호출
        pass
