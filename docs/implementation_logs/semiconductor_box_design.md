# 반도체 섹터 T-Box (Terminology Box) 고도화 설계안

## 1. 개요
본 문서는 BFO(Basic Formal Ontology)를 기반으로 대한민국 반도체 산업 및 금융 투자 분석에 최적화된 T-Box(Terminological Box) 설계를 기술합니다. 총 58개의 클래스와 21개의 관계로 구성되며, **한국 반도체 생태계의 특수성(IDM 중심, 소부장)**과 **증권 데이터 분석(Valuation, Consensus)**, 그리고 **인과관계 추론**을 반영했습니다.

## 2. 클래스 계층 구조 (Class Hierarchy: 58 Classes)

### 0. Root
- `SemiconductorEntity` (반도체 엔티티 ⊤)

### 1. Continuant (지속체) - 3D Entity
시간의 흐름 속에서도 동일성을 유지하며 실재하는 개체들입니다.

- **IndependentContinuant** (독립 지속체)
    - **Agent** (행동주체)
        - `OrganizationType` (조직 유형)
        - `Fabless` (팹리스: NVIDIA, Qualcomm, LX세미콘, 리벨리온)
        - `IDM` (종합반도체: **삼성전자**, **SK하이닉스**, Intel)
        - `Foundry` (위탁생산: TSMC, 삼성 파운드리, DB하이텍)
        - `OSAT` (후공정: ASE, Amkor, 하나마이크론, 두산테스나)
        - `SupplierOrganization` (소부장: ASML, 동진쎄미켐, 솔브레인, 한미반도체)
    - **PhysicalObject** (물리적 객체)
        - `Semiconductor` (반도체 제품)
        - `MemorySemiconductor` (DRAM, NAND, **HBM**)
        - `SystemSemiconductor` (CPU, GPU, NPU, AP)
        - `AnalogDevice` (PMIC, DDI, CIS)
        - `ProcessNode` (공정 노드: 3nm, 5nm, **GAA**, High-NA)
        - `PackagingTechnology` (패키징: **CoWoS**, HBM Stack, Chiplet)
    - **Location** (위치: 평택 캠퍼스, 용인 클러스터, 대만 신주)
- **Quality** (속성/품질)
    - `FinancialMetric` (재무지표: 매출, 영업이익, **CAPEX**, 현금흐름)
    - `TechnicalMetric` (기술지표: 수율, 전력효율, 대역폭, 적층단수)
    - `MarketMetric` (시장지표: **점유율**, **Valuation(PER/PBR)**, **Consensus**, 목표주가)
- **Role** (역할)
    - `ValueChainStage` (가치사슬단계: 설계, 전공정, 후공정, 테스트)
- **InformationObject** (정보 객체)
    - `FinancialReport` (사업보고서, 분기실적, 컨퍼런스콜)
    - `Patent` (특허)
    - `Policy` (정책: **K-칩스법**, CHIPS Act, 수출규제)
    - `TechnicalSpecification` (JEDEC 표준, 화이트페이퍼)

### 2. Occurrent (시간전개체) - 4D Entity
시간에 따라 전개되거나 발생하는 프로세스와 이벤트입니다 (금융 인과관계의 핵심).

- **Process** (프로세스)
    - `ManufacturingProcess` (제조 공정)
        - `FrontEndProcess` (전공정: 노광, 식각, 증착)
        - `BackEndProcess` (후공정: 본딩, 패키징, 테스트)
- **Event** (이벤트)
    - `StrategicAction` (전략: **감산**, M&A, 자사주매입, 투자발표)
    - `CorporateEvent` (기업사건: 어닝서프라이즈/쇼크, 경영진교체)
    - `MarketEnvironment` (시장환경: **AI 붐**, 원자재가격 변동, 금리)
    - `PolicyEvent` (정책이벤트: 보조금 확정, 제재 리스트 등재)
- **Observation** (관측/측정) **[NEW]**
    - `Observation` (e.g., "2024Q1 삼성전자 매출 측정", "3월 5일 주가 급등 기록")
    - *Note: Context-less Data(재무제표, 주가 등)를 Reification(객체화)하여 시간 및 주체와 연결하는 허브 역할*
- **TemporalRegion** (시간 영역)
    - `TemporalRegion` (e.g., 2024Q3, 2025H1, "차세대", 2024-03-05)

