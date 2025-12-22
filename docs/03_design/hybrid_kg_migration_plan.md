# 하이브리드 KG 아키텍처 마이그레이션 Implementation Plan

**작성일**: 2025-12-22  
**작성자**: Hybrid KG Migration Team  
**문서 버전**: 1.0

---

## 목차

1. [개요 및 목표](#1-개요-및-목표)
2. [현재 시스템 분석](#2-현재-시스템-분석)
3. [제안된 변경사항](#3-제안된-변경사항)
4. [검증 계획](#4-검증-계획)
5. [위험 요소 및 대응](#5-위험-요소-및-대응)

---

## 1. 개요 및 목표

### 1.1. 마이그레이션 목표

**AS-IS (현재)**:
- BFO 기반 58개 클래스 온톨로지
- 모든 시계열 데이터 → `Observation` 노드 생성
- 단순 연결 관계 (`RelatedTo`)

**TO-BE (목표)**:
- 실용적 4개 핵심 노드 (Agent, Signal, MacroMetric, Document)
- 이원화: 상태(Snapshot) = 속성, 사건(Story) = 노드
- 함수적 관계 (`AFFECTS`, `TRIGGERED_BY` with 가중치)

### 1.2. 성공 기준

1. ✅ Neo4j에 1,500개 이상 노드 적재 (PDF 리포트 기준)
2. ✅ AFFECTS 관계의 통계 검증 정확도 75% 이상
3. ✅ Hybrid Search 쿼리 응답 시간 < 1초
4. ✅ PoC 시나리오 3개 (환율-삼성전자, 주가 급등 원인, Hybrid Search) 성공

---

## 2. 현재 시스템 분석

### 2.1. nodes.py 현황 분석

#### 현재 NodeType Enum (59개)
```python
class NodeType(str, Enum):
    # Continuant - Independent
    AGENT = "Agent"
    IDM = "IDM"
    FABLESS = "Fabless"
    FOUNDRY = "Foundry"
    ...
    # Occurrent
    OBSERVATION = "Observation"
    EVENT = "Event"
    METRIC = "Metric"
    ...
```

**문제점**:
- 58개 클래스로 LLM 추출 복잡도 증가
- `Observation` 남발로 그래프 비대화
- 관계 타입에 메타데이터 부재 (가중치, 민감도 등)

#### 현재 RelationType Enum (21개)
```python
class RelationType(str, Enum):
    # Participation
    PARTICIPATES_IN = "participatesIn"
    MANUFACTURES = "manufactures"
    ...
    # Observation
    OBSERVES = "observes"
    RECORDED_AT = "recordedAt"
    ...
```

**문제점**:
- 단순 연결 관계만 표현 (방향성, 강도 없음)
- 인과관계 추론 불가능

---

### 2.2. Parser 현황 분석

| Parser | 데이터 소스 | 현재 출력 노드 | 출력 관계 | 상태 |
|---|---|---|---|---|
| **DARTParserAgent** | DART CSV | `COMPANY`, `EVENT`, `METRIC` | `AFFECTED_BY`, `HAS_METRIC` | ✅ 작동 |
| **PriceParserAgent** | 주가 CSV | `TREND`, `METRIC` (StockPrice) | `HAS_METRIC`, `HAS_TREND` | ✅ 작동 |
| **NewsParserAgent** | 뉴스 CSV | `EVENT` | `AFFECTED_BY` | ✅ 작동 |
| **PDFParserAgent** | PDF 리포트 | `OBSERVATION` (대부분) | `RELATED_TO` | ⚠️ Observation 남발 |
| **MacroParserAgent** | 거시지표 CSV | `METRIC` | - | ✅ 작동 |
| **FundParserAgent** | 펀더멘탈 CSV | `METRIC` | - | ✅ 작동 |

**출력 JSON 구조 (현재)**:
```json
{
  "entities": [
    {
      "name": "Samsung Electronics",
      "type": "COMPANY",
      "properties": {"ticker": "005930"}
    }
  ],
  "relations": [
    {
      "subject": "Samsung Electronics",
      "predicate": "HAS_METRIC",
      "object": "StockPrice_005930_20240315"
    }
  ]
}
```

---

### 2.3. prompts.yaml 현황

**현재 프롬프트 구조**:
```yaml
analysts:
  fundamentals:
    role: "Senior Equity Analyst (Fundamental Focus)"
    instruction: |
      Analyze the company's financial health...
```

**문제점**:
- PDF 파싱 프롬프트 없음 (GeminiPDFParser는 별도 구현)
- T-Box 스키마 미포함
- Signal 추출 규칙 부재

---

## 3. 제안된 변경사항

### 3.1. nodes.py 재설계

#### 📝 파일: [`src/models/nodes.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/models/nodes.py)

#### 변경 내용

**Step 1: NodeType Enum 단순화**
```python
class NodeType(str, Enum):
    # Agent Layer (정적)
    IDM = "IDM"
    FABLESS = "Fabless"
    FOUNDRY = "Foundry"
    SUPPLIER = "Supplier"
    ORGANIZATION = "Organization"
    
    # Signal Layer (동적)
    EARNINGS = "Earnings"
    PRICE_MOVEMENT = "PriceMovement"
    DISCLOSURE = "Disclosure"
    ISSUE = "Issue"
    
    # MacroMetric Layer
    ECONOMIC_INDICATOR = "EconomicIndicator"
    
    # Document Layer
    NEWS = "News"
    REPORT = "Report"
```

**Step 2: RelationType Enum 추가**
```python
class RelationType(str, Enum):
    # Logic Layer (정적 역학 관계)
    AFFECTS = "AFFECTS"  # 메타데이터: correlation, sensitivity, lag, confidence
    
    # Causal Layer (동적 인과 관계)
    TRIGGERED_BY = "TRIGGERED_BY"  # 메타데이터: confidence, reasoning
    
    # Structural Layer (밸류체인)
    SUPPLIES = "SUPPLIES"
    MANUFACTURES = "MANUFACTURES"
    HAS_SIGNAL = "HAS_SIGNAL"
    MENTIONED_IN = "MENTIONED_IN"
    
    # 기존 유지 (하위 호환성)
    HAS_METRIC = "HAS_METRIC"
    HAS_TREND = "HAS_TREND"
    AFFECTED_BY = "AFFECTED_BY"
```

**Step 3: Entity 모델 속성 추가**
```python
class Entity(BaseModel):
    name: str
    type: NodeType
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    
    # 신규 추가
    embedding: Optional[List[float]] = None  # Vector Index용
    fundamental_stats: Optional[Dict[str, float]] = None  # Agent 전용
    direction: Optional[str] = None  # Signal 전용 ("UP"/"DOWN"/"NEUTRAL")
    magnitude: Optional[float] = None  # Signal 전용
    sentiment: Optional[str] = None  # Signal 전용 ("POSITIVE"/"NEGATIVE")
```

**Step 4: Relation 모델 메타데이터 추가**
```python
class Relation(BaseModel):
    subject: str
    predicate: RelationType
    object: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    # AFFECTS 전용 메타데이터
    correlation: Optional[str] = None  # "DIRECT" | "INVERSE"
    sensitivity: Optional[float] = None  # 0.0 ~ 1.0
    lag: Optional[str] = None  # "IMMEDIATE" | "1Q" | "1Y"
    confidence: Optional[float] = None  # 0.0 ~ 1.0
    
    # TRIGGERED_BY 전용 메타데이터
    reasoning: Optional[str] = None  # 인과관계 설명
```

---

### 3.2. prompts.yaml 업데이트

#### 📝 파일: [`src/templates/prompts.yaml`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/templates/prompts.yaml)

#### 변경 내용

**Step 1: gemini_pdf_parser 섹션 신규 추가**
```yaml
gemini_pdf_parser:
  role: "Financial Knowledge Graph Specialist"
  kg_extraction:
    instruction: |
      다음 PDF 리포트에서 정보를 추출하여 Knowledge Graph로 변환하세요.
      
      [T-Box 스키마]
      ## Agent (정적 엔티티)
      - IDM: 삼성전자, SK하이닉스
      - Fabless: NVIDIA, Qualcomm
      - Foundry: TSMC
      
      ## Signal (동적 사건)
      - Earnings: 실적 발표
      - PriceMovement: 주가 급등/급락
      - Disclosure: M&A, 증설 공시
      
      ## MacroMetric (거시 지표)
      - EconomicIndicator: USD/KRW 환율, 미국 금리
      
      [중요 규칙]
      1. Signal의 magnitude는 반드시 숫자로 추출 (예: "15% 상승" → 15.0)
      2. Signal의 sentiment는 "POSITIVE" 또는 "NEGATIVE"
      3. AFFECTS 관계의 correlation은 "DIRECT" (정비례) 또는 "INVERSE" (반비례)
      
      [출력 형식]
      ```json
      {
        "entities": [
          {
            "name": "SK하이닉스",
            "type": "IDM",
            "properties": {"ticker": "000660"}
          },
          {
            "name": "SK하이닉스 4Q24 어닝 서프라이즈",
            "type": "Earnings",
            "direction": "UP",
            "magnitude": 15.5,
            "sentiment": "POSITIVE",
            "properties": {"date": "2024-10-31"}
          }
        ],
        "relations": [
          {
            "subject": "USD/KRW",
            "predicate": "AFFECTS",
            "object": "SK하이닉스",
            "correlation": "DIRECT",
            "sensitivity": 0.8,
            "lag": "1Q"
          }
        ]
      }
      ```
```

---

### 3.3. Parser 리팩토링

#### 3.3.1. DARTParserAgent 수정

#### 📝 파일: [`src/agents/parsers/dart_parser_agent.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/agents/parsers/dart_parser_agent.py:246-317)

**현재 구현 (246-317줄)**:
```python
# Disclosure → Event 변환
event_entity = Entity(
    name=event_name,
    type=NodeType.EVENT,  # ← 현재
    properties={...},
    confidence=1.0
)
```

**변경 후**:
```python
# Disclosure → Signal (Disclosure) 변환
signal_entity = Entity(
    name=event_name,
    type=NodeType.DISCLOSURE,  # ← 변경
    sentiment=self._classify_sentiment(report_nm),  # ← 신규
    properties={...},
    confidence=1.0
)
```

**추가 구현**:
```python
def _classify_sentiment(self, report_name: str) -> str:
    """
    공시 유형별 Sentiment 분류
    
    Args:
        report_name: 공시명 (예: "분할합병결정")
    
    Returns:
        "POSITIVE" | "NEGATIVE" | "NEUTRAL"
    """
    positive_keywords = ["증설", "투자", "배당", "계약", "흑자"]
    negative_keywords = ["소송", "적자", "파산", "정정", "해고"]
    
    for keyword in positive_keywords:
        if keyword in report_name:
            return "POSITIVE"
    
    for keyword in negative_keywords:
        if keyword in report_name:
            return "NEGATIVE"
    
    return "NEUTRAL"
```

---

#### 3.3.2. PriceParserAgent 수정

#### 📝 파일: [`src/agents/parsers/price_parser_agent.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/agents/parsers/price_parser_agent.py:161-270)

**신규 기능 추가**:
```python
def _detect_price_movements(self, df: pd.DataFrame, ticker: str, threshold: float = 5.0) -> List[Entity]:
    """
    주가 급등/급락 탐지 (±5% 이상 변동)
    
    Args:
        df: 주가 DataFrame
        ticker: 종목 코드
        threshold: 변동폭 임계값 (%)
    
    Returns:
        PriceMovement Signal 리스트
    """
    signals = []
    
    df['pct_change'] = df['close'].pct_change() * 100
    
    for idx, row in df.iterrows():
        if abs(row['pct_change']) >= threshold:
            signal = Entity(
                name=f"PriceMovement_{ticker}_{row['date'].strftime('%Y%m%d')}",
                type=NodeType.PRICE_MOVEMENT,  # ← 신규
                direction="UP" if row['pct_change'] > 0 else "DOWN",
                magnitude=abs(row['pct_change']),
                sentiment="POSITIVE" if row['pct_change'] > 0 else "NEGATIVE",
                properties={
                    "date": row['date'].isoformat(),
                    "close": row['close'],
                    "volume": row['volume']
                },
                confidence=1.0
            )
            signals.append(signal)
    
    return signals
```

---

#### 3.3.3. 신규 SupplyChainParser 개발

#### 📝 파일: [`src/agents/parsers/supply_chain_parser.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/agents/parsers/supply_chain_parser.py) (신규)

```python
"""
Supply Chain Parser
PDF 리포트에서 밸류체인 정보 추출 (SUPPLIES, MANUFACTURES 관계)
"""

from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI

from .base_parser_agent import BaseParserAgent
from src.models.nodes import KnowledgeGraph, Entity, Relation, NodeType, RelationType


class SupplyChainParser(BaseParserAgent):
    """
    공급망 정보 추출 Parser
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        super().__init__(name="SupplyChainParser")
        self.llm = llm
    
    def parse_from_text(self, text: str) -> KnowledgeGraph:
        """
        텍스트에서 공급망 관계 추출
        
        Args:
            text: PDF 텍스트
        
        Returns:
            KnowledgeGraph (SUPPLIES, MANUFACTURES 관계)
        """
        prompt = f"""
        다음 리포트에서 공급망 관계를 추출하세요.
        
        [리포트]
        {text}
        
        [추출 형식]
        ```json
        {{
          "supply_chain": [
            {{
              "supplier": "ASML",
              "customer": "Samsung Electronics",
              "product": "EUV 노광장비",
              "relation_type": "SUPPLIES"
            }},
            {{
              "manufacturer": "Samsung Electronics",
              "product": "HBM3E",
              "relation_type": "MANUFACTURES"
            }}
          ]
        }}
        ```
        """
        
        response = self.llm.invoke(prompt)
        # JSON 파싱 및 KnowledgeGraph 생성 로직
        # ...
```

---

### 3.4. Relation Logic 구현

#### 3.4.1. AFFECTS 관계 통계 검증

#### 📝 파일: [`src/utils/relation_validator.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/utils/relation_validator.py) (신규)

```python
"""
Relation Validator
LLM 추출 관계의 통계적 검증
"""

from scipy.stats import pearsonr
import numpy as np
from typing import Dict, Any


class RelationValidator:
    """
    AFFECTS 관계 검증기
    """
    
    def validate_affects(
        self,
        macro_data: np.ndarray,
        company_data: np.ndarray,
        llm_correlation: str,
        llm_sensitivity: float
    ) -> Dict[str, Any]:
        """
        AFFECTS 관계의 통계적 검증
        
        Args:
            macro_data: 거시지표 시계열 데이터
            company_data: 기업 데이터 시계열
            llm_correlation: LLM 추출값 ("DIRECT" | "INVERSE")
            llm_sensitivity: LLM 추출 민감도 (0.0~1.0)
        
        Returns:
            {
                "correlation": "DIRECT" | "INVERSE",
                "sensitivity": float,
                "confidence": float,
                "p_value": float
            }
        """
        # Pearson 상관계수 계산
        pearson_r, p_value = pearsonr(macro_data, company_data)
        
        # 통계적 correlation 판단
        stat_correlation = "DIRECT" if pearson_r > 0 else "INVERSE"
        
        # LLM vs 통계 비교
        correlation_match = (llm_correlation == stat_correlation)
        sensitivity_delta = abs(llm_sensitivity - abs(pearson_r))
        
        # Confidence 계산
        if correlation_match and sensitivity_delta < 0.2:
            confidence = 0.9  # 높은 신뢰도
        elif correlation_match:
            confidence = 0.7  # 중간 신뢰도
        else:
            confidence = 0.5  # 낮은 신뢰도
        
        return {
            "correlation": stat_correlation,
            "sensitivity": abs(pearson_r),
            "confidence": confidence,
            "p_value": p_value
        }
```

---

#### 3.4.2. TRIGGERED_BY 관계 구축

#### 📝 파일: [`src/utils/causal_analyzer.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/utils/causal_analyzer.py) (신규)

```python
"""
Causal Analyzer
시간 윈도우 기반 인과관계 분석
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI


class CausalAnalyzer:
    """
    TRIGGERED_BY 관계 분석기
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI, time_window_days: int = 1):
        self.llm = llm
        self.time_window = timedelta(days=time_window_days)
    
    def analyze_causality(
        self,
        event1: Dict[str, Any],  # Disclosure
        event2: Dict[str, Any],  # PriceMovement
    ) -> Optional[Dict[str, Any]]:
        """
        두 사건 간 인과관계 분석
        
        Args:
            event1: 원인 사건 (예: Disclosure)
            event2: 결과 사건 (예: PriceMovement)
        
        Returns:
            {
                "has_causality": bool,
                "confidence": float,
                "reasoning": str
            } or None
        """
        # 1. 시간 윈도우 체크
        date1 = datetime.fromisoformat(event1['properties']['date'])
        date2 = datetime.fromisoformat(event2['properties']['date'])
        
        time_diff = abs((date2 - date1).total_seconds())
        
        if time_diff > self.time_window.total_seconds():
            return None  # 시간 윈도우 벗어남
        
        # 2. LLM 기반 인과관계 판단
        prompt = f"""
        다음 두 사건 간 인과관계를 분석하세요.
        
        [사건 1: 공시]
        - 이름: {event1['name']}
        - 날짜: {event1['properties']['date']}
        
        [사건 2: 주가 변동]
        - 이름: {event2['name']}
        - 방향: {event2['direction']}
        - 변동폭: {event2['magnitude']}%
        - 날짜: {event2['properties']['date']}
        
        [질문]
        1. 사건 1이 사건 2를 직접 유발했는가? (Yes/No)
        2. 신뢰도는 얼마인가? (0.0~1.0)
        3. 이유를 설명하시오.
        
        [출력 형식]
        ```json
        {{
          "has_causality": true,
          "confidence": 0.92,
          "reasoning": "공급 계약 공시 직후 주가 급등, 시간적/의미적 인과성 확인"
        }}
        ```
        """
        
        response = self.llm.invoke(prompt)
        # JSON 파싱 및 반환
        # ...
```

---

### 3.5. Neo4j Integration

#### 📝 파일: [`src/dataflows/neo4j_loader.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/src/dataflows/neo4j_loader.py)

**Step 1: Vector Index 생성 로직 추가**
```python
def create_vector_indexes(self, session):
    """
    Neo4j Vector Index 생성
    """
    # Document Embedding Index
    session.run("""
        CREATE VECTOR INDEX document_embedding IF NOT EXISTS
        FOR (d:Document)
        ON d.embedding
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }
        }
    """)
    
    # Agent Description Embedding Index
    session.run("""
        CREATE VECTOR INDEX agent_embedding IF NOT EXISTS
        FOR (a:Agent)
        ON a.description_embedding
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }
        }
    """)
```

**Step 2: Hybrid Search 쿼리 메서드 추가**
```python
def hybrid_search(
    self,
    query_embedding: List[float],
    graph_filter: Dict[str, Any],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Graph Filter + Vector Search 하이브리드 쿼리
    
    Args:
        query_embedding: 쿼리 임베딩
        graph_filter: 그래프 필터 (예: {"company": "Samsung Electronics"})
        top_k: 상위 K개 결과
    
    Returns:
        검색 결과 리스트
    """
    with self.driver.session() as session:
        result = session.run("""
            // 1. Graph Filter
            MATCH (company:IDM {name: $company})
            MATCH (company)<-[:SUPPLIES]-(supplier:Supplier)
            
            // 2. Vector Search
            CALL db.index.vector.queryNodes(
                'document_embedding',
                $top_k,
                $query_embedding
            ) YIELD node AS doc, score
            
            // 3. 결합 필터
            WHERE (doc)-[:MENTIONED_IN]->(supplier)
            
            RETURN doc.title AS title, doc.content AS content, score
            ORDER BY score DESC
            LIMIT $top_k
        """, {
            "company": graph_filter.get("company"),
            "query_embedding": query_embedding,
            "top_k": top_k
        })
        
        return [dict(record) for record in result]
```

---

## 4. 검증 계획

### 4.1. Unit Tests

#### 📝 파일: [`tests/unit/test_nodes.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/tests/unit/test_nodes.py) (신규)

```python
"""
nodes.py 모델 Unit Test
"""

import pytest
from src.models.nodes import Entity, Relation, NodeType, RelationType


def test_agent_entity_creation():
    """Agent 노드 생성 테스트"""
    agent = Entity(
        name="Samsung Electronics",
        type=NodeType.IDM,
        properties={"ticker": "005930"},
        fundamental_stats={"per": 15.2, "pbr": 1.4}
    )
    
    assert agent.name == "Samsung Electronics"
    assert agent.type == NodeType.IDM
    assert agent.fundamental_stats["per"] == 15.2


def test_signal_entity_creation():
    """Signal 노드 생성 테스트"""
    signal = Entity(
        name="SK하이닉스 4Q24 어닝 서프라이즈",
        type=NodeType.EARNINGS,
        direction="UP",
        magnitude=15.5,
        sentiment="POSITIVE",
        properties={"date": "2024-10-31"}
    )
    
    assert signal.type == NodeType.EARNINGS
    assert signal.magnitude == 15.5
    assert signal.sentiment == "POSITIVE"


def test_affects_relation_creation():
    """AFFECTS 관계 생성 테스트"""
    relation = Relation(
        subject="USD/KRW",
        predicate=RelationType.AFFECTS,
        object="Samsung Electronics",
        correlation="DIRECT",
        sensitivity=0.72,
        lag="1Q",
        confidence=0.89
    )
    
    assert relation.predicate == RelationType.AFFECTS
    assert relation.correlation == "DIRECT"
    assert relation.sensitivity == 0.72
```

**실행 방법**:
```bash
pytest tests/unit/test_nodes.py -v
```

---

### 4.2. Integration Tests

#### 📝 파일: [`tests/integration/test_parser_pipeline.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/tests/integration/test_parser_pipeline.py) (신규)

```python
"""
Parser 파이프라인 Integration Test
"""

import pytest
from pathlib import Path
from src.agents.parsers.dart_parser_agent import DARTParserAgent
from src.agents.parsers.price_parser_agent import PriceParserAgent
from src.models.nodes import NodeType


def test_dart_parser_integration():
    """DART Parser 통합 테스트"""
    dart_dir = Path("data/raw/DART")
    parser = DARTParserAgent(dart_dir=dart_dir)
    
    kg = parser.parse(dart_dir)
    
    # Company (Agent) 노드 확인
    companies = [e for e in kg.entities if e.type == NodeType.COMPANY]
    assert len(companies) > 0
    
    # Disclosure (Signal) 노드 확인
    disclosures = [e for e in kg.entities if e.type == NodeType.DISCLOSURE]
    assert len(disclosures) > 0


def test_price_parser_price_movement_detection():
    """Price Parser의 PriceMovement 탐지 테스트"""
    file_path = Path("data/raw/price/005930.KS_prices.csv")
    parser = PriceParserAgent()
    
    kg = parser.parse(file_path)
    
    # PriceMovement Signal 노드 확인
    movements = [e for e in kg.entities if e.type == NodeType.PRICE_MOVEMENT]
    assert len(movements) > 0
    
    # magnitude 검증
    for movement in movements:
        assert movement.magnitude >= 5.0  # 5% 이상 변동
        assert movement.direction in ["UP", "DOWN"]
```

**실행 방법**:
```bash
pytest tests/integration/test_parser_pipeline.py -v
```

---

### 4.3. PoC Scenario Testing

#### 시나리오 1: 환율-삼성전자 AFFECTS 관계 **수동 검증**

```bash
# 1. Neo4j 쿼리 실행 (Neo4j Browser)
MATCH (usd:EconomicIndicator {name: "USD/KRW"})
      -[r:AFFECTS {correlation: "DIRECT"}]->(affected:IDM)
WHERE r.confidence > 0.8
RETURN affected.name AS company, 
       r.sensitivity AS impact_strength,
       r.lag AS time_lag
ORDER BY r.sensitivity DESC
```

**기대 결과**:
```
company               | impact_strength | time_lag
Samsung Electronics   | 0.72           | 1Q
```

**검증 방법**:
1. Neo4j Browser에서 위 쿼리 실행
2. 결과가 1개 이상 반환되는지 확인
3. `sensitivity` 값이 0.7 이상인지 확인

---

#### 시나리오 2: 주가 급등 TRIGGERED_BY 분석 **수동 검증**

```bash
# Neo4j 쿼리 실행
MATCH (sig:PriceMovement {date: datetime("2024-03-05")})
      -[:TRIGGERED_BY]->(cause:News)
RETURN sig.summary AS event,
       cause.title AS root_cause,
       cause.url AS source
```

**기대 결과**:
```
event                    | root_cause                          | source
삼성전자 주가 12.3% 급등   | 삼성전자, HBM3E 공급 계약 체결       | https://...
```

---

#### 시나리오 3: Hybrid Search **자동 테스트**

#### 📝 파일: [`tests/e2e/test_hybrid_search.py`](file:///d:/0.Sogang/동아리%20및%20학회/Insight/2025-2/2차%20인사이콘/25-2-Insightcon/tests/e2e/test_hybrid_search.py) (신규)

```python
"""
Hybrid Search E2E Test
"""

import pytest
from openai import OpenAI
from src.dataflows.neo4j_loader import Neo4jKGLoader


def test_hybrid_search_response_time():
    """Hybrid Search 응답 시간 테스트 (< 1초)"""
    import time
    
    client = OpenAI()
    loader = Neo4jKGLoader()
    
    # 쿼리 임베딩 생성
    query = "삼성전자 밸류체인에서 수율 개선 관련 리포트"
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding
    
    # Hybrid Search 실행
    start_time = time.time()
    results = loader.hybrid_search(
        query_embedding=embedding,
        graph_filter={"company": "Samsung Electronics"},
        top_k=3
    )
    elapsed_time = time.time() - start_time
    
    # 검증
    assert elapsed_time < 1.0  # 1초 미만
    assert len(results) > 0  # 결과 있음
```

**실행 방법**:
```bash
pytest tests/e2e/test_hybrid_search.py -v
```

---

## 5. 위험 요소 및 대응

### 5.1. Critical Risks

| 위험 요소 | 영향도 | 발생 가능성 | 대응 방안 |
|---|---|---|---|
| **LLM 추출 정확도 부족** | High | Medium | - 프롬프트 엔지니어링 반복<br>- Few-shot 예제 추가<br>- 통계 검증으로 보정 |
| **밸류체인 데이터 부재** | High | High | - LLM 기반 추출 (75% 정확도 목표)<br>- 수동 검증 (샘플 100개)<br>- 외부 데이터 구매 (Plan B) |
| **Neo4j Vector Index 성능** | Medium | Low | - 인덱스 파라미터 튜닝<br>- Batch 임베딩 생성<br>- 쿼리 최적화 |
| **기존 코드 하위 호환성** | Low | Medium | - RelationType 기존 값 유지<br>- 점진적 마이그레이션 (Phased Rollout) |

### 5.2. Mitigation Strategies

**전략 1: 점진적 마이그레이션 (Phased Rollout)**
- Week 1-2: Schema 변경 → 기존 파서와 병행 운영
- Week 3-4: 신규 파서 개발 → A/B 테스트
- Week 5-6: 기존 파서 Deprecated

**전략 2: Rollback Plan**
- `nodes.py` v1.0 백업
- Git 브랜치 전략 (`feature/hybrid-kg` → `main`)
- 실패 시 즉시 롤백

---

**[문서 끝]**
