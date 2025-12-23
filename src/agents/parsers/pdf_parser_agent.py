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
from src.models.nodes import KnowledgeGraph, get_kg_json_schema, NodeType
from src.utils.ticker_mapping import resolve_entity_name, get_ticker_from_name

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
        model_name: str = None,  # None이면 중앙 설정 사용
        use_batch: bool = False # 테스트 단계에서는 False, 향후 True로 변경
    ):
        """
        Args:
            model_name: Gemini 모델 이름 (기본: llm_config에서 가져옴)
            use_batch: Batch API 사용 여부 (비용 50% 절감)
        """
        # 중앙 설정에서 모델명 가져오기
        if model_name is None:
            from src.config.llm_config import get_model
            model_name = get_model("pdf_parsing")
        
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
            
            # 3. KnowledgeGraph 객체 생성
            knowledge_graph = KnowledgeGraph.from_gemini_dict(kg_json)
            
            # 3.5 엔티티 이름 정규화 (표준명 변환 & Ticker 매핑)
            self._normalize_entities(knowledge_graph)
            
            # 4. 임베딩 생성 및 주입 (Vector Index용)
            logger.info("Generating embeddings for entities...")
            self._enrich_with_embeddings(knowledge_graph)
            
            # 5. JSON 파일로 저장 (data/processed/)
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
            
            # 저장 (임베딩 포함됨)
            knowledge_graph.save_to_json(str(json_path))
            
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
        
        # Fallback: YAML에 없으면 에러 발생 (명시적 실패)
        if not prompt:
            raise RuntimeError(
                "Prompt not found in prompts.yaml at 'gemini_pdf_parser.kg_extraction.instruction'. "
                "Please check the YAML file configuration."
            )
        
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
    
    def _normalize_entities(self, kg: KnowledgeGraph):
        """
        추출된 엔티티의 이름을 정규화하고 Ticker를 보강함
        예: "퀄컴" -> "Qualcomm", "삼성전자(주)" -> "삼성전자"
        
        v3.0 추가: 관계의 subject/object도 함께 정규화하여 MATCH 실패 방지
        """
        # 이름 매핑 테이블 (원본 → 정규화)
        name_mapping = {}
        
        for entity in kg.entities:
            # 1. 이름 정규화
            original_name = entity.name
            normalized_name = resolve_entity_name(original_name)
            
            if original_name != normalized_name:
                logger.debug(f"Normalized entity: {original_name} -> {normalized_name}")
                name_mapping[original_name] = normalized_name
                entity.name = normalized_name
            
            # 2. Ticker 보강 (Agent 타입인 경우)
            if entity.type in [NodeType.IDM, NodeType.FABLESS, NodeType.FOUNDRY, NodeType.SUPPLIER]:
                ticker = get_ticker_from_name(entity.name)
                if ticker:
                    if "ticker" not in entity.properties:
                        entity.properties["ticker"] = ticker
                        logger.debug(f"Added ticker {ticker} to {entity.name}")
        
        # 3. 관계의 subject/object 정규화 (v3.0 추가)
        for relation in kg.relations:
            if relation.subject in name_mapping:
                logger.debug(f"Normalized relation subject: {relation.subject} -> {name_mapping[relation.subject]}")
                relation.subject = name_mapping[relation.subject]
            if relation.object in name_mapping:
                logger.debug(f"Normalized relation object: {relation.object} -> {name_mapping[relation.object]}")
                relation.object = name_mapping[relation.object]

    
    def _enrich_with_embeddings(self, kg: KnowledgeGraph):
        """
        KG 엔티티에 임베딩 추가 (Batch 처리)
        """
        try:
            # 임베딩 대상 텍스트 생성
            # 포맷: "이름 (타입): 속성요약"
            texts = []
            valid_entities = []
            
            for entity in kg.entities:
                # 임베딩 텍스트 구성
                props_str = ", ".join(f"{k}={v}" for k, v in entity.properties.items())
                text = f"{entity.name} ({entity.type.value})"
                if props_str:
                    text += f": {props_str}"
                
                texts.append(text)
                valid_entities.append(entity)
            
            if not texts:
                return

            # Batch 임베딩 생성 (text-embedding-004)
            # 한 번에 최대 100개씩 처리 권장
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_entities = valid_entities[i:i + batch_size]
                
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=batch_texts
                )
                
                # 결과 매핑
                for entity, embedding in zip(batch_entities, response.embeddings):
                    entity.embedding = embedding.values
                    
            logger.info(f"Generated embeddings for {len(valid_entities)} entities")
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            # 임베딩 실패해도 전체 프로세스는 계속 진행 (선택적 기능)
