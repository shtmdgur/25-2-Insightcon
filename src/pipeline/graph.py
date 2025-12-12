"""
LangGraph 워크플로우 그래프 생성
"""
import time
import json
from pathlib import Path
from typing import List
from langgraph.graph import StateGraph, END

# 로그 파일 경로 설정
_DEBUG_LOG_PATH = Path(__file__).parent.parent.parent.parent / ".cursor" / "debug.log"
_DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

from .state import ReportState
from .nodes import (
    kg_construction_node,
    quality_check_node,
    ontology_architect_node,
    graphrag_query_node,
    sector_analyst_node,
    company_analyst_node,
    report_generation_node
)


def route_after_quality_check(state: ReportState) -> str:
    """
    Quality Check 후 라우팅 결정
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        다음 노드 이름
    """
    # 스키마 이슈가 있으면 Ontology Architect로
    schema_issues = state.get('schema_issues', [])
    if schema_issues:
        return "ontology_architect"
    
    # 문제 없으면 GraphRAG Query로
    return "graphrag_query"


def route_to_analysts(state: ReportState) -> List[str]:
    """
    리포트 타입에 따라 분석 에이전트 선택 (병렬 실행)
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        실행할 노드 이름 리스트
    """
    # #region agent log
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"graph.py:route_to_analysts","message":"Function entry","data":{"report_type":state.get("report_type"),"target_companies":state.get("target_companies")},"timestamp":int(time.time()*1000)}) + "\n")
    except Exception:
        pass
    # #endregion agent log
    
    report_type = state.get("report_type", "sector")
    nodes = []
    
    if report_type in ["sector", "all"]:
        nodes.append("sector_analyst")
    
    if report_type in ["company", "all"]:
        nodes.append("company_analyst")
    
    # 기본값: sector_analyst
    if not nodes:
        nodes.append("sector_analyst")
    
    # #region agent log
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"graph.py:route_to_analysts","message":"Function exit","data":{"returned_nodes":nodes,"nodes_count":len(nodes)},"timestamp":int(time.time()*1000)}) + "\n")
    except Exception:
        pass
    # #endregion agent log
    
    return nodes


def create_workflow() -> StateGraph:
    """
    LangGraph 워크플로우 그래프 생성
    
    스마트 워크플로우: document가 있으면 그래프 구축을 실행하고,
    없으면 자동으로 스킵하여 질의 처리만 수행합니다.
    
    Returns:
        StateGraph 객체 (컴파일 전)
    """
    # 상태 그래프 생성
    workflow = StateGraph(ReportState)
    
    # 1. 온톨로지·그래프 관리 노드 추가
    workflow.add_node("kg_construction", kg_construction_node)
    workflow.add_node("quality_check", quality_check_node)
    workflow.add_node("ontology_architect", ontology_architect_node)
    
    # 2. GraphRAG 검색 노드 추가
    workflow.add_node("graphrag_query", graphrag_query_node)
    
    # 3. 분석 에이전트 노드 추가 (병렬 실행)
    workflow.add_node("sector_analyst", sector_analyst_node)
    workflow.add_node("company_analyst", company_analyst_node)
    
    # 4. 리포트 생성 노드 추가
    workflow.add_node("report_generation", report_generation_node)
    
    # 엣지 연결
    # Entry point
    workflow.set_entry_point("kg_construction")
    
    # KG Construction → Quality Check
    workflow.add_edge("kg_construction", "quality_check")
    
    # 조건부 엣지: Quality Check → (Ontology Architect | GraphRAG Query)
    workflow.add_conditional_edges(
        "quality_check",
        route_after_quality_check,
        {
            "ontology_architect": "ontology_architect",
            "graphrag_query": "graphrag_query"
        }
    )
    
    # Ontology Architect → GraphRAG Query
    workflow.add_edge("ontology_architect", "graphrag_query")
    
    # 조건부 엣지: GraphRAG Query → (Sector Analyst, Company Analyst) 병렬
    # route_to_analysts가 리스트를 반환하면 병렬 실행
    workflow.add_conditional_edges(
        "graphrag_query",
        route_to_analysts,
        {
            "sector_analyst": "sector_analyst",
            "company_analyst": "company_analyst"
        }
    )
    
    # 모든 분석 에이전트 완료 후 리포트 생성으로 수렴
    workflow.add_edge("sector_analyst", "report_generation")
    workflow.add_edge("company_analyst", "report_generation")
    
    # 리포트 생성 후 종료
    workflow.add_edge("report_generation", END)
    
    return workflow


def compile_workflow():
    """
    워크플로우 컴파일
    
    Returns:
        컴파일된 워크플로우 앱 (CompiledGraph)
    """
    workflow = create_workflow()
    app = workflow.compile()
    return app


# 전역 워크플로우 인스턴스 (싱글톤)
_workflow_app = None


def get_workflow_app():
    """
    워크플로우 앱 싱글톤 반환
    
    Returns:
        컴파일된 워크플로우 앱
    """
    global _workflow_app
    if _workflow_app is None:
        _workflow_app = compile_workflow()
    return _workflow_app
