## **MDGNN: Multi-Relational Dynamic Graph Neural Network for Comprehensive** **and Dynamic Stock Investment Prediction**

**Hao Qian** [1] **, Hongting Zhou** [1] **, Qian Zhao** [1] **, Hao Chen** [1] **, Hongxiang Yao** [2] **,**
**Jingwei Wang** [1] **, Ziqi Liu** [1] **, Fei Yu** [1] **, Zhiqiang Zhang** [1] **, Jun Zhou** [1*]

1Ant Group,Hangzhou,China
2Alibaba Group,Hangzhou,China
_{_ qianhao.qh,zhouhongting.zht,zq317110,chuhu.ch,wangjingwei.wjw,ziqiliu,lingyao.zzq,jun.zhoujun _}_ @antgroup.com
henry.yhx@alibaba-inc.com



**Abstract**


The stock market is a crucial component of the financial system, but predicting the movement of stock prices is challenging due to the dynamic and intricate relations arising from
various aspects such as economic indicators, financial reports,
global news, and investor sentiment. Traditional sequential
methods and graph-based models have been applied in stock
movement prediction, but they have limitations in capturing
the multifaceted and temporal influences in stock price movements. To address these challenges, the Multi-relational Dynamic Graph Neural Network (MDGNN) framework is proposed, which utilizes a discrete dynamic graph to comprehensively capture multifaceted relations among stocks and their
evolution over time. The representation generated from the
graph offers a complete perspective on the interrelationships
among stocks and associated entities. Additionally, the power
of the Transformer structure is leveraged to encode the temporal evolution of multiplex relations, providing a dynamic
and effective approach to predicting stock investment. Further, our proposed MDGNN framework achieves the best performance in public datasets compared with state-of-the-art
(SOTA) stock investment methods.


**Introduction**


The stock market is a crucial component of the financial
system, offering investors a marketplace to trade shares of
a wide range of assets. Nevertheless, predicting the movement of stock prices is challenging due to the dynamic and
intricate relations arising from various aspects. The active
trading behaviors of investors, such as buying and selling,
drive the fluctuations in stock prices. Additionally, the stock
market is influenced by several factors, including economic
indicators, financial reports, global news, political events, investor sentiments, and many others. Hence, it’s indispensable to integrate comprehensive and multifaceted relations
to capture the dynamics of the stock markets accurately.
Two lines of research have been applied to stock movement prediction. Traditional sequential methods (Hochreiter and Schmidhuber 1997; Chung et al. 2014; Feng et al.
2019a; Lin et al. 2021; Zhang, Aggarwal, and Qi 2017) propose to capture the temporal patterns of stock movement


*Corresponding author
Copyright © 2024, Association for the Advancement of Artificial
Intelligence (www.aaai.org). All rights reserved.



by optimizing the temporal dependency encoder, which employs sequential extraction techniques (Jain and Medsker
1999; Devlin et al. 2019). Nevertheless, the majority of these
methods still assume that stocks are independent of each
other and overlook the influence of complex relations. In
addition, graph-based models (Xu et al. 2021a; Chen and
Robert 2021a; Wang et al. 2021a; Sawhney et al. 2021;
Wang et al. 2022) incorporate heterogeneous information
explicitly from data or implicitly mine it from textual data to
capture the interdependence of stocks by designing various
graph representation methods. However, these approaches
could still be dissatisfactory due to the following two issues.
(1) **Multifacetedness** . The stock price movement is influenced not only by a single factor but also by multiple relations among stocks, industries, investment banks, etc. For
example, changes in the stock prices in a particular industry
can be caused by a variety of factors, such as high product demand, new government policies, the rise of raw material costs, and negative earnings reports from large companies. Similarly, investment banks can influence stock prices
in numerous ways, including conducting research on companies, releasing positive or negative reports, and trading
shares. Therefore, accurately predicting the movement of
stock prices requires consideration of the multifaceted relations among stocks. Previous graph-based methods for stock
investment prediction have only utilized single relations between stocks, ignoring the potential of incorporating other
complex relations as auxiliary information.
(2) **Temporal** . The movement of stock prices and the
multifaceted relations among stocks are not static but exhibit temporal evolution. Stock prices can change rapidly
due to external factors such as economic conditions, political
events, and regulatory changes, while internal factors such
as company earnings and industry performance can also influence the movement of stock prices over time. Relationships among stocks change over time due to factors such as
investment banks trading stocks, common shareholders coholding stocks, and companies releasing products into new
industries. Hence, accurately predicting the movement of
stock prices and anticipating the impacts of these changes
requires a dynamic approach that considers the historical
trends and evolving relationships among stocks.
To address the aforementioned issues, we introduce a
novel framework to underline the multifacetedness and tem

poral influences in stock investment prediction and propose a **M** ulti-relational **D** ynamic **G** raph **N** eural **N** etwork
( **MDGNN** ). Overall, we utilize the discrete dynamic graph
framework to tackle the stock investment prediction. Specifically, to comprehensively capture the multifacetedness nature of stocks, we construct each graph snapshot with daily
stock information and relationship data, which is then analyzed with a multi-relational graph embedding layer. The
generated representation from the multi-relational graph offers a thorough and complete perspective on the interrelationships among stocks and associated entities. Additionally, we leverage the power of the Transformer structure to
encode the temporal evolution of multiplex relations, providing a dynamic and effective approach to predicting stock
investment. Our contributions are summarized as follows:


 - We discuss the multifacetedness and temporal in the context of stock investment prediction tasks. We also provide
insights on modeling complex stock relations based on
empirical evidence.

 - We propose to capture the multifaceted and temporal
evolution nature of stocks with a multi-relational dynamic graph and generate a comprehensive representation of the stock market.

 - We perform extensive experiments on public datasets to
