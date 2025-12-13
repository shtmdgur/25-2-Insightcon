# 📌 25-2 Insightcon - Hanwha Multi-Agent Decision System (v0.1.0)

온톨로지 기반 AI 금융 코파일럿 프로젝트

## 📖 프로젝트 개요

한국 반도체 섹터(상장/주요 비상장)의 정적·동적 정보를 온톨로지와 지식그래프로 구조화하고, 멀티 에이전트가 증권 리포트 초안·팩트체크·시나리오 분석을 자동 수행하는 리서치 워크벤치를 구축하는 프로젝트.

## 🔧 기술 스택 및 주요 의존성

- Python >=3.10, <3.13
- Poetry (의존성 및 가상환경 관리)
- 주요 라이브러리: `pymupdf4llm`, `langgraph`, `langchain`, `langchain-neo4j`
- 그래프/DB: `neo4j`, `neo4j-graphrag`
- 유틸리티: `python-dotenv`, `pydantic`
- LLM 통합/SDK: `langchain-openai`, `langchain-google-genai`, `google-generativeai`, `openai`

(더 자세한 의존성은 `pyproject.toml`의 `dependencies` 섹션을 참고하세요.)

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

### 3. Python 환경 설정
프로젝트는 Python 3.10 이상, 3.13 미만을 권장합니다.
```bash
# Windows (예시)
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
# .env 파일을 열어서 필요한 API 키 및 설정 입력
```

## 🚀 실행 예시

### Phase 0: PyMuPDF + VLM Parser
```bash
poetry run python test/test_phase0.py
```

### Gemini PDF → Neo4j Pipeline (NEW)
```bash
poetry run python test/test_gemini_pdf_neo4j.py
```

## 🌿 브랜치 구조

- `main`: 안정 버전
- `dev`: 개발 브랜치
- `sh-develop4`: Phase 0 구현 (PyMuPDF + VLM)
- `sh-geminiParsingPDF`: **Gemini PDF Native Parser** (PDF → KG → Neo4j)

## 🔥 Gemini PDF Pipeline (sh-geminiParsingPDF 브랜치)

PDF를 Gemini API(gemini-2.5-pro)로 직접 분석하여 Knowledge Graph를 추출하고 Neo4j에 주입하는 파이프라인:

```
PDF → Gemini Files API → Structured Output (JSON) → Neo4j
```

**특징**:
- Structured JSON Schema로 일관된 KG 추출
- 7가지 엔티티 타입 (Company, Product, Metric, Event, Trend, Technology, Person)
- 7가지 관계 타입 (PRODUCES, COMPETES_WITH, HAS_METRIC 등)
- Neo4j 바로 주입 가능
- Batch API 지원 (50% 비용 절감)

**문서**: `docs/implementation_logs/gemini_pdf_neo4j_pipeline.md`

## 📚 문서

- 추가 설명 및 예시는 `docs/README.md`를 참고하세요.
- Phase 0 구현: `docs/implementation_logs/phase0_작업내역.md`
- Gemini PDF Pipeline: `docs/implementation_logs/gemini_pdf_neo4j_pipeline.md`

## 📝 개발 규칙

- Git Flow: `main` → `dev` → `feature/xxx`  
- 코드 스타일: Black, isort, flake8  
- `poetry.lock`은 반드시 커밋해야 함
