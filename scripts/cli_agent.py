import os
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가하여 모듈 로드 가능하게 함
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# .env 로드 (src 내부에서 할 수도 있지만 CLI 진입점에서 보장)
from dotenv import load_dotenv
load_dotenv()

import logging
# 로깅 설정을 초기에 하여 불필요한 로그 억제
logging.basicConfig(level=logging.WARNING)
logging.getLogger("src.dataflows.neo4j_loader").setLevel(logging.WARNING)
logging.getLogger("src.utils.entity_matcher").setLevel(logging.WARNING)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("neo4j.notifications").setLevel(logging.WARNING)

# FutureWarning 억제
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from src.pipeline.debate_workflow import create_debate_workflow_for_studio

def main():
    print("\n" + "="*50)
    print("🚀 Investment Debate Interactive CLI 시작")
    print("="*50)
    print("분석하고 싶은 주제나 기업명을 입력하세요. (예: 삼성전자 HBM 전략)")
    print("종료하려면 'q', 'exit', 'quit'을 입력하세요.")
    print("-" * 50)

    # 워크플로우 생성
    try:
        graph = create_debate_workflow_for_studio()
    except Exception as e:
        print(f"❌ 워크플로우 초기화 실패: {e}")
        return

    while True:
        try:
            print("\n" + "-"*50)
            user_input = input("🔍 투자 분석 요청 > ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 프로그램을 종료합니다. 감사합니다!")
                break
            
            if not user_input:
                continue

            # 1. 날짜 입력 (날짜는 1줄이므로 먼저 입력받아 Paste 버퍼 오염 방지)
            date_input = input(f"📅 분석 기준일 (엔터 시 자동) > ").strip()
            target_date = date_input if date_input else None

            # 2. 문서 입력 (경로 또는 멀티라인 텍스트)
            print("📄 첨부 문서 (파일 경로 입력 또는 텍스트 직접 입력)")
            print("   (직접 입력 시 마지막 줄에 'DONE' 또는 'EOF' 입력 시 종료, 없으면 엔터)")
            
            doc_input = None
            first_line = input(" > ").strip()
            
            if first_line:
                from pathlib import Path
                if Path(first_line).exists() and Path(first_line).is_file():
                    doc_path = first_line
                else:
                    # 멀티라인 입력 처리
                    lines = [first_line]
                    while True:
                        line = input(".. ")
                        if line.strip().upper() in ["DONE", "EOF"]:
                            break
                        # 엔터만 두 번 친 경우 종료하게 하고 싶다면 아래 조건 추가 가능
                        # if not line.strip() and lines[-1] == "": break
                        lines.append(line)
                    doc_path = "\n".join(lines)
            else:
                doc_path = None

            # 초기 상태 정의 (ReportState 형식)
            initial_state = {
                "query": user_input,
                "ticker": None,
                "target_companies": [],
                "target_date": target_date,
                "document": doc_path,
                "document_summary": None, # [NEW] 문서 분석 요약 필드
                "debate_state": None, # initialize 노드에서 생성
                "retry_count": 0,
                "errors": [],
                "execution_trace": []
            }

            msg = f" (기준일: {target_date})" if target_date else " (날짜 자동 추출/오늘)"
            print(f"\n🤖 분석을 시작합니다: '{user_input}'{msg}")
            print("데이터 조회 및 토론을 진행합니다. 잠시만 기다려 주세요...\n")
            
            # 스트리밍 실행 (노드 내부에 이미 print문이 있으므로 진행 상황이 터미널에 보임)
            final_report = None
            validation_result = None
            for event in graph.stream(initial_state, stream_mode="updates"):
                for node_name, output in event.items():
                    # synthesizer 노드가 완료되면 최종 리포트 저장
                    if node_name == "synthesizer" and "final_report" in output:
                        final_report = output["final_report"]
                    elif node_name == "validator" and "debate_state" in output:
                        validation_result = output["debate_state"].get("validation_result")
            
            if final_report:
                print("\n" + "✨" * 20)
                print("📊 분석 결과 요약")
                print("✨" * 20)
                # 리포트의 앞부분만 간단히 출력
                lines = final_report.split('\n')
                preview = "\n".join(lines[:15])
                print(preview)
                if len(lines) > 15:
                    print(f"\n... (총 {len(lines)}줄의 리포트가 생성되었습니다) ...")
                
                # Validator 결과 출력
                if validation_result:
                    print("\n" + "🔍" * 20)
                    print("✅ Quality Check 결과")
                    print("🔍" * 20)
                    print(f"   Status: {validation_result.get('decision', 'N/A').upper()}")
                    feedback = validation_result.get('feedback', '')
                    if feedback:
                        print(f"   Feedback: {feedback}")
                # 리포트 파일 저장
                output_dir = PROJECT_ROOT / "data" / "outputs" / "cli"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                import re
                safe_query = re.sub(r'[\\/*?:"<>|]', "", user_input)[:20].strip()
                filename = output_dir / f"report_{safe_query}_{timestamp}.md"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(final_report)
                
                print(f"\n💾 전체 리포트 저장 완료: {filename.relative_to(PROJECT_ROOT)}")
                print("   (마크다운 뷰어로 열면 차트가 예쁘게 그려집니다!)")
            else:
                print("\n⚠️ 리포트 생성에 실패했습니다. 로그를 확인해 주세요.")

        except KeyboardInterrupt:
            print("\n\n⚠️ 중단되었습니다. 메인 메뉴로 돌아갑니다. (종료는 'q' 입력)")
            continue
        except Exception as e:
            print(f"\n❌ 분석 도중 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
