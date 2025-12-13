"""
Gemini Files API 통합

대용량 PDF를 Base64 인코딩 없이 URI 기반으로 효율적으로 처리합니다.
"""
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Gemini Client 초기화
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


class GeminiFilesClient:
    """
    Gemini Files API 클라이언트
    
    파일 업로드 및 URI 캐싱을 관리합니다.
    """
    
    def __init__(self):
        """초기화"""
        self.uploaded_files: Dict[str, Any] = {}  # 파일 경로 -> File 객체
    
    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> str:
        """
        파일을 Gemini에 업로드
        
        Args:
            file_path: 업로드할 파일 경로
            display_name: 표시 이름 (기본: 파일명)
        
        Returns:
            업로드된 파일의 URI
        """
        file_path = str(Path(file_path).resolve())
        
        # 이미 업로드된 파일인지 확인
        if file_path in self.uploaded_files:
            file_obj = self.uploaded_files[file_path]
            logger.info(f"Using cached file URI: {file_obj.uri}")
            return file_obj.uri
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 파일 업로드
        logger.info(f"Uploading file to Gemini: {file_path}")
        
        file_obj = client.files.upload(
            path=file_path
        )
        
        # 캐시에 저장
        self.uploaded_files[file_path] = file_obj
        
        logger.info(f"File uploaded successfully. URI: {file_obj.uri}")
        return file_obj.uri
    
    def get_file_uri(self, file_path: str) -> Optional[str]:
        """
        캐시된 파일 URI 가져오기
        
        Args:
            file_path: 파일 경로
        
        Returns:
            URI (없으면 None)
        """
        file_path = str(Path(file_path).resolve())
        file_obj = self.uploaded_files.get(file_path)
        return file_obj.uri if file_obj else None
    
    def delete_file(self, file_path: str) -> bool:
        """
        업로드된 파일 삭제
        
        Args:
            file_path: 파일 경로
        
        Returns:
            삭제 성공 여부
        """
        file_path = str(Path(file_path).resolve())
        file_obj = self.uploaded_files.get(file_path)
        
        if file_obj is None:
            logger.warning(f"File not found in cache: {file_path}")
            return False
        
        try:
            client.files.delete(name=file_obj.name)
            del self.uploaded_files[file_path]
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False
    
    def clear_cache(self):
        """모든 캐시 클리어"""
        for file_path in list(self.uploaded_files.keys()):
            self.delete_file(file_path)
        
        self.uploaded_files.clear()
        logger.info("Cache cleared")


# 싱글톤 인스턴스
_gemini_files_client: Optional[GeminiFilesClient] = None


def get_gemini_files_client() -> GeminiFilesClient:
    """
    GeminiFilesClient 싱글톤 인스턴스 반환
    
    Returns:
        GeminiFilesClient 인스턴스
    """
    global _gemini_files_client
    
    if _gemini_files_client is None:
        _gemini_files_client = GeminiFilesClient()
    
    return _gemini_files_client
