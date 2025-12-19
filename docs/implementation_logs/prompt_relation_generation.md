# BFO 기반 반도체 온톨로지 관계(Relations) 정의 요청 프롬프트

> **목적**: 이 프롬프트는 LLM(ChatGPT, Claude 등)을 사용하여 반도체 산업 특화 Knowledge Graph의 T-Box에 필요한 **Missing Relations**를 생성하기 위해 작성되었습니다.

---

**[System Instruction]**
당신은 BFO(Basic Formal Ontology)와 RO(Relation Ontology)에 정통한 온톨로지 설계 전문가입니다. 반도체 산업의 도메인 지식을 바탕으로 엄밀한 관계(Relationships)를 정의해야 합니다.

**[Context]**
우리는 반도체 산업을 분석하기 위한 지식 그래프를 구축하고 있습니다.
엔티티(Classes)는 총 57개로, `Continuant`(지속체)와 `Occurrent`(시간전개체)로 구분되어 이미 정의되었습니다.
총 18개의 핵심 관계(Relations)를 정의하기로 계획했으나, 현재 4개만 확인되고 나머지 14개가 누락된 상태입니다.

**[Input: Defined Classes]**
(계층 구조 요약)
1. **Continuant**: Agent(Organization, Person), PhysicalObject(Product, Tech), Location, Quality(Metric), Role, InformationObject
2. **Occurrent**: Process(Manufacturing), Event(Corporate, Market, Policy), TemporalRegion
3. **Risk/Opportunity**

**[Input: Known Relations (4/18)]**
1. `participatesIn`: 참여한다 (Agent -> Occurrent)
2. `hasRole`: 역할을 가진다 (Continuant -> Role)
3. `producedBy`: 생산되었다 (PhysicalObject -> Agent)
4. `locatedAt`: 위치하다 (Continuant -> Location)

**[Task]**
위의 클래스 구조와 호환되는 **나머지 14개의 관계**를 BFO/RO 표준에 맞춰 정의하십시오.
반도체 비즈니스 분석(투자, 공급망, 기술 경쟁)에 유용한 관계여야 합니다.

**[Required Output Format]**
각 관계에 대해 다음 형식을 지켜주십시오:
- **Relation Code**: (CamelCase, 예: `hasQuality`)
- **Label**: (한국어 라벨, 예: 특성을 가진다)
- **Domain**: (시작 노드 타입)
- **Range**: (대상 노드 타입)
- **Description**: (관계의 의미와 사용 예시)

**[Suggested Relations derived from RO]**
다음 관계들을 포함하여 총 18개를 완성하십시오:
- `hasPart` / `partOf` (구성 관계)
- `hasQuality` (속성 관계: Entity -> Metric)
- `concretizes` / `isAbout` (정보 관계: Report -> Entity)
- `realizes` (실현 관계: Process -> Plan/Function)
- `precededBy` (시간 순서: Process -> Process)
- `causallyRelatedTo` / `affects` (인과 관계: Event -> Market/Price)
- `derivesFrom` (파생 관계: Tech -> Tech)

**[Example Output]**
5. `hasQuality`: 특성을 가진다 (IndependentContinuant -> Quality) - 기업이나 제품이 특정 재무/기술 지표를 가짐을 나타냄.
6. `isAbout`: ~에 대한 것이다 (InformationObject -> Entity) - 보고서나 뉴스가 특정 기업/기술을 다룸.
... (총 18번까지 작성)
