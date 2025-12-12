## **FinKario: Event-Enhanced Automated Construction of Financial** **Knowledge Graph**



Xiang Li [∗]

xli906@connect.hkust-gz.edu.cn
The Hong Kong University of Science
and Technology (Guangzhou)
Guangzhou, China


Zikai Wei
weizikai@idea.edu.cn
International Digital Economy
Academy
Shenzhen, China


**Abstract**



Penglei Sun [∗]

psun012@connect@hkust-gz.edu.cn
The Hong Kong University of Science
and Technology (Guangzhou)
Guangzhou, China


Yongqi Zhang [†]

yongqizhang@hkust-gz.edu.cn
The Hong Kong University of Science
and Technology (Guangzhou)
Guangzhou, China


**Keywords**



Wanyun Zhou
wzhou266@connect.hkust-gz.edu.cn
The Hong Kong University of Science
and Technology (Guangzhou)
Guangzhou, China


Xiaowen Chu [†]

xwchu@hkust-gz.edu.cn
The Hong Kong University of Science
and Technology (Guangzhou)
Guangzhou, China



Individual investors are significantly outnumbered and disadvantaged in financial markets, overwhelmed by abundant information and lacking professional analysis. Equity research reports
stand out as crucial resources, offering valuable insights. By leveraging these reports, large language models (LLMs) can enhance
investors’ decision-making capabilities and strengthen financial
analysis. However, two key challenges limit their effectiveness:
(1) the rapid evolution of market events often outpaces the slow
update cycles of existing knowledge bases, (2) the long-form and
unstructured nature of financial reports further hinders timely and
context-aware integration by LLMs. To address these challenges,
we tackle both data and methodological aspects. First, we introduce
the Event-Enhanced Automated Construction of Financial Knowledge Graph **(FinKario)**, a dataset comprising over 305 _,_ 360 entities,
9 _,_ 625 relational triples, and 19 distinct relation types. FinKario automatically integrates real-time company fundamentals and market
events through prompt-driven extraction guided by professional institutional templates, providing structured and accessible financial
insights for LLMs. Additionally, we propose a Two-Stage, GraphBased retrieval strategy **(FinKario-RAG)**, optimizing the retrieval
of evolving, large-scale financial knowledge to ensure efficient and
precise data access. Extensive experiments show that FinKario with
FinKario-RAG achieves superior stock trend prediction accuracy,
outperforming financial LLMs by **18.81%** and institutional strategies by **17.85%** on average in backtesting.


∗Equal Contribution.
†Corresponding author.


