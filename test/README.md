# Test Suite

## 테스트 파일 목록

### 1. `test_integration.py` ⭐ **통합 테스트 (신규)**

스키마 통합 및 데이터 플로우 리팩토링 후 전체 파이프라인을 테스트합니다.

**테스트 항목:**
- ✅ **Test 1**: Schema Conversion (nodes.py ↔ Gemini API)
- ✅ **Test 2**: JSON Save/Load (KnowledgeGraph)
- ✅ **Test 3**: KGMerger (중복 제거)
- ✅ **Test 4**: Gemini PDF Parser (JSON 자동 저장)
- ✅ **Test 5**: Full Pipeline (PDF → JSON → Merge → Neo4j)

**실행:**
```bash
python test/test_integration.py
```

---

### 2. `test_gemini_pdf_neo4j.py` (업데이트됨)

Gemini PDF Parser와 Neo4j Loader를 테스트합니다.

**변경사항:**
- nodes.py 스키마로 업데이트
- JSON 자동 저장 확인 추가
- Entity/Relation 출력 포맷 수정

**실행:**
```bash
python test/test_gemini_pdf_neo4j.py
```

---

### 3. `test_phase0.py` (참고용)

Phase 0 기능 테스트 (LLM Config, Parser Interface, Gemini Files API).

---

### 4. `test_workflow.py` (참고용)

워크플로우 테스트.

---

## 테스트 실행 가이드

### 사전 준비

1. **환경변수 설정**
   ```bash
   # .env 파일에 추가
   GEMINI_API_KEY=your_api_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

2. **Neo4j 실행**
   ```bash
   # Docker로 실행
   docker run -d \
     --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:latest
   ```

3. **샘플 PDF 준비**
   `data/raw/reports/` 디렉토리에 테스트용 PDF 파일 배치

---

### 권장 테스트 순서

#### 1. 스키마 변환 테스트 (단위)
```bash
python test/test_integration.py
# 선택: 1 (Schema Conversion)
```

#### 2. JSON 저장/로드 테스트 (단위)
```bash
python test/test_integration.py
# 선택: 2 (JSON Save/Load)
```

#### 3. KGMerger 테스트 (단위)
```bash
python test/test_integration.py
# 선택: 3 (KGMerger)
```

#### 4. Gemini PDF Parser 테스트
```bash
python test/test_integration.py
# 선택: 4 (Gemini PDF + JSON)
```

#### 5. 전체 파이프라인 테스트 (통합)
```bash
python test/test_integration.py
# 선택: 5 (Full Pipeline + Neo4j)
```

#### 6. 모든 테스트 실행
```bash
python test/test_integration.py
# 선택: 6 (모두 실행)
```

---

## 검증 체크리스트

### ✅ Schema Conversion
- [ ] Entity: nodes.py ↔ Gemini API 변환 성공
- [ ] Relation: nodes.py ↔ Gemini API 변환 성공
- [ ] Properties: Dict ↔ JSON String 변환 성공

### ✅ JSON Save/Load
- [ ] KnowledgeGraph.save_to_json() 성공
- [ ] KnowledgeGraph.load_from_json() 성공
- [ ] Entities/Relations 수 일치
- [ ] Properties 내용 일치

### ✅ KGMerger
- [ ] 중복 Entity 제거 (name + type 기준)
- [ ] properties 병합 (나중 것 우선)
- [ ] confidence 최대값 선택
- [ ] 중복 Relation 제거 (subject + predicate + object)
- [ ] weight 최대값 선택

### ✅ Gemini PDF Parser
- [ ] PDF 업로드 성공
- [ ] Knowledge Graph 추출 성공
- [ ] JSON 자동 저장 (`data/processed/`)
- [ ] JSON 파일 로드 가능

### ✅ Neo4j Integration
- [ ] Neo4j 연결 성공
- [ ] 노드 생성 성공
- [ ] 관계 생성 성공
- [ ] 중복 노드 없음 (MERGE 전략)
- [ ] Graph Stats 조회 성공

---

## 트러블슈팅

### 1. GEMINI_API_KEY not found
```bash
# .env 파일 확인
cat .env | grep GEMINI_API_KEY
```

### 2. Neo4j connection failed
```bash
# Neo4j 실행 확인
docker ps | grep neo4j

# Neo4j 로그 확인
docker logs neo4j
```

### 3. No PDF files found
```bash
# PDF 파일 확인
ls -la data/raw/reports/*.pdf
```

### 4. JSON 파일 생성 안됨
```bash
# processed 디렉토리 확인
ls -la data/processed/

# 권한 확인
chmod -R 755 data/processed/
```

---

## 테스트 결과 예시

### 성공 예시
```
================================================================================
🧪 Integration Test Suite
================================================================================

[TEST 1: Schema Conversion]
✅ Schema conversion test passed!

[TEST 2: JSON Save/Load]
✅ JSON save/load test passed!

[TEST 3: KGMerger]
[Merged KG]: 3 entities, 2 relations
✅ KGMerger test passed!

[TEST 4: Gemini PDF Parser]
  Entities: 154
  Relations: 97
  JSON Path: data/processed/sample_report_20241214_180600.json
✅ Gemini PDF Parser test passed!

[TEST 5: Full Pipeline]
  Total Nodes: 154
  Total Relationships: 97
✅ Full pipeline test passed!

================================================================================
✅ Testing Complete!
================================================================================
```
