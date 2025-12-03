# 📌 25-2 Insightcon - Hanwha Multi-Agent Decision System

온톨로지 기반 AI 금융 코파일럿 프로젝트

## 📖 프로젝트 개요

한화그룹 관련 뉴스·정책·마켓 이벤트를 온톨로지 기반 지식그래프로 구조화하고,
Bull/Bear/Judge 기반 멀티 에이전트가 투자·리스크 의사결정을 시뮬레이션하는 프로젝트입니다.

## 🔧 기술 스택

- Python 3.10
- Poetry (의존성 관리)
- LangChain / LangGraph (에이전트 프레임워크)
- Owlready2 (온톨로지 조작)
- NetworkX / RDFlib (지식 그래프)

## 🛠 초기 설정

### 1. 저장소 클론
```bash
git clone <저장소_URL>
cd 25-2-Insightcon
```

### 2. Poetry 설치
```bash
pip install poetry
```

### 3. Python 3.10 환경 설정
```bash
# Windows
poetry env use "$(py -3.10 -c 'import sys; print(sys.executable)')"

# macOS/Linux
poetry env use python3.10
```

### 4. 의존성 설치
```bash
poetry install
```

### 5. 가상환경 활성화
```bash
poetry shell
```

### 6. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 API 키 입력
```

## 🚀 실행

```bash
poetry run python src/pipeline/run_multi_agent.py
```

## 📝 개발 규칙

- Git Flow: `main` → `dev` → `feature/xxx`
- 코드 스타일: Black, isort, flake8
- `poetry.lock`은 반드시 커밋해야 함