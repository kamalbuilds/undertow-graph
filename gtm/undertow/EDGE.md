# undertow: tools that put us ahead

swept: 2026-10-18

What shipped recently (SDKs, protocol features, precompiles, papers, APIs, models) that teams on the
default stack are not using. Each entry ends adopted, spiked, rejected with a reason, or candidate.

### Morpho Vault V2 adapters (vault-v2 repo, adapter-based allocation)
https://github.com/morpho-org/vault-v2/releases
released: 2026-10-12
edge: V2 vaults allocate through MetaMorphoAdapter (V2 to V1 vault), MorphoVaultV2Adapter (V2 to V2) and MorphoMarketV1Adapter (V2 to market). Undertow ingests all three as ALLOCATES edges, so vault-of-vault exposure is traversed instead of read off one vault's market list; 537 V2 vaults sit in the live graph.
competitors: gh search code "MorphoVaultV2Adapter" found 9 repos (e.g. IPOR-Labs/ipor-fusion.py, Haythem666/Defi-Risk-Hackaton); none inspected as a multi-hop shock tool, and none of the 9 is a curator-action drafter.
status: adopted backend/ingest.py

### falkordb Python client 1.8.0
https://pypi.org/project/falkordb/
released: 2026-10-14
edge: Current client for the graph that holds Vault, Market, Asset, Scenario and Alert nodes; the same client talks to embedded and server FalkorDB, so the demo and the deploy run identical queries.
competitors: not applicable, shared dependency of every FalkorDB entrant; gh search code "from redislite.falkordb_client import FalkorDB" found 23 repos using the same embedded path.
status: adopted pyproject.toml

### falkordblite 0.10.0 (embedded FalkorDB, no server process)
https://pypi.org/project/falkordblite/
released: 2026-05-02
edge: Graph runs inside the API process on a file (data/undertow.db), so the live deploy needs no separate database service and a shock query is a local call.
competitors: gh search code "falkordblite" found 16 repos, mostly code-graph and memory tools; none found for DeFi exposure (gh search repos "falkordb defi vault depeg" created >=2026-10-10 returned 0 in docs/WIN-CONDITIONS.md).
status: adopted backend/db.py

### FalkorDB 6.0.0 (Rust engine)
https://github.com/FalkorDB/FalkorDB/releases/tag/v6.0.0
released: 2026-09-29
edge: New query engine and RediSearch 8.6.1 for full-text and vector indexes; same GRAPH.* commands and Cypher.
competitors: none found; the release notes say 6.0 has the same procedures as 4.20.7 and no macOS module builds.
status: rejected same procedures as 4.20.7 and no macOS module build, so no change to shock traversal; revisit when A* and CCH are ported

### FalkorDB 4.22.0 (k-shortest and all-shortest paths, CCH index)
https://github.com/FalkorDB/FalkorDB/releases/tag/v4.22.0
released: 2026-09-30
edge: All-shortest-paths and k-shortest-paths procedures would enumerate every contagion route to a vault, ranked by loss.
competitors: none found; 23 FalkorDB releases since 2026-04-21 (gh api repos/FalkorDB/FalkorDB/releases), no DeFi project cites them.
status: rejected not in the engine falkordblite 0.10.0 ships: CALL dbms.procedures() there lists algo.SPpaths and algo.SSpaths only, so Undertow keeps variable-length MATCH paths

### @morpho-org/simulation-sdk 4.0.3
https://github.com/morpho-org/sdks
released: 2026-06-02
edge: Simulates Morpho operations against a state snapshot, which can check that a drafted reallocation moves the curator's vault out of the shocked market before the draft is shown.
competitors: none found among the repos read for this sweep; published by the Morpho org itself.
status: candidate

### @morpho-org/blue-sdk 8.0.0
https://github.com/morpho-org/sdks/tree/main/packages/blue-sdk
released: 2026-10-12
edge: Typed Morpho position and vault accrual math to replace the API's USD snapshot with share-exact exposure on the same block as the RPC reads.
competitors: none found beyond Morpho's own apps.
status: candidate

