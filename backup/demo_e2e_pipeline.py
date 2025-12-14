"""
Phase 0 + Phase 1 통합 E2E 데모
==================================

전체 파이프라인 테스트:
PDF 파일 → Parsing (Phase 0) → Knowledge Graph 구축 (Phase 1) → Neo4j 저장

사용법:
    python demo_e2e_pipeline.py
"""

import os
import sys
from pathlib import Path
import logging

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dataflows.parsers.vlm import VLMParser
from src.dataflows.parsers.gemini_pdf import GeminiPDFParser
from src.dataflows.neo4j_loader import Neo4jKGLoader
from src.agents.kg_construction import KGConstructionAgent
from src.utils.event_extractor import EventExtractor
from src.utils.time_series_processor import TimeSeriesProcessor
from src.utils.neo4j_client import Neo4jClient
from src.utils.llm_config import get_llm

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """헤더 출력"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100 + "\n")


def test_phase0_vlm_parser():
    """Phase 0: VLM Parser 테스트 (차트 분석용)"""
    print_header("📄 Phase 0: VLM Parser - 차트 세부 분석 특화")
    
    print("💡 용도: PDF의 **차트/그래프**를 상세 분석할 때 사용")
    print("   (Knowledge Graph 추출은 GeminiPDFParser 권장!)\n")
    
    # 샘플 PDF 선택
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  No PDF files found in data/raw/reports")
        print("   샘플 PDF를 해당 폴더에 넣어주세요.\n")
        return None
    
    sample_pdf = pdf_files[0]
    print(f"📁 테스트 파일: {sample_pdf.name}")
    print(f"📊 파일 크기: {sample_pdf.stat().st_size / 1024:.2f} KB\n")
    
    try:
        # VLM Parser 초기화
        parser = VLMParser()
        
        print("🔍 Parsing PDF (Text + Chart Analysis)...")
        result = parser.parse(str(sample_pdf))
        
        print("✅ Parsing 완료!")
        print(f"\n📝 결과:")
        print(f"  - 추출된 텍스트: {len(result['parsed_text'])} characters")
        print(f"  - 분석된 차트: {len(result['extracted_charts'])}개")
        print(f"  - 파서: {result['metadata']['parser']}")
        
        # 차트 분석 결과 강조
        if result['extracted_charts']:
            print(f"\n📊 차트 분석 결과:")
            for i, chart in enumerate(result['extracted_charts'][:3], 1):
                print(f"  {i}. {chart.get('title', 'Chart')} - {chart.get('summary', 'N/A')[:50]}...")
        
        # 텍스트 미리보기
        print(f"\n📖 텍스트 미리보기 (처음 500자):")
        print("-" * 100)
        print(result['parsed_text'][:500])
        print("-" * 100)
        
        return result
        
    except Exception as e:
        logger.error(f"VLM Parser 실패: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}\n")
        return None


def test_phase0_gemini_pdf_parser():
    """Phase 0: Gemini PDF Native Parser 테스트"""
    print_header("🤖 Phase 0: Gemini PDF Native Parser (Direct KG Extraction)")
    
    # 샘플 PDF 선택
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  No PDF files found in data/raw/reports\n")
        return None
    
    sample_pdf = pdf_files[0]
    print(f"📁 테스트 파일: {sample_pdf.name}\n")
    
    try:
        # Gemini PDF Parser 초기화
        parser = GeminiPDFParser(model_name="gemini-2.5-pro")
        
        print("🔍 Gemini로 PDF 분석 및 Knowledge Graph 추출 중...")
        print("   (이 작업은 PDF 크기에 따라 30초~2분 소요될 수 있습니다)\n")
        
        result = parser.parse(str(sample_pdf))
        
        kg = result['knowledge_graph']
        
        print("✅ Knowledge Graph 추출 완료!")
        print(f"\n📊 결과:")
        print(f"  - 엔티티: {len(kg.entities)}개")
        print(f"  - 관계: {len(kg.relations)}개")
        print(f"  - 모델: {result['metadata']['model']}")
        
        # 엔티티 미리보기
        print(f"\n🏢 추출된 엔티티 (처음 10개):")
        for i, entity in enumerate(kg.entities[:10], 1):
            print(f"  {i}. [{entity.label.value}] {entity.name}")
        
        # 관계 미리보기
        print(f"\n🔗 추출된 관계 (처음 10개):")
        for i, relation in enumerate(kg.relations[:10], 1):
            print(f"  {i}. {relation.source_id} -[{relation.type.value}]-> {relation.target_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Gemini PDF Parser 실패: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}\n")
        return None


def test_phase1_kg_construction(parsed_text: str):
    """Phase 1: KG Construction Agent 테스트"""
    print_header("🏗️  Phase 1: Knowledge Graph Construction Agent")
    
    try:
        # LLM 및 Neo4j 초기화
        llm = get_llm("quick")  # Gemini 2.5 Flash
        neo4j_client = Neo4jClient()
        
        # KGConstructionAgent 초기화
        kg_agent = KGConstructionAgent(llm, neo4j_client)
        
        print("🔍 텍스트에서 엔티티 및 관계 추출 중...")
        
        # Document 처리
        result = kg_agent.process_document(
            document=parsed_text[:3000],  # 처음 3000자만 (토큰 절약)
            source="demo_vlm_parsed.md"
        )
        
        print("✅ Knowledge Graph 구축 완료!")
        print(f"\n📊 통계:")
        print(f"  - 생성된 엔티티: {result['stats']['entities']}개")
        print(f"  - 생성된 관계: {result['stats']['relations']}개")
        print(f"  - 에러: {result['stats']['errors']}개")
        
        # KG 상세 정보
        kg = result['knowledge_graph']
        
        if kg['entities']:
            print(f"\n🏢 엔티티 샘플:")
            for entity in kg['entities'][:5]:
                print(f"  - [{entity['type']}] {entity['name']}")
        
        if kg['relations']:
            print(f"\n🔗 관계 샘플:")
            for relation in kg['relations'][:5]:
                print(f"  - {relation['subject']} -[{relation['predicate']}]-> {relation['object']}")
        
        neo4j_client.close()
        return result
        
    except Exception as e:
        logger.error(f"KG Construction 실패: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}\n")
        return None


def test_phase1_neo4j_injection(kg_result):
    """Phase 1: Neo4j Loader를 사용한 KG 주입"""
    print_header("💾 Phase 1: Neo4j Knowledge Graph Loader")
    
    try:
        # Neo4j Loader 초기화
        loader = Neo4jKGLoader()
        
        print("🔍 Knowledge Graph를 Neo4j에 주입 중...")
        
        # KG 로드
        stats = loader.load_knowledge_graph(
            kg=kg_result['knowledge_graph'],
            clear_existing=False  # 기존 데이터 유지
        )
        
        print("✅ Neo4j 주입 완료!")
        print(f"\n📊 주입 통계:")
        print(f"  - 노드 생성: {stats.get('nodes_created', 0)}개")
        print(f"  - 관계 생성: {stats.get('relationships_created', 0)}개")
        print(f"  - 에러: {stats.get('errors', 0)}개")
        
        # 그래프 통계 조회
        print(f"\n📈 Neo4j 전체 그래프 통계:")
        graph_stats = loader.get_graph_stats()
        
        for label, count in graph_stats.get('node_counts', {}).items():
            print(f"  - {label}: {count}개")
        
        print(f"\n🌐 Neo4j Browser에서 확인:")
        print(f"  → http://localhost:7474")
        print(f"  → Cypher: MATCH (n) RETURN n LIMIT 50")
        
        loader.close()
        return stats
        
    except Exception as e:
        logger.error(f"Neo4j injection 실패: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}\n")
        return None


def test_e2e_pipeline_option1():
    """옵션 1: VLM Parser → KG Construction → Neo4j"""
    print_header("🚀 E2E Pipeline Option 1: VLM Parser → KG Agent → Neo4j")
    
    print("📝 파이프라인 단계:")
    print("  1️⃣  Phase 0: VLM Parser로 PDF 파싱 (Text + Charts)")
    print("  2️⃣  Phase 1: KG Construction Agent로 엔티티/관계 추출")
    print("  3️⃣  Phase 1: Neo4j에 Knowledge Graph 저장\n")
    
    # Step 1: VLM Parser
    parsed_result = test_phase0_vlm_parser()
    if not parsed_result:
        print("❌ VLM Parser 실패로 파이프라인 중단\n")
        return
    
    input("\n계속하려면 Enter를 누르세요...")
    
    # Step 2: KG Construction
    kg_result = test_phase1_kg_construction(parsed_result['parsed_text'])
    if not kg_result:
        print("❌ KG Construction 실패로 파이프라인 중단\n")
        return
    
    input("\n계속하려면 Enter를 누르세요...")
    
    # Step 3: Neo4j Injection
    test_phase1_neo4j_injection(kg_result)
    
    print_header("✅ E2E Pipeline Option 1 완료!")


def test_e2e_pipeline_option2():
    """옵션 2: Gemini PDF Parser → Neo4j (Direct)"""
    print_header("🚀 E2E Pipeline Option 2: Gemini PDF Parser → Neo4j (Direct)")
    
    print("📝 파이프라인 단계:")
    print("  1️⃣  Phase 0: Gemini PDF Parser로 Knowledge Graph 직접 추출")
    print("  2️⃣  Phase 1: Neo4j에 Knowledge Graph 저장\n")
    
    # Step 1: Gemini PDF Parser
    kg_result = test_phase0_gemini_pdf_parser()
    if not kg_result:
        print("❌ Gemini PDF Parser 실패로 파이프라인 중단\n")
        return
    
    input("\n계속하려면 Enter를 누르세요...")
    
    # Step 2: Neo4j Injection
    test_phase1_neo4j_injection(kg_result)
    
    print_header("✅ E2E Pipeline Option 2 완료!")


def main():
    """메인 함수"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                     Phase 0 + Phase 1 통합 E2E 데모                                 ║
