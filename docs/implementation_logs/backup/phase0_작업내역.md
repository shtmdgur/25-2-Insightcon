# Phase 0 작업 내역

## 완료된 작업

### 0.1 LLM Config Setup ✓
**파일**: `src/utils/llm_config.py`  
**내용**:
- Quick/Deep 모델 매핑 (gemini-2.5-flash / gemini-3-pro-preview)
- Batch API 설정 (enabled, max_batch_size, polling_interval)
- 작업 유형별 모델 매핑 (`TASK_MODEL_MAPPING`)
- `get_model_config()`, `should_use_batch()`, `get_llm()` 함수

---

### 0.2 Parser Interface ✓
**파일**: `src/dataflows/parser_interface.py`  
**내용**:
- `ParserInterface` 추상 클래스
- `RobustPDFParser` 클래스 (Fallback 메커니즘)
- Primary → Secondary → Fallback 순서 자동 전환
- `ParserStrategy` Enum (PRIMARY, SECONDARY, FALLBACK)

---

### 0.3 Files API Integration ✓
**파일**: `src/utils/gemini_files.py`  
**내용**:
- `GeminiFilesClient` 클래스
- `upload_file()`: 파일 업로드 및 URI 반환
- `get_file_uri()`: 캐시된 URI 조회
- `delete_file()`, `clear_cache()`: 캐시 관리
- 싱글톤 패턴 (`get_gemini_files_client()`)
- 한글 경로 지원 및 MIME 타입 자동 감지

---

### 0.4 Gemini PDF Native Parser ✓ ⭐ **추천 방식**
**파일**: `src/dataflows/parsers/gemini_pdf.py`  
**내용**:
- `GeminiPDFParser` 클래스 - **PDF에서 Knowledge Graph 직접 추출**
- Gemini API Structured Output 활용
- PDF → Knowledge Graph JSON (원스텝 파이프라인)
- Batch API 지원 (`use_batch=True`)
- YAML 기반 프롬프트 관리

**장점**:
- ✅ PDF 전체 문맥 이해
- ✅ 일관성 있는 KG 출력
- ✅ 비용 최적화 (Batch API 50% 절감)

---

### 0.5 Neo4j Loader ✓
**파일**: `src/dataflows/neo4j_loader.py`  
**내용**:
- `Neo4jKGLoader` 클래스
- `load_knowledge_graph()`: KG를 Neo4j에 주입
- `_create_entity()`, `_create_relation()`: MERGE 전략
- `get_graph_stats()`: 그래프 통계 조회
- `load_kg_from_gemini_pdf()`: 전체 파이프라인 함수

---

### 0.6 Graph Schema Models ✓
**파일**: `src/models/graph_schema.py`  
**내용**:
- `NodeLabel` Enum: Company, Product, Metric, Event, Trend, Technology, Person
- `RelationType` Enum: PRODUCES, COMPETES_WITH, SUPPLIES_TO, HAS_METRIC, AFFECTED_BY, DEVELOPS, LEADS
- `Entity`, `Relation`, `KnowledgeGraph` Pydantic 모델
- `get_kg_json_schema()`: Gemini Structured Output용 스키마

---

## 백로그 (향후 옵션)

### VLM Parser (차트 분석 특화)
**파일**: `src/dataflows/parsers/vlm.py`  
**용도**: PDF 차트/그래프 상세 분석 (연구/탐색 단계)
**현재**: Knowledge Graph 추출은 GeminiPDFParser 사용 권장
**백로그 사유**: 
- Gemini PDF Parser가 더 정확하고 효율적
- VLM은 차트 세부 분석이 필요한 특수 케이스에만 사용
- Phase 2 이후 필요시 재검토

---

## 생성된 파일 목록
1. `src/utils/llm_config.py`
2. `src/dataflows/__init__.py`
3. `src/dataflows/parsers/__init__.py`
4. `src/dataflows/parser_interface.py`
5. `src/utils/gemini_files.py`
6. **`src/dataflows/parsers/gemini_pdf.py`** ⭐
7. **`src/dataflows/neo4j_loader.py`** ⭐
8. **`src/models/graph_schema.py`** ⭐
9. `src/dataflows/parsers/vlm.py` (백로그)

## 수정된 파일 목록
1. `src/pipeline/state.py`
2. `src/utils/llm_config.py` (get_llm 함수 추가)

---

## E2E 데모 및 문서 ✓

### 데모 스크립트
1. **`demo_e2e_pipeline.py`** - Phase 0 + Phase 1 통합 파이프라인
   - 옵션 1: VLM Parser → KG Agent → Neo4j (백로그)
   - 옵션 2: Gemini PDF Parser → Neo4j (추천 ⭐)

