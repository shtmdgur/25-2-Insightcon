# 금융 Knowledge Graph RAG 시스템 고도화 구현 작업

## Phase 0: Foundation (Parser & Ontology)
- [x] 0.1 **LLM Config Setup**
  - [x] `src/utils/llm_config.py` 생성 (Quick/Deep 모델 매핑)
  - [x] Batch API 설정 추가
  
- [x] 0.2 **Parser Interface**
  - [x] `src/dataflows/parser_interface.py` 생성
  - [x] Fallback 메커니즘 구현 (Primary → Secondary → Fallback)
  
- [x] 0.3 **Files API Integration**
  - [x] `src/utils/gemini_files.py` 생성
  - [x] Upload 및 URI 캐싱 로직 구현
  
- [x] 0.4 **VLM Parser (Media-First)**
  - [x] `src/dataflows/parsers/vlm.py` 생성
  - [x] Image-First Prompting 구현
  
- [x] 0.5 **State Definition 확장**
  - [x] `src/pipeline/state.py` 수정
  - [x] 새로운 필드 추가 (parsed_text, file_uri, debate 관련 등)

---

## Phase 1: Knowledge Graph Update
- [x] 1.1 **Ontology Models**
  - [x] `src/models/nodes.py` 생성
  - [x] Pydantic Entity/Relation 모델 정의 (Enum 사용)
  
- [x] 1.2 **KG Extract Logic 개선**
  - [x] `src/agents/kg_construction.py` 수정
  - [x] Seed Ontology 기반 추출로 변경
  
- [x] 1.3 **Batch API Job**
  - [x] `src/utils/batch_job.py` 생성
  - [x] JSONL Create → Submit → Poll 로직 구현
  
- [x] 1.4 **Neo4j Inject 업데이트**
  - [x] `src/utils/neo4j_client.py` 수정
  - [x] `inject_subgraph` 메서드 추가
  
- [x] 1.5 **Entity Normalizer**
  - [x] `src/utils/entity_normalizer.py` 생성
  - [x] Fuzzy Matching, Semantic Search 구현
  
- [x] 1.6 **Time Series Processor**
  - [x] `src/utils/time_series_processor.py` 생성
  - [x] SAX 패턴 변환 및 Neo4j 저장
  
- [x] 1.7 **Event Extractor**
  - [x] `src/utils/event_extractor.py` 생성
  - [x] 뉴스 → Event 노드 추출 및 Time-decay 적용
  
- [ ] 1.8 **Integration Test (Phase 1 E2E)**
  - [ ] PDF → Files API → Batch Job → Neo4j 저장 테스트

---

## Phase 2: Intelligence Upgrade (Multi-Agent)
- [ ] 2.1 **Prompt Templates**
  - [ ] `templates/prompts.yaml` 생성
  - [ ] Analyst, Debate 프롬프트 정의
  
- [ ] 2.2 **Analyst Agents 구현**
  - [ ] `src/agents/analysts/fundamentals_analyst.py` 생성
  - [ ] `src/agents/analysts/trend_analyst.py` 생성
  - [ ] `src/agents/analysts/event_analyst.py` 생성
  
- [ ] 2.3 **Debate Agents 구현**
  - [ ] `src/agents/debate/bull_agent.py` 생성
  - [ ] `src/agents/debate/bear_agent.py` 생성
  
- [ ] 2.4 **Synthesizer 구현**
  - [ ] `src/agents/debate/synthesizer.py` 생성
  - [ ] 변증법적 통합 로직 구현
  
- [ ] 2.5 **Quality Check Agent 강화**
  - [ ] `src/agents/quality_check.py` 수정
  - [ ] Fact-checking, Relevance Scoring 추가
  
- [ ] 2.6 **Multi-hop GraphRAG**
  - [ ] `src/pipeline/multi_hop_graphrag.py` 생성
  - [ ] 1-Hop, 2-Hop 확장 로직 구현
  
- [ ] 2.7 **LangGraph Flow 재구성**
  - [ ] `src/pipeline/graph.py` 수정
  - [ ] Analysts (병렬) → Debate (순차) → Synthesizer 흐름 구현
  - [ ] Loop Limit (최대 3라운드) 조건부 엣지 추가
  
- [ ] 2.8 **Nodes 래퍼 업데이트**
  - [ ] `src/pipeline/nodes.py` 수정
  - [ ] Analysts, Debate 노드 래퍼 추가

---

## Phase 3: Robustness & Validation
- [ ] 3.1 **Retry Decorator**
  - [ ] `src/utils/retry_handler.py` 생성
  - [ ] Tenacity 기반 `@retry_on_llm_error` 데코레이터 구현
  - [ ] 모든 LLM 호출 노드에 적용
  
- [ ] 3.2 **Loop Control**
  - [ ] `src/pipeline/graph.py` 수정
  - [ ] `route_after_qc`, `route_debate`에 카운트 체크 로직 추가
  
- [ ] 3.3 **Test Suite 작성**
  - [ ] Unit Tests 작성 (각 Phase별)
  - [ ] Integration Tests 작성
  - [ ] E2E Tests 작성
  
- [ ] 3.4 **Final Manual Verification**
  - [ ] PDF Parsing 품질 검증
  - [ ] Neo4j 데이터 무결성 확인
  - [ ] Debate 품질 평가
  - [ ] Hallucination Check
