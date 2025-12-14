"""
Enhanced Hybrid Parser (PyMuPDF + VLM)

개선사항:
1. PyMuPDF4LLM 파싱 옵션 최적화 (더 많은 텍스트 추출)
2. VLM 프롬프트 YAML 관리 (prompts.yaml에서 로드)
3. 금융 리포트 특화 분석
"""
import os
import logging
import shutil
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
import pymupdf4llm
import fitz  # PyMuPDF
from google import genai
from google.genai import types

from ..parser_interface import ParserInterface
from ...utils.gemini_files import get_gemini_files_client

logger = logging.getLogger(__name__)

# Gemini Client 초기화
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompts YAML 로드
PROMPTS_FILE = Path(__file__).parent.parent.parent / "templates" / "prompts.yaml"
with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
    PROMPTS = yaml.safe_load(f)


class EnhancedVLMParser(ParserInterface):
    """
    개선된 Hybrid 파서
    - 더 많은 텍스트 추출 (PyMuPDF 옵션 최적화)
    - 더 상세한 차트 분석 (YAML 프롬프트)
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.files_client = get_gemini_files_client()
        
        # 이미지 저장 임시 경로
        self.temp_image_dir = Path("temp/extracted_images")
        self.temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        향상된 하이브리드 파싱
        """
        try:
            # 파일명 기반 고유 디렉토리
            file_stem = Path(file_path).stem
            image_output_dir = self.temp_image_dir / file_stem
            if image_output_dir.exists():
                shutil.rmtree(image_output_dir)
            image_output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Extracting text and images from {file_path}...")
            
            # 1. PyMuPDF4LLM - 최적화된 옵션으로 파싱
            md_text = pymupdf4llm.to_markdown(
                file_path,
                write_images=True,
                image_path=str(image_output_dir),
                image_format="png",
                page_chunks=False,  # 페이지별 분할 안 함
                margins=(0, 0, 0, 0),  # 여백 최소화
                dpi=200  # 이미지 해상도 향상
            )
            
            # 2. 추출된 이미지 VLM 분석
            image_files = list(image_output_dir.glob("*.png"))
            extracted_charts = []
            
            if image_files:
                logger.info(f"Found {len(image_files)} images. Analyzing with enhanced VLM...")
                extracted_charts = self._analyze_images_enhanced(image_files)
            
            return {
                "parsed_text": md_text,
                "extracted_charts": extracted_charts,
                "file_uri": None,
                "metadata": {
                    "parser": "Enhanced-Hybrid(PyMuPDF+VLM)",
                    "image_count": len(image_files),
                    "chart_count": len(extracted_charts)
                }
            }
            
        except Exception as e:
            logger.error(f"Enhanced hybrid parsing failed: {str(e)}")
            raise RuntimeError(f"Enhanced hybrid parsing failed: {str(e)}")

    def _analyze_images_enhanced(self, image_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        강화된 VLM 이미지 분석 (YAML 프롬프트 사용)
        """
        results = []
        
        # YAML에서 프롬프트 로드
        vlm_prompt = PROMPTS['vlm_parser']['chart_analysis']['instruction']
        
        for img_path in image_paths:
            try:
                # 이미지 업로드
                file_uri = self.files_client.upload_file(str(img_path))
                
                # YAML 프롬프트 사용
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_uri(file_uri=file_uri, mime_type="image/png"),
                        vlm_prompt
                    ]
                )
                
                # 결과 파싱
                analysis = self._parse_vlm_response(response.text)
                
                if analysis.get("type") != "Ignore":
                    analysis["image_path"] = str(img_path)
                    results.append(analysis)
                
            except Exception as e:
                logger.warning(f"Failed to analyze image {img_path}: {str(e)}")
                continue
                
        return results

    def _parse_vlm_response(self, text: str) -> Dict[str, Any]:
        """VLM 응답 텍스트를 딕셔너리로 변환"""
        import json
        import re
        
        try:
            # JSON 블록 추출
            match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            else:
                # JSON 포맷이 아닐 경우 텍스트 기반 폴백
                return {
                    "type": "Text",
                    "title": "Unknown",
                    "extracted_text": text[:500],
                    "summary": text
                }
        except Exception as e:
            logger.warning(f"Failed to parse VLM response: {str(e)}")
            return {
                "type": "Error",
                "title": "Parse Error",
                "extracted_text": text[:500],
                "error": str(e)
            }
