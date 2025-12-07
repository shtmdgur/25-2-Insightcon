"""
종목 분석 에이전트
개별 종목에 대한 상세 분석 수행
"""
from typing import Dict, Any, Optional, List
from langchain_core.language_models import BaseChatModel


class CompanyAnalystAgent:
    """
    개별 종목을 분석하는 에이전트
    """
    
    def __init__(self, llm: BaseChatModel, graphrag_results: Optional[Dict[str, Any]] = None):
        """
        CompanyAnalystAgent 초기화
        
        Args:
            llm: LLM 모델 (분석 리포트 생성에 사용)
            graphrag_results: GraphRAG 검색 결과 (선택)
        """
        self.llm = llm
        self.graphrag_results = graphrag_results
    
    def analyze(
        self, 
        company_name: str, 
        graphrag_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        개별 종목 분석
        
        Args:
            company_name: 분석할 기업명
            graphrag_results: GraphRAG 검색 결과
        
        Returns:
            종목 분석 리포트
        """
        results = graphrag_results or self.graphrag_results or {}
        
        # 해당 기업 관련 정보 추출
        company_context = self._extract_company_data(company_name, results)
        
        prompt = f"""
        당신은 개별 종목 전문 분석가입니다.
        
        종목: {company_name}
        
        관련 정보:
        {company_context}
        
        다음을 포함한 종목 리포트를 작성하세요:
        1. 사업 구조
        2. 주요 제품 및 기술
        3. 재무 분석
        4. 경쟁 우위
        5. 리스크 요인
        6. 투자 의견
        
        리포트는 마크다운 형식으로 작성해주세요.
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            raise RuntimeError(f"종목 분석 실패 ({company_name}): {str(e)}")
    
    def analyze_multiple(
        self,
        company_names: List[str],
        graphrag_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        여러 종목을 병렬로 분석
        
        Args:
            company_names: 분석할 기업명 리스트
            graphrag_results: GraphRAG 검색 결과
        
        Returns:
            기업명을 키로 하는 분석 결과 딕셔너리
        """
        results = {}
        
        for company_name in company_names:
            try:
                analysis = self.analyze(company_name, graphrag_results)
                results[company_name] = analysis
            except Exception as e:
                results[company_name] = f"분석 실패: {str(e)}"
        
        return results
    
    def _extract_company_data(
        self, 
        company_name: str, 
        results: Dict[str, Any]
    ) -> str:
        """
        GraphRAG 결과에서 특정 기업 관련 정보 추출
        
        Args:
            company_name: 기업명
            results: GraphRAG 검색 결과
        
        Returns:
            포맷팅된 기업 정보 텍스트
        """
        if not results:
            return f"{company_name}에 대한 정보가 없습니다."
        
        text = f"=== {company_name} 관련 정보 ===\n\n"
        
        # Companies 정보에서 해당 기업 찾기
        if 'companies' in results:
            for company in results.get('companies', []):
                if company.get('name', '').lower() == company_name.lower():
                    text += f"기업 정보:\n"
                    for key, value in company.items():
                        if key != 'name':
                            text += f"- {key}: {value}\n"
                    text += "\n"
                    break
        
        # Products 정보 (해당 기업의 제품)
        if 'products' in results:
            text += "주요 제품:\n"
            for product in results.get('products', []):
                # 간단한 필터링 (실제로는 더 정교한 로직 필요)
                text += f"- {product.get('name', 'Unknown')}: {product.get('category', '')}\n"
            text += "\n"
        
        # Metrics 정보 (해당 기업의 지표)
        if 'metrics' in results:
            text += "재무 지표:\n"
            for metric in results.get('metrics', []):
                metric_type = metric.get('type', 'Unknown')
                value = metric.get('value', '')
                period = metric.get('period', '')
                text += f"- {metric_type}: {value} ({period})\n"
            text += "\n"
        
        return text