### 3. Risk & Opportunity (투자 분석 layer)
- `RiskFactor` (**위험요인**)
    - `GeopoliticalRisk` (지정학: 미중분쟁, 대만해협, 소부장 국산화 이슈)
    - `SupplyChainRisk` (공급망: 재고과잉, 리드타임 증가, 원자재 수급)
- `OpportunityFactor` (**기회요인**)
    - `OpportunityFactor` (e.g., AI 데이터센터 수요, 온디바이스 AI)

### 4. Other
- `Person` (주요 인물: CEO, CTO, 애널리스트)

---

## 3. R-Box (Relation Box) 설계 및 검증

RO(Relation Ontology)를 준수하며, 반도체 비즈니스 로직을 표현하는 21개의 핵심 관계를 정의합니다. 각 관계에 대해 Domain(주어)과 Range(목적어) 제약조건을 명시하여 논리적 정합성을 보장합니다.

### 3.1. R-Box 정의 (21 Relations)

#### A. 참여 및 역할 (Participation & Role)
| Relation Code | Label | Domain (Class) | Range (Class) | 설명 | 증권 분석 활용 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **participatesIn** | 참여한다 | `Agent` | `Occurrent` | 기업이 특정 사건/공정에 관여함 | 투자 발표, M&A 참여 |
| **hasRole** | 역할을 가진다 | `Continuant` | `Role` | 개체가 특정 역할을 수행함 | 파운드리/팹리스 구분 |
| **realizedBy** | 실현된다 | `Role` | `Process` | 역할이 실제 프로세스로 구현됨 | 파운드리 -> 위탁생산 공정 |

#### B. 생산 및 공급 (Production & Supply)
| Relation Code | Label | Domain (Class) | Range (Class) | 설명 | 증권 분석 활용 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **producedBy** | 생산되었다 | `PhysicalObject` | `Agent` | 제품의 제조사 | 시장 점유율 산출 기준 |
| **manufactures** | 제조한다 | `Agent` | `Semiconductor` | 기업이 특정 반도체를 생산함 | 제품 포트폴리오 분석 |
| **supplies** | 공급한다 | `SupplierOrganization` | `PhysicalObject` | 소부장 기업이 장비/재료 공급 | 공급망 의존도 분석 |
| **dependsOn** | 의존한다 | `Agent` | `Agent` | 기업 간의 비즈니스 의존성 | 밸류체인 리스크 분석 |
| **inValueChainStage** | 단계에 있다 | `Agent` | `ValueChainStage` | 기업의 가치사슬 위치 | 섹터 분류 (전공정/후공정) |

#### C. 구조 및 속성 (Structure & Quality)
| Relation Code | Label | Domain (Class) | Range (Class) | 설명 | 증권 분석 활용 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **hasPart** | 부분을 가진다 | `Continuant` | `Continuant` | 전체-부분 관계 (Transitive) | SoC 패키징 구조 분석 |
| **partOf** | 부분이다 | `Continuant` | `Continuant` | 부분-전체 관계 (Inverse) | 클러스터 내 공장 위치 |
| **hasQuality** | 특성을 가진다 | `SemiconductorEntity` | `Quality` | 개체의 속성 (수치/상태) | **PER, PBR, 수율 등 핵심지표** |
| **locatedAt** | 위치하다 | `Continuant` | `Location` | 물리적 위치 | 지정학적 리스크 노출 여부 |

#### D. 시간 및 인과 (Temporal & Causal)
| Relation Code | Label | Domain (Class) | Range (Class) | 설명 | 증권 분석 활용 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **precededBy** | 선행된다 | `Occurrent` | `Occurrent` | 시간적 순서 (Transitive) | 선행지표 -> 후행지표 예측 |
| **occursDuring** | ~동안 발생 | `Occurrent` | `TemporalRegion` | 시간적 포함 관계 | 분기 실적 매핑 (e.g., 4Q24) |
| **affects** | 영향을 미친다 | `Occurrent` | `SemiconductorEntity` | 인과적 영향 (Causal) | **호재/악재 이벤트 파급효과** |

