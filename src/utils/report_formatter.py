# src/utils/report_formatter.py

import markdown
from datetime import datetime
from typing import Dict, Optional
import jinja2
import os

# WeasyPrint is optional (requires GTK on Windows)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None

class HanwhaSecuritiesReportFormatter:
    """한화투자증권 스타일 리포트 생성기"""
    
    def __init__(self, template_dir: str = "src/templates", template_name: str = "hanwha_securities_template.md"):
        # Jinja2 템플릿 로더 - 절대 경로 또는 상대 경로 처리
        if not os.path.exists(template_dir):
             # Fallback to current dir or fixed path if needed
             template_dir = os.path.join(os.getcwd(), "src", "templates")
        
        self.template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=template_dir))
        self.template = self.template_env.get_template(template_name)
    
    def generate_report(
        self,
        company_name: str,
        bull_argument: str,
        bear_argument: str,
        synthesis: str,
        analysis_data: Dict,
        judge_verdict: Optional[Dict] = None,
        graph_paths: Optional[list] = None,
        sources: Optional[list] = None,
        network_graph_path: Optional[str] = None,
        score_chart_path: Optional[str] = None,
        radar_chart_path: Optional[str] = None,
        financial_chart_path: Optional[str] = None
    ) -> str:
        """
        한화투자증권 스타일 마크다운 리포트 생성
        
        Args:
            company_name: 기업명
            bull_argument: Bull 에이전트 주장
            bear_argument: Bear 에이전트 주장
            synthesis: Synthesizer 최종 판단 (전체 텍스트)
            analysis_data: 재무/비재무 분석 데이터
            graph_paths: Graph 경로 (Provenance)
            sources: 참고 자료 링크
            network_graph_path: 네트워크 그래프 이미지 경로
            score_chart_path: 토론 점수 차트 경로
            radar_chart_path: 레이더 차트 경로
            financial_chart_path: 재무 추이 차트 경로
        
        Returns:
            Markdown 형식 리포트
        """
        # Judge verdict에서 투자의견 추출 (우선), 없으면 Synthesis에서 추출
        investment_opinion = self._extract_opinion(synthesis, judge_verdict)
        target_price = self._extract_target_price(synthesis)
        confidence = self._extract_confidence(synthesis)
        
        # 템플릿 렌더링
        report_md = self.template.render(
            company_name=company_name,
            date=datetime.now().strftime("%Y.%m.%d"),
            target_price=f"{target_price:,}" if target_price else "N/A",
            upside=self._calculate_upside(target_price, analysis_data.get('current_price')),
            investment_opinion=investment_opinion,
            executive_summary=self._generate_summary(synthesis),
            
            # 재무 데이터 (실제 값이 없으면 "N/A" 반환)
            revenue_2023=self._safe_format(analysis_data.get('revenue_2023'), "조원"),
            revenue_2024=self._safe_format(analysis_data.get('revenue_2024'), "조원"),
            revenue_2025=self._safe_format(analysis_data.get('revenue_2025'), "조원"),
            op_2023=self._safe_format(analysis_data.get('op_2023'), "조원"),
            op_2024=self._safe_format(analysis_data.get('op_2024'), "조원"),
            op_2025=self._safe_format(analysis_data.get('op_2025'), "조원"),
            eps_2023=self._safe_format(analysis_data.get('eps_2023'), "원"),
            eps_2024=self._safe_format(analysis_data.get('eps_2024'), "원"),
            eps_2025=self._safe_format(analysis_data.get('eps_2025'), "원"),
            
            # 분석 섹션
            business_structure=analysis_data.get('business_structure', 'N/A'),
            key_products=analysis_data.get('key_products', 'N/A'),
            financial_performance=analysis_data.get('financial_performance', 'N/A'),
            valuation=analysis_data.get('valuation_comment', 'N/A'),
            
            # 변증법 토론 결과
            bull_argument=bull_argument,
            bear_argument=bear_argument,
            synthesis=synthesis,
            confidence=f"{confidence:.1%}",
            
            # Visuals
            network_graph_path=network_graph_path,
            score_chart_path=score_chart_path,
            radar_chart_path=radar_chart_path,
            financial_chart_path=financial_chart_path,
            
            # Provenance
            graph_paths=self._format_graph_paths(graph_paths) if graph_paths else "N/A",
            sources=self._format_sources(sources) if sources else "N/A"
        )
        
        return report_md
    
    def _extract_opinion(self, synthesis: str, judge_verdict: Optional[Dict] = None) -> str:
        """Judge verdict 또는 Synthesis에서 투자의견 추출 (Buy/Hold/Sell)"""
        # 1. Judge verdict가 있으면 우선 사용
        if judge_verdict and 'decision' in judge_verdict:
            decision = judge_verdict['decision'].upper()
            if 'BUY' in decision:
                return "매수 (Buy)"
            elif 'SELL' in decision:
                return "매도 (Sell)"
            elif 'HOLD' in decision or 'NR' in decision:
                return "중립 (Hold)"
        
        # 2. Synthesis에서 키워드 추출 (fallback)
        if "HOLD" in synthesis or "관망" in synthesis or "유보" in synthesis:
            return "중립 (Hold)"
        elif "매수" in synthesis or "Buy" in synthesis or "BUY" in synthesis:
            return "매수 (Buy)"
        elif "매도" in synthesis or "Sell" in synthesis or "SELL" in synthesis:
            return "매도 (Sell)"
        else:
            return "중립 (Hold)"
    
    def _safe_format(self, value, unit: str = "") -> str:
        """숫자 값을 안전하게 포맷팅 (비숫자 값은 N/A 반환)"""
        if value is None:
            return "N/A"
        if isinstance(value, str):
            # 이미 문자열인 경우 (N/A, 데이터 미연동 등)
            if "N/A" in value or "미연동" in value or not value.strip():
                return "N/A"
            try:
                value = float(value.replace(",", ""))
            except ValueError:
                return "N/A"
        try:
            if isinstance(value, (int, float)):
                return f"{value:,.0f}{unit}"
            return "N/A"
        except (TypeError, ValueError):
            return "N/A"
    
    def _extract_target_price(self, synthesis: str) -> int:
        """Synthesis에서 목표주가 추출"""
        import re
        # 정규식으로 "목표주가: 85,000원" 패턴 찾기
        match = re.search(r'목표주가[:\s]*([0-9,]+)원', synthesis)
        if match:
            return int(match.group(1).replace(',', ''))
        return 0
    
    def _extract_confidence(self, synthesis: str) -> float:
        """Synthesis에서 신뢰도 추출"""
        import re
        match = re.search(r'신뢰도[:\s]*([0-9.]+)', synthesis)
        if match:
            return float(match.group(1))
        return 0.7  # 기본값
    
    def _calculate_upside(self, target_price: int, current_price: Optional[int]) -> str:
        """예상 수익률 계산"""
        if not target_price or not current_price or current_price == 0:
            return "N/A"
        upside = ((target_price - current_price) / current_price) * 100
        return f"{upside:+.1f}"
    
    def _generate_summary(self, synthesis: str) -> str:
        """Investment Summary 생성 - Synthesis의 첫 3-4 줄"""
        summary_lines = [line for line in synthesis.split('\n') if line.strip() and not line.startswith('#')]
        return '\n'.join(summary_lines[:3]) if summary_lines else synthesis[:200]
    
    def _format_graph_paths(self, paths: list) -> str:
        """Graph Path를 텍스트로 포맷팅"""
        if not paths: return "N/A"
        formatted = []
        for i, path in enumerate(paths, 1):
            if isinstance(path, str): # Handle string paths
                formatted.append(f"{i}. {path}")
                continue
                
            path_str = " → ".join([
                f"**{node['name']}**" if isinstance(node, dict) and 'name' in node else f"*{str(node)}*"
                for node in path
            ])
            formatted.append(f"{i}. {path_str}")
        return '\n'.join(formatted)
    
    def _format_sources(self, sources: list) -> str:
        """출처 포맷팅"""
        if not sources: return "N/A"
        formatted = []
        for source in sources:
            if isinstance(source, dict):
                formatted.append(f"- {source.get('title', 'Untitled')} (페이지 {source.get('page', 'N/A')})")
            else:
                formatted.append(f"- {str(source)}")
        return '\n'.join(formatted)
