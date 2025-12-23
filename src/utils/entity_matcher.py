"""
Entity Matcher - 마스터 엔티티 리스트 기반 정규화

YAML에서 마스터 엔티티를 로드하고, 새로운 엔티티 이름을 
정규화된 이름으로 매칭합니다.

사용법:
    from src.utils.entity_matcher import EntityMatcher
    
    matcher = EntityMatcher()
    canonical_name = matcher.match("삼성")  # → "삼성전자"
"""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class EntityMatcher:
    """마스터 엔티티 리스트 기반 정규화기"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: master_entities.yaml 경로 (기본: src/config/master_entities.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "master_entities.yaml"
        
        self.config_path = config_path
        self.entities: Dict[str, dict] = {}  # canonical_name -> {type, ticker, aliases}
        self.alias_map: Dict[str, str] = {}  # alias -> canonical_name
        self.config: dict = {}
        
        self._load_master_entities()
    
    def _load_master_entities(self):
        """YAML에서 마스터 엔티티 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 설정 로드
            self.config = data.get('matching_config', {
                'min_similarity_threshold': 80,
                'case_insensitive': True,
                'ignore_whitespace': True
            })
            
            # 엔티티 카테고리 순회
            for category, entities in data.items():
                if category == 'matching_config':
                    continue
                    
                if not isinstance(entities, list):
                    continue
                    
                for entity in entities:
                    name = entity.get('name')
                    if not name:
                        continue
                    
                    # 엔티티 저장
                    self.entities[name] = {
                        'type': entity.get('type'),
                        'ticker': entity.get('ticker'),
                        'aliases': entity.get('aliases', [])
                    }
                    
                    # 별칭 맵 생성
                    for alias in entity.get('aliases', []):
                        normalized_alias = self._normalize_for_matching(alias)
                        self.alias_map[normalized_alias] = name
                    
                    # 정규 이름도 자기 자신으로 매핑
                    normalized_name = self._normalize_for_matching(name)
                    self.alias_map[normalized_name] = name
            
            logger.info(f"Loaded {len(self.entities)} master entities with {len(self.alias_map)} aliases")
            
        except Exception as e:
            logger.error(f"Failed to load master entities: {e}")
            raise
    
    def _normalize_for_matching(self, text: str) -> str:
        """매칭용 텍스트 정규화"""
        if not text:
            return ""
        
        result = text
        
        # 대소문자 무시
        if self.config.get('case_insensitive', True):
            result = result.lower()
        
        # 공백 정규화
        if self.config.get('ignore_whitespace', True):
            result = re.sub(r'\s+', '', result)
        
        # 특수문자 제거
        result = re.sub(r'[^\w가-힣]', '', result)
        
        return result
    
    def match(self, name: str) -> str:
        """
        엔티티 이름을 정규화된 이름으로 매칭
        
        Args:
            name: 원본 엔티티 이름
        
        Returns:
            정규화된 이름 (매칭 실패시 원본 반환)
        """
        if not name:
            return name
        
        # 1. 정확한 별칭 매칭
        normalized = self._normalize_for_matching(name)
        if normalized in self.alias_map:
            return self.alias_map[normalized]
        
        # 2. Fuzzy 매칭 시도
        threshold = self.config.get('min_similarity_threshold', 80) / 100.0
        best_match, best_score = self._fuzzy_match(normalized, threshold)
        
        if best_match:
            logger.debug(f"Fuzzy matched '{name}' → '{best_match}' (score: {best_score:.2f})")
            return best_match
        
        # 3. 매칭 실패시 원본 반환
        return name
    
    def _fuzzy_match(self, normalized_name: str, threshold: float) -> Tuple[Optional[str], float]:
        """
        Fuzzy 매칭 수행
        
        Args:
            normalized_name: 정규화된 이름
            threshold: 최소 유사도 임계값 (0-1)
        
        Returns:
            (매칭된 정규 이름, 유사도 점수)
        """
        best_match = None
        best_score = 0.0
        
        for alias, canonical in self.alias_map.items():
            # SequenceMatcher로 유사도 계산
            score = SequenceMatcher(None, normalized_name, alias).ratio()
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = canonical
        
        return best_match, best_score
    
    def get_entity_info(self, name: str) -> Optional[dict]:
        """
        엔티티 정보 조회
        
        Args:
            name: 엔티티 이름 (별칭도 가능)
        
        Returns:
            {type, ticker, aliases} 또는 None
        """
        canonical = self.match(name)
        return self.entities.get(canonical)
    
    def get_canonical_name(self, name: str) -> str:
        """match()의 별칭"""
        return self.match(name)
    
    def get_all_canonical_names(self) -> List[str]:
        """모든 정규 이름 리스트 반환"""
        return list(self.entities.keys())
    
    def add_entity(self, name: str, entity_type: str, aliases: List[str] = None, ticker: str = None):
        """
        런타임에 엔티티 추가 (YAML에는 반영 안됨)
        
        Args:
            name: 정규 이름
            entity_type: NodeType
            aliases: 별칭 리스트
            ticker: 주식 코드
        """
        aliases = aliases or []
        
        self.entities[name] = {
            'type': entity_type,
            'ticker': ticker,
            'aliases': aliases
        }
        
        # 별칭 맵 갱신
        for alias in aliases:
            normalized_alias = self._normalize_for_matching(alias)
            self.alias_map[normalized_alias] = name
        
        normalized_name = self._normalize_for_matching(name)
        self.alias_map[normalized_name] = name


# 싱글톤 인스턴스
_matcher_instance: Optional[EntityMatcher] = None


def get_entity_matcher() -> EntityMatcher:
    """싱글톤 EntityMatcher 인스턴스 반환"""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = EntityMatcher()
    return _matcher_instance


def match_entity(name: str) -> str:
    """편의 함수: 엔티티 이름 매칭"""
    return get_entity_matcher().match(name)
