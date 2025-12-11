# Agent Spec Template

- Agent Name: 예: KGConstructionAgent
- Role: 문서에서 엔티티/관계를 추출하여 Neo4j에 주입하는 에이전트
- Constructor:
  - llm: LangChain LLM
  - neo4j_client: Neo4j 클라이언트
- 주요 메서드:
  - process_document(document: str) -> Dict[str, Any]
  - extract_entities(document: str) -> Dict[str, Any]
  - inject_to_neo4j(entities: Dict[str, Any]) -> Dict[str, int]
- 예시:
```python
class KGConstructionAgent:
    def __init__(self, llm, neo4j_client):
        ...
    def process_document(self, document: str) -> Dict[str, Any]:
        ...
```

