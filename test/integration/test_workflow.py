"""
워크플로우 통합 테스트
"""
import sys
import time
import json
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 로그 파일 경로 설정
DEBUG_LOG_PATH = project_root.parent / ".cursor" / "debug.log"
DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

from src.pipeline import (
    get_workflow_app,
    ReportState
)


def test_full_workflow():
    """전체 워크플로우 테스트"""
    
    # 워크플로우 앱 가져오기
    app = get_workflow_app()
    
    # 초기 상태 설정
    initial_state: ReportState = {
        "query": "반도체 섹터 전체 동향 분석",
        "target_companies": ["삼성전자", "SK하이닉스"],
        "report_type": "all",  # sector, company, all
        "document": None,  # 새 문서 없음 (질의만 처리)
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": [],
        "execution_times": []
    }
    
    print("=" * 60)
    print("워크플로우 실행 시작")
    print("=" * 60)
    print(f"질의: {initial_state['query']}")
    print(f"대상 기업: {initial_state['target_companies']}")
    print(f"리포트 타입: {initial_state['report_type']}")
    print("-" * 60)
    
    try:
        # 워크플로우 실행
        result = app.invoke(initial_state)
        
        # 결과 검증
        print("\n실행 결과:")
        print("-" * 60)
        
        if result.get('final_report'):
            print("✓ 리포트 생성 완료")
            print(f"\n리포트 길이: {len(result['final_report'])} 문자")
            print("\n리포트 미리보기:")
            print(result['final_report'][:500] + "..." if len(result['final_report']) > 500 else result['final_report'])
        else:
            print("✗ 리포트 생성 실패")
        
        if result.get('errors'):
            print(f"\n경고: {len(result['errors'])}개의 에러 발생")
            for error in result['errors']:
                print(f"  - {error}")
        else:
            print("\n✓ 에러 없음")
        
        # 실행 시간 출력
        if result.get('execution_times'):
            print("\n실행 시간:")
            total_time = 0.0
            for time_dict in result['execution_times']:
                for node_name, elapsed_time in time_dict.items():
                    print(f"  - {node_name}: {elapsed_time:.2f}초")
                    total_time += elapsed_time
            print(f"  총 실행 시간: {total_time:.2f}초")
        
        print("\n실행 추적:")
        for trace in result.get('execution_trace', []):
            print(f"  - {trace}")
        
        print("\n" + "=" * 60)
        print("워크플로우 테스트 완료")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"\n✗ 워크플로우 실행 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_sector_only_workflow():
    """섹터 분석만 수행하는 워크플로우 테스트"""
    
    app = get_workflow_app()
    
    initial_state: ReportState = {
        "query": "반도체 섹터 동향",
        "target_companies": None,
        "report_type": "sector",
        "document": None,
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": [],
        "execution_times": []
    }
    
    print("\n섹터 분석 워크플로우 테스트")
    print("-" * 60)
    
    try:
        result = app.invoke(initial_state)
        
        if result.get('sector_analysis'):
            print("✓ 섹터 분석 완료")
        else:
            print("✗ 섹터 분석 실패")
        
        return result
    except Exception as e:
        print(f"✗ 실행 실패: {str(e)}")
        return None


def test_company_only_workflow():
    """종목 분석만 수행하는 워크플로우 테스트"""
    
    app = get_workflow_app()
    
    initial_state: ReportState = {
        "query": "삼성전자 종목 분석",
        "target_companies": ["삼성전자"],
        "report_type": "company",
        "document": None,
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": [],
        "execution_times": []
    }
    
    print("\n종목 분석 워크플로우 테스트")
    print("-" * 60)
    
    try:
        result = app.invoke(initial_state)
        
        if result.get('company_analysis'):
            print("✓ 종목 분석 완료")
            for company, analysis in result['company_analysis'].items():
                print(f"  - {company}: {len(analysis)} 문자")
        else:
            print("✗ 종목 분석 실패")
        
        return result
    except Exception as e:
        print(f"✗ 실행 실패: {str(e)}")
        return None


