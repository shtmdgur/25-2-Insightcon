"""
Knowledge Graph Merger

여러 JSON 파일의 Knowledge Graph를 병합하고 중복을 제거합니다.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path

from ..models.nodes import KnowledgeGraph, Entity, Relation
from ..utils.entity_matcher import get_entity_matcher

logger = logging.getLogger(__name__)


class KGMerger:
    """
    Knowledge Graph 병합기
    
    여러 파싱결과를 하나의 통합된 그래프로 병합하고 중복을 제거합니다.
    """
    
    def __init__(self):
        self.entity_matcher = get_entity_matcher()
    
    def merge_knowledge_graphs(self, kgs: List[KnowledgeGraph]) -> KnowledgeGraph:
        """
        여러 Knowledge Graph 객체를 병합하고 중복 제거
        
        Args:
            kgs: 병합할 KnowledgeGraph 객체 리스트
        
        Returns:
            병합된 KnowledgeGraph 객체
        """
        all_entities: Dict[tuple, Entity] = {}  # (name, NodeType) -> Entity
        all_relations: Dict[tuple, Relation] = {}  # (subject, RelationType, object) -> Relation
        all_metadata: List[Dict[str, Any]] = []
        
        logger.info(f"Merging {len(kgs)} Knowledge Graphs...")
        
        for kg in kgs:
            try:
                # 엔티티 병합 (정규화된 이름 기준)
                for entity in kg.entities:
                    # EntityMatcher로 정규화
                    normalized_name = self.entity_matcher.match(entity.name)
                    key = (normalized_name, entity.type)
                    
                    if key in all_entities:
                        # 기존 엔티티와 병합
                        existing = all_entities[key]
                        # properties 병합 (나중 것이 우선, 단 None은 제외)
                        for k, v in entity.properties.items():
                            if v is not None:
                                existing.properties[k] = v
                        # confidence 최대값
                        existing.confidence = max(existing.confidence, entity.confidence)
                    else:
                        # 새 엔티티 추가 (정규화된 이름으로)
                        entity.name = normalized_name
                        all_entities[key] = entity
                
                # 관계 병합 (정규화된 subject/object 기준)
                for relation in kg.relations:
                    # subject/object 정규화
                    normalized_subject = self.entity_matcher.match(relation.subject)
                    normalized_object = self.entity_matcher.match(relation.object)
                    key = (normalized_subject, relation.predicate, normalized_object)
                    
                    if key in all_relations:
                        # 기존 관계와 병합
                        existing = all_relations[key]
                        # weight 최대값
                        existing.weight = max(existing.weight, relation.weight)
                        # source 병합
                        if relation.source and existing.source != relation.source:
                            existing.source = f"{existing.source}, {relation.source}"
                    else:
                        # 새 관계 추가 (정규화된 이름으로)
                        relation.subject = normalized_subject
                        relation.object = normalized_object
                        all_relations[key] = relation
                
                # 메타데이터 수집
                all_metadata.append(kg.metadata)
                
            except Exception as e:
                logger.error(f"Failed to merge a KG: {str(e)}", exc_info=True)
                continue
        
        # 병합 결과 생성
        merged_kg = KnowledgeGraph(
            entities=list(all_entities.values()),
            relations=list(all_relations.values()),
            metadata={
                "merged_from": [kg.metadata.get("source_file", "unknown") for kg in kgs],
                "source_count": len(kgs),
                "total_entities": len(all_entities),
                "total_relations": len(all_relations),
                "source_metadata": all_metadata
            }
        )
        
        logger.info(
            f"Merge complete: {len(merged_kg.entities)} unique entities, "
            f"{len(merged_kg.relations)} unique relations"
        )
        
        return merged_kg
    
    def merge_and_save(
        self,
        json_files: List[Path],
        output_path: Path
    ) -> KnowledgeGraph:
        """
        여러 JSON 파일을 로드하여 병합 후 저장
        """
        kgs = []
        for f in json_files:
            try:
                kgs.append(KnowledgeGraph.load_from_json(str(f)))
            except Exception as e:
                logger.error(f"Failed to load {f}: {e}")
        
        merged_kg = self.merge_knowledge_graphs(kgs)
        merged_kg.save_to_json(str(output_path))
        
        logger.info(f"Merged KG saved to: {output_path}")
        return merged_kg


def merge_kg_files(
    processed_dir: Path,
    output_file: str = "merged_kg.json",
    pattern: str = "*.json"
) -> KnowledgeGraph:
    """
    지정된 디렉토리의 모든 KG JSON 파일을 병합
    
    Args:
        processed_dir: processed 디렉토리 경로
        output_file: 출력 파일명
        pattern: 파일 패턴 (기본: *.json)
    
    Returns:
        병합된 KnowledgeGraph
    """
    merger = KGMerger()
    
    # JSON 파일 수집
    json_files = sorted(processed_dir.glob(pattern))
    
    # merged_kg.json은 제외
    json_files = [f for f in json_files if f.name != output_file]
    
    if not json_files:
        logger.warning(f"No JSON files found in {processed_dir}")
        return KnowledgeGraph(entities=[], relations=[], metadata={})
    
    # 병합 및 저장
    output_path = processed_dir / output_file
    return merger.merge_and_save(json_files, output_path)
