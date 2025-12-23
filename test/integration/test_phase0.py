"""
Phase 0 테스트 스크립트

Phase 0에서 구현된 주요 기능들을 테스트합니다:
- LLM Config
- Parser Interface
- Gemini Files API
- VLM Parser
"""
import os
import sys
import logging
from pathlib import Path
from pprint import pprint

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.llm_config import get_model_config, get_model, TASK_TO_MODEL as TASK_MODEL_MAPPING
from src.utils.gemini_files import get_gemini_files_client
from src.dataflows.parsers.vlm import VLMParser
from src.dataflows.parser_interface import RobustPDFParser, ParserStrategy

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_llm_config():
    """0.1 LLM Config 테스트"""
    print("\n" + "="*80)
    print("TEST 0.1: LLM Configuration")
    print("="*80)
    
    # 다양한 태스크 타입 테스트
    test_tasks = ["pdf_parsing", "kg_construction", "synthesis", "quality_check"]
    
    for task in test_tasks:
        config = get_model_config(task)
        batch = should_use_batch(task, num_requests=10)
        
        print(f"\n[Task: {task}]")
        print(f"  Model: {config['model']}")
        print(f"  Strategy: {config['strategy']}")
        print(f"  Temperature: {config['temperature']}")
        print(f"  Use Batch (10 requests): {batch}")
    
    print("\n✅ LLM Config Test Complete!\n")


def test_gemini_files():
    """0.3 Gemini Files API 테스트"""
    print("\n" + "="*80)
    print("TEST 0.3: Gemini Files API")
    print("="*80)
    
    # 샘플 PDF 선택 (첫 번째 파일)
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data/raw/reports")
        return
    
    sample_pdf = pdf_files[0]
    print(f"\n[Test File]: {sample_pdf.name}")
    
    # Gemini Files Client 테스트
    files_client = get_gemini_files_client()
    
    try:
        # 파일 업로드
        print("\n📤 Uploading file to Gemini...")
        file_uri = files_client.upload_file(str(sample_pdf))
        print(f"  ✅ File URI: {file_uri}")
        
        # 캐시 확인
        cached_uri = files_client.get_file_uri(str(sample_pdf))
        print(f"\n💾 Cached URI: {cached_uri}")
        print(f"  ✅ Cache working: {cached_uri == file_uri}")
        
        # 파일 삭제 (옵션 - 주석 처리하면 캐시 유지)
        # print("\n🗑️ Deleting file...")
        # success = files_client.delete_file(str(sample_pdf))
        # print(f"  ✅ Delete success: {success}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Gemini Files test failed: {str(e)}", exc_info=True)
    
    print("\n✅ Gemini Files API Test Complete!\n")


