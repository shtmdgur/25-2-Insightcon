# Backup Directory

이 디렉토리는 향후 사용하지 않지만 참고용으로 보관하는 파일들을 저장합니다.

## 파일 목록

### Demo 파일
- `demo_e2e_pipeline.py` - 초기 E2E 파이프라인 데모 (2024-12-14)
  - 새로운 Orchestrator 아키텍처로 대체됨
  - 참고: KGConstructionAgent가 이 역할을 수행

- `demo_phase1_agents.py` - Phase 1 에이전트 데모 (2024-12-14)
  - 개별 에이전트 테스트용
  - 참고: 통합 테스트(`test/test_integration.py`)로 대체됨

### 실험적 파서 및 에이전트
- `ontology_architect.py` - Neo4j GraphRAG 기반 온톨로지 자동 생성 (2024-12-14)
  - Neo4j GraphRAG + Vertex AI 사용
  - 현재 Seed Ontology(Pydantic Enum) 방식 사용으로 불필요

- `vlm_enhanced.py` - Enhanced VLM Parser (2024-12-14)
  - PyMuPDF + Gemini Vision 하이브리드 파서
  - GeminiPDFParser(Gemini Native PDF)로 대체됨

### 유틸리티 (미사용)
- `convert_pdfs.py` - PDF 변환 유틸리티 (사용되지 않음)
- `document_loader.py` - 문서 로더 (사용되지 않음)
- `prompt_loader.py` - 프롬프트 로더 (YAML 직접 로드 방식으로 대체)

## 사용하지 않는 이유

### Orchestrator 아키텍처 도입
새로운 아키텍처에서는 `KGConstructionAgent`가 모든 파싱 및 주입을 오케스트레이션합니다:

```python
# 기존 (Deprecated)
parser = GeminiPDFParser()
result = parser.parse("report.pdf")
loader = Neo4jKGLoader()
loader.load_knowledge_graph(result["knowledge_graph"])

# 신규 (Orchestrator)
agent = KGConstructionAgent()
agent.construct_knowledge_graph(auto_scan=True)
```

### Gemini Native PDF Parser 우선
PDF 파싱은 Gemini PDF Native Parser를 우선 사용:
- ✅ 원스텝 파이프라인 (PDF → KG 직접 추출)
- ✅ Structured Output 지원
- ✅ Batch API 지원 (50% 비용 절감)

VLM Enhanced Parser는 특수한 케이스에만 사용 예정

## 참고 문서
- [Orchestrator Architecture](../docs/implementation_logs/orchestrator_architecture.md)
- [Implementation Log](../docs/implementation_logs/implementation_log.md)
