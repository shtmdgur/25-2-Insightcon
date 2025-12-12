**2.5** **5.5**

### **Article**

# **A Framework for Market State** **Prediction with Ontological Asset** **Selection: A Multimodal Approach**


**Igor Felipe Carboni Battazza, Cleyton Mário de Oliveira Rodrigues and João Fausto L. de Oliveira**




Article
## **A Framework for Market State Prediction with Ontological Asset** **Selection: A Multimodal Approach**


**Igor Felipe Carboni Battazza** **[1,2,]** ***** **[,†]** **, Cleyton Mário de Oliveira Rodrigues** **[2,†]** **and João Fausto L. de Oliveira** **[2,†]**


1 Polytechnic School of Pernambuco, POLI/UPE, Rua Benfica, 455, Recife 50720-001, Pernambuco, Brazil
2 FITec—Technological Innovations, Cais do Apolo, 222-12º andar, Recife 50030-230, Pernambuco, Brazil;
cleyton.rodrigues@upe.br (C.M.d.O.R.); fausto.lorenzato@upe.br (J.F.L.d.O.)

***** Correspondence: ifcb@ecomp.poli.br; Tel.: +55-19-98718-3729

                      - These authors contributed equally to this work.



Academic Editor: Andrea Prati


Received: 30 December 2024


Revised: 14 January 2025


Accepted: 16 January 2025


Published: 21 January 2025


**Citation:** Battazza, I.F.C.; Rodrigues,


C.M.d.O.; Oliveira, J.F.L.d. A


Framework for Market State


Prediction with Ontological Asset


Selection: A Multimodal Approach.


