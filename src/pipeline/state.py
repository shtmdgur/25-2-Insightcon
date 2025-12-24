"""
리포트 생성 워크플로우의 상태 정의
"""
import operator
from typing import TypedDict, List, Dict, Optional, Annotated, Literal, Any


class DebateState(TypedDict):
    """변증법 토론 상태 (TradingAgents InvestDebateState 참고)"""
    
    # 토론 이력
    bull_history: str  # Bull 주장 누적 (Markdown)
    bear_history: str  # Bear 주장 누적
    full_history: str  # 전체 토론 흐름 (타임라인)
    
    # 현재 라운드
    current_bull_arg: Optional[str]  # 현재 라운드 Bull 주장
    current_bear_arg: Optional[str]  # 현재 라운드 Bear 주장
    
    # 제어
    debate_count: int  # 토론 라운드 (max 3)
    should_continue: bool  # 토론 계속 여부
    
    # Progressive Path Expansion 캐시
    cached_paths: Optional[Dict[int, List[Dict]]]  # {round_num: [paths]}
    
    # Debate 전용 실행 추적 (병렬 문제 없음)
    debate_trace: Optional[List[str]]  # Debate workflow 내부 trace

    # 신규 분석 결과 (Judge, Validator)
    judge_result: Optional[Dict[str, Any]]  # Judge의 판결 (decision, score 등)
    validation_result: Optional[Dict[str, Any]]  # Validator의 검증 결과 (pass/fail)


class ReportState(TypedDict):
    """리포트 생성 워크플로우의 중앙 상태 객체"""
    
    # ========================================
    # 1. 입력 필드 (사용자 입력)
    # ========================================
    query: str  # 사용자 질의
    ticker: Optional[str]  # 분석 대상 종목 코드 (e.g., "005930")
    target_companies: Optional[List[str]]  # 분석 대상 기업 목록
    target_date: Optional[str]  # 분석 기준 날짜 (YYYY-MM-DD, Price DB 조회용)
    document: Optional[str]  # 새로 처리할 문서 (파일 경로 또는 텍스트)
    impact_paths: Optional[List[str]]  # Debate Agent가 사용할 Impact Paths (prompts.yaml 호환)
    
    # ========================================
    # 2. Parser 결과 (Phase 0)
    # ========================================
    parsed_text: Optional[str]  # PDF 파싱 결과 텍스트
    file_uri: Optional[str]  # Gemini Files API URI
    extracted_charts: Optional[List[Dict]]  # VLM이 분석한 차트 정보
    
    # ========================================
    # 3. 온톨로지 및 Knowledge Graph (Phase 1)
    # ========================================
    ontology_schema: Optional[Dict]  # 생성된 온톨로지 스키마
    schema_issues: Optional[List[str]]  # 스키마 문제 목록
    kg_data: Optional[Dict]  # Neo4j에서 가져온 지식 그래프 데이터
    kg_updates: Annotated[List[Dict], operator.add]  # 새로 생성된 노드/엣지 (Reducer)
    
    # ========================================
    # 4. GraphRAG 검색 결과
    # ========================================
    graphrag_results: Optional[Dict[str, Any]]  # GraphRAG 검색 결과
    news_events: Optional[List[Dict]]  # 관련 뉴스 이벤트
    
    # ========================================
    # 5. Analyst 분석 결과 (Phase 2 - Parallel)
    # ========================================
    fundamental_analysis: Optional[str]  # 재무 분석 결과
    trend_analysis: Optional[str]  # 트렌드(SAX-DM) 분석 결과
    event_analysis: Optional[str]  # 이벤트 임팩트 분석 결과
    analyst_reports: Optional[Dict[str, str]]  # 통합된 Analyst 리포트 (확장성 고려)
    
    # ========================================
    # 6. Debate 에이전트 결과 (Phase 2 - Sequential)
    # ========================================
    debate_state: Optional[DebateState]  # 토론 상태 (통합 관리)
    synthesis_report: Optional[str]  # Synthesizer 최종 리포트 및 판단
    
    # ========================================
    # 7. 분석 결과 (기존 필드 유지)
    # ========================================
    sector_analysis: Optional[str]  # 섹터 분석 결과
    company_analysis: Optional[Dict[str, str]]  # 종목별 분석 결과 (기업명: 분석결과)
    
    # ========================================
    # 8. 최종 출력
    # ========================================
    final_report: Optional[str]  # 최종 생성된 리포트
    
    # ========================================
    # 9. 메타데이터 및 제어
    # ========================================
    retry_count: int  # 재시도 횟수 (Infinite Loop 방지)
    critical_paths: Optional[List[str]]  # 근거로 사용된 핵심 경로 (Provenance)
    
    errors: Annotated[List[str], operator.add]  # 에러 목록 (병렬 노드에서 추가 가능)
    execution_trace: Annotated[List[str], operator.add]  # 실행 추적 로그 (병렬 안전)
    execution_times: Annotated[List[Dict[str, float]], operator.add]  # 실행 시간 추적 (노드명: 소요시간)

