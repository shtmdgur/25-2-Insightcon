"""
워크플로우 통합 테스트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import get_workflow_app, ReportState


def test_full_workflow():
    """전체 워크플로우 테스트"""
    
    # 워크플로우 앱 가져오기
    app = get_workflow_app()
    
    # 초기 상태 설정
    initial_state: ReportState = {
        "query": "반도체 섹터 전체 동향 분석",
        "target_companies": ["삼성전자", "SK하이닉스"],
        "report_type": "all",  # sector, company, all
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": []
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
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": []
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
        "ontology_schema": None,
        "schema_issues": None,
        "kg_data": None,
        "graphrag_results": None,
        "sector_analysis": None,
        "company_analysis": None,
        "final_report": None,
        "errors": [],
        "execution_trace": []
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


if __name__ == "__main__":
    # 전체 워크플로우 테스트
    test_full_workflow()
    
    # 섹터 분석만 테스트
    # test_sector_only_workflow()
    
    # 종목 분석만 테스트
    # test_company_only_workflow()
