[chatgpt] tool:web.run

Sources:
  https://scite.ai/
  https://scite.ai/features
  https://scite.ai/api
  https://scite.ai/getting-started
  https://scite.ai/integrations
  https://scite.ai/extension-install
  https://github.com/swarnnim/trace
  https://github.com/howdycarter/graph-hacks-falkordb-2026/blob/main/README.md
  https://github.com/science-as-data/openalex/blob/main/api/api-reference.md
  https://github.com/xaviercallens/xopenalex-docs/blob/main/api-entities/works/filter-works.md
  https://www.wemakedevs.org/hackathons/falkordb/rules
  https://www.wemakedevs.org/hackathons/falkordb
  https://www.wemakedevs.org/hackathons/falkordb/schedule
  https://www.wemakedevs.org/hackathons/falkordb/resources
  https://info.arkm.com/announcements/announcing-the-arkham-tracer
  https://info.arkm.com/arkham-blockchain-explorer
  https://info.arkm.com/research/blockchain-analytics-all-the-use-cases-for-on-chain-data
  https://info.arkm.com/announcements/arkham-x-pfl
  https://info.arkm.com/announcements/announcing-arkham-x-coingecko-x-geckoterminal
  https://info.arkm.com/announcements/announcing-arkham-x-sui
  https://metasleuth.io/blockchain-investigation
  https://doi.org/doi%3A10.1038/nature04533
  https://openalex.org/W4200394820
  https://openalex.org/W3167848497
  https://www.falkordb.com/blog/memory-meets-motion-the-falkordb-standouts/
  https://www.falkordb.com/blog/how-builders-at-hack-for-humanity-used-falkordb-to-solve-real-community-problems/?trk=public_post_comment-text
  https://help.openalex.org/how-to/api-recipes/
  https://help.openalex.org/how-to/searching/
  https://help.openalex.org/api/
  https://help.openalex.org/data/works/
  https://help.openalex.org/api/sorting/
  https://skmtc.dev/openalex/apis/openalex-api/docs/works/%3Aid/get
  https://codex.arkm.com/
  https://codex.arkm.com/the-intelligence-platform
  https://arxiv.org/abs/2403.13339
  https://library.smu.edu.sg/topics-insights/openalex-promising-alternative-microsoft-academic-graph
  https://landing.breadcrumbs.app/law-enforcement
[gpt-5-6 - 19.5s - https://chatgpt.com/c/6ad4700f-51d4-83ec-a921-e38499df06c7]
## Verdict: B wins, but only after a substantial cut.

**A is a polished feature in an existing category. B has a chance to expose a gap between citation analysis and actual scientific dependency.** Neither wins by putting familiar algorithms behind an LLM.

The hackathon rules explicitly require FalkorDB to be central enough that removing it breaks the product. <Cite refs={["turn796243search6","turn796243search7"]}/>

## A. Follow the Money

<badge color="danger">Kill as pitched</badge>

**Strongest kill shot:** Arkham already offers multistage fund-flow graphs, automated pathfinding, entity labels, and cross-chain tracing. MetaSleuth offers cross-chain investigations, pathfinding, and over 400 million address labels. <Cite refs={["turn796243search8","turn796243search14","turn796243search10"]}/>

- **Prior art and usage:** [Arkham Tracer](https://info.arkm.com/announcements/announcing-the-arkham-tracer) shipped in September 2023. [MetaSleuth](https://metasleuth.io/blockchain-investigation) advertises 400M+ address labels. These are substantial product precedents, although those figures measure coverage, not active users.
- **Is it generic?** Yes. Ethereum ingestion → graph traversal → path ranking → AI-generated compliance letter is an integration demo. Shortest path, weakly connected components, and max flow are implementation choices, not a novel product insight.
- **Demo risk:** High. Exchange deposit attribution is uncertain; mixers, bridges, omnibus wallets, and partial withdrawals make “how much can still reach an exchange?” easy to misrepresent. Max flow on a transaction graph does not establish recoverable funds. A convincing graph can still produce a false freeze request.
- **One change to make it novel:** Replace tracing with **provable recovery windows**. Model each transfer's amount, timestamp, asset, and confidence; account for commingling and known exchange custody; output a conservative lower bound on funds attributable to the exploit, with an auditable path for every claim. Demonstrate against one documented exploit and independently verified destination addresses.

Even then, the differentiator is the recovery accounting, not the graph visualization.

## B. Retraction Contagion

<badge color="success">Winner, with conditions</badge>

**Strongest kill shot:** Scite already classifies citation contexts as supporting, contrasting, or mentioning, at massive scale. Calling the same classification “dependency” and traversing it across a graph risks being a thin wrapper. <Cite refs={["turn796243search1","turn796243search2"]}/>

- **Prior art and usage:**
  - [Scite](https://scite.ai/features): 1.7B+ Smart Citations, 323M+ articles indexed, 44+ publisher partners, and 2M users. These are the company's advertised figures. <Cite refs={["turn796243search1","turn796243search4"]}/>
  - [Research on retracted-paper citations](https://openalex.org/W4200394820): a study covering 7,813 retracted papers and 169,434 citations found that only 722 of 13,252 post-retraction citation contexts (5.4%) acknowledged the retraction. <Cite refs={["turn796243search15"]}/>
  - [OpenAlex API](https://help.openalex.org/how-to/api-recipes/): exposes citation relationships and supports retrieving citing works, so the graph ingestion itself is not novel. <Cite refs={["turn590648search0","turn590648search2"]}/>
  - [Lesné et al., Nature 2006](https://doi.org/10.1038/nature04533): retracted in June 2024, with 2,539 citations currently shown by Nature, not the proposed 2,769. <Cite refs={["turn796243search12"]}/>

- **Is it generic?** The first-hop classifier is. The potentially novel part is distinguishing *citation* from *epistemic dependence*: does the downstream paper actually rely on the retracted result for a central conclusion? Then tracing that dependency through subsequent papers and clinical-trial rationales.
- **Demo risk:** Very high if you promise to process all 2,769 citing papers and multiple hops. Full text access, paywalls, citation-context extraction, and false-positive dependency labels can sink the demo. OpenAlex metadata alone cannot establish scientific dependence. A retracted result also does not automatically invalidate every paper citing it.
- **One change to make it novel:** Build a **claim-level dependency graph**, not a paper-level contamination graph. For one retracted paper, extract a specific claim, identify downstream claims that explicitly depend on it, attach quoted evidence and confidence to every edge, and let a reviewer challenge or approve each link. Show one verified multi-hop chain and one citation that mentions the paper without relying on it.

## Final decision

**Pick B: Retraction Contagion.**

A competes directly with mature blockchain investigation platforms and their established attribution data. B has equally serious prior art, but a narrower, evidence-backed dependency graph could be a distinct research-integrity tool.

The winning demo is not “look how many papers are contaminated.” It's: **“Here is the exact scientific claim that may no longer be supported, the downstream conclusions that rely on it, and the evidence for each connection.”**

FalkorDB must make multi-hop dependency queries, provenance, and reviewer corrections essential to the result. If removing the graph leaves the same ranked list and generated notices, both entries fail the rules. <Cite refs={["turn796243search6"]}/>
