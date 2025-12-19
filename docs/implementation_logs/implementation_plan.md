# 반도체 T-Box Schema 구현 계획

User가 요청한 57개 클래스와 18개 관계를 포함하는 BFO 기반 반도체 온톨로지를 `src/models/nodes.py`에 구현합니다.

## User Review Required

> [!WARNING]
> **Breaking Changes**
> `NodeType`과 `RelationType` Enum이 전면 교체됩니다. 기존 코드가 구버전 Enum 멤버(예: 단순 `Company`, `Product`)를 참조하고 있다면 수정이 필요할 수 있습니다.
> 다만, 주요 클래스(Company, Product 등)는 상위 개념이나 매핑으로 유지되도록 설계했습니다.

## Proposed Changes

### [src/models/nodes.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/models/nodes.py)

#### [MODIFY] NodeType Enum 및 RelationType Enum 확장
- **NodeType**: 58개 클래스 정의 (Continuant/Occurrent 계층 구조 반영)
  - `Observation` 추가 (Dynamic Layer)
  - `IDM`, `Fabless`, `Foundry`, `OSAT` 등 구체적 기업 타입 추가
  - `EUV`, `GAA` 등 기술 구체화
- **RelationType**: 21개 관계 정의 (RO/BFO 준수)
  - `RECORDED_AT`, `OBSERVES`, `HAS_VALUE` 추가 (Time-Stitching용)

### [src/templates/prompts.yaml](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/templates/prompts.yaml)

#### [MODIFY] Gemini PDF Parser Prompt
- **Schema Mapping**: 새로운 58개 Entity Type과 21개 Relation Type에 대한 정의 및 예시 추가
- **Observation Logic**: "맥락 없는 데이터(Context-less Data)는 Observation으로 객체화하라"는 지시사항 추가
- **Extraction Rules**:
  - `Company` 추출 시 Ticker 포함 규칙 강화
  - `Metric` 추출 시 `Observation` 패턴 적용 가이드
  - `Time-Event Stitching` 예시 추가

### [src/dataflows/neo4j_loader.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/dataflows/neo4j_loader.py)

#### [MODIFY] Entity Layer 분류 로직 수정 (`_classify_entity_layer`)
- **Static Types**: `SemiconductorEntity`, `IndependentContinuant`, `Agent`, `OrganizationType`, `Fabless`, `IDM`, `Foundry`, `OSAT`, `SupplierOrganization`, `PhysicalObject`, `Semiconductor`, `MemorySemiconductor`, `SystemSemiconductor`, `AnalogDevice`, `ProcessNode`, `PackagingTechnology`, `Location`, `Role`, `ValueChainStage`, `InformationObject`, `FinancialReport`, `Patent`, `Policy`, `TechnicalSpecification`, `RiskFactor`, `GeopoliticalRisk`, `SupplyChainRisk`, `OpportunityFactor`, `Person`, `Technology`
- **Dynamic Types**: `Occurrent`, `Process`, `ManufacturingProcess`, `FrontEndProcess`, `BackEndProcess`, `Event`, `StrategicAction`, `CorporateEvent`, `MarketEnvironment`, `PolicyEvent`, `Observation`, `TemporalRegion`, `Quality`, `FinancialMetric`, `TechnicalMetric`, `MarketMetric`, `Trend`

#### [MODIFY] Dynamic Entity 생성 로직 (`_create_dynamic_entity`)
- `Observation` 노드 생성 시 `created_at` 자동 생성 외에 `recorded_at` 속성이 있는 경우 이를 시계열 인덱싱에 활용 가능하도록 처리

## Verification Plan

### Automated Tests
1. **Schema Validation Script**:
   새로운 스키마가 로드되고 유효한지 확인하는 스크립트를 작성하여 실행합니다.
   ```bash
   poetry run python scripts/verify_schema.py
   ```

### Manual Verification
- `nodes.py` 파일의 Enum 정의가 설계 문서(`semiconductor_tbox_design.md`)와 일치하는지 확인합니다.
