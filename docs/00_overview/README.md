# 📚 반도체 증권 리포트 시스템 - 논문 정리 문서

이 디렉토리에는 프로젝트에 필요한 모든 논문 내용이 상세하게 정리되어 있습니다.

## 📖 문서 목차

### 1. [온톨로지 (Ontology)](01_온톨로지_Ontology.md)
- 온톨로지 기본 개념
- 금융 도메인 온톨로지 (FIBO)
- FinKario의 이중 스키마 설계
- LLM 기반 온톨로지 자동 생성
- MOMA 방법론 (5단계 개발 프로세스)
- 한국 반도체 섹터 온톨로지 설계 예시

### 2. [지식 그래프 (Knowledge Graph)](02_지식그래프_Knowledge_Graph.md)
- 지식 그래프 기본 개념
- FinKario의 지식 그래프 구조
- Attribute Subgraph + Event Subgraph
- 자동 구축 파이프라인 (4단계)
- 품질 관리 및 정제 방법
- MDGNN의 다중 관계 동적 그래프

### 3. [멀티에이전트 시스템 (Multi-Agent Systems)](03_멀티에이전트_Multi_Agent.md)
- 멀티에이전트 시스템 기본 개념
- TradingAgents 프레임워크 상세 분석
- 7가지 에이전트 역할 (Analyst, Researcher, Trader, Risk Manager 등)
- 구조화된 통신 프로토콜
- ReAct 프레임워크
- LangGraph를 사용한 워크플로우 설계

### 4. [금융 도메인 (Finance Domain)](04_금융_도메인_Finance.md)
- 금융 분석 3가지 접근법 (펀더멘털, 기술적, 감성)
- 증권 리포트 분석 방법
- 시장 상태 예측 (NMC, BERT, LSTM)
- FIBO 온톨로지를 활용한 감성 분석
- 기술적 분석 지표 (MACD, RSI, Bollinger Bands)
- 리스크 관리 전략
- 실전 데이터 소스

### 5. [GraphRAG](05_GraphRAG.md)
- GraphRAG 기본 개념
- 전통적인 RAG vs GraphRAG 비교
- FinKario-RAG 2단계 검색 전략
- Microsoft GraphRAG 패턴 (글로벌/로컬 검색)
- Cypher 쿼리 자동 생성
- 완전한 GraphRAG 파이프라인 구현

### 6. [LLM 활용](06_LLM_활용.md)
- LLM 기본 개념 및 작동 원리
- 금융 도메인 LLM (BloombergGPT, FinGPT, FinBERT)
- 온톨로지 스키마 자동 생성 방법
- 엔티티·관계 추출
- 프롬프트 엔지니어링 베스트 프랙티스
- LLM 선택 전략 (Quick-thinking vs Deep-thinking)

### 7. [구현 방법론](07_구현_방법론.md)
- 전체 개발 프로세스
- 3주 MVP 개발 계획 (상세 일정)
- 기술 스택 선택 가이드
- 아키텍처 설계
- 단계별 구현 가이드
- 베스트 프랙티스
- 문제 해결 가이드

---

## 🎯 빠른 시작 가이드

### 처음 시작하는 경우

1. **기본 개념 이해**: [온톨로지](01_온톨로지_Ontology.md) → [지식 그래프](02_지식그래프_Knowledge_Graph.md)
2. **시스템 구조 이해**: [멀티에이전트](03_멀티에이전트_Multi_Agent.md) → [GraphRAG](05_GraphRAG.md)
3. **도메인 지식**: [금융 도메인](04_금융_도메인_Finance.md)
4. **구현 시작**: [LLM 활용](06_LLM_활용.md) → [구현 방법론](07_구현_방법론.md)

### 특정 주제를 찾는 경우

- **온톨로지를 어떻게 만들지?** → [01_온톨로지_Ontology.md](01_온톨로지_Ontology.md)
- **지식 그래프는 어떻게 구축하지?** → [02_지식그래프_Knowledge_Graph.md](02_지식그래프_Knowledge_Graph.md)
- **에이전트는 어떻게 설계하지?** → [03_멀티에이전트_Multi_Agent.md](03_멀티에이전트_Multi_Agent.md)
- **GraphRAG는 어떻게 구현하지?** → [05_GraphRAG.md](05_GraphRAG.md)
- **LLM은 어떻게 활용하지?** → [06_LLM_활용.md](06_LLM_활용.md)
- **실제로 어떻게 개발하지?** → [07_구현_방법론.md](07_구현_방법론.md)

