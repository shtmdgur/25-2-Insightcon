import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import asyncio

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

# 로깅 설정 (Streamlit에 맞게 조정 가능)
import logging
logging.basicConfig(level=logging.WARNING)

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Custom CSS for Hanwha Branding (Orange & Modern)
    st.markdown("""
        <style>
        /* [Typography] Drastically Reduce Header Sizes */
        .stMarkdown h1, h1 { font-size: 24px !important; line-height: 1.4 !important; }
        .stMarkdown h2, h2 { font-size: 20px !important; line-height: 1.3 !important; }
        .stMarkdown h3, h3 { font-size: 18px !important; line-height: 1.2 !important; }
        .stMarkdown h4, h4 { font-size: 16px !important; }
        
        /* Main Headers Color */
        h1, h2, h3 {
            color: #F37321 !important;
            font-family: 'Pretendard', sans-serif;
        }
        
        /* Top Decoration Bar */
        header[data-testid="stHeader"] {
            border-bottom: 5px solid #F37321;
        }

        /* Buttons (Hanwha Orange) */
        .stButton button {
            background-color: #F37321 !important;
            color: white !important;
            border: none !important;
            font-weight: bold !important;
            border-radius: 8px !important;
        }
        .stButton button:hover {
            background-color: #D95F12 !important;
        }
        
        /* [Box Layout] Bull & Bear Containers */
        .bull-container {
            background-color: #FFEBEE; /* More visible Light Red */
            border: 2px solid #FF8A80;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .bear-container {
            background-color: #E3F2FD; /* More visible Light Blue */
            border: 2px solid #90CAF9;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }

        /* Headers inside boxes */
        .bull-container h1, .bull-container h2, .bull-container h3 { color: #D32F2F !important; }
        .bear-container h1, .bear-container h2, .bear-container h3 { color: #1976D2 !important; }

        /* Judge Message (Existing style, but kept for consistency if not replaced) */
        .judge-message {
            background-color: #E8F5E9;
            border-left: 5px solid #4CAF50;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
        }

        /* Input Fields Focus Border */
        div[data-baseweb="input"] {
            border-color: #F37321 !important;
        }
        .stTextInput > div > div > input:focus {
            box-shadow: 0 0 0 1px #F37321 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            border-right: 3px solid #F37321;
        }
        section[data-testid="stSidebar"] h1 {
            color: #F37321 !important;
        }
        
        /* Metrics and Status */
        div[data-testid="stMetricValue"] {
            color: #F37321 !important;
        }
        div[data-testid="stStatusWidget"] {
            border: 1px solid #F37321 !important;
            background-color: #FFF5F0 !important;
        }
        
        /* Expander Header */
        .streamlit-expanderHeader {
            color: #333333 !important;
            border-left: 5px solid #F37321 !important;
            background-color: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)

def run_query_mode():
    st.header("🔍 투자 분석 (Query Only)")
    st.markdown("기존에 구축된 Knowledge Graph를 기반으로 토론 및 분석을 수행합니다.")

    with st.form("query_form"):
        user_input = st.text_input("분석 주제 (예: 삼성전자 HBM 전략)", placeholder="질문을 입력하세요.")
        
        col1, col2 = st.columns(2)
        with col1:
            target_date = st.date_input("분석 기준일", value=datetime.now())
        with col2:
            st.write("") # Spacer

        document_text = st.text_area("관련 문서 내용 (선택 사항)", height=150, placeholder="뉴스 기사나 보고서 내용을 여기에 붙여넣으세요.")
        uploaded_file = st.file_uploader("또는 파일 업로드 (TXT, MD)", type=["txt", "md"])

        submitted = st.form_submit_button("분석 시작 🚀")

    if submitted:
        if not user_input:
            st.error("분석 주제를 입력해주세요.")
            return

        # 문서 처리
        final_doc_text = None
        if uploaded_file is not None:
            final_doc_text = uploaded_file.read().decode("utf-8")
        elif document_text:
            final_doc_text = document_text

        
        # 워크플로우 실행
        status_box = st.status("🕵️ 에이전트가 분석 중입니다...", expanded=True)
        debate_container = st.container() # 토론 내용이 실시간으로 쌓일 공간
        
        # Markdown 렌더링 헬퍼 함수
        import markdown
        def render_bubble(role, text):
            html_content = markdown.markdown(text, extensions=['tables'])
            if role == "Bull":
                return f"""
                <div class="bull-container">
                    <div style="font-weight:bold; font-size:1.2rem; color:#D32F2F; margin-bottom:10px; border-bottom:1px solid #FFCDD2; padding-bottom:5px;">
                        🐂 Bull Agent
                    </div>
                    {html_content}
                </div>
                """
            elif role == "Bear":
                return f"""
                <div class="bear-container">
                    <div style="font-weight:bold; font-size:1.2rem; color:#1976D2; margin-bottom:10px; border-bottom:1px solid #BBDEFB; padding-bottom:5px; text-align:right;">
                        🐻 Bear Agent
                    </div>
                    {html_content}
                </div>
                """
            return text

        try:
            from src.pipeline.debate_workflow import create_debate_workflow_for_studio
            graph = create_debate_workflow_for_studio()
            
            initial_state = {
                "query": user_input,
                "target_date": str(target_date),
                "document": final_doc_text,
                "retry_count": 0,
                "errors": [],
                "execution_trace": []
            }

            final_report = None
            validation_result = None
            judge_verdict = None

            status_box.write("⚙️ 워크플로우 초기화 완료")
            
            # 스트리밍 실행
            for event in graph.stream(initial_state, stream_mode="updates"):
                for node_name, output in event.items():
                    # 상태 업데이트 및 실시간 토론 시각화
                    if node_name == "initialize": # initialize_debate 함수 이름과 매칭 주의 (보통 노드이름을 씀)
                        # graph 정의에서 initialize 노드 이름 확인
                        status_box.write("✅ 쿼리/문서 분석 및 초기화 완료")
                        
                    elif node_name == "bull":
                        status_box.write("🔴 Bull 에이전트 의견 완료")
                        debate_state = output["debate_state"]
                        arg_preview = debate_state["current_bull_arg"]
                        
                        with debate_container:
                            st.markdown(render_bubble("Bull", arg_preview), unsafe_allow_html=True)
                                
                    elif node_name == "bear":
                        status_box.write("🔵 Bear 에이전트 의견 완료")
                        debate_state = output["debate_state"]
                        arg_preview = debate_state["current_bear_arg"]
                        
                        with debate_container:
                            st.markdown(render_bubble("Bear", arg_preview), unsafe_allow_html=True)

                    elif node_name == "judge":
                        status_box.write("⚖️ 판결 완료")
                        if "debate_state" in output:
                            judge_verdict = output["debate_state"].get("judge_verdict")
                            # [安全_FIX] judge_verdict가 None일 경우 처리
                            if judge_verdict:
                                with debate_container:
                                    with st.chat_message("Judge", avatar="⚖️"):
                                        st.markdown(f"### 🧑‍⚖️ 최종 판결: {judge_verdict.get('decision', 'N/A')}")
                                        st.info(judge_verdict.get('rationale', ''))
                            else:
                                status_box.warning("⚠️ 판결 데이터를 생성하지 못했습니다.")
                                    
                    elif node_name == "synthesizer":
                        status_box.write("📝 최종 리포트 작성 중...")
                        if "final_report" in output:
                            final_report = output["final_report"]
                            
                    elif node_name == "validator":
                        if "debate_state" in output:
                            validation_result = output["debate_state"].get("validation_result")
                            if validation_result:
                                decision = validation_result.get('decision', 'N/A')
                                status_box.write(f"✅ 검증 완료: {decision}")

            status_box.update(label="분석이 완료되었습니다!", state="complete", expanded=False)

            # 결과 출력
            st.divider()
            
            # Judge 결과 시각화
            if judge_verdict:
                st.subheader("📢 판결 결과")
                col_j1, col_j2, col_j3 = st.columns(3)
                col_j1.metric("판결 (Decision)", judge_verdict.get('decision', 'N/A'))
                col_j2.metric("점수 (Score)", f"{judge_verdict.get('score', 0)}/100")
                col_j3.metric("신뢰도 (Confidence)", judge_verdict.get('confidence', 'N/A'))
                
                with st.expander("판결 상세 사유 (Rationale)"):
                    st.write(judge_verdict.get('rationale', '내용 없음'))

            # 최종 리포트 (이미지 포함 렌더링)
            if final_report:
                st.subheader("📊 최종 투자 분석 리포트")
                
                # 이미지 경로 처리 함수 (Local Images -> Base64)
                import base64
                import re
                
                def replace_images_with_base64(markdown_text):
                    def repl(match):
                        alt = match.group(1)
                        path = match.group(2)
                        # 경로에서 파일명 추출 (상대 경로 무시 및 charts 폴더 탐색)
                        filename = Path(path).name
                        # 차트 저장 경로 예상 (data/outputs/charts 또는 현재 디렉토리 등)
                        # Synthesizer가 data/outputs/charts에 저장한다고 가정
                        possible_paths = [
                            PROJECT_ROOT / "data" / "outputs" / "charts" / filename,
                            PROJECT_ROOT / "charts" / filename,
                            Path(path)
                        ]
                        
                        target_path = None
                        for p in possible_paths:
                            if p.exists():
                                target_path = p
                                break
                        
                        if target_path:
                            try:
                                img_bytes = target_path.read_bytes()
                                encoded = base64.b64encode(img_bytes).decode()
                                # 확장자 판별
                                ext = target_path.suffix.lower().replace(".", "")
                                mime = f"image/{ext}" if ext else "image/png"
                                return f'![{alt}](data:{mime};base64,{encoded})'
                            except Exception as e:
                                print(f"이미지 변환 실패: {e}")
                                return match.group(0)
                        return match.group(0)

                    return re.sub(r'!\[(.*?)\]\((.*?)\)', repl, markdown_text)

                # 리포트 내 이미지 링크 변환
                processed_report = replace_images_with_base64(final_report)
                st.markdown(processed_report, unsafe_allow_html=True)
                
                # 다운로드 버튼
                st.download_button(
                    label="리포트 다운로드 (Markdown)",
                    data=final_report, # 다운로드는 원본(경로 포함) 유지
                    file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            else:
                st.error("리포트 생성에 실패했습니다.")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
            import traceback
            st.code(traceback.format_exc())

    # Stop Button (Sidebar)
    with st.sidebar:
        st.divider()
        if st.button("🛑 실행 중단 (Stop)", type="primary"):
            st.stop()

def run_rebuild_kg_mode():
    st.header("🔄 KG 재구축 (Rebuild KG)")
    st.markdown("`data/processed` 폴더의 JSON 파일들을 Neo4j에 다시 주입합니다.")

    if st.button("KG 데이터 주입 시작"):
        output_container = st.container()
        with output_container:
            with st.spinner("데이터 주입 중..."):
                try:
                    # 기존 로직 import 및 실행을 함수로 래핑하여 로그 캡처
                    # 여기서는 간단히 로직을 직접 구현하거나 run.py의 함수를 import해서 쓸 수도 있음
                    # 하지만 streamlit에 로그를 찍으려면 직접 구현이 나음
                    
                    from src.dataflows.kg_merger import KGMerger
                    from src.dataflows.neo4j_loader import Neo4jKGLoader
                    from src.models.nodes import KnowledgeGraph
                    
                    processed_dir = PROJECT_ROOT / "data" / "processed"
                    json_files = list(processed_dir.glob("**/*_kg.json"))
                    
                    if not json_files:
                        st.warning("⚠️ data/processed에 JSON 파일이 없습니다.")
                        return
                    
                    st.info(f"📂 {len(json_files)}개의 JSON 파일을 발견했습니다.")
                    
                    merger = KGMerger()
                    kgs = []
                    progress_bar = st.progress(0)
                    
                    for i, jf in enumerate(json_files):
                        try:
                            kg = KnowledgeGraph.load_from_json(str(jf))
                            kgs.append(kg)
                        except Exception as e:
                            st.error(f"⚠️ {jf.name} 로드 실패: {e}")
                        progress_bar.progress((i + 1) / len(json_files))
                    
                    if not kgs:
                        st.error("❌ 로드된 KG가 없습니다.")
                        return

                    st.write("데이터 병합 중...")
                    merged_kg = merger.merge_knowledge_graphs(kgs)
                    st.success(f"✅ 병합 완료: Entities {len(merged_kg.entities)}, Relations {len(merged_kg.relations)}")
                    
                    st.write("Neo4j에 업로드 중...")
                    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
                    
                    loader = Neo4jKGLoader(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
                    stats = loader.load_knowledge_graph(merged_kg)
                    loader.close()
                    
                    st.success(f"✅ Neo4j 주입 완료: Static Nodes {stats.get('static_nodes', 0)}, Dynamic Nodes {stats.get('dynamic_nodes', 0)}")

                except Exception as e:
                    st.error(f"작업 실패: {e}")

def run_full_pipeline_mode():
    st.header("🚀 전체 파이프라인 (Full E2E)")
    st.markdown("PDF/뉴스 원본 데이터 파싱부터 KG 구축, Debate까지 수행합니다.")
    
    test_mode = st.checkbox("테스트 모드 (소량 데이터만 처리)", value=True)
    
    if st.button("파이프라인 실행"):
        st.info("이 작업은 시간이 오래 걸릴 수 있습니다.")
        
        with st.status("KG 구축 진행 중...", expanded=True) as status:
            try:
                from src.agents.kg_construction import KGConstructionAgent
                from langchain_google_genai import ChatGoogleGenerativeAI
                from src.config.llm_config import get_model
                
                # 설정 업데이트 (테스트 모드 시)
                if test_mode:
                    from src.config.parser_config import update_config
                    update_config('news', sample_size=5)
                    status.write("🧪 테스트 모드 설정 적용됨")

                llm = ChatGoogleGenerativeAI(model=get_model("news_parsing"))
                agent = KGConstructionAgent(
                    data_dir=PROJECT_ROOT / "data",
                    neo4j_uri=os.getenv("NEO4J_URI"),
                    llm=llm
                )
                
                status.write("데이터 파싱 및 KG 생성 시작...")
                # Streamlit에서 오래 걸리는 작업을 실행할 때 스피너나 프로그레스가 필요하지만
                # agent 내부 로직을 뜯어고치지 않는 한 여기서 대기해야 함.
                result = agent.construct_knowledge_graph(
                    auto_scan=True,
                    use_batch=False,
                    load_to_neo4j=True,
                    skip_existing=True
                )
                
                status.update(label="KG 구축 완료!", state="complete", expanded=False)
                
                if result.get('merged_kg'):
                    st.success(f"KG 구축 성공! (Entities: {len(result['merged_kg'].entities)})")
                    st.balloons()
                
            except Exception as e:
                status.update(label="KG 구축 실패", state="error")
                st.error(f"오류: {e}")

def main():
    st.set_page_config(
        page_title="Insightcon 투자 분석 에이전트",
        page_icon="📈",
        layout="wide"
    )

    st.title("📈 Insightcon AI Agent")
    
    with st.sidebar:
        st.title("메뉴 (Menu)")
        mode = st.radio(
            "실행 모드 선택",
            ["Query Only", "Rebuild KG", "Full Pipeline"],
            index=0,
            captions=[
                "기존 데이터로 토론/분석만 수행합니다.",
                "저장된 JSON 데이터를 Neo4j에 다시 넣습니다.",
                "문서 파싱부터 전체 과정을 실행합니다."
            ]
        )
        st.markdown("---")
        st.info("제작: Insight 25-2 Insightcon Team")

    if mode == "Query Only":
        run_query_mode()
    elif mode == "Rebuild KG":
        run_rebuild_kg_mode()
    elif mode == "Full Pipeline":
        run_full_pipeline_mode()

if __name__ == "__main__":
    main()
