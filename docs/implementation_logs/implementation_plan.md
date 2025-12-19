# 반도체 T-Box Schema 구현 계획

User가 요청한 57개 클래스와 18개 관계를 포함하는 BFO 기반 반도체 온톨로지를 `src/models/nodes.py`에 구현합니다.

## User Review Required

> [!WARNING]
> **Breaking Changes**
> `NodeType`과 `RelationType` Enum이 전면 교체됩니다. 기존 코드가 구버전 Enum 멤버(예: 단순 `Company`, `Product`)를 참조하고 있다면 수정이 필요할 수 있습니다.
> 다만, 주요 클래스(Company, Product 등)는 상위 개념이나 매핑으로 유지되도록 설계했습니다.

## Proposed Changes

### [src/models/nodes.py](file:///d:/0.Sogang/동아리 및 학회/Insight/2025-2/2차 인사이콘/25-2-Insightcon/src/models/nodes.py)

#### [MODIFY] NodeType Enum 및 RelationType Enum 교체
- **NodeType**: 57개 클래스 정의 (Continuant/Occurrent 계층 구조 반영)
- **RelationType**: 18개 관계 정의 (RO/BFO 준수)
- **PARENT_MAP**: 계층 구조 매핑 추가 (Leaf Node -> Parent Class)
- **ENTITY_TYPE_PROPERTIES**: 각 노드 타입별 필수 속성 정의 업데이트

## Verification Plan

### Automated Tests
1. **Schema Validation Script**:
   새로운 스키마가 로드되고 유효한지 확인하는 스크립트를 작성하여 실행합니다.
   ```bash
   poetry run python scripts/verify_schema.py
   ```

### Manual Verification
- `nodes.py` 파일의 Enum 정의가 설계 문서(`semiconductor_tbox_design.md`)와 일치하는지 확인합니다.
