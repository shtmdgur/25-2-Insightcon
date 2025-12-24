"""
차트 자동 생성 유틸리티

Bull/Bear 토론에서 사용된 데이터를 기반으로 차트 생성:
1. 네트워크 그래프: Impact Paths 시각화
2. 토론 점수 차트: Bull vs Bear 비교
3. 근거 요약 차트: Judge가 채택한 핵심 근거들
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for server
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class ChartGenerator:
    """Bull/Bear 토론 데이터 기반 차트 생성기"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path("data/outputs/charts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 한글 폰트 설정
        self._setup_korean_font()
    
    def _setup_korean_font(self):
        """한글 폰트 설정"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Windows 한글 폰트 시도
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",  # 맑은 고딕
            "C:/Windows/Fonts/NanumGothic.ttf",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # Linux
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    fm.fontManager.addfont(font_path)
                    plt.rcParams['font.family'] = fm.FontProperties(fname=font_path).get_name()
                    break
                except:
                    pass
        
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
    
    def generate_network_graph(
        self, 
        impact_paths: List[Dict], 
        target_company: str,
        timestamp: str = None
    ) -> Optional[str]:
        """
        Impact Paths를 네트워크 그래프로 시각화
        
        Args:
            impact_paths: Bull/Bear가 사용한 인과 경로 리스트
            target_company: 분석 대상 기업명
            timestamp: 파일명에 사용할 타임스탬프
            
        Returns:
            생성된 이미지 파일 경로 (실패 시 None)
        """
        if not NETWORKX_AVAILABLE or not MATPLOTLIB_AVAILABLE:
            print("⚠️ NetworkX 또는 Matplotlib이 설치되지 않았습니다.")
            return None
        
        if not impact_paths:
            print("⚠️ Impact Paths가 비어있어 네트워크 그래프를 생성할 수 없습니다.")
            return None
        
        try:
            G = nx.DiGraph()
            
            # Impact Paths에서 노드와 엣지 추출
            for path in impact_paths[:20]:  # 상위 20개만 사용
                nodes = path.get("nodes", [])
                relations = path.get("relations", [])
                
                # 노드 추가
                for node in nodes:
                    node_name = node.get("name", "Unknown")
                    node_type = node.get("type", "Entity")
                    G.add_node(node_name, type=node_type)
                
                # 엣지 추가
                for rel in relations:
                    source = rel.get("source", "")
                    target = rel.get("target", "")
                    rel_type = rel.get("type", "RELATED")
                    if source and target:
                        G.add_edge(source, target, label=rel_type)
            
            # 타겟 기업 강조
            if target_company and target_company not in G.nodes():
                G.add_node(target_company, type="Target")
            
            if len(G.nodes()) == 0:
                print("⚠️ 그래프에 노드가 없습니다.")
                return None
            
            # 시각화
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # 레이아웃
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
            
            # 노드 색상 (타입별)
            node_colors = []
            for node in G.nodes():
                node_type = G.nodes[node].get("type", "Entity")
                if node == target_company:
                    node_colors.append("#FF6B6B")  # 빨강 (타겟)
                elif node_type in ["IDM", "Fabless", "Foundry"]:
                    node_colors.append("#4ECDC4")  # 청록 (기업)
                elif node_type in ["Earnings", "Issue", "Disclosure"]:
                    node_colors.append("#FFE66D")  # 노랑 (시그널)
                else:
                    node_colors.append("#95E1D3")  # 연두
            
            # 그리기
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1500, alpha=0.9, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold", ax=ax)
            nx.draw_networkx_edges(G, pos, edge_color="#666666", arrows=True, 
                                   arrowsize=15, alpha=0.6, ax=ax)
            
            # 엣지 라벨
            edge_labels = nx.get_edge_attributes(G, 'label')
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6, ax=ax)
            
            ax.set_title(f"📊 {target_company} 인과관계 네트워크 (Impact Paths)", fontsize=14, fontweight='bold')
            ax.axis('off')
            
            # 범례
            legend_elements = [
                plt.scatter([], [], c="#FF6B6B", s=100, label="분석 대상"),
                plt.scatter([], [], c="#4ECDC4", s=100, label="기업"),
                plt.scatter([], [], c="#FFE66D", s=100, label="시그널/이슈"),
            ]
            ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
            
            plt.tight_layout()
            
            # 저장
            ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"network_graph_{ts}.png"
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"✅ 네트워크 그래프 생성: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 네트워크 그래프 생성 실패: {e}")
            return None
    
    def generate_debate_score_chart(
        self,
        judge_verdict: Dict,
        bull_rounds: int = 3,
        bear_rounds: int = 3,
        timestamp: str = None
    ) -> Optional[str]:
        """
        Bull vs Bear 토론 점수 차트 생성
        
        Args:
            judge_verdict: Judge 판결 결과 (score, winning_side 등)
            bull_rounds: Bull 라운드 수
            bear_rounds: Bear 라운드 수
            
        Returns:
            생성된 이미지 파일 경로
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            score = judge_verdict.get("score", 50)
            winning_side = judge_verdict.get("winning_side", "Neutral")
            confidence = judge_verdict.get("confidence", "Medium")
            
            # Bull/Bear 점수 계산 (Judge 점수 기반)
            if winning_side.upper() == "BULL":
                bull_score = score
                bear_score = 100 - score
            elif winning_side.upper() == "BEAR":
                bull_score = 100 - score
                bear_score = score
            else:
                bull_score = 50
                bear_score = 50
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            categories = ['Bull (매수)', 'Bear (매도)']
            scores = [bull_score, bear_score]
            colors = ['#4CAF50', '#F44336']  # 초록, 빨강
            
            bars = ax.barh(categories, scores, color=colors, height=0.5)
            
            # 점수 텍스트 표시
            for bar, score in zip(bars, scores):
                ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, 
                        f'{score}점', va='center', fontsize=12, fontweight='bold')
            
            ax.set_xlim(0, 110)
            ax.set_xlabel('점수 (100점 만점)', fontsize=11)
            ax.set_title(f'🏆 AI 토론 결과: {winning_side.upper()} 승리 (신뢰도: {confidence})', 
                        fontsize=13, fontweight='bold')
            
            # 중앙선
            ax.axvline(x=50, color='gray', linestyle='--', alpha=0.5)
            
            plt.tight_layout()
            
            ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"debate_score_{ts}.png"
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"✅ 토론 점수 차트 생성: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 토론 점수 차트 생성 실패: {e}")
            return None
    
    def generate_evidence_summary_chart(
        self,
        bull_evidence: List[str],
        bear_evidence: List[str],
        adopted_evidence: List[str],
        timestamp: str = None
    ) -> Optional[str]:
        """
        Bull/Bear 근거 및 Judge 채택 근거 시각화
        
        Args:
            bull_evidence: Bull이 제시한 근거 목록
            bear_evidence: Bear가 제시한 근거 목록
            adopted_evidence: Judge가 채택한 핵심 근거
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 데이터 준비
            categories = ['Bull 근거', 'Bear 근거', 'Judge 채택']
            counts = [len(bull_evidence), len(bear_evidence), len(adopted_evidence)]
            colors = ['#4CAF50', '#F44336', '#2196F3']
            
            bars = ax.bar(categories, counts, color=colors, width=0.6)
            
            for bar, count in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{count}개', ha='center', fontsize=12, fontweight='bold')
            
            ax.set_ylabel('근거 수', fontsize=11)
            ax.set_title('📋 토론 근거 분석', fontsize=13, fontweight='bold')
            ax.set_ylim(0, max(counts) + 3)
            
            plt.tight_layout()
            
            ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.output_dir / f"evidence_summary_{ts}.png"
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"✅ 근거 요약 차트 생성: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ 근거 요약 차트 생성 실패: {e}")
            return None
    
    def generate_all_charts(
        self,
        impact_paths: List[Dict],
        target_company: str,
        judge_verdict: Dict,
        timestamp: str = None
    ) -> Dict[str, Optional[str]]:
        """
        모든 차트 일괄 생성
        
        Returns:
            {"network_graph": path, "debate_score": path, ...}
        """
        ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {
            "network_graph": self.generate_network_graph(impact_paths, target_company, ts),
            "debate_score": self.generate_debate_score_chart(judge_verdict, timestamp=ts),
        }
        
        return results
