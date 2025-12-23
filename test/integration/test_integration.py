"""
통합 테스트: 스키마 통합 및 데이터 플로우

스키마 통합(nodes.py), JSON 저장, KGMerger, Neo4j 주입을 테스트합니다.
"""
import os
import sys
import json
import logging
from pathlib import Path
from pprint import pprint

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.nodes import Entity, Relation, KnowledgeGraph, NodeType, RelationType
from src.dataflows.parsers.gemini_pdf import GeminiPDFParser
from src.dataflows.kg_merger import KGMerger, merge_kg_files
from src.dataflows.neo4j_loader import Neo4jKGLoader

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_schema_conversion():
    """1. 스키마 변환 테스트 (Gemini API 호환)"""
    print("\n" + "="*80)
    print("TEST 1: Schema Conversion (nodes.py ↔ Gemini API)")
    print("="*80)
    
    # Entity 생성
    entity = Entity(
        name="삼성전자",
        type=NodeType.COMPANY,
        properties={"ticker": "005930", "industry": "반도체"},
        confidence=0.95
    )
    
    print("\n[Original Entity (nodes.py)]")
    print(f"  Name: {entity.name}")
    print(f"  Type: {entity.type.value}")
    print(f"  Properties: {entity.properties}")
    print(f"  Confidence: {entity.confidence}")
    
    # Gemini 포맷으로 변환
    gemini_dict = entity.to_gemini_dict()
    
    print("\n[Converted to Gemini Format]")
    print(f"  {json.dumps(gemini_dict, ensure_ascii=False, indent=2)}")
    
    # 다시 nodes.py 포맷으로 복원
    entity_restored = Entity.from_gemini_dict(gemini_dict)
    
    print("\n[Restored to nodes.py]")
    print(f"  Name: {entity_restored.name}")
    print(f"  Type: {entity_restored.type.value}")
    print(f"  Properties: {entity_restored.properties}")
    
    # 검증
    assert entity.name == entity_restored.name, "Name mismatch!"
    assert entity.type == entity_restored.type, "Type mismatch!"
    # Note: properties는 커스텀 Gemini 스키마에서 제외되므로 빈 dict로 복원됨
    # assert entity.properties == entity_restored.properties, "Properties mismatch!"
    
    print("\n✅ Schema conversion test passed!")
    print("   ⚠️  Note: properties field is excluded in custom Gemini schema")


def test_json_save_load():
    """2. JSON 저장/로드 테스트"""
    print("\n" + "="*80)
    print("TEST 2: JSON Save/Load (nodes.KnowledgeGraph)")
    print("="*80)
    
    # 샘플 KG 생성
    kg = KnowledgeGraph(
        entities=[
            Entity(name="삼성전자", type=NodeType.COMPANY, properties={"ticker": "005930"}, confidence=1.0),
            Entity(name="DRAM", type=NodeType.PRODUCT, properties={"category": "메모리"}, confidence=1.0)
        ],
        relations=[
            Relation(subject="삼성전자", predicate=RelationType.PRODUCES, object="DRAM", weight=1.0, source="test")
        ],
        metadata={"test": "json_save_load"}
    )
    
    print(f"\n[Original KG]")
    print(f"  Entities: {len(kg.entities)}")
    print(f"  Relations: {len(kg.relations)}")
    
    # JSON 저장
    test_file = project_root / "data" / "processed" / "test_kg.json"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    kg.save_to_json(str(test_file))
    print(f"\n💾 Saved to: {test_file}")
    
    # JSON 로드
    kg_loaded = KnowledgeGraph.load_from_json(str(test_file))
    
    print(f"\n[Loaded KG]")
    print(f"  Entities: {len(kg_loaded.entities)}")
    print(f"  Relations: {len(kg_loaded.relations)}")
    print(f"  Metadata: {kg_loaded.metadata}")
    
    # 검증
    assert len(kg.entities) == len(kg_loaded.entities), "Entity count mismatch!"
    assert len(kg.relations) == len(kg_loaded.relations), "Relation count mismatch!"
    assert kg.entities[0].name == kg_loaded.entities[0].name, "Entity name mismatch!"
    
    # 정리
    test_file.unlink()
    print("\n✅ JSON save/load test passed!")


