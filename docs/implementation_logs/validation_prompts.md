# 코드 및 작업 검증 프롬프트 예시

## 1. 전체 시스템 아키텍처 검증

```
현재 구현된 시스템을 다음 관점에서 검증해주세요:

1. **아키텍처 일관성**
   - T/R Box 2.0 온톨로지가 모든 파서와 로더에서 일관되게 사용되는가?
   - 이중 레이어 전략 (Static MERGE / Dynamic CREATE)이 올바르게 구현되었는가?
   - 14개 동적 타입이 실제로 CREATE로, 44개 정적 타입이 MERGE로 처리되는가?

2. **데이터 흐름 검증**
   - PDF → Gemini API → KnowledgeGraph → Neo4j 파이프라인이 끊김없이 작동하는가?
   - Entity Normalizer가 모든 파서 결과에 적용되는가?
   - Time-Decay 가중치가 Event 관계에 올바르게 적용되는가?

3. **프롬프트 관리**
   - 모든 LLM 호출이 prompts.yaml을 사용하는가?
   - 하드코딩된 프롬프트가 남아있지 않은가?
   - Ontology schema가 prompts.yaml과 nodes.py 사이에 동기화되어 있는가?

검증 파일:
- src/models/nodes.py
- src/dataflows/neo4j_loader.py
- src/parsers/gemini_pdf.py
- src/utils/event_extractor.py
- src/templates/prompts.yaml
```

---

## 2. Neo4j 데이터 적재 검증

```
Neo4j 그래프 데이터베이스의 데이터 품질을 검증해주세요:

1. **노드 분류 확인**
   - Static 노드 (Company, Product 등)가 ID 기준으로 MERGE되고 있는가?
   - Dynamic 노드 (Observation, Event, Metric)가 period/date 포함 ID로 CREATE되는가?
   - 중복 노드가 생성되지 않았는가? (같은 Company가 여러 개 등)

2. **시간 속성 필수성**
   - 모든 Dynamic 노드에 period 또는 date 속성이 있는가?
   - TemporalRegion 노드들이 올바르게 생성되었는가?
   - Time-Scoped ID가 적용되었는가? (예: "Year-end_Shopping_Season_2024Q4")

3. **관계 품질**
   - recordedAt, observes 관계가 Observation 노드에 제대로 연결되었는가?
   - AFFECTS 관계에 time_decay 가중치가 있는가?
   - 고아 노드 (관계가 없는 노드)가 있는가?

Cypher 쿼리 예시:
```cypher
// 동적 노드 중 period/date 없는 것 찾기
MATCH (n)
WHERE n:Event OR n:Metric OR n:Observation
  AND NOT EXISTS(n.period) AND NOT EXISTS(n.date)
RETURN labels(n), n.id, properties(n) LIMIT 10

// 중복 Company 노드 찾기  
MATCH (c:Company)
WITH c.name as company_name, count(*) as cnt
WHERE cnt > 1
RETURN company_name, cnt
ORDER BY cnt DESC
```
```

---

## 3. Parser 결과물 품질 검증

```
각 Parser의 출력 품질을 검증해주세요:

1. **GeminiPDFParser**
   - Entity의 properties가 비어있지 않은가?
   - Ticker가 name이 아닌 properties에 저장되는가?
   - 관계 수가 엔티티 수의 최소 80% 이상인가?
   - Observation 노드가 제대로 생성되는가?

2. **PriceParserAgent**
   - SAX-DM 패턴이 올바르게 생성되는가?
   - Trend 노드에 period 속성이 있는가?
   - Trend classification (Upward/Downward/Volatile/Stable)이 작동하는가?

3. **NewsParserAgent / EventExtractor**
   - 이벤트 추출이 prompts.yaml에서 로드된 프롬프트를 사용하는가?
   - Time-decay 가중치가 계산되는가?
   - Event 노드에 date 속성이 필수로 들어가는가?

검증 방법:
- 각 Parser의 테스트 파일 실행
- 출력 JSON 검사
- Neo4j 통계 확인
```

---

## 4. 코드 일관성 및 스타일 검증