#### E. 정보 및 리스크 (Info & Risk)
| Relation Code | Label | Domain (Class) | Range (Class) | 설명 | 증권 분석 활용 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **isAbout** | ~에 대한 | `InformationObject` | `SemiconductorEntity` | 정보의 대상 | 뉴스/리포트의 타겟 기업 식별 |
| **exposedTo** | 노출된다 | `SemiconductorEntity` | `RiskFactor` | 리스크 노출 상태 | **Risk Discount Valuation** |
| **benefitsFrom** | 이익을 얻는다 | `SemiconductorEntity` | `OpportunityFactor` | 기회 요인 활용 상태 | **Growth Potential Valuation** |

#### F. 관측 및 측정 (Observation & Measurement) **[NEW]**
*Context-less Data(재무제표, 주가 등)를 연결하기 위한 핵심 관계*

| Relation Code | Label | Domain (Class) | Range (Class) | 설명 | 증권 분석 활용 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **recordedAt** | ~에 기록됨 | `Observation` | `TemporalRegion` | 측정 시점 (타임스탬프) | **시계열 데이터 정렬 및 스티칭** |
| **observes** | 관측한다 | `Observation` | `SemiconductorEntity` | 관측 대상 (기업/제품) | 재무/주가 데이터 주체 연결 |
| **hasValue** | 값을 가진다 | `Observation` | `Literal`(Value) | 실제 측정값 (70조, 5%) | 정량 데이터 분석 |

---

### 3.2. 정합성 검증 (Validation Checklist)

**1. Domain/Range 일관성 검증**
- `participatesIn`의 Domain은 `Agent` (IndependentContinuant의 하위)이므로, T-Box의 `IndependentContinuant` 정의와 일치합니다.
- `affects`의 Domain은 `Occurrent` (Event/Process)이므로, "금리 인상(`MarketEnvironment`)이 주가(`MarketMetric`)에 영향을 미침"과 같은 진술이 논리적으로 성립합니다.

**2. BFO/RO 표준 준수 여부**
- `hasPart` / `partOf`: Transitive 성질을 가지며 Inverse 관계가 성립함을 확인했습니다.
- `precededBy`: 시간적 순서를 나타내며, 인과관계(`affects`)와는 구별됩니다 (선행한다고 반드시 원인은 아님).

**3. 반도체 도메인 적합성**
- **소부장 생태계**: `supplies`, `dependsOn` 관계를 통해, "ASML -> 삼성전자" 장비 공급 및 의존성을 표현할 수 있습니다.
- **투자 분석**: `hasQuality` (Valuation), `exposedTo` (Risk), `benefitsFrom` (Opportunity) 관계가 모두 포함되어 있어, 증권사 리포트의 논리 구조를 그래프로 완벽히 변환 가능합니다.

**판정 결과**: ✅ **PASS** (정의된 21개 관계는 T-Box 58개 클래스와 모순 없이 상호작용하며, 투자 분석 목적에 부합합니다.)


## 4. 시계열 데이터 처리 및 LLM 연동 전략 (Time-Series Handling)

### 4.1. 구조적 한계와 해결책: Observation Class 도입

기존의 `Subject -> Verb -> Object` (Triple) 방식으로는 "2024년 1분기 삼성전자 매출 70조"와 같이 시간에 따라 변하는 값을 표현하기 어렵습니다. 이를 해결하기 위해 **Measurement(측정값)** 또는 **Observation(관측)** 개념을 도입하여 데이터를 객체화(Reification)합니다.

#### N-ary 관계 모델링 구조
- **Node 1 (주체)**: `Samsung Electronics` (`Agent`)
- **Node 2 (사건/측정)**: `2024_Q1_Revenue_Report` (`Observation` or `Event`)
- **Node 3 (시간)**: `2024-03-31` (`TemporalRegion`)
- **Node 4 (값)**: `70조` (`Literal` via `hasValue`)

> **LLM 지시사항**: "이 엑셀 데이터의 각 행(Row)을 하나의 '이벤트'나 '관측(Observation)'으로 간주하고, 타임스탬프를 반드시 연결해라."

### 4.2. Time을 허브로 활용한 Graph Stitching (연결 전략)

맥락이 없는 비정형/반정형 데이터들을 엮는(Stitching) 유일한 단서는 **"동시간성(Simultaneity)"**과 **"선후관계(Sequence)"**입니다.

#### 시나리오: 서로 다른 출처의 데이터 연결
1. **데이터 A (뉴스)**: "2024년 3월 5일, 엔비디아 CEO, HBM3E 공급사로 SK하이닉스 언급"
2. **데이터 B (주가)**: "2024년 3월 5일, SK하이닉스 주가 5% 급등"
3. **데이터 C (공시)**: "2024년 3월 5일, SK하이닉스 신규 시설 투자 공시"