2. **`demo_phase1_agents.py`** - Phase 1 개별 에이전트 테스트
   - KGConstructionAgent (텍스트 전용)
   - EventExtractor
   - TimeSeriesProcessor

### 문서
1. **`docs/파서_선택_가이드.md`** - GeminiPDFParser vs VLMParser vs KGConstructionAgent 비교
2. **`test/test_phase0.py`** - Phase 0 기능 테스트 스크립트
3. **`test/test_gemini_pdf_neo4j.py`** - Gemini PDF Parser 테스트

---

---

## Raw 데이터 파싱 전략 (Layer 0.5)

### 📊 수집된 데이터 현황

| 디렉토리 | 내용 | 파일 수 | 데이터 규모 | 주요 컬럼 |
|----------|------|---------|-------------|-----------|
| `data/raw/DART` | 공시 데이터 | 3 CSV | 기업 4개, 공시 3,025건, 재무 92건 | ticker, corp_code, corp_name, revenue, operating_profit |
| `data/raw/reports` | 애널리스트 리포트 | **1,469 PDF** | ~1.5GB (2020-2025) | 증권사 분석 리포트 |
| `data/raw/news` | 뉴스 데이터 | 1 CSV | **7,500건** (3.5MB) | keyword, title, link, date, description |
| `data/raw/price` | 주가 시계열 | 23 CSV | 각 ~5년치 (2020~) | date, open, high, low, close, volume |
| `data/raw/SAX_price` | SAX 패턴 변환 | 23 CSV | 각 ~5년치 | ticker, date, price, sax_symbol, trend, volatility |
| `data/raw/macro` | 거시경제 지표 | 1 CSV | **19,673건** (470KB) | date, value, series (FRED 지표) |
| `data/raw/fund` | 펀더멘탈 데이터 | 3 CSV | 소량 (~2KB) | ticker, marketCap, totalDebt, profitMargins, ROE |
| `data/raw/ir` | IR 자료 | **60 PDF** (6개 기업) | ~50MB | 실적 발표, 지속가능성 보고서, 사업보고서 |

**주요 종목**:
- **한국**: 삼성전자(005930), SK하이닉스(000660), DB하이텍(000990), 한미반도체(091160, 102110)
- **미국**: NVDA, TSM, INTC, AMAT, ASML, LRCX, MU, AVGO
- **지수**: KOSPI, KOSDAQ, S&P500, NASDAQ, Dow
- **환율**: USD/KRW, USD/JPY

### ✅ 구현 완료: PDF Parser

**파일**: `src/dataflows/parsers/gemini_pdf.py` + `src/dataflows/neo4j_loader.py`

**기능**:
- ✅ Gemini PDF Native Parser (Knowledge Graph 직접 추출)
- ✅ Neo4j UPSERT 전략 (MERGE로 기존 데이터와 병합)
- ✅ Batch API 준비 (50% 비용 절감)

**UPSERT 전략 변경사항**:
```python
# 이전: 기존 데이터 삭제 후 재생성
# if clear_existing:
#     session.run("MATCH (n) DETACH DELETE n")

# 현재: MERGE를 통한 데이터 누적 (UPSERT)
query = f"""
MERGE (n:`{entity.label}` {{id: $id}})
SET n.name = $name
SET n += $properties
RETURN n
"""
```

**장점**:
- 동일한 PDF를 재파싱해도 중복 생성 방지
- 기존 그래프에 새로운 정보 누적
- 여러 소스의 데이터를 통합 관리

### 🔧 구현 필요: 나머지 데이터 파서

#### 1. CSV Parser (구조화 데이터)
**우선순위**: 🟡 High  
**대상**: `price/`, `SAX_price/`, `macro/`, `fund/`, `DART/`