verify the superiority of our proposed framework. With
detailed analysis, we demonstrate the effectiveness of the
multi-relational dynamic graph in tackling the stock investment prediction task.


**Related Work**

**Stock Trend Prediction.** In quantitative trading, the ability
to anticipate stock trends is crucial. To accomplish this task,
a multi-factor model is commonly employed, as detailed in
Nagel’s recent work (Nagel 2021). This model considers
several influential factors from an econometrics standpoint,
including trading volumes and prices, as well as companyspecific fundamental data like earnings and debt ratio.
When utilizing learning-based methods, it’s a common
practice to start with linear regression (Gu, Kelly, and Xiu
2020). Moreover, (Roy et al. 2015) utilized ordinary least
squares equipped with regularization, such as ridges and
lasso, to overcome the over-fitting issues. However, linear
models have limitations in capturing complicated patterns
in stock price trends. To overcome this limitation, attempts
have been made to incorporate more complex learning techniques. XGBoost (Han, Kim, and Enke 2023) based method
is developed and evaluated through an empirical analysis of
companies listed on the NASDAQ. Neural-network-based
LSTM (Nelson, Pereira, and De Oliveira 2017) is utilized in
predicting future trends of stock prices and shows potential
to tackle the challenge of an immensely complex, chaotic,
and dynamic environment for the stock market.
**Dynamic Graph Neural Networks.** The above-mentioned
methods for predicting stock trends primarily concentrate
on individual stocks and disregard the interdependence and
resulting interactions between various stocks. For instance,
stocks that belong to the same supply chain are interrelated
due to profit transmission.



In recent years, GNN has gained great success owing to its
powerful capability of representing complex relations. Traditional GNN methods (e.g., GCN (Kipf and Welling 2017),
GAT (Veliˇckovi´c et al. 2018)) are mostly based on static
graphs where nodes and edges don’t change over time. However, many real-world relations (e.g., financial transactions,
social relations) are continuously evolving, in which dynamic graphs are indispensable to capture the advancing relations. Several approaches have been proposed to represent
dynamic graphs. One method is RSR (Feng et al. 2019b),
which incorporates sector and supply chain relation information into its temporal graph convolution. Another approach
is MGRN (Chen and Robert 2021b), which utilizes more relationships such as historical price. This is calculated by the
correlation coefficient of two stocks’ daily return time series.
The multi-graph embedding combined with text embedding
extracted from the news is then fed into an LSTM network
to predict the stock trend. HATR (Wang et al. 2021b) takes
this further by introducing topicality associations in graph
modeling. Additionally, Concept-oriented shared information for stock trend forecasting (Xu et al. 2021b) proposed to
mine hidden relations by designing a hidden concept module. This approach successfully mined information beyond
that carried by predefined concepts. Evolvegcn (Pareja et al.
2020) exploits the combination of graph convolution and
RNN (Jain and Medsker 1999) to capture both the topological structures and temporal relations.


**Preliminary**


**Definition 1. Problem Formulation.** Given that the relationships between stocks are multifaceted and changing on
a daily basis, we propose a Dynamic Graph Neural Network (DGNN) to capture and represent them. Let _G_ =
is a multi-relational graph snapshot at trading day t and _{G_ 1 _, G_ 2 _, ..., GT }_ represent DGNN, where _Gt_ = ( _Vt, Et, R Tt_ )
is the total number of snapshots. For a stock node _vit_ _t_,
the closing price at a trading day t is denoted as _pit ∈V_ . The
ground-truth label of stock _vit_ on trading day t based on the
return between two consecutive trading days is denoted as
_yit_ = _pi,t_ +1 _pit−pit_ benchmark _t_, in which benchmark _t_ is

_−_
the return of the benchmark index on trading day _t_ .
We formulate the stock prediction as a node regression
task that utilizes DGNN to learn a scoring function, **f** ( _G_ ; **Θ** ),
parameterized by **Θ** . The scoring function is usually optimized by minimizing the loss function as:


_L_ =      - _ℓ{_ **Y** _,_ **f** ( _G_ ; **Θ** ) _},_ (1)

_N_


where _N_ is the set of training samples, and _ℓ_ is the loss computed from each sample.


**Algorithm Design**


In the following sections, we will describe the architecture of
the MDGNN model as depicted in Figure 1, which includes
the Intra-day layer, the Inter-day Temporal Extraction layer,
and the prediction layer.


|(a) Intra-day Graph Snapshot|(b) Inter-day Temporal Extraction Layer|
|---|---|
|…<br>(a.1) Multi-relational Graph Construction<br>(a.2) Hierarchical Multi-relational<br>Graph Embedding Layer<br>_⇥L_<br>Step 2. Stock→ Others<br>Step 1. Others→ Stock<br>Step 3. Meta-Path Aggregation<br>_G_1<br>_G_2<br>_GT_|…<br>V<br>Q<br>K<br>ALIBI position<br>Softmax<br>stock<br>embeddings<br>?<br>Excess<br>Return<br>_T_<br>_n_<br>1<br>2<br>_T_<br>3<br>4<br>5<br>6<br>_d_|
|…<br>(a.1) Multi-relational Graph Construction<br>(a.2) Hierarchical Multi-relational<br>Graph Embedding Layer<br>_⇥L_<br>Step 2. Stock→ Others<br>Step 1. Others→ Stock<br>Step 3. Meta-Path Aggregation<br>_G_1<br>_G_2<br>_GT_|Bank<br>Industry<br>Invisible node<br>Visible node<br>Stock<br>History node<br>Future node<br>Sum<br>Multiply<br>Dot product|



Figure 1: The overview architecture of the MDGNN Model.



**Intra-day Graph Snapshot**


