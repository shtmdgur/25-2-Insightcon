# 최종 스키마 v3.0

> **결정 사항**: 사용자 피드백 7개 항목 반영

---

## ⚠️ 스키마 사용 원칙

> **모든 예시와 옵션은 가이드라인일 뿐, 제약 조건이 아닙니다.**

1. **유연한 추출**: LLM은 문서에서 발견한 모든 관련 정보를 추출해야 합니다. 예시에 없는 정보라도 의미가 있다면 적절한 properties에 저장합니다.

2. **자유 텍스트 우선**: `description`, `lag`, `impact` 등은 자유 형식입니다. LLM이 문서의 맥락을 최대한 반영하여 기술합니다.

3. **properties 확장 가능**: 정의된 properties 외에도 문서에서 발견한 추가 정보는 `properties: {}` 딕셔너리에 자유롭게 추가합니다.

4. **타입 매핑 유연성**: 정확한 타입이 불분명할 경우 가장 가까운 타입을 선택하거나 `Organization`/`Issue`를 사용합니다.

---

## 1. NodeType (11개)

### Agent Layer (정적)
| Type | 설명 | 예시 (참고용) |
|------|------|--------------|
| `IDM` | 종합반도체 | 삼성전자, SK하이닉스, Intel |
| `Fabless` | 팹리스 | NVIDIA, Qualcomm, 리벨리온 |
| `Foundry` | 파운드리 | TSMC, DB하이텍 |
| `OSAT` ✨ | 후공정 | ASE, Amkor, 하나마이크론 |
| `Supplier` | 소부장 | ASML, 동진쎄미켐, 한미반도체 |
| `Organization` | 기타 조직 | 정부기관, 협회, 기타 |

### Signal Layer (동적)
| Type | 설명 | 추출 조건 (참고용) |
|------|------|-------------------|
| `Earnings` | 실적 시그널 | 어닝 서프라이즈/쇼크 등 |
| `PriceMovement` | 주가 변동 | 의미있는 움직임 (급등/급락 등) |
| `Disclosure` | 공시 | 시설투자, 자사주매입 등 |
| `Issue` | 이슈 통합 | 정책/리스크/기회/기타 모두 포함 |

### MacroMetric Layer
| Type | 설명 |
|------|------|
| `EconomicIndicator` | USD/KRW, 금리, 원자재 등 |

> ❌ **Document Layer 제거**: `News`, `Report` → `source` property로 대체

---

## 2. RelationType (8개)

### 기존 (5개)
| Type | 용도 |
|------|------|
| `AFFECTS` | 영향 관계 |
| `TRIGGERED_BY` | 인과 관계 |
| `SUPPLIES` | 공급망 |
| `MANUFACTURES` | 생산 |
| `HAS_SIGNAL` | 시그널 보유 |

### 신규 (3개) ✨
| Type | 용도 | 예시 |
|------|------|------|
| `COMPETES_WITH` | 경쟁 | 삼성전자 ↔ SK하이닉스 |
| `PARTNERS_WITH` | 협력/파트너 | NVIDIA → TSMC |
| `INVESTS_IN` | 투자/인수/지분 | 삼성 → 용인 클러스터, A가 B 인수 |

---

## 3. Entity Properties

### 공통
| Property | Type | 필수 | 전략 | 설명 |
|----------|------|------|------|------|
| `name` | str | ✅ | 정적 | 정규화된 이름 (MERGE 키) |
| `type` | NodeType | ✅ | 정적 | 노드 타입 |
| `date` | str | | 메타 | 데이터 발생/추출 날짜 (YYYY-MM-DD) |
| `confidence` | float | | 동적 | 추출 신뢰도 (0-1, 최신값 우선) |
| `source` | str | | 히스토리 | 출처 문서명 (배열 누적) |
| `embedding` | List[float] | | 동적 | **PDF/News만** (최신값 우선) |

**전략 범례**:
- 정적: 변경 불가/불필요 (최초값 유지)
- 동적: 날짜 비교 후 최신값만 저장
- 히스토리: 모든 변경 배열로 누적
- 메타: 갱신 기준 (비교용)

### Agent Layer
| Property | Type | 설명 |
|----------|------|------|
| `ticker` | str | 종목코드 |
| `fundamental_stats` | Dict | 재무 통계 |
| `technical_metric` | Dict | 기술 지표 (수율, 대역폭) |
| `market_metric` | Dict | 시장 지표 (점유율, PER/PBR) |
| `value_chain_stage` | str | 설계/전공정/후공정/테스트 |
| `location` | str | 물리적 위치 |