**구현 계획**:
```python
# src/dataflows/parsers/layer0/csv_parser.py

class FinancialCSVParser:
    """CSV 데이터를 Neo4j 노드 속성으로 변환"""
    
    def parse_price_data(self, csv_path: str) -> List[dict]:
        """
        주가 CSV → TimeSeries 노드
        
        입력 컬럼: date, open, high, low, close, volume
        출력: TimeSeries 노드 + HAS_PRICE_DATA 관계
        """
        df = pd.read_csv(csv_path)
        
        results = []
        for _, row in df.iterrows():
            results.append({
                "date": row['date'],
                "ticker": self._extract_ticker(csv_path),  # 파일명에서 추출
                "ohlcv": {
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": int(row['volume'])
                }
            })
        return results
    
    def parse_sax_data(self, csv_path: str) -> List[dict]:
        """
        SAX CSV → Trend 노드
        
        입력 컬럼: ticker, date, price, sax_symbol, trend, volatility, 
                  daily_return, cumulative_return
        출력: Trend 노드 + AFFECTED_BY 관계
        """
        df = pd.read_csv(csv_path)
        
        results = []
        for _, row in df.iterrows():
            results.append({
                "ticker": row['ticker'],
                "date": row['date'],
                "sax_symbol": row['sax_symbol'],  # A~E
                "trend": row['trend'],  # Uptrend/Downtrend/Unknown
                "volatility": row['volatility'],
                "daily_return": float(row['daily_return']),
                "cumulative_return": float(row['cumulative_return'])
            })
        return results
    
    def parse_macro_data(self, csv_path: str) -> List[dict]:
        """
        거시경제 CSV → Metric 노드
        
        입력 컬럼: date, value, series
        출력: Metric 노드 (19,673건)
        
        series 종류: DGS3MO (3개월 국채), FEDFUNDS (연방기금금리) 등
        """
        df = pd.read_csv(csv_path)
        
        results = []
        for _, row in df.iterrows():
            if pd.notna(row['value']):  # NULL 값 제외
                results.append({
                    "date": row['date'],
                    "value": float(row['value']),
                    "series": row['series'],
                    "metric_type": "macro_economic"
                })
        return results
    
    def parse_fundamentals(self, csv_path: str) -> List[dict]:
        """
        펀더멘탈 CSV → Company 노드 속성
        
        입력 컬럼: ticker, currency, marketCap, totalDebt, totalCash, 
                  totalRevenue, profitMargins, returnOnEquity, returnOnAssets
        출력: Company 노드 재무 속성
        """
        df = pd.read_csv(csv_path)
        
        results = []
        for _, row in df.iterrows():
            results.append({
                "ticker": row['ticker'],
                "currency": row['currency'],
                "market_cap": float(row['marketCap']) if pd.notna(row['marketCap']) else None,
                "total_debt": float(row['totalDebt']) if pd.notna(row['totalDebt']) else None,
                "profit_margins": float(row['profitMargins']) if pd.notna(row['profitMargins']) else None,
                "roe": float(row['returnOnEquity']) if pd.notna(row['returnOnEquity']) else None
            })
        return results
    
    def parse_dart_companies(self, csv_path: str) -> List[dict]:
        """
        DART 기업정보 → Company 노드
        
        입력 컬럼: ticker, corp_code, corp_name, ceo_nm, hm_url, ir_url, adres
        출력: Company 노드 (4개 기업)
        """
        df = pd.read_csv(csv_path)
        
        return [{
            "ticker": row['ticker'],
            "corp_code": row['corp_code'],
            "name": row['corp_name'],
            "ceo": row['ceo_nm'],
            "homepage": row['hm_url'],
            "ir_url": row['ir_url'],
            "address": row['adres']
        } for _, row in df.iterrows()]
    
    def parse_dart_financials(self, csv_path: str) -> List[dict]:
        """
        DART 재무제표 → Metric 노드
        
        입력 컬럼: ticker, year, quarter_code, revenue, operating_profit, net_profit
        출력: Metric 노드 (92건 분기 실적)
        """
        df = pd.read_csv(csv_path)
        
        return [{
            "ticker": row['ticker'],
            "period": f"{row['year']}-Q{row['quarter_code']}",
            "revenue": float(row['revenue']) if pd.notna(row['revenue']) else None,
            "operating_profit": float(row['operating_profit']) if pd.notna(row['operating_profit']) else None,
            "net_profit": float(row['net_profit']) if pd.notna(row['net_profit']) else None
        } for _, row in df.iterrows()]
```

**Neo4j 주입 전략**:
```python
# MERGE 사용으로 중복 방지
def load_price_data(self, data: List[dict]):
    for record in data:
        query = """
        MERGE (c:Company {ticker: $ticker})
        MERGE (ts:TimeSeries {
            date: date($date),
            ticker: $ticker
        })
        SET ts.open = $open,
            ts.high = $high,
            ts.low = $low,
            ts.close = $close,
            ts.volume = $volume
        MERGE (c)-[:HAS_PRICE_DATA]->(ts)
        """
        self.neo4j.run(query, {
            "ticker": record['ticker'],
            "date": record['date'],
            **record['ohlcv']
        })

def load_sax_trend(self, data: List[dict]):
    for record in data:
        query = """
        MERGE (c:Company {ticker: $ticker})
        MERGE (t:Trend {
            date: date($date),
            ticker: $ticker,
            type: 'SAX_Pattern'
        })
        SET t.sax_symbol = $sax_symbol,
            t.trend = $trend,
            t.volatility = $volatility,
            t.daily_return = $daily_return,
            t.cumulative_return = $cumulative_return
        MERGE (c)-[:HAS_TREND]->(t)
        """
        self.neo4j.run(query, record)
```

