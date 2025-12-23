"""
KG Construction Agent Orchestration Test

KGConstructionAgent가 5개의 Parser Agent를 오케스트레이션하여
data/preprocessed에서 Neo4j까지 전체 파이프라인을 실행하는 테스트입니다.

Parser Agents (v3.0):
1. PDFParserAgent - PDF 파일 처리 (data/raw에서)
2. DARTParserAgent - DART 공시 데이터 처리
3. NewsParserAgent - 뉴스 데이터 처리 (CSV)
4. MacroParserAgent - 거시경제 데이터 처리 (CSV)
5. FundParserAgent - 펀더멘털 데이터 처리 (CSV)

제거됨 (v3.0): PriceParserAgent
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from src.agents.kg_construction import KGConstructionAgent
from src.config.parser_config import PARSER_CONFIGS

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # 간결한 포맷
    datefmt='%H:%M:%S'  # 시간만 표시
)
logger = logging.getLogger(__name__)

# 외부 라이브러리 로그 숨기기 (WARNING 이상만)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)

# 환경변수 로드
load_dotenv()


def print_banner(text: str):
    """배너 출력"""
    print("\n" + "=" * 80)
    print(f"🚀 {text}")
    print("=" * 80 + "\n")


def print_section(text: str):
    """섹션 헤더 출력"""
    print("\n" + "-" * 80)
    print(f"📌 {text}")
    print("-" * 80)


def check_environment():
    """환경 설정 확인"""
    print_section("1. 환경 설정 확인")
    
    # API 키 확인
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        logger.error("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        return False
    print(f"✅ GEMINI_API_KEY: {gemini_key[:10]}...")
    
    # Neo4j 설정 확인
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    print(f"✅ NEO4J_URI: {neo4j_uri}")
    print(f"✅ NEO4J_USER: {neo4j_user}")
    print(f"✅ NEO4J_PASSWORD: {'*' * len(neo4j_password) if neo4j_password else 'None'}")
    
    # 데이터 디렉토리 확인
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    print(f"\n📁 데이터 디렉토리:")
    print(f"  - Root: {data_dir}")
    print(f"  - Raw: {raw_dir} (exists: {raw_dir.exists()})")
    print(f"  - Processed: {processed_dir} (exists: {processed_dir.exists()})")
    
    return True


def check_data_sources():
    """데이터 소스 확인 (v3.0: preprocessed 기준)"""
    print_section("2. 데이터 소스 스캔")
    
    preprocessed_dir = project_root / "data" / "preprocessed"
    raw_dir = project_root / "data" / "raw"
    
    # 각 데이터 소스별 파일 확인 (v3.0 반영)
    sources = {
        "PDF (raw)": list(raw_dir.glob("reports/**/*.pdf")) + list(raw_dir.glob("ir/**/*.pdf")),
        "DART (preprocessed)": [preprocessed_dir / 'dart'] if (preprocessed_dir / 'dart').exists() else [],
        "News (preprocessed)": list(preprocessed_dir.glob("news/**/*.csv")),
        "Macro": list(preprocessed_dir.glob("macro/**/*.csv")) or list(raw_dir.glob("macro/**/*.csv")),
        "Fund (preprocessed)": list(preprocessed_dir.glob("fund/**/*.csv"))
        # Price: v3.0에서 제거됨
    }
    
    total_files = 0
    for source_name, files in sources.items():
        count = len(files)
        total_files += count
        status = "✅" if count > 0 else "⚠️"
        print(f"{status} {source_name}: {count}개 파일")
        if count > 0 and count <= 3:
            for f in files[:3]:
                print(f"    - {f.name}")
        elif count > 3:
            for f in files[:3]:
                print(f"    - {f.name}")
            print(f"    ... 외 {count-3}개")
    
    print(f"\n📊 총 {total_files}개 파일 발견")
    
    if total_files == 0:
        print("\n⚠️  경고: 처리할 데이터 파일이 없습니다.")
        print("   테스트를 계속하려면 data/raw 디렉토리에 데이터를 추가하세요.")
        return False
    
    return True


def display_parser_configs():
    """Parser 설정 출력"""
    print_section("3. Parser 설정 확인")
    
    print("📝 News Parser:")
    print(f"  - Sample Size: {PARSER_CONFIGS.news.sample_size}건")
    print(f"  - Use LLM: {PARSER_CONFIGS.news.use_llm}")
    print(f"  - LLM Model: {PARSER_CONFIGS.news.llm_model}")
    print(f"  - Use Batch: {PARSER_CONFIGS.news.use_batch}")
    
    print("\n📝 Macro Parser:")
    print(f"  - Sample per Series: {PARSER_CONFIGS.macro.sample_per_series}개")
    
    print("\n📝 DART Parser:")
    print(f"  - Sample Disclosure: {PARSER_CONFIGS.dart.sample_disclosure}")
    print(f"  - Sample Financial: {PARSER_CONFIGS.dart.sample_financial}")
    
    print("\n📝 Fund Parser:")
    print(f"  - Save as Snapshot: {PARSER_CONFIGS.fund.save_as_snapshot}")


def enable_test_mode():
    """테스트 모드 활성화 (소량 샘플링)"""
    from src.config.parser_config import update_config
    
    print_section("테스트 모드 활성화")
    print("⚠️  테스트 모드: 소량 데이터만 처리합니다")
    print("  - 뉴스: 5행만 파싱")
    print("  - PDF: reports 1개 + ir 1개\n")
    
    # 파서별 테스트 모드 설정 적용 (v3.0)
    update_config('news', sample_size=5)  # 뉴스 5행만
    # update_config('price', sample_size=10)  # v3.0: 제거됨
    
    print("✅ 테스트 모드 설정 적용 완료")


def run_orchestration_test(load_to_neo4j: bool = False, test_mode: bool = False):
    """
    KG Construction Agent 오케스트레이션 테스트
    
    Args:
        load_to_neo4j: Neo4j 주입 여부
        test_mode: 테스트 모드 (소량 데이터만 처리)
    """
    print_banner("KG Construction Agent 오케스트레이션 테스트")
    
    # 테스트 모드 활성화
    if test_mode:
        enable_test_mode()
    
    # 1. 환경 확인
    if not check_environment():
        print("\n❌ 환경 설정이 올바르지 않습니다. 테스트를 중단합니다.")
        return
    
    # 2. 데이터 소스 확인
    has_data = check_data_sources()
    if not has_data:
        response = input("\n계속하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("테스트를 중단합니다.")
            return
    
    # 3. Parser 설정 확인
    display_parser_configs()
    
    # 4. KG Construction Agent 초기화
    print_section("4. KG Construction Agent 초기화")
    
    try:
        # LLM 초기화 (News Parser용)
        from langchain_google_genai import ChatGoogleGenerativeAI
        from src.config.llm_config import get_model
        llm = ChatGoogleGenerativeAI(model=get_model("news_parsing"))
        print(f"✅ LLM 초기화 완료: {get_model('news_parsing')}")
        
        agent = KGConstructionAgent(
            data_dir=project_root / "data",
            neo4j_uri=os.getenv("NEO4J_URI"),  # None이면 주입 스킵
            llm=llm  # News Parser용 LLM 전달
        )
        print("✅ KGConstructionAgent 초기화 완료")
    except Exception as e:
        logger.error(f"❌ Agent 초기화 실패: {e}")
        return
    
    # 5. Knowledge Graph 구축 실행
    print_section("5. Knowledge Graph 자동 구축")
    
    start_time = datetime.now()
    print(f"⏰ 시작 시각: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 테스트 모드: 파일 수 제한
        data_sources = None
        if test_mode:
            print("\n⚠️  테스트 모드: 파일 수 제한 적용")
            raw_dir = project_root / "data" / "raw"
            preprocessed_dir = project_root / "data" / "preprocessed"
            
            # PDF: reports 1개 + ir/Samsung 1개 = 총 2개
            pdf_files = []
            reports_pdfs = list((preprocessed_dir / 'reports').glob('*.pdf'))[:1]  # reports에서 1개
            if not reports_pdfs:
                reports_pdfs = list((raw_dir / 'reports').glob('*.pdf'))[:1]
            pdf_files.extend(reports_pdfs)
            
            # ir 폴더에서 첫 번째 회사의 첫 번째 PDF
            ir_dir = preprocessed_dir / 'ir'
            if not ir_dir.exists():
                ir_dir = raw_dir / 'ir'
            if ir_dir.exists():
                company_dirs = sorted([d for d in ir_dir.iterdir() if d.is_dir()])
                if company_dirs:
                    first_company_pdf = list(company_dirs[0].glob('*.pdf'))[:1]
                    pdf_files.extend(first_company_pdf)
            
            data_sources = {
                'pdf': pdf_files,  # 총 2개 (reports 1개 + ir 1개)
                'dart': [preprocessed_dir / 'dart'] if (preprocessed_dir / 'dart').exists() else [],  # 전체
                'news': list((preprocessed_dir / 'news').glob('*.csv')),  # 전체 (내부에서 5행 샘플링)
                'macro': list((raw_dir / 'macro').glob('*.csv')),  # 전체
                'fund': list((preprocessed_dir / 'fund').glob('*.csv'))  # 전체
            }
            
            print(f"  PDF: {len(data_sources['pdf'])}개 (reports 1 + ir 1)")
            print(f"  DART: {len(data_sources['dart'])}개 디렉토리 (전체)")
            print(f"  News: {len(data_sources['news'])}개 CSV (내부 5행 샘플링)")
            print(f"  Macro: {len(data_sources['macro'])}개 CSV (전체)")
            print(f"  Fund: {len(data_sources['fund'])}개 CSV (전체)\n")
        
        result = agent.construct_knowledge_graph(
            data_sources=data_sources,  # 테스트 모드일 때 제한된 파일 목록 사용
            auto_scan=(not test_mode),  # 테스트 모드가 아니면 auto_scan
            use_batch=False,  # Batch API 사용 여부
            load_to_neo4j=load_to_neo4j  # Neo4j 주입 여부
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n⏰ 종료 시각: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  소요 시간: {duration:.2f}초")
        
        # 6. 결과 출력
        print_section("6. 실행 결과")
        
        # Parser 결과
        # Parser 결과
        print("\n📊 Parser 실행 결과:")
        for parser_name, parser_result in result.get('parser_results', {}).items():
            # success 키가 있거나 failed가 0이면 성공으로 간주
            is_success = parser_result.get('failed', 0) == 0 and parser_result.get('total', 0) > 0
            status = "✅" if is_success else "⚠️" if parser_result.get('failed', 0) > 0 else "ℹ️"
            
            total = parser_result.get('total', 0)
            success = parser_result.get('success', 0)
            failed = parser_result.get('failed', 0)
            
            print(f"\n{status} {parser_name}:")
            print(f"    Files: {total}개 (성공: {success}, 실패: {failed})")
            
            # 에러가 있는 경우 출력
            errors = parser_result.get('errors', [])
            if errors:
                for idx, error in enumerate(errors[:3]): # 최대 3개까지만 출력
                    print(f"    ❌ Error {idx+1}: {error}")
                if len(errors) > 3:
                    print(f"    ... 외 {len(errors)-3}개 에러")
        
        # JSON 파일
        print("\n📄 생성된 JSON 파일:")
        json_files = result.get('json_files', [])
        if isinstance(json_files, int):
            print(f"  총 {json_files}개 파일 (목록 없음)")
        else:
            print(f"  총 {len(json_files)}개 파일")
            for json_file in json_files[:5]:
                print(f"    - {Path(json_file).name}")
            if len(json_files) > 5:
                print(f"    ... 외 {len(json_files)-5}개")
        
        # 병합된 KG
        print("\n🔗 병합된 Knowledge Graph:")
        merged_kg = result.get('merged_kg')
        if merged_kg:
            print(f"  Entities: {len(merged_kg.entities)}개")
            print(f"  Relations: {len(merged_kg.relations)}개")
            
            # Entity 타입별 통계
            entity_types = {}
            for entity in merged_kg.entities:
                entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
            
            print("\n  📌 Entity 타입별 분포:")
            for etype, count in sorted(entity_types.items(), key=lambda x: -x[1]):
                print(f"    - {etype}: {count}개")
        
        # Neo4j 통계
        if load_to_neo4j:
            print("\n💾 Neo4j 주입 결과:")
            neo4j_stats = result.get('neo4j_stats', {})
            if neo4j_stats:
                static_nodes = neo4j_stats.get('static_nodes', 0)
                dynamic_nodes = neo4j_stats.get('dynamic_nodes', 0)
                total_nodes = static_nodes + dynamic_nodes
                print(f"  Nodes Created: {total_nodes}개 (Static: {static_nodes}, Dynamic: {dynamic_nodes})")
                print(f"  Relationships Created: {neo4j_stats.get('relationships_created', 0)}개")
            else:
                print("  ⚠️  Neo4j 통계를 가져올 수 없습니다.")
        
        # 최종 상태
        print_banner("테스트 완료 ✅")
        print(f"📊 총 Entities: {len(merged_kg.entities) if merged_kg else 0}개")
        print(f"🔗 총 Relations: {len(merged_kg.relations) if merged_kg else 0}개")
        print(f"⏱️  실행 시간: {duration:.2f}초")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Knowledge Graph 구축 실패: {e}", exc_info=True)
        print(f"\n❌ 오류 발생: {e}")
        return None


def interactive_menu():
    """대화형 메뉴"""
    print_banner("KG Construction Agent 테스트 메뉴")
    
    print("테스트 옵션을 선택하세요:")
    print("1. 환경 및 데이터 소스만 확인")
    print("2. Parser 설정 확인")
    print("3. KG 구축 (Neo4j 주입 없음)")
    print("4. KG 구축 + Neo4j 주입")
    print("5. 전체 테스트 (설정 확인 + KG 구축 + Neo4j)")
    print("6. 샘플 테스트 - KG 구축")
    print("7. 샘플 테스트 - KG + Neo4j")
    print("0. 종료")
    
    choice = input("\n선택 (0-7): ").strip()
    
    if choice == "0":
        print("테스트를 종료합니다.")
        return
    
    elif choice == "1":
        check_environment()
        check_data_sources()
    
    elif choice == "2":
        display_parser_configs()
    
    elif choice == "3":
        run_orchestration_test(load_to_neo4j=False, test_mode=False)
    
    elif choice == "4":
        run_orchestration_test(load_to_neo4j=True, test_mode=False)
    
    elif choice == "5":
        run_orchestration_test(load_to_neo4j=True, test_mode=False)
    
    elif choice == "6":
        run_orchestration_test(load_to_neo4j=False, test_mode=True)
    
    elif choice == "7":
        run_orchestration_test(load_to_neo4j=True, test_mode=True)
    
    else:
        print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
