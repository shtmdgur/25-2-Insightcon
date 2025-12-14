# 금융 도메인 (Finance Domain) 완전 정리 가이드

## 📖 목차
1. [금융 도메인 개요](#금융-도메인-개요)
2. [증권 리포트 분석](#증권-리포트-분석)
3. [시장 상태 예측](#시장-상태-예측)
4. [감성 분석](#감성-분석)
5. [기술적 분석](#기술적-분석)
6. [리스크 관리](#리스크-관리)
7. [실전 데이터 소스](#실전-데이터-소스)

---

## 금융 도메인 개요

### 금융 시장의 복잡성

금융 시장은 다음과 같은 복잡한 특성을 가집니다:

1. **다차원적 요인**: 기업 펀더멘털, 시장 감성, 기술적 지표, 거시경제 등
2. **동적 변화**: 실시간으로 변하는 가격과 시장 상황
3. **불확실성**: 예측 불가능한 이벤트와 변동성
4. **상호 의존성**: 다양한 자산과 시장 간 복잡한 상관관계

### 금융 분석의 3가지 접근법

#### 1. 펀더멘털 분석 (Fundamental Analysis)

**목적**: 기업의 내재가치 평가

**분석 요소**:
- 재무제표 (손익계산서, 재무상태표, 현금흐름표)
- 재무 비율 (P/E, P/B, ROE, Debt Ratio 등)
- 산업 분석
- 경쟁 우위

**예시**:
```
삼성전자 펀더멘털 분석:
- P/E Ratio: 12.5 (업계 평균: 15.0) → 저평가
- ROE: 15.3% (업계 평균: 12.0%) → 우수한 수익성
- Debt Ratio: 0.15 (업계 평균: 0.25) → 건전한 재무구조
- 결론: 내재가치 대비 저평가, 매수 권장
```

#### 2. 기술적 분석 (Technical Analysis)

**목적**: 가격 패턴과 추세 분석

**분석 요소**:
- 가격 차트 패턴
- 기술적 지표 (MACD, RSI, Bollinger Bands 등)
- 거래량 분석
- 지지/저항선

**예시**:
```
삼성전자 기술적 분석:
- MACD: 상승 추세 확인
- RSI: 58 (과매수/과매도 구간 밖)
- 지지선: 73,000원
- 저항선: 78,000원
- 결론: 상승 추세, 78,000원 돌파 시 매수
```

#### 3. 감성 분석 (Sentiment Analysis)

**목적**: 시장 심리와 투자자 감성 파악

**분석 요소**:
- 뉴스 감성
- 소셜 미디어 감성
- 내부자 거래 패턴
- 분석가 리포트 톤

**예시**:
```
삼성전자 감성 분석:
- 뉴스 감성 점수: 0.75 (긍정적)
- 소셜 미디어: 0.68 (중립-긍정)
- 분석가 리포트: 80% 매수 권장
- 결론: 전반적으로 긍정적 감성
```

---

## 증권 리포트 분석

### 증권 리포트의 구조

전형적인 증권 리포트는 다음과 같은 구조를 가집니다:

```
1. Executive Summary (요약)
   - 투자 의견 (Buy/Hold/Sell)
   - 목표가
   - 핵심 논거

2. Company Overview (기업 개요)
   - 사업 구조
   - 주요 제품/서비스
   - 시장 위치

3. Industry Analysis (산업 분석)
   - 산업 동향
   - 성장 전망
   - 경쟁 구도

4. Financial Analysis (재무 분석)
   - 재무제표 분석
   - 재무 비율
   - 실적 전망

5. Valuation (밸류에이션)
   - DCF 모델
   - 상대 밸류에이션
   - 목표가 산출

6. Risk Factors (리스크 요인)
   - 산업 리스크
   - 기업 특화 리스크
   - 거시경제 리스크

7. Investment Recommendation (투자 권장사항)
   - 최종 의견
   - 투자 전략
   - 포트폴리오 배분 제안
```

### FinKario의 리포트 분석 방법

#### 1. 문서 전처리

```python
from mineru import PDFParser

def preprocess_report(pdf_path):
    """PDF 리포트를 분석 가능한 형태로 변환"""
    
    # PDF → Markdown 변환
    parser = PDFParser()
    markdown = parser.parse(pdf_path)
    
    # 불필요한 내용 제거
    cleaned = remove_disclaimers(markdown)
    cleaned = remove_images(cleaned)
    cleaned = remove_legal_statements(cleaned)
    
    return cleaned
```

#### 2. 구조화된 정보 추출

**Attribute 추출**:
```python
def extract_attributes(document, schema):
    """증권 리포트에서 속성 정보 추출"""
    
    prompt = f"""
    다음 증권 리포트에서 기업 속성 정보를 추출하세요.
    
    문서:
    {document}
    
    스키마:
    {schema}
    
    추출할 속성:
    - 기업명, 티커, 거래소
    - 산업, 섹터
    - 시가총액, 현재가, 목표가
    - 투자 등급 (Buy/Hold/Sell)
    - 주요 제품
    - 리스크 요인
    
    JSON 형식으로 반환하세요.
    """
    
    result = llm.generate(prompt)
    return json.loads(result)
```

**Event 추출**:
```python
def extract_events(document, event_schema):
    """이벤트 정보 추출"""
    
    prompt = f"""
    다음 증권 리포트에서 이벤트 정보를 추출하세요.
    
    문서:
    {document}
    
    이벤트 스키마:
    {event_schema}
    
    추출할 이벤트:
    - 실적 발표 (Earnings)
    - 가이던스 변경 (Guidance)
    - 전략적 행동 (M&A, 해외 진출 등)
    - 기술 혁신 (신제품, 공정 개선)
    - 규제 변화
    
    각 이벤트에 대해:
    - 주체 (Subject)
    - 객체 (Object)
    - 이벤트 타입
    - 날짜
    - 설명
    
    JSON 형식으로 반환하세요.
    """
    
    result = llm.generate(prompt)
    return json.loads(result)
```

#### 3. 지식 그래프 구축

```python
def build_knowledge_graph(attributes, events):
    """추출된 정보로 지식 그래프 구축"""
    
    graph = Neo4jGraph()
    
    # Company 노드 생성
    company_node = {
        "name": attributes["company_name"],
        "ticker": attributes["ticker"],
        "exchange": attributes["exchange"],
        "industry": attributes["industry"],
        "market_cap": attributes["market_cap"]
    }
    graph.create_node("Company", company_node)
    
    # Metric 노드 생성
    for metric in attributes["metrics"]:
        metric_node = {
            "type": metric["type"],
            "value": metric["value"],
            "period": metric["period"]
        }
        graph.create_node("Metric", metric_node)
        graph.create_relationship(
            company_node["name"],
            "HAS_METRIC",
            metric_node["name"]
        )
    
    # Event 노드 생성
    for event in events:
        event_node = {
            "type": event["type"],
            "date": event["date"],
            "description": event["description"]
        }
        graph.create_node("Event", event_node)
        graph.create_relationship(
            company_node["name"],
            "TRIGGERED_BY",
            event_node["name"]
        )
    
    return graph
```

---

## 시장 상태 예측

### 시장 상태의 정의

시장 상태는 일반적으로 3가지로 분류됩니다:

1. **Bull Market (강세장)**: 상승 추세
   - 특징: 지속적인 가격 상승, 높은 거래량, 낙관적 감성
   - 전략: 성장주 중심, 공격적 투자

2. **Bear Market (약세장)**: 하락 추세
   - 특징: 지속적인 가격 하락, 높은 변동성, 비관적 감성
   - 전략: 방어주 중심, 보수적 투자

3. **Neutral Market (중립장)**: 횡보
   - 특징: 가격 변동 제한적, 낮은 거래량, 불확실성
   - 전략: 균형 잡힌 포트폴리오, 현금 보유

### Non-Stationary Markov Chain (NMC) 모델

**목적**: 시장 상태 전환을 동적으로 모델링

#### 기본 Markov Chain

**전통적인 Markov Chain**:
```
P(St+1 = Sj | St = Si) = Pij (고정 확률)
```

**문제점**: 시장 상태 전환 확률이 시간에 따라 변하지 않음

#### Non-Stationary Markov Chain

**동적 전환 확률**:
```
P(St+1 = Sj | St = Si, X(t)) = Pij(t)
```

**X(t)**: 외생 변수
- Sentiment Index (SI): 시장 감성 지수
- Illiquidity Index (ILLIQ): 유동성 지수
- VIX: 변동성 지수
- GARCH: 변동성 모델

**예시**:
```python
def calculate_transition_probability(
    current_state, 
    next_state, 
    sentiment_index, 
    illiquidity_index
):
    """외생 변수를 고려한 전환 확률 계산"""
    
    # 기본 전환 확률
    base_prob = transition_matrix[current_state][next_state]
    
    # 감성 지수 영향
    sentiment_effect = sentiment_index * 0.3
    
    # 유동성 지수 영향
    liquidity_effect = illiquidity_index * 0.2
    
    # 동적 확률 계산
    dynamic_prob = base_prob + sentiment_effect - liquidity_effect
    
    # 0과 1 사이로 제한
    return max(0, min(1, dynamic_prob))
```

#### t-Copula를 사용한 의존성 모델링

**목적**: 극단적 이벤트와 비선형 의존성 포착

**Gaussian Copula vs t-Copula**:

```
Gaussian Copula:
- 정규 분포 가정
- 극단적 이벤트 과소평가
- 대칭적 의존성

t-Copula:
- heavy-tailed 분포
- 극단적 이벤트 정확히 모델링
- 비대칭적 의존성 포착
```

**예시**:
```python
from scipy.stats import t

def t_copula_dependency(u1, u2, rho, nu):
    """t-Copula를 사용한 의존성 모델링"""
    
    # t 분포의 역변환
    t1 = t.ppf(u1, nu)
    t2 = t.ppf(u2, nu)
    
    # 상관관계 행렬
    corr_matrix = [[1, rho], [rho, 1]]
    
    # t-Copula 밀도
    copula_density = multivariate_t.pdf(
        [t1, t2], 
        corr=corr_matrix, 
        df=nu
    )
    
    return copula_density
```

### BERT를 사용한 감성 분석

**목적**: 뉴스 기사에서 시장 감성을 추출

```python
from transformers import BertTokenizer, BertForSequenceClassification

class FinancialSentimentAnalyzer:
    def __init__(self):
        self.tokenizer = BertTokenizer.from_pretrained('finbert')
        self.model = BertForSequenceClassification.from_pretrained('finbert')
    
    def analyze_sentiment(self, news_articles):
        """뉴스 기사 감성 분석"""
        
        sentiments = []
        for article in news_articles:
            # 토크나이징
            inputs = self.tokenizer(
                article,
                return_tensors='pt',
                truncation=True,
                max_length=512
            )
            
            # 감성 예측
            outputs = self.model(**inputs)
            sentiment_score = torch.softmax(outputs.logits, dim=1)
            
            sentiments.append({
                'article': article,
                'sentiment': sentiment_score[0][1].item(),  # 긍정 확률
                'label': 'positive' if sentiment_score[0][1] > 0.5 else 'negative'
            })
        
        # Sentiment Index 계산
        sentiment_index = np.mean([s['sentiment'] for s in sentiments])
        
        return {
            'individual_sentiments': sentiments,
            'sentiment_index': sentiment_index
        }
```

### LSTM을 사용한 시계열 예측

**목적**: 시장 상태의 시간적 의존성 포착

```python
import torch
import torch.nn as nn

class MarketStateLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )
        
        self.fc = nn.Linear(hidden_size, num_classes)
    
    def forward(self, x):
        # x shape: (batch, sequence_length, input_size)
        lstm_out, _ = self.lstm(x)
        
        # 마지막 시퀀스만 사용
        last_output = lstm_out[:, -1, :]
        
        # 분류
        output = self.fc(last_output)
        
        return output

# 사용 예시
model = MarketStateLSTM(
    input_size=5,  # NMC 출력, SI, ILLIQ, VIX, GARCH
    hidden_size=128,
    num_layers=2,
    num_classes=3  # Bull, Bear, Neutral
)

# 입력 데이터 준비
inputs = torch.tensor([
    [nmc_output, sentiment_index, illiquidity_index, vix, garch]
    for _ in range(sequence_length)
])

# 예측
predictions = model(inputs)
predicted_state = torch.argmax(predictions, dim=1)
```

---

## 감성 분석

### 감성 분석의 중요성

금융 시장에서 감성은 가격 변동에 큰 영향을 미칩니다:

1. **단기 가격 변동**: 감성 변화가 즉각적인 가격 변동 유발
2. **거래량 증가**: 강한 감성은 거래량 증가로 이어짐
3. **과매수/과매도**: 극단적 감성은 시장 왜곡 초래

### FIBO 온톨로지를 활용한 감성 분석

#### 텍스트 일반화 방법

**목적**: 도메인 온톨로지를 사용하여 텍스트를 일반화

**과정**:
1. 텍스트에서 용어 추출
2. FIBO 온톨로지에서 일반화된 개념 찾기
3. 일반화된 용어로 텍스트 변환

**예시**:
```
원본 텍스트:
"삼성전자의 HBM3 제품 매출이 급증하고 있습니다."

일반화 후:
"삼성전자의 HBM3 제품 매출이 급증하고 있습니다. 
[Memory, Semiconductor, Revenue, Growth]"
```

**코드 예시**:
```python
def generalize_with_fibo(text, fibo_ontology):
    """FIBO 온톨로지를 사용한 텍스트 일반화"""
    
    # 텍스트에서 용어 추출
    terms = extract_terms(text)
    
    generalizations = []
    for term in terms:
        # FIBO에서 일반화된 개념 찾기
        generalized = fibo_ontology.find_generalization(term)
        if generalized:
            generalizations.extend(generalized)
    
    # 일반화된 용어를 텍스트에 추가
    generalized_text = text + " " + ", ".join(generalizations)
    
    return generalized_text
```

#### Term Swapping (용어 교체)

**목적**: 일반화된 용어로 교체하여 데이터 증강

**과정**:
1. 원본 문장에서 용어 찾기
2. 일반화된 용어로 교체
3. 새로운 학습 샘플 생성

**예시**:
```
원본:
"USA의 반도체 수출이 증가했습니다."

일반화 1:
"United States of America의 반도체 수출이 증가했습니다."

일반화 2:
"Geographic Region Identifier의 반도체 수출이 증가했습니다."
```

#### Generalization Concatenation (일반화 연결)

**목적**: 일반화된 용어를 문장 끝에 추가

**예시**:
```
원본:
"삼성전자의 매출이 증가했습니다."

일반화 연결:
"삼성전자의 매출이 증가했습니다. 
[Company, Semiconductor, Revenue, Growth, Positive]"
```

### 감성 분류 모델

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

class FinancialSentimentClassifier:
    def __init__(self, model_name='finbert'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    def classify(self, text, use_generalization=True, fibo_ontology=None):
        """텍스트 감성 분류"""
        
        # 일반화 적용 (선택적)
        if use_generalization and fibo_ontology:
            text = generalize_with_fibo(text, fibo_ontology)
        
        # 토크나이징
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=256,
            padding=True
        )
        
        # 예측
        outputs = self.model(**inputs)
        probabilities = torch.softmax(outputs.logits, dim=1)
        
        # 레이블 매핑
        labels = ['negative', 'neutral', 'positive']
        predicted_label = labels[torch.argmax(probabilities, dim=1).item()]
        confidence = torch.max(probabilities).item()
        
        return {
            'label': predicted_label,
            'confidence': confidence,
            'probabilities': {
                label: prob.item() 
                for label, prob in zip(labels, probabilities[0])
            }
        }
```

---

## 기술적 분석

### 기술적 지표

#### 1. MACD (Moving Average Convergence Divergence)

**목적**: 추세의 방향과 강도 측정

**계산**:
```
MACD Line = 12일 EMA - 26일 EMA
Signal Line = MACD의 9일 EMA
Histogram = MACD Line - Signal Line
```

**해석**:
- MACD > Signal: 상승 추세
- MACD < Signal: 하락 추세
- Histogram 증가: 추세 강화
- Histogram 감소: 추세 약화

#### 2. RSI (Relative Strength Index)

**목적**: 과매수/과매도 구간 식별

**계산**:
```
RS = 평균 상승폭 / 평균 하락폭
RSI = 100 - (100 / (1 + RS))
```

**해석**:
- RSI > 70: 과매수 (매도 신호)
- RSI < 30: 과매도 (매수 신호)
- 30 < RSI < 70: 중립

#### 3. Bollinger Bands

**목적**: 변동성과 가격 범위 측정

**계산**:
```
Middle Band = 20일 이동평균
Upper Band = Middle + (2 × 표준편차)
Lower Band = Middle - (2 × 표준편차)
```

**해석**:
- 가격이 Upper Band 근처: 과매수 가능
- 가격이 Lower Band 근처: 과매도 가능
- 밴드 폭 증가: 변동성 증가
- 밴드 폭 감소: 변동성 감소

### 기술적 분석 구현

```python
import pandas as pd
import numpy as np
import talib

class TechnicalAnalyzer:
    def __init__(self, price_data):
        self.price_data = price_data
        self.close = price_data['close'].values
        self.high = price_data['high'].values
        self.low = price_data['low'].values
        self.volume = price_data['volume'].values
    
    def calculate_macd(self):
        """MACD 계산"""
        macd, signal, histogram = talib.MACD(
            self.close,
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )
        
        return {
            'macd': macd[-1],
            'signal': signal[-1],
            'histogram': histogram[-1],
            'trend': 'bullish' if macd[-1] > signal[-1] else 'bearish'
        }
    
    def calculate_rsi(self, period=14):
        """RSI 계산"""
        rsi = talib.RSI(self.close, timeperiod=period)
        
        current_rsi = rsi[-1]
        
        if current_rsi > 70:
            signal = 'overbought'
        elif current_rsi < 30:
            signal = 'oversold'
        else:
            signal = 'neutral'
        
        return {
            'rsi': current_rsi,
            'signal': signal
        }
    
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        """Bollinger Bands 계산"""
        upper, middle, lower = talib.BBANDS(
            self.close,
            timeperiod=period,
            nbdevup=std_dev,
            nbdevdn=std_dev
        )
        
        current_price = self.close[-1]
        
        # 밴드 위치 계산
        if current_price > upper[-1]:
            position = 'above_upper'
        elif current_price < lower[-1]:
            position = 'below_lower'
        else:
            position = 'middle'
        
        # 밴드 폭 (변동성)
        band_width = (upper[-1] - lower[-1]) / middle[-1]
        
        return {
            'upper': upper[-1],
            'middle': middle[-1],
            'lower': lower[-1],
            'current_price': current_price,
            'position': position,
            'band_width': band_width
        }
    
    def identify_support_resistance(self, window=20):
        """지지선과 저항선 식별"""
        # 최근 window 기간의 고점과 저점
        recent_highs = self.high[-window:]
        recent_lows = self.low[-window:]
        
        resistance = np.max(recent_highs)
        support = np.min(recent_lows)
        
        return {
            'support': support,
            'resistance': resistance,
            'current_price': self.close[-1]
        }
    
    def comprehensive_analysis(self):
        """종합 기술적 분석"""
        macd = self.calculate_macd()
        rsi = self.calculate_rsi()
        bb = self.calculate_bollinger_bands()
        sr = self.identify_support_resistance()
        
        # 종합 신호
        signals = []
        if macd['trend'] == 'bullish':
            signals.append('MACD 상승 추세')
        if rsi['signal'] == 'oversold':
            signals.append('RSI 과매도')
        if bb['position'] == 'below_lower':
            signals.append('Bollinger 하단 터치')
        
        recommendation = 'Buy' if len(signals) >= 2 else 'Hold'
        
        return {
            'macd': macd,
            'rsi': rsi,
            'bollinger_bands': bb,
            'support_resistance': sr,
            'signals': signals,
            'recommendation': recommendation
        }
```

---

## 리스크 관리

### 리스크의 종류

#### 1. 시장 리스크 (Market Risk)

**정의**: 시장 전체의 변동으로 인한 손실

**요인**:
- 주가 하락
- 금리 변동
- 환율 변동
- 원자재 가격 변동

**측정**:
- 변동성 (Volatility)
- 베타 (Beta)
- VaR (Value at Risk)

#### 2. 신용 리스크 (Credit Risk)

**정의**: 거래 상대방의 채무 불이행 위험

**요인**:
- 기업 파산
- 채권 불이행
- 신용 등급 하락

#### 3. 유동성 리스크 (Liquidity Risk)

**정의**: 자산을 현금으로 전환하기 어려운 위험

**요인**:
- 거래량 부족
- 시장 깊이 부족
- 매도 압력

**측정**:
- Bid-Ask Spread
- Illiquidity Index (ILLIQ)

### 리스크 관리 전략

#### 1. 분산 투자 (Diversification)

```python
def calculate_portfolio_risk(portfolio):
    """포트폴리오 리스크 계산"""
    
    # 각 자산의 가중치
    weights = np.array([asset['weight'] for asset in portfolio])
    
    # 공분산 행렬
    returns = np.array([asset['returns'] for asset in portfolio])
    cov_matrix = np.cov(returns)
    
    # 포트폴리오 변동성
    portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
    portfolio_volatility = np.sqrt(portfolio_variance)
    
    # 섹터 집중도
    sector_weights = {}
    for asset in portfolio:
        sector = asset['sector']
        sector_weights[sector] = sector_weights.get(sector, 0) + asset['weight']
    
    sector_concentration = max(sector_weights.values())
    
    return {
        'volatility': portfolio_volatility,
        'sector_concentration': sector_concentration,
        'diversification_score': 1 - sector_concentration
    }
```

#### 2. Stop-Loss 주문

```python
def set_stop_loss(entry_price, risk_tolerance=0.02):
    """Stop-Loss 가격 설정"""
    
    # 리스크 허용 범위 (예: 2%)
    stop_loss_price = entry_price * (1 - risk_tolerance)
    
    return stop_loss_price

# 사용 예시
entry_price = 75,000
stop_loss = set_stop_loss(entry_price, risk_tolerance=0.02)
# stop_loss = 73,500 (2% 하락 시 매도)
```

#### 3. 포지션 사이징

```python
def calculate_position_size(
    account_value,
    entry_price,
    stop_loss_price,
    risk_per_trade=0.01
):
    """리스크 기반 포지션 크기 계산"""
    
    # 거래당 허용 리스크 금액
    risk_amount = account_value * risk_per_trade
    
    # 주당 리스크
    risk_per_share = entry_price - stop_loss_price
    
    # 포지션 크기
    position_size = risk_amount / risk_per_share
    
    return int(position_size)

# 사용 예시
account_value = 100,000,000  # 1억원
entry_price = 75,000
stop_loss = 73,500
risk_per_trade = 0.01  # 계좌의 1%

position_size = calculate_position_size(
    account_value,
    entry_price,
    stop_loss,
    risk_per_trade
)
# position_size = 약 500주
```

---

## 실전 데이터 소스

### 한국 시장 데이터

#### 1. DART (Data Analysis, Retrieval and Transfer System)

**제공 데이터**:
- 공시 정보
- 재무제표
- 사업보고서

**API 사용 예시**:
```python
import requests

def get_dart_data(corp_code, bgn_de, end_de):
    """DART API로 공시 데이터 조회"""
    
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        'crtfc_key': 'YOUR_API_KEY',
        'corp_code': corp_code,
        'bgn_de': bgn_de,
        'end_de': end_de,
        'page_no': 1,
        'page_count': 100
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

#### 2. 한국거래소 (KRX)

**제공 데이터**:
- 일일 주가 데이터
- 거래량
- 시가총액

#### 3. 네이버/다음 금융

**제공 데이터**:
- 실시간 주가
- 뉴스
- 재무 정보

### 글로벌 데이터

#### 1. Yahoo Finance

```python
import yfinance as yf

# 주가 데이터 다운로드
ticker = yf.Ticker("005930.KS")  # 삼성전자
data = ticker.history(period="1y")

# 재무 정보
info = ticker.info
```

#### 2. Alpha Vantage

```python
from alpha_vantage.timeseries import TimeSeries

ts = TimeSeries(key='YOUR_API_KEY', output_format='pandas')
data, meta_data = ts.get_daily(symbol='AAPL', outputsize='full')
```

#### 3. Tushare (중국 시장)

**제공 데이터**:
- 주가 데이터
- 재무 데이터
- 뉴스

```python
import tushare as ts

ts.set_token('YOUR_TOKEN')
pro = ts.pro_api()

# 주가 데이터
df = pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20241231')
```

---

## 요약

### 핵심 포인트

1. **3가지 분석 접근법**: 펀더멘털, 기술적, 감성 분석
2. **시장 상태 예측**: NMC, BERT, LSTM을 활용한 다중 모달 접근
3. **감성 분석**: FIBO 온톨로지 활용한 텍스트 일반화
4. **기술적 분석**: MACD, RSI, Bollinger Bands 등 다양한 지표
5. **리스크 관리**: 분산 투자, Stop-Loss, 포지션 사이징

### 다음 단계

- [이전 문서: 멀티에이전트 시스템](03_멀티에이전트_Multi_Agent.md)
- [다음 문서: GraphRAG](05_GraphRAG.md)

---

**참고 논문**:
- FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph
- A Framework for Market State Prediction with Ontological Asset Selection
- Sentiment Classification by Incorporating Background Knowledge from Financial Ontologies
- TradingAgents: Multi-Agents LLM Financial Trading Framework