║                                                                                      ║
║  이 데모는 PDF 파싱부터 Neo4j Knowledge Graph 구축까지 전체 파이프라인을 테스트합니다  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("⚠️  사전 요구사항:")
    print("  1. .env 파일에 GEMINI_API_KEY 설정")
    print("  2. Neo4j 인스턴스 실행 중 (localhost:7687)")
    print("  3. data/raw/reports/ 폴더에 테스트용 PDF 파일 존재\n")
    
    # 환경 변수 체크
    if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        print("❌ 에러: GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일을 확인해주세요.\n")
        return
    
    # PDF 파일 체크
    data_dir = project_root / "data" / "raw" / "reports"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"⚠️  {data_dir} 폴더가 생성되었습니다.")
        print("   테스트용 PDF 파일을 이 폴더에 넣어주세요.\n")
        return
    
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"⚠️  {data_dir} 폴더에 PDF 파일이 없습니다.")
        print("   테스트용 PDF 파일을 이 폴더에 넣어주세요.\n")
        return
    
    print(f"✅ 테스트용 PDF 파일 발견: {len(pdf_files)}개\n")
    
    # 파이프라인 선택
    print("어떤 E2E 파이프라인을 실행하시겠습니까?\n")
    print("  1️⃣  Option 1: VLM Parser → KG Agent → Neo4j")
    print("     (장점: 차트 분석 포함, 단계별 확인 가능)")
    print("     (단점: 비용 증가, 처리 시간 김)")
    print()
    print("  2️⃣  Option 2: Gemini PDF Parser → Neo4j (Direct)")
    print("     (장점: 빠름, 일관된 KG 출력, Batch API 활용 가능)")
    print("     (단점: 차트 세부 분석 제한적)")
    print()
    print("  3️⃣  Both (두 방식 모두 실행하여 비교)")
    print()
    
    choice = input("선택 (1-3): ").strip()
    
    try:
        if choice == "1":
            test_e2e_pipeline_option1()
        elif choice == "2":
            test_e2e_pipeline_option2()
        elif choice == "3":
            test_e2e_pipeline_option1()
            input("\n\n옵션 2로 계속하려면 Enter를 누르세요...")
            test_e2e_pipeline_option2()
        else:
            print("❌ 잘못된 선택입니다. 옵션 1을 실행합니다.\n")
            test_e2e_pipeline_option1()
        
        print_header("🎉 전체 데모 완료!")
        print("""
다음 단계:
  1. Neo4j Browser에서 그래프 확인: http://localhost:7474
  2. Phase 2 고도화 작업 진행 (Multi-hop Retrieval, Quality Check 등)
  3. 실제 데이터셋으로 대규모 테스트
        """)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 중단했습니다.")
    except Exception as e:
        logger.error(f"데모 실행 중 에러 발생: {str(e)}")
        print(f"\n❌ 에러 발생: {str(e)}")


if __name__ == "__main__":
    main()