In this section, we outline the framework for capturing node
representations from graph snapshots generated on each
trading day. The framework comprises two key components:
the construction of the multi-relation graph and the graph
embedding layer.
**Multi-relational Graph Construction** The performance of
a single stock is influenced by a wide range of factors beyond its individual characteristics. As the stock markets are
complex and multifaceted, a singlet relation is not sufficient
to depict the intricate relations. As such, it is important to
consider the correlations between stocks from comprehensive relations so that a more accurate picture of the overall
performance of stock markets can be depicted.
To tackle the intricacy of stock markets, we integrate relations from industry, investment banks, and stock pairs to establish a multi-relational graph. This approach enables us to
reveal these complex connections and offer a deeper understanding of the underlying dynamics of the financial system.
(1) _Industry Graph_ : The performance of a company and
its corresponding stock is closely tied to the industry in
which it operates. For instance, as an industry is growing
rapidly, companies in that industry are likely to experience
increased demand for their products or services, which will
lead to higher revenue and profits. As a result, the stock
prices of these companies are likely to increase. Besides, the
products manufactured by a company can either serve as raw
materials for another industry or depend on the raw materials produced by another industry. Therefore, any increase in
the cost of raw materials can result in an increase in the expenses of companies. Additionally, government regulations
and policies toward industries can significantly impact the
associated companies. To be specific, we represent the stock
as _S_ and the industry as _I_, while the connection between
them is denoted as _SI_ . This connection contains features
_E_
that encode the aforementioned supply, demand, competition, and regulatory connections to account for the impact



transmission from the industry.
(2) _Investment Bank Graph_ : Investment banks greatly impact stock because they provide a wide range of services
related to stock markets. Investment banks often act as market makers for stocks, meaning they provide liquidity to
the market by buying and selling stocks on a regular basis. In addition, investment banks provide research reports
on stocks regarding the company’s financial performance,
industry trends, and other factors. These relationships allow
investment banks to have an impact on the price of the stock.
We extract the buy, sell, research, and advisory relations
from investment banks to capture the wield significant influence over stock prices. We denote the investment bank as
and the connection between that and stock as _SB_, which
_B_ _E_
incorporates the intricate aforementioned relations.
(3) _Stock Graph_ : Stocks have a great impact on other
stocks because of the interconnectedness of the stock market and the various factors that can affect stock prices. A
company’s earnings can lead to increased or reduced demand for its stock, as well as other companies in the same
industry or sector. In some cases, companies can be held
by the same owners, in which the co-holding relations offer a means of gauging the correlation among stocks. Additionally, common shareholders may engage in simultaneous
buying or selling of a company’s stock during a specific period of time. Therefore, the performance of stocks can be
positively or negatively correlated with one another. To capture the interconnected nature of the stock market, we identify relationships between stocks based on factors such as
sector, ownership, and co-holding relations. These relationships are denoted as _SS_ .
_E_
To create the multiplex relations mentioned earlier, we
start by gathering daily trading data and textual data such
as macroeconomic reports, financial news, financial statements, and research reports from TuShare [1] . We then employ financial lexicons and syntactic methods, as suggested


1https://tushare.pro/


by (Wang, Wang, and Li 2020), to build the edges between
pairs of entities. Through intricate data preparation and extraction processes, we construct a multi-relational graph that
integrates stocks, industries, and investment banks as nodes
and multiplex relations as edges.
**Hierarchical Multi-relational Graph Embedding Layer**
As stated above, we construct a multi-relational graph from
different relationships associated with stocks. This enables
us to capture complex representations of the relationships
between stocks, leading to a more comprehensive understanding of stock investment modeling. Concretely, we define a few meta-paths starting from stock nodes, such
as “Stock-Stock ( _SS_ )”, “Stock-Bank-Stock ( _SBS_ )”, and
“Stock-Industry-Industry-Stock ( _SIIS_ )”. As both nodes
and edges have a distinct impact on stock nodes, we propose a hierarchical graph embedding layer that can aggregate and propagate information. Besides, edge features are
crucial in graph-based models as they encode essential information about the relationships between nodes. For instance,
in the context of stock market prediction, the features that
encode supply, demand, competition, and regulatory connections between an industry and its corresponding stocks
can provide valuable insights into the future trends of stocks.
Concretely, we utilize an attention mechanism when aggregating information from neighborhood nodes, allowing
the model to attend to distinctive attributes of the edges and
the nodes they connect. As demonstrated in (Veliˇckovi´c
et al. 2018), using multi-head attention in the graph attention
mechanism is advantageous. Hereby, the attention weight of
the _k_ -th head when aggregating the neighbors of target node
_vi_ is conducted as follows:



Specifically, we design a relation-aware graph module
that aggregates node and relation features from a multirelational graph in an adaptive manner as follows:



3




**h** _vi_ = _σ_ (



Softmax( **Wh** _ij_ ) **h** _ij_ ) _,_ (4)
_j_ =1



_βij_ = _a_ _[T]_ [ **Wh** _i||_ **Wh** _j||_ **We** _ij_ ] _,_



exp(LeakyReLU( _βij_ ))
_αij_ _[k]_ [=] ~~�~~



exp(LeakyReLU( _βij_ )) (2)

_j_ _[′]_ _∈Ni_ [exp(LeakyReLU(] _[β][ij][′]_ [))] _[,]_



where _Ni_ denotes the neighborhood nodes of the target node
_i_, _||_ represents the concatenation operation, and **W** is the
shared projection matrix. Moreover, we aggregate representations from multiple heads and use average pooling to update the target node’s representation as follows:







