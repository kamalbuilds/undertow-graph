# A symbol alert saw $10.6M. The graph found $31.1M.

When a DeFi asset depegs, the first question is usually which markets accept it as collateral. We can answer that by searching for the asset's symbol and listing the markets that reference it. The harder question is how much risk sits behind those markets, including exposure that passes through wrappers, nested vaults, and vault shares used as collateral elsewhere.

We built Undertow for FalkorDB Graph Hacks to answer that second question. It models collateral and allocation relationships as a graph, propagates a hypothetical loss through those relationships, and lets an agent investigate the resulting exposure with auditable Cypher queries.

At a 30% haircut on USDe, our symbol-based alert found two vaults with $10.62M in exposure. Undertow found ten vaults with $31.14M in modelled losses across three hops.

The difference comes from following the money rather than matching a symbol.

## The problem with symbol-based alerts

A symbol alert works when risk is local. If a market lists USDe as collateral, an alert keyed on USDe can identify it. But the alert does not necessarily identify the vaults supplying that market, the vaults allocating into those vaults, or the collateral relationships created by tokenized vault shares.

Consider a wrapper chain:

`USDe -> sUSDe -> Pendle PT-sUSDe`

A market can accept the final wrapper without directly listing USDe. A search for USDe can miss that dependency.

The same problem appears in vault composition. A Morpho V2 adapter can allocate into a V1 or V2 vault, which supplies another market. If that market incurs bad debt, the loss can affect the supplying vault and propagate to its parent. A vault's share token can also be posted as collateral in another market, creating another route through which losses can travel.

These are different mechanisms, but they create the same analytical problem: risk follows relationships that a flat list of markets cannot represent.

There is precedent for this kind of investigation. During the November 2025 Stream Finance xUSD collapse, analysts at Yields and More mapped approximately $285M of exposure across lending markets by hand, as reported by The Block on November 4, 2025. In June 2026, a Morpho forum RFC proposed a "DeFi Integration Graph" to expose recursive collateral dependencies.

Undertow explores how we can make that dependency mapping queryable and the resulting loss estimates reproducible.

## Building the graph

We collected mainnet data from Morpho's public GraphQL API: 1,830 markets, 470 V1 vaults, and 537 V2 vaults. For wrapper relationships, we combined on-chain ERC-4626 `asset()` reads with Pendle PT symbols.

We then loaded a connected model into FalkorDB containing 252 vaults, 220 markets, 156 assets, and 29 curators. The graph includes 561 `ALLOCATES` edges and 53 `WRAPS` edges.

We represent the core relationships as follows:

```text
(Vault)-[:ALLOCATES {usd}]->(Market|Vault)
(Market)-[:COLLATERAL]->(Asset)
(Market)-[:LENDS]->(Asset)
(Asset)-[:WRAPS]->(Asset)
(Asset)-[:SHARE_OF]->(Vault)
(Curator)-[:CURATES]->(Vault)
(Scenario)-[:HITS {lossUsd,hops,path}]->(Vault)
```

Each edge captures a different part of the risk model. `ALLOCATES` represents capital deployed by a vault into a market or another vault. `COLLATERAL` and `LENDS` describe a market's asset relationships. `WRAPS` connects an asset to its underlying asset, while `SHARE_OF` links vault share tokens to the vault they represent. `CURATES` identifies the curator responsible for a vault.

When we run a shock, the resulting `Scenario` records which vaults were hit, the modelled loss, the number of hops, and the path through which exposure propagated.

This structure makes relationships first-class data. Instead of writing a separate traversal for every combination of wrappers, markets, and nested vaults, we can query the graph for paths that connect them.

## Finding wrapper dependencies

Our wrapper query starts with an asset symbol and walks up to four `WRAPS` edges:

```cypher
MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($symbol)
MATCH p = (w:Asset)-[:WRAPS*0..4]->(s)
RETURN w.address, w.symbol, length(p), [n IN nodes(p) | n.symbol]
```

The zero-length path includes the asset itself. Longer paths expose wrappers connected to it through intermediate assets. Returning the complete symbol path helps us explain why an apparently unrelated collateral token belongs to a shocked asset's dependency family.

That is important because discovering a wrapper is only the beginning. We still need to determine which markets accept it, which vaults supply those markets, and how much loss can reach each vault.

## Propagating a hypothetical loss

We model a depeg as a haircut applied to collateral value. For each market, the added bad debt is:

`max(0, borrow - collateral * (1 - haircut)) - existing bad debt`

The subtraction is essential. We want to estimate the additional bad debt caused by the scenario, not count losses that were already present before the shock.

We distribute the added loss across supplying vaults according to their share of market supply, capped at each vault's allocation. We then propagate losses through vault-of-vault relationships. For those relationships, the model uses allocation divided by child vault TVL to calculate the relevant exposure ratio.

The nesting calculation is expressed as a single Cypher `reduce()` over variable-length allocation paths:

