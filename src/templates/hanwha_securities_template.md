# [{{ company_name }}] {{ investment_opinion }}
**Date**: {{ date }} | **Target Price**: {{ target_price }} | **Upside**: {{ upside }}% | **Confidence**: {{ confidence }}

> [!NOTE]
> 본 보고서는 **Ontology 기반 Knowledge Graph → Bull/Bear Debate Agents → Judicial Agent**의 3단계 AI Reasoning Pipeline을 통해 생성된 결과물입니다.

## 1. Executive Summary
{{ executive_summary }}

## 2. Investment Thesis (핵심 투자 포인트)
{{ synthesis }}

### 🔥 Bull Argument (매수 논리)
{{ bull_argument }}

### ❄️ Bear Argument (매도 논리)
{{ bear_argument }}

## 3. Financial Analysis (재무/비재무 분석)

> [!CAUTION]
> 아래 재무 데이터는 **파이프라인 테스트 및 시연을 위한 Mock Data**입니다. 실제 온톨로지 DB 연동 시 실시간 데이터로 대체됩니다.

**[재무 요약]**
- **Revenue (매출)**: {{ revenue_2024 }} (Expected)
- **Operating Profit (영업이익)**: {{ op_2024 }}
- **EPS**: {{ eps_2024 }}

**[사업 구조]**
{{ business_structure }}

**[밸류에이션 코멘트]**
{{ valuation }}

## 4. 데이터 시각화 (Data & Visualization)

> [!TIP]
> 아래 차트 이미지는 파이프라인 실행 시 자동 생성되며, `data/outputs/charts/` 폴더에 저장됩니다.

### 📊 NetworkX Subgraph Analysis
아래 그래프는 분석에 사용된 핵심 엔티티와 관계망을 시각화한 것입니다.

[Figure: NetworkX Subgraph - {{ company_name }} 공급망]
![Graph Visualization]({{ network_graph_path }})

> **해석**: 위 그래프에서 노드의 크기는 영향력(Centrality), 엣지의 굵기는 관계의 가중치(Weight)를 의미합니다.

### 📉 핵심 차트 (Key Charts)

| AI 토론 점수 | 핵심 경쟁력 분석 |
| :---: | :---: |
| ![Debate Score]({{ score_chart_path }}) | ![Radar Chart]({{ radar_chart_path }}) |

**[주요 지표 추이]**
![Financial Trend]({{ financial_chart_path }})

---

### 참고 자료 (References & Provenance)
**Checked Impact Paths**:
{{ graph_paths }}

**Sources**:
{{ sources }}

---

<div style="font-size: 10px; color: gray;">
**[Compliance Notice]**  
본 리포트는 AI 에이전트에 의해 작성되었으며, 투자 참고용으로만 활용되어야 합니다. 실제 투자에 대한 책임은 투자자 본인에게 있습니다.
</div>