where **W** is a learnable matrix and **h** _vi_ is the representation of node _vi_ after incorporating multiple relations among
nodes. By assigning different attention weights to each representation, the model can prioritize the most informative
representations, enhancing the model’s ability to capture
important patterns and relationships. Moreover, analyzing
these weights makes it possible to understand the importance of each relation or meta-path in the final prediction.
This interpretability is crucial for understanding the reasoning behind the model’s decision-making process.
To enhance the representations of stock nodes, we stack
multiple hierarchical multi-relational graph embedding layers. The first layer captures local information, while subsequent layers capture increasingly global information. Hence,
as we stack multiple graph layers, nodes that are distant from
the originating node will be impacted. This facilitates the
modeling of the intricate relationships involved in the transmission of stock information. This also enables the model to
learn complex patterns and relationships in the graph, leading to improved performance. Specifically, we stack L GNN
layers to obtain the representation of each stock node _v_ on a
trading day _t_, denoted as **h** _vt_, using the final GNN layer.


**Inter-day Temporal Extraction Layer**

Although the node representation is obtained through the
graph embedding layer from each graph snapshot, the semantics of stocks and the relationships between them are
constantly evolving. For instance, every day, securities companies adjust their positions by selling the stocks of a company purchased the previous day while buying stocks of
companies that have not been purchased. Furthermore, the
features of stocks (e.g., the momentum, volatility, and yield
factors) are also changing due to the impact of market
changes every day. Therefore, it is essential to capture the
dynamic nature of nodes and the evolving relations among
graph snapshots in the temporal order.
To tackle the aforementioned challenge, we have developed a temporal extraction module that employs the transformer structure (Vaswani et al. 2017). This module enables
the extraction of the temporal evolution of graph snapshots’
propagation by taking in the representation of the target
nodes within a time window.
sent the node’s representation, from trading day t and look-Concretely, let **H** _v,t−δt_ : _t_ = _{_ **h** _vt′|t −_ _δt ≤_ _t_ _[′]_ _≤_ _t}_ repreing back to the preceding _δt_ trading days. Hereby, the window size _δt_ is a hyperparameter. To facilitate with the structure, we transform _hv,t−δt_ : _t_ into query **Q** and key **K**, and
value **V** as follows:


**Q** = **WQHv** _,_ **t** _−δ_ **t** : **t** _,_
**K** = **WKHv** _,_ **t** _−δ_ **t** : **t** _,_ (5)
**V** = **WVHv** _,_ **t** _−δ_ **t** : **t** _,_




- _αij_ _[k]_ **[W]** _[k]_ **[h]** _[j]_

_j∈Ni_



 [1]






 _,_ (3)



**h** _i_ = _σ_



_K_







_K_



_k_ =1



where **W** _[k]_ is the shared projection matrix and _K_ is the total
number of heads. Consequently, we obtain the stock representations from each meta-path. Specifically, we define the
stock representations from the meta-paths “ _SS_ ”, “ _SBS_ ”,
and “ ” as **h** _i_ 1, **h** _i_ 2, and **h** _i_ 3.
_SIIS_
However, combining these representations effectively can
be a challenging task. Attention mechanisms provide a solution by allowing the model to selectively focus on the most
relevant representations for the target node. By assigning
different attention weights to each representation, the model
can effectively combine and aggregate the information from
multiple meta-paths. This process not only captures the most
critical information but also helps reduce the noise and redundancy in the representations.


where **WQ**, **WK**, and **WV** are trainable weight matrices of
query, key, and value, respectively.
In addition, the temporal dependency of graph snapshots
is crucial for modeling the dependency in the node’s representation. Over time, the historical relationship between
stocks and current price changes will diminish, making stock
prices more susceptible to the influence of recent events.
Hereby, we leverage the relative position method proposed
in ALIBI (Press, Smith, and Lewis 2022) that adds a static,
non-learnable bias to the query-key dot product. It introduces an inductive bias in favor of recent events, as it imposes a penalty on attention scores between distant querykey pairs. Moreover, the penalty increases in proportion to
the distance between a key and a query.
Moreover, we also employ the forward mask to prevent
positions in the input sequence from attending to subsequent
positions during the self-attention mechanism. It’s applied to
the attention mechanism’s softmax operation to mask out the
future positions, ensuring that each position can only attend
to the previous positions.
We calculate the dot product of query and key vectors
to capture information between any node pair via a selfattention network, in which the multiplicative operation efficiently captures complex feature interactions. Then we apply the softmax function to scale the attention weight before
multiplying it with the corresponding value vector.


|Col1|# stocks # banks # industries # edges|
|---|---|
|CSI100|100<br>196<br>97<br>18,950,706|
|CSI300|300<br>202<br>191<br>62,500,988|



**Z** = softmax( **[QK]** _[T]_



~~_√_~~



_d_ + _m ·_ **P** + **M** ) **V** _,_ (6)



Table 1: Detailed statistics of the datasets.


1-dimensional institutional consensus expectations feature.
All of these features are normalized prior to analysis.
**Backtest.** We use the timeframe from 01/01/2020 to
02/31/2023 for backtest. The training cycle is set at half a
year, meaning that we train the model every six months, resulting in a total of seven models in the experimental set
cycle. The training set utilizes data and labels from the preceding six months, while the validation set employs those
from last month. The model utilizes fixed parameter values
for prediction during the following six months.
**Baselines.** To show the performance of our proposed model,
we compare MDGNN with SOTA methods. We select the
following models as the baseline for comparison: (1) Traditional time series modeling methods (MLP, LSTM (Hochreiter and Schmidhuber 1997), Transformer (Devlin et al.
2019)). (2) Homogeneous graph methods (GCN (Kipf and
Welling 2017), GAT (Veliˇckovi´c et al. 2018)). (3) Heterogeneous graph methods (RGCN (Schlichtkrull et al. 2017),
HAN (Han, Kim, and Enke 2023), HGT (Hu et al. 2020)).
(4) Dynamic graph methods (EvolveGCN (Pareja et al.
2020), HTGNN (Fan et al. 2021)).
**Metrics.** We utilize Information Coefficient (IC) (Li et al.
2019), Information Ratio (IR), Cumulative Return (CR), and
Precision@K (J¨arvelin and Kek¨al¨ainen 2000) as evaluation
metrics. IC evaluates the overall ranking performance, and
IR divides the excess return of a portfolio by its tracking
error. CR is the accumulated portfolio return based on the
prediction score. Precision@K evaluates whether the excess
returns of TopK stocks outperform the benchmark index.
**Implementation Details.** Our experiment is trained with
Nvidia V100 GPU, and all models are built using PyTorch.
The hidden size was set to 128, the number of GNN layers is
2, and the window size is 10. The training and validation sets
are kept consistent across all models. To ensure that all models receive sufficient training, we train each for 500 epochs
and implement an early stopping strategy.


