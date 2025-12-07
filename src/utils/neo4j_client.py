"""
Neo4j 클라이언트 유틸리티
"""
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()


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
            return schema if schema else {}
        except Exception as e:
            raise RuntimeError(f"스키마 조회 실패: {str(e)}")
    
    def refresh_schema(self) -> None:
        """스키마 정보 새로고침"""
        self.graph.refresh_schema()
