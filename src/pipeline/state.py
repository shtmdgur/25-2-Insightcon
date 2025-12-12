"""
리포트 생성 워크플로우의 상태 정의
"""
import operator
from typing import TypedDict, List, Dict, Optional, Annotated


class ReportState(TypedDict):
    """리포트 생성 워크플로우의 중앙 상태 객체"""
    
    # 입력 필드
    query: str  # 사용자 질의
    target_companies: Optional[List[str]]  # 분석 대상 기업 목록
    report_type: str  # "sector" | "company" | "all"
    document: Optional[str]  # 새로 처리할 문서 (그래프 구축용)
    
    # 온톨로지 관련
    ontology_schema: Optional[Dict]  # 생성된 온톨로지 스키마
    schema_issues: Optional[List[str]]  # 스키마 문제 목록
    
    # 중간 결과
    kg_data: Optional[Dict]  # Neo4j에서 가져온 지식 그래프 데이터
    graphrag_results: Optional[Dict]  # GraphRAG 검색 결과
    
    # 분석 결과 (병렬 실행 결과)
    sector_analysis: Optional[str]  # 섹터 분석 결과
    company_analysis: Optional[Dict[str, str]]  # 종목별 분석 결과 (기업명: 분석결과)
    
    # 최종 출력
    final_report: Optional[str]  # 최종 생성된 리포트
    
    # 메타데이터 (병렬 실행 시 reducer 필요)
    errors: Annotated[List[str], operator.add]  # 에러 목록 (병렬 노드에서 추가 가능)
    execution_trace: Annotated[List[str], operator.add]  # 실행 추적 로그 (병렬 노드에서 추가 가능)
    execution_times: Annotated[List[Dict[str, float]], operator.add]  # 실행 시간 추적 (노드명: 소요시간)
