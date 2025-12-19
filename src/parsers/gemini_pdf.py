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

from src.dataflows.parser_interface import ParserInterface
from src.utils.gemini_files import get_gemini_files_client
from src.models.nodes import KnowledgeGraph, get_kg_json_schema

logger = logging.getLogger(__name__)

# Gemini Client 초기화
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompts YAML 로드
PROMPTS_FILE = Path(__file__).parent.parent / "templates" / "prompts.yaml"
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
        use_batch: bool = False # 테스트 단계에서는 False, 향후 True로 변경
    ):
        """
        Args:
            model_name: Gemini 모델 이름 (기본: gemini-2.5-pro)
            use_batch: Batch API 사용 여부 (비용 50% 절감)
        """
        self.model_name = model_name
        self.use_batch = use_batch
        self.files_client = get_gemini_files_client()
    
    def parse_pdf_to_kg(self, file_path: str) -> KnowledgeGraph:
        """
        PDF를 Knowledge Graph 객체로 파싱 (PDFParserAgent 호환용)
        """
        result = self.parse(file_path)
        return KnowledgeGraph.from_gemini_dict(result)

    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        PDF를 Knowledge Graph로 파싱
        """
        try:
            logger.info(f"Uploading PDF to Gemini: {file_path}")
            
            # 1. PDF 업로드
            file_uri = self.files_client.upload_file(file_path)
            
            # 2. Structured Output으로 Knowledge Graph 추출
            logger.info("Extracting Knowledge Graph with Gemini Structured Output...")
            
            kg_json = self._extract_knowledge_graph(file_uri)
            
            # 3. JSON 파일로 저장 (data/processed/)
            import os
            from datetime import datetime
            from pathlib import Path
            
            # 파일명 생성: {file_id}_{timestamp}.json
            file_id = Path(file_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 프로젝트 루트 기준 경로
            project_root = Path(__file__).parent.parent.parent.parent
            processed_dir = project_root / "data" / "processed"
            json_path = processed_dir / f"{file_id}_{timestamp}.json"
            
            # KnowledgeGraph 객체 생성 (저장용)
            knowledge_graph = KnowledgeGraph.from_gemini_dict(kg_json)
            knowledge_graph.save_to_json(str(json_path))
            
            return kg_json  # Dict 반환
            
            logger.info(f"Saved KG to: {json_path}")
            
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
                    "file_path": file_path,
                    "json_path": str(json_path)  # JSON 저장 경로 추가
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
