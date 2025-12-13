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

## 개선 사항 (2025-12-13 추가)

### VLM Parser 개선 ✓
**파일**: `src/dataflows/parsers/vlm_enhanced.py`  
**내용**:
- PyMuPDF4LLM 파싱 옵션 최적화 (`page_chunks=False`, `margins=(0,0,0,0)`, `dpi=150`)
- VLM 프롬프트 YAML 관리 (`templates/prompts.yaml`에서 로드)
- 금융 리포트 특화 차트 분석 (모든 텍스트/데이터 포인트 추출)

### Gemini Files API 개선 ✓
**파일**: `src/utils/gemini_files.py`  
**내용**:
- 한글 경로 지원 (파일 객체로 업로드)
- MIME 타입 자동 감지 (`mimetypes` 모듈)
- 파일 업로드 오류 수정 (`path` → `file` 파라미터)

### Prompts YAML 확장 ✓
**파일**: `src/templates/prompts.yaml`  
**내용**:
- VLM Parser 섹션 추가 (`vlm_parser.chart_analysis`)
- 금융 리포트 특화 프롬프트 (상세한 차트/표 분석 지침)

### 테스트 스크립트 개선 ✓
**파일**: `test/test_phase0.py`  
**내용**:
- Enhanced VLM Parser 테스트 추가 (옵션 6)
- MD 파일 자동 저장 기능
- 전체 텍스트 출력 옵션

---

## 다음 단계
Phase 1: Knowledge Graph Update 시작

