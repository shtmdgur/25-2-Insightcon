"""
LangGraph 노드 함수 구현
각 에이전트를 LangGraph 노드로 래핑
"""
import time
import json
import hashlib
from pathlib import Path
from functools import lru_cache, wraps
from typing import Dict, Any, Tuple
from .state import ReportState

# 로그 파일 경로 설정
_DEBUG_LOG_PATH = Path(__file__).parent.parent.parent.parent / ".cursor" / "debug.log"
_DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
from ..agents.kg_construction import KGConstructionAgent
from ..agents.quality_check import QualityCheckAgent
from ..agents.ontology_architect import OntologyArchitectAgent
from ..agents.sector_analyst import SectorAnalystAgent
from ..agents.company_analyst import CompanyAnalystAgent
from ..utils.neo4j_client import Neo4jClient
from ..utils.llm_client import LLMSelector
from ..utils.document_loader import load_document


# 전역 클라이언트 인스턴스 (실제로는 의존성 주입 사용 권장)
_neo4j_client = None
_llm_selector = None

# GraphRAG 결과 캐시
_graphrag_cache = {}


def track_execution_time(node_name: str):
    """
    노드 실행 시간을 추적하는 데코레이터
    
    Args:
        node_name: 노드 이름
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state: ReportState) -> ReportState:
            # #region agent log
            try:
                with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":f"nodes.py:{node_name}","message":"Node entry","data":{"node_name":node_name,"has_document":state.get("document") is not None,"has_query":bool(state.get("query"))},"timestamp":int(time.time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion agent log
            
            start_time = time.time()
            try:
                result = func(state)
                elapsed_time = time.time() - start_time
                
                # 실행 시간을 결과에 추가
                # LangGraph reducer를 위해 리스트로 반환 (기존 state와 병합됨)
                execution_times = [{node_name: elapsed_time}]
                result['execution_times'] = execution_times
                
                # 실행 추적 로그에도 추가
                # LangGraph reducer를 위해 리스트로 반환 (기존 state와 병합됨)
                trace = [f"{node_name} completed in {elapsed_time:.2f}s"]
                result['execution_trace'] = trace
                
                # #region agent log
                try:
                    with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":f"nodes.py:{node_name}","message":"Node exit","data":{"node_name":node_name,"elapsed_time":elapsed_time,"result_keys":list(result.keys())},"timestamp":int(time.time()*1000)}) + "\n")
                except Exception:
                    pass
                # #endregion agent log
                
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                error_msg = f"{node_name} error after {elapsed_time:.2f}s: {str(e)}"
                
                # #region agent log
                try:
                    with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":f"nodes.py:{node_name}","message":"Node error","data":{"node_name":node_name,"error":str(e),"error_type":type(e).__name__},"timestamp":int(time.time()*1000)}) + "\n")
                except Exception:
                    pass
                # #endregion agent log
                
                # LangGraph reducer를 위해 리스트로 반환
                return {
                    'errors': [error_msg],
                    'execution_trace': [error_msg],
                    'execution_times': [{node_name: elapsed_time}]
                }
        return wrapper
    return decorator


def _get_cache_key(query: str, target_companies: list) -> str:
    """
    GraphRAG 쿼리 캐시 키 생성
    
    Args:
        query: 사용자 질의
        target_companies: 대상 기업 목록
    
    Returns:
        캐시 키 (해시값)
    """
    companies_str = ",".join(sorted(target_companies)) if target_companies else ""
    cache_string = f"{query}::{companies_str}"
    return hashlib.md5(cache_string.encode()).hexdigest()


def _get_neo4j_client() -> Neo4jClient:
    """Neo4j 클라이언트 싱글톤"""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
    return _neo4j_client


def _get_llm_selector() -> LLMSelector:
    """LLM Selector 싱글톤"""
    global _llm_selector
    if _llm_selector is None:
        _llm_selector = LLMSelector()
    return _llm_selector


@track_execution_time("kg_construction")
def kg_construction_node(state: ReportState) -> ReportState:
    """
    KG Construction Agent 실행 노드
    문서가 있을 때만 그래프를 구축하고, 없으면 스킵
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    try:
        # 새 문서가 있는지 확인
        document_input = state.get('document')
        
        # 문서가 없으면 스킵
        if not document_input:
            return {
                'kg_data': None,
                'execution_trace': ["KG Construction skipped (no new document)"]
            }
        
        # 문서 로드 (파일 경로인 경우 파일을 읽어서 텍스트로 변환)
        try:
            document = load_document(document_input)
        except Exception as e:
            error_msg = f"문서 로드 실패: {str(e)}"
            return {
                'errors': [error_msg],
                'execution_trace': [error_msg],
                'kg_data': None
            }
        
        # 문서가 없으면 스킵
        if not document:
            return {
                'kg_data': None,
                'execution_trace': ["KG Construction skipped (document is empty)"]
            }
        
        # 문서가 있으면 그래프 구축
        neo4j_client = _get_neo4j_client()
        llm_selector = _get_llm_selector()
        llm = llm_selector.get_llm("deep")
        
        agent = KGConstructionAgent(llm, neo4j_client)
        result = agent.process_document(document)
        
        return {
            'kg_data': result,
            'execution_trace': ["KG Construction completed"]
        }
        
    except Exception as e:
        error_msg = f"KG Construction error: {str(e)}"
        import traceback
        traceback.print_exc()  # 스택 트레이스 출력 추가
        return {
            'errors': [error_msg],
            'execution_trace': [error_msg],
            'kg_data': None  # 명시적으로 None 반환
        }


