"""
LLM 모델 설정 중앙 관리

모든 LLM 모델명과 설정을 이 파일에서 중앙 관리합니다.
다른 파일에서는 이 모듈을 import하여 사용합니다.

사용 예시:
    from src.config.llm_config import get_model, MODELS
    
    model = get_model("pdf_parsing")       # → "gemini-3-flash-preview"
    model = get_model("news_parsing")      # → "gemini-3-flash-preview"
    model = MODELS["flash"]                # → "gemini-3-flash-preview"
"""
from typing import Dict, Any, Literal
import os
from dotenv import load_dotenv

load_dotenv()


# ============================================
# 모델 레지스트리 (공식 모델명)
# ============================================
# Google AI 공식 문서: https://ai.google.dev/gemini-api/docs/models

MODELS = {
    # Flash 계열 (빠른 속도, 대량 처리, 대규모 문서 분석) - 모든 파싱 작업에 사용
    "flash": "gemini-3-flash-preview",
    
    # Deep Think (토론, 고급 추론용) - 토론 에이전트 전용
    "deep": "gemini-3-pro-preview",
}


# ============================================
# 작업별 모델 매핑
# ============================================
TASK_TO_MODEL: Dict[str, str] = {
    # PDF 파싱
    "pdf_parsing": MODELS["flash"],
    
    # 뉴스 파싱
    "news_parsing": MODELS["flash"],
    
    # KG 구축   
    "kg_construction": MODELS["flash"],
    "entity_extraction": MODELS["flash"],
    
    # 차트/이미지 분석
    "chart_description": MODELS["flash"],
    
    # 분석 작업
    "trend_analysis": MODELS["flash"],
    "fundamentals_analysis": MODELS["flash"],
    "event_analysis": MODELS["flash"],
    
    # 토론/추론 (Deep Think)
    "debate": MODELS["deep"],
    "bull_argument": MODELS["deep"],
    "bear_argument": MODELS["deep"],
    "quality_check": MODELS["deep"],
    "relevance_scoring": MODELS["deep"],
    "synthesis": MODELS["deep"],
    "final_report": MODELS["deep"],
    
    # 쿼리 분석 및 유틸리티
    "query_parsing": MODELS["flash"],
    "batch": MODELS["flash"],
}


# ============================================
# 모델별 기본 설정
# ============================================
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    MODELS["flash"]: {
        "temperature": 0.0,
        "max_tokens": 8192,
        "timeout": 60,
    },
    MODELS["deep"]: {
        "temperature": 0.2,
        "max_tokens": 8192,
        "timeout": 120,
    },
}


# ============================================
# 헬퍼 함수
# ============================================
def get_model(task: str) -> str:
    """
    작업 유형에 따른 모델명 반환
    
    Args:
        task: 작업 유형 (예: "pdf_parsing", "news_parsing")
    
    Returns:
        모델명 문자열
    
    Example:
        >>> get_model("pdf_parsing")
        'gemini-3-flash-preview'
    """
    return TASK_TO_MODEL.get(task, MODELS["flash"])


def get_model_config(task: str) -> Dict[str, Any]:
    """
    작업 유형에 따른 모델 설정 반환
    
    Args:
        task: 작업 유형
    
    Returns:
        모델 설정 딕셔너리
    """
    model = get_model(task)
    config = MODEL_CONFIGS.get(model, MODEL_CONFIGS[MODELS["flash"]]).copy()
    config["model"] = model
    config["task"] = task
    return config


def get_flash_model() -> str:
    """Flash 모델명 반환 (모든 파싱 작업)"""
    return MODELS["flash"]


def get_deep_model() -> str:
    """Deep Think 모델명 반환 (토론 등)"""
    return MODELS["deep"]
