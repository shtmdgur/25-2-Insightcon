from typing import Dict, Any, Optional
from .base_debate_agent import BaseDebateAgent

class SynthesizerAgent(BaseDebateAgent):
    """
    종합 에이전트 (Synthesizer / CIO Role)
    """
    
    def __init__(self, llm, neo4j_connection=None):
        super().__init__(llm, neo4j_connection, role="synthesizer")
        

    def argue(self, state: Dict[str, Any], opponent_last_arg: Optional[str] = None) -> Dict[str, str]:
        # Synthesizer는 argue를 사용하지 않지만, 인터페이스 호환성을 위해 구현
        return {"argument": "저는 종합 에이전트입니다."}

    def synthesize(self, state: Dict[str, Any]) -> str:
        """
        토론 종합 및 최종 리포트 생성 (시각화 및 전문 포맷팅 포함)
        """
        # 1. 유틸리티 초기화
        from src.utils.visualizer import MatplotlibVisualizer
        from src.utils.report_formatter import HanwhaSecuritiesReportFormatter
        
        vis = MatplotlibVisualizer()
        formatter = HanwhaSecuritiesReportFormatter()
        
        # 2. State에서 데이터 추출
        debate_state = state.get("debate_state", {})
        bull_history = debate_state.get("bull_history", "")
        bear_history = debate_state.get("bear_history", "")
        full_history = debate_state.get("full_history", "")
        
        judge_result = debate_state.get("judge_result", {})
        rationale = judge_result.get("rationale", "판결 결과 없음")
        decision = judge_result.get("decision", "HOLD")
        score = judge_result.get("score", 50)
        
        data = self._extract_data_from_state(state)
        target_company = state.get("target_companies", ["알 수 없음"])[0] if state.get("target_companies") else "알 수 없음"
        
        # 3. 시각화 자료(Charts) 생성
        print(f"📊 {target_company} 분석 차트 생성 중...")
        try:
            # (1) 토론 점수 차트
            score_path = vis.plot_debate_score(
                bull_score=float(score) if judge_result.get("winning_side") == "Bull" else 100 - float(score),
                bear_score=float(score) if judge_result.get("winning_side") == "Bear" else 100 - float(score)
            )
            
            # (2) 레이더 차트 (기본값 설정 후 필요시 LLM으로 보강 가능)
            radar_path = vis.plot_radar_chart(
                categories=['Valuation', 'Growth', 'Profitability', 'Risk', 'Moat'],
                bull_values=[score, score-10, score+5, 40, score-5], # Mock logic
                bear_values=[100-score, 110-score, 95-score, 60, 105-score]
            )
            
            # (3) 재무 추이 차트 (Mock or extracted from state)
            financial_path = vis.plot_financial_trend(
                periods=['2023', '2024(E)', '2025(E)'],
                revenue=[258.9, 305.2, 332.5],
                op_margin=[2.5, 9.8, 12.4]
            )
            
            # (4) 네트워크 그래프
            nodes = [target_company]
            edges = []
            for path in data.get("impact_paths", []):
                # path가 dict이고 'text'가 있는 경우 파싱 시도 (간소화)
                if isinstance(path, dict) and "text" in path:
                    parts = path["text"].split(" --")
                    if len(parts) > 1:
                        nodes.append(parts[0].strip())
                        # edges.append((parts[0], target_company))
            
            network_path = vis.plot_network_graph(list(set(nodes))[:10], edges)
            
        except Exception as e:
            print(f"⚠️ 시각화 생성 중 오류 발생 (스킵): {e}")
            score_path = radar_path = financial_path = network_path = ""

        # 4. LLM을 통한 분석 원문(Synthesis) 생성
        template = self.prompts.get("debate_agents", {}).get("synthesizer", {}).get("instruction", "")
        try:
            prompt = template.format(
                ticker=target_company,
                rationale=rationale,
                history=full_history,
                evidence_paths=str(data.get("impact_paths", [])),
                decision=decision,
                score=score,
                confidence_level=judge_result.get("confidence_level", "Medium"),
                winning_side=judge_result.get("winning_side", "Neutral"),
                bull_history=bull_history,
                bear_history=bear_history,
                critical_paths=str(data.get("impact_paths", [])),
                target_date=state.get("target_date", ""),
                risk_profile="중립",
                rationale_summary=rationale[:200] if len(rationale) > 200 else rationale,
                bull_outcome="매수 논지",
                bear_outcome="매도 논지",
                document_context=self._format_document_summary(data.get("document_summary"))
            )
            response = self.llm.invoke(prompt)
            synthesis_text = self._parse_response(response)["argument"]
        except Exception as e:
            print(f"⚠️ Synthesis 생성 실패: {e}")
            synthesis_text = rationale

        # 5. Formatter를 통한 최종 리포트 조립
        print("📄 리포트 포맷팅 중...")
        # ⚠️ [Anti-Hallucination] 하드코딩된 Mock 데이터 대신 N/A 플레이스홀더 사용
        # 실제 데이터는 Neo4j 또는 외부 API 연동 시 주입
        analysis_data = {
            "current_price": "(데이터 미연동)",
            "revenue_2023": "(N/A)", "revenue_2024": "(N/A)", "revenue_2025": "(N/A)",
            "op_2023": "(N/A)", "op_2024": "(N/A)", "op_2025": "(N/A)",
            "eps_2023": "(N/A)", "eps_2024": "(N/A)", "eps_2025": "(N/A)",
            "business_structure": "(KG 또는 공시 데이터 연동 필요)",
            "key_products": "(KG에서 자동 추출 예정)",
            "valuation_comment": "(밸류에이션 데이터 미연동)"
        }
        
        final_report = formatter.generate_report(
            company_name=target_company,
            bull_argument=bull_history,
            bear_argument=bear_history,
            synthesis=synthesis_text,
            analysis_data=analysis_data,
            judge_verdict=judge_result,
            graph_paths=data.get("impact_paths", []),
            network_graph_path=network_path,
            score_chart_path=score_path,
            radar_chart_path=radar_path,
            financial_chart_path=financial_path
        )
        
        return final_report