@track_execution_time("quality_check")
def quality_check_node(state: ReportState) -> ReportState:
    """
    Quality Check Agent 실행 노드
    그래프 업데이트가 없으면 스킵
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    try:
        # 그래프 업데이트가 없으면 스킵
        kg_data = state.get('kg_data')
        if not kg_data:
            return {
                'schema_issues': [],
                'execution_trace': ["Quality Check skipped (no graph update)"]
            }
        
        # 그래프 업데이트가 있을 때만 검사
        neo4j_client = _get_neo4j_client()
        agent = QualityCheckAgent(neo4j_client)
        
        # 품질 검사 실행
        check_result = agent.check(kg_data)
        
        # 결과를 상태에 저장
        schema_issues = check_result.get('schema_issues', [])
        schema_issues_list = [
            issue.get('message', '') for issue in schema_issues
        ] if schema_issues else []
        
        if check_result.get('has_issues'):
            issues = check_result.get('issues', [])
            return {
                'schema_issues': schema_issues_list,
                'execution_trace': [f"Quality Check: {len(issues)} issues found"]
            }
        else:
            return {
                'schema_issues': schema_issues_list,
                'execution_trace': ["Quality Check: No issues found"]
            }
        
    except Exception as e:
        error_msg = f"Quality Check error: {str(e)}"
        return {
            'errors': [error_msg],
            'execution_trace': [error_msg],
            'schema_issues': [error_msg]  # 에러 발생 시 스키마 이슈가 있다고 가정
        }


@track_execution_time("ontology_architect")
def ontology_architect_node(state: ReportState) -> ReportState:
    """
    Ontology Architect Agent 실행 노드
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    try:
        neo4j_client = _get_neo4j_client()
        llm_selector = _get_llm_selector()
        llm = llm_selector.get_llm("deep")
        
        agent = OntologyArchitectAgent(llm, neo4j_client)
        
        # 템플릿 문서 로드 (실제로는 파일이나 데이터베이스에서 로드)
        templates = _load_report_templates()
        
        # 스키마 생성
        schema_result = agent.generate_schema(templates)
        return {
            'ontology_schema': schema_result,
            'schema_issues': [],  # 스키마 이슈 해결됨
            'execution_trace': ["Ontology schema generated"]
        }
        
    except Exception as e:
        error_msg = f"Ontology Architect error: {str(e)}"
        return {
            'errors': [error_msg],
            'execution_trace': [error_msg]
        }


