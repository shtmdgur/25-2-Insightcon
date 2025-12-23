# Price DB Integration Plan (Hybrid RAG)

**목표**: 토론 에이전트(Debate Agent)가 시장의 추세(Trend)와 변동성(Volatility)을 근거로 제시할 수 있도록, 전처리된 가격 CSV 데이터(`data/preprocessed/price/*.csv`)를 연결합니다.

**제약 사항**: 팀원과의 Git 충돌을 방지하기 위해 `src/pipeline/nodes.py`를 직접 수정하지 않고 별도 파일로 분리합니다.

---

## 🏗️ 아키텍처 설계

### 1. 데이터 소스 (기존)
- **경로**: `data/preprocessed/price/{ticker}_states.csv`
- **내용**: 날짜(Date), 가격(Price), 추세(Trend - Uptrend/Downtrend), 변동성(Volatility - High/Med/Low), SAX Symbol.
- **역할**: Neo4j에 넣지 않고 별도로 조회하는 "경량 가격 데이터베이스(Lightweight Price DB)" 역할을 합니다.

### 2. 신규 컴포넌트 구현

#### A. `src/utils/price_data_loader.py` (유틸리티)
CSV 읽기, 캐싱, 그리고 **자연어 변환(Natural Language Formatting)**을 담당하는 전용 로더 클래스입니다.

- **주요 기능**:
    - **Lazy Loading**: 요청된 티커(Ticker)의 CSV만 그 시점에 읽어옵니다.
    - **Caching**: 한 번 읽은 데이터프레임은 메모리(`_cache`)에 담아두어 디스크 I/O를 최소화합니다.
    - **Natural Language Formatter**: LLM이 이해하기 쉬운 문장으로 데이터를 변환합니다.
        - *입력*: `2023-01-05, Downtrend, Low Volatility`
        - *출력 예시*: **"2023년 1월 5일 기준, 시장은 하락 추세(Downtrend)였으며 변동성은 낮았습니다."**

#### B. `src/pipeline/price_nodes.py` (파이프라인 노드)
`PriceDataLoader`를 호출하여 LangGraph 상태(State)에 데이터를 주입하는 노드 함수입니다.

- **함수**: `load_price_context(state: ReportState) -> ReportState`
- **로직**:
    1. `state`에서 분석 대상 기업(`target_companies`)과 날짜 정보를 추출합니다.
    2. `PriceDataLoader.get_context(ticker, date)`를 호출하여 자연어 문장을 가져옵니다.
    3. 결과를 `state["market_context"]` 필드에 저장합니다.

#### C. `src/pipeline/state.py` (상태 정의)
- **변경 사항**: `ReportState`에 필드 하나를 추가합니다.
    ```python
    market_context: Optional[str]  # 시장 상황 요약 (자연어)
    ```

---

## 📅 구현 단계

1.  **유틸리티 구현**: `src/utils/price_data_loader.py` 작성
2.  **노드 구현**: `src/pipeline/price_nodes.py` 작성
3.  **상태 업데이트**: `src/pipeline/state.py` 수정
4.  **검증(Verification)**:
    - 단위 테스트: 로더가 CSV를 잘 읽고 문장으로 잘 변환하는지 확인
    - 통합 테스트: `price_node`가 상태(State)를 올바르게 업데이트하는지 확인

## ✅ 기대 효과
토론 에이전트가 다음과 같이 풍부한 근거를 들어 주장을 펼칠 수 있게 됩니다:
> *"긍정적인 뉴스가 발표되었음에도 불구하고, **당시 시장은 강력한 하락 추세(Downtrend)와 높은 변동성(High Volatility)을 보이고 있어** 주가 상승이 제한적이었습니다."*
