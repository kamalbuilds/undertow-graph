# Undertow

**When one DeFi asset breaks, Undertow shows every vault the loss reaches, the path it travels, and what the curator should move first.**

**Live:** [undertow-graph.fly.dev](https://undertow-graph.fly.dev)  ·  **Demo film (2:33):** [video/undertow-film.mp4](video/undertow-film.mp4)  ·  **Blog:** [docs/BLOG.md](docs/BLOG.md)

**In plain words.** Savers deposit into lending pools ("vaults") that lend their money to borrowers. Borrowers lock up a guarantee, usually a digital dollar, worth more than the loan. That guarantee is rarely the plain digital dollar: it is repackaged into a savings version, then a fixed-term version, each with a new name. When the underlying dollar breaks, warning systems search for its name, miss every repackaged layer, and the hole lands in savers' deposits unflagged. Undertow walks every layer as a graph and shows exactly which vaults take the loss.

A stablecoin depegs. A risk alert keyed on its symbol flags the markets that list it as collateral. The loss does not stop there: it flows through wrappers (USDe to sUSDe to a Pendle PT on sUSDe), through vaults that allocate into other vaults, and through vault share tokens posted as collateral in markets that never mention the original asset. Undertow models Morpho mainnet as a FalkorDB graph and follows all of it.

Graph Hacks: Context for AI Agents (WeMakeDevs x FalkorDB). **Tracks entered: Track 01, Agents That Act on Connected Data; Track 02, Agent Memory and Coordination.**

## What the graph finds that a symbol alert misses

30% price shock, live Morpho mainnet state (ingested 2026-10-18 from `blue-api.morpho.org/graphql`):

| Shocked asset | Symbol-match alert | Undertow, through the graph | Deepest path |
|---|---|---|---|
| USDe | 2 vaults, $10.62M | **10 vaults, $31.14M** | 3 hops |
| USDS | 0 vaults, $0 | **19 vaults, $20.50M** | 3 hops |
| reUSD | 10 vaults, $1.62M | **23 vaults, $11.33M** | 3 hops |
| USDC | 0 vaults, $0 | **20 vaults, $16.87M** | 3 hops |

Worst single hit for USDe: **senPYUSDmain** (curated by Sentora) holds $109.5M in the sUSDe/PYUSD market. Modelled loss $18.75M along `USDe → sUSDe → market sUSDe/PYUSD → senPYUSDmain`. Undertow's curator plan: set that market's supply cap to 0 and reallocate into kBTC/PYUSD, the largest PYUSD market whose collateral sits outside the USDe family.

Reproduce the table: `uv run python -m backend.sweep`.

## How it works

1. **Ingest** (`backend/ingest.py`): 1,830 markets, 470 V1 vaults and 537 V2 vaults with their adapters from Morpho's public API. Wrapper edges come from on-chain `asset()` reads on every collateral token (ERC-4626) plus Pendle PT symbols; unknown underlyings get their symbol from an on-chain `symbol()` read. The live graph holds 252 vaults, 220 markets, 156 assets and 29 curators, with 561 allocation edges and 53 wrapper edges.
2. **Shock** (`backend/shock.py`): the shocked asset and every wrapper above it lose the haircut. Each market with that collateral books the bad debt the shock adds, `max(0, borrow - collateral x (1 - haircut))` minus any bad debt already there, the instant-depeg case where liquidations cannot clear. Bad debt splits across supplying vaults by their share of supply, capped at what each vault allocated, then climbs every vault-of-vault edge by `allocation / child TVL`. Vault share tokens used as collateral take their vault's loss ratio as a fresh haircut, which carries the loss into the next round of markets.
3. **Agent** (`backend/agent.py`): a tool-calling analyst that runs shocks, reads vault exposure, walks paths, ranks systemic assets, queries the graph read-only, and drafts curator actions. Every answer cites the path and dollar figures its tools returned, and every Cypher statement it ran is shown in the UI.
4. **Memory**: every shock is stored as a `Scenario` node with `HITS` edges to each vault, so past scenarios survive restarts and the agent can compare them. Each chat session gets its own FalkorDB graph (`session_<id>`), using FalkorDB's multi-graph isolation, with turns chained by `NEXT` edges.

Remove FalkorDB and nothing works: the shock is a set of variable-length traversals, the curator plan is a graph search for a safe market, and memory lives in the graph.

## Graph data model

```
(:Curator)-[:CURATES]->(:Vault {address, symbol, version, tvlUsd})
(:Vault)-[:ALLOCATES {usd}]->(:Market {id, label, lltv, supplyUsd, borrowUsd, collateralUsd, badDebtUsd})
(:Vault)-[:ALLOCATES {usd}]->(:Vault)              V2 adapters into V1 or V2 vaults
(:Market)-[:COLLATERAL]->(:Asset {address, symbol, priceUsd})
(:Market)-[:LENDS]->(:Asset)
(:Asset)-[:WRAPS]->(:Asset)                        sUSDe -> USDe, PT-sUSDe -> sUSDe
(:Asset)-[:SHARE_OF]->(:Vault)                     collateral token that is a vault share
(:Scenario {id, asset, haircut, totalLossUsd, directVaults, graphVaults})-[:HITS {lossUsd, hops, path}]->(:Vault)
Per session graph:  (:Turn {i, role, content, ts})-[:NEXT]->(:Turn)
```

## The Cypher it depends on

Every wrapper above the shocked asset:

```cypher
MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($symbol)
MATCH p = (w:Asset)-[:WRAPS*0..4]->(s)
RETURN w.address, w.symbol, length(p), [n IN nodes(p) | n.symbol]
```

Loss carried up nested vaults, multiplying allocation ratios along each path:

```cypher
MATCH p = (parent:Vault)-[:ALLOCATES*1..4]->(child:Vault)
WHERE child.address IN $addrs
RETURN parent.address, parent.symbol, parent.tvlUsd, child.address,
       reduce(x = 1.0, i IN range(0, size(relationships(p)) - 1) |
              x * relationships(p)[i].usd / nodes(p)[i + 1].tvlUsd) AS ratio,
       [n IN nodes(p) | n.symbol], length(p)
```

Safe reallocation target: same loan asset, collateral outside the shocked asset's wrapper family:

```cypher
MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($asset)
MATCH (m:Market)-[:LENDS]->(:Asset {address: $loan})
MATCH (m)-[:COLLATERAL]->(c:Asset)
WHERE NOT (c)-[:WRAPS*0..4]->(s) AND m.supplyUsd > 1000000 AND m.borrowUsd < m.supplyUsd * 0.9
RETURN m.id, m.label, c.symbol, m.supplyUsd ORDER BY m.supplyUsd DESC LIMIT 1
```

Systemic assets rank by vault TVL reachable through their wrapper family, alongside `CALL algo.pageRank(NULL, NULL)` over the whole exposure graph. The full set is in `backend/queries.py` and `backend/shock.py`.

## Run it

Needs [uv](https://docs.astral.sh/uv/) and Python 3.12. FalkorDB runs embedded through `falkordblite` by default; set `FALKORDB_URL` to use a FalkorDB server or FalkorDB Cloud instead.

```bash
uv sync
cp .env.example .env               # add OPENROUTER_API_KEY and ALCHEMY_API_KEY (or ETH_RPC_URL)
set -a; source .env; set +a
uv run python -m backend.ingest    # pulls Morpho mainnet, resolves wrappers on-chain, builds the graph
uv run python -m backend.test_shock
uv run python -m backend.server    # http://localhost:8000
```

`UNDERTOW_REFRESH=1` forces a fresh pull from the Morpho API; otherwise ingest reuses the cached responses in `data/`.

With Docker and FalkorDB server:

```bash
docker run -d -p 6379:6379 falkordb/falkordb:latest
FALKORDB_URL=redis://localhost:6379 uv run python -m backend.ingest
```

## Verification

`backend/test_shock.py` builds a three-market, four-vault graph by hand and asserts exact losses for each vault: direct, through a wrapper, through a vault-of-vault edge, and through a vault share token reused as collateral. Cutting propagation to a single round makes it fail (`KeyError: 'C'`, the share-token hop disappears); restoring it passes.

## Built with

FalkorDB (embedded via falkordblite), FastAPI, d3, the Morpho public API, Ethereum JSON-RPC, and OpenRouter for the agent model. AI coding assistants (Claude Code and OpenCode with free models) were used during the build; the graph model, propagation rules and every number above were checked by running the code.