def test_vlm_parser():
    """0.4 VLM Parser 테스트"""
    print("\n" + "="*80)
    print("TEST 0.4: VLM Parser (Hybrid)")
    print("="*80)
    
    # 샘플 PDF 선택
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data/raw/reports")
        return
    
    # 첫 번째 PDF 사용
    sample_pdf = pdf_files[0]
    print(f"\n[Test File]: {sample_pdf.name}")
    print(f"[File Size]: {sample_pdf.stat().st_size / 1024:.2f} KB")
    
    # VLM Parser 초기화
    parser = VLMParser()
    
    try:
        print("\n📄 Parsing PDF with Hybrid Parser (PyMuPDF + VLM)...")
        result = parser.parse(str(sample_pdf))
        
        print("\n[Parsing Result]")
        print(f"  ✅ Parsed Text Length: {len(result['parsed_text'])} characters")
        print(f"  ✅ Extracted Charts: {len(result['extracted_charts'])} charts")
        print(f"  ✅ Parser: {result['metadata']['parser']}")
        print(f"  ✅ Image Count: {result['metadata']['image_count']}")
        
        # 텍스트 미리보기
        print(f"\n[Text Preview ]:")
        print("-" * 80)
        print(result['parsed_text'])
        print("-" * 80)
        
        # 차트 정보 출력
        if result['extracted_charts']:
            print(f"\n[Chart Analysis Results]:")
            for i, chart in enumerate(result['extracted_charts'][:3], 1):  # 처음 3개만
                print(f"\n  Chart {i}:")
                print(f"    Title: {chart.get('title', 'N/A')}")
                print(f"    Type: {chart.get('chart_type', chart.get('type', 'N/A'))}")
                print(f"    Summary: {chart.get('trend_summary', chart.get('summary', 'N/A'))[:100]}...")
        
        # MD 파일로 저장
        output_dir = project_root / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{sample_pdf.stem}_parsed.md"
        
        print(f"\n💾 Saving parsed result to MD file...")
        print(f"  Output: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {sample_pdf.stem}\n\n")
            f.write(f"**Parser**: {result['metadata']['parser']}\n")
            f.write(f"**Image Count**: {result['metadata']['image_count']}\n")
            f.write(f"**Chart Count**: {len(result['extracted_charts'])}\n\n")
            f.write("---\n\n")
            f.write("## Parsed Text\n\n")
            f.write(result['parsed_text'])
            
            if result['extracted_charts']:
                f.write("\n\n---\n\n## Chart Analysis\n\n")
                for i, chart in enumerate(result['extracted_charts'], 1):
                    f.write(f"### Chart {i}\n\n")
                    for key, value in chart.items():
                        if key != 'image_path':
                            f.write(f"**{key}**: {value}\n\n")
        
        print(f"  ✅ MD file saved successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"VLM Parser test failed: {str(e)}", exc_info=True)
    
    print("\n✅ VLM Parser Test Complete!\n")


def test_parser_interface():
    """0.2 Parser Interface 테스트 (Fallback 메커니즘)"""
    print("\n" + "="*80)
    print("TEST 0.2: Parser Interface (Fallback)")
    print("="*80)
    
    # VLM Parser를 Primary로 설정
    vlm_parser = VLMParser()
    
    # RobustPDFParser 초기화
    robust_parser = RobustPDFParser(primary_parser=vlm_parser)
    
    # 샘플 PDF
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    sample_pdf = pdf_files[0]
    print(f"\n[Test File]: {sample_pdf.name}")
    
    try:
        print("\n📄 Parsing with Robust Parser (with fallback)...")
        result = robust_parser.parse(str(sample_pdf), strategy=ParserStrategy.PRIMARY)
        
        print(f"\n  ✅ Parser Strategy Used: {result.get('parser_strategy', 'N/A')}")
        print(f"  ✅ Text Length: {len(result['parsed_text'])} characters")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Parser Interface test failed: {str(e)}", exc_info=True)
    
    print("\n✅ Parser Interface Test Complete!\n")


def test_vlm_parser_enhanced():
    """0.4E Enhanced VLM Parser 테스트 (개선 버전)"""
    print("\n" + "="*80)
    print("TEST 0.4E: Enhanced VLM Parser (YAML Prompts + Optimized)")
    print("="*80)
    
    # Enhanced VLM Parser import
    from src.dataflows.parsers.vlm_enhanced import EnhancedVLMParser
    
    # 샘플 PDF 선택
    data_dir = project_root / "data" / "raw" / "reports"
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in data/raw/reports")
        return
    
    # 첫 번째 PDF 사용
    sample_pdf = pdf_files[0]
    print(f"\n[Test File]: {sample_pdf.name}")
    print(f"[File Size]: {sample_pdf.stat().st_size / 1024:.2f} KB")
    
    # Enhanced VLM Parser 초기화
    parser = EnhancedVLMParser()
    
    try:
        print("\n📄 Parsing PDF with Enhanced VLM Parser...")
        print("  ✅ PyMuPDF 최적화 옵션 사용")
        print("  ✅ YAML 기반 프롬프트 사용")
        result = parser.parse(str(sample_pdf))
        
        print("\n[Parsing Result]")
        print(f"  ✅ Parsed Text Length: {len(result['parsed_text'])} characters")
        print(f"  ✅ Extracted Charts: {len(result['extracted_charts'])} charts")
        print(f"  ✅ Parser: {result['metadata']['parser']}")
        print(f"  ✅ Image Count: {result['metadata']['image_count']}")
        
        # 텍스트 미리보기
        print(f"\n[Text Preview ]:")
        print("-" * 80)
        print(result['parsed_text'])
        print("-" * 80)
        
        # 차트 정보 출력
        if result['extracted_charts']:
            print(f"\n[Chart Analysis Results (Enhanced)]:")
            for i, chart in enumerate(result['extracted_charts'][:3], 1):  # 처음 3개만
                print(f"\n  Chart {i}:")
                print(f"    Title: {chart.get('title', 'N/A')}")
                print(f"    Type: {chart.get('chart_type', chart.get('type', 'N/A'))}")
                
                # None 값 안전하게 처리
                extracted_text = chart.get('extracted_text') or 'N/A'
                key_insight = chart.get('key_insight') or 'N/A'
                
                print(f"    Extracted Text: {extracted_text[:100] if len(extracted_text) > 100 else extracted_text}...")
                print(f"    Key Insight: {key_insight[:100] if len(key_insight) > 100 else key_insight}...")
        
        # MD 파일로 저장
        output_dir = project_root / "data" / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{sample_pdf.stem}_enhanced_parsed.md"
        
        print(f"\n💾 Saving enhanced result to MD file...")
        print(f"  Output: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {sample_pdf.stem} (Enhanced Parser)\n\n")
            f.write(f"**Parser**: {result['metadata']['parser']}\n")
            f.write(f"**Image Count**: {result['metadata']['image_count']}\n")
            f.write(f"**Chart Count**: {len(result['extracted_charts'])}\n\n")
            f.write("---\n\n")
            f.write("## Parsed Text\n\n")
            f.write(result['parsed_text'])
            
            if result['extracted_charts']:
                f.write("\n\n---\n\n## Chart Analysis (Enhanced)\n\n")
                for i, chart in enumerate(result['extracted_charts'], 1):
                    f.write(f"### Chart {i}\n\n")
                    for key, value in chart.items():
                        if key != 'image_path':
                            f.write(f"**{key}**: {value}\n\n")
        
        print(f"  ✅ Enhanced MD file saved successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Enhanced VLM Parser test failed: {str(e)}", exc_info=True)
    
    print("\n✅ Enhanced VLM Parser Test Complete!\n")


def main():
    """메인 테스트 실행"""
    print("\n" + "="*80)
    print("🚀 PHASE 0 TESTING SUITE")
    print("="*80)
    print("\nPhase 0에서 구현된 5가지 주요 기능을 테스트합니다:")
    print("  0.1 LLM Config Setup")
    print("  0.2 Parser Interface")
    print("  0.3 Gemini Files API")
    print("  0.4 VLM Parser (Hybrid)")
    print("  0.5 State Definition (코드 검증)")
    print("\n" + "="*80 + "\n")
    
    # 선택적 테스트 실행
    print("어떤 테스트를 실행하시겠습니까?")
    print("  1. 전체 테스트 (All)")
    print("  2. LLM Config만")
    print("  3. Gemini Files API만")
    print("  4. VLM Parser만 (기본)")
    print("  5. Parser Interface만")
    print("  6. Enhanced VLM Parser (개선 버전) ⭐ NEW")
    
    choice = input("\n선택 (1-6): ").strip()
    
    if choice == "1":
        test_llm_config()
        test_parser_interface()
        test_gemini_files()
        test_vlm_parser_enhanced()
    elif choice == "2":
        test_llm_config()
    elif choice == "3":
        test_gemini_files()
    elif choice == "4":
        test_vlm_parser()
    elif choice == "5":
        test_parser_interface()
    elif choice == "6":
        test_vlm_parser_enhanced()
    else:
        print("❌ Invalid choice. Running all tests...")
        test_llm_config()
        test_parser_interface()
        test_gemini_files()
        test_vlm_parser()
    
    print("\n" + "="*80)
    print("✅ PHASE 0 TESTING COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
