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
        토론 종합 및 최종 리포트 생성 (Judge의 판결 기반)
        
        Args:
            state: ReportState containing:
                   - debate_state: bull_history, bear_history
                   - judge_verdict: Dict (from JudgeAgent)
        
        Returns:
            최종 투자 판단 리포트 (Markdown)
        """
        # 1. State에서 데이터 추출
        debate_state = state.get("debate_state", {})
        bull_history = debate_state.get("bull_history", "")
        bear_history = debate_state.get("bear_history", "")
        judge_verdict = state.get("judge_verdict", {})
        
        # 2. 템플릿 로드
        template = self.prompts.get("debate_agents", {}).get("synthesizer", {}).get("instruction", "")
        
        # 3. 프롬프트 구성
        # Judge Verdict가 딕셔너리이므로 보기 좋게 JSON 문자열이나 포맷팅된 문자열로 변환
        import json
        verdict_str = json.dumps(judge_verdict, indent=2, ensure_ascii=False)
        
        # 안전한 get을 위해 기본값 설정
        decision = judge_verdict.get("decision", "HOLD")
        score = judge_verdict.get("score", 50)
        confidence = judge_verdict.get("confidence_level", "Medium")
        rationale = judge_verdict.get("rationale", "No rationale provided.")
        winning_side = judge_verdict.get("winning_side", "Neutral")
        
        
        # 4. 차트 생성 (Visualizer 호출)
        visual_charts_md = ""
        network_graph_path = "" # For Formatter
        
        try:
            from src.utils.visualizer import MatplotlibVisualizer
            visualizer = MatplotlibVisualizer()
            
            # 4-1. 토론 스코어 차트
            bull_score = judge_verdict.get("bull_score", 45) # 기본값
            bear_score = judge_verdict.get("bear_score", 55) # 기본값
            score_chart_path = visualizer.plot_debate_score(bull_score, bear_score, filename="debate_score.png")
            
            # 4-2. 재무 추이 차트 (데이터가 없으면 Mock 데이터 사용 - 데모용)
            # 실제 환경에서는 context_data나 KG에서 추출해야 함
            periods = ['23.1Q', '23.2Q', '23.3Q', '23.4Q', '24.1Q', '24.2Q', '24.3Q']
            revenue = [63.7, 60.0, 67.4, 67.8, 71.9, 74.1, 79.1]
            op_margin = [1.0, 1.1, 3.6, 4.2, 9.2, 14.1, 11.6]
            
            financial_chart_path = visualizer.plot_financial_trend(periods, revenue, op_margin, filename="financial_trend.png")
            
            # 4-3. 핵심 경쟁력 레이더 차트 (Radar Chart)
            import random
            categories = ["성장성", "수익성", "밸류에이션", "모멘텀", "리스크 관리"]
            
            # Bull: 총점이 높으면 성장성/모멘텀/수익성 위주로 높게 설정
            b_base = bull_score
            bull_values = [
                min(b_base + 10, 95), # 성장성 강점
                min(b_base + 5, 90),  # 수익성
                max(b_base - 10, 40), # 밸류에이션 (보통 고평가 논란 있음)
                min(b_base + 15, 98), # 모멘텀
                max(b_base - 5, 50)   # 리스크
            ]
            
            # Bear
            be_base = bear_score
            bear_values = [
                max(be_base - 15, 30), # 성장성 의심
                max(be_base - 5, 40),  # 수익성
                min(be_base + 15, 95), # 밸류에이션 (저평가 아님을 주장하거나 고평가 지적)
                max(be_base - 10, 30), # 모멘텀 약화 주장
                min(be_base + 10, 90)  # 리스크 관리 필요성 역설
            ]
            
            radar_chart_path = visualizer.plot_radar_chart(categories, bull_values, bear_values, filename="debate_radar.png")
            
            # 4-4. [New] Network Graph Visualization
            # Impact Paths를 파싱하여 노드와 엣지 생성
            nodes = set()
            edges = []
            impact_paths = state.get("impact_paths", [])
            
            for path in impact_paths:
                # e.g., "[A] -> [B] -> [C]"
                import re
                parts = re.findall(r"\[(.*?)\]", path)
                for i in range(len(parts) - 1):
                    u, v = parts[i], parts[i+1]
                    nodes.add(u)
                    nodes.add(v)
                    edges.append((u, v))
            
            if not nodes: # Fallback dummy
                nodes = ["Market Context", "Price", "Fundametals"]
                edges = [("Market Context", "Price"), ("Fundametals", "Price")]
            
            network_graph_path = visualizer.plot_network_graph(list(nodes), edges, filename="network_graph.png")
            
            # 상대 경로 변환 for Markdown
            import os
            try:
                score_rel_path = os.path.relpath(score_chart_path, os.getcwd()).replace("\\", "/")
                financial_rel_path = os.path.relpath(financial_chart_path, os.getcwd()).replace("\\", "/")
                radar_rel_path = os.path.relpath(radar_chart_path, os.getcwd()).replace("\\", "/")
                network_rel_path = os.path.relpath(network_graph_path, os.getcwd()).replace("\\", "/")
            except ValueError:
                score_rel_path = score_chart_path
                financial_rel_path = financial_chart_path
                radar_rel_path = radar_chart_path
                network_rel_path = network_graph_path

            visual_charts_md = f"""
