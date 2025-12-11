# Node Spec Template

- Node Name: 예: kg_construction
- Description: 이 노드는 문서를 받아 KG를 구성하는 에이전트 파이프라인의 한 단계입니다.
- Input (state: ReportState):
  - document: 문서 경로 또는 텍스트
  - query: 질의 문자열
  - target_companies: 대상 기업 목록
  - report_type: "sector" | "company" | "all"
- Output (state: ReportState):
  - kg_data 또는 schema_issues 등 워크플로우의 중간 상태 업데이트
- Dependencies:
  - KGConstructionAgent, Neo4jClient, LLM
- Example:
```python
@track_execution_time("kg_construction")
def kg_construction_node(state: ReportState) -> ReportState:
    ...
```