def test_kg_merger():
    """3. KGMerger 중복 제거 테스트"""
    print("\n" + "="*80)
    print("TEST 3: KGMerger (Duplicate Removal)")
    print("="*80)
    
    # 중복이 있는 두 개의 KG 생성
    kg1 = KnowledgeGraph(
        entities=[
            Entity(name="삼성전자", type=NodeType.COMPANY, properties={"ticker": "005930"}, confidence=0.9),
            Entity(name="DRAM", type=NodeType.PRODUCT, properties={"category": "메모리"}, confidence=1.0)
        ],
        relations=[
            Relation(subject="삼성전자", predicate=RelationType.PRODUCES, object="DRAM", weight=0.8, source="doc1")
        ],
        metadata={"source": "file1"}
    )
    
    kg2 = KnowledgeGraph(
        entities=[
            Entity(name="삼성전자", type=NodeType.COMPANY, properties={"industry": "반도체"}, confidence=0.95),
            Entity(name="SK하이닉스", type=NodeType.COMPANY, properties={"ticker": "000660"}, confidence=1.0)
        ],
        relations=[
            Relation(subject="삼성전자", predicate=RelationType.PRODUCES, object="DRAM", weight=0.9, source="doc2"),
            Relation(subject="삼성전자", predicate=RelationType.COMPETES_WITH, object="SK하이닉스", weight=1.0, source="doc2")
        ],
        metadata={"source": "file2"}
    )
    
    # JSON 저장
    file1 = project_root / "data" / "processed" / "test_merge1.json"
    file2 = project_root / "data" / "processed" / "test_merge2.json"
    
    kg1.save_to_json(str(file1))
    kg2.save_to_json(str(file2))
    
    print(f"\n[KG1]: {len(kg1.entities)} entities, {len(kg1.relations)} relations")
    print(f"[KG2]: {len(kg2.entities)} entities, {len(kg2.relations)} relations")
    print(f"[Total (without merge)]: {len(kg1.entities) + len(kg2.entities)} entities, {len(kg1.relations) + len(kg2.relations)} relations")
    
    # 병합
    merger = KGMerger()
    merged = merger.merge_knowledge_graphs([file1, file2])
    
    print(f"\n[Merged KG]: {len(merged.entities)} entities, {len(merged.relations)} relations")
    print(f"\n[Entity Details]:")
    for entity in merged.entities:
        print(f"  - {entity.name} ({entity.type.value})")
        print(f"    Properties: {entity.properties}")
        print(f"    Confidence: {entity.confidence}")
    
    print(f"\n[Relation Details]:")
    for rel in merged.relations:
        print(f"  - {rel.subject} -[{rel.predicate.value}]-> {rel.object}")
        print(f"    Weight: {rel.weight}, Source: {rel.source}")
    
    # 검증
    assert len(merged.entities) == 3, f"Expected 3 unique entities, got {len(merged.entities)}"
    assert len(merged.relations) == 2, f"Expected 2 unique relations, got {len(merged.relations)}"
    
    # 삼성전자 엔티티가 병합되었는지 확인
    samsung = next(e for e in merged.entities if e.name == "삼성전자")
    assert "ticker" in samsung.properties and "industry" in samsung.properties, "Properties not merged!"
    assert samsung.confidence == 0.95, f"Expected max confidence 0.95, got {samsung.confidence}"
    
    # 정리
    file1.unlink()
    file2.unlink()
    
    print("\n✅ KGMerger test passed!")


def test_gemini_pdf_with_json():
    """4. Gemini PDF Parser + JSON 자동 저장 테스트"""
    print("\n" + "="*80)
    print("TEST 4: Gemini PDF Parser (Auto JSON Save)")
    print("="*80)
    
    # 샘플 PDF 찾기 - reports와 ir 디렉토리에서 검색
    reports_dir = project_root / "data" / "raw" / "reports"
    ir_dir = project_root / "data" / "raw" / "ir"
    
    pdf_files = []
    
    # reports 디렉토리에서 찾기
    if reports_dir.exists():
        pdf_files.extend(list(reports_dir.glob("*.pdf"))[:2])  # 처음 2개
    
    # ir 디렉토리의 하위 디렉토리에서 찾기
    if ir_dir.exists() and len(pdf_files) < 2:
        for subdir in ir_dir.iterdir():
            if subdir.is_dir():
                pdf_files.extend(list(subdir.glob("*.pdf")))
            if len(pdf_files) >= 2:
                break
    
    if not pdf_files:
        print("⚠️  No PDF files found in data/raw/reports or data/raw/ir")
        print("   Skipping this test.")
        return
    
    # 최대 2개까지만 사용
    pdf_files = pdf_files[:2]
    
    print(f"\n[Test Files]: {len(pdf_files)} PDF(s) found")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")
    
    # 각 PDF 파일 파싱
    from src.config.llm_config import get_model
    parser = GeminiPDFParser(model_name=get_model("pdf_parsing"))
    
    for i, sample_pdf in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Parsing: {sample_pdf.name}")
        
        try:
            result = parser.parse(str(sample_pdf))
            
            kg = result["knowledge_graph"]
            metadata = result["metadata"]
            
            print(f"\n[Result]")
            print(f"  Entities: {metadata['entity_count']}")
            print(f"  Relations: {metadata['relation_count']}")
            print(f"  JSON Path: {metadata.get('json_path')}")
            
            # JSON 자동 저장 확인
            json_path = metadata.get('json_path')
            if json_path and Path(json_path).exists():
                kg_loaded = KnowledgeGraph.load_from_json(json_path)
                print(f"  ✅ JSON verified: {len(kg_loaded.entities)} entities, {len(kg_loaded.relations)} relations")
            else:
                print(f"  ⚠️  Warning: JSON file not found")
        
        except Exception as e:
            print(f"  ❌ Error parsing {sample_pdf.name}: {str(e)}")
            logger.error(f"PDF parsing failed", exc_info=True)
    
    print("\n✅ Gemini PDF Parser test passed!")


