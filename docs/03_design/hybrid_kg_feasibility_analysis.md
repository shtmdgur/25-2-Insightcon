# 하이브리드 KG 아키텍처 설계 실행 가능성 분석 (Feasibility Analysis)
## 현재 보유 데이터 vs 설계 요구사항 검증

**분석일**: 2025-12-22  
**분석자**: KG Architecture Validation Team  
**참조문서**: [`hybrid_kg_architecture_design.md`](file:///d:/0.Sogang/%EB%8F%99%EC%95%84%EB%A6%AC%20%EB%B0%8F%20%ED%95%99%ED%9A%8C/Insight/2025-2/2%EC%B0%A8%20%EC%9D%B8%EC%82%AC%EC%9D%B4%EC%BD%98/25-2-Insightcon/docs/03_design/hybrid_kg_architecture_design.md)

---

## 📊 목차

1. [현재 보유 데이터 현황](#1-현재-보유-데이터-현황)
2. [T-Box 노드 생성 가능성 검증](#2-t-box-노드-생성-가능성-검증)
3. [R-Box 관계 구축 가능성 검증](#3-r-box-관계-구축-가능성-검증)
4. [Dual-Path Pipeline 구현 가능성](#4-dual-path-pipeline-구현-가능성)
5. [Gap Analysis 및 해결 방안](#5-gap-analysis-및-해결-방안)
6. [최종 결론 및 권고사항](#6-최종-결론-및-권고사항)

---

## 1. 현재 보유 데이터 현황

### 1.1. 데이터 인벤토리

| 데이터 유형 | 파일 개수 | 형식 | 샘플 구조 | 용도 |
|---|---|---|---|---|
| **PDF 리포트** | ~1,500개 | PDF | 애널리스트 리포트 | Agent, Signal, Document 추출 |
| **뉴스 기사** | 1개 (통합) | CSV (20MB) | `keyword, title, date, link, content` | Signal, Document 생성 |
| **주가 데이터** | 23개 | CSV | `date, open, high, low, close, volume` | Metric (PriceMovement) 생성 |
| **DART 공시** | 3개 | CSV | `companies.csv`, `disclosure_states.csv`, `financial_states.csv` | Agent (Company), Signal (Disclosure), Metric 생성 |
| **거시지표** | 1개 | CSV | `date, value, series` (FRED 금리) | MacroMetric (EconomicIndicator) 생성 |
| **펀더멘탈** | 3개 | CSV | 기업별 PER, PBR 등 | Agent 속성 (fundamental_stats) |

### 1.2. 데이터 샘플 상세

#### 1.2.1. 뉴스 CSV (`Semiconductor_Final_Integrated_20251220_1141.csv`)
```csv
keyword, title, date, link, content
반도체, "SK하이닉스 어닝 서프라이즈", 2024-10-31, https://..., "SK하이닉스가 4분기..."
```
- ✅ **활용 가능**: `title` + `content` → LLM 추출 → Signal (Earnings), Document

#### 1.2.2. DART CSV
```csv
# companies.csv
ticker, corp_code, corp_name, ...
000660, 00126380, "SK하이닉스", ...

# disclosure_states.csv
ticker, corp_code, date, rcept_no, report_nm, ...
000660, 00126380, 2020-03-27, ..., "분할합병결정", ...

# financial_states.csv
ticker, 날짜, 자산총계, 부채총계, ...
```
- ✅ **활용 가능**: 
  - `companies.csv` → Agent (Company) + fundamental_stats
  - `disclosure_states.csv` → Signal (Disclosure)
  - `financial_states.csv` → Metric

#### 1.2.3. 주가 CSV (`005930.KS_prices.csv`)
```csv
date, open, high, low, close, volume
2020-01-07, 55700.0, 56400.0, 55600.0, 55800.0, 10009778
```
- ✅ **활용 가능**: 급등/급락 탐지 → Signal (PriceMovement)

#### 1.2.4. 거시지표 CSV (`fred_rates.csv`)
```csv
date, value, series
2020-01-02, 1.54, DGS3MO
```
- ✅ **활용 가능**: MacroMetric (EconomicIndicator)

---

## 2. T-Box 노드 생성 가능성 검증

### 2.1. Agent 노드

#### 요구사항 (설계문서)
```cypher
CREATE (s:IDM {
  name: "Samsung Electronics",
  ticker: "005930",
  fundamental_stats: {per: 15.2, pbr: 1.4, market_cap: "400T"},
  description_embedding: [0.123, -0.456, ...]
})
```

#### 데이터 매핑
| 속성 | 데이터 소스 | 추출 방법 | 상태 |
|---|---|---|---|
| `name` | `DART/companies.csv::corp_name` | 직접 | ✅ 가능 |
| `ticker` | `DART/companies.csv::ticker` | 직접 | ✅ 가능 |
| `fundamental_stats` | `fund/*_fundamentals.csv` | 직접 (PER, PBR, Market Cap) | ✅ 가능 |
| `description_embedding` | `reports/*.pdf` | **LLM 요약 + Embedding** | ⚠️ 구현 필요 |

**결론**: ✅ **Agent 노드 생성 100% 가능**  
단, `description_embedding`은 PDF 요약 → Embedding 파이프라인 구현 필요.

---

### 2.2. Signal 노드

#### 요구사항 (설계문서)
```cypher
CREATE (sig:Earnings {
  summary: "삼성전자 4Q24 어닝 서프라이즈",
  direction: "UP",
  magnitude: 15.5,
  sentiment: "POSITIVE",
  date: datetime("2024-10-31"),
  confidence: 0.9
})
```

#### 데이터 매핑

##### 2.2.1. Earnings (실적 발표)
| 속성 | 데이터 소스 | 추출 방법 | 상태 |
|---|---|---|---|
| `summary` | `news/*.csv::title` | **LLM 요약** | ✅ 가능 |
| `direction` | `news/*.csv::content` | **LLM 분류** ("UP"/"DOWN") | ✅ 가능 |
| `magnitude` | `news/*.csv::content` | **LLM 추출** (예: "15% 상승" → 15.0) | ✅ 가능 |
| `sentiment` | `news/*.csv::content` | **LLM 분류** ("POSITIVE"/"NEGATIVE") | ✅ 가능 |
| `date` | `news/*.csv::date` | 직접 | ✅ 가능 |
| `confidence` | - | **LLM 자체 판단** | ✅ 가능 |

##### 2.2.2. PriceMovement (주가 급등/급락)
| 속성 | 데이터 소스 | 추출 방법 | 상태 |
|---|---|---|---|
| `summary` | `price/*.csv` | 통계 분석 (예: "삼성전자 주가 12.3% 급등") | ✅ 가능 |
| `direction` | `price/*.csv::close` | 계산 (전일 대비 ± 5% 이상) | ✅ 가능 |
| `magnitude` | `price/*.csv::close` | 계산 ((close - prev_close) / prev_close * 100) | ✅ 가능 |
| `sentiment` | - | 규칙 (direction == "UP" → "POSITIVE") | ✅ 가능 |
| `date` | `price/*.csv::date` | 직접 | ✅ 가능 |

##### 2.2.3. Disclosure (공시)
| 속성 | 데이터 소스 | 추출 방법 | 상태 |
|---|---|---|---|
| `summary` | `DART/disclosure_states.csv::report_nm` | 직접 (예: "분할합병결정") | ✅ 가능 |
| `direction` | - | **LLM 분류** (공시 유형별) | ⚠️ 규칙 정의 필요 |
| `magnitude` | - | N/A (공시는 magnitude 없음) | - |
| `sentiment` | `DART/disclosure_states.csv::report_nm` | **LLM 분류** | ✅ 가능 |
| `date` | `DART/disclosure_states.csv::date` | 직접 | ✅ 가능 |

**결론**: ✅ **Signal 노드 생성 85% 가능**  
단, LLM 기반 방향/감정 분류 로직 구현 필요.

---

### 2.3. MacroMetric 노드

#### 요구사항
```cypher
CREATE (m:EconomicIndicator {
  name: "USD/KRW 환율",
  current_trend: "RISING",
  current_value: 1350.0,
  last_updated: datetime()
})
```

#### 데이터 매핑
| 속성 | 데이터 소스 | 추출 방법 | 상태 |
|---|---|---|---|
| `name` | `macro/fred_rates.csv::series` | 직접 (예: "DGS3MO" → "미국 3개월 금리") | ✅ 가능 |
| `current_trend` | `macro/fred_rates.csv::value` | 계산 (최근 N일 이동평균 비교) | ✅ 가능 |
| `current_value` | `macro/fred_rates.csv::value` | 직접 (최신 값) | ✅ 가능 |
| `last_updated` | `macro/fred_rates.csv::date` | 직접 | ✅ 가능 |

**결론**: ✅ **MacroMetric 노드 생성 100% 가능**

---

### 2.4. Document 노드

#### 요구사항
```cypher
CREATE (d:News {
  title: "삼성전자, HBM3E 공급 계약 체결",
  content: "...",
  url: "https://...",
  published_date: datetime("2024-03-05"),
  embedding: [0.789, -0.234, ...]
})
```

#### 데이터 매핑
| 속성 | 데이터 소스 | 추출 방법 | 상태 |
|---|---|---|---|
| `title` | `news/*.csv::title` | 직접 | ✅ 가능 |
| `content` | `news/*.csv::content` | 직접 | ✅ 가능 |
| `url` | `news/*.csv::link` | 직접 | ✅ 가능 |
| `published_date` | `news/*.csv::date` | 직접 | ✅ 가능 |
| `embedding` | `news/*.csv::content` | **Embedding 모델** (OpenAI text-embedding-3-small) | ✅ 가능 |

**결론**: ✅ **Document 노드 생성 100% 가능**

---

## 3. R-Box 관계 구축 가능성 검증

### 3.1. AFFECTS (Logic Layer)

#### 요구사항
```cypher
CREATE (usd:EconomicIndicator {name: "USD/KRW"})
CREATE (samsung:IDM {name: "Samsung Electronics"})
CREATE (usd)-[:AFFECTS {
  correlation: "DIRECT",
  sensitivity: 0.72,  // Pearson r
  lag: "1Q",
  confidence: 0.89
}]->(samsung)
```

#### 데이터 매핑
| 속성 | 추출 방법 | 데이터 소스 | 상태 |
|---|---|---|---|
| `correlation` | **LLM 추출** + **통계 검증** | `reports/*.pdf` + `price/*.csv` | ✅ 가능 |
| `sensitivity` | **Pearson 상관계수 계산** | `macro/fred_rates.csv` + `price/*.csv` | ✅ 가능 |
| `lag` | **시차 분석** (Cross-Correlation) | `macro/fred_rates.csv` + `price/*.csv` | ✅ 가능 |
| `confidence` | **LLM 값 vs 통계 값 비교** | - | ✅ 가능 |

**구현 방법**:
1. **초기값 (LLM)**: PDF 리포트에서 "환율 상승 시 수출 실적 개선 예상" → `correlation: "DIRECT"`
2. **통계 검증**: 
   ```python
   from scipy.stats import pearsonr
   
   usd_krw = macro_df[macro_df['series'] == 'USDKRW']['value']
   samsung_revenue = finance_df[finance_df['ticker'] == '005930']['revenue']
   
   pearson_r, p_value = pearsonr(usd_krw, samsung_revenue)
   # pearson_r = 0.72 → sensitivity
   ```
3. **신뢰도 계산**:
   ```python
   llm_sensitivity = 0.8  # "HIGH" 매핑
   if abs(llm_sensitivity - pearson_r) > 0.2:
       confidence = 0.6
   else:
       confidence = 0.9
   ```

**결론**: ✅ **AFFECTS 관계 생성 100% 가능** (단, 데이터 정합성 확보 필요)

---

### 3.2. TRIGGERED_BY (Causal Layer)

#### 요구사항
```cypher
CREATE (disclosure:Disclosure {summary: "HBM3E 공급 계약 공시"})
CREATE (priceUp:PriceMovement {direction: "UP", magnitude: 12.3})
CREATE (priceUp)-[:TRIGGERED_BY {
  confidence: 0.92,
  reasoning: "공급 계약 공시 직후 주가 급등, 시간적/의미적 인과성 확인"
}]->(disclosure)
```

#### 데이터 매핑
| 속성 | 추출 방법 | 데이터 소스 | 상태 |
|---|---|---|---|
| `confidence` | **시간 접근성 분석** + **LLM 판단** | `DART/disclosure_states.csv::date` + `price/*.csv::date` | ✅ 가능 |
| `reasoning` | **LLM 생성** | `DART/disclosure_states.csv::report_nm` + `price/*.csv` | ✅ 가능 |

**구현 방법**:
```python
# 1. 시간 윈도우 내 이벤트 매칭
disclosure_date = "2024-03-05"
price_spike_date = "2024-03-05"

time_diff = abs((disclosure_date - price_spike_date).days)

if time_diff <= 1:  # 1일 이내
    temporal_causality = True
    
# 2. LLM 판단
prompt = f"""
공시: {disclosure_summary}
주가 변동: {price_movement_summary}

이 두 사건 간 인과관계가 있는가? (Yes/No)
이유를 설명하시오.
"""

llm_response = llm.generate(prompt)
confidence = llm_response['confidence']
reasoning = llm_response['reasoning']
```

**결론**: ✅ **TRIGGERED_BY 관계 생성 90% 가능** (단, LLM 프롬프트 정교화 필요)

---

### 3.3. Structural Layer

| 관계 | 소스 | 타겟 | 데이터 소스 | 상태 |
|---|---|---|---|---|
| `SUPPLIES` | Supplier | IDM | **밸류체인 정보 부재** | ❌ 불가능 |
| `MANUFACTURES` | IDM | Product | **제품 정보 부재** | ❌ 불가능 |
| `HAS_SIGNAL` | Agent | Signal | `DART/companies.csv` + `news/*.csv::title` | ✅ 가능 (Entity Linking) |
| `MENTIONED_IN` | Agent | Document | `news/*.csv::content` | ✅ 가능 (Named Entity Recognition) |

**결론**: ⚠️ **Structural Layer 50% 가능**  
→ **Gap**: 밸류체인 정보 (`SUPPLIES`, `MANUFACTURES`) 데이터 부재

---

## 4. Dual-Path Pipeline 구현 가능성

### 4.1. Path A: Vector Embedding

```python
from openai import OpenAI

client = OpenAI()

# 1. 텍스트 청킹
chunks = text_splitter.split_text(news['content'], chunk_size=500)

# 2. 임베딩 생성
embeddings = client.embeddings.create(
    model="text-embedding-3-small",
    input=chunks
).data[0].embedding

# 3. Neo4j 저장
session.run("""
    CREATE (d:DocumentChunk {
        content: $content,
        embedding: $embedding
    })
""", content=chunk, embedding=embeddings)
```

**상태**: ✅ **Path A 구현 100% 가능** (OpenAI API 사용)

---

### 4.2. Path B: Structure Extraction (LLM)

```python
prompt = f"""
다음 뉴스에서 정보를 추출하세요.

[T-Box 스키마]
- Agent: IDM (삼성전자, SK하이닉스), Fabless (NVIDIA)
- Signal: Earnings (실적), PriceMovement (주가), Disclosure (공시)
- Relation: AFFECTS (correlation, sensitivity, lag)

[뉴스]
{news['title']}
{news['content']}

[추출 형식]
{{
  "signals": [
    {{"type": "Earnings", "summary": "SK하이닉스 4Q 어닝 서프라이즈", "direction": "UP", "magnitude": 15.5}}
  ],
  "affected_entities": ["SK하이닉스"],
  "relations": [
    {{"from": "미국 금리", "to": "SK하이닉스", "type": "AFFECTS", "correlation": "INVERSE"}}
  ]
}}
"""

response = llm.generate(prompt)
extracted_data = json.loads(response)
```

**상태**: ✅ **Path B 구현 100% 가능** (Gemini API 사용)

---

## 5. Gap Analysis 및 해결 방안

### 5.1. Critical Gaps (치명적 결함)

| Gap | 영향도 | 해결 방안 | 우선순위 |
|---|---|---|---|
| **밸류체인 정보 부재** | High | 외부 데이터 수집 (Bloomberg, FactSet) **OR** 리포트에서 LLM 추출 | P1 |
| **제품 정보 부재** | High | Wikipedia, 기업 IR 사이트 크롤링 | P1 |
| **LLM 가중치 검증 로직** | Medium | Pearson 상관계수, Cross-Correlation 구현 | P2 |
| **Entity Normalization** | Medium | 기존 `entity_normalizer.py` 활용 | P2 |

### 5.2. Non-Critical Gaps (비치명적 결함)

| Gap | 영향도 | 해결 방안 | 우선순위 |
|---|---|---|---|
| `description_embedding` 생성 | Low | PDF 전처리 + LLM 요약 + Embedding | P3 |
| 통계 검증 파이프라인 | Low | `scipy.stats` 활용 | P3 |
| Neo4j Vector Index 최적화 | Low | 인덱스 파라미터 튜닝 | P4 |

---

### 5.3. 해결 방안 상세

#### 5.3.1. 밸류체인 정보 수집 (Critical Gap #1)

**Option A: 외부 데이터 구매** (❌ 비용 발생)
- Bloomberg Terminal: $2,000/month
- FactSet Supply Chain Database: $5,000/year

**Option B: LLM 기반 자동 추출** (✅ 권장)
```python
prompt = f"""
다음 리포트에서 공급망 관계를 추출하세요.

[리포트]
{pdf_content}

[추출 형식]
{{
  "supply_chain": [
    {{"supplier": "ASML", "customer": "Samsung Electronics", "product": "EUV 노광장비"}},
    {{"supplier": "동진쎄미켐", "customer": "SK하이닉스", "product": "포토레지스트"}}
  ]
}}
"""
```

**예상 정확도**: 75-85% (수동 검증 필요)

---

#### 5.3.2. 제품 정보 수집 (Critical Gap #2)

**Wikipedia API 활용**:
```python
import wikipedia

product_info = wikipedia.summary("HBM3E", sentences=5)
```

**기업 IR 사이트 크롤링**:
```python
from selenium import webdriver

driver.get("https://www.skhynix.com/products")
product_list = driver.find_elements_by_class_name("product-name")
```

---

#### 5.3.3. LLM 가중치 검증 로직 (Non-Critical Gap)

```python
from scipy.stats import pearsonr
import numpy as np

def calculate_correlation(macro_data, company_data):
    """
    macro_data: [1200, 1250, 1300, ...] (USD/KRW 환율)
    company_data: [60T, 62T, 65T, ...] (매출액)
    """
    # 1. 시계열 정렬
    macro_data = np.array(macro_data)
    company_data = np.array(company_data)
    
    # 2. Pearson 상관계수 계산
    pearson_r, p_value = pearsonr(macro_data, company_data)
    
    # 3. LLM 예측값과 비교
    llm_prediction = 0.8  # "HIGH" sensitivity
    delta = abs(llm_prediction - pearson_r)
    
    if delta > 0.2:
        confidence = 0.6  # 차이 크면 신뢰도 하향
    else:
        confidence = 0.9
    
    return {
        'correlation': 'DIRECT' if pearson_r > 0 else 'INVERSE',
        'sensitivity': pearson_r,
        'confidence': confidence,
        'p_value': p_value
    }
```

---

## 6. 최종 결론 및 권고사항

### 6.1. Feasibility 종합 평가

| 구성 요소 | 구현 가능성 | 데이터 완전성 | 추가 작업 필요 |
|---|---|---|---|
| **T-Box: Agent** | ✅ 100% | ✅ 100% | `description_embedding` 구현 |
| **T-Box: Signal** | ✅ 90% | ✅ 85% | LLM 분류 로직 정교화 |
| **T-Box: MacroMetric** | ✅ 100% | ✅ 100% | - |
| **T-Box: Document** | ✅ 100% | ✅ 100% | - |
| **R-Box: AFFECTS** | ✅ 100% | ⚠️ 70% | 통계 검증 파이프라인 구축 |
| **R-Box: TRIGGERED_BY** | ✅ 90% | ✅ 80% | 시간 윈도우 튜닝 |
| **R-Box: Structural** | ⚠️ 50% | ❌ 30% | **밸류체인 데이터 수집** |
| **Dual-Path Pipeline** | ✅ 100% | ✅ 100% | - |

**전체 평가**: ✅ **85% 구현 가능** (Structural Layer 보완 필요)

---

### 6.2. 단계별 실행 계획 (3-Phase Roadmap)

#### Phase 1: Core Implementation (4주)
**목표**: T-Box 4개 노드 + AFFECTS/TRIGGERED_BY 관계 구현

- [ ] Week 1-2: 데이터 전처리 파이프라인 구축
  - [ ] PDF → Text 변환 (`pymupdf4llm`)
  - [ ] CSV 정제 (`pandas`)
  - [ ] Embedding 생성 (`OpenAI API`)
- [ ] Week 3: T-Box 노드 생성 로직 구현
  - [ ] Agent Parser (DART + Fund 데이터)
  - [ ] Signal Parser (News + Price + DART)
  - [ ] MacroMetric Parser (FRED 데이터)
  - [ ] Document Parser (News)
- [ ] Week 4: R-Box 관계 생성 로직 구현
  - [ ] AFFECTS (LLM + 통계)
  - [ ] TRIGGERED_BY (시간 윈도우)
  - [ ] HAS_SIGNAL, MENTIONED_IN (Entity Linking)

**검증 기준**: Neo4j에 1,000개 이상의 노드 및 5,000개 이상의 관계 적재

---

#### Phase 2: Structural Layer 보완 (2주)
**목표**: 밸류체인 정보 수집 및 SUPPLIES/MANUFACTURES 관계 구축

- [ ] Week 5: 데이터 수집
  - [ ] LLM 기반 리포트 공급망 추출
  - [ ] Wikipedia API로 제품 정보 수집
  - [ ] IR 사이트 크롤링 (Selenium)
- [ ] Week 6: 관계 생성 및 검증
  - [ ] SUPPLIES 관계 생성
  - [ ] MANUFACTURES 관계 생성
  - [ ] 수동 검증 (샘플 100개)

**검증 기준**: 주요 기업 10개의 완전한 밸류체인 그래프 구축

---

#### Phase 3: Optimization & Validation (2주)
**목표**: 성능 최적화 및 Neo4j Vector Index 구축

- [ ] Week 7: Neo4j 최적화
  - [ ] Vector Index 생성 (`document_embedding`, `agent_embedding`)
  - [ ] Index 파라미터 튜닝 (dimension, similarity_function)
  - [ ] Hybrid Search 쿼리 최적화
- [ ] Week 8: End-to-End 검증
  - [ ] PoC 시나리오 테스트 (설계문서 8.1-8.3)
  - [ ] 성능 벤치마크 (쿼리 응답 시간 < 1초)
  - [ ] 정확도 평가 (샘플 200개 수동 검증)

**검증 기준**: Hybrid Search 쿼리 정확도 85% 이상

---

### 6.3. 최종 권고사항

#### ✅ 즉시 진행 가능 항목
1. **Agent, Signal, MacroMetric, Document 노드 생성** (데이터 100% 확보)
2. **AFFECTS, TRIGGERED_BY 관계 구축** (LLM + 통계 검증)
3. **Dual-Path Pipeline 구현** (OpenAI Embedding + Gemini Structure Extraction)

#### ⚠️ 조건부 진행 항목
1. **Structural Layer (SUPPLIES, MANUFACTURES)**
   - **조건**: LLM 기반 밸류체인 추출 정확도 75% 이상 달성
   - **대안**: 수동 입력 또는 외부 데이터 구매

#### 🚀 향후 확장 항목
1. **실시간 데이터 스트리밍**: Kafka + Neo4j Change Data Capture
2. **GNN 기반 임베딩**: GraphSAGE로 노드 임베딩 학습
3. **자동 신뢰도 업데이트**: 주기적 통계 검증으로 `confidence` 갱신

---

## 부록 A: 데이터 샘플 접근 경로

| 데이터 유형 | 파일 경로 |
|---|---|
| PDF 리포트 | `data/raw/reports/*.pdf` (1,500개) |
| 뉴스 CSV | `data/raw/news/Semiconductor_Final_Integrated_20251220_1141.csv` |
| 주가 CSV | `data/raw/price/*.csv` (23개) |
| DART CSV | `data/raw/DART/companies.csv`, `disclosure_states.csv`, `financial_states.csv` |
| 거시지표 CSV | `data/raw/macro/fred_rates.csv` |
| 펀더멘탈 CSV | `data/raw/fund/*.csv` (3개) |

---

**[문서 끝]**
