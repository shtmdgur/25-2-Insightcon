"""
온톨로지 아키텍트 에이전트
증권 리포트 템플릿에서 온톨로지 스키마를 자동으로 추출하고 Neo4j에 적용
"""
from typing import List, Dict, Any, Optional
import asyncio
import os
from dotenv import load_dotenv

# neo4j_graphrag의 올바른 import 경로
try:
    from neo4j_graphrag.experimental.components.schema import SchemaFromTextExtractor
    from neo4j_graphrag.llm import OpenAILLM
    NEO4J_GRAPHRAG_AVAILABLE = True
except ImportError:
    try:
        from neo4j_graphrag.components.schema import SchemaFromTextExtractor
        from neo4j_graphrag.llm import OpenAILLM
        NEO4J_GRAPHRAG_AVAILABLE = True
    except ImportError:
        SchemaFromTextExtractor = None
        OpenAILLM = None
        NEO4J_GRAPHRAG_AVAILABLE = False

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from ..utils.neo4j_client import Neo4jClient

load_dotenv()


class OntologyArchitectAgent:
    """
    온톨로지 스키마를 자동으로 생성하고 Neo4j에 적용하는 에이전트
    """
    
    def __init__(self, llm: BaseChatModel, neo4j_client: Neo4jClient):
        """
        OntologyArchitectAgent 초기화
        
        Args:
            llm: LLM 모델 (LangChain BaseChatModel, 스키마 추출에 사용)
            neo4j_client: Neo4j 클라이언트
        """
        if not NEO4J_GRAPHRAG_AVAILABLE:
            raise ImportError(
                "neo4j_graphrag.experimental.components.schema를 import할 수 없습니다. "
                "neo4j-graphrag 패키지가 올바르게 설치되었는지 확인하세요."
            )
        
        self.llm = llm
        self.neo4j_client = neo4j_client
        
        # LangChain LLM을 neo4j_graphrag의 OpenAILLM으로 변환
        # 주의: neo4j_graphrag는 OpenAI만 직접 지원하므로, Gemini인 경우 OpenAI API를 사용
        neo4j_llm = self._convert_langchain_to_neo4j_llm(llm)
        self.extractor = SchemaFromTextExtractor(llm=neo4j_llm)
    
    def _convert_langchain_to_neo4j_llm(self, langchain_llm: BaseChatModel) -> OpenAILLM:
        """
        LangChain LLM을 neo4j_graphrag의 OpenAILLM으로 변환
        
        주의: neo4j_graphrag는 OpenAI만 직접 지원하므로,
        Gemini를 사용하는 경우 OpenAI API 키가 필요합니다.
        Gemini를 사용하려면 OpenAI API 키를 .env에 설정해야 합니다.
        
        Args:
            langchain_llm: LangChain BaseChatModel
            
        Returns:
            neo4j_graphrag OpenAILLM 인스턴스
        """
        # OpenAI API 키 가져오기
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # LangChain LLM에서 API 키 추출 시도
            if hasattr(langchain_llm, 'openai_api_key'):
                api_key = langchain_llm.openai_api_key
            elif hasattr(langchain_llm, 'api_key'):
                api_key = langchain_llm.api_key
        
        if not api_key:
            # Gemini를 사용하는 경우에도 neo4j_graphrag는 OpenAI가 필요
            # 따라서 OpenAI API 키가 없으면 에러 발생
            raise ValueError(
                "neo4j_graphrag는 OpenAI API를 필요로 합니다. "
                "Gemini를 사용하더라도 .env에 OPENAI_API_KEY를 설정해야 합니다."
            )
        
        # 모델 이름 추출 (기본값: gpt-4o)
        model_name = "gpt-4o"
        if isinstance(langchain_llm, ChatOpenAI):
            model_name = langchain_llm.model_name or langchain_llm.model or "gpt-4o"
        elif isinstance(langchain_llm, ChatGoogleGenerativeAI):
            # Gemini를 사용하는 경우에도 OpenAI API를 사용 (neo4j_graphrag 제약)
            # 사용자에게 알림
            model_name = "gpt-4o"  # Gemini 대신 OpenAI 사용
        
        # neo4j_graphrag OpenAILLM 생성
        return OpenAILLM(
            model_name=model_name,
            model_params={
                "max_tokens": 2000,
                "response_format": {"type": "json_object"},
            }
        )
    
    def generate_schema(self, templates: List[str]) -> Dict[str, Any]:
        """
        증권 리포트 템플릿에서 스키마 자동 생성
        
        Args:
            templates: 증권 리포트 템플릿 문서 리스트
                예: [CFA 템플릿, J.P. Morgan 템플릿, 한국 반도체 리포트 샘플]
        
        Returns:
            추출된 스키마 정보
        """
        try:
            # 템플릿을 하나의 텍스트로 결합
            combined_text = "\n\n".join(templates)
            
            # neo4j-graphrag를 사용하여 스키마 추출 (asyncio 사용)
            schema = asyncio.run(self.extractor.run(text=combined_text))
            
            # Neo4j 스키마로 변환
            neo4j_schema = schema.to_neo4j_schema()
            
            # Neo4j에 적용 (Cypher 생성 및 실행)
            # Iterator 소진 방지: 먼저 리스트로 변환
            cypher_statements = list(neo4j_schema.to_cypher())
            for statement in cypher_statements:
                self.neo4j_client.run(statement)
            
            return {
                "schema": schema,
                "neo4j_schema": neo4j_schema,
                "cypher_statements": cypher_statements
            }
        except Exception as e:
            raise RuntimeError(f"온톨로지 스키마 생성 실패: {str(e)}")
    
    def update_schema(self, new_documents: List[str]) -> Dict[str, Any]:
        """
        기존 스키마에 새로운 개념 추가
        
        Args:
            new_documents: 새로운 문서 리스트
        
        Returns:
            업데이트된 스키마 정보
        """
        try:
            # 기존 스키마 조회
            existing_schema = self._get_existing_schema()
            
            # 새 문서에서 스키마 추출
            combined_text = "\n\n".join(new_documents)
            new_schema_obj = asyncio.run(self.extractor.run(text=combined_text))
            
            # schema 객체를 Dict로 변환
            new_schema_dict = self._schema_to_dict(new_schema_obj)
            
            # 스키마 병합 (간단한 버전 - 실제로는 더 복잡한 로직 필요)
            merged_schema = self._merge_schemas(existing_schema, new_schema_dict)
            
            # Neo4j 업데이트
            self._apply_schema_update(merged_schema)
            
            return merged_schema
        except Exception as e:
            raise RuntimeError(f"온톨로지 스키마 업데이트 실패: {str(e)}")
    
    def _get_existing_schema(self) -> Dict[str, Any]:
        """현재 Neo4j의 스키마 조회"""
        try:
            # Neo4j에서 스키마 정보 조회
            schema_info = self.neo4j_client.get_schema()
            return schema_info
        except Exception:
            # 스키마가 없으면 빈 딕셔너리 반환
            return {}
    
    def _merge_schemas(
        self, 
        existing: Dict[str, Any], 
        new: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        기존 스키마와 새 스키마 병합
        
        Args:
            existing: 기존 스키마
            new: 새 스키마
        
        Returns:
            병합된 스키마
        """
        # 간단한 병합 로직 (실제로는 더 정교한 로직 필요)
        merged = {
            "node_types": list(set(
                existing.get("node_types", []) + new.get("node_types", [])
            )),
            "relationship_types": list(set(
                existing.get("relationship_types", []) + 
                new.get("relationship_types", [])
            ))
        }
        return merged
    
    def _schema_to_dict(self, schema_obj) -> Dict[str, Any]:
        """
        schema 객체를 Dict로 변환
        
        Args:
            schema_obj: neo4j_graphrag의 schema 객체
        
        Returns:
            Dict 형태의 스키마 정보
        """
        try:
            # neo4j_schema로 변환하여 정보 추출
            neo4j_schema = schema_obj.to_neo4j_schema()
            
            # 스키마 정보를 Dict로 변환
            # 실제 구현은 neo4j_graphrag의 스키마 구조에 따라 다를 수 있음
            # 여기서는 기본적인 변환 로직 제공
            # TODO: neo4j_schema에서 실제 노드 타입과 관계 타입 추출
            return {
                "node_types": [],  # TODO: neo4j_schema에서 노드 타입 추출
                "relationship_types": []  # TODO: neo4j_schema에서 관계 타입 추출
            }
        except Exception as e:
            # 변환 실패 시 빈 Dict 반환
            return {
                "node_types": [],
                "relationship_types": []
            }
    
    def _apply_schema_update(self, schema: Dict[str, Any]) -> None:
        """스키마 업데이트를 Neo4j에 적용"""
        # 스키마 업데이트 로직 구현
        # 실제로는 neo4j-graphrag의 스키마 업데이트 기능 활용
        pass