@track_execution_time("graphrag_query")
def graphrag_query_node(state: ReportState) -> ReportState:
    """
    GraphRAG 쿼리 실행 노드
    캐싱을 통해 동일한 질의는 캐시에서 반환
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    try:
        query = state.get('query', '')
        target_companies = state.get('target_companies') or []
        
        # 캐시 키 생성
        cache_key = _get_cache_key(query, target_companies)
        
        # #region agent log
        try:
            with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"nodes.py:graphrag_query_node","message":"Cache check","data":{"cache_key":cache_key,"cache_hit":cache_key in _graphrag_cache,"cache_size":len(_graphrag_cache)},"timestamp":int(time.time()*1000)}) + "\n")
        except Exception:
            pass
        # #endregion agent log
        
        # 캐시 확인
        if cache_key in _graphrag_cache:
            return {
                'graphrag_results': _graphrag_cache[cache_key],
                'execution_trace': ["GraphRAG query completed (from cache)"]
            }
        
        # 캐시 미스 - Neo4j 쿼리 실행
        neo4j_client = _get_neo4j_client()
        
        # 간단한 GraphRAG 쿼리 (실제로는 더 정교한 구현 필요)
        if target_companies and len(target_companies) > 0:
            # 특정 기업 조회 (파라미터 사용)
            cypher_query = """
            MATCH (c:Company)
            WHERE c.name IN $target_companies
            OPTIONAL MATCH (c)-[:MANUFACTURES]->(p:ProductLine)
            OPTIONAL MATCH (c)-[:HAS_METRIC]->(m:Metric)
            RETURN c, collect(DISTINCT p) as products, collect(DISTINCT m) as metrics
            """
            result = neo4j_client.query(cypher_query, {"target_companies": target_companies})
        else:
            # 전체 섹터 조회
            cypher_query = """
            MATCH (c:Company)
            OPTIONAL MATCH (c)-[:MANUFACTURES]->(p:ProductLine)
            OPTIONAL MATCH (c)-[:HAS_METRIC]->(m:Metric)
            RETURN c, collect(DISTINCT p) as products, collect(DISTINCT m) as metrics
            LIMIT 20
            """
            result = neo4j_client.query(cypher_query)
        
        # 결과를 구조화
        graphrag_results = {
            'companies': [],
            'products': [],
            'metrics': []
        }
        
        # Neo4j 쿼리 결과 처리
        # LangChain Neo4jGraph는 일반적으로 Record 객체 리스트를 반환
        if result:
            for record in result:
                try:
                    # Record 객체에서 값 추출 (키로 접근)
                    company = record.get('c') if hasattr(record, 'get') else (record['c'] if 'c' in record else None)
                    products = record.get('products', []) if hasattr(record, 'get') else (record.get('products', []) if isinstance(record, dict) else [])
                    metrics = record.get('metrics', []) if hasattr(record, 'get') else (record.get('metrics', []) if isinstance(record, dict) else [])
                    
                    # Company 정보 추출
                    if company:
                        # Node 객체인 경우 properties 속성 접근
                        if hasattr(company, 'properties'):
                            company_props = company.properties
                        elif isinstance(company, dict):
                            company_props = company
                        else:
                            company_props = {}
                        
                        if company_props.get('name'):
                            graphrag_results['companies'].append({
                                'name': company_props.get('name', ''),
                                'industry': company_props.get('industry', ''),
                                'marketCap': company_props.get('marketCap', '')
                            })
                    
                    # Products 정보 추출
                    if products:
                        for product in products:
                            if product:
                                if hasattr(product, 'properties'):
                                    product_props = product.properties
                                elif isinstance(product, dict):
                                    product_props = product
                                else:
                                    product_props = {}
                                
                                if product_props.get('name'):
                                    graphrag_results['products'].append({
                                        'name': product_props.get('name', ''),
                                        'category': product_props.get('category', '')
                                    })
                    
                    # Metrics 정보 추출
                    if metrics:
                        for metric in metrics:
                            if metric:
                                if hasattr(metric, 'properties'):
                                    metric_props = metric.properties
                                elif isinstance(metric, dict):
                                    metric_props = metric
                                else:
                                    metric_props = {}
                                
                                if metric_props.get('type') or metric_props.get('name'):
                                    graphrag_results['metrics'].append({
                                        'type': metric_props.get('type', metric_props.get('name', '')),
                                        'value': metric_props.get('value', ''),
                                        'period': metric_props.get('period', '')
                                    })
                except Exception as e:
                    # 개별 레코드 처리 실패는 무시하고 계속 진행
                    continue
        
        # 결과를 캐시에 저장
        _graphrag_cache[cache_key] = graphrag_results
        
        # 캐시 크기 제한 (최대 100개)
        if len(_graphrag_cache) > 100:
            # 가장 오래된 항목 제거 (FIFO)
            oldest_key = next(iter(_graphrag_cache))
            del _graphrag_cache[oldest_key]
        
        return {
            'graphrag_results': graphrag_results,
            'execution_trace': ["GraphRAG query completed"]
        }
        
    except Exception as e:
        error_msg = f"GraphRAG query error: {str(e)}"
        return {
            'errors': [error_msg],
            'execution_trace': [error_msg]
        }


@track_execution_time("sector_analyst")
def sector_analyst_node(state: ReportState) -> ReportState:
    """
    Sector Analyst 실행 노드
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    try:
        llm_selector = _get_llm_selector()
        llm = llm_selector.get_llm("deep")
        
        query = state.get('query', '')
        graphrag_results = state.get('graphrag_results', {})
        
        agent = SectorAnalystAgent(llm, graphrag_results)
        analysis = agent.analyze(query, graphrag_results)
        
        return {
            'sector_analysis': analysis,
            'execution_trace': ["Sector analysis completed"]
        }
        
    except Exception as e:
        error_msg = f"Sector Analyst error: {str(e)}"
        return {
            'errors': [error_msg],
            'execution_trace': [error_msg]
        }