#### 연결 메커니즘
그래프 상에서 이들은 직접 연결되지 않지만, `2024-03-05`라는 `TemporalRegion` 노드를 공유하게 됩니다.

```mermaid
graph TD
    T[2024-03-05 (Time Hub)]
    
    E1[News Event: Nvidia CEO Speech] -->|occursDuring| T
    O1[Stock Observation: SK Hynix +5%] -->|recordedAt| T
    E2[Disclosure Event: CAPEX Plan] -->|occursDuring| T
    
    C[SK Hynix]
    C -->|participatesIn| E1
    C -->|observes| O1
    C -->|participatesIn| E2
    
    %% Implicit Inference
    E1 -.->|Infer: affects| O1
    E2 -.->|Infer: affects| O1
```

### 4.3. RAG 추론 프로세스 (Graph Inference)

1. **질문**: "SK하이닉스 주가 급등 원인이 뭐야?"
2. **검색 (Retrieval)**: 그래프에서 `SK하이닉스` + `주가 급등(Observation)` + `Time(2024-03-05)` 노드를 찾음.
3. **확장 (Expansion)**: `2024-03-05` 허브에 연결된 다른 노드(`Nvidia CEO Speech`, `CAPEX Plan`)를 조회함.
4. **추론 (Reasoning)**:
   - "직접적인 텍스트는 없지만, **동일 시점(2024-03-05)**에 엔비디아의 HBM3E 언급과 시설 투자가 있었습니다."
   - "이것이 주가 급등의 주요 원인으로 추정됩니다."

### 4.4. LLM 프롬프트 전략 (Schema Mapping)

데이터 주입 시 LLM에게 명확한 역할을 부여합니다.

**Prompt 예시**:
> "다음은 SK하이닉스의 분기 재무 데이터(CSV)다. 우리의 온톨로지 스키마에 맞춰 Triple로 변환해라.
> 규칙:
> 1. 각 분기('23.4Q')는 `TemporalRegion` 인스턴스로 생성하라.
> 2. '영업이익' 수치는 `FinancialMetric` 인스턴스로 만들지 말고, `Observation` 이벤트를 생성하여 연결하라.
> 3. `Observation`은 `SK Hynix`(observes)와 `TemporalRegion`(recordedAt) 양쪽에 반드시 연결되어야 한다."

## 5. 한국 반도체 섹터 및 금융 특화 적용 방안

### 5.1. 소부장 낙수효과 (Trickle-down Effect) 분석
- **Scenario**: 삼성전자가 300조원 용인 클러스터 투자 발표 (Event: `StrategicAction`)
- **Graph Path**:
  - 삼성전자 `participatesIn` 용인 클러스터 투자 (`StrategicAction`)
  - 용인 클러스터 투자 `affects` 설비 증설 (`ManufacturingProcess`)
  - 설비 증설 `requires` 장비 (`PhysicalObject`)
  - 장비 `producedBy` **원익IPS, 유진테크** (`SupplierOrganization`)
  - **Inference**: 삼성전자 투자 -> 소부장 기업(`SupplierOrganization`)의 매출(`FinancialMetric`) 증가 예상 (`OpportunityFactor`)

### 5.2. Valuation & Risk Analysis
- **HBM 밸류체인**:
  - 한미반도체 `supplies` TC본더 `dependsOn` SK하이닉스 `manufactures` HBM3E
  - SK하이닉스 `observes` PBR 2.0 (`Observation`) <-- `Infer` <-- HBM 점유율 확대
- **지정학적 리스크**:
  - `US_Chip_Interim_Rule` (`PolicyEvent`) --`affects`--> `Samsung_Xi_an_Fab` (`Location`)
  - `Samsung_Electronics` --`exposedTo`--> `China_Risk` (`GeopoliticalRisk`)
  - `China_Risk` --`affects`--> `Revenue` (`FinancialMetric`)

## 6. 구현 참조 사항
- `src/models/nodes.py`의 `NodeType` 및 `RelationType` Enum은 위 스키마와 1:1로 매핑되어야 합니다.
- LLM 프롬프트(`prompts.yaml`)에서 관계 추출 시 위 21개 관계 정의를 Few-shot 예제로 제공해야 정확도가 높아집니다.
