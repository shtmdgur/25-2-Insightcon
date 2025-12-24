"""
Streamlit Demo App

PipelineService를 활용한 투자 분석 데모 앱

실행 방법:
    streamlit run app/streamlit_demo.py
"""

import streamlit as st
import os
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.services import PipelineService, PipelineConfig, PipelineMode, CheckpointData


def main():
    st.set_page_config(
        page_title="AI 투자 분석 시스템",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 AI 멀티에이전트 투자 분석 시스템")
    st.markdown("---")
    
    # Sidebar: 설정
    with st.sidebar:
        st.header("⚙️ 분석 설정")
        
        # 1. 모드 선택
        mode = st.selectbox(
            "분석 모드",
            options=["query_only", "full", "document_query"],
            format_func=lambda x: {
                "query_only": "🔍 기존 KG로 분석",
                "full": "🔄 KG 구축 + 분석",
                "document_query": "📄 새 문서 + 기존 KG"
            }.get(x, x)
        )
        
        st.info({
            "query_only": "이미 구축된 Knowledge Graph를 사용하여 분석합니다.",
            "full": "데이터 파싱부터 시작하여 KG를 구축하고 분석합니다.",
            "document_query": "새 문서를 파싱하여 기존 KG에 추가한 후 분석합니다."
        }.get(mode, ""))
        
        # 2. 타겟 기업
        target_company = st.text_input("분석 대상 기업", value="삼성전자")
        
        # 3. 문서 업로드 (document_query 모드)
        document_path = None
        if mode == "document_query":
            uploaded_file = st.file_uploader("PDF 문서 업로드", type=["pdf"])
            if uploaded_file:
                # 임시 저장
                temp_path = Path("data/temp") / uploaded_file.name
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())
                document_path = str(temp_path)
                st.success(f"✅ 파일 업로드 완료: {uploaded_file.name}")
        
        # 4. 고급 설정
        with st.expander("고급 설정"):
            test_mode = st.checkbox("테스트 모드 (소량 데이터)", value=True)
            max_rounds = st.slider("토론 라운드 수", 1, 5, 3)
        
        # 5. 실행 버튼
        run_button = st.button("🚀 분석 시작", type="primary", use_container_width=True)
    
    # Main: 결과 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 분석 리포트")
        report_placeholder = st.empty()
    
    with col2:
        st.header("📊 진행 상태")
        status_placeholder = st.empty()
        progress_bar = st.progress(0)
    
    # 실행
    if run_button:
        service = PipelineService()
        
        config = service.create_config(
            mode=mode,
            target_company=target_company,
            document_path=document_path,
            test_mode=test_mode,
            max_debate_rounds=max_rounds
        )
        
        # Checkpoint 핸들러
        checkpoints = []
        def on_checkpoint(cp: CheckpointData):
            checkpoints.append(cp)
            
            # 진행률 업데이트
            progress_map = {
                "mode_selection": 0.1,
                "target_selection": 0.2,
                "kg_complete": 0.4,
                "debate_round": 0.6,
                "judge_result": 0.8,
                "final_report": 1.0
            }
            progress = progress_map.get(cp.checkpoint_type.value, 0.5)
            progress_bar.progress(progress)
            
            # 상태 표시
            status_placeholder.markdown(f"""
            **현재 단계**: {cp.checkpoint_type.value}
            
            {cp.message}
            
            ---
            **지난 체크포인트**:
            """ + "\n".join([f"- {c.message}" for c in checkpoints[-5:]]))
        
        # 실행
        with st.spinner("분석 중..."):
            result = service.run(config, on_checkpoint=on_checkpoint)
        
        # 결과 표시
        if result.success:
            st.balloons()
            
            # 리포트 표시
            if result.final_report_content:
                report_placeholder.markdown(result.final_report_content)
            else:
                report_placeholder.warning("리포트 생성에 실패했습니다.")
            
            # 요약 정보
            st.sidebar.success(f"""
            ✅ **분석 완료**
            
            - 판결: **{result.judge_decision or 'N/A'}**
            - 점수: {result.judge_score or 'N/A'}/100
            - 토론 라운드: {result.debate_rounds}회
            - 소요 시간: {result.duration_seconds:.1f}초
            """)
        else:
            st.error(f"❌ 분석 실패: {', '.join(result.errors)}")


if __name__ == "__main__":
    main()
