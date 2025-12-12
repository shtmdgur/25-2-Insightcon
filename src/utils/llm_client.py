"""
LLM 클라이언트 유틸리티
"""
import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class LLMSelector:
    """
    작업 유형에 따라 적절한 LLM을 선택하는 클래스
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None
    ):
        """
        LLMSelector 초기화
        
        Args:
            openai_api_key: OpenAI API 키 (기본값: 환경변수 OPENAI_API_KEY)
            google_api_key: Google API 키 (기본값: 환경변수 GOOGLE_API_KEY)
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        # Quick-thinking 모델 (빠른 작업용) - Gemini 우선
        self.quick_llm = None
        if self.google_api_key:
            self.quick_llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite",
                temperature=0,
                google_api_key=self.google_api_key
            )
        elif self.openai_api_key:
            self.quick_llm = ChatOpenAI(
                model="gpt-5-nano",
                temperature=0,
                api_key=self.openai_api_key
            )
        
        # Deep-thinking 모델 (추론 집약적 작업용) - Gemini 우선
        self.deep_llm = None
        if self.google_api_key:
            self.deep_llm = ChatGoogleGenerativeAI(
                model="gemini-3-pro-preview",
                temperature=0,
                google_api_key=self.google_api_key
            )
        elif self.openai_api_key:
            self.deep_llm = ChatOpenAI(
                model="gpt-5-mini",
                temperature=0,
                api_key=self.openai_api_key
            )
    
    def get_llm(self, task_type: str):
        """
        작업 유형에 따라 LLM 선택
        
        Args:
            task_type: 작업 유형
                - "quick": 빠른 작업 (요약, 데이터 검색 등)
                - "deep": 추론 집약적 작업 (분석, 리포트 생성 등)
                - 기타: deep 모델 사용
        
        Returns:
            선택된 LLM 인스턴스
        """
        quick_tasks = [
            "quick",
            "summarization",
            "data_retrieval",
            "table_to_text",
            "simple_classification"
        ]
        
        if task_type in quick_tasks:
            if self.quick_llm is None:
                raise ValueError("Quick-thinking 모델이 설정되지 않았습니다.")
            return self.quick_llm
        else:
            if self.deep_llm is None:
                raise ValueError("Deep-thinking 모델이 설정되지 않았습니다.")
            return self.deep_llm
    
    def get_quick_llm(self):
        """Quick-thinking 모델 반환"""
        if self.quick_llm is None:
            raise ValueError("Quick-thinking 모델이 설정되지 않았습니다.")
        return self.quick_llm
    
    def get_deep_llm(self):
        """Deep-thinking 모델 반환"""
        if self.deep_llm is None:
            raise ValueError("Deep-thinking 모델이 설정되지 않았습니다.")
        return self.deep_llm
