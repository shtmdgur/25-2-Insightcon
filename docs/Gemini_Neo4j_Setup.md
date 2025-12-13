# Neo4j + Gemini (Vertex AI) 통합 가이드

이 문서는 프로젝트에서 **Gemini (Vertex AI)**와 **Neo4j GraphRAG**를 사용하도록 설정하는 방법을 안내합니다.

## 필수 환경 변수

`.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 추가하세요:

```bash
# Neo4j Connection
NEO4J_URI=neo4j+s://your-auradb-instance.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j

# Google Cloud / Vertex AI (Gemini)
GOOGLE_API_KEY=your-google-api-key
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1

# Neo4j GraphRAG + Gemini Settings
GEMINI_ENABLED=True
EMBEDDING_MODEL=vertexai
VITE_LLM_MODELS=gemini-1.0-pro,gemini-1.5-pro
```

## 의존성 설치

프로젝트에 이미 필요한 패키지가 `pyproject.toml`에 추가되어 있습니다:
- `google-cloud-aiplatform>=1.30.0`: Vertex AI SDK
- `neo4j-graphrag>=0.1.0`: Neo4j GraphRAG 라이브러리
- `langchain-google-genai>=1.0.0`: LangChain Gemini 통합

설치 방법:
```bash
pip install -e .
# 또는
poetry install
```

## 지원 모델

### Gemini 모델
- `gemini-1.0-pro`: 일반 텍스트 생성 및 추론
- `gemini-1.5-pro`: 향상된 멀티모달 및 긴 컨텍스트 지원

### 임베딩 모델
- `vertexai`: Vertex AI 텍스트 임베딩 (추천)
- `all-MiniLM-L6-v2`: 로컬 임베딩 (경량화)

## OntologyArchitectAgent 사용 예시

```python
from src.agents.ontology_architect import OntologyArchitectAgent
from src.utils.llm_client import LLMSelector
from src.utils.neo4j_client import Neo4jClient

# LLM 클라이언트 초기화
llm_selector = LLMSelector()
llm = llm_selector.get_deep_llm()

# Neo4j 클라이언트 초기화
neo4j_client = Neo4jClient()

# 온톨로지 아키텍트 초기화
architect = OntologyArchitectAgent(
    llm=llm,
    neo4j_client=neo4j_client,
    project_id="your-gcp-project-id",
    location="us-central1"
)

# 스키마 자동 생성
templates = ["증권 리포트 1...", "증권 리포트 2..."]
schema_result = architect.generate_schema(templates)
```

## 참고 문서
- [Neo4j + Vertex AI Codelab](https://codelabs.developers.google.com/neo4j-vertexai-movie-recommender-python?hl=ko)
- [Neo4j LLM Graph Builder Deployment](https://neo4j.com/labs/genai-ecosystem/llm-graph-builder-deployment/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