**Experiment Result**

The results of our proposed method, as well as the other
baseline models, are presented in Table 2 for CSI100 and
CSI300 datasets. Our model outperforms all other methods
across all metrics. Based on these experimental findings, we
draw the following conclusions:
1) **Time series modeling and static graphs** : Traditional
time series modeling methods, such as MLP, primarily rely
on the intrinsic node features of the stock, while LSTM/Transformer places greater emphasis on temporal features.
However, homogeneous graph-based approaches, such as
GAT and GCN, only consider node features and stock connections. Despite their inferior performance on the CSI100
dataset, these methods outperform Transformer on the larger
CSI300 dataset.



where _m_ is a slope parameter, **P** is the position bias introduced from ALIBI, and **M** is the forward mask matrix.
**Z** combines the significant evolving patterns extracted from
the historical data between time period _t −_ _δt_ and _t_ . **z** _vt_ denotes the representation of stock node _v_ on trading day _t_ .


**Prediction Layer**

In stock investment prediction, we aim to estimate the probability ˆ _yvt_ that a given stock will yield a positive return on
trading day _t_ based on the stock’s representation **z** _vt_ as:


_y_ ˆ _vt_ = _σ_ ( **W** 1 **z** _vt_ + **b** 1) _._ (7)


where **W** 1 and **b** 1 are trainable matrices and bias; _σ_ is the
sigmoid activation function.


**Experiments**

To validate the efficacy of our method, we conducted extensive experiments using Chinese stock market data.


**Experiment Setup**

**Datasets.** First, we construct datasets using the CSI100
and CSI300 indices of China’s stock market with details
in Table 1. Next, we extract a set of 42-dimensional features, which includes 25-dimensional market performance
features such as opening price, closing price, change percentage, volatility, and turnover rate, 12-dimensional company valuation features such as P/E ratio, P/B ratio, and
P/S ratio, 4-dimensional company categorical features, and


|CSI 100 CSI 300<br>Methods<br>IC IR CR Prec@30 IC IR CR Prec@30|CSI 100|CSI 300|
|---|---|---|
|Methods<br>CSI 100<br>CSI 300<br>IC<br>IR<br>CR<br>Prec@30<br>IC<br>IR<br>CR<br>Prec@30|IC<br>IR<br>CR<br>Prec@30|IC<br>IR<br>CR<br>Prec@30|
|MLP|0.0027<br>0.0282<br>0.1166<br>0.4751<br>(2.25e-03)<br>(2.26e-02)<br>(8.10e-03)<br>(8.17e-04)|0.0039<br>0.0314<br>0.1721<br>0.4958<br>(9.42e-04)<br>(1.53e-02)<br>(1.08e-02)<br>(1.01e-03)|
|LSTM|0.0040<br>0.0335<br>0.1289<br>0.4808<br>(1.27e-03)<br>(1.31e-02)<br>(1.90e-03)<br>(2.70e-04)|0.0049<br>0.0345<br>0.1859<br>0.4958<br>(6.84e-04)<br>(1.09e-02)<br>(1.29e-02)<br>(1.99e-03)|
|Transformer|0.0058<br>0.0422<br>0.1383<br>0.4987<br>(2.50e-03)<br>(1.51e-02)<br>(7.47e-02)<br>(3.22e-03)|0.0063<br>0.0442<br>0.2122<br>0.5065<br>(1.95e-03)<br>(1.28e-02)<br>(1.14e-01)<br>(6.03e-03)|
|GAT|0.0031<br>0.0274<br>0.1534<br>0.4812<br>(9.08e-04)<br>(7.63e-03)<br>(2.45e-02)<br>(2.31e-03)|0.0066<br>0.0454<br>0.2653<br>0.4991<br>(1.50e-03)<br>(2.46e-02)<br>(2.42e-02)<br>(3.00e-04)|
|GCN|0.0038<br>0.0305<br>0.1616<br>0.4927<br>(1.34e-03)<br>(9.36e-03)<br>(8.64e-03)<br>(2.33e-03)|0.0075<br>0.0674<br>0.2816<br>0.5055<br>(9.85e-04)<br>(3.80e-02)<br>(2.88e-02)<br>(2.04e-03)|
|RGCN|0.0104<br>0.0578<br>0.1912<br>0.4985<br>(1.29e-03)<br>(7.47e-03)<br>(2.84e-02)<br>(2.59e-03)|0.0090<br>0.0845<br>0.5159<br>0.5104<br>(1.69e-03)<br>(1.42e-02)<br>(5.32e-02)<br>(1.85e-03)|
|HAN|0.0108<br>0.0525<br>0.2267<br>0.4997<br>(4.08e-04)<br>(2.69e-03)<br>(2.48e-02)<br>(3.25e-03)|0.0086<br>0.0848<br>0.3511<br>0.5112<br>(4.68e-03)<br>(4.53e-02)<br>(5.72e-02)<br>(4.53e-03)|
|HGT|0.0112<br>0.0657<br>0.2384<br>0.5036<br>(1.35e-03)<br>(7.46e-03)<br>(1.98e-02)<br>(4.72e-03)|0.0115<br>0.0874<br>0.4108<br>0.4923<br>(2.05e-03)<br>(1.17e-02)<br>(5.65e-02)<br>(6.93e-03)|
|EvolveGCN|0.0065<br>0.0538<br>0.1815<br>0.4961<br>(3.54e-04)<br>(3.18e-03)<br>(2.81e-02)<br>(2.26e-03)|0.0080<br>0.5012<br>0.4989<br>0.4830<br>(3.46e-04)<br>(4.69e-03)<br>(6.09e-02)<br>(3.11e-03)|
|HTGNN|0.0118<br>0.0724<br>0.2643<br>0.5039<br>(3.76e-03)<br>(2.45e-02)<br>(8.23e-02)<br>(3.54e-03)|0.0192<br>0.1773<br>0.4653<br>0.5126<br>(7.59e-04)<br>(9.94e-03)<br>(7.03e-02)<br>(1.12e-03)|
|**MDGNN**|**0.0123**<br>**0.0746**<br>**0.2741**<br>**0.5081**<br>**(2.75e-03)**<br>**(1.59e-02)**<br>**(8.11e-02)**<br>**(3.22e-03)**|**0.0322**<br>**0.2488**<br>**0.9828**<br>**0.5232**<br>**(2.43e-03)**<br>**(4.19e-03)**<br>**(1.13e-02)**<br>**(3.01e-03)**|


