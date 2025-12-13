"""
Hybrid Parser (PyMuPDF + VLM)

텍스트: pymupdf4llm을 사용하여 정확하게 추출 (Markdown 포맷)
이미지: 추출된 이미지를 VLM(Gemini)으로 분석하여 차트/도표 해석
"""
import os
import logging
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
import pymupdf4llm
import fitz  # PyMuPDF
import google.generativeai as genai

from ..parser_interface import ParserInterface
from ...utils.gemini_files import get_gemini_files_client

logger = logging.getLogger(__name__)


class VLMParser(ParserInterface):
    """
    Hybrid 방식의 파서
    1. PyMuPDF: 텍스트 및 테이블을 Markdown으로 정확하게 추출
    2. VLM (Gemini): 문서 내 포함된 이미지를 분석하여 캡션 생성
    """
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.files_client = get_gemini_files_client()
        
        # VLM 모델 설정
        self.model = genai.GenerativeModel(model_name)
        
        # 이미지 저장 임시 경로
        self.temp_image_dir = Path("temp/extracted_images")
        self.temp_image_dir.mkdir(parents=True, exist_ok=True)
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        하이브리드 파싱 실행
        """
        try:
            # 1. PyMuPDF로 Markdown 변환 및 이미지 추출
            # write_images=True로 설정하여 이미지를 로컬에 저장
            # image_path는 저장될 디렉토리
            
            # 파일명 기반으로 고유한 이미지 디렉토리 생성
            file_stem = Path(file_path).stem
            image_output_dir = self.temp_image_dir / file_stem
            if image_output_dir.exists():
                shutil.rmtree(image_output_dir)
            image_output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Extracting text and images from {file_path}...")
            
            # pymupdf4llm 파싱
            md_text = pymupdf4llm.to_markdown(
                file_path,
                write_images=True,
                image_path=str(image_output_dir),
                image_format="png"
            )
            
            # 2. 추출된 이미지 확인 및 VLM 분석
            image_files = list(image_output_dir.glob("*.png"))
            extracted_charts = []
            
            if image_files:
                logger.info(f"Found {len(image_files)} images. Analyzing with VLM...")
                extracted_charts = self._analyze_images(image_files)
                
                # 3. 분석 결과를 Markdown 텍스트에 삽입 (선택적)
                # 여기서는 원본 텍스트는 유지하고, 차트 정보는 별도 필드로 반환
                # 필요시 md_text 내의 이미지 링크를 분석 텍스트로 치환 가능
            
            # 정리 (이미지 파일 삭제)
            # shutil.rmtree(image_output_dir)  # 디버깅을 위해 주석 처리 가능
            
            return {
                "parsed_text": md_text,
                "extracted_charts": extracted_charts,
                "file_uri": None,  # 로컬 파싱이므로 전체 PDF URI는 없음 (필요시 업로드)
                "metadata": {
                    "parser": "Hybrid(PyMuPDF+VLM)",
                    "image_count": len(image_files)
                }
            }
            
        except Exception as e:
            logger.error(f"Hybrid parsing failed: {str(e)}")
            raise RuntimeError(f"Hybrid parsing failed: {str(e)}")

    def _analyze_images(self, image_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        이미지 리스트를 VLM으로 분석
        """
        results = []
        
        for img_path in image_paths:
            try:
                # 1. 이미지 업로드 (Gemini Files API)
                # 작은 이미지는 바로 Data로 보내도 되지만, 일관성을 위해 Files API 사용
                # 또는 PIL Image로 로드하여 전송
                
                # 효율성을 위해 PIL Image로 직접 전송 (Batch 처리가 아닐 경우)
                # Files API는 대용량/다수 파일 관리에 유리하지만, 
                # 여기서는 빠른 처리를 위해 PIL 사용 고려. 
                # 하지만 로깅된 코드 스타일에 맞춰 Files API 사용.
                
                file_uri = self.files_client.upload_file(str(img_path))
                
                # 2. VLM 분석 요청
                prompt = """
                # Role
                이미지에서 데이터를 추출하여 JSON으로 변환하는 ETL(Extract, Transform, Load) 전문가입니다.

                # Task
                이미지를 분석하여 다음 JSON 스키마에 맞춰 데이터를 추출하세요.
                이미지가 의미 없는 장식이나 아이콘이면 type을 "Ignore"로 하세요.

                # JSON Schema
                {
                "title": "차트 제목",
                "chart_type": "Bar|Line|Pie|Table",
                "unit": "화폐 또는 단위",
                "time_period": "기간",
                "data_points": [
                    {"label": "2024-Q1", "value": 150.5, "series": "Revenue"},
                    {"label": "2024-Q2", "value": 160.0, "series": "Revenue"}
                ],
                "trend_summary": "상승/하락 추세 설명",
                "insight": "핵심 인사이트"
                }
                """
                
                response = self.model.generate_content([
                    genai.get_file(file_uri),
                    prompt
                ])
                
                # 3. 결과 파싱
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
                return {"summary": text, "type": "Unknown", "title": "Unknown"}
        except Exception:
            return {"summary": text, "type": "Error", "title": "Error"}
