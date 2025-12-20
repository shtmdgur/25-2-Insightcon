"""
엔티티 정규화 (Entity Linking)

"삼성", "삼성전자", "Samsung" → 단일 노드로 통합
"""
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class EntityNormalizer:
    """
    엔티티 정규화 클래스
    
    다양한 표기의 엔티티를 표준 엔티티로 매핑합니다.
    """
    
    def __init__(self, master_data_path: Optional[str] = None):
        """
        Args:
            master_data_path: Master Data CSV 파일 경로
        """
        self.master_data_path = master_data_path or "data/master/krx_companies.csv"
        self.master_data: Optional[pd.DataFrame] = None
        
        # Master Data 로드 시도
        if Path(self.master_data_path).exists():
            self._load_master_data()
    
    def _load_master_data(self) -> pd.DataFrame:
        """
        KRX 상장사 리스트 로드
        
        CSV 구조:
        ticker,name,name_en,aliases
        005930,삼성전자,Samsung Electronics,"삼성,Samsung,SEC"
        000660,SK하이닉스,SK Hynix,"하이닉스,Hynix"
        
        Returns:
            Master Data DataFrame
        """
        try:
            self.master_data = pd.read_csv(self.master_data_path)
            logger.info(f"Loaded {len(self.master_data)} companies from master data")
            return self.master_data
        except Exception as e:
            logger.warning(f"Failed to load master data: {str(e)}")
            # Placeholder: 빈 DataFrame
            self.master_data = pd.DataFrame(columns=["ticker", "name", "name_en", "aliases"])
            return self.master_data
    
    def normalize_entity(self, mention: str) -> Dict[str, Any]:
        """
        텍스트 멘션을 표준 엔티티로 매핑
        
        Args:
            mention: 원본 텍스트 멘션
        
        Returns:
            {
                "canonical_name": str,  # 표준 이름
                "ticker": str,           # 종목 코드
                "aliases": List[str],    # 별칭들
                "confidence": float      # 신뢰도 (0.0~1.0)
            }
        """
        if self.master_data is None or len(self.master_data) == 0:
            # Master Data 없으면 원본 그대로 반환
            return {
                "canonical_name": mention,
                "ticker": None,
                "aliases": [],
                "confidence": 0.5
            }
        
        # 1. Exact Match (Ticker 또는 정확한 이름)
        exact_match = self.master_data[
            (self.master_data['ticker'] == mention) |
            (self.master_data['name'] == mention) |
            (self.master_data['name_en'] == mention)
        ]
        
        if not exact_match.empty:
            return self._to_entity_dict(exact_match.iloc[0], confidence=1.0)
        
        # 2. Fuzzy Matching (철자 유사도)
        fuzzy_matches = self._fuzzy_search(mention)
        if fuzzy_matches:
            return fuzzy_matches[0]  # 가장 유사도 높은 것
        
        # 3. 매칭 실패 - 원본 그대로 반환
        logger.warning(f"No match found for: {mention}")
        return {
            "canonical_name": mention,
            "ticker": None,
            "aliases": [],
            "confidence": 0.3
        }
    
    def _fuzzy_search(self, mention: str, threshold: int = 80) -> List[Dict]:
        """
        Levenshtein Distance 기반 유사도 검색
        
        Args:
            mention: 검색할 멘션
            threshold: 유사도 임계값 (0~100)
        
        Returns:
            매칭 결과 (신뢰도 순 정렬)
        """
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            logger.warning("fuzzywuzzy not installed. Skipping fuzzy matching.")
            return []
        
        matches = []
        for _, row in self.master_data.iterrows():
            # 이름 및 영문명과 비교
            score = max(
                fuzz.ratio(mention, row['name']),
                fuzz.ratio(mention, row['name_en'])
            )
            
            if score > threshold:
                matches.append(self._to_entity_dict(row, confidence=score/100))
        
        return sorted(matches, key=lambda x: x['confidence'], reverse=True)
    
    def _to_entity_dict(self, row: pd.Series, confidence: float) -> Dict[str, Any]:
        """Series를 Entity Dict로 변환"""
        aliases_str = row.get('aliases', '')
        aliases = [a.strip() for a in aliases_str.split(',')] if aliases_str else []
        
        return {
            "canonical_name": row['name'],
            "ticker": row['ticker'],
            "aliases": aliases,
            "confidence": confidence
        }


# 싱글톤 인스턴스
_entity_normalizer: Optional[EntityNormalizer] = None


def get_entity_normalizer() -> EntityNormalizer:
    """싱글톤 EntityNormalizer 반환"""
    global _entity_normalizer
    
    if _entity_normalizer is None:
        _entity_normalizer = EntityNormalizer()
    
    return _entity_normalizer