Permission to make digital or hard copies of all or part of this work for personal or
classroom use is granted without fee provided that copies are not made or distributed
for profit or commercial advantage and that copies bear this notice and the full citation
on the first page. Copyrights for components of this work owned by others than the
author(s) must be honored. Abstracting with credit is permitted. To copy otherwise, or
republish, to post on servers or to redistribute to lists, requires prior specific permission
and/or a fee. Request permissions from permissions@acm.org.
_Conference’17, Washington, DC, USA_
© 2025 Copyright held by the owner/author(s). Publication rights licensed to ACM.
ACM ISBN 978-x-xxxx-xxxx-x/YYYY/MM
[https://doi.org/10.1145/nnnnnnn.nnnnnnn](https://doi.org/10.1145/nnnnnnn.nnnnnnn)



Financial research report, Knowledge graph, RAG


**ACM Reference Format:**
Xiang Li, Penglei Sun, Wanyun Zhou, Zikai Wei, Yongqi Zhang, and Xiaowen
Chu. 2025. FinKario: Event-Enhanced Automated Construction of Financial
Knowledge Graph. In _._ [ACM, New York, NY, USA, 14 pages. https://doi.org/](https://doi.org/10.1145/nnnnnnn.nnnnnnn)
[10.1145/nnnnnnn.nnnnnnn](https://doi.org/10.1145/nnnnnnn.nnnnnnn)


**1** **Introduction**


The financial market is dominated by institutional investors, leaving
individual investors at a significant disadvantage [8, 21]. Individual investors yet often struggle to make informed decisions due
to a lack of access to professional-grade analysis [11]. Equity research reports, which provide expert insights into market trends
and company performance, serve as a critical resource to bridge this
gap [13, 38]. LLMs can reason through complex financial data and
interpret context [2, 29, 34]. These capabilities make them suited for
the analysis of financial research reports, thereby enabling timely
and scalable insights. Recent advances at the intersection of data
mining and financial trading [27, 37] further highlight the potential
of LLMs in this domain.
However, LLM-based research report analysis faces two primary
challenges: **Ch1**, the rapid evolution of financial events [6, 32],
which outpaces the slow update cycles of existing knowledge bases
shown in Table 1; and **Ch2**, the inherent complexity of processing
long-form, unstructured data [20, 30]. Events such as earnings releases, product launches, and regulatory changes are key drivers
of market behavior and are essential for understanding temporal
shifts in asset performance [19, 25]. Financial markets are characterized by a continuous stream of such events, which are often
reflected in research reports. Yet, both traditional knowledge bases
and modern LLMs struggle to keep pace with these dynamic updates. As illustrated in Figure 1 and Table 1, two key limitations
persist. **Lim1** : Current knowledge base approaches rely heavily on
static, target-only retrieval and report chunking strategies, which
lack semantic coherence, fail to provide contextual explanations
(i.e., "why"), and cannot incorporate evolving market signals in real
time. **Lim2** : Existing event-centric Financial Knowledge Graphs
(FKGs), for instance, still depend on manual or semi-automated


Conference’17, July 2017, Washington, DC, USA Xiang Li et al.


























|Col1|Discrete B stY ruD ct us ra ele cs h ange Knowledge Base<br>BYD expands Semantic coherence<br>BYD overseas presence… Dynamic update<br>Report chunking B inY crD ea’s s eR …evenue Why? Retrieve target only<br>CITI SERESS o Rva el e ve r es s n es uat s eru . . gc ( rt su otrr wae t t e hc gh …ia cn dg re is v e n) Kn So ew ml ae nd tg ice cG ohr ea rp enh ce<br>.2 p…0 r2 o5 D rey latn ta iem ei sc tu ap rgd ea tt e<br>AtP ti rn ig b uA tn eB gY rD aph 2 0 +2 4 Event graph Me .r g e . f. iI tnc. R e r i vv e &|
|---|---|
|Please predict the rise<br>and fall of ~~**BYD** ~~ Inc in<br>next week based on …<br>Retrieval<br>Investor|Please predict the rise<br>and fall of ~~**BYD** ~~ Inc in<br>next week based on …<br>Retrieval<br>Investor|
|||



**Figure 1: Comparison of Traditional Single-research Report**
**Retrieval vs. FinKario Retrieval.**


construction pipelines [7, 14, 16, 39], resulting in outdated representations that limit their effectiveness in dynamic environments.
Although LLMs excel at processing natural language, their internal knowledge remains static and infrequently updated, leading to
persistent knowledge lag [1, 22].
To address the mentioned challenge, we propose **FinKario**, a
dual-structured financial knowledge graph built from equity research reports that can capture financial attributes, indicators and
events automatically and dynamically ( **Ch1** ). It comprises two subgraphs: an **attribute subgraph** for stable fundamentals and an
**event subgraph**, which captures time-sensitive events like quarterly financial performance and key profitability drivers ( **Ch2** ).
The process begins with the automated generation of schema for
both subgraphs, using prompt-driven extraction guided by professional institutional frameworks such as the CFA handbook ( **Lim2** ).
Specifically, the schema for the event subgraph adopts a top-down
structure, guided by high-level categories extracted from academic
reports provided by the University of Wisconsin, and is further refined into a detailed event ontology based on the Financial Industry
Business Ontology (FIBO). Based on these schemas, the pipeline further extracts structured knowledge from financial research reports
using LLMs aligned with domain-specific templates. Moreover, a
quality control module ensures the reliability of the extracted knowledge by correcting erroneous or outdated information, normalizing
entities, and completing missing attributes with the support of the
Tushare financial data platform. We collect a corpus of research
reports from August 2024 to March 2025. The FinKario instance
comprises over 305 _,_ 360 entities, 9 _,_ 625 relational triples, and 19 distinct relation types. In addition to the FinKario dataset, to address
the retrieval challenge posed by dynamically evolving, large-scale
financial knowledge, we propose the **FinKario-RAG**, which first
retrieves information directly related to the queried entity, then
expands retrieval to related entities and relationships, ensuring a
holistic financial context essential for accurate predictions ( **Lim1** ).
To evaluate the effectiveness of FinKario, we conduct backtests
comparing the predictive accuracy of our method with traditional
financial LLMs and institutional strategies. Our results show that,
on average, FinKario, combined with FinKario-RAG, outperforms
existing financial LLMs by 18 _._ 81% and institutional strategies by
17 _._ 85% in predictive accuracy. Our ablation studies further verify
that FinKario-RAG surpasses existing mainstream retrieval methods by an average of 12 _._ 70% in predictive accuracy. The principal
contributions of this paper are as follows:




  - We introduce **FinKario**, a dynamic, event-driven financial
knowledge graph with over 305,360 entities, 9,625 relational
triples, and 19 relation types, supporting automated updates
without manual intervention or predefined domain knowledge, and enabling professional template–driven schema
construction.

  - We propose **FinKario-RAG**, a retrieval strategy that integrates both industry-level and index-level perspectives to
transcend the limitations of single-target retrieval, facilitating holistic and realistic analysis in line with practical investment scenarios and supporting retrieval over large-scale,
dynamically evolving financial knowledge.

  - We empirically validate FinKario-RAG through extensive
experiments, demonstrating that our method surpasses the
runner-up by **58.14%** in Sharpe ratio, **30.86%** in Accumulative rate of return, and **1.04%** in predictive accuracy, proving
its effectiveness for financial analysis and stock trend forecasting.


**2** **Related Work**

**2.1** **Financial Knowledge Graph**


In recent years, Financial Knowledge Graphs (FKGs) have gained
growing attention for their ability to improve financial data analysis and decision-making. Traditional approaches largely relied
on standard natural language processing techniques, including semantic recognition, classification, and Named Entity Recognition
(NER). For instance, Wang et al. [28] proposed datasets and evaluations specifically for the construction of financial knowledge
graphs, facilitating comprehensive assessments. Similarly, Liu et
al. [18] introduced an approach focusing on financial event evolution through knowledge association, providing systematic risk
identification and management. In contrast, recent methodologies
have begun leveraging large language models (LLMs) to summarize domain-specific corpora or participate directly in constructing
relational entities within financial knowledge graphs. Chen et al.

[5] introduced a retrieval-augmented framework that incorporates
structured financial knowledge graphs into language models to enhance reliability and accuracy in financial market analyses and report generation. Furthermore, Sun et al. [24] proposed a knowledgeenhanced prompt learning framework specifically aimed at improving financial news recommendation, leveraging FKGs to provide
context-aware and accurate recommendations. However, most existing methods still depend on predefined schemas and manual input,
underscoring the need for fully automated, schema-independent
FKG construction in future research.


**2.2** **Automatic Knowledge Graph Construction**


Recent advances have explored Automatic Knowledge Graph Construction (AKGC) using LLMs, with an increasing emphasis on
reducing manual schema engineering. Zhang et al.[36] proposed
the EDC framework, which decouples extraction, schema definition,
and canonicalization, allowing the schema to be either pre-defined
or self-generated. Similarly, Ding et al.[9] introduced TKGCon,
leveraging Wikipedia-derived ontologies, existing theme-specific
KGs, and LLM-generated relation sets to build fine-grained and


FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph Conference’17, July 2017, Washington, DC, USA


**Table 1: Comparison of key characteristics of financial knowledge graph construction methods, including events, dynamics,**
**automation, major sources, and the number of entities, relations, and triples.**


**Knowledge** **Event** **Dynamic Updated** **Automation** **Entities** **Relations** **Triples** **Major Source**


FR2KG [28] ✗ ✗ ✗ 17,799 13 1,328 Research Report
KGEEF [6] ✓ ✗ ✗ 5,262,423 / 325,786 News
T-FinKB [39] ✗ ✓ ✗ 3,974 16 / News
FinKG [14] ✗ ✗ ✗ 37,382,905 12 30M+ Market data
FEEKG [18] ✓ ✗ ✗ 112,000 12 / News
FinDKG [16] ✗ ✓ ✗ 13,645 15 / News
FMAG [5] ✗ ✓ ✗ 8,052 5 5,664 Research Report
FNRKPL [24] ✗ ✗ ✗ 11,432 6 52,384 News
EKG [7] ✗ ✗ ✗ / 9 / Market data
FinRipple [32] ✓ ✗ ✗ / 4 / News
**FinKario (Ours)** ✓ ✓ ✓ 305,360 19 9,625 Research Report



timely theme-specific KGs. SAC-KG [3] further integrated generation, verification, and pruning to iteratively construct highprecision domain KGs. In contrast, Su et al. [23] designed a rulebased framework over relational databases for power systems, relying on static schemas and device metadata. Despite these developments, most existing methods either expand pre-existing graphs
or apply prompt-based extraction without grounding in authoritative domain templates. This gap is particularly evident in the
financial domain, where consistency and interpretability are crucial, yet current AKGC approaches seldom incorporate professional,
domain-specific schemas.


**2.3** **LLMs in Finance**


The integration of Large Language Models (LLMs) into financial applications has progressed through distinct phases of methodological
innovation. Initial efforts focused on domain-specific pretraining,
exemplified by Wu et al. [29], who developed BloombergGPT, a 50billion-parameter model trained on proprietary financial datasets
that demonstrated superior performance in financial NLP tasks.
Concurrent work by Yang et al. [34] introduced FinGPT, an opensource alternative emphasizing real-time market adaptability through
self-supervised learning architectures. Building on these pioneering efforts, research expanded the scope and capabilities of LLMs
in finance. Li et al. [15] proposed Alphafin, a retrieval-augmented
stock-chain framework that benchmarks financial analysis by dynamically integrating financial data from multiple sources. Additionally, Yu et al. [35] developed FinCon, a synthesized multi-agent
system incorporating conceptual verbal reinforcement to enhance
financial decision-making through collaborative agent interactions.
Recent innovations have targeted multimodal understanding and
specialized training regimens. Gan et al. [10] established MMEFinance, a comprehensive benchmark evaluating cross-modal comprehension of financial texts, tables, and charts. Building on prior
work, recent efforts such as Fin-R1 [17] have advanced financial reasoning through high-quality CoT datasets, supervised fine-tuning,
and reinforcement learning. The field has progressed toward more
sophisticated frameworks incorporating retrieval, multi-agent collaboration, and multimodal reasoning, while ongoing challenges
remain in temporal reasoning and explainability for dynamic financial contexts.



**3** **Methodology**

**3.1** **FinKario construction**


To support structured interpretation of financial narratives, we
introduce a dual-schema design comprising an **Attribute Graph**
and an **Event Graph** . These are constructed via a schema-guided
extraction function:


F : (D × S) →G _,_


where F is a schema-guided extraction function that takes as input
a document corpus D and a schema S, and outputs a structured
graph G.
The Attribute Graph focuses on relatively stable entity-level
properties, such as a firm’s industry, exchange, code, product lines,
and risk factors. These attributes provide foundational background
knowledge and support context-aware retrieval tasks. In contrast,
the Event Graph extends factual information by capturing the underlying drivers of observed financial metrics, such as factors that
may trigger a rise in profitability, through a diverse set of _driven_
_categories_ (e.g., strategic actions or technological innovation).
Although the Attribute Graph offers a relatively static and straightforward snapshot of the current position and capabilities of a company, the Event Graph provides richer context with greater interpretative flexibility. It allows for deeper insight into a firm’s strategic
direction, potential growth trajectories, and underlying decision
logic, enabling more informed financial analysis and forecasting.
Table 1 presents our knowledge graph alongside existing financial knowledge graphs. Compared to the existing ones, which rely
on manually defined schemas and lack comprehensive knowledge
updates throughout the process. To construct these graphs in a
fully automated manner, we introduce **FinKario**, a dataset built
upon four primary modules, as depicted in Figure 2: _Domain Cor-_
_pus Acquisition_, _Schema Construction_, _Knowledge Population_, and
_Quality Control Refinement_ . Each module fulfills a distinct role in
automatically transforming raw financial reports into a robust KG
without any manually predefined schemas or ontologies.


_3.1.1_ _Domain Corpus Acquisition._ We begin by collecting raw financial research reports from the East Money website [1] . To facilitate


[1https://www.eastmoney.com](https://www.eastmoney.com)


Conference’17, July 2017, Washington, DC, USA Xiang Li et al.






































































|(e) Knowledge Graph<br>Vectorization & Injection<br>FinKario<br>Vector DB<br>Entity Relation<br>Graph vector|Today is Sep 1st 2024. Please<br>predict the rise and fall of BYD<br>Inc in next week based on …<br>User Query<br>Sub-graph<br>LLM LLM<br>Coarse-grained Fine-grained<br>Industry<br>Stock: BYD<br>Market cap<br>Date: Sep 1st 2024 Rate Price<br>…<br>(f) Two-stage Retrieval|Decision:<br>Stock Code: 002594.SZ<br>Prediction:Rise<br>Confidence Score: 8<br>Reasons:<br>1. Financial Indicators: The current share<br>price of BYD… 293.19-290.31 yuan, …<br>target price set at 438 yuan. This<br>indicates…<br>2. Main Products and Industry: BYD’s …<br>electric vehicles, … automobile<br>manufacturing industry. Its main<br>competitors include Seres and Changan<br>Automobile. Compared to these rivals,<br>BYD demonstrates stronger profitability<br>and cash flow…<br>3. Event: BYD’s increased investment in<br>overseas markets is expected to boost its<br>profits…(Strategic action)<br>…<br>Overall, …BYD’s stock price in next week<br>will rise…|
|---|---|---|
|**FinKario**<br>**Vector DB**<br>Entity<br>Relation<br>**Graph vector**<br>**(e) Knowledge Graph**<br>**Vectorization & Injection**|User Query<br>**LLM**<br>Today is Sep 1st 2024. Please<br>predict the rise and fall of**BYD**<br>Inc in next week based on …<br>Fine-grained<br>BYD<br>Sep 1st 2024<br>Industry<br>Market cap<br>Rate<br>Price<br>…<br>Coarse-grained<br>Sub-graph<br>Stock:<br>Date:<br>**LLM**<br>**(f) Two-stage Retrieval**|**(g) Investment Guidance**|



**Figure 2: The overall framework of FinKario and FinKario-RAG: (a)–(d) The construction process of FinKario; (e)–(g) Details of**
**the FinKario-RAG pipeline.**



text parsing, we employ MinerU [2] [26], which converts each report
into a standardized Markdown format. We then perform a refinement step to remove non-informative content such as disclaimers,
images, and repeated legal statements, ensuring that the resulting
corpus D [′] contains only the most relevant textual information for
downstream processing.


_3.1.2_ _Schema Construction._ In this module, we construct two distinct but complementary schemas: the Attribute Graph Schema and
the Event Graph Schema.

- **Schema for Attribute Graph.** We leverage standardized equity research templates from authoritative sources (e.g., the CFA


[2https://github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)


















|Event Graph<br>Revenue Efficiency Cost … Strategic Action Tech Innovation D Cr ai tv ee gn o|Col2|Col3|Col4|Col5|Col6|Col7|
|---|---|---|---|---|---|---|
|**Event Graph**<br>Revenue<br>Efficiency Cost<br>Strategic Action<br>Tech Innovation<br>**…**<br>**Driven**<br>**Catego**|||||||
|**Event Graph**<br>Revenue<br>Efficiency Cost<br>Strategic Action<br>Tech Innovation<br>**…**<br>**Driven**<br>**Catego**|Strategic Action<br>**…**|Strategic Action<br>**…**|Strategic Action<br>**…**|Strategic Action<br>**…**|Strategic Action<br>**…**|Strategic Action<br>**…**|
|Earning||Spin-off|Spin-off||Is applicable in|New product|
|Income-oriented<br>classifie**r** <br><br>Income-oriented<br>classifie|Overseas<br>expansion<br>|Overseas<br>expansion<br>|Merge /<br>Acquisition<br>|Merge /<br>Acquisition<br>|Has innovated|Iteration|
|Income-oriented<br>classifie**r** <br><br>Income-oriented<br>classifie|Overseas<br>expansion<br>|Overseas<br>expansion<br>|Merge /<br>Acquisition<br>|Merge /<br>Acquisition<br>|**…**|**…**|
|Income-oriented<br>classifie**r** <br><br>Income-oriented<br>classifie|**Top-Down**<br>**…**|**Top-Down**<br>**…**|**Top-Down**<br>**…**|**Top-Down**<br>**…**|**Top-Down**<br>**…**|**Top-Down**<br>**…**|



**Figure 3: Tree-Structured Schema for Event Graph.**


FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph Conference’17, July 2017, Washington, DC, USA


i



Institute [3] and J.P. Morgan [4] ) as reference guides. These templates,
designated as _𝜃_ CFA and _𝜃_ JPM, capture the core structure and content
of high-quality financial reports. Based on their organization, we design prompts to guide the LLM in identifying core attribute relation
types. Formally, we define: S _𝐴_ = LLM(Promptattr; _𝜃_ CFA _,𝜃_ JPM), and
S _𝐴_ is the set of attribute-level relation types such as _Industry_, _Risk_
_Factors_, and _Exchange_ . The schema S _𝐴_ serves as the foundation for
attribute-level knowledge population. Figure 2 details the schema
in part (b).

- **Schema for Event Graph.** We construct a hierarchical event i
schema S _𝐸_ using a top-down approach. At the first level, we generate high-level driven categories by prompting the LLM based on
the institutional template _𝜃_ WIS from the University of Wisconsin [5] :
C = LLM(Promptcat; _𝜃_ WIS), where C = { _𝑐_ 1 _,𝑐_ 2 _, . . .,𝑐𝑚_ } represents
the set of high-level event categories. For each category _𝑐𝑖_ ∈C,
we construct prompts grounded in the Financial Industry Business
Ontology (FIBO) [6], denoted as OFIBO, to generate corresponding
low-level event ontology: O _𝑐𝑖_ = LLM(Promptevent; _𝑐𝑖,_ OFIBO). The
resulting schema is defined as: S _𝐸_ = [�] _[𝑚]_ _𝑖_ =1 [{(] _[𝑐][𝑖][,𝑜]_ [) |] _[ 𝑜]_ [∈O] _[𝑐][𝑖]_ [}][. Fig-]
ure 3 visualizes the tree-structured event schema.


_3.1.3_ _Knowledge Population._ For each refined Markdown document D [′], entities are extracted at each timestamp _𝜏_ ∈ _𝑇_ via a
dedicated prompt guided by the previously formed schema S _𝐴_ and
S _𝐸_ :

EA _𝜏_ ; E E _𝜏_ _,_ R E _𝜏_ = LLM(Prompt _, 𝐷_ [′] _,_ S _𝐴,_ S _𝐸,𝜏_ ) _,_


where EA _𝜏_ and E E _𝜏_ denote the set of extracted entities at timestamp _𝜏_ . These timestamped entity sets EA _𝜏_ and relation types R _𝐴_
are combined to form the attribute knowledge graph for each stock
_𝑠_ :


   G _𝐴_ [(] _[𝑠]_ [)] = {( _𝑒ℎ,𝑟,𝑒𝑡_ _,𝜏_ ) | _𝑒ℎ,𝑒𝑡_ ∈EA _𝜏_ _,𝑟_ ∈R _𝐴_ } _,_

_𝜏_ ∈ _𝑇_


where _𝑒ℎ_ and _𝑒𝑡_ denote head and tail entities, respectively. Subsequently, a dynamic Event Knowledge Graph is constructed separately, guided by a distinct set of schema S _𝐸_ :


   G _𝐸_ [(] _[𝑠]_ [)] = {( _𝑒𝑠,𝑟_ [′] _,𝑒𝑜,𝜏_ ) | _𝑒𝑠,𝑒𝑜_ ∈E E _𝜏_ _,𝑟_ [′] ∈R E _𝜏_ } _,_

_𝜏_ ∈ _𝑇_


where _𝑒𝑠_ is the subject entity, _𝑒𝑜_ is the object entity, and _𝑟_ [′] represents the trigger relationship R E _𝜏_ . Finally, the comprehensive
financial knowledge graph for stock _𝑠_ integrates both attribute and
event knowledge graphs:


GFinKario [(] _[𝑠]_ [)] [=][ G] _𝐴_ [(] _[𝑠]_ [)] ∪G _𝐸_ [(] _[𝑠]_ [)] _._


This integrated graph G [(] _[𝑠]_ [)]
FinKario [effectively captures structured fi-]
nancial information along with inferred event interactions. Figure 4
illustrates the daily temporal structure of FinKario.


[3https://www.cfainstitute.org/sites/default/files/-/media/documents/support/](https://www.cfainstitute.org/sites/default/files/-/media/documents/support/research-challenge/challenge/rc-equity-research-report-essentials.pdf)
[research-challenge/challenge/rc-equity-research-report-essentials.pdf](https://www.cfainstitute.org/sites/default/files/-/media/documents/support/research-challenge/challenge/rc-equity-research-report-essentials.pdf)
[4https://www.wallstreetprep.com/knowledge/sample-equity-research-report/](https://www.wallstreetprep.com/knowledge/sample-equity-research-report/)
[5https://eiexchange.com/content/the-causal-analysis-a-great-way-to-tell-the-](https://eiexchange.com/content/the-causal-analysis-a-great-way-to-tell-the-financial-story)
[financial-story](https://eiexchange.com/content/the-causal-analysis-a-great-way-to-tell-the-financial-story)
[6https://spec.edmcouncil.org/fibo/ontology](https://spec.edmcouncil.org/fibo/ontology)



_3.1.4_ _Quality Control Refinement._ To ensure the reliability of the
constructed knowledge graph, we implement a refinement module
that addresses common issues in financial text extraction, including
entity ambiguity, missing numeric values, and extraction errors.
Specifically, the module performs entity normalization, attribute
completion via the Tushare platform [7], and error or placeholder
correction via the LLM. The complete refinement pipeline is detailed
in Algorithm 1.


**Algorithm 1** Quality Control Refinement


**Require:** Raw knowledge graph G [(] _[𝑠]_ [)]
FinKario [, reference dictionary]
Tref, and LLM(·) instantiated as GPT-4o-mini
**Ensure:** Refined knowledge graph G [′(] _[𝑠]_ [)]
FinKario
**// Step 1: Entity Normalization**

1: **for all** entity _𝑒_ ∈G [(] _[𝑠]_ [)]
FinKario **[do]**

2: **if** _𝑒_ is a name variant (e.g., "BYD Inc.", "BYD Auto") **then**

3: Replace _𝑒_ with canonical form (e.g., "BYD")

4: **end if**

5: **end for**


**// Step 2: Attribute Completion**

6: **for all** triple ( _𝑒ℎ,𝑟,𝑒𝑡_ ) ∈G [(] _[𝑠]_ [)]
FinKario **[do]**

7: **if** _𝑟_ is a numeric attribute (e.g., "Price", "Cap") and ( _𝑒𝑡_ is
missing or lacks unit) **then**

8: Query Tref for value and unit (e.g., CNY, USD, billions)

9: Replace _𝑒𝑡_ with correct value and unit

10: **end if**

11: **end for**


**// Step 3: Error Correction via LLM**

12: **for all** triple ( _𝑒ℎ,𝑟,𝑒𝑡_ ) ∈G [(] _[𝑠]_ [)]
FinKario **[do]**

13: **if** _𝑒𝑡_ contains a placeholder (e.g., "No relevant information
was found", "Extraction error") **then**

14: Re-feed the source Markdown passage to LLM(·)

15: Replace _𝑒𝑡_ with the corrected output from the LLM

16: **end if**

17: **end for**

18: **return** G [′(] _[𝑠]_ [)]
FinKario


**3.2** **FinKario-RAG**


The two-stage graph-based retrieval augmented generation pipeline
(FinKario-RAG) converts GFinKario [′(] _[𝑠]_ [)] [=][ (E] _[,]_ [ R)][ into actionable invest-]
ment advice through three interlocking modules, as illustrated in
Fig. 2.


_3.2.1_ _Knowledge Graph Vectorization & Ingestion._ To support semantic retrieval, the event-augmented financial knowledge graph
G [′(] _[𝑠]_ [)]
FinKario [is vectorized into three components: entity-level, relation-]
level, and graph-level representations.

- **Entity and Relation Embedding.** We encode all entities and relations using a graph encoder Φ to obtain the structural embedding
set:
Zlocal = Φ(GFinKario [′(] _[𝑠]_ [)] [)][ =][ {][e] _[𝑖]_ [}] _𝑖_ [| E|] =1 [∪{][r] _[𝑗]_ [}] [|R|] _𝑗_ =1 _[,]_


[7https://tushare.pro](https://tushare.pro)


Conference’17, July 2017, Washington, DC, USA Xiang Li et al.





01-Sep-2024


30-Aug-2024


29-Aug-2024


28-Aug-2024



























Date: 29-Aug-2024


**Figure 4: Temporal Visualization of FinKario.**


where e _𝑖_ and r _𝑗_ denote the latent vectors of the _𝑖_ -th entity and _𝑗_ -th
relation, respectively.

- **Graph-level Embedding.** To capture global context and topological semantics, we also compute a graph-level vector using a
readout function _𝜌_, where gglobal = _𝜌_ (GFinKario [′(] _[𝑠]_ [)] [)][.]

- **Vector Store Indexing.** The unified representation ZFinKario =
Zlocal ∪{gglobal} is normalized and stored in the vector database
V, which supports efficient maximum inner product search during
downstream retrieval.


_3.2.2_ _Two-stage Retrieval._ Given a user query _𝑞_, the system first
encodes it into a dense vector h _𝑞_ = Ψ( _𝑞_ ) via a language model
encoder Ψ. Retrieval is performed in two stages:

- **Coarse-grained Retrieval.** The first stage aims to identify rough
semantic anchors such as relevant stocks and dates. This is achieved
by matching h _𝑞_ against indexed stock and date representations in
the vector store:


Vcoarse = Rcoarse (h _𝑞,_ V _,𝑘𝑐_ ) _,_

returning the top- _𝑘𝑐_ coarse candidates (e.g., BYD, Sep 1 [st] 2024).

- **Fine-grained Retrieval.** Building on the coarse results, a finergrained retrieval is conducted to collect surrounding financial entities—such as industry, market cap, and price by searching over
relevant portions of the vector set:


Vfine = Rfine (h _𝑞,_ Vcoarse _,𝑘𝑓_ ) _,_


where _𝑘𝑓_ represents the number of related entities from fine-grained
process. To facilitate structured reasoning, the retrieved fine-level
vectors are mapped back to their original graph context to reconstruct a semantically aligned subgraph:

Gsub = Mapping(Vfine) _,_ Gsub ⊆GFinKario [′(] _[𝑠]_ [)] _[.]_

where Mapping(·) refers to a lookup procedure that aligns vectorretrieved entities with their corresponding nodes and edges in the
original graph G [′(] _[𝑠]_ [)]
FinKario [. This two-stage process allows FinKario-]
RAG to retrieve a compact, semantically coherent subgraph for
downstream reasoning, preserving both high-level user intent and
local financial context.


_3.2.3_ _Investment Guidance._ The subgraph Gsub and the user query
_𝑞_ are jointly fed into the final reasoning model:


_𝑦_ = LLMAnalyst ( _𝑞,_ Gsub) _,_



where _𝑦_ includes a predicted movement label (e.g., Rise or Fall),
an associated confidence level, and a textual rationale grounded in
the retrieved knowledge. This completes the FinKario-RAG pipeline
by converting graph-derived evidence into interpretable and actionable investment guidance.


**4** **Experiment Results**

**4.1** **Experiment Setup**


Given a universe of stocks S, for any stock _𝑠_ ∈S on a given
trading day _𝑡_, we evaluate a long-only trading strategy driven by
FinKario-RAG signals. The strategy operates as follows: (1) **Signal**
**Generation.** On trading day _𝑡_, FinKario-RAG generates a signal
_𝛾𝑠,𝑡_ for stock _𝑠_ ; (2) **Entry Rule.** If _𝛾𝑠,𝑡_ indicates a buy signal, we
initiate a position by purchasing the stock at the closing price _𝑐𝑠,𝑡_ +1
on day _𝑡_ + 1; (3) **Exit Rule.** The position is held until the last trading
day of the following week, denoted as _𝜏_ ( _𝑡_ ),, at which point the
stock is sold at the closing price _𝑐𝑠,𝜏_ ( _𝑡_ ) .


**4.2** **Dataset & Metrics**


We evaluate our model using a multi-source dataset that combines
textual and financial data. The raw research reports are collected
from the East Money website, covering the period from 2024-0828 to 2025-02-28. Corresponding stock price data for backtesting
is obtained from Tushare, spanning from 2024-08-28 to 2025-0307. In addition, we incorporate index components and industry
classification information provided by Wind platform to support
graph construction and semantic enrichment.
To evaluate the performance of our model, we adopt six widely
used metrics: **Annualized Rate of Return (ARR)** measures the
compound annual growth rate of the portfolio value over the evaluation period. **Volatility (VOL)** quantifies the annualized standard
deviation of weekly returns, indicating the portfolio’s risk level.
**Sharpe Ratio (SR)** quantifies risk-adjusted performance by dividing the annualized return by the annualized volatility. **Maximum**
**Drawdown (MDD)** measures the largest peak-to-trough decline
in portfolio value, representing the worst-case loss scenario. **Cal-**
**mar Ratio (CR)** assesses risk-adjusted returns by dividing the
annualized return by the absolute maximum drawdown. **Accuracy**
**(ACC)** measures the percentage of correct directional predictions
generated by FinKario-RAG trading signals. Together, these metrics provide a comprehensive view of both predictive quality and
practical investment performance of our model.


**4.3** **Baseline**


Our proposed approach is evaluated against four categories of
baselines:

- **Market Indices.** Market indices are standard passive benchmarks.
We report results on several representative indices, including the
**CSI 300**, **CSI 500**, **SSE Composite Index**, and **SSE Dividend**
**Index**, which cover major segments of the Chinese market.

- **Vanilla LLMs.** We include general-purpose language models such
as Qwen3-8B [33] and GPT-4o-mini [12], which are not specifically
tuned for financial tasks.


FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph Conference’17, July 2017, Washington, DC, USA




- **Financial Domain LLMs.** We evaluate several open-source financial language models, including FinMA [31], FinGPT [34], DISCFinLLM [4], XuanYuan-6B [8] and Stock-Chain [15]. These models
are tailored for financial forecasting and investment recommendations, making them suitable for downstream backtesting and
comparison.

- **Financial Institutions.** To the best of our knowledge, this is
the first work to incorporate real-world institutional strategies as a
baseline. The selected institutions—Tianfeng, Southwest, Sinolink,
Soochow, Guolian-Mingsheng, Guosen, Huaan, Kaiyuan, China
Fortune, and China Post—were chosen as leading brokerages that
frequently publish research reports, each appearing in at least 300
reports.


**4.4** **Experimental Results**


Figure 5 illustrates that FinKario-RAG consistently outperforms all
benchmark models in cumulative returns, showcasing the effectiveness of our knowledge graph-enhanced retrieval framework. In late
September 2024, most strategies surged in response to favorable
Chinese fiscal policies, followed by a period of pullback and sideways movement, during which SOOCHOW’s strategy remained
notably stable.
A major turning point occurred in early February 2025, as many
strategies rebounded. Stock-Chain exhibited a sharp spike, while
FinKario-RAG entered a phase of steady and accelerating growth,
ultimately surpassing nearly all competitors by early March. These
results highlight FinKario-RAG’s adaptability to market shifts, effectiveness in capturing transient signals, and robust performance
across volatile periods through its structured graph-based design.
In addition to the visual insights from cumulative NAV trends,
Table 2 presents a quantitative comparison that further validates
FinKario-RAG’s superiority. FinKario-RAG achieves the highest
scores in ARR (2.633), Sharpe Ratio (4.926), Calmar Ratio (15.315),
and ACC (0.581), while maintaining a moderate Maximum Drawdown (MDD) of 0.172. These results reflect a balanced and effective
investment strategy.
In terms of ARR, FinKario-RAG outperforms Guolian-Minsheng
(2.012) by 30.8%, SOOCHOW (1.625) by 62.0%, and exceeds StockChain by a significant 123.7%. For risk-adjusted returns, FinKarioRAG’s SR and CR represent improvements of 58.1% and 24.4% over
the runner-up performers. Although its volatility (0.534) is not the
lowest, it remains well-controlled relative to its high returns.
Regarding predictive accuracy, FinKario-RAG achieves a leading
ACC of 0.581, outperforming Guolian-Minsheng (0.575), China Fortune (0.573), and RAG (0.559). While some institutional strategies
also demonstrate strong accuracy, performance varies considerably
across institutions, with the maximum accuracy gap reaching 0.164.
Overall, FinKario-RAG strikes a robust risk-reward balance. Its
knowledge graph-enhanced design delivers both superior profitability and effective risk control, positioning it as a state-of-the-art
approach for LLM-based quantitative investment.


**4.5** **Ablation Study**


We conduct two ablation studies. All variants are built on the same
backbone, GPT-4o-mini, serving as both the chat-based reasoning


8https://huggingface.co/Duxiaoman-DI/XuanYuan-6B



module and the embedding encoder for vector retrieval, ensuring
consistency across comparisons.


_4.5.1_ _Varied Knowledge Source Injection._ Table 3 presents an ablation study quantifying the significance of varied knowledge sources.
Removing the Event graph (w/o Event graph) results in a dramatic
decrease in ARR, showing an 87.2% drop, from 2.633 to 0.336, and a
reduction in SR by 81.1%, from 4.926 to 0.932. In contrast, removing
the Attribute graph (w/o Attribute graph) also leads to performance
degradation, but the decline is less pronounced across all indicators,
underscoring the complementary role of the Event graph in enhancing model performance. Additionally, we examine the impact
of raw markdown content, which leads to a noticeable decline in
performance. The model struggles to filter out useful information,
particularly when processing long-text, highlighting its inefficiency
in handling unstructured data. Furthermore, we compare the opensource knowledge base HiDy [9], which integrates multiple sources
of financial data. The results suggest that HiDy provides valuable
supplementary knowledge but does not outperform the full knowledge graph structure in improving performance, with a reduction
in SR by 72.5%.


_4.5.2_ _Varied Retrieval Approach._ Table 4 highlights the ablation
study on varied retrieval approaches. We integrate FinKario with
traditional retrieval methods. The Vanilla RAG approach shows
lowest performance across all metrics, with ARR and SR both dropping by 85.7% and 80.5%, respectively. In contrast, the LightRAG
method shows modest gains, with ARR and SR improvements of
23.5% and 17.5%, respectively, suggesting the effectiveness of the
graph-based retrieval approach. However, it still underperforms
compared to FinKario-RAG. These results underscore the advantage
of FinKario-RAG framework, which delivers superior performance
across all metrics.


**4.6** **Case Study**


To illustrate model behavior, we compare FinKario-RAG with the
best-performing models in each category: Qwen3-8B (vanilla LLM),
Guolian-Mingsheng (institution), and Stock-Chain (financial LLM).
As depicted in Figure 6, FinKario-RAG exhibits a strong concentration in high-growth sectors such as Electrical Equipment, Semiconductor, and Healthcare—an allocation strategy that closely aligns
with the technology-led market rally observed around February
2025.
In contrast, Qwen3-8B and Stock-Chain present broader and less
focused industry allocations across their top 3–4 sectors. GuolianMingsheng narrows its focus mainly to Auto Parts and Semiconductor, which aligns with FinKario-RAG to some extent and helps
sustain performance in the later market stages. Although StockChain also overweights Semiconductor, its simultaneous heavy
allocation to sectors like Food, Coal Mining and Bank results in an
implicit internal hedging effect, partially diluting return potential
during sector rallies. FinKario-RAG’s industry targeting strategy,
by contrast, reflects higher consistency and adaptability to sector
momentum.


[9https://zenodo.org/records/12630355](https://zenodo.org/records/12630355)


Conference’17, July 2017, Washington, DC, USA Xiang Li et al.


**Figure 5: Accumulated returns (AR) of each baseline strategy on the financial-report dataset from August 28, 2024 to March 7,**
**2025. The figure shows the net asset value (NAV) curves over the weekly backtesting period.**


**Table 2: Performance comparison across market indices, vanilla LLMs, financial domain LLMs, and institutional strategies.**


**Model** **ARR↑** **VOL↓** **SR↑** **MDD↓** **CR↑** **ACC↑**

CSI 300 0.392 0.295 1.330 0.091 4.332        CSI 500 0.648 0.342 1.894 0.137 4.729        

Qwen3-8b 0.941 0.459 2.051 0.132 7.130 0.475
GPT-4o-mini 0.351 0.372 0.944 0.178 1.977 0.471
RAG (4o-mini) 0.336 0.360 0.932 0.197 1.703 0.559


FinMA 0.348 0.389 0.895 0.214 1.623 0.479
FinGPT 0.443 0.327 1.355 0.103 4.294 0.475
DISC-FinLLM 0.729 0.468 1.559 0.163 4.462 0.474
XuanYuan-6B 0.318 0.373 0.852 0.170 1.868 0.471
Stock-Chain 1.177 1.211 0.971 0.190 6.182 0.546


Tianfeng 0.054 0.542 0.100 0.225 0.242 0.411
Southwest 0.121 0.485 0.249 0.173 0.701 0.492
Sinolink 0.391 0.648 0.604 0.365 1.070 0.438
SOOCHOW 1.625 0.522 3.115 0.132 12.311 0.557
Guolian-Minsheng 2.012 0.647 3.108 0.169 11.880 0.575
Guosen 0.167 0.456 0.366 0.197 0.845 0.460
Huaan 0.170 0.471 0.361 0.333 0.509 0.435
KaiYuan 0.181 0.473 0.383 0.279 0.650 0.552
China-Fortune 0.263 0.537 0.489 0.216 1.218 0.573
China-Post 0.830 0.559 1.485 0.236 3.519 0.440


**FinKario-RAG** 2.633 0.534 4.926 0.172 15.315 0.581



**Table 3: Ablation study on the impact of different knowl-**
**edge sources.** [′] _𝑤_ / [′] **uses other knowledge sources instead of**
**FinKario;** [′] _𝑤_ / _𝑜_ [′] **removes parts of FinKario for ablation.**





**Table 4: Ablation study of varied retrieval approach.**




|Col1|Method|ARR↑ SR↑ MDD↓ ACC↑|
|---|---|---|
|FinKario|Vanilla RAG<br>LightRAG<br>**FinKario-RAG (Ours)**|0.377<br>0.758<br>**0.120**<br>0.413<br>0.821<br>1.313<br>0.140<br>0.495<br>**  2.633 4.926**<br>0.172<br>**0.581**|






|Col1|Knowledge|ARR↑ SR↑ MDD↓ACC↑|
|---|---|---|
|FinKario-RAG<br>w/ Research report<br>0.336 0.932<br>0.197<br>0.559<br>w/ HiDy<br>0.462 1.353<br>0.174<br>0.455<br>w/o Event graph<br>0.386 0.903<br>0.177<br>0.474<br>w/o Attribute graph 2.230 4.691<br>0.181<br>0.433<br>**FinKario (Ours)**<br>**2.633 4.926 0.172 0.581**|FinKario-RAG<br>w/ Research report<br>0.336 0.932<br>0.197<br>0.559<br>w/ HiDy<br>0.462 1.353<br>0.174<br>0.455<br>w/o Event graph<br>0.386 0.903<br>0.177<br>0.474<br>w/o Attribute graph 2.230 4.691<br>0.181<br>0.433<br>**FinKario (Ours)**<br>**2.633 4.926 0.172 0.581**|FinKario-RAG<br>w/ Research report<br>0.336 0.932<br>0.197<br>0.559<br>w/ HiDy<br>0.462 1.353<br>0.174<br>0.455<br>w/o Event graph<br>0.386 0.903<br>0.177<br>0.474<br>w/o Attribute graph 2.230 4.691<br>0.181<br>0.433<br>**FinKario (Ours)**<br>**2.633 4.926 0.172 0.581**|


FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph Conference’17, July 2017, Washington, DC, USA



(a) FinKario-RAG (b) Qwen3-8b


(c) Guolian-Mingsheng (d) Stock-Chain


**Figure 6: Visualization of Model Industry Preferences vs.**
**Baseline Preferences. The baseline reflects the original in-**
**dustry distribution derived from raw research reports.**


**5** **Conclusion**


This work presents **FinKario**, a fully automated dataset constructed
with event-enhanced knowledge grounded in professional institutional templates, ensuring both domain alignment and scalable dynamic updates. By integrating **FinKario-RAG**, a two-stage graphbased RAG mechanism, our approach overcomes the limitations
of single-target retrieval and reduces hallucination risk when handling large, dynamically evolving graphs. Extensive experiments
demonstrate that FinKario-RAG significantly outperforms both
vanilla LLMs and state-of-the-art FinLLMs in stock trend forecasting. To the best of our knowledge, this is the first benchmark against
real-world institutional strategies, providing a more grounded and
practical performance comparison. Looking forward, FinKario can
be extended to incorporate multi-modal financial inputs, such as
tables, charts, and time-series data from research reports, to further
enrich its retrieval context and enhance predictive robustness.


**References**


[1] Titilope Tosin Adewale, Titilayo Deborah Olorunyomi, and Theodore Narku
Odonkor. 2023. Big data-driven financial analysis: A new paradigm for strategic
insights and decision-making. _Journal of Financial Innovation and Analytics_ 1, 1
(2023), 1–15.

[2] Dogu Araci. 2019. Finbert: Financial sentiment analysis with pre-trained language
models. _arXiv preprint arXiv:1908.10063_ (2019).

[3] Hanzhu Chen, Xu Shen, Qitan Lv, Jie Wang, Xiaoqi Ni, and Jieping Ye. 2024.
SAC-KG: Exploiting Large Language Models as Skilled Automatic Constructors
for Domain Knowledge Graph. In _Proceedings of the 62nd Annual Meeting of_
_the Association for Computational Linguistics (Volume 1: Long Papers)_, Lun-Wei
Ku, Andre Martins, and Vivek Srikumar (Eds.). Association for Computational
[Linguistics, 4345–4360. doi:10.18653/v1/2024.acl-long.238](https://doi.org/10.18653/v1/2024.acl-long.238)

[4] Wei Chen, Qiushi Wang, Zefei Long, Xianyin Zhang, Zhongtian Lu, Bingxuan Li,
Siyuan Wang, Jiarong Xu, Xiang Bai, Xuanjing Huang, et al. 2023. Disc-finllm: A
chinese financial large language model based on multiple experts fine-tuning.
_arXiv preprint arXiv:2310.15205_ (2023).

[5] Yuemin Chen, Feifan Wu, Jingwei Wang, Hao Qian, Ziqi Liu, Zhiqiang Zhang, Jun
Zhou, and Meng Wang. 2024. Knowledge-augmented Financial Market Analysis
and Report Generation. In _Proceedings of the 2024 Conference on Empirical Methods_
_in Natural Language Processing: Industry Track_ . 1207–1217.

[6] Dawei Cheng, Fangzhou Yang, Xiaoyang Wang, Ying Zhang, and Liqing Zhang.
2020. Knowledge graph-based event embedding framework for financial quantitative investments. In _Proceedings of the 43rd International ACM SIGIR Conference_
_on Research and Development in Information Retrieval_ . 2221–2230.




[7] Andrea Colombo, Teodoro Baldazzi, Luigi Bellomarini, Emanuel Sallinger, and
Stefano Ceri. 2025. Template-based Explainable Inference over High-Stakes
Financial Knowledge Graphs. _computational complexity_ 7, 24 (2025), 47.

[8] E Philip Davis. 1996. The role of institutional investors in the evolution of
financial structure and behaviour. _The Future of the Financial System_ 33 (1996),
49–99.

[9] Linyi Ding, Sizhe Zhou, Jinfeng Xiao, and Jiawei Han. 2024. Automated construction of theme-specific knowledge graphs. _arXiv preprint arXiv:2404.19146_
(2024).

[10] Ziliang Gan, Yu Lu, Dong Zhang, Haohan Li, Che Liu, Jian Liu, Ji Liu, Haipang
Wu, Chaoyou Fu, Zenglin Xu, Rongjunchen Zhang, and Yong Dai. 2024. MMEFinance: A Multimodal Finance Benchmark for Expert-level Understanding and
[Reasoning. arXiv:2411.03314 [cs.CV] https://arxiv.org/abs/2411.03314](https://arxiv.org/abs/2411.03314)

[11] Denis J Hilton. 2001. The psychology of financial decision-making: Applications
to trading, dealing, and investment analysis. _The Journal of Psychology and_
_Financial Markets_ 2, 1 (2001), 37–53.

[12] Aaron Hurst, Adam Lerer, Adam P Goucher, Adam Perelman, Aditya Ramesh,
Aidan Clark, AJ Ostrow, Akila Welihinda, Alan Hayes, Alec Radford, et al. 2024.
Gpt-4o system card. _arXiv preprint arXiv:2410.21276_ (2024).

[13] K Kapellas and G Siougle. 2017. Financial reporting practices and investment
decisions: A review of the literature. _Industrial Engineering & Management_ 6, 04
(2017), 1–9.

[14] Natthawut Kertkeidkachorn, Rungsiman Nararatwong, Ziwei Xu, and Ryutaro
Ichise. 2023. Finkg: A core financial knowledge graph for financial analysis. In
_2023 IEEE 17th International Conference on Semantic Computing (ICSC)_ . IEEE,
90–93.

[15] Xiang Li, Zhenyu Li, Chen Shi, Yong Xu, Qing Du, Mingkui Tan, Jun Huang,
and Wei Lin. 2024. Alphafin: Benchmarking financial analysis with retrievalaugmented stock-chain framework. _arXiv preprint arXiv:2403.12582_ (2024).

[16] Xiaohui Victor Li and Francesco Sanna Passino. 2024. Findkg: Dynamic knowledge graphs with large language models for detecting global trends in financial
markets. In _Proceedings of the 5th ACM International Conference on AI in Finance_ .
573–581.

[17] Zhaowei Liu, Xin Guo, Fangqi Lou, Lingfeng Zeng, Jinyi Niu, Zixuan Wang, Jiajie
Xu, Weige Cai, Ziwei Yang, Xueqian Zhao, et al. 2025. Fin-R1: A Large Language
Model for Financial Reasoning through Reinforcement Learning. _arXiv preprint_
_arXiv:2503.16252_ (2025).

[18] Zhenghao Liu, Zhijian Zhang, and Xi Zeng. 2024. Risk identification and management through knowledge Association: A financial event evolution knowledge
graph approach. _Expert Systems with Applications_ 252 (2024), 123999.

[19] A Craig MacKinlay. 1997. Event studies in economics and finance. _Journal of_
_economic literature_ 35, 1 (1997), 13–39.

[20] Bhaskarjit Sarmah, Dhagash Mehta, Benika Hall, Rohan Rao, Sunil Patel, and
Stefano Pasquali. 2024. Hybridrag: Integrating knowledge graphs and vector
retrieval augmented generation for efficient information extraction. In _Proceedings_
_of the 5th ACM International Conference on AI in Finance_ . 608–616.

[21] Michael C Schlachter. 2013. How You Compare to the Big Funds: Advantages and
Disadvantages of Individual Investors. In _INVEST LIKE AN INSTITUTION: PRO-_
_FESSIONAL STRATEGIES FOR FUNDING A SUCCESSFUL RETIREMENT_ . Springer,
1–14.

[22] Kuldeep Singh, Simerjot Kaur, and Charese Smiley. 2024. Finqapt: Empowering
financial decisions with end-to-end llm-driven question answering pipeline. In
_Proceedings of the 5th ACM International Conference on AI in Finance_ . 266–273.

[23] Zheng Su, Mukai Hao, Qiang Zhang, Bo Chai, and Ting Zhao. 2020. Automatic
knowledge graph construction based on relational data of power terminal equipment. In _2020 5th International Conference on Computer and Communication_
_Systems (ICCCS)_ . IEEE, 761–765.

[24] ShaoBo Sun, Xiaoming Pan, Shuang Qi, and Jun Gao. 2025. Knowledge Enhanced
Prompt Learning Framework for Financial News Recommendation. _Pattern_
_Recognition_ (2025), 111461.

[25] Rex Thompson. 1995. Empirical methods of event studies in corporate finance.
_Handbooks in Operations Research and Management Science_ 9 (1995), 963–992.

[26] Bin Wang, Chao Xu, Xiaomeng Zhao, Linke Ouyang, Fan Wu, Zhiyuan Zhao,
Rui Xu, Kaiwen Liu, Yuan Qu, Fukai Shang, et al. 2024. Mineru: An open-source
solution for precise document content extraction. _arXiv preprint arXiv:2409.18839_
(2024).

[27] Mengyu Wang, Tiejun Ma, and Shay B Cohen. 2025. Pre-training Time Series
Models with Stock Data Customization. _arXiv preprint arXiv:2506.16746_ (2025).

[28] Wenguang Wang, Yonglin Xu, Chunhui Du, Yunwen Chen, Yijie Wang, and
Hui Wen. 2021. Data set and evaluation of automated construction of financial
knowledge graph. _Data Intelligence_ 3, 3 (2021), 418–443.

[29] Shijie Wu, Ozan Irsoy, Steven Lu, Vadim Dabravolski, Mark Dredze, Sebastian
Gehrmann, Prabhanjan Kambadur, David Rosenberg, and Gideon Mann. 2023.
[BloombergGPT: A Large Language Model for Finance. arXiv:2303.17564 [cs.LG]](https://arxiv.org/abs/2303.17564)
[https://arxiv.org/abs/2303.17564](https://arxiv.org/abs/2303.17564)

[30] Bolun Xia, Vipula Rawte, Aparna Gupta, and Mohammed Zaki. 2024. FETILDA:
evaluation framework for effective representations of long financial documents.
_ACM Transactions on Knowledge Discovery from Data_ 18, 7 (2024), 1–27.


Conference’17, July 2017, Washington, DC, USA Xiang Li et al.




[31] Qianqian Xie, Weiguang Han, Xiao Zhang, Yanzhao Lai, Min Peng, Alejandro
Lopez-Lira, and Jimin Huang. 2023. Pixiu: A large language model, instruction
data and evaluation benchmark for finance. _arXiv preprint arXiv:2306.05443_
(2023).

[32] Yuanjian Xu, Jianing Hao, Kunsheng Tang, Jingnan Chen, Anxian Liu, Peng Liu,
and Guang Zhang. 2025. FinRipple: Aligning Large Language Models with Financial Market for Event Ripple Effect Awareness. _arXiv preprint arXiv:2505.23826_
(2025).

[33] An Yang, Anfeng Li, Baosong Yang, Beichen Zhang, Binyuan Hui, Bo Zheng,
Bowen Yu, Chang Gao, Chengen Huang, Chenxu Lv, et al. 2025. Qwen3 technical
report. _arXiv preprint arXiv:2505.09388_ (2025).

[34] Hongyang Yang, Xiao-Yang Liu, and Christina Dan Wang. 2023. FinGPT: Open[Source Financial Large Language Models. arXiv:2306.06031 [q-fin.ST] https:](https://arxiv.org/abs/2306.06031)
[//arxiv.org/abs/2306.06031](https://arxiv.org/abs/2306.06031)

[35] Yangyang Yu, Zhiyuan Yao, Haohang Li, Zhiyang Deng, Yupeng Cao, Zhi Chen,
Jordan W. Suchow, Rong Liu, Zhenyu Cui, Zhaozhuo Xu, Denghui Zhang, Koduvayur Subbalakshmi, Guojun Xiong, Yueru He, Jimin Huang, Dong Li, and
Qianqian Xie. 2024. FinCon: A Synthesized LLM Multi-Agent System with Conceptual Verbal Reinforcement for Enhanced Financial Decision Making. _arXiv_
_preprint arXiv:2407.06567_ (2024).

[36] Bowen Zhang and Harold Soh. 2024. Extract, define, canonicalize: An llm-based
framework for knowledge graph construction. _arXiv preprint arXiv:2404.03868_
(2024).

[37] Wentao Zhang, Lingxuan Zhao, Haochong Xia, Shuo Sun, Jiaze Sun, Molei Qin,
Xinyi Li, Yuqing Zhao, Yilei Zhao, Xinyu Cai, et al. 2024. A multimodal foundation agent for financial trading: Tool-augmented, diversified, and generalist. In
_Proceedings of the 30th acm sigkdd conference on knowledge discovery and data_
_mining_ . 4314–4325.

[38] Tianyu Zhou, Pinqiao Wang, Yilin Wu, and Hongyang Yang. 2024. Finrobot:
Ai agent for equity research and valuation with large language models. _arXiv_
_preprint arXiv:2411.08804_ (2024).

[39] Xinyi Zhu, Liping Wang, Hao Xin, Xiaohan Wang, Zhifeng Jia, Jiyao Wang, Chunming Ma, and Yuxiang Zengt. 2023. T-FinKB: A Platform of Temporal Financial
Knowledge Base Construction. In _2023 IEEE 39th International Conference on Data_
_Engineering (ICDE)_ . IEEE, 3671–3674.


**A** **Prompts in FinKario**

**A.1** **The Prompt for Acquiring Schema of**
**Attribute Graph**


We leverage standardized equity research templates from authoritative sources (e.g., the CFA Institute and J.P. Morgan) as reference guides. We design a prompt that guides the model to identify core company attributes for schema construction, including
name, ticker, rating, market capitalization, and more. Specifically,
the attribute schema comprises 11 relation types: Stock Ticker,
Primary Exchange, Primary Industry, Investment Rating, Current
Stock Price, Market Capitalization, Target Price, Major Shareholders, Risk Assessment, Key Products, Research Institution. Figure 7
illustrates an example of the automatically acquired schema for our
Attribute graph.


**A.2** **The Prompt for Attribute Graph**
**Construction**


After acquiring the schema of the Attribute Graph, this structure
serves as the foundation for attribute-level knowledge population
from financial research reports. Figure 8 provides an example of
the designed prompt used to guide the model in extracting these
attributes during the knowledge population process.


**A.3** **The Prompt for Acquiring Schema of Event**
**Graph**


We automatically construct the top-down event-driven schema by
prompting LLMs to extract high-level driven categories from the
Wisconsin handbook and further match low-level event ontologies



from FIBO to support interpretable event graph construction. Figure 9 illustrates the resulting tree-structured schema. Each event
category corresponds to a high-level driver and is associated with
its fine-grained instances or relations. Below is the list of categories
and their typical subtypes:


  - **Supply** : is provided by, Capacity Adjustment, Market Action,
Holds

  - **Demand** : Sales, Consumption, Performance, Is needed by

  - **Revenue** : Earning, Profit, Income-oriented classifier, Is issued by, Has increased / decreased

  - **Efficiency Cost** : Lower the cost, Automation

  - **Strategic Action** : Merger / Acquisition, Overseas expansion,
Spin-off

  - **Technology Innovation** : Is applicable in, New product, Has
innovated, Iteration

  - **Policy Regulation** : Regulatory action, Governs, License

  - **Macro** : Interest rate, GDP, Disaster


**A.4** **The Prompt for Event Graph Construction**


After establishing the event schema, we designed a tailored prompt
to guide large language models in extracting structured event-level
information from equity research reports. As illustrated in Figure 10,
the prompt instructs the model to (1) identify the subject and object
of the event, (2) extract relevant entities such as company names,
products, and indicators, (3) annotate the timeframe, and (4) determine a driven category from options like “Supply”, “Demand”, or
“Strategic Action”.
To ensure relevance and accuracy, the prompt restricts extraction
to events directly tied to company activities. The resulting JSON
output includes not only the core event tuple but also a reasoning
statement that explains the event linkage. The figure presents both
an illustrative example and a real-case output to demonstrate the
clarity and consistency achieved through our prompt design.


**B** **The Case Study of Investment Query**
**Response**


This subsection presents a case study comparing how various models—including FinLLMs such as FinGPT, XuanYuan-6B, Stock-Chain,
and FinKario-RAG, as well as an advanced vanilla LLM (GPT-4omini), respond to a user query about investment analysis for Haier
Biomedical (Haier Bio). The query asks the model to analyze the
stock’s investment potential and predict its future price trend.
As shown in Figure 11, FinGPT, XuanYuan-6B, and GPT-4o-mini
consistently emphasize the limitations of LLMs in delivering definitive investment predictions. These models cite the inherent uncertainty of market dynamics and the lack of access to real-time data as
major barriers. Their responses generally avoid direct suggestions,
instead encouraging users to consider macroeconomic conditions,
company fundamentals, and to consult financial professionals. In
contrast, Stock-Chain attempts a more analytical response by summarizing company fundamentals and macro-level trends. However,
its output includes factual inaccuracies such as misidentifying the
stock code, and it fails to synthesize comparative insights across
the industry, falling short of the user’s request for a cross-company


FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph Conference’17, July 2017, Washington, DC, USA







**Figure 7: Prompt for acquiring schema of Attribute graph.**



investment evaluation. Moreover, it does not offer actionable investment guidance, only suggesting that decisions require consideration
of multiple external factors.
FinKario-RAG addresses these shortcomings by accurately grounding its analysis in correct entity identifiers, comparing the target
stock with other industry players, and offering nuanced conclusions.
This demonstrates the effectiveness of our financial knowledge
graph construction and retrieval approach, which goes beyond
traditional single-document retrieval methods to support more
context-aware and investor-aligned responses.


**C** **The Supplementary Experiments of**
**Institutional Strategy**


In the main manuscript, we compared our method against institutional agencies that published at least 300 equity research reports.
To enable a more comprehensive evaluation of institutional strategy
effectiveness, we additionally included agencies that have rated
at least 100 reports in this supplementary analysis. The cumulative performance of these strategies is illustrated in the NAV curve
shown in Figure 12, while detailed performance metrics are summarized in Table 5.
For example, Guolian-Minsheng, SOOCHOW, and Caixin demonstrate strong annualized returns, with Guolian-Minsheng reaching
2.012, SOOCHOW at 1.625, and Caixin also at 1.625. Compared to
low-return agencies such as Tianfeng and Cinda, whose annualized
returns are below 0.06, these top performers yield more than 25
times higher returns. However, high returns do not always equate



to stability. Caixin, despite having the highest Sharpe Ratio of 3.816,
shows relatively low accuracy at 0.455, indicating that effective
market timing can sometimes matter more than raw predictive accuracy. In contrast, Guolian-Minsheng achieves both a high return
and an accuracy of 0.575, the best among all institutions. Zhongtai
and Ping-An exhibit the lowest volatility values at 0.312 and 0.324,
respectively, which are about 40% lower than the average across
institutions. Nonetheless, their returns remain moderate, indicating
a trade-off between risk and reward. Meanwhile, Shanxi and Dongxing record negative returns, highlighting potential weaknesses in
their investment strategies during weekly backtesting. Some institutions, such as China-Post and Pacific, deliver reasonably high
returns above 0.8 and 1.5, respectively. However, their performance
metrics such as drawdown and accuracy remain suboptimal, indicating inconsistent prediction quality. Agencies like Guosen and
KaiYuan exhibit more balanced profiles with moderate returns and
volatility, yet lack standout performance in any single dimension.
Overall, these results illustrate the fragmented quality and strategic effectiveness among institutional players. Against this backdrop,
FinKario-RAG delivers the strongest performance across all major return-oriented metrics, including the highest annualized return, Sharpe Ratio, and accuracy, while keeping risk measures such
as maximum drawdown and volatility within acceptable bounds,
thereby reinforcing the advantage of our structured retrieval and
knowledge-grounded approach.


Conference’17, July 2017, Washington, DC, USA Xiang Li et al.







**Figure 8: Prompt for Attribute graph construction.**







**Figure 9: Prompt for acquiring schema of Event graph.**


FinKario: Event-Enhanced Automated Construction of Financial Knowledge Graph Conference’17, July 2017, Washington, DC, USA







**Figure 10: Prompt for Event graph construction.**


**Table 5: Performance of institutional agencies that published at least 100 equity research reports.**


**Agency** **ARR↑** **VOL↓** **SR↑** **MDD↓** **CR↑** **ACC↑**

Tianfeng 0.054 0.542 0.100 0.225 0.242 0.411
Southwest 0.121 0.485 0.249 0.173 0.701 0.492
Sinolink 0.391 0.648 0.604 0.365 1.070 0.438
SOOCHOW 1.625 0.522 3.115 0.132 12.311 0.557
Guolian-Minsheng 2.012 0.647 3.108 0.169 11.880 0.575
Guosen 0.167 0.456 0.366 0.197 0.845 0.460
Huaan 0.170 0.471 0.361 0.333 0.509 0.435
KaiYuan 0.181 0.473 0.383 0.279 0.650 0.552
China-Fortune 0.263 0.537 0.489 0.216 1.218 0.573
China-Post 0.830 0.559 1.485 0.236 3.519 0.440
Pacific 1.557 0.582 2.674 0.170 9.138 0.458
China-Galaxy 0.533 0.452 1.179 0.289 1.847 0.482
Huafu 0.465 0.381 1.222 0.162 2.881 0.409
Zhongtai 0.432 0.312 1.388 0.068 6.358 0.328
Cinda 0.005 0.413 0.011 0.117 0.041 0.496
Shanxi -0.198 0.817 -0.243 0.532 -0.373 0.440
Guohai 0.340 0.387 0.879 0.136 2.506 0.402
Huajin 0.813 0.569 1.429 0.192 4.233 0.358
Ping-An 0.403 0.324 1.243 0.196 2.056 0.538
Guoyuan 1.488 0.623 2.391 0.220 6.768 0.491
Huayuan 0.553 0.421 1.314 0.168 3.292 0.409
Haitong-International 0.852 0.571 1.490 0.256 3.322 0.395
Zhongyuan 0.964 0.561 1.718 0.270 3.565 0.483
Caixin 1.625 0.426 3.816 0.126 12.897 0.455
AVIC -0.091 0.589 -0.154 0.329 -0.276 0.437
Dongxing -0.087 0.391 -0.223 0.181 -0.481 0.415


**FinKario-RAG** 2.633 0.534 4.926 0.172 15.315 0.581


Conference’17, July 2017, Washington, DC, USA Xiang Li et al.









**XuanYuan-6B**


**GPT-4o-mini**







**FinKario-RAG**



**Figure 11: Evaluation of investment suggestions from FinGPT, XuanYuan-6B, GPT-4o-mini, Stock-Chain, and FinKario**


**Figure 12: Accumulated returns (AR) of each institutional strategy on the financial-report dataset from August 28, 2024 to**
**March 7, 2025. The figure shows the net asset value (NAV) curves over the weekly backtesting period.**