```
코드베이스의 일관성을 검증해주세요:

1. **Import 구조**
   - 순환 참조가 없는가?
   - 모든 import가 절대 경로로 통일되어 있는가?
   - 사용하지 않는 import는 없는가?

2. **에러 처리**
   - 모든 API 호출 (Gemini, Neo4j)에 try-except가 있는가?
   - Circuit Breaker 패턴이 적용되어야 할 곳에 적용되었는가?
   - 에러 메시지가 명확한가?

3. **타입 힌팅**
   - 모든 함수에 타입 힌팅이 있는가?
   - Pydantic 모델이 올바르게 사용되고 있는가?
   - Optional, Union 등이 적절히 사용되는가?

4. **설정 관리**
   - 하드코딩된 설정값이 없는가?
   - 모든 설정이 config 파일에서 관리되는가?
   - 환경 변수가 적절히 사용되는가?

검증 도구:
- mypy (타입 체크)
- pylint (코드 스타일)
- pytest (단위 테스트)
```

---

## 5. 성능 및 비용 검증

```
시스템의 성능과 비용 효율성을 검증해주세요:

1. **LLM 사용 최적화**
   - Batch API가 적절한 곳에 사용되고 있는가?
   - Quick 모델과 Deep 모델이 용도에 맞게 분리되어 있는가?
   - 불필요한 LLM 호출이 없는가?

2. **Neo4j 쿼리 최적화**
   - 인덱스가 필요한 속성 (id, period, date)에 생성되었는가?
   - MERGE 쿼리가 효율적으로 작성되었는가?
   - 대량 데이터 주입 시 UNWIND를 사용하는가?

3. **캐시 전략**
   - GraphRAG 쿼리 결과가 캐시되는가?
   - 캐시 무효화가 Graph 업데이트 시 작동하는가?
   - Gemini Files API 캐시가 작동하는가?

4. **비용 추정**
   - 1000개 PDF 처리 시 예상 비용은?
   - Batch API 사용 시 절감 효과는?
   - Neo4j Aura 사용량은 적정한가?
```

---

## 6. 통합 테스트 프롬프트 (E2E)

```
전체 파이프라인을 End-to-End로 테스트해주세요:

시나리오: 삼성전자 분석 리포트 생성

1. **데이터 수집**
   - PDF 리포트 1개 파싱
   - 주가 데이터 (최근 3개월) 파싱
   - 뉴스 데이터 (최근 1개월) 파싱

2. **KG 구축**
   - 3개 파서 결과를 KGMerger로 병합
   - Entity Normalizer로 엔티티 통합
   - Neo4j에 주입

3. **검증 포인트**
   - 삼성전자 노드가 1개만 생성되었는가?
   - Event 노드들이 날짜별로 구분되어 있는가?
   - Trend 노드가 기간별로 생성되었는가?
   - 모든 Metric이 period 속성을 가지는가?

4. **조회 테스트**
   - "삼성전자의 2024년 매출은?" 쿼리 성공?
   - "최근 1개월 긍정적 이벤트는?" 쿼리 성공?
   - Multi-hop: "삼성전자 → DRAM → SK하이닉스" 경로 찾기

5. **리포트 생성**
   - Bull/Bear 토론이 작동하는가?
   - Synthesizer가 근거를 제시하는가?
   - PDF Export가 한화 스타일로 생성되는가?

테스트 스크립트:
```python
# test/integration/test_e2e_samsung.py
def test_samsung_analysis_pipeline():
    # 1. 데이터 파싱
    pdf_result = gemini_pdf_parser.parse("samsung_report.pdf")
    price_result = price_parser.parse("005930")
    news_result = news_parser.parse("삼성전자")
    
    # 2. KG 병합 및 주입
    merged_kg = kg_merger.merge([pdf_result, price_result, news_result])
    load_stats = neo4j_loader.load(merged_kg)
    
    # 3. 검증
    assert load_stats["static_nodes"] > 0
    assert load_stats["dynamic_nodes"] > 0
    
    # 4. 쿼리
    result = query_agent.run("삼성전자의 최신 재무 상황은?")
    
    # 5. 리포트
    report = debate_workflow.run("삼성전자")
    assert "Bull Argument" in report
    assert "Bear Argument" in report
```
```

---

이 프롬프트들을 사용하여 각 영역별로 체계적으로 검증할 수 있습니다.