---

## 📚 참고 논문 목록

이 문서들은 다음 논문들을 기반으로 작성되었습니다:

1. **FinKario**: Event-Enhanced Automated Construction of Financial Knowledge Graph
   - 이중 스키마 설계 (Attribute + Event)
   - LLM 기반 자동 구축 파이프라인
   - FinKario-RAG 2단계 검색

2. **TradingAgents**: Multi-Agents LLM Financial Trading Framework
   - 7가지 에이전트 역할 분화
   - 구조화된 통신 프로토콜
   - ReAct 프레임워크

3. **Design and Development of Financial Applications Using Ontology-Based Multi-Agent Systems**
   - MOMA 방법론 (5단계 온톨로지 개발)
   - 온톨로지 기반 멀티에이전트 시스템

4. **A Framework for Market State Prediction with Ontological Asset Selection**
   - 온톨로지 기반 주식 선택
   - NMC, BERT, LSTM을 활용한 시장 상태 예측

5. **Sentiment Classification by Incorporating Background Knowledge from Financial Ontologies**
   - FIBO 온톨로지 활용
   - 텍스트 일반화 방법

6. **MDGNN**: Multi-Relational Dynamic Graph Neural Network
   - 다중 관계 동적 그래프
   - Industry, Bank, Stock 관계 모델링

7. **Knowledge graphs as tools for explainable machine learning: A survey**
   - GraphRAG 패턴
   - 지식 그래프 기반 설명 가능한 AI

---

## 🔑 핵심 개념 요약

### 온톨로지
- **정의**: 도메인의 개념, 관계, 인스턴스를 구조화한 지식 표현
- **구성**: TBox (개념, 속성) + ABox (개체, 명제)
- **자동 생성**: LLM + 전문 템플릿 → 스키마 추출

### 지식 그래프
- **구조**: 노드 (엔티티) + 엣지 (관계) + 속성
- **이중 설계**: Attribute Graph (정적) + Event Graph (동적)
- **자동 구축**: 수집 → 스키마 → 추출 → 정제

### 멀티에이전트
- **역할 분화**: Analyst, Researcher, Trader, Risk Manager
- **통신**: 구조화된 문서 + 자연어 토론
- **워크플로우**: LangGraph로 상태 관리

### GraphRAG
- **2단계 검색**: Coarse-grained → Fine-grained
- **서브그래프**: 관련 엔티티만 선택적 검색
- **Cypher 생성**: 자연어 → Cypher 자동 변환

### LLM 활용
- **온톨로지 생성**: 전문 템플릿 기반 자동 추출
- **엔티티 추출**: 문서에서 구조화된 정보 추출
- **선택 전략**: Quick-thinking vs Deep-thinking

---

## 💡 실전 적용 팁

### 3주 MVP 개발 시

1. **Week 1**: 기반 구축에 집중
   - Neo4j 설정 완료
   - LangGraph 기본 구조
   - GraphRAG 기본 통합

2. **Week 2**: 핵심 에이전트 우선
   - Ontology Architect (neo4j-graphrag 활용)
   - Sector/Company Analyst
   - Quality Check (기본만)

3. **Week 3**: 통합 및 완성
   - 전체 워크플로우 연결
   - 리포트 생성
   - 기본 테스트

### 시간 절약 팁

1. **기존 라이브러리 활용**
   - `neo4j-graphrag.SchemaFromTextExtractor`
   - LangChain 통합 도구들

2. **샘플 데이터로 빠른 검증**
   - 실제 대량 데이터보다 작은 샘플로 먼저 검증

3. **프롬프트 템플릿 재사용**
   - 공통 프롬프트 패턴 추출

---

## 📞 추가 도움

각 문서에는 상세한 예시 코드와 설명이 포함되어 있습니다. 
특정 부분이 이해되지 않으면 해당 문서의 해당 섹션을 다시 읽어보세요.

**문서 구조**:
- 각 문서는 독립적으로 읽을 수 있도록 구성
- 이전 개념 참조 시 링크 제공
- 코드 예시와 다이어그램 포함
- 실전 적용 가이드 포함

---

**작성일**: 2025년 12월  
**버전**: 1.0  
**대상**: 프로젝트 개발자 및 이해관계자