![AI 토론 점수]({score_rel_path})

![Bull vs Bear 핵심 경쟁력 분석]({radar_rel_path})

![분기별 실적 추이]({financial_rel_path})
"""
        except Exception as e:
            print(f"Visualization Error: {e}")
            visual_charts_md = f"(차트 생성 실패: {e})"
            network_rel_path = ""

        impact_paths = state.get("impact_paths", [])
        evidence_paths_str = "\n".join([f"- {path}" for path in impact_paths]) if impact_paths else "(No specific validation paths found in this session.)"

        # 5. 템플릿 채우기 (LLM Prompt)
        try:
            prompt = template.format(
                ticker=state.get("query", ""),
                bull_history=bull_history,
                bear_history=bear_history,
                evidence_paths=evidence_paths_str, 
                judge_verdict=verdict_str,
                decision=decision,
                score=score,
                confidence_level=confidence,
                rationale_summary=rationale[:100] + "..." if len(rationale) > 100 else rationale, 
                rationale=rationale, 
                winning_side=winning_side,
                bull_outcome="Winner" if winning_side == "Bull" else "Lose",
                bear_outcome="Winner" if winning_side == "Bear" else "Lose",
                history=f"Bull History:\n{bull_history}\n\nBear History:\n{bear_history}",
                visual_charts=visual_charts_md,
                market_context=state.get("market_context", "(Market data unavailable)")
            )
            
            # 6. LLM 실행 (Analysis Content Generation)
            response = self.llm.invoke(prompt)
            
            # 7. 응답 파싱
            content = response.content
            # Handle List/Dict structure
            analysis_content = ""
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        text_parts.append(item["text"])
                    elif hasattr(item, "text"):
                         text_parts.append(item.text)
                    else:
                        text_parts.append(str(item))
                analysis_content = "".join(text_parts)
            elif isinstance(content, dict):
                 analysis_content = content.get("text", str(content))
            else:
                 analysis_content = str(content)
            
            # 8. [New] Report Formatting using HanwhaFormatter
            from src.utils.report_formatter import HanwhaSecuritiesReportFormatter
            formatter = HanwhaSecuritiesReportFormatter()
            
            # Prepare Analysis Data (Mocking for now, or extracting from price_context if available)
            # In a real scenario, this comes from Financial Analysis Node.
            analysis_data = {
                "current_price": state.get("price_context", {}).get("prices", [0])[-1] if state.get("price_context") else 0,
                "revenue_2023": 258,  # 조원 (Trillion Won)
                "revenue_2024": 302,  # 조원
                "revenue_2025": 350,  # 조원
                "op_2023": 6.5,       # 조원
                "op_2024": 35.8,      # 조원
                "op_2025": 52.1,      # 조원
                "eps_2023": 950,      # 원
                "eps_2024": 4200,     # 원
                "eps_2025": 6100,     # 원
                "business_structure": "DS(반도체, 45%), DX(모바일/가전, 40%), SDC(디스플레이, 10%), Harman(5%)",
                "key_products": "DRAM, NAND, System LSI, Smartphone, TV",
                "valuation_comment": f"P/B 1.05x (Historical Low). {winning_side} view prevails."
            }
            
            final_report = formatter.generate_report(
                company_name=state.get("query", "Target Company"),
                bull_argument=bull_history,
                bear_argument=bear_history,
                synthesis=analysis_content,
                analysis_data=analysis_data,
                judge_verdict=state.get("judge_verdict"),  # Judge verdict 전달
                graph_paths=impact_paths,
                sources=state.get("citation_paths", []),  # Assuming citations
                network_graph_path=network_rel_path,
                score_chart_path=score_rel_path,
                radar_chart_path=radar_rel_path,
                financial_chart_path=financial_rel_path
            )
            
            return final_report
            
        except Exception as e:
            return f"Error generating report: {str(e)}"

    def _parse_response(self, response) -> Dict[str, Any]:
         # 상위 클래스 호환성 유지용
         return super()._parse_response(response)