### DeXposure-FM: graph foundation model for DeFi credit exposure (arXiv 2602.03981)
https://arxiv.org/abs/2602.03981
released: 2026-02-03
edge: Trained on 43.7M exposure entries across 4,300+ protocols; weights on Hugging Face (EVIEHub/DeXposure-FM) can supply priors for cross-protocol edges (Aave, Euler, Pendle) that the Morpho API does not expose.
competitors: none found; gh search code "dthinkr DeXposure" returned 0 hits (control: "falkordblite" returned 16 in the same lane).
status: candidate

### DeXposure dataset and benchmarks (arXiv 2511.22314)
https://arxiv.org/abs/2511.22314
released: 2025-11-27
edge: Public inter-protocol exposure dataset (github.com/dthinkr/DeXposure) that seeds wrapper and protocol-to-protocol edges beyond Morpho.
competitors: none found, same query as above.
status: candidate

### Measuring DeFi Risk (arXiv 2609.07902)
https://arxiv.org/abs/2609.07902
released: 2026-09-07
edge: Aggregate-only fragility measure from total deposits and borrowings.
competitors: none found; arXiv all:"DeFi" AND all:"systemic risk" returned 11 papers, this is the newest.
status: rejected needs only aggregate deposits and borrowings, so it cannot name a vault or a curator and cannot draft a cap cut

### Sigma Labs DeFi Integration Graph and Yield Tree Decomposition (Morpho RFC)
https://forum.morpho.org/t/rfc-a-user-centric-defi-collateral-transparency-framework-phase-1/2301
released: 2026-06-08
edge: Recursive collateral decomposition (DIG and YTD) proposed as a public good for Morpho; its wrapper decompositions could replace our ERC4626 asset() derivation if published as data.
competitors: Sigma Labs itself, grant-stage in the thread; replies there ask for fork-based depeg propagation, which is the shock Undertow runs.
status: candidate

### Chaos AI knowledge graph of USR-exposed vaults
https://x.com/omeragoldberg/status/2036478623952023920
released: 2026-03-24
edge: Chaos Labs shows the same graph idea on two Gauntlet vaults after the fact; Undertow runs it before the incident on every vault and ends in a curator draft.
competitors: Chaos Labs (closed tooling, post-incident, two vaults shown).
status: rejected closed tooling and a single post-incident case, nothing to adopt

### graphrag-sdk 1.4.0
https://pypi.org/project/graphrag-sdk/
released: 2026-08-10
edge: FalkorDB's retrieval SDK for LLM question answering over a graph.
competitors: FalkorDB hackathon entrants build on it; not a DeFi exposure tool.
status: rejected shock loss is a deterministic Cypher traversal over numbers, not retrieval, so an LLM layer would add error to a computed result

## Sweep log

- gh "MorphoVaultV2Adapter" -> 9 hits, repos reading V2 adapter types, none a multi-hop shock tool among those inspected
- gh "falkordblite" -> 16 hits, code-graph and memory tools, no DeFi
- gh "from redislite.falkordb_client import FalkorDB" -> 23 hits, same embedded pattern
- gh "dthinkr DeXposure" -> 0 hits, control "falkordblite" returned 16 in the same lane
- gh "falkordb defi vault depeg stablecoin collateral (repos created >=2026-10-10)" -> 0 hits, recorded in docs/WIN-CONDITIONS.md
- npm "@morpho-org/simulation-sdk" -> 1 package, 4.0.3 published 2026-06-02
- npm "@morpho-org/blue-sdk" -> 1 package, 8.0.0 published 2026-10-12
- pypi "falkordb" -> 1 package, 1.8.0 uploaded 2026-10-14
- pypi "falkordblite" -> 1 package, 0.10.0 uploaded 2026-05-02
- pypi "graphrag-sdk" -> 1 package, 1.4.0 uploaded 2026-08-10
- arxiv "DeFi systemic risk" -> 11 hits, newest 2609.07902 and 2603.23480
- arxiv "decentralized finance inter-protocol credit exposure" -> 2 hits, DeXposure and DeXposure-FM
- arxiv "Morpho vault" -> 0 hits, control "DeFi systemic risk" returned 11
- hn "Stream Finance xUSD" -> 2 hits, both unrelated hiring posts
- x "morpho vault exposed USR Resolv since:2026-03-22" -> 17 hits, curator statements and the Chaos AI graph post
- x "vaults exposure wstUSR PT-USR RLP curators" -> 14 hits, D2 Finance, Octave and KazumaxCrypto exposure lists