@track_execution_time("company_analyst")
def company_analyst_node(state: ReportState) -> ReportState:
    """
    Company Analyst 실행 노드
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    try:
        llm_selector = _get_llm_selector()
        llm = llm_selector.get_llm("deep")
        
        target_companies = state.get('target_companies') or []
        graphrag_results = state.get('graphrag_results', {})
        
        if not target_companies or len(target_companies) == 0:
            return {
                'execution_trace': ["Company Analyst skipped (no target companies)"]
            }
        
        agent = CompanyAnalystAgent(llm, graphrag_results)
        analyses = agent.analyze_multiple(target_companies, graphrag_results)
        
        return {
            'company_analysis': analyses,
            'execution_trace': [f"Company analysis completed for {len(analyses)} companies"]
        }
        
    except Exception as e:
        error_msg = f"Company Analyst error: {str(e)}"
        return {
            'errors': [error_msg],
            'execution_trace': [error_msg]
        }


@track_execution_time("report_generation")
def report_generation_node(state: ReportState) -> ReportState:
    """
    최종 리포트 생성 노드
    
    Args:
        state: 워크플로우 상태
    
    Returns:
        업데이트된 상태
    """
    try:
        report_parts = []
        
        # 리포트 헤더
        report_parts.append("# 금융 분석 리포트\n")
        report_parts.append(f"**질의**: {state.get('query', '')}\n")
        report_parts.append(f"**리포트 타입**: {state.get('report_type', 'sector')}\n\n")
        
        # 섹터 분석 추가
        if state.get('sector_analysis'):
            report_parts.append("## 섹터 분석\n\n")
            report_parts.append(state['sector_analysis'])
            report_parts.append("\n\n")
        
        # 종목별 분석 추가
        if state.get('company_analysis'):
            report_parts.append("## 종목별 분석\n\n")
            for company, analysis in state['company_analysis'].items():
                report_parts.append(f"### {company}\n\n")
                report_parts.append(analysis)
                report_parts.append("\n\n")
        
        # 에러 정보 추가 (있는 경우)
        if state.get('errors'):
            report_parts.append("## 주의사항\n\n")
            for error in state['errors']:
                report_parts.append(f"- ⚠️ {error}\n")
            report_parts.append("\n")
        
        # 리포트 결합
        final_report = "".join(report_parts)
        return {
            'final_report': final_report,
            'execution_trace': ["Report generation completed"]
        }
        
    except Exception as e:
        error_msg = f"Report generation error: {str(e)}"
        return {
            'errors': [error_msg],
            'execution_trace': [error_msg],
            'final_report': f"리포트 생성 중 오류 발생: {str(e)}"
        }


def _load_report_templates() -> list:
    """
    리포트 템플릿 로드 (실제로는 파일이나 DB에서 로드)
    
    Returns:
        템플릿 문서 리스트
    """
    # 간단한 예시 템플릿 (실제로는 파일에서 로드)
    templates = [
        """
        증권 리포트 템플릿:
        - Company: 기업 정보
        - ProductLine: 제품 라인
        - Metric: 재무 지표
        - Relationship: MANUFACTURES, HAS_METRIC
        """,
        """
        반도체 섹터 리포트 구조:
        - 기업 분석: 사업 구조, 제품, 기술
        - 재무 분석: 매출, 이익, 지표
        - 경쟁 분석: 경쟁사 비교
        """
    ]
    return templates