Table 2: Results of methods on public datasets. The last row in each dataset indicates the percentage of improvements gained
by the proposed method w.r.t the best-performed baseline. Prec@k is a shortened form of Precision@k.



2) **Heterogeneous and dynamic graphs** : The inclusion
of diverse heterogeneous graph information in algorithms,
such as RGCN, HAN, and HGT, has led to notable performance enhancements over prior approaches. Additionally,
we compared time series heterogeneous graph-based methods such as EvolveGCN and HTGNN, which are designed
for temporal and multi-relational graphs, respectively. Our
findings suggest that the incorporation of both temporal
and multi-relational graph information can yield further improvements in performance.
3) **Our proposed method** : Our proposed MDGNN algorithm, leveraging enhanced modules to capture information from the distinctive multi-relational graph structure of
stocks, surpasses previous time series heterogeneous graphbased algorithms on both datasets. Moreover, the performance improvement is more pronounced in the CSI300
dataset compared to the CSI100 dataset. This outcome can
be attributed to the inclusion of additional institutional and
industry nodes, which results in a larger training graph and
enables more effective information propagation. These findings provide further evidence of the effectiveness of constructing graphs for stock trend prediction.


**Ablation Study**


**Effect of Components.** To validate the design choices in our
proposed framework, we perform an ablation experiment by
removing four components individually: edge weight (w/o



edge), meta-path (w/o meta-path), hierarchical aggregation
(w/o aggregation), and temporal extraction layer (w/o temporal). The experiment is performed on the CSI300 dataset,
and the results are presented in Table 3. We observe that the
removal of the meta-path module results in the most significant decrease in performance, thereby confirming the effectiveness of the multi-relational graph in our framework.

|Col1|IC IR CR Prec@30|
|---|---|
|w/o edge|0.0268<br>0.2155<br>0.8950<br>0.5152|
|w/o meta-path|0.0216<br>0.1723<br>0.7502<br>0.5076|
|w/o aggregation|0.0303<br>0.2392<br>0.9402<br>0.5227|
|w/o temporal|0.0286<br>0.2226<br>0.8745<br>0.5215|
|MDGNN|0.0322<br>0.2488<br>0.9828<br>0.5232|



Table 3: The results of the effect of components.


**Effect of Relations.** To further confirm the effectiveness of
each relationship in our multi-relational graph, we present
the results in Table 4. Here, _SS_, _SB_, _SI_, and _II_ refer to
the relationships between stocks and stocks, stocks and investment banks, stocks and industries, and industries and industries, respectively. The default connection between different node types is bidirectional, and if the required edges
in the meta-path are removed, the corresponding meta-path
will also be removed. With the _SB_ and _SI_ edges, the performance improves to some extent, thereby confirming our


J.P. Morgan Broking
(Hong Kong) Limited







Commercial
Bank Services


**(a)**



Figure 2: The results of the case study.



basic assumption of constructing a multi-relational graph,
namely that the stock price changes of stocks held by the
same investment bank or belonging to the same industry exhibit a certain degree of consistency. Furthermore, the introduction of the connection between investment banks yields
a more significant effect than the connection between industries, as the former brings about greater differences in
information when multiple investment banks hold a stock,
whereas it can only belong to one industry.

|SS SB SI II|IC IR CR Prec@30|
|---|---|
|✓<br>-<br>-<br>-<br>✓<br>✓<br>-<br>-<br>✓<br>-<br>✓<br>-<br>✓<br>-<br>✓<br>✓<br>✓<br>✓<br>✓<br>-<br>✓<br>✓<br>✓<br>✓|0.0217<br>0.1727<br>0.7372<br>0.5128<br>0.0264<br>0.2092<br>0.8220<br>0.5203<br>0.0210<br>0.1632<br>0.7133<br>0.5101<br>0.0217<br>0.1802<br>0.7755<br>0.5134<br>0.0283<br>0.2300<br>0.9074<br>0.5208<br>0.0322<br>0.2488<br>0.9828<br>0.5232|



Table 4: The results of the effect of relations.


**Case Study**


