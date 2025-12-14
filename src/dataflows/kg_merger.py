"""
Knowledge Graph Merger

여러 JSON 파일의 Knowledge Graph를 병합하고 중복을 제거합니다.
"""
import logging
from typing import List, Dict, Any
from pathlib import Path

from ..models.nodes import KnowledgeGraph, Entity, Relation

logger = logging.getLogger(__name__)


class KGMerger:
    """
    Knowledge Graph 병합기
    
    여러 파싱결과를 하나의 통합된 그래프로 병합하고 중복을 제거합니다.
    """
    
    def __init__(self):
        pass
    
    def merge_knowledge_graphs(self, json_files: List[Path]) -> KnowledgeGraph:
        """
        여러 JSON 파일의 Knowledge Graph를 병합하고 중복 제거
        
        병합 전략:
        - Entity: (name, type) 기준으로 중복 제거
          - properties는 병합 (나중 파일이 우선)
          - confidence는 최대값 선택
        - Relation: (subject, predicate, object) 기준으로 중복 제거
          - weight는 최대값 선택
          - source는 쉼표로 연결
        
        Args:
            json_files: 병합할 JSON 파일 경로 리스트
        
        Returns:
            병합된 KnowledgeGraph 객체
        """
        all_entities: Dict[tuple, Entity] = {}  # (name, type) -> Entity
        all_relations: Dict[tuple, Relation] = {}  # (subject, predicate, object) -> Relation
        all_metadata: List[Dict[str, Any]] = []
        
        logger.info(f"Merging {len(json_files)} KG JSON files...")
        
        for json_file in json_files:
            try:
                # JSON 로드
                kg = KnowledgeGraph.load_from_json(str(json_file))
                
                # 엔티티 병합
                for entity in kg.entities:
                    key = (entity.name, entity.type)
                    
                    if key in all_entities:
                        # 기존 엔티티와 병합
                        existing = all_entities[key]
                        # properties 병합 (나중 것이 우선)
                        existing.properties.update(entity.properties)
                        # confidence 최대값
                        existing.confidence = max(existing.confidence, entity.confidence)
                    else:
                        # 새 엔티티 추가
                        all_entities[key] = entity
                
                # 관계 병합
                for relation in kg.relations:
                    key = (relation.subject, relation.predicate, relation.object)
                    
                    if key in all_relations:
                        # 기존 관계와 병합
                        existing = all_relations[key]
                        # weight 최대값
                        existing.weight = max(existing.weight, relation.weight)
                        # source 병합
                        if relation.source and existing.source != relation.source:
                            existing.source = f"{existing.source}, {relation.source}"
                    else:
                        # 새 관계 추가
                        all_relations[key] = relation
                
                # 메타데이터 수집
                all_metadata.append(kg.metadata)
                
                logger.info(f"Merged {json_file.name}: {len(kg.entities)} entities, {len(kg.relations)} relations")
                
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {str(e)}")
                continue
        
        # 병합 결과 생성
        merged_kg = KnowledgeGraph(
            entities=list(all_entities.values()),
            relations=list(all_relations.values()),
            metadata={
                "merged_from": [str(f) for f in json_files],
                "source_count": len(json_files),
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
        병합 후 결과를 JSON 파일로 저장
        
        Args:
            json_files: 병합할 JSON 파일들
            output_path: 출력 파일 경로
        
        Returns:
            병합된 KnowledgeGraph
        """
        merged_kg = self.merge_knowledge_graphs(json_files)
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
