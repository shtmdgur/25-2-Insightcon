"""
온톨로지 아키텍트 에이전트
Neo4j GraphRAG + Vertex AI (Gemini)를 사용하여 온톨로지 스키마 자동 생성
"""
from typing import List, Dict, Any
import logging
import os
from dotenv import load_dotenv

from langchain_google_vertexai import VertexAI
from langchain_core.language_models import BaseChatModel

from ..utils.neo4j_client import Neo4jClient

# Neo4j GraphRAG 라이브러리 (Vertex AI 지원)
try:
    from neo4j_graphrag.experimental.components.schema import SchemaFromTextExtractor
    from neo4j_graphrag.llm import VertexAILLM
    NEO4J_GRAPHRAG_AVAILABLE = True
except ImportError:
    try:
        from neo4j_graphrag.components.schema import SchemaFromTextExtractor
        from neo4j_graphrag.llm import VertexAILLM
        NEO4J_GRAPHRAG_AVAILABLE = True
    except ImportError:
        SchemaFromTextExtractor = None
        VertexAILLM = None
        NEO4J_GRAPHRAG_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)


class OntologyArchitectAgent:
    """
    온톨로지 스키마를 자동으로 생성하고 Neo4j에 적용하는 에이전트
    Vertex AI (Gemini)와 Neo4j GraphRAG를 활용
    """
    
    def __init__(
        self, 
        llm: BaseChatModel, 
        neo4j_client: Neo4jClient,
        project_id: str = None,
        location: str = "us-central1"
    ):
        """
        OntologyArchitectAgent 초기화
        
        Args:
            llm: LLM 모델 (LangChain BaseChatModel)
            neo4j_client: Neo4j 클라이언트
            project_id: Google Cloud 프로젝트 ID (환경변수에서 자동 설정 가능)
            location: Vertex AI 리전
        """
        if not NEO4J_GRAPHRAG_AVAILABLE:
            logger.warning(
                "neo4j_graphrag를 사용할 수 없습니다. "
                "LangChain만 사용하여 스키마를 생성합니다."
            )
            self.use_graphrag = False
        else:
            self.use_graphrag = True
            
        self.llm = llm
        self.neo4j_client = neo4j_client
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.location = location
        
        if self.use_graphrag:
            # Neo4j GraphRAG용 VertexAI LLM 설정
            self.graphrag_llm = VertexAILLM(
                model_name="gemini-2.5-pro",
                project_id=self.project_id,
                location=self.location
            )
            self.extractor = SchemaFromTextExtractor(llm=self.graphrag_llm)
    
    def generate_schema(self, templates: List[str]) -> Dict[str, Any]:
        """
        증권 리포트 템플릿에서 스키마 자동 생성
        
        Args:
            templates: 증권 리포트 템플릿 문서 리스트
        
        Returns:
            추출된 스키마 정보
        """
        if self.use_graphrag:
            return self._generate_schema_with_graphrag(templates)
        else:
            return self._generate_schema_with_langchain(templates)
    
    def _generate_schema_with_graphrag(self, templates: List[str]) -> Dict[str, Any]:
        """Neo4j GraphRAG를 사용한 스키마 생성"""
        import asyncio
        
        try:
            # 템플릿을 하나의 텍스트로 결합
            combined_text = "\n\n".join(templates)
            
            # neo4j-graphrag를 사용하여 스키마 추출 (asyncio 사용)
            schema = asyncio.run(self.extractor.run(text=combined_text))
            
            # Neo4j 스키마로 변환
            neo4j_schema = schema.to_neo4j_schema()
            
            # Neo4j에 적용 (Cypher 생성 및 실행)
            cypher_statements = list(neo4j_schema.to_cypher())
            for statement in cypher_statements:
                self.neo4j_client.run(statement)
            
            return {
                "schema": schema,
                "neo4j_schema": neo4j_schema,
                "cypher_statements": cypher_statements,
                "method": "graphrag"
            }
        except Exception as e:
            logger.error(f"GraphRAG 스키마 생성 실패: {str(e)}")
            raise RuntimeError(f"온톨로지 스키마 생성 실패: {str(e)}")
    
    def _generate_schema_with_langchain(self, templates: List[str]) -> Dict[str, Any]:
        """LangChain을 사용한 스키마 생성 (폴백)"""
        # 1. 템플릿 결합
        combined_text = "\n\n".join(templates)[:50000]  # 토큰 제한 고려
        
        # 2. 스키마 추출 프롬프트
        prompt = f"""
        당신은 지식 그래프 전문가입니다.
        다음 문서들을 분석하여 금융 도메인에 적합한 온톨로지 스키마를 정의하세요.
        
        문서:
        {combined_text}
        
        다음 항목들을 정의해야 합니다:
        1. Node Labels: 예 - Company, Product, Industry, Event
        2. Relationship Types: 예 - COMPETITOR_OF, SUPPLIER_OF, AFFECTS
        3. Properties: 각 노드와 관계의 필수 속성들
        
        출력은 반드시 실행 가능한 Cypher Query 형식으로 작성하세요.
        
        예시:
        CREATE CONSTRAINT FOR (c:Company) REQUIRE c.name IS UNIQUE;
        """
        
        try:
            # 3. LLM 호출
            response = self.llm.invoke(prompt)
            cypher_queries = self._extract_cypher_queries(response.content)
            
            # 4. Neo4j 적용
            executed_queries = []
            for query in cypher_queries:
                try:
                    self.neo4j_client.run(query)
                    executed_queries.append(query)
                    logger.info(f"Executed schema query: {query}")
                except Exception as e:
                    logger.warning(f"Failed to execute query: {query}. Error: {e}")
            
            return {
                "generated_schema_queries": executed_queries,
                "raw_response": response.content,
                "method": "langchain_fallback"
            }
            
        except Exception as e:
            logger.error(f"Schema generation failed: {str(e)}")
            raise RuntimeError(f"온톨로지 스키마 생성 실패: {str(e)}")

    def _extract_cypher_queries(self, text: str) -> List[str]:
        """LLM 응답에서 Cypher 쿼리 추출"""
        import re
        
        queries = []
        lines = text.split('\n')
        
        current_query = ""
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue
                
            if (line.upper().startswith("CREATE") or 
                line.upper().startswith("MERGE") or 
                line.upper().startswith("CALL")):
                current_query = line
            elif current_query:
                current_query += " " + line
            
            if current_query and current_query.endswith(";"):
                queries.append(current_query)
                current_query = ""
                
        # 코드 블록에서 추출 (백업)
        if not queries:
            matches = re.findall(r"```cypher(.*?)```", text, re.DOTALL)
            for match in matches:
                queries.extend([q.strip() for q in match.split(';') if q.strip()])
                
        return queries