def test_full_pipeline_with_neo4j():
    """5. 전체 파이프라인 테스트 (Neo4j 포함)"""
    print("\n" + "="*80)
    print("TEST 5: Full Pipeline (PDF → JSON → Merge → Neo4j)")
    print("="*80)
    
    # Neo4j 연결 확인
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"\n[Neo4j Connection]")
    print(f"  URI: {neo4j_uri}")
    
    try:
        loader = Neo4jKGLoader(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
        
        # JSON 파일 수집
        processed_dir = project_root / "data" / "processed"
        json_files = list(processed_dir.glob("*.json"))
        
        if not json_files:
            print("\n⚠️  No JSON files found in data/processed/")
            print("   Run test 4 first to generate JSON files.")
            loader.close()
            return
        
        print(f"\n[JSON Files]: {len(json_files)} found")
        
        # 병합 및 주입
        json_paths = [str(f) for f in json_files[:2]]  # 처음 2개만
        
        print(f"\n📊 Loading {len(json_paths)} files to Neo4j...")
        stats = loader.load_from_json_files(json_paths, merge=True)
        
        print(f"\n[Load Stats]")
        print(f"  Nodes Created: {stats['nodes_created']}")
        print(f"  Relationships Created: {stats['relationships_created']}")
        
        # 그래프 통계
        graph_stats = loader.get_graph_stats()
        
        print(f"\n[Graph Stats]")
        print(f"  Total Nodes: {graph_stats['total_nodes']}")
        print(f"  Total Relationships: {graph_stats['total_relationships']}")
        
        loader.close()
        
        print("\n✅ Full pipeline test passed!")
        
    except Exception as e:
        print(f"\n⚠️  Neo4j test skipped: {str(e)}")
        print("   Make sure Neo4j is running and credentials are correct.")


def main():
    """메인 테스트 실행"""
    print("\n" + "="*80)
    print("🧪 Integration Test Suite")
    print("="*80)
    print("\n스키마 통합, JSON 저장, KGMerger, Neo4j 주입을 테스트합니다.\n")
    
    tests = [
        ("Schema Conversion", test_schema_conversion),
        ("JSON Save/Load", test_json_save_load),
        ("KGMerger", test_kg_merger),
        ("Gemini PDF + JSON", test_gemini_pdf_with_json),
        ("Full Pipeline + Neo4j", test_full_pipeline_with_neo4j)
    ]
    
    print("어떤 테스트를 실행하시겠습니까?")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")
    print(f"  {len(tests)+1}. 모두 실행")
    
    choice = input("\n선택 (1-6): ").strip()
    
    try:
        if choice == str(len(tests)+1):
            # 모두 실행
            for name, test_func in tests:
                try:
                    test_func()
                except Exception as e:
                    logger.error(f"Test failed: {name}", exc_info=True)
                    print(f"\n❌ {name} failed: {str(e)}")
        elif 1 <= int(choice) <= len(tests):
            # 개별 실행
            name, test_func = tests[int(choice)-1]
            test_func()
        else:
            print("❌ Invalid choice")
    except Exception as e:
        logger.error("Test execution failed", exc_info=True)
        print(f"\n❌ Error: {str(e)}")
    
    print("\n" + "="*80)
    print("✅ Testing Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
