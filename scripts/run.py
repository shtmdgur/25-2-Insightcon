"""
투자 분석 통합 CLI (E2E Pipeline)

사용자가 모드를 선택하여 KG 구축부터 Debate까지 원하는대로 실행할 수 있습니다.

모드:
1. 🔍 Query Only: 기존 KG를 활용하여 Debate만 실행
2. 🔄 Rebuild KG: JSON 파일들을 Neo4j에 재주입 후 Debate 실행  
3. 🚀 Full Pipeline: 원본 데이터(PDF/뉴스)부터 KG 구축 후 Debate 실행
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


def print_banner(text: str):
    """배너 출력"""
    print("\n" + "=" * 60)
    print(f"🚀 {text}")
    print("=" * 60 + "\n")


def print_section(text: str):
    """섹션 헤더 출력"""
    print("\n" + "-" * 50)
    print(f"📌 {text}")
    print("-" * 50)


def show_mode_selection() -> str:
    """모드 선택 UI"""
    print("\n" + "=" * 60)
    print("📊 투자 분석 에이전트 - 모드 선택")
    print("=" * 60)
    print("""
    [1] 🔍 Query Only (빠른 분석)
        → 기존 Neo4j 데이터를 활용하여 Debate만 실행
        → 가장 빠름, KG가 이미 구축되어 있어야 함

    [2] 🔄 Rebuild KG (JSON 재주입)
        → data/processed/*.json 파일들을 Neo4j에 주입 후 Debate
        → KG 데이터 갱신이 필요할 때 사용

    [3] 🚀 Full E2E Pipeline (전체 구축)
        → 원본 데이터(PDF, 뉴스 CSV)부터 파싱 → KG 구축 → Debate
        → 가장 오래 걸림, 처음 실행 시 사용

    [q] 종료
    """)
    
    while True:
        choice = input("모드를 선택하세요 (1/2/3/q): ").strip().lower()
        if choice in ['1', '2', '3', 'q', 'quit', 'exit']:
            return choice
        print("⚠️ 1, 2, 3 또는 q를 입력하세요.")


def run_kg_construction(test_mode: bool = True):
    """Phase 1: KG 구축 (PDF/뉴스 파싱 → Neo4j)"""
    print_section("Phase 1: Knowledge Graph Construction")
    
    from src.agents.kg_construction import KGConstructionAgent
    from langchain_google_genai import ChatGoogleGenerativeAI
    from src.config.llm_config import get_model
    
    try:
        llm = ChatGoogleGenerativeAI(model=get_model("news_parsing"))
        
        agent = KGConstructionAgent(
            data_dir=PROJECT_ROOT / "data",
            neo4j_uri=os.getenv("NEO4J_URI"),
            llm=llm
        )
        
        if test_mode:
            from src.config.parser_config import update_config
            update_config('news', sample_size=5)
            print("🧪 테스트 모드: 소량 데이터만 처리")
        
        result = agent.construct_knowledge_graph(
            auto_scan=True,
            use_batch=False,
            load_to_neo4j=True,
            skip_existing=True
        )
        
        print(f"✅ KG Construction 완료")
        if result.get('merged_kg'):
            print(f"   - Entities: {len(result['merged_kg'].entities)}")
            print(f"   - Relations: {len(result['merged_kg'].relations)}")
        
        return True
        
    except Exception as e:
        print(f"❌ KG Construction 실패: {e}")
        return False


def run_json_injection():
    """Phase 1.5: 기존 JSON → Neo4j 주입"""
    print_section("Phase 1.5: JSON Merge & Neo4j Injection")
    
    try:
        from src.dataflows.kg_merger import KGMerger
        from src.dataflows.neo4j_loader import Neo4jKGLoader
        from src.models.nodes import KnowledgeGraph
        
        processed_dir = PROJECT_ROOT / "data" / "processed"
        
        # 로더 로깅 활성화 (진행상황 확인용)
        logging.getLogger("src.dataflows.neo4j_loader").setLevel(logging.INFO)

        json_files = list(processed_dir.glob("**/*_kg.json"))
        
        if not json_files:
            print("⚠️ data/processed에 JSON 파일이 없습니다.")
            return False
        
        print(f"📂 {len(json_files)} JSON 파일 발견")
        
        # 머지
        merger = KGMerger()
        kgs = []
        for i, jf in enumerate(json_files, 1):
            print(f"   [{i}/{len(json_files)}] Loading {jf.name}...", end='\r')
            try:
                kg = KnowledgeGraph.load_from_json(str(jf))
                kgs.append(kg)
            except Exception as e:
                print(f"   ⚠️ {jf.name} 로드 실패: {e}")
        
        if not kgs:
            print("❌ 로드된 KG가 없습니다.")
            return False
        
        merged_kg = merger.merge_knowledge_graphs(kgs)
        print(f"   - Merged: {len(merged_kg.entities)} entities, {len(merged_kg.relations)} relations")
        
        # Neo4j 주입
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        loader = Neo4jKGLoader(
            uri=neo4j_uri, 
            user=neo4j_user, 
            password=neo4j_password,
            batch_size=500  # 안정성을 위해 배치 크기 축소 (1000 -> 500)
        )
        stats = loader.load_knowledge_graph(merged_kg)
        
        print(f"✅ Neo4j 주입 완료: {stats.get('static_nodes', 0)} static, {stats.get('dynamic_nodes', 0)} dynamic nodes")
        
        # 품질 검사 및 자동 수정
        print("\n🔍 품질 검사 및 자동 수정 중...")
        try:
            from src.agents.quality_check import QualityCheckAgent
            from src.utils.neo4j_client import Neo4jClient
            
            neo4j_client = Neo4jClient(neo4j_uri, neo4j_user, neo4j_password)
            quality_agent = QualityCheckAgent(neo4j_client)
            
            fix_result = quality_agent.check_and_fix()
            
            if fix_result['status'] == 'clean':
                print("✅ 품질 검사 통과 - 문제 없음")
            elif fix_result['status'] == 'fixed':
                print(f"🔧 {fix_result['message']}")
            else:
                print(f"⚠️ {fix_result['message']}")
                for issue in fix_result.get('remaining_issues', [])[:5]:
                    print(f"   - {issue.get('message', issue)}")
            
            neo4j_client.close()
        except Exception as qe:
            print(f"⚠️ 품질 검사 스킵: {qe}")
        
        loader.close()
        return True
        
    except Exception as e:
        print(f"❌ JSON 주입 실패: {e}")
        return False