#### 2. News Event Extractor
**우선순위**: 🟡 High  
**대상**: `news/Semiconductor_News_Raw_20251210.csv`

**구현 계획**:
```python
# src/dataflows/parsers/layer0/news_parser.py

class NewsEventExtractor:
    """뉴스 데이터에서 이벤트 추출"""
    
    def extract_events(self, news_csv: str) -> List[dict]:
        """
        뉴스 CSV → Event 리스트
        
        Returns:
            [
                {
                    "event_type": "실적발표",
                    "description": "SK하이닉스 4분기 영업이익 5조",
                    "date": "2024-01-26",
                    "affected_entities": ["SK하이닉스", "DRAM"],
                    "sentiment": "positive",
                    "importance": 0.85
                },
                ...
            ]
        """
        df = pd.read_csv(news_csv)
        
        events = []
        for _, row in df.iterrows():
            event = self._extract_single_event(
                title=row['title'],
                description=row['description'],
                date=row['date']
            )
            events.append(event)
        
        return events
    
    def _extract_single_event(self, title, description, date):
        """LLM을 사용한 이벤트 추출 (Gemini Flash)"""
        prompt = f"""
        뉴스에서 주요 이벤트를 추출하세요.
        
        제목: {title}
        내용: {description}
        날짜: {date}
        
        추출:
        - event_type: 실적발표|M&A|제품출시|금리변경|정책발표
        - affected_entities: [...] 
        - sentiment: positive|negative|neutral
        - importance: 0.0~1.0
        """
        
        response = self.llm.invoke(prompt)
        return self._parse_response(response)
```

**Neo4j 주입 전략**:
```python
def load_event(self, event: dict):
    query = """
    MERGE (e:Event {
        type: $event_type,
        date: datetime($date),
        description: $description
    })
    SET e.sentiment = $sentiment,
        e.importance = $importance
    
    WITH e
    UNWIND $affected_entities AS entity_name
    MATCH (c:Company {name: entity_name})
    MERGE (e)-[:AFFECTS {
        weight: $importance,
        time_decay: $time_decay
    }]->(c)
    """
    
    time_decay = self._calculate_time_decay(event['date'])
    self.neo4j.run(query, {**event, 'time_decay': time_decay})
```

#### 3. SAX TimeSeries Processor
**우선순위**: 🟡 High  
**대상**: 주가 데이터 (`SAX_price/*.csv`)

**구현**: ✅ `src/utils/time_series_processor.py` 이미 존재

**통합 필요사항**:
- CSV Parser와 연동
- SAX 데이터 직접 로드 (이미 SAX 변환 완료)
- 자동으로 Trend 노드 생성 및 Neo4j 주입

#### 4. IR 문서 Parser
**우선순위**: 🟡 High  
**대상**: `ir/` (60 PDF - 6개 기업)

**파서**: ✅ GeminiPDFParser 재사용

**IR 디렉토리 구조**:
- `Samsung/` (12개): 실적 컨퍼런스콜, 지속가능성 보고서, 사업보고서
- `SKHynix/`
- `NVIDIA/`
- `TSMC/`
- `DBHiTek/`
- `HanmiSemi/`

**특징**:
- 공식 IR 자료로 **높은 신뢰도**
- Metric 노드의 공식 수치 출처
- 사업보고서: 전략, 제품 라인업, 시장 분석 포함

**구현**:
```python
# src/dataflows/parsers/layer0/ir_parser.py

class IRDocumentParser:
    """IR 문서 파싱 (GeminiPDFParser 활용)"""
    
    def __init__(self):
        self.pdf_parser = GeminiPDFParser(model_name="gemini-2.5-flash")
    
    def parse_ir_directory(self, ir_dir: str = "data/raw/ir") -> Dict[str, List[dict]]:
        """
        IR 디렉토리 전체 파싱
        
        Returns:
            {
                "Samsung": [kg1, kg2, ...],
                "SKHynix": [...],
                ...
            }
        """
        results = {}
        
        for company_dir in Path(ir_dir).iterdir():
            if company_dir.is_dir():
                company_name = company_dir.name
                pdf_files = list(company_dir.glob("*.pdf"))
                
                results[company_name] = []
                for pdf_file in pdf_files:
                    kg = self.pdf_parser.parse(str(pdf_file))
                    results[company_name].append(kg)
        
        return results
```

