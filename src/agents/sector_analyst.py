"""
섹터 분석 에이전트
GraphRAG 결과를 기반으로 섹터 전체 동향을 분석
"""
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel


class SectorAnalystAgent:
    """
    섹터 전체 동향을 분석하는 에이전트
    """
    
    def __init__(self, llm: BaseChatModel, graphrag_results: Optional[Dict[str, Any]] = None):
        """
        SectorAnalystAgent 초기화
        
        Args:
            llm: LLM 모델 (분석 리포트 생성에 사용)
            graphrag_results: GraphRAG 검색 결과 (선택)
        """
        self.llm = llm
        self.graphrag_results = graphrag_results
    
    def analyze(self, query: str, graphrag_results: Optional[Dict[str, Any]] = None) -> str:
        """
        섹터 분석 수행
        
        Args:
            query: 사용자 질의
            graphrag_results: GraphRAG 검색 결과
        
        Returns:
            섹터 분석 리포트
        """
        results = graphrag_results or self.graphrag_results or {}
        
        # GraphRAG 결과를 텍스트로 변환
        context = self._format_graphrag_results(results)
        
        prompt = f"""
        당신은 반도체 섹터 전문 분석가입니다.
        
        질의: {query}
        
        관련 정보:
        {context}
        
        다음을 포함한 섹터 리포트를 작성하세요:
        1. 섹터 전체 동향
        2. 주요 기업 비교
        3. 밸류체인 분석
        4. 리스크 요인
        5. 투자 포인트
        
        리포트는 마크다운 형식으로 작성해주세요.
        """
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            raise RuntimeError(f"섹터 분석 실패: {str(e)}")
    
    def _format_graphrag_results(self, results: Dict[str, Any]) -> str:
        """
        GraphRAG 결과를 읽기 쉬운 텍스트로 변환
        
        Args:
            results: GraphRAG 검색 결과
        
        Returns:
            포맷팅된 텍스트
        """
        if not results:
            return "관련 정보가 없습니다."
        
        text = "=== 관련 정보 ===\n\n"
        
        # Companies 정보
        if 'companies' in results:
            text += "Companies:\n"
            for company in results.get('companies', []):
                name = company.get('name', 'Unknown')
                industry = company.get('industry', '')
                text += f"- {name}: {industry}\n"
            text += "\n"
        
        # Products 정보
        if 'products' in results:
            text += "Products:\n"
            for product in results.get('products', []):
                name = product.get('name', 'Unknown')
                category = product.get('category', '')
                text += f"- {name}: {category}\n"
            text += "\n"
        
        # Metrics 정보
        if 'metrics' in results:
            text += "Metrics:\n"
            for metric in results.get('metrics', []):
                metric_type = metric.get('type', 'Unknown')
                value = metric.get('value', '')
                text += f"- {metric_type}: {value}\n"
            text += "\n"
        
        # Subgraph 정보
        if 'subgraph' in results:
            subgraph = results['subgraph']
            if 'nodes' in subgraph:
                text += f"관련 노드 수: {len(subgraph['nodes'])}\n"
            if 'edges' in subgraph:
                text += f"관련 관계 수: {len(subgraph['edges'])}\n"
        
        return text
