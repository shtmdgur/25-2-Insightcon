
import warnings
# Glyph missing warnings suppress
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message="Glyph.*missing from font")

import logging
logging.getLogger('matplotlib').setLevel(logging.ERROR)

import matplotlib
matplotlib.use('Agg') # GUI 없는 환경용
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
from typing import List, Dict, Tuple, Any

class MatplotlibVisualizer:
    """
    리포트용 차트 생성을 위한 시각화 유틸리티 클래스
    Matplotlib를 사용하여 정적 이미지를 생성합니다.
    """
    
    
    def __init__(self, save_dir: str = "data/outputs/charts"):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        
        # 한글 폰트 설정 (Windows: 맑은 고딕 기준)
        self._setup_font()
        
        # 스타일 설정
        try:
            plt.style.use('seaborn-v0_8-whitegrid')
        except:
            pass
        
    def _setup_font(self):
        """한글 폰트 설정 (강화 버전)"""
        import platform
        from matplotlib import font_manager
        
        system = platform.system()
        
        # Windows에서 사용 가능한 한글 폰트 찾기
        if system == "Windows":
            korean_fonts = [
                'Malgun Gothic',
                'NanumGothic', 
                'NanumBarunGothic',
                'Gulim',
                'Batang',
                'Dotum'
            ]
            
            # 설치된 폰트 목록에서 한글 폰트 찾기
            available_fonts = [f.name for f in font_manager.fontManager.ttflist]
            
            font_to_use = None
            for font in korean_fonts:
                if font in available_fonts:
                    font_to_use = font
                    break
            
            if font_to_use:
                plt.rcParams['font.family'] = font_to_use
                self.font_family = font_to_use # 인스턴스 변수에 저장
                print(f"✅ Korean font set to: {self.font_family}")
            else:
                # 폰트를 찾지 못한 경우 기본 설정
                plt.rcParams['font.family'] = 'sans-serif'
                self.font_family = 'sans-serif'
                print("⚠️ No Korean font found. Falling back to sans-serif")
                
        elif system == "Darwin":  # macOS
            plt.rcParams['font.family'] = 'AppleGothic'
            self.font_family = 'AppleGothic'
        else:  # Linux
            plt.rcParams['font.family'] = 'NanumGothic'
            self.font_family = 'NanumGothic'
        
        # 마이너스 기호 깨짐 방지
        plt.rcParams['axes.unicode_minus'] = False
        
        # 폰트 캐시 리빌드 (필요시)
        try:
            font_manager._rebuild()
        except:
            pass

    def plot_financial_trend(
        self, 
        periods: List[str], 
        revenue: List[float], 
        op_margin: List[float],
        filename: str = "financial_trend.png"
    ) -> str:
        """
        매출액(Bar) 및 영업이익률(Line) 추이 그래프 생성
        
        Args:
            periods: 기간 리스트 (예: ['23.1Q', '23.2Q', ...])
            revenue: 매출액 리스트 (단위: 조원)
            op_margin: 영업이익률 리스트 (단위: %)
            filename: 저장할 파일명
            
        Returns:
            저장된 이미지의 절대 경로
        """
        fig, ax1 = plt.subplots(figsize=(10, 6))

        # 1. Revenue (Bar Chart)
        bars = ax1.bar(periods, revenue, color='#00539F', alpha=0.7, label='Revenue (Trillion Won)')
        ax1.set_xlabel('Period', fontsize=12)
        ax1.set_ylabel('Revenue (Trillion Won)', color='#00539F', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='#00539F')
        
        # Value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}',
                     ha='center', va='bottom')

        # 2. Operating Margin (Line Chart) - dual axis
        ax2 = ax1.twinx()
        line = ax2.plot(periods, op_margin, color='#E31E24', marker='o', linewidth=2, label='Operating Margin (%)')
        ax2.set_ylabel('Operating Margin (%)', color='#E31E24', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='#E31E24')
        ax2.set_ylim(min(op_margin)-5, max(op_margin)+5)

        # Value labels
        for i, v in enumerate(op_margin):
            ax2.text(i, v + 0.5, f'{v}%', color='#E31E24', fontweight='bold', ha='center')

        plt.title('Quarterly Performance Trend', fontsize=16, pad=20)
        
        # Layout and save
        save_path = os.path.join(self.save_dir, filename)
        abs_path = os.path.abspath(save_path)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.close()
        
        return abs_path

    def plot_debate_score(
        self, 
        bull_score: float, 
        bear_score: float,
        filename: str = "debate_score.png"
    ) -> str:
        """
        Bull vs Bear 토론 점수 차트 생성 (Horizontal Bar Chart)
        """
        fig, ax = plt.subplots(figsize=(8, 4))
        
        categories = ['Bull (Bullish)', 'Bear (Bearish)']
        scores = [bull_score, bear_score]
        colors = ['#ff6b6b', '#4ecdc4']
        
        bars = ax.barh(categories, scores, color=colors, alpha=0.8, edgecolor='black')
        
        # Score labels
        for i, (bar, score) in enumerate(zip(bars, scores)):
            width = bar.get_width()
            ax.text(width + 2, bar.get_y() + bar.get_height()/2, 
                   f'{score:.0f}', 
                   va='center', ha='left', fontsize=12, fontweight='bold', fontfamily=self.font_family)
        
        # [FIX] 폰트 설정
        for tick in ax.get_yticklabels():
            tick.set_fontfamily(self.font_family)
        ax.set_xlabel('Debate Score (out of 100)', fontsize=11, fontfamily=self.font_family)
        ax.set_title('AI Debate Score Comparison', fontsize=14, fontweight='bold', fontfamily=self.font_family, pad=15)
        ax.set_xlim(0, 100)
        ax.grid(axis='x', alpha=0.3)
        
        save_path = os.path.join(self.save_dir, filename)
        abs_path = os.path.abspath(save_path)
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return abs_path

    def plot_radar_chart(
        self,
        categories: List[str],
        bull_values: List[int],
        bear_values: List[int],
        filename: str = "debate_radar.png"
    ) -> str:
        """
        Bull vs Bear 5각/6각 레이더 차트 생성 (상황 종합 분석용)
        """
        import numpy as np
        
        # 각도 계산
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1] # 닫힌 도형을 위해 시작점 반복
        
        # 값 반복 (닫힌 도형)
        bull_values = bull_values + bull_values[:1]
        bear_values = bear_values + bear_values[:1]
        
        # 차트 생성
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        # Bull Plot
        ax.plot(angles, bull_values, linewidth=2, linestyle='solid', label='Bull (Buy)', color='#E74C3C')
        ax.fill(angles, bull_values, '#E74C3C', alpha=0.2)
        
        # Bear Plot
        ax.plot(angles, bear_values, linewidth=2, linestyle='solid', label='Bear (Sell)', color='#4A90E2')
        ax.fill(angles, bear_values, '#4A90E2', alpha=0.2)
        
        # Label settings
        ax.set_xticks(angles[:-1])
        # [FIX] fontfamily 명시
        ax.set_xticklabels(categories, fontsize=11, fontweight='bold', fontfamily=self.font_family)
        
        # Y-axis settings
        ax.set_rlabel_position(0)
        plt.yticks([20, 40, 60, 80], ["20", "40", "60", "80"], color="grey", size=8)
        plt.ylim(0, 100)
        
        plt.title('Bull vs Bear Core Competitiveness Analysis', size=15, y=1.05, fontfamily=self.font_family)
        # 범례 폰트
        prop = fm.FontProperties(family=self.font_family, size=10)
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1), prop=prop)
        
        save_path = os.path.join(self.save_dir, filename)
        abs_path = os.path.abspath(save_path)
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return abs_path

    def plot_network_graph(self, nodes: List[str], edges: List[Tuple[str, str]], filename: str = "network_graph.png") -> str:
        """
        NetworkX를 사용한 관계망 시각화
        """
        try:
            import networkx as nx
        except ImportError:
            print("NetworkX not found. Install with `pip install networkx`.")
            return ""
        
        plt.figure(figsize=(10, 8))
        
        G = nx.Graph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        
        # 레이아웃 설정
        pos = nx.spring_layout(G, k=0.8, iterations=50)
        
        # Draw nodes and edges
        nx.draw_networkx_nodes(G, pos, node_size=2000, node_color="#E31E24", alpha=0.9)
        nx.draw_networkx_edges(G, pos, width=2, alpha=0.5, edge_color="gray")
        nx.draw_networkx_labels(G, pos, font_size=10, font_color="white", font_weight="bold")
        
        plt.title("Key Entity Relationship Network", fontsize=15, pad=20)
        plt.axis("off")
        
        save_path = os.path.join(self.save_dir, filename)
        abs_path = os.path.abspath(save_path)
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return abs_path

    def plot_impact_paths_network(
        self, 
        impact_paths: List[Dict], 
        target_company: str,
        filename: str = "network_graph.png",
        context_nodes: Dict[str, Any] = None
    ) -> str:
        """
        Bull/Bear가 사용한 Impact Paths를 네트워크 그래프로 시각화 (개선 버전)
        
        Args:
            impact_paths: Bull/Bear 에이전트가 사용한 인과 경로 리스트
            target_company: 분석 대상 기업명
            filename: 저장할 파일명
            context_nodes: 추가적으로 표시할 노드 정보 (debate data context)
            
        Returns:
            저장된 이미지의 절대 경로
        """
        try:
            import networkx as nx
        except ImportError:
            print("NetworkX not found. Install with `pip install networkx`.")
            return ""
        
        G = nx.DiGraph()
        node_types = {}  # 노드별 타입 저장
        
        # 1. Context Nodes 추가 (최대 15개로 제한하여 복잡도 감소)
        if context_nodes:
            # 매칭 정의
            type_mapping = {
                "agents": "IDM",
                "suppliers": "Supplier",
                "earnings": "Earnings",
                "price_moves": "PriceMovement",
                "issues": "Issue",
                "macros": "EconomicIndicator"
            }
            
            node_count = 0
            MAX_CONTEXT_NODES = 15
            
            for key, ntype in type_mapping.items():
                if node_count >= MAX_CONTEXT_NODES:
                    break
                    
                node_list = context_nodes.get(key, [])
                for node in node_list:
                    if node_count >= MAX_CONTEXT_NODES:
                        break
                        
                    if isinstance(node, dict):
                        name = node.get("name", str(node))
                        if name not in G.nodes():
                            G.add_node(name)
                            node_types[name] = ntype
                            # 타겟 기업과 연결
                            if name != target_company:
                                G.add_edge(name, target_company, weight=0.5)
                            node_count += 1

        # 2. Impact Paths에서 노드와 엣지 추출 (최대 5개 경로로 제한)
        for path in impact_paths[:5]:  # 상위 5개만 사용 (기존 15개에서 축소)
            if isinstance(path, dict):
                nodes = path.get("nodes", [])
                # ... (중략) ... 
                node_names = []
                for node in nodes:
                    if isinstance(node, dict):
                        name = node.get("name", str(node))
                        labels = node.get("_labels", [])
                        if labels and isinstance(labels, list):
                            ntype = labels[0]
                        else:
                            ntype = node.get("type", "Entity")
                        node_names.append(name)
                    else:
                        name = str(node)
                        ntype = "Entity"
                        node_names.append(name)
                    
                    if name not in G.nodes():
                        G.add_node(name)
                        node_types[name] = ntype
                
                # 엣지 추출: 노드 순서대로 연결
                for i in range(len(node_names) - 1):
                    G.add_edge(node_names[i], node_names[i + 1], weight=1.5) # 가중치 증가
            
            elif isinstance(path, str):
                import re
                matches = re.findall(r'\(([^:]+):?([^)]*)\)', path)
                prev_node = None
                for match in matches:
                    name = match[0].strip()
                    ntype = match[1].strip() if match[1] else "Entity"
                    G.add_node(name)
                    node_types[name] = ntype
                    if prev_node:
                        G.add_edge(prev_node, name, weight=1.0)
                    prev_node = name
        
        # 타겟 기업 노드 상태 보정
        if target_company not in G.nodes():
            G.add_node(target_company)
        node_types[target_company] = "Target"
        
        if len(G.nodes()) <= 1 and not impact_paths and not context_nodes:
            # 진짜 아무것도 없으면 기본 그래프라도 시각화
            pass
        
        # 시각화
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # 레이아웃 (엣지 가중치 고려)
        pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
        
        # 노드 색상 (타입별)
        node_colors = []
        for node in G.nodes():
            ntype = node_types.get(node, "Entity")
            if ntype == "Target":
                node_colors.append("#FF6B6B")  # 빨강 (타겟)
            elif ntype in ["IDM", "Fabless", "Foundry", "OSAT"]:
                node_colors.append("#4ECDC4")  # 청록 (기업)
            elif ntype in ["Earnings", "Disclosure", "PriceMovement"]:
                node_colors.append("#FFE66D")  # 노랑 (시그널)
            elif ntype in ["Issue", "Risk"]:
                node_colors.append("#F38181")  # 연분홍 (이슈)
            elif ntype in ["EconomicIndicator", "Policy"]:
                node_colors.append("#AA96DA")  # 보라 (매크로)
            else:
                node_colors.append("#95E1D3")  # 연두 (기타)
        
        # 그리기
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, alpha=0.9, ax=ax)
        # [FIX] font_family 명시적으로 전달
        nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", font_family=self.font_family, ax=ax)
        nx.draw_networkx_edges(G, pos, edge_color="#666666", arrows=True, 
                               arrowsize=20, alpha=0.6, width=2, ax=ax,
                               connectionstyle="arc3,rad=0.1")
        
        ax.set_title(f"📊 {target_company} 인과관계 네트워크 (Bull/Bear Evidence)", 
                    fontsize=14, fontweight='bold', fontfamily=self.font_family, pad=20)
        ax.axis('off')
        
        # 범례
        from matplotlib.lines import Line2D
        # 범례 폰트 설정
        prop = fm.FontProperties(family=self.font_family, size=10)
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF6B6B', markersize=12, label='분석 대상'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#4ECDC4', markersize=12, label='기업'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFE66D', markersize=12, label='시그널'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#F38181', markersize=12, label='이슈/리스크'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#AA96DA', markersize=12, label='매크로'),
        ]
        ax.legend(handles=legend_elements, loc='upper left', prop=prop)
        
        plt.tight_layout()
        
        save_path = os.path.join(self.save_dir, filename)
        abs_path = os.path.abspath(save_path)
        
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"✅ Impact Paths 네트워크 그래프 생성: {abs_path}")
        return abs_path

