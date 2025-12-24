# 📌 25-2 Insightcon - Hanwha Multi-Agent Decision System (v0.2.0)

**[2025-2 Insightcon] 온톨로지 기반 AI 금융 코파일럿 프로젝트**

본 프로젝트는 한국 반도체 섹터의 정적·동적 정보를 **Knowledge Graph**로 구조화하고, **Bull vs Bear 멀티 에이전트 토론**을 통해 심도 있는 투자 리포트를 자동 생성하는 시스템입니다.

## 🌟 주요 기능 (Key Features)

### 1. 🔍 Multi-Agent Debate System (AI 변증법 토론)
- **Bull Agent (낙관론)**: 기업의 성장성, 기회 요인, 긍정적 시그널(호재)을 중심으로 논리 전개.
- **Bear Agent (비관론)**: 리스크 요인, 밸류에이션 부담, 지정학적 위협 등을 중심으로 반박.
- **Judge Agent (판결자)**: 양측의 주장을 듣고 데이터(Graph Path) 기반의 냉정한 판결(Buy/Hold/Sell) 및 평점 부여.

### 2. 🕸️ Knowledge Graph & GraphRAG
- **Neo4j 기반 지식 그래프**: 뉴스, 리포트, 재무제표를 구조화된 그래프(Entity & Relation)로 저장.
- **GraphRAG**: 단순 검색이 아닌, '인과 관계 경로(Impact Path)'를 추적하여 나비효과 분석.
- **Time-Traveling**: 분석 기준일(Target Date) 시점의 데이터만 조회하여 미래 참조 편향(Look-ahead Bias) 방지.

### 3. 🖥️ Interactive Web Interface (Streamlit)
- **Hanwha Branding**: 한화투자증권 브랜드 아이덴티티(Orange Theme) 적용.
- **Real-time Streaming**: 에이전트 간의 치열한 토론 과정을 실시간 채팅 UI로 시각화.
- **Visual Report**: Network Graph, Radar Chart 등을 포함한 고품질 Markdown 리포트 자동 생성 및 다운로드.

---

## � 기술 스택 (Tech Stack)

- **Framework**: `LangChain`, `LangGraph` (Multi-Agent Workflow)
- **Database**: `Neo4j` (Graph DBMS)
- **Frontend**: `Streamlit` (Interactive Web App)
- **LLM**: `Gemini-1.5-Pro` (Main Logic), `OpenAI` (Fallback)
- **Tools**: `Poetry` (Dependency Management)

---

## 🛠 실행 방법 (Getting Started)

### 1. 환경 설정 (Prerequisites)
- Python 3.10+
- Neo4j Database (Local or AuraDB)
- API Keys (`.env` 파일 설정 필요)

```bash
# .env 파일 생성 및 키 입력
cp .env.example .env
```

### 2. 의존성 설치
```bash
poetry install
```

### 3. Streamlit 앱 실행 (Main)
```bash
poetry run streamlit run streamlit_app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 접속할 수 있습니다.

---

## 📂 프로젝트 구조 (Structure)

```
25-2-Insightcon/
├── src/
│   ├── agents/          # Bull, Bear, Judge, Synthesizer Agents
│   ├── pipeline/        # GraphRAG, Debate Workflow 정의
│   ├── models/          # Pydantic Schemas, Neo4j Nodes
│   └── tools/           # Visualization, Data Loaders
├── charts/              # 생성된 시각화 차트 저장소
├── data/                # 원본 데이터 및 결과물
├── streamlit_app.py     # 웹 애플리케이션 진입점
├── pyproject.toml       # 의존성 관리
└── README.md            # 메인 문서
```

## 📝 개발 규칙

- **Git Flow**: `main` (Stable) → `dev` (Development) → `feature/xxx`
- **Commit Message**: Conventional Commits (e.g., `feat: add bull agent logic`)

