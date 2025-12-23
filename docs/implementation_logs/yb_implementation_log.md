# 구현 작업 내역 (Validator & Report Refinement)

> **최종 업데이트**: 2024-12-23 (Phase 3.2: 리포트 시각화 고도화 및 품질 개선)
> **작업 범위**: Report Formatter 도입, NetworkX 그래프, 한글 폰트 문제 해결, 피드백 반영

---

## 📋 목차

- [Phase 3.2: 리포트 시각화 고도화 및 품질 개선](#phase-32-리포트-시각화-고도화-및-품질-개선)
- [Phase 3.1: 리포트 신뢰성 및 안전성 강화](#phase-31-리포트-신뢰성-및-안전성-강화)
- [주요 변경 내용 상세](#주요-변경-내용-상세)
- [검증 및 테스트](#검증-및-테스트)
- [생성/수정 파일 목록](#생성수정-파일-목록)

---

# Phase 3.2: 리포트 시각화 고도화 및 품질 개선

## 개요
리포트 생성 파이프라인에 **전문적인 포맷팅**, **시각화 강화**, **한글 폰트 문제 해결**을 적용했습니다. Jinja2 템플릿 엔진과 한화투자증권 스타일 리포트 포맷을 도입하여 보고서 품질을 대폭 향상시켰습니다.

---

## 주요 변경 내용 상세

### 1. Report Formatter 도입 ✅
**파일**: `src/utils/report_formatter.py`, `src/templates/hanwha_securities_template.md`
**내용**:
- **HanwhaSecuritiesReportFormatter 클래스** 구현
  - Jinja2 템플릿 엔진 기반 리포트 생성
  - 투자의견, 목표주가, 신뢰도 자동 추출
  - 재무 데이터 자동 포맷팅 (조원, 원 단위)
- **템플릿 구조**:
  - Executive Summary (단일, 중복 제거)
  - Investment Thesis (Bull/Bear 주장 포함)
  - Financial Analysis (Mock 데이터 명시)
  - Data Visualization (4종 차트 임베딩)
  - References & Provenance (Impact Paths 표시)

### 2. 시각화 강화 ✅
**파일**: `src/utils/visualizer.py`
**내용**:
- **기존 차트 개선**:
  - `plot_debate_score()`: 토론 점수 비교 (Horizontal Bar)
  - `plot_radar_chart()`: 5가지 핵심 경쟁력 레이더 차트
  - `plot_financial_trend()`: 매출/영업이익률 이중축 차트
- **신규 차트 추가**:
  - `plot_network_graph()`: **NetworkX 기반 엔티티 관계망 그래프**
    - Impact Paths를 노드와 엣지로 파싱
    - Spring layout 알고리즘 적용
    - 시각적으로 지식 그래프 관계 표현

### 3. 한글 폰트 문제 해결 ✅
**변경 사항**:
- **시도 1**: `Malgun Gothic` 폰트 명시적 설정 + `font_manager` 활용
  - 결과: Windows 폰트 캐싱 이슈로 여전히 깨짐 발생
- **최종 해결**: 모든 차트 레이블을 **영어로 전환**
  - "AI 토론 점수 비교" → "AI Debate Score Comparison"
  - "Bull vs Bear 핵심 경쟁력" → "Bull vs Bear Core Competitiveness"
  - "분기별 실적 추이" → "Quarterly Performance Trend"
  - "핵심 엔티티 관계망" → "Key Entity Relationship Network"

### 4. 피드백 반영 (GPT/Gemini 리뷰) ✅
**변경 파일**: `hanwha_securities_template.md`, `report_formatter.py`, `synthesizer_agent.py`
**개선 사항**:
- ✅ Executive Summary 중복 제거
- ✅ AI Pipeline 방법론 명시 (NOTE 블록)
- ✅ Mock 데이터 명시 (CAUTION 경고)
- ✅ 단위 오류 수정 (억원 → 조원)
- ✅ 차트 자동 생성 안내 (TIP 블록)

---

## 검증 및 테스트

### 1. 통합 테스트 (`test/test_mid_end_pipeline.py`)
- **목적**: Bull/Bear Debate → Judge → Synthesizer → Report 전체 파이프라인 검증
- **결과**:
  - 4종 차트 자동 생성 (`data/outputs/charts/`)
  - 한화투자증권 스타일 리포트 생성 (`final_report_test_mid_end.md`)
  - Impact Paths 정상 표시
  - Bull/Bear 주장 체계적으로 정리됨

### 2. 시각화 검증
- **생성된 차트**:
  - `debate_score.png`: 영어 레이블로 정상 표시 ✓
  - `debate_radar.png`: 영어 레이블로 정상 표시 ✓
  - `financial_trend.png`: 영어 레이블로 정상 표시 ✓
  - `network_graph.png`: NetworkX 그래프 정상 생성 ✓

---

## 생성/수정 파일 목록

### Phase 3.2에서 생성된 파일 (2개)
1. `src/utils/report_formatter.py`: 한화투자증권 스타일 리포트 생성기
2. `src/templates/hanwha_securities_template.md`: Jinja2 템플릿 (NOTE/CAUTION/TIP 블록 포함)

### Phase 3.2에서 수정된 파일 (3개)
1. `src/utils/visualizer.py`:
   - `plot_network_graph()` 메서드 추가
   - 모든 차트 레이블 영어 전환
   - 폰트 설정 강화 (font_manager 활용)
2. `src/agents/synthesizer_agent.py`:
   - `HanwhaSecuritiesReportFormatter` 통합
   - NetworkX 그래프 경로 전달
   - Mock 데이터 단위 명시 (조원)
3. `src/templates/prompts.yaml`:
   - Synthesizer 프롬프트를 "분석 콘텐츠만 생성"으로 변경
   - 포맷팅은 Formatter가 담당하도록 분리

---

# Phase 3.1: 리포트 신뢰성 및 안전성 강화

## 개요
기존의 `SynthesizerAgent`가 판결과 작성을 동시에 수행하던 구조를 **"판결(Judge) -> 작성(Synthesizer) -> 검증(Validator)"**의 3단계 파이프라인으로 분리했습니다. 이를 통해 리포트의 논리적 객관성을 확보하고, LLM의 환각(Hallucination)을 방지하며, 전문적인 증권사 스타일의 포맷을 강제했습니다.

---

## 주요 변경 내용 상세

### 1. Validator Agent (신설) ✅
**파일**: `src/agents/validator_agent.py`
**내용**:
- **역할**: Synthesizer가 작성한 리포트의 **Fact Check** 및 **Style Check** 담당.
- **검증 항목**:
  1. **Hallucination**: 토론 내역(Context)에 없는 수치나 사실을 창작했는지 여부.
  2. **Data Gaps**: 데이터가 없을 때 이를 솔직하게 `(확인 필요)`로 표시했는지 여부.
  3. **Style**: 증권사 리포트 톤앤매너(건조한 문체, 두괄식 등) 준수 여부.
- **출력**: JSON 형식 (`{"decision": "pass" | "fail", "feedback": "..."}`)

### 2. Judge & Synthesizer 역할 분리 ✅
**파일**: `src/agents/judge_agent.py`, `src/agents/synthesizer_agent.py`
**내용**:
- **JudgeAgent**:
  - 純粋 Decision Maker. 매수/매도 여부(`verdict`)와 핵심 논거(`rationale`)만 결정.
  - 리포트의 문구 작성에는 관여하지 않음 (객관성 유지).
- **SynthesizerAgent**:
  - 純粋 Writer. Judge의 판결을 입력(`state['judge_verdict']`)으로 받아 포맷팅만 수행.
  - 본인의 의견을 섞지 않고 Judge의 `rationale`을 그대로 인용.
  - Mermaid Diagram 및 Markdown Table 작성 기능 추가.

### 3. Prompt Engineering (Anti-Hallucination) ✅
**파일**: `src/templates/prompts.yaml`
**내용**:
- **Strict Constraints 추가**:
  - `DO NOT FABRICATE DATA`: 없는 수치는 절대 지어내지 말 것.
  - `Mark as (확인 필요)`: 데이터 공백 시 명시적인 플레이스홀더 사용 규칙.
- **Visual Thinking**:
  - Mermaid.js 문법 예시 제공 (논리적 인과관계 시각화).
  - Markdown Table 포맷 강제.
- **Localization**:
  - 한국어 증권 리포트 스타일 가이드라인(어조, 용어) 적용.

---

## 검증 및 테스트

### 1. 기본 파이프라인 검증 (`test/test_judge_manual.py`)
- **목적**: Judge -> Synthesizer -> Validator의 순차적 실행 및 데이터 전달 확인.
- **결과**:
  - Judge의 판결이 Synthesizer 프롬프트로 정확히 전달됨.
  - Synthesizer가 생성한 리포트에서 환각이 없을 경우 Validator가 **PASS** 판정을 내림.
  - 최종 결과물 `final_report_test.md` 생성 성공.

### 2. 신규 데이터 수용성 검증 (`test/test_new_data_flow.py`)
- **목적**: 새로운 회사(SK Hynix)와 반대 의견(SELL)이 입력되었을 때 시스템이 유연하게 반응하는지 확인.
- **결과**:
  - Prompt Inspection 결과, Judge의 새로운 판결(SELL)이 Synthesizer에게 정확히 주입됨을 확인.
  - "Target Company: SK Hynix", "Verdict: SELL" 확인 완료.

### 3. 성능 비교 (Before vs After) (`test/compare_performance.py`)
- **목적**: 안전장치 도입 전후의 리포트 품질 비교.
- **결과**:
  - **Before**: 데이터 공백 시 "2.5조원 매출" 등 허위 사실 창작(Hallucination).
  - **After**: "데이터 확인 필요"로 명시하고 Validator가 이를 승인함. 신뢰성 대폭 향상.

---

## 생성/수정 파일 목록

### Phase 3.1에서 생성된 파일 (4개)
1. `src/agents/validator_agent.py`: 검증 에이전트 구현체.
2. `test/test_new_data_flow.py`: 신규 시나리오 검증 스크립트.
3. `test/compare_performance.py`: 성능 비교(Before/After) 스크립트.
4. `final_report_test.md`: 최종 리포트 결과 샘플.

### Phase 3.1에서 수정된 파일 (5개)
1. `src/agents/__init__.py`: ValidatorAgent export 추가.
2. `src/agents/synthesizer_agent.py`: Judge Verdict 참조 로직 및 Mermaid/Table 구현 추가.
3. `src/agents/judge_agent.py`: Rationale 출력 강화.
4. `src/pipeline/debate_workflow.py`: Validator 노드 추가 및 워크플로우 연결.
5. `src/templates/prompts.yaml`: Validator, Synthesizer 프롬프트 고도화.
