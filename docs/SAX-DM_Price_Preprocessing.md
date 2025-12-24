# SAX-DM: LLM을 위한 Price 데이터 전처리

## 개념: SAX-DM (Symbolic Aggregate approXimation - Direction & Magnitude)

> **시계열 → 심볼 시퀀스 변환** (LLM이 이해할 수 있는 형태)

LLM은 숫자(70,000 / 71,200 / 69,800…)의 미세한 변화를 잘 다루지 못함.
대신 이런 표현이 훨씬 이해하기 쉬움:
- "완만한 상승 추세 (Soft Uptrend)"
- "강한 하락과 높은 변동성 (Strong Down, High Volatility)"

---

## 계산 원리

### 1단계: Z-Score 정규화
```
z = (가격 - 평균) / 표준편차
```

### 2단계: Double Mean (이중 평균) 기준점 계산
```
μ         = 전체 평균
μ_lower   = 평균 이하 값들의 평균 (하단 평균)
μ_upper   = 평균 이상 값들의 평균 (상단 평균)
```

### 3단계: 심볼 할당

| Z 값 구간 | 심볼 | 의미 |
|----------|------|------|
| z ≤ μ_lower | **D2** | 강한 하락 (Down Strong) |
| μ_lower < z ≤ μ | **D1** | 약한 하락 (Down Mild) |
| μ < z ≤ μ_upper | **U1** | 약한 상승 (Up Mild) |
| z > μ_upper | **U2** | 강한 상승 (Up Strong) |

---

## 변환 파이프라인

```
[Raw Price]     52300 → 53100 → 54800 → 53200
       ↓ Z-Score 정규화
[Z-Score]       -0.8  → +0.3  → +1.5  → +0.1
       ↓ SAX-DM 심볼 할당
[Symbol]        D1    →  U1   →  U2   →  U1
       ↓ NLP Formatting
[LLM Context]   "SAX 패턴: 강한 상승 - 통계적으로 유의미한 변동"
```

---

## LLM Context 출력

### 일자별 조회
```
2024-01-15 기준, 005930.KS 시장 상황 요약:
- 주가: 78,000원 (전일 대비 +2.35%)
- SAX 패턴: 강한 상승 (Strong Uptrend) - Z-Score: 1.52
- 추세/변동성: 상승 추세 / 변동성 보통
```

### 기간별 패턴 분포 요약
```
[005930.KS] 2024-01-01 ~ 2024-01-31 기간 분석 (22일):
- 기간 수익률: +5.23%
- SAX 패턴 분포: U2: 8일, U1: 6일, D1: 5일, D2: 3일
- Z-Score 범위: -1.23 ~ 2.15
- 주요 추세: 상승 우위 (U 계열 14일 vs D 계열 8일)
```

---

## 장점 (vs 전통 SAX)

| 전통 SAX (a,b,c,d,e) | SAX-DM (U1,U2,D1,D2) |
|---------------------|----------------------|
| 의미 불명확 | **의미론적** (U=Up, D=Down) |
| 방향성만 표현 | **방향 + 강도** 동시 표현 |
| 고정 정규분포 구간 | **데이터 적응형** (Double Mean) |
| LLM 해석 필요 | **즉시 이해 가능** |

---

## 멀티에이전트 활용 예시

| Agent | 조회 패턴 | 활용 |
|-------|----------|------|
| **Bull** | `sax_symbol in [U1, U2]` + 상승 추세 | "강한 모멘텀, 매수 주장" |
| **Bear** | `volatility = High` + `zscore` 과열 | "단기 과열, 조정 가능성" |
| **Judge** | 기간별 패턴 분포 + 수익률 | 양측 논거 검증 |

---

## 참고
- 개념 문서: `docs/02_implementation/09_시계열.md`
- 구현 코드: `src/crawl/yfinance.py` (sax_dm 함수)
- Context 변환: `src/utils/price_data_loader.py`