def run_debate_interactive():
    """메인 Debate 인터랙티브 루프"""
    from src.pipeline.debate_workflow import create_debate_workflow_for_studio
    
    try:
        graph = create_debate_workflow_for_studio()
    except Exception as e:
        print(f"❌ 워크플로우 초기화 실패: {e}")
        return
    
    print("\n" + "-" * 50)
    print("🎯 분석하고 싶은 주제나 기업명을 입력하세요.")
    print("   예: '삼성전자 HBM 전략', 'SK하이닉스와 한미반도체 관계 분석'")
    print("   종료하려면 'q' 또는 'back' 입력")
    print("-" * 50)
    
    while True:
        try:
            print("\n" + "-" * 50)
            user_input = input("🔍 투자 분석 요청 > ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q', 'back']:
                print("👋 메인 메뉴로 돌아갑니다.")
                break
            
            if not user_input:
                continue
            
            # 날짜 입력
            date_input = input("📅 분석 기준일 (엔터 시 자동) > ").strip()
            target_date = date_input if date_input else None
            
            # 문서 입력
            print("📄 첨부 문서 (파일 경로 또는 텍스트 직접 입력, 없으면 엔터)")
            first_line = input(" > ").strip()
            
            doc_path = None
            if first_line:
                if Path(first_line).exists() and Path(first_line).is_file():
                    doc_path = first_line
                else:
                    lines = [first_line]
                    print("   (멀티라인 입력 시 'DONE' 또는 'EOF'로 종료)")
                    while True:
                        line = input(".. ")
                        if line.strip().upper() in ["DONE", "EOF"]:
                            break
                        lines.append(line)
                    doc_path = "\n".join(lines)
            
            # 초기 상태
            initial_state = {
                "query": user_input,
                "ticker": None,
                "target_companies": [],
                "target_date": target_date,
                "document": doc_path,
                "document_summary": None,
                "debate_state": None,
                "retry_count": 0,
                "errors": [],
                "execution_trace": []
            }
            
            msg = f" (기준일: {target_date})" if target_date else " (날짜 자동)"
            print(f"\n🤖 분석을 시작합니다: '{user_input}'{msg}")
            print("데이터 조회 및 토론을 진행합니다. 잠시만 기다려 주세요...\n")
            
            # 워크플로우 실행
            final_report = None
            validation_result = None
            judge_verdict = None  # [NEW] Judge 판결 결과 캡처
            
            for event in graph.stream(initial_state, stream_mode="updates"):
                for node_name, output in event.items():
                    if node_name == "synthesizer" and "final_report" in output:
                        final_report = output["final_report"]
                    elif node_name == "validator" and "debate_state" in output:
                        validation_result = output["debate_state"].get("validation_result")
                    elif node_name == "judge" and "debate_state" in output:
                        # [NEW] Judge 판결 결과 캡처
                        judge_verdict = output["debate_state"].get("judge_verdict")
            
            # [NEW] Judge 판결 결과 전체 출력
            if judge_verdict:
                print("\n" + "=" * 60)
                print("📢 [Judge 판결 결과]")
                print("=" * 60)
                print(f"   📌 Decision: {judge_verdict.get('decision', 'N/A')}")
                print(f"   📊 Score: {judge_verdict.get('score', 'N/A')}/100")
                print(f"   💪 Confidence: {judge_verdict.get('confidence', 'N/A')}")
                print(f"   🏆 Winning Side: {judge_verdict.get('winning_side', 'N/A')}")
                print(f"\n   📋 Rationale (판결 이유):")
                rationale = judge_verdict.get('rationale', '판결 이유 없음')
                # 긴 rationale을 보기 좋게 줄바꿈
                for line in rationale.split('. '):
                    print(f"      {line.strip()}.")
                print("=" * 60)
            
            if final_report:
                print("\n" + "✨" * 20)
                print("📊 분석 결과 요약")
                print("✨" * 20)
                
                lines = final_report.split('\n')
                preview = "\n".join(lines[:15])
                print(preview)
                if len(lines) > 15:
                    print(f"\n... (총 {len(lines)}줄의 리포트가 생성되었습니다) ...")
                
                # Validator 결과
                if validation_result:
                    print(f"\n✅ Quality Check: {validation_result.get('decision', 'N/A').upper()}")
                
                # 파일 저장
                output_dir = PROJECT_ROOT / "data" / "outputs" / "cli"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                import re
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_query = re.sub(r'[\\/*?:"<>|]', "", user_input)[:20].strip()
                filename = output_dir / f"report_{safe_query}_{timestamp}.md"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(final_report)
                
                print(f"\n💾 리포트 저장: {filename.relative_to(PROJECT_ROOT)}")
                    
            else:
                print("⚠️ 리포트 생성에 실패했습니다.")
                
        except KeyboardInterrupt:
            print("\n\n⚠️ 중단되었습니다.")
            continue
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 진입점"""
    print_banner("투자 분석 통합 에이전트 (E2E Pipeline)")
    
    while True:
        mode = show_mode_selection()
        
        if mode in ['q', 'quit', 'exit']:
            print("\n👋 에이전트를 종료합니다. 안녕 ~")
            break
        
        elif mode == '1':
            # Query Only - 바로 Debate
            print_section("Mode 1: Query Only (기존 KG 활용)")
            run_debate_interactive()
        
        elif mode == '2':
            # Rebuild KG - JSON 주입 후 Debate
            print_section("Mode 2: Rebuild KG (JSON 재주입)")
            success = run_json_injection()
            if success:
                run_debate_interactive()
            else:
                print("⚠️ KG 주입에 실패했습니다. 모드 선택으로 돌아갑니다.")
        
        elif mode == '3':
            # Full E2E - 전체 파이프라인
            print_section("Mode 3: Full E2E Pipeline")
            
            test_mode_input = input("🧪 테스트 모드로 실행할까요? (y/n, 기본: y): ").strip().lower()
            test_mode = test_mode_input != 'n'
            
            success = run_kg_construction(test_mode=test_mode)
            if success:
                run_debate_interactive()
            else:
                print("⚠️ KG 구축에 실패했습니다. 모드 선택으로 돌아갑니다.")


if __name__ == "__main__":
    main()