A research report on investment bank holdings reveals a rising credit pulse trend from December 2021 to March 2022,
accompanied by an increase in the proportion of bank holdings by international investment institutions. To analyze this
trend, we focus on Chengdu Bank (601838.SH) and its subgraph, which consists of four stock nodes: Chengdu Bank
(601838.SH), Nanjing Bank (601009.SH), Jiangsu Bank
(600919.SH), and Vanke A (000002.SZ). The first three
stocks belong to the commercial banking service industry
and are held by the same institution. The last stock belongs
to the real estate industry and is held by a different institution, which also holds both Vanke A and Jiangsu Bank.
Figure 2(b) shows the average stock change rates for the
four selected stocks between January 4 and 17, 2022. Traditional temporal models predict negative change rates for
most bank-related stocks, except for 000002.SZ. However,
the MDGNN model enables the upward trend to propagate
through multiple relation graphs, influencing the change
rates of all bank-related stocks and leading to an increase
in the change rate of 600919.SH. Further analysis of the average stock change rates of three key industries during this
period is shown in Figure 2(c). The findings indicate that



the utilization of multiple relational graphs has a more pronounced influence on banks and real estate than securities.


**Hyperparameter Study**

We also design some experiments to check the sensitivity of
hyperparameters. In Figure 3(a), the changes in cumulative
return are depicted across different window sizes. It appears
that increasing the window size improves the effect, but only
up to a certain limit for information capture. Similarly, as the
number of GNN layers increases in Figure 3(b), the effect
also improves gradually, but an excessively high complexity
can lead to a decline in performance.


Figure 3: The results of hyperparameter study.


**Conclusion**

In this work, we formally define the multifacetedness and
temporal patterns of stocks through empirical analysis for
the first time and propose a novel hierarchical multirelational dynamic graph framework for modeling stock investment prediction. Our approach involves constructing a
multi-relational graph for each trading day and generating
a set of discrete graph snapshots within the specified lookback window size. In terms of the intra-day graph snapshot,
we design a hierarchical multi-relational graph embedding
layer to first aggregate the neighbor nodes within a specific
meta-path and then adaptively integrate the stock representation from distinct meta-paths. Furthermore, we incorporate
the transformer structure to aggregate the temporal evolving
patterns of stocks. We demonstrate the effectiveness and robustness of our proposed framework through extensive experiments. In the future, we would like to study MDGNN
with contrastive learning methods for stock investment prediction and improve performance even further.


**References**


Chen, Q.; and Robert, C. Y. 2021a. Graph-Based Learning
for Stock Movement Prediction with Textual and Relational
Data. In _The Journal of Financial Data Science_ .


Chen, Q.; and Robert, C.-Y. 2021b. Graph-based learning
for stock movement prediction with textual and relational
data. _arXiv preprint arXiv:2107.10941_ .


Chung, J.; Gulcehre, C.; Cho, K.; and Bengio, Y. 2014. Empirical Evaluation of Gated Recurrent Neural Networks on
Sequence Modeling. _arXiv:1412.3555_ .


Devlin, J.; Chang, M.-W.; Lee, K.; and Toutanova, K. 2019.
BERT: Pre-training of Deep Bidirectional Transformers for
Language Understanding. 4171–4186.


Fan, Y.; Ju, M.; Zhang, C.; Zhao, L.; and Ye, Y.
2021. Heterogeneous Temporal Graph Neural Network.
arXiv:2110.13889.


Feng, F.; Chen, H.; He, X.; Ding, J.; Sun, M.; and Chua, T.-S.
2019a. Enhancing Stock Movement Prediction with Adversarial Training. In _Proceedings of the Twenty-Eighth Inter-_
_national Joint Conference on Artificial Intelligence, IJCAI-_
_19_, 5843–5849. International Joint Conferences on Artificial
Intelligence Organization.


Feng, F.; He, X.; Wang, X.; Luo, C.; Liu, Y.; and Chua, T.S. 2019b. Temporal relational ranking for stock prediction.
_ACM Transactions on Information Systems (TOIS)_, 37(2):
1–30.


Gu, S.; Kelly, B.; and Xiu, D. 2020. Empirical asset pricing via machine learning. _The Review of Financial Studies_,
33(5): 2223–2273.


Han, Y.; Kim, J.; and Enke, D. 2023. A machine learning
trading system for the stock market based on N-period MinMax labeling using XGBoost. _Expert Systems with Applica-_
_tions_, 211: 118581.


Hochreiter, S.; and Schmidhuber, J. 1997. Long Short-Term
Memory. _Neural Computation_, 9(8): 1735–1780.


Hu, Z.; Dong, Y.; Wang, K.; and Sun, Y. 2020. Heterogeneous Graph Transformer. In _Proceedings of The_
_Web Conference 2020_, WWW ’20, 2704–2710. New York,
NY, USA: Association for Computing Machinery. ISBN
9781450370233.


Jain, L. C.; and Medsker, L. R. 1999. _Recurrent Neural Net-_
_works: Design and Applications_ . USA: CRC Press, Inc., 1st
edition. ISBN 0849371813.


J¨arvelin, K.; and Kek¨al¨ainen, J. 2000. IR Evaluation Methods for Retrieving Highly Relevant Documents. In _Pro-_
_ceedings of the 23rd Annual International ACM SIGIR Con-_
_ference on Research and Development in Information Re-_
_trieval_, SIGIR ’00, 41–48. New York, NY, USA: Association for Computing Machinery. ISBN 1581132263.


Kipf, T. N.; and Welling, M. 2017. Semi-Supervised Classification with Graph Convolutional Networks. In _5th In-_
_ternational Conference on Learning Representations, ICLR_
_2017, Toulon, France, April 24-26, 2017, Conference Track_
_Proceedings_ . OpenReview.net.