#### 5. 통합 Layer0 Pipeline
**파일**: `src/dataflows/parsers/layer0/__init__.py`

```python
class Layer0Parser:
    """모든 Layer0 파서를 통합 관리"""
    
    def __init__(self):
        self.pdf_parser = GeminiPDFParser()  # ✅ 이미 구현
        self.csv_parser = FinancialCSVParser()  # TODO
        self.news_parser = NewsEventExtractor()  # TODO
        self.ts_processor = TimeSeriesProcessor()  # ✅ 이미 구현
        self.ir_parser = IRDocumentParser()  # TODO
    
    def parse_all(self, data_dir: str = "data/raw") -> dict:
        """
        data/raw 전체 파싱 → Neo4j 주입 준비
        
        Returns:
            {
                "reports": [...],      # PDF 파싱 결과 (1,469개)
                "ir_docs": {...},      # IR 문서 (60개)
                "prices": [...],       # 주가 시계열 (23개 종목)
                "sax_trends": [...],   # SAX 패턴 (23개)
                "events": [...],       # 뉴스 이벤트 (7,500건)
                "companies": [...],    # 기업 정보 (4개)
                "financials": [...],   # 재무제표 (92건)
                "fundamentals": [...], # 펀더멘탈 (3개 파일)
                "macro": [...]         # 거시경제 (19,673건)
            }
        """
        results = {}
        
        # 1. PDF 리포트 (Batch API)
        pdf_dir = f"{data_dir}/reports"
        results['reports'] = self.pdf_parser.batch_parse(pdf_dir)
        
        # 2. IR 문서
        results['ir_docs'] = self.ir_parser.parse_ir_directory(f"{data_dir}/ir")
        
        # 3. 주가 데이터
        price_files = Path(f"{data_dir}/price").glob("*.csv")
        results['prices'] = [
            self.csv_parser.parse_price_data(str(f)) 
            for f in price_files
        ]
        
        # 4. SAX 트렌드
        sax_files = Path(f"{data_dir}/SAX_price").glob("*.csv")
        results['sax_trends'] = [
            self.csv_parser.parse_sax_data(str(f))
            for f in sax_files
        ]
        
        # 5. 뉴스 이벤트
        news_file = f"{data_dir}/news/Semiconductor_News_Raw_20251210.csv"
        results['events'] = self.news_parser.extract_events(news_file)
        
        # 6. DART 데이터
        results['companies'] = self.csv_parser.parse_dart_companies(
            f"{data_dir}/DART/companies.csv"
        )
        results['financials'] = self.csv_parser.parse_dart_financials(
            f"{data_dir}/DART/financial_states.csv"
        )
        
        # 7. 펀더멘탈
        fund_files = Path(f"{data_dir}/fund").glob("*.csv")
        results['fundamentals'] = [
            self.csv_parser.parse_fundamentals(str(f))
            for f in fund_files
        ]
        
        # 8. 거시경제 지표
        results['macro'] = self.csv_parser.parse_macro_data(
            f"{data_dir}/macro/fred_rates.csv"
        )
        
        return results
```

### 📅 구현 우선순위

| 순서 | 컴포넌트 | 대상 데이터 | 상태 | 예상 시간 |
|------|----------|-------------|------|-----------|
| 1 | PDF Parser | reports (1,469 PDF) | ✅ 완료 | - |
| 2 | CSV Parser | price (23), SAX (23), DART (3) | 🔧 필요 | 1.5일 |
| 3 | News Event Extractor | news (7,500건) | 🔧 필요 | 2일 |
| 4 | SAX TimeSeries | SAX_price (23 CSV) | 🔧 필요 | 0.5일 |
| 5 | Macro/Fund Parser | macro (19,673), fund (3) | 🔧 필요 | 0.5일 |
| 6 | IR Parser | ir (60 PDF, 6개 기업) | 🔧 필요 | 1일 |
| 7 | Layer0 통합 Pipeline | 전체 | 🔧 필요 | 1일 |

**총 예상 기간**: 약 6.5일

### 💰 비용 추정

- **Gemini Flash (뉴스 이벤트 추출)**: 7,500건 × $0.001 ≈ **$7.5**
- **Gemini Flash (PDF Batch - reports)**: 1,469개 × $0.01 (Batch 50% 할인) ≈ **$7~15**
- **Gemini Flash (IR 문서)**: 60개 × $0.01 ≈ **$0.6**

**총 예상 비용**: **$15~23**

---

## 다음 단계
Layer 0.5 완료 후 → Phase 1 완료 확인 → Phase 2: 에이전트 지능 강화 시작


