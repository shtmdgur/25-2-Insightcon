# PR: Knowledge Graph Schema Integration & Data Flow Refactoring

## 📋 Summary

Knowledge Graph 시스템의 스키마를 통합하고 데이터 플로우를 개선하여 PDF 파싱부터 Neo4j 주입까지의 전체 파이프라인을 안정화했습니다.

## 🎯 Main Objectives

1. ✅ **스키마 통합**: `graph_schema.py`와 `nodes.py` 통합 → `nodes.py` 단일 스키마로 표준화
2. ✅ **JSON 중간 저장**: PDF 파싱 결과를 JSON으로 저장하여 재처리 및 병합 가능
3. ✅ **중복 제거 로직**: `KGMerger` 구현으로 여러 문서의 KG 병합 및 중복 제거
4. ✅ **Gemini API 호환성**: 커스텀 JSON 스키마로 Gemini API 제약사항 해결
5. ✅ **통합 테스트**: 전체 파이프라인 검증을 위한 테스트 스위트 구축

## 🔧 Key Changes

### 1. Schema Integration (`src/models/nodes.py`)

**통합 작업:**
- `NodeType`에 `TECHNOLOGY`, `PERSON` 추가
- `RelationType`에 `PRODUCES`, `COMPETES_WITH`, `SUPPLIES_TO`, `AFFECTED_BY`, `DEVELOPS`, `LEADS` 추가
- `graph_schema.py` → `src/models/deprecated/` 이동

**Gemini API 호환성:**
```python
# 커스텀 JSON 스키마 작성 (빈 object 에러 해결)
def get_kg_json_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "entities": [...],  # properties 필드 제외
            "relations": [...]  # metadata 필드 제외
        }
    }
```

**Enum 타입 처리:**
```python
class Config:
    use_enum_values = False  # JSON 로드 시 Enum 유지
```

### 2. Data Flow Refactoring

**새로운 플로우:**
```
PDF → GeminiPDFParser → JSON (data/processed/) → KGMerger → Neo4j
```

**구현:**
- `GeminiPDFParser.parse()`: 자동 JSON 저장 (`{filename}_{timestamp}.json`)
- `KGMerger`: 여러 JSON 파일 병합 및 중복 제거
  - Entity 병합: `name + type` 기준, properties 병합, max confidence
  - Relation 병합: `subject + predicate + object` 기준, max weight, source 연결
- `Neo4jKGLoader.load_from_json_files()`: JSON → Neo4j 주입

### 3. Test Suite (`test/test_integration.py`)

**5개 통합 테스트:**
1. ✅ Schema Conversion (nodes.py ↔ Gemini API)
2. ✅ JSON Save/Load
3. ✅ KGMerger (중복 제거)
4. ✅ Gemini PDF Parser (JSON 자동 저장)
5. ✅ Full Pipeline (PDF → Neo4j)

**실행 결과:**
```
Total Nodes: 250
Total Relationships: 228
✅ All tests passed!
```

### 4. Prompt Enhancement (`src/templates/prompts.yaml`)

**엔티티 명명 규칙 추가:**
- 회사: "삼성전자 (005930)"
- 제품: "DRAM [DDR5 8Gb]"
- 기술: "EUV [7nm]"
- 지표: "매출액 [2024Q1]"

**효과:** Neo4j Browser에서 엔티티 식별 용이

## 📁 Files Changed

### Created (9 files)
- `src/dataflows/kg_merger.py` - KG 병합 및 중복 제거
- `test/test_integration.py` - 통합 테스트 스위트
- `test/README.md` - 테스트 가이드
- `data/processed/README.md` - JSON 저장 디렉토리 설명
- `src/models/deprecated/README.md` - 스키마 통합 히스토리
- `src/models/deprecated/graph_schema.py` - 이전 스키마 (백업)
- 기타 Phase 1 파일들

### Modified (6 files)
- `src/models/nodes.py` - 스키마 통합 + Gemini API 최적화
- `src/dataflows/parsers/gemini_pdf.py` - JSON 자동 저장
- `src/dataflows/neo4j_loader.py` - JSON 로드 및 UPSERT 전략
- `src/templates/prompts.yaml` - 엔티티 명명 규칙 추가
- `test/test_gemini_pdf_neo4j.py` - nodes.py 스키마 적용
- `docs/implementation_logs/implementation_log.md` - 작업 내역 업데이트

## 🐛 Issues Resolved

### Issue 1: Gemini API Schema Validation Error
**문제:**
```
400 INVALID_ARGUMENT
- metadata.properties: should be non-empty for OBJECT type
- entities.items.properties["properties"].properties: should be non-empty
```

**해결:**
- Pydantic 자동 생성 스키마 대신 커스텀 스키마 작성
- `properties`와 `metadata` 필드를 스키마에서 제외

**트레이드오프:**
- ❌ Entity 추가 속성 손실 (ticker, industry 등)
- ✅ Gemini API 호환성 확보
- ✅ 프롬프트 개선으로 이름에 식별 정보 포함 ("삼성전자 (005930)")

### Issue 2: Enum Type Serialization
**문제:** JSON 저장 시 Enum이 문자열로 변환되어 로드 시 `.value` 접근 불가

**해결:**
```python
class Config:
    use_enum_values = False  # Enum 유지
```

### Issue 3: Schema Method Mismatch
**문제:** `to_gemini_dict()`는 구 포맷(`label`), `from_gemini_dict()`는 신 포맷(`type`) 사용

**해결:** 두 메서드를 커스텀 스키마에 맞게 동기화

## 🧪 Testing

### Manual Testing
```bash
# 통합 테스트 실행
poetry run python test/test_integration.py

# 선택: 6 (모두 실행)
```

### Neo4j Verification
```cypher
# 중복 노드 확인 (없어야 함)
MATCH (n)
WITH n.name as name, labels(n)[0] as label, count(*) as cnt
WHERE cnt > 1
RETURN name, label, cnt

# 전체 통계
MATCH (n) RETURN count(n) as total_nodes
MATCH ()-[r]->() RETURN count(r) as total_relationships
```

## 📊 Impact

### Performance
- ✅ JSON 중간 저장으로 재처리 시간 단축 (API 재호출 불필요)
- ✅ 병합 로직으로 중복 데이터 제거

### Maintainability
- ✅ 단일 스키마(`nodes.py`)로 유지보수 간소화
- ✅ 테스트 스위트로 회귀 방지

### Data Quality
- ✅ 중복 제거로 데이터 일관성 향상
- ✅ UPSERT 전략으로 데이터 누적 가능

## 🔜 Next Steps

1. **CSV Parser 구현** - 가격, DART, 매크로 데이터 파싱
2. **Entity Normalizer 고도화** - Master data 기반 속성 보강
3. **LLM Router 구현** - 데이터 타입별 자동 라우팅
4. **Phase 1 Agent 통합** - KGConstructionAgent 리팩토링

## 📝 Notes

- Neo4j Aura에 250개 노드, 228개 관계 정상 주입 확인
- 커스텀 스키마로 인한 `properties` 손실은 프롬프트 개선으로 보완
- 모든 테스트 통과 확인

## 👥 Reviewers

@team - 스키마 통합 및 데이터 플로우 검토 요청

---

**Related Issues:** #N/A
**Related PRs:** #N/A