Li, Z.; Yang, D.; Zhao, L.; Bian, J.; Qin, T.; and Liu, T.-Y.
2019. Individualized Indicator for All: Stock-Wise Technical Indicator Optimization with Stock Embedding. In _Pro-_
_ceedings of the 25th ACM SIGKDD International Confer-_
_ence on Knowledge Discovery & Data Mining_, KDD ’19,
894–902. New York, NY, USA: Association for Computing
Machinery. ISBN 9781450362016.
Lin, H.; Zhou, D.; Liu, W.; and Bian, J. 2021. Learning Multiple Stock Trading Patterns with Temporal Routing Adaptor and Optimal Transport. In _Proceedings of the 27th ACM_
_SIGKDD Conference on Knowledge Discovery & Data Min-_
_ing_, KDD ’21, 1017–1026. New York, NY, USA: Association for Computing Machinery. ISBN 9781450383325.
Nagel, S. 2021. _Machine learning in asset pricing_, volume 8. Princeton University Press.
Nelson, D. M.; Pereira, A. C.; and De Oliveira, R. A. 2017.
Stock market’s price movement prediction with LSTM neural networks. In _2017 International joint conference on neu-_
_ral networks (IJCNN)_, 1419–1426. Ieee.
Pareja, A.; Domeniconi, G.; Chen, J.; Ma, T.; Suzumura,
T.; Kanezashi, H.; Kaler, T.; Schardl, T.; and Leiserson,
C. 2020. EvolveGCN: Evolving Graph Convolutional Networks for Dynamic Graphs. _Proceedings of the AAAI Con-_
_ference on Artificial Intelligence_, 34(04): 5363–5370.
Press, O.; Smith, N. A.; and Lewis, M. 2022. Train Short,
Test Long: Attention with Linear Biases Enables Input
Length Extrapolation. arXiv:2108.12409.
Roy, S. S.; Mittal, D.; Basu, A.; and Abraham, A. 2015.
Stock market forecasting using LASSO linear regression
model. In _Afro-European Conference for Industrial Ad-_
_vancement: Proceedings of the First International Afro-_
_European Conference for Industrial Advancement AECIA_
_2014_, 371–381. Springer.
Sawhney, R.; Agarwal, S.; Wadhwa, A.; Derr, T.; and Shah,
R. R. 2021. Stock Selection via Spatiotemporal Hypergraph
Attention Network: A Learning to Rank Approach. _Pro-_
_ceedings of the AAAI Conference on Artificial Intelligence_,
35(1): 497–504.
Schlichtkrull, M.; Kipf, T. N.; Bloem, P.; van den Berg, R.;
Titov, I.; and Welling, M. 2017. Modeling Relational Data
with Graph Convolutional Networks. arXiv:1703.06103.
Vaswani, A.; Shazeer, N.; Parmar, N.; Uszkoreit, J.; Jones,
L.; Gomez, A. N.; Kaiser, L. u.; and Polosukhin, I. 2017. Attention is All you Need. In _Advances in Neural Information_
_Processing Systems_, volume 30. Curran Associates, Inc.
Veliˇckovi´c, P.; Cucurull, G.; Casanova, A.; Romero, A.; Li`o,
P.; and Bengio, Y. 2018. Graph Attention Networks. _Inter-_
_national Conference on Learning Representations_ .
Wang, H.; Li, S.; Wang, T.; and Zheng, J. 2021a. Hierarchical Adaptive Temporal-Relational Modeling for Stock
Trend Prediction. In Zhou, Z.-H., ed., _Proceedings of the_
_Thirtieth International Joint Conference on Artificial Intel-_
_ligence, IJCAI-21_, 3691–3698. International Joint Conferences on Artificial Intelligence Organization. Main Track.
Wang, H.; Li, S.; Wang, T.; and Zheng, J. 2021b. Hierarchical Adaptive Temporal-Relational Modeling for Stock Trend
Prediction. In _IJCAI_, 3691–3698.


Wang, H.; Wang, T.; Li, S.; Zheng, J.; Guan, S.; and Chen,
W. 2022. Adaptive Long-Short Pattern Transformer for
Stock Investment Selection. In Raedt, L. D., ed., _Proceed-_
_ings of the Thirty-First International Joint Conference on_
_Artificial Intelligence, IJCAI-22_, 3970–3977. International
Joint Conferences on Artificial Intelligence Organization.
Main Track.

Wang, H.; Wang, T.; and Li, Y. 2020. Incorporating ExpertBased Investment Opinion Signals in Stock Prediction: A
Deep Learning Framework. _Proceedings of the AAAI Con-_
_ference on Artificial Intelligence_, 34(01): 971–978.

Xu, W.; Liu, W.; Wang, L.; Xia, Y.; Bian, J.; Yin, J.; and Liu,
T.-Y. 2021a. HIST: A Graph-based Framework for Stock
Trend Forecasting via Mining Concept-Oriented Shared Information. _arXiv preprint arXiv:2110.13716_ .

Xu, W.; Liu, W.; Wang, L.; Xia, Y.; Bian, J.; Yin, J.; and Liu,
T.-Y. 2021b. Hist: A graph-based framework for stock trend
forecasting via mining concept-oriented shared information.
_arXiv preprint arXiv:2110.13716_ .

Zhang, L.; Aggarwal, C.; and Qi, G.-J. 2017. Stock Price
Prediction via Discovering Multi-Frequency Trading Patterns. In _Proceedings of the 23rd ACM SIGKDD Interna-_
_tional Conference on Knowledge Discovery and Data Min-_
_ing_, KDD ’17, 2141–2149. New York, NY, USA: Association for Computing Machinery. ISBN 9781450348874.


