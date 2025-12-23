"""
Gemini PDF → Neo4j 파이프라인 테스트

PDF를 Gemini API로 직접 파싱하여 Knowledge Graph를 추출하고
Neo4j에 주입하는 전체 파이프라인을 테스트합니다.
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

from src.dataflows.parsers.gemini_pdf import GeminiPDFParser
from src.dataflows.neo4j_loader import Neo4jKGLoader, load_kg_from_gemini_pdf
from src.models.nodes import KnowledgeGraph  # nodes.py 스키마 사용

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_gemini_pdf_parser():
    """Gemini PDF Parser 단독 테스트"""
    print("\n" + "="*80)
    print("TEST: Gemini PDF Parser")
    print("="*80)
    
    # 샘플 PDF 선택
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data/raw/reports")
        return None
    
    sample_pdf = pdf_files[0]
    print(f"\n[Test File]: {sample_pdf.name}")
    print(f"[File Size]: {sample_pdf.stat().st_size / 1024:.2f} KB")
    
    # Gemini PDF Parser 초기화
    from src.config.llm_config import get_model
    parser = GeminiPDFParser(model_name=get_model("pdf_parsing"))
    
    try:
        print("\n📄 Parsing PDF with Gemini API...")
        print("  ⏳ Uploading to Gemini Files API...")
        print("  ⏳ Extracting Knowledge Graph with Structured Output...")
        
        result = parser.parse(str(sample_pdf))
        
        kg = result["knowledge_graph"]
        metadata = result["metadata"]
        
        print("\n[Parsing Result]")
        print(f"  ✅ Parser: {metadata['parser']}")
        print(f"  ✅ Model: {metadata['model']}")
        print(f"  ✅ Entities: {metadata['entity_count']}")
        print(f"  ✅ Relations: {metadata['relation_count']}")
        
        # 엔티티 샘플 출력 (처음 5개)
        if kg.entities:
            print(f"\n[Entity Samples (첫 5개)]:")
            for i, entity in enumerate(kg.entities[:5], 1):
                print(f"\n  Entity {i}:")
                print(f"    Name: {entity.name}")
                print(f"    Type: {entity.type.value}")
                print(f"    Confidence: {entity.confidence}")
                if entity.properties:
                    print(f"    Properties: {json.dumps(entity.properties, ensure_ascii=False, indent=6)}")
        
        # 관계 샘플 출력 (처음 5개)
        if kg.relations:
            print(f"\n[Relation Samples (첫 5개)]:")
            for i, rel in enumerate(kg.relations[:5], 1):
                print(f"\n  Relation {i}:")
                print(f"    {rel.subject} -[{rel.predicate.value}]-> {rel.object}")
                print(f"    Weight: {rel.weight}")
                if rel.source:
                    print(f"    Source: {rel.source}")
        
        # JSON 자동 저장 확인
        json_path = result['metadata'].get('json_path')
        if json_path:
            print(f"\n💾 JSON Auto-saved to:")
            print(f"  {json_path}")
            
            # JSON 파일 로드 테스트
            kg_loaded = KnowledgeGraph.load_from_json(json_path)
            print(f"\n  ✅ JSON file loaded successfully!")
            print(f"     Entities: {len(kg_loaded.entities)}")
            print(f"     Relations: {len(kg_loaded.relations)}")
        else:
            print(f"\n⚠️  Warning: JSON path not found in metadata")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Gemini PDF Parser test failed: {str(e)}", exc_info=True)
        return None


def test_neo4j_loader(kg_result):
    """Neo4j Loader 테스트"""
    print("\n" + "="*80)
    print("TEST: Neo4j Knowledge Graph Loader")
    print("="*80)
    
    if kg_result is None:
        print("❌ Skipping Neo4j test (no KG result)")
        return
    
    kg = kg_result["knowledge_graph"]
    
    # Neo4j 연결 정보
    print("\n[Neo4j Connection]")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"  URI: {neo4j_uri}")
    print(f"  User: {neo4j_user}")
    
    try:
        loader = Neo4jKGLoader(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
        
        print("\n📊 Loading Knowledge Graph to Neo4j...")
        print(f"  Entities: {len(kg.entities)}")
        print(f"  Relations: {len(kg.relations)}")
        
        # 기존 데이터 삭제 여부 확인
        clear_choice = input("\n기존 Neo4j 데이터를 모두 삭제하시겠습니까? (y/N): ").strip().lower()
        clear_existing = (clear_choice == 'y')
        
        load_stats = loader.load_knowledge_graph(kg, clear_existing=clear_existing)
        
        print("\n[Load Statistics]")
        print(f"  ✅ Nodes Created: {load_stats['nodes_created']}")
        print(f"  ✅ Relationships Created: {load_stats['relationships_created']}")
        
        # 그래프 통계
        print("\n📈 Graph Statistics:")
        graph_stats = loader.get_graph_stats()
        
        print(f"\n  Total Nodes: {graph_stats['total_nodes']}")
        print(f"  Total Relationships: {graph_stats['total_relationships']}")
        
        print(f"\n  Nodes by Label:")
        for label, count in graph_stats['nodes_by_label'].items():
            print(f"    {label}: {count}")
        
        print(f"\n  Relationships by Type:")
        for rel_type, count in graph_stats['relationships_by_type'].items():
            print(f"    {rel_type}: {count}")
        
        loader.close()
        
        print("\n✅ Neo4j Loading Complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Neo4j loader test failed: {str(e)}", exc_info=True)


def test_full_pipeline():
    """전체 파이프라인 테스트 (PDF → Neo4j 한 번에)"""
    print("\n" + "="*80)
    print("TEST: Full Pipeline (PDF → Gemini → Neo4j)")
    print("="*80)
    
    # 샘플 PDF 선택
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    sample_pdf = pdf_files[0]
    print(f"\n[Test File]: {sample_pdf.name}")
    
    # Neo4j 연결 정보
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    try:
        print("\n🚀 Running full pipeline...")
        
        result = load_kg_from_gemini_pdf(
            pdf_path=str(sample_pdf),
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            clear_existing=False
        )
        
        print("\n[Pipeline Result]")
        print(f"\n  Parser Result:")
        pprint(result["parser_result"], indent=4)
        
        print(f"\n  Load Stats:")
        pprint(result["load_stats"], indent=4)
        
        print(f"\n  Graph Stats:")
        pprint(result["graph_stats"], indent=4)
        
        print("\n✅ Full Pipeline Complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Full pipeline test failed: {str(e)}", exc_info=True)


def main():
    """메인 테스트 실행"""
    print("\n" + "="*80)
    print("🚀 Gemini PDF → Neo4j Pipeline Testing Suite")
    print("="*80)
    print("\nPDF를 Gemini API로 분석하여 Knowledge Graph를 추출하고")
    print("Neo4j에 주입하는 파이프라인을 테스트합니다.")
    print("\n모델: gemini-2.5-flash")
    print("="*80 + "\n")
    
    print("어떤 테스트를 실행하시겠습니까?")
    print("  1. Gemini PDF Parser만 (KG 추출 + JSON 저장)")
    print("  2. Neo4j Loader만 (기존 KG 로드)")
    print("  3. 전체 파이프라인 (PDF → Gemini → Neo4j)")
    
    choice = input("\n선택 (1-3): ").strip()
    
    if choice == "1":
        test_gemini_pdf_parser()
    elif choice == "2":
        # 먼저 KG 추출 필요
        kg_result = test_gemini_pdf_parser()
        if kg_result:
            test_neo4j_loader(kg_result)
    elif choice == "3":
        test_full_pipeline()
    else:
        print("❌ Invalid choice")
    
    print("\n" + "="*80)
    print("✅ Testing Complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
