# 09_API_명세서

이 문서는 LangGraph 기반 멀티에이전트 워크플로우의 입력/출력 명세를 정리합니다.

1) 전체 흐름 개요
- 입력: 사용자의 질의(query), 대상 기업 목록(target_companies), 리포트 타입(report_type), 처리할 문서(document) 등
- 처리: KG 구성(KG_construction) → 품질 검사(quality_check) → 온톨로지 설계(ontology_architect) 및 GraphRAG 질의(graphrag_query) → 섹터/기업 분석 → 리포트 생성
- 출력: 최종 리포트(final_report) 및 실행 로그

2) 입력 데이터 모델 (Sample)
- query: "반도체 섹터의 최신 동향은?"
- target_companies: ["삼성전자", "SK하이닉스"]
- report_type: "all" 또는 "sector" 또는 "company"
- document: "/path/to/new/document.pdf" 또는 null

3) 출력 데이터 모델 (Sample State after 각 노드)
- kg_data: Neo4j 그래프 데이터 결과
- graphrag_results: GraphRAG 질의 결과
- sector_analysis: "마크다운 형식의 섹터 분석 리포트"
- company_analysis: {"삼성전자": "리포트 내용", "SK하이닉스": "리포트 내용"}
- final_report: 최종 결합된 리포트 텍스트
- errors, execution_trace, execution_times: 로깅/에러 추적 정보

4) 노드 인터페이스 요약
- kg_construction_node(state) -> state
- quality_check_node(state) -> state
- ontology_architect_node(state) -> state
- graphrag_query_node(state) -> state
- sector_analyst_node(state) -> state
- company_analyst_node(state) -> state
- report_generation_node(state) -> state

5) 에이전트 인터페이스 요약
- KGConstructionAgent(llm, neo4j_client).process_document(document) -> {"entities": ..., "stats": ...}
- QualityCheckAgent(neo4j_client).check(graph_data) -> {"issues": [...], "has_issues": bool, ...}
- OntologyArchitectAgent(llm, neo4j_client).generate_schema(templates) -> schema 정보 및 cypher
- SectorAnalystAgent(llm, graphrag_results).analyze(query, graphrag_results) -> str
- CompanyAnalystAgent(llm, graphrag_results).analyze_multiple(company_names, graphrag_results) -> Dict[str,str]
- 각 에이전트의 주요 메서드 시그니처는 위 주석에 명시

6) 에러/로깅 정책
- 각 노드 실행 시 로그를 _DEBUG_LOG_PATH에 남깁니다.
- 노드 실패 시 error 메시지를 state에 반영하고, 실행 흐름은 종료 또는 재시도/대체 경로를 선택합니다.

7) 샘플 시퀀스
```pseudo
입력: query, target_companies, document
kg_construction_node(state) -> state(kg_data)
quality_check_node(state) -> state(schema_issues)
ontology_architect_node(state) -> state(ontology_schema)
graphrag_query_node(state) -> state(graphrag_results)
sector_analyst_node(state) -> state(sector_analysis)
company_analyst_node(state) -> state(company_analysis)
report_generation_node(state) -> state(final_report)
```