Appl. Sci. **2025** [, 15, 1034. https://](https://doi.org/10.3390/app15031034)


[doi.org/10.3390/app15031034](https://doi.org/10.3390/app15031034)


**Copyright:** © 2025 by the authors.


Licensee MDPI, Basel, Switzerland.


This article is an open access article


distributed under the terms and


conditions of the Creative Commons


Attribution (CC BY) license


[(https://creativecommons.org/](https://creativecommons.org/licenses/by/4.0/)


[licenses/by/4.0/).](https://creativecommons.org/licenses/by/4.0/)



**Abstract:** In this study, we introduce a detailed framework for predicting market conditions
and selecting stocks by integrating machine learning techniques with ontological financial
analysis. The process starts with ontology-based stock selection, categorizing companies
using fundamental financial indicators such as liquidity, profitability, debt ratios, and
growth metrics. For instance, firms showcasing favorable debt-to-equity ratios along
with robust revenue growth are identified as high-performing entities. This classification
facilitates targeted analyses of market dynamics. To predict market states—categorizing
them into bull, bear, or neutral phases—the framework utilizes a Non-Stationary Markov
Chain (NMC), BERT, to assess sentiment in financial news articles and Long Short-Term
Memory (LSTM) networks to identify temporal patterns. Key inputs like the Sentiment
Index (SI) and Illiquidity Index (ILLIQ) play essential roles in dynamically influencing
regime predictions within the NMC model; these inputs are supplemented by variables
including GARCH volatility and VIX to enhance predictive precision further still. Empirical
findings demonstrate that our approach achieves an impressive 97.20% accuracy rate for
classifying market states, significantly surpassing traditional methods like Naive Bayes,
Logistic Regression, KNN, Decision Tree, ANN, Random Forest, and XGBoost. The statepredicted strategy leverages this framework to dynamically adjust portfolio positions
based on projected market conditions. It prioritizes growth-oriented assets during bull
markets, defensive assets in bear markets, and maintains balanced portfolios in neutral
states. Comparative testing showed that this approach achieved an average cumulative
return of 13.67%, outperforming the Buy and Hold method’s return of 8.62%. Specifically,
for the S&P 500 index, returns were recorded at 6.36% compared with just a 1.08% gain from
Buy and Hold strategies alone. These results underscore the robustness of our framework
and its potential advantages for improving decision-making within quantitative trading
environments as well as asset selection processes.


**Keywords:** stock selection; market regime forecasting; market sentiment; liquidity risk;
exogenous variables; forecasting; machine learning; quantitative trading; investment
strategy; financial markets


**1. Introduction**


Predicting financial markets is a significant challenge for both academia and the investment industry due to their inherent complexity and volatility. Machine learning (ML)
techniques have substantially improved forecasting accuracy, with some studies, such
as Yu and Li (2018) [1], reporting prediction accuracies of up to 90% in certain scenarios.



Appl. Sci. **2025**, 15, 1034 [https://doi.org/10.3390/app15031034](https://doi.org/10.3390/app15031034)


Appl. Sci. **2025**, 15, 1034 2 of 31


However, traditional methods often struggle to encompass the multidimensional nature of
financial markets within a single framework—considering elements like investor sentiment,
liquidity, and fundamental analysis. For instance, statistical models like GARCH and
ARIMA are effective at identifying historical price patterns but fail to incorporate macroeconomic indicators or real-time shifts in sentiment; this issue is highlighted by Kim and
Won (2018) [2]. Similarly, although sentiment analysis models excel at processing textual
data related to public mood or news sentiments about stocks or sectors, they frequently
exclude company-specific financial metrics, which limits their broader applicability across
different contexts.
Market states, often categorized as bull (upward trend), bear (downward trend),
or neutral (sideways movement), represent distinct phases of market behavior. These
states are derived from both historical and real-time data, offering simplified yet insightful
representations of market dynamics. Accurate forecasting of market states is essential for
enabling investors to dynamically adjust their strategies. For example, recognizing an impending bull market can support risk-on strategies aimed at maximizing returns, whereas
anticipating a bear market may prompt risk-off approaches to minimize losses. Identifying
neutral phases allows for balanced portfolio strategies, preserving capital during periods
of uncertainty. Integrating these market state predictions into financial models enhances
their robustness by incorporating both quantitative and qualitative factors, bridging the
gap between theoretical research and practical applications in the investment industry.
These challenges have driven the development of hybrid models that integrate diverse
data sources and predictive techniques. Bhuyan and Sastry (2023) [3], for example, introduced financial ontologies to classify companies based on key metrics such as liquidity,
profitability, and growth, offering a structured approach to stock selection. However, their
methodology lacks integration with advanced machine learning models capable of predicting dynamic market conditions. Similarly, Liu et al. (2022) [4] proposed a multimodal
framework combining sentiment analysis with machine learning but did not leverage
ontological analysis for stock classification, leaving a critical gap between asset selection
and market state prediction.
This study addresses these gaps by proposing a unified framework that integrates
ontology-based stock selection with advanced machine learning techniques to predict
market states. The framework introduces several key innovations:


1. Ontology-Based Stock Selection: A systematic method for classifying stocks using
financial indicators like liquidity, profitability, debt, and growth to effectively identify
high-performing assets.
2. Non-Stationary Markov Chain (NMC): A model for dynamic market state transitions
incorporating t-copulas and exogenous variables such as the Illiquidity Index (ILLIQ)
ajnd Sentiment Index (SI).
3. Sentiment Analysis with BERT: Use of the Bidirectional Encoder Representations from
Transformers (BERT) model to extract market sentiment from financial news and
predict future market states.
4. Prediction with LSTM: An approach that captures temporal dependencies in market
states by integrating outputs from the NMC, sentiment scores, and external variables
like volatility (VIX) and GARCH.


By integrating these components, the proposed framework offers a comprehensive solution that unites technical, fundamental, and sentiment analyses. This approach surpasses
previous efforts where these methods were applied separately. Empirical evaluations
highlight its effectiveness with an impressive prediction accuracy of 97.20% and an average cumulative return of 13.67%, significantly outperforming the 8.62% accuracy of the
buy-and-hold strategy.


Appl. Sci. **2025**, 15, 1034 3 of 31


This study contributes to the field of quantitative trading through the following:


           - Presenting a unified framework that combines ontological financial analysis, machine
learning, and sentiment modeling;

           - Demonstrating the effectiveness of integrating financial ontologies with predictive
models for dynamic stock selection and market state forecasting;

           - Providing empirical evidence of robust performance across diverse market conditions.


The remainder of this paper is structured as follows: Section 2 presents the theoretical
framework underlying the proposed approach. Section 3 details the methodology, including
ontology-based stock selection and market state prediction. Section 4 discusses the results,
including model evaluations, computational costs, and strategy comparisons. Finally,
Section 5 highlights the implications and contributions of the study.


**2. Related Work**


Extensive research has been conducted on utilizing machine learning, sentiment
analysis, and econometric models to predict market conditions and choose stocks. However,
many existing approaches primarily focus on a single element—such as technical indicators,
sentiment data, or fundamental metrics—which limits their effectiveness and adaptability
in dynamic markets. This section reviews significant studies in the field and highlights
how our proposed framework offers innovative enhancements.


2.1. Technical Analysis Models


Traditional financial market prediction methods primarily rely on technical analysis,
which uses historical price and volume data. Models such as ARIMA, GARCH, and hybrid approaches incorporating LSTM have been extensively applied. For example, Kim
and Won (2018) [2] integrated LSTM with GARCH-type models to predict stock index
volatility. While these models are effective for time series analysis, they often overlook the
potential integration of exogenous variables, such as market sentiment or macroeconomic
indicators, which could enhance predictive accuracy by capturing additional dimensions
of market behavior.
These models are not inherently limited from including external variables. For example, methods like ARIMAX (ARIMA with exogenous variables) and GARCH-X have shown
that it is possible to integrate outside factors into statistical models, thereby improving
their ability to explain market behavior. Likewise, LSTM architectures can easily handle
multiple inputs, making them ideally suited for frameworks incorporating elements such
as GARCH, VIX, or sentiment indices. The research by Guo and Lin (2018) [5] emphasizes
the adaptability of LSTMs in managing multivariate time series; they effectively capture
temporal relationships while considering the significance of external influences using an
attention mechanism. This capability positions LSTM architectures as a natural choice for
financial settings demanding integration of diverse data sources.
Additionally, the work of Cai et al. (2024) [6] demonstrates the advantages of combining LSTM with techniques like CEEMDAN to decompose and integrate exogenous features,
further improving the accuracy of financial time series predictions. The results indicate
that LSTM models, when coupled with carefully selected exogenous variables, outperform
traditional methods by capturing complex, nonlinear dependencies in market dynamics.
In the proposed framework, the exogenous variables incorporated are specifically
limited to GARCH, representing historical volatility, and VIX, reflecting implied market
volatility. These variables are directly integrated into the LSTM, providing a targeted
yet robust approach to capturing the external dynamics influencing market states. This
focused selection ensures that the framework remains computationally efficient while
addressing critical aspects of market variability. By leveraging the strengths of LSTM for


Appl. Sci. **2025**, 15, 1034 4 of 31


multivariate analysis, the framework achieves a balance between model complexity and
predictive performance.


2.2. Sentiment Analysis-Based Approaches


With the advent of Natural Language Processing (NLP), sentiment analysis has become a popular method for market prediction. Sousa et al. (2020) [7] utilized BERT to
extract sentiment from financial news and showed significant improvements in stock trend
classification. Similarly, Zhou (2023) [8] constructed a Sentiment Index (SI) to evaluate
investor sentiment and its impact on returns. Although sentiment-based models provide
valuable insights, they often fail to integrate temporal dependencies or company-specific
financial metrics.


2.3. Ontology-Based Financial Analysis


The use of financial ontologies has emerged as an innovative approach for stock
selection. Financial ontologies are structured frameworks that organize and represent
financial concepts—such as liquidity, profitability, debt, and growth—into hierarchical
categories. By providing a systematic classification of financial data, these ontologies
enable consistent evaluation and facilitate the identification of high-performing stocks
based on predefined financial criteria. Gerber et al. (2015) [9] highlighted how ontologies
can represent financial concepts systematically, allowing for more structured and coherent
data analysis.
Bhuyan and Sastry (2023) [3] introduced a methodology that maps financial indicators
into an ontological structure to classify stocks. Their approach demonstrated significant
potential in categorizing companies based on fundamental metrics. However, despite its
strengths, their work is limited to static classification and lacks integration with dynamic
market state prediction models. Furthermore, it does not incorporate real-time sentiment
analysis, which is crucial for adapting to rapidly evolving market environments.
The proposed framework builds upon and extends this ontology-based classification by addressing these limitations. Unlike prior approaches, it incorporates a dynamic
component that continuously updates financial indicators within the ontological structure, reflecting changes in real-time market conditions. This dynamic integration creates
a feedback loop, allowing the ontology to adapt as new data become available. As highlighted by Sharma et al. (2023) [10], such integration of ontologies with dynamic updates
and machine learning enhances decision-making by aligning classifications with evolving
market dynamics.
Moreover, the framework leverages the ability of financial ontologies to integrate
diverse data sources, including fundamental financial metrics and sentiment analysis.
The work by Sharma et al. (2023) [10] further supports the utility of ontologies in combining structured data with real-time updates for enhanced stock selection processes. This
structured classification is seamlessly integrated into the broader framework, ensuring
that the identified stocks are potential candidates for further analysis by advanced predictive techniques.
The novelty of this framework lies in its ability to dynamically organize fundamental
financial data and facilitate a continuous pipeline for asset selection. After identifying
high-potential stocks, the framework transitions to a predictive stage where Non-Stationary
Markov Chains (NMCs), Bidirectional Encoder Representations from Transformers (BERT)
for sentiment analysis, and Long Short-Term Memory (LSTM) are employed to forecast
market states for the selected assets. These predictions guide decision-making in the subsequent stages of the pipeline, enabling the execution of optimized buy-and-sell strategies.


Appl. Sci. **2025**, 15, 1034 5 of 31


By leveraging these advanced techniques, the framework aims to maximize returns and
consistently outperform traditional strategies, such as Buy and Hold.
To the best of our knowledge, no prior work has integrated financial ontologies with
dynamic market state prediction and real-time sentiment analysis. This novel integration
provides a comprehensive solution that bridges the gap between structured asset classification and dynamic predictive modeling, offering a robust tool for quantitative trading and
investment strategies.


2.4. Hybrid Approaches for Market Prediction


Recent studies have explored hybrid approaches that combine various data sources
and models to improve market prediction. Liu et al. (2022) [4] introduced a multimodal framework using Non-Stationary Markov Chains (NMCs), BERT for sentiment
analysis, and LSTM to understand temporal dependencies better. Likewise, Wani and
Sujithkumar (2023) [11] proposed a machine learning method leveraging order book details to highlight how detailed datasets can enhance predictive accuracy. Roszyk and
Slepaczuk (2024) [12] demonstrated the effectiveness of hybrid frameworks by integrating
VIX, GARCH, and LSTM to forecast S&P 500 volatility, showcasing how ensemble methods
can improve predictive precision in financial markets.
Mero et al. (2024) [13] expanded the functionality of LSTM networks by incorporating genetic algorithms to optimize hyperparameters, resulting in significantly improved
performance for forecasting unemployment rates. This method underscores the benefits
of combining optimization techniques with recurrent models to enhance accuracy in time
series prediction. Similarly, de Luca Avila and De Bona (2020) [14] demonstrated the effectiveness of combining CEEMDAN and LSTM with exogenous features to improve financial
time series forecasting, further highlighting the versatility of LSTM-based approaches.
Mirmozaffari et al. (2020) [15] proposed an innovative hybrid approach that combined Data Envelopment Analysis (DEA) with machine learning techniques to assess
eco-efficiency. Their study highlighted the effectiveness of integrating optimization models
with data-driven approaches for identifying patterns and enhancing decision-making in
resource-intensive industries. Following this work, Mirmozaffari et al. (2021) [16] explored
various optimization strategies such as DEA to boost productivity and sustainability using
hybrid machine learning models.
In the meantime, Gorgolis and colleagues (2019) [17] highlighted the importance of
hyperparameter optimization by utilizing Genetic Algorithms (GAs) to enhance Long
Short-Term Memory (LSTM) model performance. This approach allowed for automated
selection of key parameters, surpassing traditional methods in effectiveness.
Despite significant advancements in these models, they frequently fall short of providing a unified method for integrating various dimensions of financial data. This includes
essential elements like ontological classifications and macroeconomic indicators, which are
critical for navigating dynamic market conditions.


2.5. Comparison with the Proposed Framework


The proposed framework advances the state of the art by addressing key limitations
of existing approaches:


           - Integration of Stock Selection and Market Prediction: Unlike existing works that treat
stock selection and market state prediction as independent tasks, our framework
combines an ontology-based stock classification system with a dynamic market state
prediction model.

           - Multimodal Data Integration: The approach integrates three critical dimensions—financial
fundamentals (via ontology), market sentiment (via BERT), and dynamic market


Appl. Sci. **2025**, 15, 1034 6 of 31


regimes (via NMC and LSTM). This multimodal integration enhances predictive
accuracy and decision-making capabilities.

           - Dynamic Framework Update: By incorporating real-time financial indicators and
exogenous variables such as VIX, GARCH volatility, and the Illiquidity Index (ILLIQ),
the framework adapts to changing market conditions.

           - Dynamic Adaptability: By incorporating real-time financial indicators and exogenous
variables such as VIX, GARCH volatility, and the Illiquidity Index (ILLIQ), the framework dynamically integrates updated market information to enhance its predictive
capabilities. While the framework does not involve automatic parameter adjustments
typically associated with adaptive machine learning algorithms, it enables decisionmaking that is responsive to changing market conditions through the integration of
continuously updated data sources.

           - Superior Performance: Empirical results show that the proposed framework achieves
a market state prediction accuracy of 97.20% and outperforms baseline models like
RNN, Random Forest, and XGBoost. The stock selection and prediction-based trading
strategy generated cumulative returns of 13.67%, significantly higher than the 8.62%
from the Buy and Hold strategy.


In summary, the proposed framework sets itself apart from existing methods by
providing a comprehensive and unified approach to stock selection and market state
prediction. It integrates ontology-based financial analysis with advanced machine learning
techniques, effectively bridging technical, fundamental, and sentiment analyses. This
creates a strong solution for quantitative trading. Comparative evaluations show that our
method not only overcomes current limitations but also outperforms others in terms of
performance, making it an important contribution to the field of financial market prediction.


**3. Theoretical Framework**


This section presents the theoretical foundation for the proposed framework, integrating financial ontologies, stochastic models, and machine learning techniques. The mathematical principles and structures underpinning each component are outlined, establishing
a cohesive context for the methodology. The integration of these methodologies is visually summarized in Figure 1, which provides an overview of the key components and
their interconnections.


**Figure 1.** The framework combines ontology-based stock selection with market state prediction.
Selected stocks are processed through NMC and BERT models, providing outputs that, along with
market volatility (VIX) and stock volatility (GARCH), serve as inputs to the LSTM. The LSTM’s
hyperparameters are tuned to enhance performance, enabling the prediction of market states, which
are then used to inform trading strategies.


Appl. Sci. **2025**, 15, 1034 7 of 31


3.1. Financial Ontologies in Asset Selection


Financial ontologies represent structured, hierarchical frameworks O that map financial indicators F = { f1, f2, . . ., fn} into categories such as liquidity, profitability, debt,
and growth. Formally, an ontology can be defined as a tuple:


O = (C, R, I), (1)


where C denotes the set of concepts (e.g., liquidity levels), R the set of relationships (e.g., “is
a” or “has component”), and I the set of instances (e.g., company-specific financial metrics).
The ontology is iteratively refined by incorporating new data streams D(t), ensuring
real-time responsiveness to evolving market conditions:


O(t + 1) = O(t) ∪ ∆D(t), (2)


where ∆D(t) represents the incremental update at time t. This process allows for the
continuous evolution of stock classifications, bridging the gap between static evaluations
and the fluid nature of financial markets. The structured organization and iterative updates
provided by ontologies have been shown to significantly enhance the interpretation and
utilization of financial data, as highlighted by Dudycz and Korczak (2015) [18].


3.2. Stochastic Models and Non-Stationary Markov Chains


Financial markets are naturally dynamic, shifting between different phases like “bull
markets”, where asset prices rise; “bear markets”, characterized by falling prices; and
“neutral markets”, marked by stable price trends. These shifts are not predetermined
but result from a complex mix of factors such as market sentiment, liquidity conditions,
and macroeconomic events.
To capture this complexity, we use a Non-Stationary Markov Chain (NMC) framework
in which the transition probabilities between market states change dynamically over time.
Unlike traditional Markov Chains with fixed probabilities, the NMC integrates external
variables like the Sentiment Index (SI) and Illiquidity Index (ILLIQ), enabling it to adapt to
shifting market conditions. This dynamic approach makes the NMC especially effective at
representing the stochastic and evolving nature of financial markets.
Additionally, financial markets frequently display complex dependencies and experience extreme events, particularly during times of economic shocks or crises. For instance,
an abrupt increase in illiquidity can align with steep drops in asset prices, triggering a chain
reaction of market stress. To effectively capture these interdependencies, we incorporate
t-copulas into the NMC framework. t-copulas excel at modeling heavy-tailed distributions
and asymmetric relationships that are prevalent in financial data but often neglected by
conventional methods. This integration enables the model to not only monitor market
dynamics but also predict extreme behaviors more accurately.
t-copulas are superior because they effectively capture nonlinear dependencies and
the simultaneous occurrence of extreme events typically linked to market stress. As shown
in Figure 2, t-copulas surpass Gaussian copulas by accurately depicting tail dependencies
and extreme co-movements, which is evident from the broader dispersion observed in the
scatterplot. This improved capability allows for a more realistic and robust modeling of
financial market dynamics, especially during periods of heightened uncertainty.


Appl. Sci. **2025**, 15, 1034 8 of 31


**Figure 2.** Comparison of dependency structures modeled by t-copulas and Gaussian copulas. The tcopulas ( **left** ) capture heavy-tailed dependencies and simultaneous extreme events, while the Gaussian copulas ( **right** ) fail to represent such extremes effectively.


To illustrate how these dependencies influence market state transitions, Figure 3
shows a heatmap of a dynamic transition matrix generated for SI = 0.5 and ILLIQ = 0.3.
The darker colors in the heatmap indicate higher probabilities, highlighting the flexibility
of the NMC framework in adapting to different market conditions.


**Figure 3.** Dynamic transition matrix generated for sentiment index SI = 0.5 and illiquidity index
ILLIQ = 0.3. The heatmap illustrates the transition probabilities between market states, with darker
colors indicating higher probabilities.


This combined approach leverages the strengths of Markov Chains in modeling
temporal transitions and copulas in capturing complex dependency structures, providing a
robust tool for predicting market behaviors under varying conditions.
Stochastic models capture the probabilistic nature of financial market transitions. Let
the market state St at time t be defined by a discrete random variable taking values in a
finite set {S1, S2, . . ., Sk}. The transitions between states are governed by a Non-Stationary
Markov Chain (NMC), where the transition probability matrix **P** (t) varies with time:


Appl. Sci. **2025**, 15, 1034 9 of 31


Pij(t) = P(St+1 = Sj | St = Si, **X** (t)), (3)


with **X** (t) representing exogenous inputs such as the Sentiment Index (SI) and Illiquidity
Index (ILLIQ). The use of Non-Stationary Markov Chains allows for the modeling of
dynamic transitions between market states, offering a flexible and probabilistic framework
for financial market analysis, as highlighted by Norberg (1999) [19].
The dependency structure among states and inputs is modeled using t-copulas
Ct(u1, . . ., uk; _ν_ ), where ui = Fi(St) is the marginal distribution of state i and _ν_ represents
the degrees of freedom:




         u1
Ct(u1, . . ., uk; _ν_ ) =



ft(x1, . . ., xk; _ν_ )dx1 . . . dxk. (4)
0




   
u1 uk

. . .
0 0



The t-copulas choice is appropriate to the nature of the financial data, which are often
nonlinear, dependent, and heavy-tailed, and the co-occurrence of extreme events represents
the same salient feature of a stressed market. In this respect, while the Gaussian copulas
are unable to capture them, t-copulas allow for modeling the tail dependency and the
asymmetric relationships. By doing so, the model improves its robustness to stress the use
of the model in extreme cases. This is particularly valuable in the face of market turbulence,
where it would be very difficult for a model to describe the occurrence of simultaneous
extreme events in the variables. Nevertheless, this approach has its drawbacks. First,
the computational complexity of the model increases with the use of t-copulas, especially
if the dimension of the data is high. The second challenge is the reliance of the model
on the exogenous input data. For instance, missing or noisy data in the SI or ILLIQ may
lead to less reliable predictions. The third challenge is related to the assumption that the
dependence structure between exogenous variables and transition probabilities is constant
over time, which can be restrictive in highly volatile markets or during structural breaks.
Future work could address these challenges incorporating Bayesian inference or machine
learning techniques to enhance robustness and scalability.
By integrating t-copulas into a Non-Stationary Markov Chain (NMC) framework, this
approach combines the temporal modeling strengths of Markov Chains with the ability
of copulas to capture complex dependency structures. As highlighted by Embrechts et al.
(2003) [20] and Rachev et al. (2009) [21], this hybrid approach offers a powerful tool
for forecasting market behaviors under varying conditions. The dynamic adjustment of
transition probabilities based on exogenous variables such as the Sentiment Index (SI)
and Illiquidity Index (ILLIQ) ensures the model remains responsive to evolving market
environments, making it highly relevant for real-world applications.
Despite its strengths, this approach is not without limitations. First, the use of t-copulas
increases computational complexity, particularly when dealing with high-dimensional
datasets. The need for extensive processing power may pose challenges in real-time
applications or when scaling the model. Second, the accuracy of predictions is closely
tied to the quality and availability of exogenous inputs. Missing or noisy data in SI or
ILLIQ indices can significantly undermine the reliability of the model’s outputs. Finally,
the framework assumes a stable relationship between exogenous variables and transition
probabilities over time—a condition that may not hold during periods of extreme market
volatility or structural changes.
To overcome these challenges, future research could explore the incorporation of
techniques such as Bayesian inference or machine learning to improve both robustness and
scalability. Bayesian methods could enhance the model’s ability to handle uncertainty in
parameter estimation, while machine learning algorithms might enable the detection of
evolving relationships between variables and transition probabilities. These enhancements


Appl. Sci. **2025**, 15, 1034 10 of 31


could pave the way for a more adaptable and computationally efficient framework, capable
of managing the complexities of modern financial markets more effectively.


3.3. Machine Learning Techniques in Financial Time Series Prediction


Machine learning models have demonstrated exceptional capabilities in capturing
temporal dependencies and patterns inherent in financial data. Among these, Long ShortTerm Memory (LSTM) networks, an advanced variant of Recurrent Neural Networks
(RNNs), are particularly effective for sequential data processing. Given a time series
{ **x** t}t [T] =1 [, where] **[ x]** [t][ ∈] [R][d][ represents the feature vector at time][ t][, the LSTM updates its hidden]
state **h** t as follows:
**h** t = _σ_ ( **W** h · **h** t−1 + **W** x · **x** t + **b** ), (5)


where **W** h and **W** x are weight matrices, **b** is the bias term, and _σ_ is the activation function.
LSTMs are particularly suited for financial time series prediction due to their ability to
retain and utilize long-term dependencies, a critical aspect of financial data. Studies, such
as Kim and Kang (2019) [22], have validated their effectiveness in this domain.
In parallel, Bidirectional Encoder Representations from Transformers (BERT) has
emerged as a powerful tool for sentiment analysis. In financial applications, BERT processes
a corpus D of news articles, encoding each document d ∈D into a semantic embedding **z** d:


**z** d = BERTencoder(d; Θ), (6)


where Θ represents the model parameters. The embedding **z** d encapsulates the contextual
semantics of the document, enabling the extraction of valuable insights for predicting
market behavior. This capability has been extensively validated in tasks involving stock
market prediction, as demonstrated by Mittal et al. (2022) [23].
To achieve a robust prediction framework, the outputs of BERT, Non-Stationary
Markov Chain (NMC), and exogenous variables **Z** (t) (e.g., GARCH, VIX) are integrated.
These components collectively form the input to the LSTM network, which models temporal dependencies to predict the future market state St+1. The process is represented
as follows:
Sˆt+1 = fLSTM( **h** t), (7)


where the hidden state **h** t is computed as


**h** t = _σ_ ( **W** h · **h** t−1 + **W** x · [BERToutput, NMCoutput, **Z** (t)] + **b** ). (8)


In this configuration,


           - BERToutput: Encodes sentiment information from financial news articles, capturing
the broader market sentiment.

           - NMCoutput: Provides probabilistic insights into market state transitions, modeling
regime changes over time.

           - **Z** (t): Represents exogenous variables such as market volatility (e.g., VIX) and autoregressive conditional heteroskedasticity (e.g., GARCH).


The weight matrices **W** h and **W** x govern the contributions of the previous hidden state
**h** t−1 and the current input features, respectively, while **b** introduces a bias term to improve
model flexibility. The activation function _σ_, typically a nonlinear function, ensures the
model can capture complex patterns in the data.
This multimodal integration ensures that the contextual insights from BERT, the probabilistic state transitions from NMC, and the exogenous market indicators collectively
contribute to the LSTM’s temporal modeling. As a result, this approach enhances the


Appl. Sci. **2025**, 15, 1034 11 of 31


accuracy of market state predictions and provides a cohesive methodology for capturing
the dynamics of financial markets.


3.4. Multimodal Integration and Framework Design


As depicted in Figure 1, the proposed framework integrates financial ontologies,
stochastic models, and machine learning techniques into a cohesive methodology for market
state prediction. This multimodal approach leverages the strengths of each component to
enhance predictive accuracy and adaptability in financial markets.
The predictive process is formalized as follows:


Sˆt+1 = Φ(O, **h** t[ **P** (t), **z** d, **Z** (t)]), (9)


where Φ denotes the multimodal function that synthesizes structured knowledge from
the financial ontology (O), deep learning embeddings from the LSTM hidden states ( **h** t),
and contextual sentiment data and exogenous variables ( **z** d and **Z** (t), respectively). The hidden state **h** t is further defined as a function of **P** (t) (NMC outputs), **z** d (BERT outputs),
and **Z** (t) (exogenous inputs).
The framework illustrated in Figure 1 demonstrates how these components interact.
Financial ontologies (O) provide a structured and hierarchical representation of financial
indicators, enabling the classification and selection of relevant assets. The Non-Stationary
Markov Chain (NMC) outputs ( **P** (t)) model the dynamic transitions between market
states, while Bidirectional Encoder Representations from Transformers (BERT) generate
embeddings ( **z** d) from financial news, capturing the contextual sentiment that reflects
market conditions. These components are complemented by exogenous variables ( **Z** (t)),
such as volatility indices (GARCH, VIX), to form the inputs for the Long Short-Term
Memory (LSTM) network.
The integration of these modalities ensures that the framework can capture both the
structured relationships in financial data and the temporal dependencies in market dynamics. By combining ontological knowledge, probabilistic state transitions, and machine
learning insights, the framework provides a robust foundation for predicting future market
states ( S [ˆ] t+1).
This multimodal design builds upon advancements in integrating diverse data modalities for predictive tasks, as highlighted by Lee and Yoo (2020) [24]. Studies such as Qin
(2024) [25] and Gao et al. (2024) [26] have demonstrated the advantages of such integrative
approaches in financial applications, particularly in volatile and dynamic market conditions.


**4. Materials and Methods**


As illustrated in Figure 1 (presented in Section 2), the methodology of this study
is structured into two main stages: (i) Ontology-Based Stock Selection and (ii) Market
State Prediction.
This framework integrates multiple components to enhance predictive accuracy, starting with the ontological classification of stocks based on financial indicators such as liquidity, profitability, debt, and growth. These selected stocks are then analyzed using
multimodal techniques, including sentiment analysis with BERT, volatility modeling with
GARCH and the Fear Index (VIX), and dynamic market regime transitions modeled by
the Non-Stationary Markov Chain (NMC). The predictive power is further enhanced by
incorporating Long Short-Term Memory (LSTM) networks, fine-tuned through hyperparameter optimization. The final output determines the market state (bull, neutral, or bear),
providing a robust foundation for future work on trading strategy development.


Appl. Sci. **2025**, 15, 1034 12 of 31


4.1. Dataset and Testing Period


The dataset spans from March 2018 to July 2020, a period that includes the significant
market stress caused by the COVID-19 pandemic. As shown in Figure 4, the S&P500
experienced sharp declines, while the VIX reached unprecedented levels, reflecting extreme
volatility. These conditions provided a natural testbed to evaluate the robustness of the
proposed framework under adverse market scenarios. By incorporating sentiment indices,
volatility measures, and illiquidity metrics, the framework demonstrated resilience in
capturing the market dynamics during this unprecedented period.


**Figure 4.** This chart highlights market stress during the COVID-19 pandemic, showing the performance of the S&P500 and the VIX from March 2018 to July 2020. The S&P500 experienced significant
declines, while the VIX reached unprecedented levels, reflecting extreme market volatility. These
trends illustrate the challenging conditions that served as a testing ground for the framework’s
robustness under adverse market scenarios.


4.2. Ontology-Based Stock Selection
4.2.1. Financial Ontology Construction


The financial ontology was developed to map and categorize stocks based on fundamental financial indicators, as illustrated in Figure 5. According to Usmonov (2023) [27],
these indicators are essential for assessing companies’ financial performance. For instance,
the financial analysis of Chevron Corporation illustrates the importance of indicators such
as liquidity, profitability, debt, and growth in identifying promising stocks.


           - Liquidity: Indicators such as the Current Rati o and Quick Ratio measure a company’s
ability to meet short-term obligations.

           - Profitability: Indicators such as Return on Assets (ROA) and Return on Equity (ROE)
assess efficiency in utilizing assets and shareholder returns.

           - Debt: The Debt-to-Assets Ratio (DAR) and Debt-to-Equity Ratio (DER) reflect financial
leverage and capital structure.

           - Growth: Metrics like Growth Rate and Revenue Growth Rate evaluate potential
future expansion.


These indicators form the foundation of a Lattice Graph, which hierarchically organizes financial metrics, enabling pattern identification and classification. The process
outlined in Figure 5 demonstrates how data ingestion, processing, and ontology creation
are streamlined to ensure consistency and accuracy in stock categorization.


Appl. Sci. **2025**, 15, 1034 13 of 31


**Figure 5.** The diagram illustrates the ontology-based stock selection process, including data ingestion,
processing, and ontology management. Each step outlines the flow from gathering financial data to
storing ontology updates in OWL format.


4.2.2. Role of Financial Ontology in Asset Selection


The financial ontology serves as the foundational framework for asset selection, focusing on identifying stocks with higher potential for returns based on their financial profiles.
Unlike traditional models that integrate ontology directly with predictive algorithms, this
study employs the ontology as a filtering mechanism to narrow down the pool of assets for
further analysis.
The selection process begins with the classification of stocks using fundamental financial indicators such as liquidity, profitability, debt, and growth. These indicators are
hierarchically organized in a lattice graph, enabling pattern identification and consistent
classification. The classification process involves the following steps:


1. Data Mapping: Financial data from each company is mapped into the ontology,
associating metrics such as current ratio (liquidity), return on equity (profitability),
debt-to-equity ratio (debt), and revenue growth (growth) to their respective nodes in
the lattice graph.
2. Threshold Application: Each metric is assessed against dynamically adjusted thresholds, calculated from the quartiles of the financial data distribution. This approach
ensures that companies meeting the revised performance criteria and aligned with
market trends are retained.
3. Hierarchical Filtering: The ontology leverages its hierarchical structure to identify
patterns across multiple metrics. Stocks that exhibit strong performance in liquidity,
profitability, and growth while maintaining manageable debt levels are classified as
high-potential assets.
4. Subset Selection: Based on the filtering process, a refined subset of stocks is created,
aligning with the investment criteria and ensuring that subsequent predictive models
are applied to a reduced pool of high-quality candidates.


This dual-purpose approach not only simplifies the computational complexity by
reducing the universe of analyzed stocks but also enhances the interpretability of the
selection process by clearly associating decisions with financial metrics.
The selected stocks are then passed to the subsequent stages of the pipeline, including
market state prediction and trading strategy optimization. This ensures that the framework
focuses on assets with a higher likelihood of generating returns, aligning with the study’s
goal of enhancing investment performance through a multimodal framework.


Appl. Sci. **2025**, 15, 1034 14 of 31


4.2.3. Dynamic Processing and Updating


The ontology dynamically incorporates updated financial data, recalculating metrics
periodically to reflect real-time performance changes. This ensures classifications remain
accurate and relevant, addressing the challenges posed by market volatility and evolving
financial conditions.


4.2.4. Stock Classification


With the developed ontology, stocks are sorted into performance categories according
to their financial profiles. Classifications are filtered using parameters like dynamically
adjusted min_threshold and min_support, calculated from quartile ranges of financial metrics,
which guarantees strong groupings while adapting to changing market conditions.
The determination of the min_threshold is achieved dynamically by utilizing quartile
ranges of financial metrics, allowing the classification to adapt according to data distribution
and market conditions. For example, companies that rank in the top quartiles for liquidity
and profitability while managing debt effectively are given priority for further analysis.
This method ensures stocks with high relative performance criteria remain prioritized,
keeping step with current market dynamics and shifts in financial data distributions.
Utilizing dynamic thresholds based on quartiles is consistent with advanced machine
learning practices and graph-based classification techniques. These data-driven thresholds
strike a balance between sensitivity and specificity by leveraging distributions within
the dataset. In financial ontologies, this approach improves adaptability and robustness,
ensuring that the classification process stays responsive to real-time financial data. This
method is supported by previous studies on adaptive and hierarchical frameworks for
asset selection.
The min_support parameter is adaptively set according to the data distribution within
the lattice graph structure. By utilizing quartile-based calculations, this framework ensures
that only stocks with statistically significant support across financial metrics are selected.
This approach reduces overfitting risk while preserving meaningful patterns in the data.


4.2.5. Advantages of Ontology-Based Selection


This approach offers several advantages:


(i) Classification Accuracy: Enhanced by integrating diverse financial indicators such
as liquidity, profitability, debt, and growth;
(ii) Reflectiveness to Market Conditions: Adapts to market changes by integrating
the latest financial data and dynamically setting thresholds based on quartiles,
ensuring that the selection process stays aligned with current market trends;
(iii) Pattern Identification: Facilitates insights through the hierarchical structure of the
lattice graph;
(iv) Investment Support: Highlights stocks with strong growth potential and robust
financial metrics.


4.2.6. Data Preprocessing and Noise Handling


Effective data preprocessing is critical for ensuring the reliability of machine learning
models, particularly in financial applications where datasets often contain noise and inconsistencies. In this study, several preprocessing steps were employed to enhance data
quality and reduce the impact of noise:


           - Data Cleaning: Missing values in financial indicators (e.g., Illiquidity Index, VIX) were
addressed through a combination of interpolation and forward-fill techniques. This
approach ensures continuity in time series data while minimizing the introduction of
artificial trends.


Appl. Sci. **2025**, 15, 1034 15 of 31


           - Outlier Detection and Treatment: Outliers in financial datasets often represent rare
events, such as market shocks, peaks in volatility, or economic crises. Instead of treating these as noise, this study considered outliers as valuable sources of information:


**–** Rare Events and Structural Changes: Outliers frequently reflect significant market
responses to macroeconomic events, such as interest rate announcements or
unexpected geopolitical developments. For example, a sudden spike in the VIX
might indicate heightened uncertainty due to a global crisis. As highlighted by
Costa et al. (2023) [28], such events provide crucial insights into systemic market
disruptions, particularly during crises when asset correlations weaken, revealing
structural changes in financial systems.

**–** Market Insights from Extremes: Turiel and Aste (2021) [29] demonstrated that
outliers, such as those observed during “flash crashes”, often indicate unbounded variance in trading volume, reflecting systemic risks and feedback
loops. These events are not noise but critical manifestations of market stress and
self-organized criticality.

**–** Contextual Validity: Outliers are not inherently errors; they may legitimately
represent extreme but relevant behaviors within financial markets. Removing
them indiscriminately risks losing critical insights into market dynamics under
extreme conditions.

**–** Controlled Smoothing: While outliers were identified using interquartile range
(IQR) analysis, their treatment depended on contextual analysis. Extreme values
that reflected genuine market movements were retained, while only spurious outliers, such as those caused by data recording errors, were smoothed or excluded.


           - Normalization and Scaling: To maintain consistency across variables with different
scales (e.g., sentiment scores, volatility indices), data were normalized using min–max
scaling. This step standardizes inputs to ensure that all features contribute equally to
the model’s performance.

           - Text Preprocessing for Sentiment Analysis: Financial news texts were tokenized,
lowercased, and stripped of stopwords before being fed into the BERT model. This
preprocessing ensures that irrelevant tokens do not dilute the sentiment signals extracted by the model, as suggested by Sousa et al. (2020) [7].


The importance of robust preprocessing in financial datasets has been emphasized in
the literature. Sousa et al. (2020) [7] demonstrated that noise in textual data can significantly
impact sentiment analysis outcomes, highlighting the need for effective text-cleaning
pipelines. Similarly, Henouda et al. (2022) [30] underscored the role of scaling and proper
handling of outliers in improving the reliability of financial models. Costa et al. (2023) [28]
and Turiel and Aste (2021) [29] further advocate for retaining outliers when they represent
rare but critical market events, ensuring that systemic insights are preserved.
By implementing these preprocessing steps, this study ensures that the inputs to
the framework—ranging from sentiment scores to financial indicators—are both accurate
and representative, minimizing the risks associated with noisy or incomplete data while
preserving critical market insights.


4.3. Market State Prediction
4.3.1. Construction of the Sentiment Index


The Sentiment Index (SI) is derived from a combination of financial variables, such
as amplitude, volume, turnover, and others, which collectively capture market sentiment.
Given the high dimensionality of these variables, dimensionality reduction techniques are
applied to ensure computational efficiency and enhance the signal-to-noise ratio.


Appl. Sci. **2025**, 15, 1034 16 of 31


Dimensionality reduction is crucial when dealing with datasets containing numerous
interdependent variables. Ayesha et al. (2020) [31] provided a comparative study of various
dimensionality reduction techniques, highlighting their respective strengths in preserving
essential features while minimizing redundancy. Their insights support the adoption of
t-SNE in this framework to create a robust and representative Sentiment Index.
Henouda et al. (2022) [30] further demonstrated the effectiveness of techniques
like PCA in processing high-dimensional datasets, which complements the findings of
Ayesha et al. However, recent studies by Pareek and Jacob (2021) [32] and Kohler et al.
(2020) [33] emphasize that t-SNE offers distinct advantages over PCA, particularly in scenarios where nonlinear relationships and clustering structures are crucial. t-SNE excels at
preserving local and global structures within the data, ensuring that the nuances of market
sentiment are retained in the reduced dimensional space.
In this study, t-SNE was employed for dimensionality reduction, enabling a concise yet
informative input for the Non-Stationary Markov Chain (NMC). By leveraging t-SNE, the SI
captures the nonlinear interdependencies between sentiment-related variables, enhancing
the accuracy and interpretability of market state predictions.


4.3.2. Non-Stationary Markov Chain (NMC) with t-Copulas


The Non-Stationary Markov Chain (NMC) captures dynamic transitions between
market states by leveraging variables such as the Sentiment Index (SI) and the Illiquidity
Index (ILLIQ), as described by Liu (2022) [4]. As highlighted by Gassen et al. (2020) [34],
illiquidity plays a crucial role in influencing the synchronization of stock prices, further
supporting the integration of the ILLIQ into the model. This approach enables a more
adaptive and accurate modeling of market regimes. The structure and implementation of
the NMC framework are illustrated in Figure 6.


**Figure 6.** Non-Stationary Markov Chain (NMC) model. It includes the calculation of the Sentiment
Index (SI) using t-SNE, derived from fundamental variables, and the analysis of liquidity ratios
(ILLIQ) based on returns and volume. The framework incorporates a t-copula to adjust the dynamic
transition matrix and estimates the expected times for each market state.


The Illiquidity Index is a critical component of this framework, as it captures the relative
difficulty of trading an asset without significantly affecting its price. Amihud and Noh
(2020) [35] demonstrated the importance of illiquidity in explaining market anomalies
and transitions, reinforcing its relevance as an input for predictive models like the NMC.


Appl. Sci. **2025**, 15, 1034 17 of 31


By incorporating ILLIQ, the framework aligns with empirical evidence that links liquidity
conditions to broader market dynamics.
The dependencies within the NMC are modeled using t-copulas, which provide a
flexible way to capture the joint distribution of variables:


C(uSt, uILLIQt ; _ν_, Σ) = t _ν_ (FS [−][1][(][u][S] t [)][,][ F] ILLIQ [−][1] [(][u][ILLIQ] t [)][;][ Σ][)] (10)


Here, uSt and uILLIQt represent the quantiles of St and ILLIQt, respectively. The transition matrix dynamically adjusts based on the copula model:


Pt+1 = P(t, C(uSt, uILLIQt ; _ν_, Σ)) (11)


4.3.3. Market State Classification


Market states are classified based on percentage changes over 10 days:


           - Bull Market (State 2): Change > 5%;

           - Neutral Market (State 1): Change between −5% and 5%;

           - Bear Market (State 0): Change < −5%.


4.3.4. Sentiment Analysis with BERT


BERT processes financial news to extract sentiment, providing a forward-looking
perspective on market dynamics by predicting sentiment trends at t + 1, as demonstrated
by Sousa (2020) [7]. Unlike traditional sentiment analysis approaches, such as Bag-of-Words
or lexicon-based methods, BERT excels in capturing contextual nuances and complex sentiment dynamics. Its bidirectional architecture, as noted by Alaparthi (2020) [36] and Yadav
(2024) [37], enables the understanding of semantic relationships by analyzing both preceding and succeeding contexts in a sentence, making it particularly suitable for financial texts.
The innovation in this study lies in employing BERT for predicting future market
states (t + 1) rather than merely classifying current sentiment. Prior works, such as Zhou
(2023) [8], aggregated daily sentiment scores or focused on immediate market impacts,
while Yadav (2024) [37] highlighted the integration of BERT with financial indicators
for trend prediction. This work extends these approaches by applying BERT outputs
directly as predictive features for t + 1 states, enabling preemptive decision-making in
market strategies.
Furthermore, this study fine-tunes BERT on a curated dataset of financial news, ensuring that the embeddings capture domain-specific vocabulary and contexts. As highlighted
by Alaparthi (2020) [36], unlike general-purpose sentiment models, this adaptation significantly enhances the accuracy and relevance of the extracted sentiments. The integration of
BERT with the Sentiment Index (SI) and Illiquidity Index (ILLIQ) ensures a multimodal
analysis, leveraging textual and fundamentalist data in tandem.
Empirical evaluations further validate this approach, demonstrating superior performance. While prior studies, such as Yadav (2024) [37], achieved accuracy levels around
70%, this framework, integrating BERT with t + 1 forecasting, delivers substantial improvements. This result underscores the role of BERT as a cornerstone for robust and
forward-looking market predictions, surpassing traditional methods and highlighting its
potential to uncover nuanced market dynamics.


4.3.5. Forecasting Using Long Short-Term Memory (LSTM)


The LSTM forecasts future market conditions by combining temporal dependencies
from NMC predictions, sentiment analysis of financial news using BERT (Transformers
v4.47.1), and external factors like the Volatility Index (VIX) and GARCH volatility. This
integration enables the model to effectively tackle both systemic and idiosyncratic risks.


Appl. Sci. **2025**, 15, 1034 18 of 31


The VIX acts as a measure of overall market sentiment and uncertainty, indicating
changes in global risk perception. On the other hand, the GARCH model offers detailed
insights into asset-specific volatility by dynamically estimating returns’ conditional variance. When combined, these variables improve the model’s capability to capture market
dynamics across different conditions. This enhancement is illustrated by Huang et al.
(2021) [38], who emphasized the importance of integrating financial and macroeconomic
indicators into machine learning models.
The choice to prioritize the VIX over other macroeconomic indicators or geopolitical
variables stems from its unparalleled capacity to encapsulate multiple aspects of market
risk and sentiment into one actionable measure. Unlike macroeconomic indicators, which
frequently reflect past data, or geopolitical factors that can add uncertainty and complexity,
the VIX provides a predictive gauge of market volatility.
Research has demonstrated that the VIX is a strong indicator of systemic shocks and
investor sentiment. For instance, Liang et al. (2024) [39] illustrated how the VIX reflects
market sentiment and its correlation with broader market dynamics. In a similar vein, Liu
(2021) [40] compared the VIX with GARCH family models and underscored its superior
effectiveness in capturing real-time volatility and investor expectations. Additionally,
Bianchi et al. (2022) [41] investigated the predictive capabilities of the VIX using advanced
modeling techniques, highlighting its relevance in turbulent market conditions.
This study uses the VIX as a primary input to strike a balance between simplicity and
strong predictive capability. This method effectively captures dynamic market conditions
while reducing the risks of overfitting or redundancy from using multiple macroeconomic
indicators, aligning with its overarching goal.
By incorporating the VIX alongside other key features such as GARCH volatility,
sentiment scores, and liquidity indices, the LSTM architecture is designed to efficiently
process these inputs, ensuring accurate market state predictions. As shown in Figure 7,
the inputs are processed through a finely-tuned LSTM layer, followed by a dropout layer
for regularization, and finally pass through a dense layer that outputs probabilities corresponding to different market states (bull, bear, neutral). This architecture adeptly integrates
both systemic and idiosyncratic viewpoints, providing a robust framework for predicting
market states.


**Figure 7.** The architecture of the Long Short-Term Memory (LSTM) network designed for market
state prediction. The model receives sequential inputs (x0, x1, . . ., xn) and processes them through
the LSTM layer, followed by dropout and dense layers. The output layer, with a softmax activation,
classifies market states into bear, neutral, or bull categories.


The incorporation of these methods, along with the optimized LSTM, greatly enhances
predictive accuracy, as confirmed by studies from Liu (2022) [4] and Yu (2018) [1].


Appl. Sci. **2025**, 15, 1034 19 of 31


4.3.6. Strategies for Robustness in Extreme Scenarios and Real-Time Applications


The framework was created to manage market dynamics, particularly during times
of high volatility or macroeconomic shocks. To assess the model’s robustness in extreme
scenarios, indices sensitive to sudden changes—such as the VIX, ILLIQ, and GARCH—were
incorporated into its evaluation process.
In the context of real-time applications, the following strategies are proposed to
enhance robustness and efficiency:


           - Incremental Updates: Instead of reprocessing the entire pipeline, partial updates of
indices and the Non-Stationary Markov Chain (NMC) can be performed, significantly
reducing latency during execution.

           - Modular Inference: The separation of the framework’s modules allows BERT inferences and NMC probabilistic calculations to be executed in parallel, optimizing
response time and scalability.

           - Computational Optimization: The use of tools like TensorRT and ONNX Runtime
for optimized model deployment improves computational efficiency by reducing
latency and maximizing the utilization of available hardware resources. For instance,
as demonstrated by More (2023) [42], converting models to the ONNX format and
deploying them on dedicated hardware, such as the Jetson Nano, achieved significant
performance gains, increasing the frame rate from 1–2 fps to 30–43 fps and GPU
utilization up to 99%. Additionally, Li (2024) [43] showed that TensorRT effectively
optimizes inferences for complex models, reducing latency and optimizing memory
consumption in embedded devices.

           - Stress Testing Simulations: Adding simulations of extreme scenarios to the training and validation process, such as market crashes or abrupt changes in economic
indices, allows for evaluating and strengthening the framework’s resilience under
adverse conditions.


These strategies ensure that the framework is applicable not only in experimental
environments but also in production contexts that demand high performance, such as
real-time trading, where latency and robustness are critical for success.


4.4. Methodological Innovations


The proposed framework introduces several methodological innovations that together improve the precision and relevance of market state predictions and stock selection
strategies. Various fields, including emerging technologies like digital twins in software
engineering, have highlighted the necessity for tailored approaches. Guinea-Cabrera and
Holgado-Terriza (2024) [44] emphasize a lack of consensus on standardized methodologies
in these areas, highlighting the importance of custom solutions to tackle domain-specific
challenges. Similarly, this framework employs a customized approach by integrating
ontology-based classification, sentiment analysis, and predictive modeling to ensure adaptability in dynamic financial markets. Below is an overview detailing each component’s
distinct contribution along with its integration within the overall framework:


4.4.1. Ontology-Based Stock Selection


Building upon the work of Bhuyan and Sastry (2023) [3], this study enhances ontologybased stock classification by integrating it into a predictive pipeline. The ontology captures domain-specific knowledge, classifying stocks based on financial metrics such as
liquidity, profitability, and growth. This structured classification enables the identification
of high-potential stocks while maintaining flexibility to adapt to varying market conditions. The dynamic thresholds in classification further differentiate this approach from
static methodologies.


Appl. Sci. **2025**, 15, 1034 20 of 31


4.4.2. Sentiment Analysis with BERT


Unlike traditional sentiment analysis models, the fine-tuned BERT model employed
here predicts forward-looking sentiment (t + 1) derived from financial news. This innovation leverages BERT’s bidirectional contextual embeddings to capture subtle linguistic
cues, enabling more precise and actionable sentiment insights. As noted by Sousa (2020) [7]
and Zhou (2023) [8], by integrating sentiment outputs into the predictive pipeline, this
approach bridges the gap between textual data analysis and quantitative trading strategies.


4.4.3. Sentiment Index and Illiquidity Index


The Sentiment Index (SI) is constructed using t-SNE, which excels at capturing nonlinear and complex relationships among features, offering superior performance over
traditional linear methods like PCA. Figures 8 and 9 show the comparative distributions
of SI produced by both PCA and t-SNE across different market classes (Bear Market, Shock
Market, and Bull Market).


**Figure 8.** Boxplots comparing Sentiment Index (SI) distributions generated by PCA and t-SNE for
Bear Market, Shock Market, and Bull Market. Boxplots highlight median, quartile ranges, and outliers
for both methods.


**Figure 9.** Violin plots comparing Sentiment Index (SI) distributions generated by PCA and t-SNE
for Bear Market, Shock Market, and Bull Market. Violin plots emphasize density and complexity of
distributions, with t-SNE demonstrating superior performance in preserving nonlinear relationships.


The boxplots (Figure 8) and violin plots (Figure 9) highlight significant differences
in the effectiveness of each technique. PCA results in compact, linear distributions, while
t-SNE-derived SI shows wider and more detailed variations, especially within the Shock
Market and Bull Market categories. This increased variability indicates that t-SNE captures
intricate nonlinear patterns inherent in data—a critical aspect for financial markets known
for their sudden changes and complex dynamics.


Appl. Sci. **2025**, 15, 1034 21 of 31


For example, during the Bear Market, the t-SNE-derived Sentiment Index (SI) reveals
a higher concentration of positive values. This illustrates its capacity to maintain local
proximities and detect nuanced sentiment-driven behaviors. Likewise, in the Shock Market,
the broader distribution of SI highlights t-SNE’s effectiveness at recognizing changing market conditions that linear methods like PCA often reduce to overly simplistic interpretations.
This evidence highlights the effectiveness of t-SNE in building the Sentiment Index
within this framework. By emphasizing nonlinear patterns, t-SNE effectively captures
sentiment-driven insights that are often linked to sudden market shifts, thus boosting
the model’s predictive accuracy. Additionally, as described by Amihud (2002) [45] and
Zhou (2023) [8], integrating the Illiquidity Index (ILLIQ) enriches this process by offering a
fundamentalist viewpoint on liquidity conditions.


4.4.4. Non-Stationary Markov Chain (NMC) with t-Copula


The NMC module dynamically models market state transitions, incorporating realtime exogenous variables such as the Sentiment Index and Illiquidity Index. As demonstrated by Huang (2021) [38], the use of t-copulas to handle serial dependencies among
event times allows for more accurate modeling of state transitions under varying market
conditions. This dynamic approach differentiates the framework from static or timeinvariant Markov models.


4.4.5. LSTM for State Prediction


The LSTM module integrates outputs from the NMC, BERT, and external variables like
VIX and GARCH to forecast market states. By incorporating historical state probabilities,
sentiment-based inputs, and external volatility indicators, it effectively captures temporal
dependencies and nonlinear relationships. This approach enhances the accuracy of market
state predictions, as demonstrated by Yu (2018) [1] and Kim (2018) [2].


4.4.6. Multimodal Integration


The overarching innovation lies in the multimodal integration of these components.
Ontology-based stock selection provides a robust starting point, while sentiment analysis
and fundamentalist insights complement technical analysis via NMC and LSTM. This integrated approach ensures a holistic perspective on market dynamics, surpassing methods
that rely on isolated data sources.
The combination of these methodological innovations positions the framework as
a comprehensive tool for market prediction. The dynamic interplay between ontology,
sentiment analysis, and predictive modeling addresses key challenges in market state
forecasting, offering practical and theoretical advancements over existing methodologies.


**5. Results**


This section presents the evaluation of the proposed model and compares its performance against various machine learning and deep learning techniques. The analysis
focuses on predictive accuracy, computational cost, and robustness through ablation studies,
providing a comprehensive assessment of the methodology.


5.1. Comparative Model Evaluation


To assess the effectiveness of the proposed model, it was compared with widely used
algorithms such as Support Vector Machine (SVM), Random Forest, K-Nearest Neighbors
(KNNs), Naive Bayes, Logistic Regression, Decision Tree, Adaptive Boosting (Adaboost),
eXtreme Gradient Boosting (XGBoost), Artificial Neural Network (ANN), Recurrent Neural
Network (RNN), and Long Short-Term Memory networks. These models were chosen
for their relevance in stock market prediction literature as noted by Kumar et al. [46] and


Appl. Sci. **2025**, 15, 1034 22 of 31


Nabipour et al. [47]. Furthermore, each algorithm was fine-tuned to optimize its parameters,
ensuring a fair comparison across different approaches.
Table 1 presents the accuracy, precision, recall, and F1-score for each model, providing
a comparative analysis of their performance metrics. Meanwhile, Table 2 focuses on the
ROC curves, highlighting the area under the curve (AUC) as a measure of each model’s
ability to discriminate between market states.


**Table 1.** Comparison of model performance.


**Model** **Accuracy (%)** **Precision (%)** **Recall (%)** **F1-Score (%)**


LSTM 97.20% 89.27% 88.53% 88.59%
RNN 86.92% 40.34% 44.76% 42.27%
Random Forest 91.07% 77.71% 65.98% 69.60%
SVC 91.96% 81.07% 62.99% 69.04%
XGBoost 94.64% 85.33% 76.32% 79.94%
KNN 93.75% 80.52% 82.30% 80.45%
Naive Bayes 85.71% 56.04% 54.60% 54.84%
Adaboost 91.96% 75.60% 84.60% 78.94%
Decision Tree 91.96% 74.55% 75.29% 74.70%
ANN 93.75% 86.93% 69.66% 76.28%
Logistic Regression 91.96% 78.02% 65.98% 70.32%


**Table 2.** ROC AUC for different models.


**Model** **ROC AUC (Curve)**


LSTM 100.00%, 99.54%, 98.84%
RNN 92.80%, 96.54%, 91.42%
Random Forest 97.84%, 95.74%, 96.64%
SVC 96.96%, 94.16%, 94.21%
XGBoost 98.92%, 96.49%, 94.77%
KNN 98.87%, 97.32%, 98.60%
Naive Bayes 83.92%, 91.41%, 90.65%
Adaboost 88.73%, 86.70%, 87.94%
Decision Tree 83.73%, 87.25%, 87.66%
ANN 99.02%, 89.97%, 91.40%
Logistic Regression 99.12%, 95.12%, 92.71%


The proposed model, LSTM, achieved the highest accuracy (97.20%) and consistently
outperformed all baselines across other metrics, such as precision, recall, and F1-score,
indicating its robustness in predicting market states.


5.2. Computational Cost and Complexity


The computational efficiency of each model was analyzed by measuring the tuning and
training times. The evaluated models exhibit diverse characteristics in terms of trainable parameters and structure. The LSTM model, with 70,211 trainable parameters, demonstrates
a strong ability to capture patterns in temporal sequences. The simpler RNN features
23,363 trainable parameters, offering a reduced but still effective capacity for sequential
data. The Random Forest comprises 177 decision trees with fixed parameters optimized
during tuning. The SVC relies on 96 support vectors to define classification boundaries,
while the XGBoost model, configured with 50 trees and a maximum depth of nine, includes
25,550 trainable parameters. The KNN uses four neighbors without additional adjustable
parameters, whereas the Naive Bayes model employs probabilistic distributions without
direct trainable parameters. The Adaboost model combines multiple weak classifiers structured with 45 nodes, 23 leaves, and a maximum depth of eight. The Decision Tree consists


Appl. Sci. **2025**, 15, 1034 23 of 31


of 141 nodes and 71 leaves, optimized to represent its hierarchical structure. The ANN
has 2467 trainable parameters, providing a simpler architecture compared to deeper networks. Lastly, the Logistic Regression model is linear, with adjustable coefficients as its
only trainable parameters.
While the proposed model required more training time than traditional machine learning methods, its superior predictive accuracy justifies the computational trade-off. These
results emphasize the balance between computational cost and performance, showcasing
the efficiency of the proposed approach. Table 3 summarizes the tuning and training times
for each model.


**Table 3.** Computational cost comparison.


**Model** **Tuning Time (s)** **Training Time (s)**


LSTM 994.36 33.04
RNN 3248.88 3.96
Random Forest 82.83 0.43
SVC 73.95 0.02
XGBoost 123.50 0.95
KNN 10.18 0.0025
Naive Bayes                  - 0.01
Adaboost 2.07 0.92
Decision Tree 3.61 0.01
ANN 577.73 8.22
Logistic Regression 8.22 0.23


5.3. Ablation Studies


To evaluate the contribution of each module in the proposed architecture, ablation
studies were conducted by systematically removing individual components. The results
highlight the importance of these modules in achieving optimal performance:


           - NMC Module: This module calculates market regime transition probabilities, playing
a critical role in identifying regime shifts. Removing it reduced the accuracy from
97.20% to 92.50% and F1-score from 88.59% to 79.95%, emphasizing its impact on
predictive accuracy and overall robustness.

           - BERT Module: Responsible for analyzing sentiment from financial news, BERT is
essential for capturing textual information relevant to market dynamics. Its exclusion resulted in a significant drop in F1-score, from 88.59% to 70.14%, and accuracy
decreased by 8.6%, indicating the loss of sentiment-driven insights.

           - VIX and GARCH Features: These exogenous variables model market volatility and
trends. Without them, recall decreased from 88.53% to 81.34%, and accuracy dropped
by 5.8%, reflecting the diminished ability to handle downturn scenarios effectively.


The results are summarized in Table 4, demonstrating the critical role of each component in enhancing the overall performance of the model.


**Table 4.** Impact of component removal on model performance.


**Component Removed** **Accuracy (%)** **Precision (%)** **Recall (%)** **F1-Score (%)**


None (Full Model) 97.20 89.27 88.53 88.59
NMC Module 92.50 83.14 80.32 79.95
BERT Module 88.60 70.33 66.21 70.14
VIX and GARCH Features 91.40 78.12 81.34 76.92


Appl. Sci. **2025**, 15, 1034 24 of 31


5.4. Comparison with the Literature


The results were compared to the methods outlined in Kumar (2018) [46] and Nabipour
(2020) [47]. The proposed model exceeded state-of-the-art algorithms like Random Forest,
XGBoost, and SVM regarding predictive accuracy and recall. For example, while XGBoost
attained an accuracy of 94.64%, our model achieved a higher rate of 97.20%, highlighting
its superior ability to reliably predict market states.


5.5. Strategy Evaluation


Based on the market state predictions, a trading strategy was implemented:


           - Bull Market: Assets were sold to capitalize on upward trends.

           - Non-Uptrend Periods: Assets were purchased if cash was available, aiming to minimize losses during downturns.


Implementing dynamic thresholds based on quartiles greatly improved the model’s
adaptability and robustness. By aligning these thresholds with financial metrics’ distribution, the framework more effectively identified high-performing assets, particularly in
volatile market conditions.
This strategy effectively leveraged the proposed model’s predictions, achieving significant gains compared to baseline methods. The results are summarized in Table 5.


**Table 5.** Comparison of Buy and Hold (BnH) and State Predicted (SP) strategies with dynamic
thresholds.


**Stock** **Accuracy (%)** **BnH (%)** **SP (%)** **ROC (AUC)**


Stock #1 64.49 46.42 55.03 0.79, 0.71, 0.82
Stock #2 59.81 −9.19 −4.67 0.90, 0.71, 0.89
Stock #3 77.57 7.55 10.93 0.89, 0.80, 0.86
Stock #4 83.18 9.87 9.81 0.80, 0.82, 0.86
Stock #5 73.83 −11.53 −2.74 0.89, 0.83, 0.84
Total                   - 8.62 13.67                   S&P500 97.20 1.08 6.36 1.00, 0.99, 0.98


The State Predicted strategy demonstrated consistent accuracy, with hit rates ranging
from 61.68% for Stock #2 to 77.57% for Stock #4, highlighting the model’s effectiveness
in classifying market states under dynamic thresholds. The cumulative gains for the Buy
and Hold strategy varied from −11.53% for Stock #5 to 46.42% for Stock #1. In comparison,
the State Predicted strategy achieved superior results, with gains spanning from −4.67% for
Stock #2 to 55.03% for Stock #1.
For the S&P 500 index, the State Predicted strategy delivered a total gain of 6.36%,
substantially outperforming the 1.08% gain from the Buy and Hold strategy, reflecting an
incremental gain of 5.28%. When applied to individual stocks, the cumulative gain for the
State Predicted strategy reached 13.67%, compared to 8.62% for the Buy and Hold approach.
The statistical robustness of the model was further evaluated using multiclass ROC
curves. The area under the curve (AUC) values for each asset, as shown in Table 5,
underscore the model’s effectiveness in discriminating between market states (0, 1, and 2).
These results reinforce the model’s capability to provide reliable predictions under diverse
market conditions.


**6. Discussion**


This study’s results highlight the effectiveness of our proposed framework, which
combines ontology-based stock selection with state prediction utilizing LSTM calibrated by
NMC and sentiment analysis through BERT. These findings support the research conducted


Appl. Sci. **2025**, 15, 1034 25 of 31


by Liu (2022) [4], Bhuyan (2023) [3], and Zhou (2023) [8]. Their work emphasizes the
importance of integrating multiple aspects of market analysis—such as sentiment, liquidity,
and technical indicators—to enhance prediction accuracy.
Compared to Bhuyan and Sastry (2023) [3], who introduced a robust ontology-based
stock classification methodology, our framework advances their work by integrating predictive models for market state transitions. This dynamic incorporation of real-time sentiment,
as extracted by BERT, and exogenous variables, such as illiquidity and volatility indices,
enables the framework to adapt to diverse market scenarios. In contrast, Bhuyan and
Sastry’s methodology lacks a predictive component, focusing solely on static classification.
The State Predicted strategy consistently outperformed traditional approaches, such
as the Buy and Hold approach, achieving significant cumulative returns across the selected
stocks and the S&P500 index. The integration of BERT for sentiment analysis offers a
distinct advantage over methods like those in Zhou (2023) [8], where sentiment indices are
constructed but not leveraged for direct state prediction. Furthermore, while Zhou’s work
aggregates sentiment scores retrospectively, this study’s forward-looking sentiment analysis
(t + 1) provides actionable insights, aligning with the recent advancements highlighted by
Yadav (2024) [37].
From a technical perspective, this study also surpasses models relying solely on
LSTM or GARCH, as seen in works by Yu and Li (2018) [1] and Kim and Won (2018) [2].
By combining LSTM predictions with NMC-calibrated state probabilities and integrating
these with sentiment-driven insights, the proposed framework achieves higher accuracy
and cumulative returns. This multimodal integration bridges the gap between fundamental,
technical, and sentiment-based analyses, as suggested by Liu (2022) [4].
Empirical results validate the robustness of this approach. While Yadav (2024) [37]
reported predictive accuracies around 70% for BERT-enhanced models, our framework
achieves superior performance, particularly when predicting future market states (t + 1).
This improvement highlights the advantage of fine-tuning BERT for the financial domain
and integrating it with ontological and exogenous components.
From a scalability standpoint, the framework was crafted to effectively adjust to market
shifts, even when faced with rigorous computational limitations. Clapham (2023) [48] and
Alaminos (2024) [49] emphasize that these issues are particularly vital in high-frequency
trading environments, where cutting-edge technology is crucial for enhancing performance and minimizing latency. To meet these requirements in real-time trading situations,
the following strategies were employed:


           - Incremental Updates: Instead of reprocessing the entire pipeline, only critical variables
and market states are updated, significantly reducing latency and computational costs.
This aligns with the findings of Turiel and Aste (2021) [29], who emphasize the
importance of efficiently managing data updates in high-frequency systems to prevent
cascading failures during critical events.

           - Modular Inference: The separation of the framework’s modules (BERT, NMC,
and LSTM) enables parallel execution, optimizing resource utilization and minimizing
response time. This modular approach resonates with methodologies highlighted in
Alaminos et al. (2024) [49], where machine learning architectures were adapted to
handle high-frequency trading data across multiple markets effectively.


The integration of these strategies into the framework addresses key concerns raised
in Clapham et al. (2023) [48], which demonstrates how low-latency infrastructures and
modular designs enhance liquidity and market stability in high-frequency environments.
By incorporating these practices, the proposed framework not only improves computational
efficiency but also contributes to the robustness and adaptability required for dynamic
market conditions.


Appl. Sci. **2025**, 15, 1034 26 of 31


Beyond its technical contributions, the framework’s potential extends to broader
economic and societal benefits, as outlined below.
Although the technical strength and predictive accuracy of the proposed framework
are well recognized, it is important to discuss its wider social and economic implications
as well. By providing more precise predictions of market conditions, this framework has
the potential to enhance efficiency in financial markets. This improvement could result in
numerous economic and societal advantages:


           - Economic Efficiency: The system facilitates optimal capital distribution by dynamically
assessing market conditions and aligning investment strategies accordingly. This can
lead to better resource management and higher returns for both institutional investors
and individual stakeholders.

           - Financial Inclusion: In developing markets, these tools have the potential to democratize access to sophisticated financial analytics, enabling smaller investors to compete
effectively and make well-informed choices.

           - Education and Transparency: Serving as a valuable educational tool, this framework
aids novice investors in grasping market dynamics while formulating informed strategies. Its emphasis on easy-to-understand ontological classification further enhances
transparency within decision-making processes.


**7. Conclusions**


This study proposed an integrated framework for market state prediction and stock
selection, leveraging a multimodal approach that combines ontology-based stock classification, Non-Stationary Markov Chains (NMCs), sentiment analysis with BERT, and Long
Short-Term Memory (LSTM) networks. The empirical results demonstrated the model’s
ability to achieve a 97.20% accuracy in market state predictions for the S&P 500 and generate cumulative returns of 13.67% with the State Predicted (SP) strategy, significantly
outperforming the traditional Buy and Hold (BnH) strategy, which yielded only 8.62%.
Additionally, the framework’s application to the S&P 500 index achieved a return of 6.36%,
compared to 1.08% from the Buy and Hold strategy, further showcasing its versatility across
diverse market conditions.
The key contributions of this study include the following:


           - Introducing a unified framework that integrates financial ontology, machine learning,
and sentiment analysis for robust stock selection and market forecasting;

           - Demonstrating the effectiveness of combining NMC with sentiment-derived inputs
and exogenous variables for capturing dynamic market states;

           - Providing an actionable decision-support tool for investors and quantitative traders,
with empirical evidence supporting its application in real-world trading scenarios.


7.1. Limitations of the Study


While the results are promising, this study has certain limitations that need to be
addressed in future research:


           - Data Dependence: The model’s performance heavily depends on the availability and
quality of financial news and real-time financial indicators. For example, inaccuracies
or delays in financial news sentiment analysis could lead to misclassification of market states, particularly during high-volatility periods. Similarly, errors in real-time
indicators such as the Illiquidity Index (ILLIQ) may introduce noise into the predictive
framework, reducing its overall accuracy. Future work should explore robust preprocessing techniques to filter out noise and inconsistencies and consider redundant data
streams for greater reliability.


Appl. Sci. **2025**, 15, 1034 27 of 31


           - Threshold Selection: The fixed threshold (0.5) for stock classification, while practical,
may not adapt optimally to market conditions. Dynamic or data-driven threshold
selection based on market trends could yield more accurate and flexible classifications.

           - Market Regime Generalization: The classification of market states (bull, bear, neutral)
relies on predefined percentage change thresholds that may not fully capture regimespecific behaviors, especially in extreme or volatile conditions. Incorporating adaptive
regime classification methods could improve model accuracy.

           - Computational Costs: The integration of multiple models (NMC, BERT, LSTM) is
computationally intensive, which may limit scalability for real-time applications.
Further research into model compression techniques or optimized architectures is
necessary to address this limitation.


7.2. Ethical Considerations


The application of machine learning models in financial markets raises several ethical
concerns that must be acknowledged:


           - Market Manipulation Risks: Predictive models, if misused, could exacerbate volatility
or unfairly influence market behavior. Implementing safeguards and monitoring
mechanisms is essential to ensure responsible use of automated trading strategies.

           - Data Privacy: Sentiment analysis relies on financial news, which may inadvertently
include private or sensitive information. Compliance with data protection regulations,
such as GDPR, is essential to maintain ethical standards.

           - Algorithmic Bias: Models trained on historical data may reflect or amplify existing
biases in financial markets, potentially leading to unfair advantages or reinforcing
systemic inequalities. Regular audits of model performance and fairness are necessary
to mitigate these risks.

           - Accessibility: Advanced AI models in trading may disproportionately benefit institutional investors, widening the gap between large firms and individual investors.
Developing tools that enhance accessibility and transparency for smaller investors can
address this concern.


Addressing these ethical considerations requires transparency in model development, adherence to regulatory frameworks, and regular monitoring to prevent unintended consequences.


**8. Future Work**


Future research could explore several directions to address the current limitations and
enhance the proposed framework’s scalability, interpretability, and applicability:


           - Threshold Optimization: Building upon the dynamic thresholds established using
quartiles, future research can investigate optimization techniques including machine
learning models, clustering algorithms, or adaptive strategies like genetic algorithms.

           - Integration of Exogenous Variables: Incorporating additional exogenous variables,
such as geopolitical events or macroeconomic indicators, to capture broader market
dynamics and enrich the framework’s predictive capabilities.

           - Adoption of Computational Optimization Tools: Employing tools like TensorRT and
ONNX Runtime for model deployment could significantly enhance computational
efficiency. These tools have demonstrated the potential to reduce latency and optimize
hardware utilization, as shown by Li (2024) [43]. For instance, converting models to the
ONNX format has achieved performance gains, including frame rate improvements of
up to 43 fps on devices like the Jetson Nano [42]. Applying these techniques in future
iterations would ensure scalability in real-time trading applications with stringent
computational constraints.


Appl. Sci. **2025**, 15, 1034 28 of 31


           - Explainable AI (XAI): Adopting explainable AI techniques, as proposed by Costa
(2023) [28], could improve the framework’s interpretability, fostering greater trust and
adoption among financial practitioners.

           - Exploration of Alternative Data Sources: Expanding model inputs to include alternative data, such as social media sentiment and ESG (Environmental, Social, and Governance) indicators, could provide a more holistic view of market dynamics and improve
predictive accuracy.


This study lays a strong groundwork for enhancing quantitative trading methods
while tackling major limitations. The suggested framework shows powerful predictive
abilities and flexibility, offering substantial potential for further refinement and application
in various financial settings.


**Author Contributions:** Methodology, I.F.C.B.; Writing—original draft, I.F.C.B.; Writing—review &
editing, I.F.C.B., C.M.d.O.R. and J.F.L.d.O.; Supervision, C.M.d.O.R. and J.F.L.d.O. All authors have
read and agreed to the published version of the manuscript.


**Funding:** This paper was financed in part by the Coordenação de Aperfeiçoamento de Pessoal de
Nível Superior—Brazil (CAPES)—Finance Code 001, Fundação de Amparo a Ciência e Tecnologia
do Estado de Pernambuco (FACEPE), the Conselho Nacional de Desenvolvimento Científico e
Tecnológico (CNPq)—Brazilian research agencies.


**Institutional Review Board Statement:** Not applicable.


**Informed Consent Statement:** Not applicable.


**Data Availability Statement:** The raw data supporting the conclusions of this article will be made
available by the authors on request.


**Conflicts of Interest:** Authors were employed by the company FITec—Technological Innovations.


**Abbreviations**


The following abbreviations are used in this manuscript:


NMC Non-Stationary Markov Chain
BERT Bidirectional Encoder Representations from Transformers
LSTM Long Short-Term Memory
RNN Recurrent Neural Network
t-SNE t-Distributed Stochastic Neighbor Embedding
VIX Volatility Index
GARCH Generalized Autoregressive Conditional Heteroskedasticity
ILLIQ Illiquidity Index
PCA Principal Component Analysis
SI Sentiment Index
ROC Receiver Operating Characteristic
AUC Area Under the Curve
XGBoost Extreme Gradient Boosting
SVM Support Vector Machine
KNNs K-Nearest Neighbors
ANN Artificial Neural Network
Adaboost Adaptive Boosting
BnH Buy and Hold
SP State Predicted
DER Debt-to-Equity Ratio
DAR Debt-to-Assets Ratio
ROA Return on Assets
ROE Return on Equity


Appl. Sci. **2025**, 15, 1034 29 of 31


HFT High-Frequency Trading
XAI Explainable AI


**References**


1. Yu, S.; Li, Z. Forecasting Stock Price Index Volatility with LSTM Deep Neural Network. In Recent Developments in Data Science
and Business Analytics: Proceedings of the International Conference on Data Science and Business Analytics (ICDSBA-2017); Springer
[Proceedings in Business and Economics; Springer: Cham, Switzerland, 2018; pp. 265–273. [CrossRef]](http://doi.org/10.1007/978-3-319-72745-5_29)
2. Kim, H.Y.; Won, C.H. Forecasting the Volatility of Stock Price Index: A Hybrid Model Integrating LSTM with Multiple GARCHType Models. Expert Syst. Appl. **2018** [, 103, 25–37. [CrossRef]](http://dx.doi.org/10.1016/j.eswa.2018.03.002)
3. Bhuyan, B.P.; Sastry, H. Stock Selection Using Ontological Financial Analysis. In Advances in Data Science and Computing
Technologies; Joshi, A., Pradhan, P.C., Eds.; Springer: Cham, Switzerland, 2023.
4. Liu, C.; Yan, J.; Guo, F.; Guo, M. Forecasting the Market with Machine Learning Algorithms: An Application of NMC-BERTLSTM-DQN-X Algorithm in Quantitative Trading. ACM Trans. Knowl. Discov. Data **2022** [, 16, 62. [CrossRef]](http://dx.doi.org/10.1145/3488378)
5. Guo, T.; Lin, T. Multi-variable LSTM Neural Network for Autoregressive Exogenous Model. arXiv **2018**, arXiv:1806.06384.

[[CrossRef]](https://doi.org/10.48550/arXiv.1806.06384)
6. Cai, S.; Gao, H.; Zhang, J.; Peng, M. A Self-Attention-LSTM Method for Dam Deformation Prediction Based on CEEMDAN
Optimization. Appl. Soft Comput. **2024** [, 159, 111615. [CrossRef]](http://dx.doi.org/10.1016/j.asoc.2024.111615)
7. Sousa, M.G.; Sakiyama, K.; Rodrigues, L.S.; Moraes, P.H.; Fernandes, E.R.; Matsubara, E.T. BERT for Stock Market Sentiment
Analysis. In Proceedings of the 2019 IEEE 31st International Conference on Tools with Artificial Intelligence (ICTAI), Portland,
[OR, USA, 4–6 November 2019; IEEE: Portland, OR, USA, 2020; pp. 1597–1601. [CrossRef]](http://dx.doi.org/10.1109/ICTAI.2019.00231)
8. Zhou, J. Sentiment Index Construction and the Influence of Sentiments on Returns. In Proceedings of the 2nd International Conference
[on Business and Policy Studies; Springer Nature Singapore Pte Ltd.: Singapore, 2023; pp. 1631–1642. [CrossRef]](http://dx.doi.org/10.1007/978-981-99-6441-3)
9. Gerber, M.C.; Gerber, A.J.; van der Merwe, A. The Conceptual Framework for Financial Reporting as a Domain Ontology. In
Proceedings of the Twenty-First Americas Conference on Information Systems, Fajardo, Puerto Rico, 13–15 August 2015; pp. 1–18.
10. Sharma, N.; Soni, M.; Kumar, S.; Kumar, R.; Deb, N.; Shrivastava, A. Supervised Machine Learning Method for Ontology-Based
Financial Decisions in the Stock Market. ACM Trans. Asian Low-Resour. Lang. Inf. Process. **2023** [, 22, 139. [CrossRef]](http://dx.doi.org/10.1145/3554733)
11. Wani, H.; Sujithkumar, S.H. An Integrated Machine Learning Approach Predicting Stock Values Using Order Book Details. In
Proceedings of the International Conference on Data Science and Applications, Kolkata, India, 26–27 March 2022; Springer Nature
[Singapore Pte Ltd.: Singapore, 2023; pp. 129–143. [CrossRef]](http://dx.doi.org/10.1007/978-981-19-6634-7_10)
12. Roszyk, N.; Slepaczuk, R. The Hybrid Forecast of S&P 500 Volatility Ensembled from VIX, GARCH and LSTM Models. arXiv
**2024** [, arXiv:2407.16780. [CrossRef]](https://doi.org/10.48550/arXiv.2407.16780)
13. Mero, K.; Salgado, N.; Meza, J.; Pacheco-Delgado, J.; Ventura, S. Unemployment Rate Prediction Using a Hybrid Model of
Recurrent Neural Networks and Genetic Algorithms. Appl. Sci. **2024** [, 14, 3174. [CrossRef]](http://dx.doi.org/10.3390/app14083174)
14. de Luca Avila, R.; De Bona, G. Financial Time Series Forecasting via CEEMDAN-LSTM with Exogenous Features. In Proceedings
of the Intelligent Systems. BRACIS 2020, Rio Grande, Brazil, 20–23 October 2023; Cerri, R., Prati, R.C., Eds.; Lecture Notes in
[Computer Science; Springer: Cham, Switzerland, 2020; Volume 12320, pp. 558–572. [CrossRef]](http://dx.doi.org/10.1007/978-3-030-61380-8_38)
15. Mirmozaffari, M.; Yazdani, M.; Boskabadi, A.; Dolatsara, H.A.; Kabirifar, K.; Golilarz, N.A. A Novel Machine Learning Approach
Combined with Optimization Models for Eco-efficiency Evaluation. Appl. Sci. **2020** [, 10, 5210. [CrossRef]](http://dx.doi.org/10.3390/app10155210)
16. Mirmozaffari, M.; Shadkam, E.; Khalili, S.M.; Kabirifar, K.; Yazdani, R.; Gashteroodkhani, T.A. A Novel Artificial Intelligent
Approach: Comparison of Machine Learning Tools and Algorithms Based on Optimization DEA Malmquist Productivity Index
for Eco-Efficiency Evaluation. Int. J. Energy Sect. Manag. **2021** [, 15, 523–550. [CrossRef]](http://dx.doi.org/10.1108/IJESM-02-2020-0003)
17. Gorgolis, N.; Hatzilygeroudis, I.; Istenes, Z.; Gyenne, L.-G. Hyperparameter Optimization of LSTM Network Models through Genetic Algorithm. In Proceedings of the 2019 10th International Conference on Information, Intelligence, Systems and Applications
[(IISA), Patras, Greece, 15–17 July 20 19; pp. 1–4. [CrossRef]](http://dx.doi.org/10.1109/IISA.2019.8900675)
18. Dudycz, H.; Korczak, J. Conceptual Design of Financial Ontology. In Proceedings of the 2015 Federated Conference on Computer
Science and Information Systems (FedCSIS), Lodz, Poland, 13–16 September 2015; IEEE: Piscataway, NJ, USA, 2015; pp. 1505–1511.
19. Norberg, R. A Markov Chain Financial Market; Working Paper; Laboratory of Actuarial Mathematics, University of Copenhagen:
Copenhagen, Denmark, 1999; p. 25.
20. Embrechts, P.; Lindskog, F.; McNeil, A. Modelling Dependence with Copulas and Applications to Risk Management. In Handbook
of Heavy Tailed Distributions in Finance; Rachev, S.T., Ed.; Handbooks in Finance; North-Holland: Amsterdam, The Netherlands,
[2003; Volume 1, pp. 329–384. [CrossRef]](http://dx.doi.org/10.1016/B978-044450896-6.50010-8)
21. Rachev, S.T.; Stein, M.; Sun, W. Copula Concepts in Financial Markets. Portf. Institutionell **2009**, 4, 12–15.
22. Kim, S.; Kang, M. Financial Series Prediction Using Attention LSTM. arXiv **2019** [, arXiv:1902.10877. [CrossRef]](https://doi.org/10.48550/arXiv.1902.10877)


Appl. Sci. **2025**, 15, 1034 30 of 31


23. Mittal, S.; Chauhan, A.; Nagpal, C.K. Stock Market Prediction by Incorporating News Sentiments Using BERT. In Modern
Approaches in Machine Learning & Cognitive Science: A Walkthrough; Gunjan, V.K., Zurada, J.M., Eds.; Studies in Computational
[Intelligence; Springer: Cham, Switzerland, 2022; Volume 1027, pp. 65–78. [CrossRef]](http://dx.doi.org/10.1007/978-3-030-96634-8_4)
24. Lee, S.I.; Yoo, S.J. Multimodal Deep Learning for Finance: Integrating and Forecasting International Stock Markets. J. Supercomput.
**2020** [, 76, 8294–8312. [CrossRef]](http://dx.doi.org/10.1007/s11227-019-03101-3)
25. Qin, J. MSMF: Multi-Scale Multi-Modal Fusion for Enhanced Stock Market Prediction. arXiv **2024** [, arXiv:2409.07855. [CrossRef]](https://doi.org/10.48550/arXiv.2409.07855)
26. Gao, H.; Kou, G.; Liang, H.; Zhang, H.; Chao, X.; Li, C.; Dong, Y. Machine Learning in Business and Finance: A Literature Review
and Research Opportunities. Financ. Innov. **2024** [, 10, 86. [CrossRef]](http://dx.doi.org/10.1186/s40854-024-00629-z)
27. Usmonov, B. The Impact of the Financial Ratios on the Financial Performance. A Case of Chevron Corporation (CVX). In
International Conference on Internet of Things, Smart Spaces, and Next Generation Networks and Systems, Proceedings of the 23rd
International Conference, NEW2AN 2023, and 16th Conference, ruSMART 2023, Dubai, United Arab Emirates, 21–22 December 2023;
[Springer Nature: Cham, Switzerland, 2023; pp. 333–344. [CrossRef]](http://dx.doi.org/10.1007/978-3-031-30258-9_37)
28. Costa, K. Anomaly Detection in Global Financial Markets with Graph Neural Networks and Nonextensive Entropy. arXiv **2023**,
[arXiv:2308.02914. [CrossRef]](https://doi.org/10.48550/arXiv.2308.02914)
29. Turiel, J.D.; Aste, T. Self-Organised Criticality in High Frequency Finance: The Case of Flash Crashes. arXiv **2021**, arXiv:2110.13718.

[[CrossRef]](https://doi.org/10.48550/arXiv.2110.13718)
30. Henouda, S.E.; Laallam, F.Z.; Kazar, O.; Harous, S.; Houfani, D. On the Effectiveness of Dimensionality Reduction Techniques
on High Dimensionality Datasets. In Proceedings of the 12th International Conference on Information Systems and Advanced
Technologies (ICISAT 2022), Istanbul, Turkey, 22–23 July 2022; Lecture Notes in Networks and Systems; Springer Nature: Cham,
[Switzerland, 2022; Volume 624, pp. 156–166. [CrossRef]](http://dx.doi.org/10.1007/978-3-031-25344-7_15)
31. Ayesha, S.; Hanif, M.K.; Talib, R. Overview and Comparative Study of Dimensionality Reduction Techniques for High Dimensional
Data. Inf. Fusion **2020** [, 59, 44–58. [CrossRef]](http://dx.doi.org/10.1016/j.inffus.2020.01.005)
32. Pareek, R.; Jacob, S. Data Compression and Visualization Using PCA and t-SNE. Int. J. Data Sci. Anal. **2021**, 9, 23–35.
33. Kohler, J.; Kronenberger, R.; Wagner, P. Classifying and Grouping Narratives with Convolutional Neural Networks, PCA and
t-SNE. Proc. Int. Conf. Comput. Soc. Sci. **2020**, 12, 45–58.
34. Gassen, J.; Skaife, H.A.; Veenman, D. Illiquidity and the Measurement of Stock Price Synchronicity. Contemp. Account. Res. **2020**,
[37, 419–456. [CrossRef]](http://dx.doi.org/10.1111/1911-3846.12519)
35. Amihud, Y.; Noh, J. Illiquidity and Stock Returns II: Cross-Section and Time-Series Effects. Rev. Financ. Stud. **2020**, 33, 1040–1072.

[[CrossRef]](http://dx.doi.org/10.1093/rfs/hhaa080)
36. Alaparthi, S.; Mishra, M. Bidirectional Encoder Representations from Transformers (BERT): A Sentiment Analysis Odyssey. arXiv
**2020** [, arXiv:2007.01127. [CrossRef]](https://doi.org/10.48550/arXiv.2007.01127)
37. Yadav, N. Enhancing Stock Trend Prediction Using BERT-Based Sentiment Analysis and Machine Learning Techniques. Int. J.
Quant. Res. Model. **2024** [, 5, 1–11. [CrossRef]](http://dx.doi.org/10.46336/ijqrm.v5i1.567)
38. Huang, X.-W.; Wang, W.; Emura, T. A Copula-Based Markov Chain Model for Serially Dependent Event Times with a Dependent
Terminal Event. Jpn. J. Stat. Data Sci. **2021** [, 4, 917–951. [CrossRef]](http://dx.doi.org/10.1007/s42081-020-00087-8)
39. Liang, Z.; Ismail, M.T.; Qu, H. Text Sentiment Analysis on VIX’s Impact on Market Sentiment Dynamics. In Recent Advances on
Soft Computing and Data Mining; Ghazali, R., Nawi, N.M., Deris, M.M., Abawajy, J.H., Arbaiy, N., Eds.; Springer Nature: Cham,
Switzerland, 2024; pp. 115–124.
40. Liu, X. Volatility Modeling of S&P500 Returns: A Comparative Study of GARCH Family Models and VIX. In 2020 International
Conference on Data Processing Techniques and Applications for Cyber-Physical Systems; Huang, C., Chan, Y.W., Yen, N., Eds.; Springer:
Singapore, 2021; pp. 257–264.
41. Bianchi, S.; Di Sciorio, F.; Mattera, R. Forecasting VIX with Hurst Exponent. In Mathematical and Statistical Methods for Actuarial
Sciences and Finance; Corazza, M., Perna, C., Pizzi, C., Sibillo, M., Eds.; Springer International Publishing: Cham, Switzerland,
2022; pp. 90–95.
42. More, G.S.; Bartakke, P. Real-Time Implementation of Automatic License Plate Recognition System. In International Conference on
[Advances and Applications of Artificial Intelligence and Machine Learning; Springer Nature: Singapore, 2023; pp. 585–597. [CrossRef]](http://dx.doi.org/10.1007/978-981-99-5974-7_47)
43. Li, B. Optimizing Embedded Neural Network Models. In Embedded Artificial Intelligence: Principles, Platforms and Practices;
[Springer: Singapore, 2024; pp. 217–247. [CrossRef]](http://dx.doi.org/10.1007/978-981-97-5038-2_10)
44. Guinea-Cabrera, M.A.; Holgado-Terriza, J.A. Digital Twins in Software Engineering—A Systematic Literature Review and Vision.
Appl. Sci. **2024** [, 14, 977. [CrossRef]](http://dx.doi.org/10.3390/app14030977)
45. Amihud, Y. Illiquidity and Stock Returns: Cross-Section and Time-Series Effects. J. Financ. Mark. **2002** [, 5, 31–56. [CrossRef]](http://dx.doi.org/10.1016/S1386-4181(01)00024-6)
46. Kumar, I.; Dogra, K.; Utreja, C.; Yadav, P. A Comparative Study of Supervised Machine Learning Algorithms for Stock Market
Trend Prediction. In Proceedings of the 2018 Second International Conference on Inventive Communication and Computational
[Technologies (ICICCT), Coimbatore, India, 20–21 April 2018; IEEE: Piscataway, NJ, USA, 2018; pp. 1003–1007. [CrossRef]](http://dx.doi.org/10.1109/ICICCT.2018.8473214)


Appl. Sci. **2025**, 15, 1034 31 of 31


47. Nabipour, M.; Nayyeri, P.; Jabani, H.; Shahab, S.; Mosavi, A. Predicting Stock Market Trends Using Machine Learning and Deep
Learning Algorithms via Continuous and Binary Data: A Comparative Analysis. IEEE Access **2020** [, 8, 150199–150212. [CrossRef]](http://dx.doi.org/10.1109/ACCESS.2020.3015966)
48. Clapham, B.; Haferkorn, M.; Zimmermann, K. The Impact of High-Frequency Trading on Modern Securities Markets. In Business
[& Information Systems Engineering; Springer International Publishing: Cham, Switzerland, 2023; Volume 65, pp. 7–24. [CrossRef]](http://dx.doi.org/10.1007/s12599-022-00768-6)
49. Alaminos, D.; Salas, M.B.; Fernández-Gámez, M.A. High-Frequency Trading in Bond Returns: A Comparison Across Alternative
Methods and Fixed-Income Markets. In Computational Economics; Springer International Publishing: Cham, Switzerland, 2024;
[Volume 64, pp. 2263–2354. [CrossRef]](http://dx.doi.org/10.1007/s10614-023-10502-3)


**Disclaimer/Publisher’s Note:** The statements, opinions and data contained in all publications are solely those of the individual
author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to
people or property resulting from any ideas, methods, instructions or products referred to in the content.


