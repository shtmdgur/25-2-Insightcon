# Workflow Spec Template

- 전체 워크플로우 흐름: kg_construction -> quality_check -> (ontology_architect | graphrag_query) -> (sector_analyst | company_analyst) -> report_generation -> END
- 조건부 경로 예시:
  - Quality Check에서 이슈가 있으면 Ontology Architect로 라우팅
- 노드 간 데이터 전달 포맷:
  - state 객체(ReportState)에 의해 공유되는 필드들 예시
- 예시 시퀀스:
```
state = {
  "query": "...",
  "report_type": "...",
  "graphrag_results": {...},
  ...
}
```

