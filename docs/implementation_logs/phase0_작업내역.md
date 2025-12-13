# Phase 0 작업 내역

## 완료된 작업

### 0.1 LLM Config Setup ✓
**파일**: `src/utils/llm_config.py`  
**내용**:
- Quick/Deep 모델 매핑 (gemini-2.5-flash / gemini-3-pro-preview)
- Batch API 설정 (enabled, max_batch_size, polling_interval)
- 작업 유형별 모델 매핑 (`TASK_MODEL_MAPPING`)
- `get_model_config()`, `should_use_batch()` 함수

---

### 0.2 Parser Interface ✓
**파일**: `src/dataflows/parser_interface.py`  
**내용**:
- `ParserInterface` 추상 클래스
- `RobustPDFParser` 클래스 (Fallback 메커니즘)
- Primary → Secondary → Fallback 순서 자동 전환
- `ParserStrategy` Enum (PRIMARY, SECONDARY, FALLBACK)

---

### 0.3 Files API Integration ✓
**파일**: `src/utils/gemini_files.py`  
**내용**:
- `GeminiFilesClient` 클래스
- `upload_file()`: 파일 업로드 및 URI 반환
- `get_file_uri()`: 캐시된 URI 조회
- `delete_file()`, `clear_cache()`: 캐시 관리
- 싱글톤 패턴 (`get_gemini_files_client()`)

---

### 0.4 VLM Parser (Media-First) ✓
**파일**: `src/dataflows/parsers/vlm.py`  
**내용**:
- `VLMParser` 클래스 (`ParserInterface` 구현)
- Media-First Prompting (파일 URI 먼저 배치)
- PDF 차트 분석 및 JSON 파싱
- Fallback: JSON 파싱 실패 시 raw text 반환

---

### 0.5 State Definition 확장 ✓
**파일**: `src/pipeline/state.py`  
**변경사항**:
- `parsed_text`, `file_uri`, `extracted_charts` 추가
- `fundamental_analysis`, `trend_analysis`, `event_analysis` 추가
- `bull_argument`, `bear_argument`, `synthesis_verdict` 추가
- `retry_count`, `debate_turn_count`, `critical_paths` 추가
- `kg_updates`, `news_events` 추가
- `report_type` 타입 변경: `str` → `Literal["scan", "deep"]`

---

## 생성된 파일 목록
1. `src/utils/llm_config.py`
2. `src/dataflows/__init__.py`
3. `src/dataflows/parsers/__init__.py`
4. `src/dataflows/parser_interface.py`
5. `src/utils/gemini_files.py`
6. `src/dataflows/parsers/vlm.py`

## 수정된 파일 목록
1. `src/pipeline/state.py`

---

## 다음 단계
Phase 1: Knowledge Graph Update 시작
