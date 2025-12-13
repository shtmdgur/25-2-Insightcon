"""
Gemini PDF Native Parser

PDF를 Gemini API에 직접 업로드하여 Structured Output으로
Knowledge Graph(엔티티/관계)를 추출합니다.

특징:
- PDF 전체를 문맥으로 이해
- Structured JSON Schema로 일관된 출력
- Neo4j 바로 주입 가능
- Batch API 지원 (비용 절감)
"""
import os
import logging
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from google import genai
from google.genai import types

from ..parser_interface import ParserInterface
from ...utils.gemini_files import get_gemini_files_client
from ...models.graph_schema import KnowledgeGraph, get_kg_json_schema

logger = logging.getLogger(__name__)

# Gemini Client 초기화
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompts YAML 로드
PROMPTS_FILE = Path(__file__).parent.parent.parent / "templates" / "prompts.yaml"
with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
    PROMPTS = yaml.safe_load(f)


class GeminiPDFParser(ParserInterface):
    """
    Gemini PDF Native Parser
    
    PDF를 Gemini에 직접 분석시켜 Knowledge Graph JSON 추출
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-pro",
        use_batch: bool = False
    ):
        """
        Args:
            model_name: Gemini 모델 이름 (기본: gemini-2.5-pro)
            use_batch: Batch API 사용 여부 (비용 50% 절감)
        """
        self.model_name = model_name
        self.use_batch = use_batch
        self.files_client = get_gemini_files_client()
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        PDF를 Knowledge Graph로 파싱
        
        Args:
            file_path: PDF 파일 경로
        
        Returns:
            {
                "knowledge_graph": KnowledgeGraph,  # Pydantic 모델
                "raw_json": dict,  # 원본 JSON
                "metadata": {...}
            }
        """
        try:
            logger.info(f"Uploading PDF to Gemini: {file_path}")
            
            # 1. PDF 업로드
            file_uri = self.files_client.upload_file(file_path)
            
            # 2. Structured Output으로 Knowledge Graph 추출
            logger.info("Extracting Knowledge Graph with Gemini Structured Output...")
            
            kg_json = self._extract_knowledge_graph(file_uri)
            
            # 3. Pydantic 모델로 파싱
            knowledge_graph = KnowledgeGraph.model_validate(kg_json)
            
            logger.info(
                f"Extracted {len(knowledge_graph.entities)} entities "
                f"and {len(knowledge_graph.relations)} relations"
            )
            
            return {
                "knowledge_graph": knowledge_graph,
                "raw_json": kg_json,
                "metadata": {
                    "parser": "Gemini-PDF-Native",
                    "model": self.model_name,
                    "entity_count": len(knowledge_graph.entities),
                    "relation_count": len(knowledge_graph.relations),
                    "file_path": file_path
                }
            }
            
        except Exception as e:
            logger.error(f"Gemini PDF parsing failed: {str(e)}")
            raise RuntimeError(f"Gemini PDF parsing failed: {str(e)}")
    
    def _extract_knowledge_graph(self, file_uri: str) -> dict:
        """
        Gemini Structured Output으로 Knowledge Graph 추출
        
        Args:
            file_uri: Gemini Files API URI
        
        Returns:
            Knowledge Graph JSON
        """
        # YAML에서 프롬프트 로드
        prompt = PROMPTS.get('gemini_pdf_parser', {}).get('kg_extraction', {}).get('instruction', '')
        
        # Fallback: YAML에 없으면 기본 프롬프트 사용
        if not prompt:
            prompt = self._get_default_prompt()
        
        # Gemini API 호출 (Structured Output)
        response = client.models.generate_content(
            model=self.model_name,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "fileData": {
                                "fileUri": file_uri,
                                "mimeType": "application/pdf"
                            }
                        }
                    ]
                }
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=get_kg_json_schema()
            )
        )
        
        # JSON 파싱
        import json
        return json.loads(response.text)
    
    def _get_default_prompt(self) -> str:
        """기본 KG 추출 프롬프트"""
        return """
# Role
당신은 금융 도메인 Knowledge Graph 전문가입니다.

# Task
이 PDF 문서를 분석하여 다음을 추출하세요:

1. **엔티티(Entities)**: 회사, 제품, 지표, 이벤트, 트렌드, 기술, 인물
2. **관계(Relations)**: 엔티티 간의 의미 있는 연결

# 중요 지침
- 엔티티 ID는 고유하고 의미 있게 만드세요 (예: "삼성전자", "DRAM_2024Q1")
- 모든 숫자 데이터는 properties에 저장하세요
- 시간 정보(날짜, 분기, 연도)는 반드시 포함하세요
- 관계는 방향성이 명확해야 합니다
- 불확실한 정보는 포함하지 마세요

# 도메인 주요 엔티티
- Company: 기업명, 시가총액, 본사 등
- Product: 제품명, 카테고리, 사양 등  
- Metric: 매출, 영업이익, 점유율 등 (반드시 수치 포함)
- Event: 신제품 출시, M&A, 실적 발표 등
- Trend: 가격 추세, 수요 변화 등

출력은 반드시 정의된 JSON Schema를 따라야 합니다.
"""
