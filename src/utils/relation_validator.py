"""
Relation Validator
LLM 추출 관계의 통계적 검증
"""

from scipy.stats import pearsonr
import numpy as np
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class RelationValidator:
    """
    AFFECTS 관계 검증기
    """
    
    def validate_affects(
        self,
        macro_data: np.ndarray,
        company_data: np.ndarray,
        llm_correlation: str,
        llm_sensitivity: float
    ) -> Dict[str, Any]:
        """
        AFFECTS 관계의 통계적 검증
        
        Args:
            macro_data: 거시지표 시계열 데이터
            company_data: 기업 데이터 시계열
            llm_correlation: LLM 추출값 ("DIRECT" | "INVERSE")
            llm_sensitivity: LLM 추출 민감도 (0.0~1.0)
        
        Returns:
            {
                "correlation": "DIRECT" | "INVERSE",
                "sensitivity": float,
                "confidence": float,
                "p_value": float
            }
        """
        if len(macro_data) < 2 or len(company_data) < 2:
            return {
                "correlation": llm_correlation,
                "sensitivity": llm_sensitivity,
                "confidence": 0.5,
                "p_value": 1.0,
                "reason": "데이터 부족"
            }

        # Pearson 상관계수 계산
        pearson_r, p_value = pearsonr(macro_data, company_data)
        
        # 통계적 correlation 판단
        stat_correlation = "DIRECT" if pearson_r > 0 else "INVERSE"
        
        # LLM vs 통계 비교
        correlation_match = (llm_correlation == stat_correlation)
        sensitivity_delta = abs(llm_sensitivity - abs(pearson_r))
        
        # Confidence 계산
        if p_value < 0.05:
            if correlation_match and sensitivity_delta < 0.2:
                confidence = 0.9  # 높은 신뢰도
            elif correlation_match:
                confidence = 0.7  # 중간 신뢰도
            else:
                confidence = 0.4  # 불일치
        else:
            confidence = 0.5  # 통계적 유의성 낮음
        
        return {
            "correlation": stat_correlation,
            "sensitivity": abs(pearson_r),
            "confidence": confidence,
            "p_value": p_value
        }
