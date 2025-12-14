# LLM 활용 완전 정리 가이드

## 📖 목차
1. [LLM이란 무엇인가?](#llm이란-무엇인가)
2. [금융 도메인 LLM](#금융-도메인-llm)
3. [온톨로지 스키마 자동 생성](#온톨로지-스키마-자동-생성)
4. [엔티티·관계 추출](#엔티티관계-추출)
5. [프롬프트 엔지니어링](#프롬프트-엔지니어링)
6. [LLM 선택 전략](#llm-선택-전략)
7. [실전 구현 가이드](#실전-구현-가이드)

---

## LLM이란 무엇인가?

### 기본 개념

**LLM (Large Language Model)**은 대규모 텍스트 데이터로 학습된 인공지능 모델로, 자연어를 이해하고 생성할 수 있습니다.

#### LLM의 능력

1. **이해 (Understanding)**: 텍스트의 의미 파악
2. **생성 (Generation)**: 맥락에 맞는 텍스트 생성
3. **추론 (Reasoning)**: 논리적 추론 수행
4. **번역 (Translation)**: 언어 간 번역
5. **요약 (Summarization)**: 긴 텍스트 요약

### LLM의 작동 원리

#### Transformer 아키텍처

```
입력 텍스트
    ↓
토크나이징 (Tokenization)
    ↓
임베딩 (Embedding)
    ↓
Transformer 블록 (여러 층)
    ├─ Self-Attention
    ├─ Feed-Forward
    └─ Layer Normalization
    ↓
출력 임베딩
    ↓
디코딩 (Decoding)
    ↓
생성된 텍스트
```

#### Attention 메커니즘

**목적**: 입력의 각 부분에 얼마나 집중할지 결정

**예시**:
```
입력: "삼성전자는 HBM을 제조합니다."

Attention 가중치:
- "삼성전자": 0.3
- "HBM": 0.4  (가장 중요)
- "제조": 0.2
- "합니다": 0.1
```

### LLM의 한계

1. **환각 (Hallucination)**: 잘못된 정보 생성
2. **컨텍스트 길이 제한**: 긴 문서 처리 어려움
3. **최신 정보 부족**: 학습 시점 이후 정보 없음
4. **계산 비용**: 대규모 모델은 비용이 높음

### RAG로 한계 극복

**RAG (Retrieval Augmented Generation)**:
- 외부 지식 소스에서 정보 검색
- 검색된 정보를 컨텍스트로 제공
- LLM이 검색된 정보를 바탕으로 답변 생성

---

## 금융 도메인 LLM

### 일반 LLM vs 금융 LLM

#### 일반 LLM의 문제

```
질의: "삼성전자의 P/E 비율이 12.5인데, 이게 좋은가?"

일반 LLM 답변:
"P/E 비율 12.5는 업계 평균과 비교해 봐야 합니다.
 일반적으로 낮은 P/E는 저평가를 의미할 수 있지만,
 업종과 성장 단계를 고려해야 합니다."
 
문제점:
- 구체적인 업계 평균 정보 없음
- 최신 시장 데이터 없음
- 금융 전문 용어 이해 부족
```

#### 금융 LLM의 장점

**Fine-tuned 금융 LLM**:
- 금융 텍스트로 추가 학습
- 금융 용어와 개념 이해 향상
- 금융 도메인 특화 답변

**예시 모델**:
- **BloombergGPT**: Bloomberg 데이터로 학습
- **FinGPT**: 오픈소스 금융 LLM
- **FinBERT**: 금융 감성 분석 특화

### FinGPT 예시

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

# FinGPT 모델 로드
tokenizer = AutoTokenizer.from_pretrained("FinGPT/fingpt-forecaster_dow30_llama2-7b-lora")
model = AutoModelForCausalLM.from_pretrained("FinGPT/fingpt-forecaster_dow30_llama2-7b-lora")

# 금융 질의
prompt = """
삼성전자의 재무 정보:
- P/E Ratio: 12.5
- 업계 평균 P/E: 15.0
- ROE: 15.3%

이 기업의 투자 가치를 평가하세요.
"""

inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_length=200)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)

print(response)
```

**출력**:
```
삼성전자는 현재 저평가 상태입니다.
- P/E 비율 12.5는 업계 평균 15.0 대비 낮아 저평가를 나타냅니다.
- ROE 15.3%는 업계 평균을 상회하는 우수한 수익성을 보여줍니다.
- 종합적으로 매수 권장 등급입니다.
```

---

## 온톨로지 스키마 자동 생성

### 왜 자동 생성인가?

**전통적인 방법**:
- 도메인 전문가와 온톨로지 엔지니어 협업
- 수개월에서 수년 소요
- 유지보수 어려움

**LLM 자동 생성**:
- 전문 템플릿 기반 자동 추출
- 수일 내 기본 스키마 생성
- 지속적 업데이트 용이

### FinKario의 방법

#### Step 1: 전문 템플릿 수집

```python
templates = {
    "CFA": """
    Equity Research Report Structure:
    1. Executive Summary
    2. Investment Thesis
    3. Company Overview
       - Business Model
       - Products & Services
       - Market Position
    4. Industry Analysis
    5. Financial Analysis
       - Income Statement
       - Balance Sheet
       - Cash Flow
       - Key Ratios (P/E, P/B, ROE, etc.)
    6. Valuation
    7. Risk Factors
    8. Investment Recommendation
    """,
    
    "JPMorgan": """
    Research Report Components:
    - Company Description
    - Investment Summary
    - Financial Metrics
    - Competitive Analysis
    - Risk Assessment
    - Price Target
    """,
    
    "Korean_Semiconductor": """
    반도체 섹터 리포트:
    - 기업 개요 (사업 구조, 제품 라인)
    - 공정 기술 (Front-end, Back-end)
    - 설비 현황 (EUV, DUV)
    - 재무 분석 (매출, 영업이익, CapEx)
    - 경쟁 분석 (경쟁사 비교)
    - 리스크 요인 (사이클, 규제)
    """
}
```

#### Step 2: LLM 기반 스키마 추출

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class OntologySchemaGenerator:
    def __init__(self, llm):
        self.llm = llm
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """당신은 금융 도메인 온톨로지 설계 전문가입니다.
            증권 리포트 템플릿을 분석하여 온톨로지 스키마를 추출하세요."""),
            ("human", """다음 증권 리포트 템플릿들을 분석하여 
            온톨로지 스키마를 추출하세요.

템플릿:
{templates}

추출할 정보:
1. 엔티티 타입 (예: Company, Product, Metric)
2. 관계 타입 (예: manufactures, hasMetric, competesWith)
3. 속성 타입 (예: marketCap, revenue, P/E)

JSON 형식으로 반환하세요:
{{
    "entities": [
        {{"name": "Company", "description": "...", "properties": [...]}},
        ...
    ],
    "relations": [
        {{"name": "manufactures", "from": "Company", "to": "Product"}},
        ...
    ],
    "properties": [
        {{"name": "marketCap", "type": "number", "unit": "원"}},
        ...
    ]
}}""")
        ])
    
    def generate_schema(self, templates):
        """스키마 생성"""
        
        # 템플릿 결합
        combined_templates = "\n\n".join([
            f"{name}:\n{content}"
            for name, content in templates.items()
        ])
        
        # 프롬프트 생성
        prompt = self.prompt_template.format_messages(
            templates=combined_templates
        )
        
        # LLM 호출
        response = self.llm.invoke(prompt)
        
        # JSON 파싱
        import json
        schema = json.loads(response.content)
        
        return schema
```

#### Step 3: Neo4j 스키마 변환

```python
class Neo4jSchemaConverter:
    def __init__(self):
        pass
    
    def convert(self, ontology_schema):
        """온톨로지 스키마를 Neo4j 스키마로 변환"""
        
        cypher_statements = []
        
        # 노드 타입 및 제약 조건 생성
        for entity in ontology_schema['entities']:
            # 제약 조건
            cypher_statements.append(
                f"CREATE CONSTRAINT {entity['name'].lower()}_name IF NOT EXISTS "
                f"FOR (n:{entity['name']}) REQUIRE n.name IS UNIQUE;"
            )
            
            # 인덱스 생성
            for prop in entity.get('properties', []):
                cypher_statements.append(
                    f"CREATE INDEX {entity['name'].lower()}_{prop['name']} IF NOT EXISTS "
                    f"FOR (n:{entity['name']}) ON (n.{prop['name']});"
                )
        
        return cypher_statements
```

### neo4j-graphrag 활용

```python
from neo4j_graphrag import SchemaFromTextExtractor

# LLM 설정
llm = ChatOpenAI(model="gpt-4o")

# 템플릿 문서 준비
documents = [
    cfa_template,
    jpmorgan_template,
    korean_semiconductor_template
]

# 스키마 추출
extractor = SchemaFromTextExtractor(
    llm=llm,
    documents=documents
)

# 스키마 추출
schema = extractor.extract_schema()

# Neo4j 스키마로 변환
neo4j_schema = schema.to_neo4j_schema()

# Neo4j에 적용
for statement in neo4j_schema.to_cypher():
    neo4j_client.execute(statement)
```

---

## 엔티티·관계 추출

### 문서에서 지식 추출

#### 기본 프로세스

```
원본 문서
    ↓
전처리 (정제)
    ↓
LLM 기반 추출
    ├─ 엔티티 식별
    ├─ 관계 식별
    └─ 속성 추출
    ↓
구조화된 데이터
    ↓
지식 그래프 구축
```

#### FinKario의 추출 방법

```python
class KnowledgeExtractor:
    def __init__(self, llm, attribute_schema, event_schema):
        self.llm = llm
        self.attribute_schema = attribute_schema
        self.event_schema = event_schema
    
    def extract(self, document, timestamp):
        """문서에서 지식 추출"""
        
        # Attribute 추출
        attributes = self._extract_attributes(document)
        
        # Event 추출
        events = self._extract_events(document, timestamp)
        
        return {
            'attributes': attributes,
            'events': events,
            'timestamp': timestamp
        }
    
    def _extract_attributes(self, document):
        """속성 정보 추출"""
        
        prompt = f"""
        다음 증권 리포트에서 기업 속성 정보를 추출하세요.
        
        문서:
        {document}
        
        스키마:
        {self.attribute_schema}
        
        추출할 속성:
        - 기업명, 티커, 거래소
        - 산업, 섹터
        - 시가총액, 현재가, 목표가
        - 투자 등급
        - 주요 제품
        - 리스크 요인
        
        JSON 형식:
        {{
            "company_name": "...",
            "ticker": "...",
            "industry": "...",
            "market_cap": "...",
            "products": [...],
            "risk_factors": [...]
        }}
        """
        
        response = self.llm.invoke(prompt)
        return json.loads(response.content)
    
    def _extract_events(self, document, timestamp):
        """이벤트 정보 추출"""
        
        prompt = f"""
        다음 증권 리포트에서 이벤트 정보를 추출하세요.
        
        문서:
        {document}
        
        이벤트 스키마:
        {self.event_schema}
        
        타임스탬프: {timestamp}
        
        추출할 이벤트:
        - 실적 발표 (Earnings)
        - 가이던스 변경 (Guidance)
        - 전략적 행동 (M&A, 해외 진출)
        - 기술 혁신
        - 규제 변화
        
        각 이벤트에 대해:
        - 주체 (Subject)
        - 객체 (Object)
        - 이벤트 타입
        - 날짜
        - 설명
        
        JSON 형식:
        {{
            "events": [
                {{
                    "type": "Earnings",
                    "subject": "삼성전자",
                    "object": "Revenue",
                    "date": "2024-10-25",
                    "description": "..."
                }},
                ...
            ]
        }}
        """
        
        response = self.llm.invoke(prompt)
        return json.loads(response.content)
```

### 품질 관리 및 정제

```python
class QualityController:
    def __init__(self, llm, reference_data_source):
        self.llm = llm
        self.reference = reference_data_source
    
    def refine(self, raw_knowledge_graph):
        """지식 그래프 정제"""
        
        # 1. 엔티티 정규화
        normalized = self._normalize_entities(raw_knowledge_graph)
        
        # 2. 속성 보완
        completed = self._complete_attributes(normalized)
        
        # 3. 오류 수정
        corrected = self._correct_errors(completed)
        
        return corrected
    
    def _normalize_entities(self, graph):
        """엔티티 이름 정규화"""
        
        for entity in graph['entities']:
            # 이름 변형 감지
            if self._is_name_variant(entity['name']):
                # 표준 형태로 변환
                canonical = self._find_canonical_form(entity['name'])
                entity['name'] = canonical
        
        return graph
    
    def _complete_attributes(self, graph):
        """누락된 속성 보완"""
        
        for entity in graph['entities']:
            for metric in entity.get('metrics', []):
                if not metric.get('value') or metric['value'] == 'N/A':
                    # 참조 데이터 소스에서 조회
                    value = self.reference.query(
                        entity['name'],
                        metric['type']
                    )
                    if value:
                        metric['value'] = value
        
        return graph
    
    def _correct_errors(self, graph):
        """LLM을 사용한 오류 수정"""
        
        for entity in graph['entities']:
            for prop in entity.get('properties', []):
                if 'placeholder' in str(prop.get('value', '')).lower():
                    # 원본 문서를 LLM에 다시 입력
                    prompt = f"""
                    다음 정보에서 오류를 수정하세요:
                    
                    엔티티: {entity['name']}
                    속성: {prop['name']}
                    현재 값: {prop['value']}
                    원본 문서: {entity['source_document']}
                    
                    올바른 값을 반환하세요.
                    """
                    
                    corrected = self.llm.invoke(prompt)
                    prop['value'] = corrected.content
        
        return graph
```

---

## 프롬프트 엔지니어링

### 효과적인 프롬프트 작성법

#### 1. 명확한 역할 정의

```python
# 나쁜 예
prompt = "삼성전자를 분석하세요."

# 좋은 예
prompt = """
당신은 전문 금융 분석가입니다.
다음 기업을 펀더멘털 관점에서 분석하세요.

기업: 삼성전자
분석 항목:
1. 재무 건전성
2. 수익성
3. 성장성
4. 밸류에이션

각 항목에 대해 구체적인 수치와 근거를 제시하세요.
"""
```

#### 2. 구조화된 출력 요구

```python
prompt = """
다음 형식으로 답변하세요:

{
    "analysis": {
        "financial_health": {
            "score": 8,
            "reasoning": "..."
        },
        "profitability": {
            "score": 7,
            "reasoning": "..."
        },
        "growth": {
            "score": 9,
            "reasoning": "..."
        },
        "valuation": {
            "score": 8,
            "reasoning": "..."
        }
    },
    "recommendation": "Buy",
    "target_price": 85000,
    "confidence": 0.85
}
"""
```

#### 3. Few-shot 예시 제공

```python
prompt = """
다음 예시를 참고하여 삼성전자를 분석하세요.

예시 1:
기업: Apple
분석:
- 재무 건전성: 우수 (현금 보유량 높음)
- 수익성: 우수 (ROE 150%)
- 성장성: 보통 (성숙 시장)
- 밸류에이션: 고평가 (P/E 30)
권장사항: Hold

예시 2:
기업: Tesla
분석:
- 재무 건전성: 보통 (부채 비율 높음)
- 수익성: 보통 (변동성 큼)
- 성장성: 우수 (전기차 시장 성장)
- 밸류에이션: 고평가 (P/E 50)
권장사항: Buy (성장 주도)

이제 삼성전자를 같은 형식으로 분석하세요.
"""
```

#### 4. 체인 오브 사고 (Chain of Thought)

```python
prompt = """
삼성전자의 투자 가치를 평가하세요.
단계별로 사고 과정을 보여주세요.

1단계: 재무 지표 분석
- P/E: 12.5
- 업계 평균: 15.0
- 분석: 저평가 상태

2단계: 수익성 분석
- ROE: 15.3%
- 업계 평균: 12.0%
- 분석: 우수한 수익성

3단계: 성장성 분석
- 매출 성장률: 10%
- 업계 평균: 8%
- 분석: 평균 이상 성장

4단계: 종합 평가
- 저평가 + 우수한 수익성 + 성장성
- 결론: 매수 권장
"""
```

### 도메인 특화 프롬프트 템플릿

#### 반도체 섹터 분석 프롬프트

```python
SEMICONDUCTOR_ANALYSIS_PROMPT = """
당신은 반도체 산업 전문 분석가입니다.

다음 기업을 반도체 섹터 관점에서 분석하세요.

기업: {company_name}

분석 항목:

1. 사업 구조
   - 제품 포트폴리오 (Memory, Logic, Foundry)
   - 공정 기술 (nm 수준)
   - 설비 현황 (EUV, DUV)

2. 시장 위치
   - 시장 점유율
   - 경쟁사 비교
   - 기술 경쟁력

3. 재무 분석
   - 매출 구조 (제품별, 지역별)
   - 수익성 (영업이익률, 순이익률)
   - 투자 (CapEx, R&D)

4. 리스크 요인
   - 반도체 사이클
   - 규제 리스크 (미국, 중국)
   - 공급망 리스크

5. 투자 의견
   - 목표가
   - 투자 등급
   - 핵심 논거

JSON 형식으로 반환하세요.
"""
```

---

## LLM 선택 전략

### 작업 유형별 LLM 선택

#### Quick-thinking 모델

**용도**: 빠른 작업, 낮은 추론 필요

**모델**:
- `gpt-4o-mini`
- `gpt-3.5-turbo`
- `claude-haiku`

**사용 사례**:
- 데이터 검색
- 요약
- 간단한 변환
- 표 → 텍스트

```python
quick_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 데이터 검색 요약
summary = quick_llm.invoke("다음 데이터를 요약하세요: [데이터]")
```

#### Deep-thinking 모델

**용도**: 복잡한 추론, 분석, 의사결정

**모델**:
- `gpt-4o`
- `o1-preview`
- `claude-opus`

**사용 사례**:
- 펀더멘털 분석
- 투자 의사결정
- 복잡한 추론
- 리포트 작성

```python
deep_llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 복잡한 분석
analysis = deep_llm.invoke("""
삼성전자의 재무제표를 종합적으로 분석하고
투자 의견을 제시하세요.
[재무제표 데이터]
""")
```

### TradingAgents의 전략

```python
class LLMSelector:
    def __init__(self):
        self.quick_llm = ChatOpenAI(model="gpt-4o-mini")
        self.deep_llm = ChatOpenAI(model="gpt-4o")
    
    def get_llm(self, task_type):
        """작업 유형에 따라 LLM 선택"""
        
        quick_tasks = [
            "summarization",
            "data_retrieval",
            "table_to_text",
            "simple_classification"
        ]
        
        if task_type in quick_tasks:
            return self.quick_llm
        else:
            return self.deep_llm

# 사용 예시
selector = LLMSelector()

# 분석가: deep-thinking
fundamental_analyst = FundamentalAnalystAgent(
    llm=selector.get_llm("analysis"),
    tools=tools
)

# 데이터 검색: quick-thinking
data_retriever = DataRetrieverAgent(
    llm=selector.get_llm("data_retrieval"),
    tools=tools
)
```

---

## 실전 구현 가이드

### 통합 LLM 시스템

```python
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI

class UnifiedLLMSystem:
    def __init__(self, config):
        self.config = config
        self.llms = {}
        self._initialize_llms()
    
    def _initialize_llms(self):
        """다양한 LLM 초기화"""
        
        # OpenAI
        if self.config.get('openai_api_key'):
            self.llms['openai'] = {
                'gpt-4o': ChatOpenAI(
                    model="gpt-4o",
                    temperature=0
                ),
                'gpt-4o-mini': ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0
                )
            }
        
        # Google Gemini
        if self.config.get('google_api_key'):
            self.llms['gemini'] = {
                'gemini-3': ChatGoogleGenerativeAI(
                    model="gemini-3",
                    temperature=0
                )
            }
        
        # 로컬 모델 (Ollama)
        if self.config.get('use_local'):
            self.llms['local'] = {
                'llama2': Ollama(model="llama2"),
                'mistral': Ollama(model="mistral")
            }
    
    def get_llm(self, provider, model):
        """특정 LLM 가져오기"""
        return self.llms[provider][model]
    
    def get_best_llm(self, task_type):
        """작업 유형에 맞는 최적 LLM 선택"""
        
        if task_type == "analysis":
            # 분석 작업: 가장 강력한 모델
            if 'openai' in self.llms:
                return self.llms['openai']['gpt-4o']
            elif 'gemini' in self.llms:
                return self.llms['gemini']['gemini-3']
        
        elif task_type == "quick":
            # 빠른 작업: 효율적인 모델
            if 'openai' in self.llms:
                return self.llms['openai']['gpt-4o-mini']
        
        elif task_type == "local":
            # 로컬 처리: 오픈소스 모델
            if 'local' in self.llms:
                return self.llms['local']['llama2']
        
        # 기본값
        return list(self.llms.values())[0][list(self.llms.values())[0].keys()[0]]
```

### 프롬프트 관리 시스템

```python
class PromptManager:
    def __init__(self):
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """프롬프트 템플릿 로드"""
        
        self.templates = {
            'ontology_extraction': """
            다음 템플릿에서 온톨로지 스키마를 추출하세요.
            
            템플릿: {templates}
            
            출력 형식: JSON
            """,
            
            'entity_extraction': """
            다음 문서에서 엔티티를 추출하세요.
            
            문서: {document}
            스키마: {schema}
            
            출력 형식: JSON
            """,
            
            'analysis': """
            다음 기업을 분석하세요.
            
            기업: {company}
            데이터: {data}
            
            출력 형식: JSON
            """
        }
    
    def get_prompt(self, template_name, **kwargs):
        """프롬프트 생성"""
        template = self.templates[template_name]
        return template.format(**kwargs)
```

---

## 요약

### 핵심 포인트

1. **LLM은 강력하지만 한계 있음**: RAG로 보완 필요
2. **금융 도메인 특화**: Fine-tuned 모델 활용
3. **온톨로지 자동 생성**: 전문 템플릿 기반 LLM 활용
4. **프롬프트 엔지니어링**: 명확한 역할, 구조화된 출력, 예시 제공
5. **작업별 LLM 선택**: Quick vs Deep thinking 모델 구분

### 다음 단계

- [이전 문서: GraphRAG](05_GraphRAG.md)
- [다음 문서: 구현 방법론](07_구현_방법론.md)

---

**참고 논문**:
- FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph
- TradingAgents: Multi-Agents LLM Financial Trading Framework
- Design and Development of Financial Applications Using Ontology-Based Multi-Agent Systems