### Signal Layer
| Property | Type | 설명 |
|----------|------|------|
| `direction` | str | UP/DOWN/NEUTRAL |
| `magnitude` | float | 변동 크기 (%) |
| `sentiment` | str | POSITIVE/NEGATIVE/NEUTRAL |

#### PriceMovement 전용
| Property | Type | 설명 |
|----------|------|------|
| `is_significant` | bool | 의미있는 변동 |
| `relative_performance` | str | 시장 대비 성과 |
| `trigger` | str | 원인 이벤트 |

#### Issue (자유형식)
| Property | Type | 설명 |
|----------|------|------|
| `description` | str | LLM 자유형식 기술 |

---

## 4. Relation Properties

### 공통
| Property | Type | 전략 | 설명 |
|----------|------|------|------|
| `date` | str | 메타 | 관계 발생/추출 날짜 (YYYY-MM-DD) |
| `source` | str | 히스토리 | 출처 문서 (배열 누적) |
| `confidence` | float | 동적 | 추출 신뢰도 (최신값 우선) |

### AFFECTS
| Property | Type | 전략 | 설명 |
|----------|------|------|------|
| `correlation` | str | 히스토리 | DIRECT/INVERSE (변화 추적) |
| `sensitivity` | float | 히스토리 | 민감도 (0-1, 변화 추적) |
| `lag` | str | 히스토리 | 자유형식 (LLM 기술, 변화 추적) |

### TRIGGERED_BY
| Property | Type | 설명 |
|----------|------|------|
| `reasoning` | str | 인과 논리 |
| `impact` | str | **자유형식** (duration+lag 통합) |

### SUPPLIES
| Property | Type | 설명 |
|----------|------|------|
| `dependency` | float | 의존도 (0-1) |
| `is_critical` | bool | 핵심 공급망 |
| `supply_type` | str | 장비/소재/부품/설계IP 등 (자유형식) |
| `product` | str | 공급 품목명 (EUV 노광기, PR 등) |

### COMPETES_WITH ✨
| Property | Type | 설명 |
|----------|------|------|
| `market_segment` | str | 경쟁 시장 (HBM, 파운드리) |
| `competitive_dynamic` | str | 경쟁 양상 설명 |

### PARTNERS_WITH ✨
| Property | Type | 설명 |
|----------|------|------|
| `partnership_type` | str | 기술협력/생산위탁/JV |
| `scope` | str | 협력 범위 |

### INVESTS_IN ✨
| Property | Type | 설명 |
|----------|------|------|
| `investment_type` | str | M&A/지분투자/시설투자 |
| `amount` | str | 투자 규모 |
| `stake_percentage` | float | 지분율 (해당 시) |

---

## 5. Few-shot 예시 (리포트 기반)

### 예시 1: 삼성전자 4Q23 Review
```json
{
  "entities": [
    {"name": "삼성전자", "type": "IDM", "ticker": "005930"},
    {"name": "4Q23 메모리 출하량 급증", "type": "Earnings", "direction": "UP", "magnitude": 15.0}
  ],
  "relations": [
    {
      "subject": "4Q23 메모리 출하량 급증",
      "predicate": "TRIGGERED_BY",
      "object": "삼성전자",
      "reasoning": "공격적인 재고 소진 전략과 고객사 수요 회복",
      "impact": "단기 실적 개선, 1Q24까지 영향 지속 예상"
    }
  ]
}
```

### 예시 2: 500조 투자 발표
```json
{
  "entities": [
    {"name": "삼성전자", "type": "IDM"},
    {"name": "용인 반도체 클러스터", "type": "Issue", "description": "500조원 규모 10년간 투자 계획"}
  ],
  "relations": [
    {
      "subject": "삼성전자",
      "predicate": "INVESTS_IN",
      "object": "용인 반도체 클러스터",
      "investment_type": "시설투자",
      "amount": "500조원"
    },
    {
      "subject": "용인 반도체 클러스터",
      "predicate": "AFFECTS",
      "object": "원익IPS",
      "correlation": "DIRECT",
      "sensitivity": 0.8,
      "lag": "투자 집행 시점(2024년 이후)부터 순차적 수혜"
    }
  ]
}
```

---

## 변경 요약

| 항목 | 기존 | 최종 |
|------|------|------|
| NodeType | 13개 | **11개** (-News, -Report) |
| RelationType | 5개 | **8개** (+COMPETES_WITH, +PARTNERS_WITH, +INVESTS_IN) |
| Entity Props | 다수 | **정리됨** (Issue 자유형식) |
| Relation Props | 다수 | **간소화** (impact 통합, lag 자유형식) |