def test_graph_build_workflow():
    """그래프 구축 테스트 (document 제공)"""
    
    app = get_workflow_app()
    
    initial_state: ReportState = {
        "query": "반도체 섹터 동향",  # 질의도 함께 제공 가능
        "target_companies": None,
        "report_type": "sector",
        "document": """
        삼성전자는 2024년 3분기 매출 300조원을 기록했습니다.
        주요 제품은 HBM3 메모리 반도체입니다.
        SK하이닉스는 경쟁사로, 동일한 제품 라인을 보유하고 있습니다.
        """,  # 새 문서 → 그래프 구축 실행
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": [],
        "execution_times": []
    }
    
    print("\n" + "=" * 60)
    print("그래프 구축 테스트 (document 제공)")
    print("=" * 60)
    print("document가 있으므로 그래프 구축이 실행됩니다.")
    
    try:
        result = app.invoke(initial_state)
        
        if result.get('kg_data'):
            print("✓ 그래프 구축 완료")
            stats = result.get('kg_data', {}).get('stats', {})
            print(f"  - Companies: {stats.get('companies', 0)}")
            print(f"  - Products: {stats.get('products', 0)}")
            print(f"  - Metrics: {stats.get('metrics', 0)}")
        else:
            print("✗ 그래프 구축 실패")
            # 디버깅 정보 추가
            if result.get('errors'):
                print(f"  에러: {result['errors']}")
            if result.get('execution_trace'):
                print(f"  추적: {result['execution_trace']}")
        
        # 실행 시간 출력
        if result.get('execution_times'):
            print("\n실행 시간:")
            total_time = 0.0
            for time_dict in result['execution_times']:
                for node_name, elapsed_time in time_dict.items():
                    print(f"  - {node_name}: {elapsed_time:.2f}초")
                    total_time += elapsed_time
            print(f"  총 실행 시간: {total_time:.2f}초")
        
        return result
    except Exception as e:
        print(f"✗ 실행 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_query_workflow():
    """질의 처리 테스트 (document 없음 → 자동 스킵)"""
    
    app = get_workflow_app()
    
    initial_state: ReportState = {
        "query": "반도체 섹터 동향 분석",
        "target_companies": ["삼성전자"],
        "report_type": "all",
        "document": None,  # 문서 없음 → KG Construction 자동 스킵
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": [],
        "execution_times": []
    }
    
    print("\n" + "=" * 60)
    print("질의 처리 테스트 (document 없음)")
    print("=" * 60)
    print("document가 없으므로 KG Construction이 자동으로 스킵됩니다.")
    
    try:
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"test_workflow.py:test_query_workflow","message":"Workflow invoke start","data":{"initial_state_keys":list(initial_state.keys()),"report_type":initial_state.get("report_type")},"timestamp":int(time.time()*1000)}) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        result = app.invoke(initial_state)
        
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"test_workflow.py:test_query_workflow","message":"Workflow invoke complete","data":{"result_keys":list(result.keys()) if result else None,"has_final_report":bool(result.get('final_report')) if result else False,"has_errors":bool(result.get('errors')) if result else False},"timestamp":int(time.time()*1000)}) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        if result.get('final_report'):
            print("✓ 리포트 생성 완료")
        else:
            print("✗ 리포트 생성 실패")
        
        # 실행 시간 출력
        if result.get('execution_times'):
            print("\n실행 시간:")
            total_time = 0.0
            for time_dict in result['execution_times']:
                for node_name, elapsed_time in time_dict.items():
                    print(f"  - {node_name}: {elapsed_time:.2f}초")
                    total_time += elapsed_time
            print(f"  총 실행 시간: {total_time:.2f}초")
        
        return result
    except Exception as e:
        print(f"✗ 실행 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 전체 워크플로우 테스트
    # test_full_workflow()
    
    # 그래프 구축 워크플로우 테스트
    test_graph_build_workflow()
    
    # 질의 처리 워크플로우 테스트 (빠른 모드)
    test_query_workflow()
    
    # 섹터 분석만 테스트
    # test_sector_only_workflow()
    
    # 종목 분석만 테스트
    # test_company_only_workflow()