```cypher
MATCH p = (parent:Vault)-[:ALLOCATES*1..4]->(child:Vault)
WHERE child.address IN $addrs
RETURN parent.address, reduce(x = 1.0, i IN range(0, size(relationships(p)) - 1) | x * relationships(p)[i].usd / nodes(p)[i + 1].tvlUsd) AS ratio
```

This lets us calculate the compounded allocation ratio along each path rather than treating every parent vault as if it had direct exposure to the original market.

Vault share tokens introduce another layer. When a vault is hit, its loss ratio becomes a new haircut on its share token in the next round. That haircut can create additional bad debt in markets where the share token is collateral.

Propagation therefore continues across rounds. A shock can affect a market, its supplying vaults, vaults allocating into those vaults, and markets accepting the resulting vault shares. The model records these dependencies rather than collapsing them into one symbol match.

## The results at a 30% haircut

We compared Undertow's graph-based propagation with symbol-based alerts for four assets.

| Asset | Symbol alert | Graph result | Graph hops |
|---|---:|---:|---:|
| USDe | 2 vaults, $10.62M | 10 vaults, $31.14M | 3 |
| USDS | 0 vaults | 19 vaults, $20.50M | Not specified |
| reUSD | 10 vaults, $1.62M | 23 vaults, $11.33M | Not specified |
| USDC | 0 vaults | 20 vaults, $16.87M | Not specified |

These are modelled results under the specified haircut, not predictions of realised losses.

USDe illustrates the difference most clearly. The symbol alert identifies a limited set of direct relationships. The graph includes additional exposure reached through wrappers, market suppliers, and nested vaults.

USDS and USDC demonstrate a separate limitation: an alert can return zero vaults even when the graph finds material modelled exposure. A zero in a symbol-based result means the alert found no matching vaults. It does not establish that the asset has no indirect dependencies.

## From exposure paths to an action

The largest USDe hit in our results was `senPYUSDmain`, curated by Sentora. The vault holds $109.5M in sUSDe/PYUSD. Our model assigns it a loss of $18.75M along this path:

`USDe -> sUSDe -> sUSDe/PYUSD -> senPYUSDmain`

The path explains how a shock to USDe can reach a vault whose name does not directly identify USDe exposure.

Undertow's agent proposed capping that market at zero and reallocating into kBTC/PYUSD. It found the alternative with a Cypher query that selects the largest market using the same loan asset while keeping collateral outside the USDe wrapper family.

This is a proposed curator action, not an executed transaction. The graph provides the exposure path and a way to identify an alternative; a curator still needs to evaluate and approve the decision.

## Making the analysis inspectable

We connected a tool-calling LLM through OpenRouter to a set of graph operations:

- `run_shock` models a hypothetical asset shock.
- `vault_exposure` retrieves vault exposure.
- `paths` traces dependency paths.
- `systemic_assets` ranks assets using reachable vault TVL and `algo.pageRank`.
- `past_scenarios` retrieves previous shocks.
- `read-only query_graph` permits direct graph investigation.
- `draft_curator_action` drafts a potential response.

The UI shows every Cypher statement the agent ran. This matters because an answer such as "$31.1M at risk" is not sufficient by itself. We need to inspect which paths contributed to that number, how the model traversed them, and what assumptions affected the result.

We also persist every shock as a `Scenario` node. Each chat session receives its own FalkorDB graph named `session_<id>`, providing multi-graph isolation. Turns within a session are chained through `NEXT` relationships. This gives us a record of the analysis without mixing the conversational state of separate sessions.

## A bug that changed the result

While building Undertow, we found a dead Elixir sdeUSD/USDC market showing $11.4B borrowed against $0.096 of collateral. When we counted existing bad debt as part of the shock, deUSD appeared to cause a $912M shock.

That result exposed a modelling error, not a newly discovered loss caused by deUSD. The calculation was attributing pre-existing bad debt to the hypothetical event.

We fixed the calculation to count only the bad debt added by the shock. This is why the loss rule subtracts existing bad debt before propagation. Without that distinction, an extreme market state can dominate the scenario and make the downstream exposure estimate misleading.

We also built a hand-constructed four-vault test that asserts exact losses. The test fails when propagation is cut to a single round. That gives us a concrete check that the implementation follows dependencies beyond the first layer, rather than merely producing a plausible-looking total.

## What Undertow establishes

Undertow demonstrates a graph-based approach to tracing DeFi risk across wrappers, lending markets, nested vaults, and collateralized vault shares. Its main contribution is not simply finding more vaults. It is making the paths between an initial shock and downstream exposure explicit, queryable, and inspectable.

The USDe comparison captures the point: a symbol alert found $10.62M across two vaults, while the graph model found $31.14M across ten vaults and three hops.

That difference is useful only if we can explain how the model reached it. By storing relationships in FalkorDB, recording scenarios, exposing the agent's Cypher statements, and testing exact loss propagation, we have a foundation for investigating that explanation.

The model still depends on the quality of its underlying data and its assumptions about haircuts, allocations, and propagation. Its output is a scenario estimate, not a guarantee of realised losses. But when a depeg crosses several layers of DeFi composition, following the graph gives us a more complete picture than searching for a symbol alone.
