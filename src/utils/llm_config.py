"""
LLM 모델 선택 전략 및 설정 관리

Quick/Deep 모델 매핑 및 Batch API 설정을 중앙에서 관리합니다.
"""
from typing import Literal, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# LLM 전략 설정
LLM_STRATEGY: Dict[str, Dict[str, Any]] = {
    # Quick Think: 반복적, 구조적 작업 (파싱, KG 구축, 단순 분석)
    "quick": {
        "model": "gemini-2.5-flash",
        "temperature": 0.0,
        "max_tokens": 1000,
        "timeout": 30,
    },
    
    # Deep Think: 복잡한 추론, 최종 판단 (Synthesizer, Quality Check)
    "deep": {
        "model": "gemini-3-pro-preview",
        "temperature": 0.2,
        "max_tokens": 4000,
        "timeout": 60,
    }
}

# Batch API 설정
BATCH_API_CONFIG = {
    "enabled": True,
    "max_batch_size": 100,  # 한 번에 처리할 최대 요청 수
    "polling_interval": 10,  # 초 단위
    "max_polling_attempts": 60,  # 최대 폴링 시도 (10분)
}

# 작업 유형별 모델 매핑
TASK_MODEL_MAPPING = {
    # Quick 모델 사용
    "pdf_parsing": "quick",
    "chart_description": "quick",
    "kg_construction": "quick",
    "entity_extraction": "quick",
    "trend_analysis": "quick",
    "fundamentals_analysis": "quick",
    "event_analysis": "quick",
    
    
    # Deep 모델 사용
    "bull_argument": "deep",
    "bear_argument": "deep",
    "quality_check": "deep",
    "relevance_scoring": "deep",
    "synthesis": "deep",
    "final_report": "deep",
}


def get_model_config(task_type: str) -> Dict[str, Any]:
    """
    작업 유형에 따른 모델 설정 반환
    
    Args:
        task_type: 작업 유형 (예: "kg_construction", "synthesis")
    
    Returns:
        모델 설정 딕셔너리
    """
    strategy = TASK_MODEL_MAPPING.get(task_type, "deep")
    config = LLM_STRATEGY[strategy].copy()
    config["strategy"] = strategy
    return config


def should_use_batch(task_type: str, num_requests: int = 1) -> bool:
    """
    Batch API 사용 여부 결정
    
    Args:
        task_type: 작업 유형
        num_requests: 처리할 요청 수
    
    Returns:
        Batch API 사용 여부
    """
    if not BATCH_API_CONFIG["enabled"]:
        return False
    
    # KG 구축 및 파싱 작업만 Batch 사용 (실시간성 덜 중요)
    batch_eligible_tasks = ["kg_construction", "pdf_parsing", "entity_extraction"]
    
    return task_type in batch_eligible_tasks and num_requests >= 5
