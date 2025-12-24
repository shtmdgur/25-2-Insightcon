from typing import Dict, Any, Optional
import os
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
        
        # 3. 시각화 자료(Charts) 생성 - 리포트 제목을 파일명으로 사용
        import re
        query = state.get("query", target_company)
        # 파일명에 사용 불가한 문자 제거
        safe_title = re.sub(r'[\\/*?:"<>|]', "", query)[:30].strip().replace(" ", "_")
        
        print(f"📊 {target_company} 분석 차트 생성 중...")
        try:
            # (1) 토론 점수 차트
            score_path = vis.plot_debate_score(
                bull_score=float(score) if judge_result.get("winning_side") == "Bull" else 100 - float(score),
                bear_score=float(score) if judge_result.get("winning_side") == "Bear" else 100 - float(score),
                filename=f"debate_score_{safe_title}.png"
            )
            
            # (2) 레이더 차트 - LLM이 debate 결과를 기반으로 점수 추출
            radar_data = self._extract_radar_scores_from_debate(bull_history, bear_history, score)
            radar_path = vis.plot_radar_chart(
                categories=['Valuation', 'Growth', 'Profitability', 'Risk', 'Moat'],
                bull_values=radar_data.get("bull", [score, score-10, score+5, 40, score-5]),
                bear_values=radar_data.get("bear", [100-score, 110-score, 95-score, 60, 105-score]),
                filename=f"debate_radar_{safe_title}.png"
            )
            
            # (3) 재무 추이 차트 - 제거 요청에 따라 주석 처리 또는 삭제
            # financial_data = self._extract_financial_from_debate(bull_history, bear_history)
            # financial_path = vis.plot_financial_trend(...)
            financial_path = ""
            
            # (4) 네트워크 그래프 (개선된 Impact Paths + 컨텍스트 기반)
            network_path = vis.plot_impact_paths_network(
                impact_paths=data.get("impact_paths", []),
                target_company=target_company,
                filename=f"network_graph_{safe_title}.png",
                context_nodes=data  # 전체 data(agents, macros 등)를 컨텍스트로 전달
            )
            
        except Exception as e:
            print(f"⚠️ 시각화 생성 중 오류 발생 (스킵): {e}")
            score_path = radar_path = financial_path = network_path = ""

        # 4. LLM을 통한 분석 원문(Synthesis) 생성
        template = self.prompts.get("debate_agents", {}).get("synthesizer", {}).get("instruction", "")
        try:
            # Risk Profile을 Judge decision에 따라 동적 설정
            decision_to_risk = {
                "STRONG BUY": "적극 매수(Bullish)",
                "BUY": "매수(Buy)",
                "HOLD": "중립(Neutral)", 
                "SELL": "매도(Sell)",
                "STRONG SELL": "적극 매도(Bearish)"
            }
            risk_profile = decision_to_risk.get(decision.upper(), "중립(Neutral)")
            
            # [FIX] 토큰 제한 방지를 위한 텍스트 절삭 (최대 1M 토큰 방어)
            # 주요 히스토리를 1인당 1만자 내외로 조절 (총 합 3만자 내외)
            trimmed_bull = bull_history[:10000] + ("..." if len(bull_history) > 10000 else "")
            trimmed_bear = bear_history[:10000] + ("..." if len(bear_history) > 10000 else "")
            trimmed_full = full_history[:20000] + ("..." if len(full_history) > 20000 else "")
            
            # Impact Paths가 매우 길어질 수 있으므로 상위 20개 정도로 더 제한
            paths = data.get("impact_paths", [])
            trimmed_paths = str(paths[:20]) + ("..." if len(paths) > 20 else "")

            prompt = template.format(
                ticker=target_company,
                rationale=rationale,
                history=trimmed_full,
                evidence_paths=trimmed_paths,
                decision=decision,
                score=score,
                confidence_level=judge_result.get("confidence_level", "Medium"),
                winning_side=judge_result.get("winning_side", "Neutral"),
                bull_history=trimmed_bull,
                bear_history=trimmed_bear,
                critical_paths=trimmed_paths,
                target_date=state.get("target_date", ""),
                risk_profile=risk_profile,  # 동적 설정
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
        # LLM이 debate 결과에서 추출한 분석 데이터 사용
        analysis_data = self._extract_analysis_data_from_debate(bull_history, bear_history, target_company)
        
        # [FIX] 마크다운 삽입을 위한 상대 경로 계산
        # 리포트가 data/outputs/cli/ 에 저장된다고 가정할 때, 
        # 이미지는 ../charts/ 에 있으므로 상대 경로로 변환
        def get_rel_path(abs_path):
            if not abs_path: return ""
            return f"../charts/{os.path.basename(abs_path)}"

        final_report = formatter.generate_report(
            company_name=target_company,
            bull_argument=bull_history,
            bear_argument=bear_history,
            synthesis=synthesis_text,
            analysis_data=analysis_data,
            judge_verdict=judge_result,
            graph_paths=data.get("impact_paths", []),
            network_graph_path=get_rel_path(network_path),
            score_chart_path=get_rel_path(score_path),
            radar_chart_path=get_rel_path(radar_path),
            financial_chart_path="" # 제거
        )
        
        return final_report

    def _extract_radar_scores_from_debate(self, bull_history: str, bear_history: str, base_score: int) -> Dict:
        """Debate 내용에서 각 카테고리별 점수를 LLM으로 추출"""
        try:
            prompt = f"""다음 Bull/Bear 토론 내용을 분석하여 각 카테고리별 점수(0-100)를 추출하세요.

[Bull 주장]
{bull_history[:1500]}

[Bear 주장]
{bear_history[:1500]}

각 카테고리에 대해 Bull과 Bear 관점의 점수를 JSON 형식으로 반환하세요:
- Valuation: 밸류에이션 매력도
- Growth: 성장 잠재력
- Profitability: 수익성
- Risk: 리스크 수준 (높을수록 안전)
- Moat: 경쟁 우위 (진입 장벽)

출력 형식:
{{"bull": [Valuation, Growth, Profitability, Risk, Moat], "bear": [Valuation, Growth, Profitability, Risk, Moat]}}
"""
            response = self.llm.invoke(prompt)
            # [FIX] response.content이 list인 경우 처리
            content = response.content if hasattr(response, "content") else response
            if isinstance(content, list):
                text = "".join([item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in content])
            else:
                text = str(content)
            
            import json
            import re
            # JSON 추출
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # JSON 객체 찾기
            match = re.search(r'\{[^}]+\}', text)
            if match:
                data = json.loads(match.group())
                return data
        except Exception:
            pass # Fallback으로 이동
        # Fallback: 기본 로직
        return {
            "bull": [base_score, base_score-10, base_score+5, 40, base_score-5],
            "bear": [100-base_score, 110-base_score, 95-base_score, 60, 105-base_score]
        }

    def _extract_financial_from_debate(self, bull_history: str, bear_history: str) -> Dict:
        """Debate 내용에서 재무 수치 추출"""
        try:
            prompt = f"""다음 토론 내용에서 언급된 재무 수치를 추출하세요.

[토론 내용]
{(bull_history + bear_history)[:2000]}

다음 JSON 형식으로 숫자만 반환하세요 (단위: 조원, %):
{{"periods": ["2023", "2024(E)", "2025(E)"], "revenue": [매출1, 매출2, 매출3], "op_margin": [영업이익률1, 영업이익률2, 영업이익률3]}}

수치를 찾을 수 없으면 0으로 표시하세요.
"""
            response = self.llm.invoke(prompt)
            # [FIX] response.content이 list인 경우 처리
            content = response.content if hasattr(response, "content") else response
            if isinstance(content, list):
                text = "".join([item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in content])
            else:
                text = str(content)
            
            import json
            import re
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            match = re.search(r'\{[^}]+\}', text.replace('\n', ''))
            if match:
                data = json.loads(match.group())
                return data
        except Exception:
            pass  # 조용히 fallback
        
        return {"periods": ['2023', '2024(E)', '2025(E)'], "revenue": [0, 0, 0], "op_margin": [0, 0, 0]}

    def _extract_analysis_data_from_debate(self, bull_history: str, bear_history: str, target_company: str) -> Dict:
        """Debate 내용에서 분석 데이터 추출"""
        try:
            prompt = f"""다음 {target_company}에 대한 토론 내용에서 핵심 분석 정보를 추출하세요.

[토론 내용]
{(bull_history + bear_history)[:2500]}

다음 JSON 형식으로 반환하세요:
{{
  "business_structure": "사업 구조 요약 (1-2문장)",
  "key_products": "핵심 제품/서비스 (쉼표로 구분)",
  "valuation_comment": "밸류에이션 평가 (1문장)"
}}
"""
            response = self.llm.invoke(prompt)
            # [FIX] response.content이 list인 경우 처리
            content = response.content if hasattr(response, "content") else response
            if isinstance(content, list):
                text = "".join([item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in content])
            else:
                text = str(content)
            
            import json
            import re
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                # 기본 필드 보완
                return {
                    "current_price": "(가격 데이터 연동 필요)",
                    "revenue_2023": "(N/A)", "revenue_2024": "(N/A)", "revenue_2025": "(N/A)",
                    "op_2023": "(N/A)", "op_2024": "(N/A)", "op_2025": "(N/A)",
                    "eps_2023": "(N/A)", "eps_2024": "(N/A)", "eps_2025": "(N/A)",
                    "business_structure": data.get("business_structure", "정보 없음"),
                    "key_products": data.get("key_products", "정보 없음"),
                    "valuation_comment": data.get("valuation_comment", "정보 없음")
                }
        except Exception:
            pass  # 조용히 fallback
        
        return {
            "current_price": "(데이터 미연동)",
            "revenue_2023": "(N/A)", "revenue_2024": "(N/A)", "revenue_2025": "(N/A)",
            "op_2023": "(N/A)", "op_2024": "(N/A)", "op_2025": "(N/A)",
            "eps_2023": "(N/A)", "eps_2024": "(N/A)", "eps_2025": "(N/A)",
            "business_structure": "토론에서 추출된 정보 없음",
            "key_products": "토론에서 추출된 정보 없음",
            "valuation_comment": "토론에서 추출된 정보 없음"
        }
