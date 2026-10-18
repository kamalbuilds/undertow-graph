Maya puts $10,000 into a savings vault. The vault lends her money to borrowers and pays her interest. To borrow, each borrower locks up a guarantee worth more than the loan, so Maya's money is safe.

Until the guarantee quietly loses a third of its value, and nobody's alarm goes off.

This post is about why that happens, why it is a graph problem at its core, and how we built **Undertow** on FalkorDB in four days to find where the losses actually land.

**Try it:** [undertow-graph.fly.dev](https://undertow-graph.fly.dev) · **Code:** [github.com/kamalbuilds/undertow-graph](https://github.com/kamalbuilds/undertow-graph) · **Film (2:33):** [watch](https://github.com/kamalbuilds/undertow-graph/blob/main/video/undertow-film.mp4)

## The guarantee is wearing a disguise

In DeFi lending, the guarantee is usually a digital dollar: a token built to always be worth one dollar. But it is rarely the plain one.

Take USDe. Stake it and you get **sUSDe**, the savings version. Split that into a fixed-term token on Pendle and you get **PT-sUSDe**. Three layers, three names, one underlying dollar.

![Three layers, three names, one dollar](https://raw.githubusercontent.com/kamalbuilds/undertow-graph/main/docs/img/layers.png)

Now imagine USDe drops 30%. Every layer drops with it. The guarantees in Maya's vault are suddenly worth less than the loans they back, and the hole lands in her savings.

The warning systems most people rely on search for the name "USDe". Maya's vault only ever sees the outer layer, with a different name. Nothing gets flagged.

![The name search sees only the outer label](https://raw.githubusercontent.com/kamalbuilds/undertow-graph/main/docs/img/missed.png)

## This already happened

In November 2025, Stream Finance disclosed a $93M loss. Its token had been reused as a guarantee across lending markets, and analysts at Yields and More had to piece together roughly **$285M of linked debt across at least seven networks** ([The Block](https://www.theblock.co/news/defi/2025-11-04-analysts-map-285m-in-potential-exposure-across-defi-after-stream-finances-93m-loss-377491)). In March 2026, Resolv's USR was exploited and bad debt surfaced in lending markets again. A Morpho governance proposal in June 2026 asked, in so many words, for a "DeFi Integration Graph" that exposes these recursive dependencies.

The data to answer "who is exposed?" is public. Nobody had wired it together so the question takes seconds instead of days.

## Why this is a graph problem, not a spreadsheet problem

Here is the thing that makes it hard: **nobody knows in advance how many hops there are.**

A loss can travel:

- through a wrapper (USDe to sUSDe),
- through another wrapper (sUSDe to PT-sUSDe),
- into a lending market that accepts it as a guarantee,
- into the vault that funds that market,
- into a *second* vault that allocates into the first one,
- and, if that vault's own share token is used as a guarantee somewhere else, into a completely unrelated market.

In SQL that is a recursive join of unknown depth across five tables. In a graph it is one variable-length path query. That is the whole reason Undertow lives in FalkorDB.

## What we built

Undertow loads Morpho mainnet into a FalkorDB graph: **252 vaults, 220 markets, 156 assets, 29 curators, 561 allocation edges and 53 wrapper edges**, pulled from Morpho's public API. Wrapper edges come from on-chain `asset()` reads on every guarantee token, so `sUSDe -[:WRAPS]-> USDe` is a fact read from Ethereum, not a guess from a ticker.

```
(:Curator)-[:CURATES]->(:Vault)
(:Vault)-[:ALLOCATES {usd}]->(:Market)
(:Vault)-[:ALLOCATES {usd}]->(:Vault)        vaults that fund other vaults
(:Market)-[:COLLATERAL]->(:Asset)
(:Asset)-[:WRAPS]->(:Asset)                  sUSDe -> USDe
(:Asset)-[:SHARE_OF]->(:Vault)               a vault's own share token
(:Scenario)-[:HITS {lossUsd, hops, path}]->(:Vault)
```

Then you pick an asset, pick a drop, and press one button.

![Name search versus the graph](https://raw.githubusercontent.com/kamalbuilds/undertow-graph/main/docs/img/headline.png)

On today's real data, a 30% drop in USDe:

| | Vaults flagged | Money at risk |
|---|---|---|
| Name search for "USDe" | 2 | $10.6M |
| Undertow, following every layer | **10** | **$31.1M** |

Three times the exposure, five times the vaults. And USDe is not the extreme case: for USDS, the name search finds **zero** vaults. Undertow finds **19 vaults and $20.5M**, all reached through sUSDS, a Pendle token on top of it, and stUSDS.

## The two queries doing the heavy lifting

Every wrapper sitting on top of the shocked asset, at any depth:

```cypher
MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($symbol)
MATCH p = (w:Asset)-[:WRAPS*0..4]->(s)
RETURN w.address, w.symbol, length(p), [n IN nodes(p) | n.symbol]
```

And the loss carried up through vaults that fund other vaults. Each hop passes on `allocation / child TVL` of the loss, so we multiply those ratios along the path with a single `reduce()`:

```cypher
MATCH p = (parent:Vault)-[:ALLOCATES*1..4]->(child:Vault)
WHERE child.address IN $addrs
RETURN parent.address,
       reduce(x = 1.0, i IN range(0, size(relationships(p)) - 1) |
              x * relationships(p)[i].usd / nodes(p)[i + 1].tvlUsd) AS ratio
```

The loss rule itself is simple and stated up front: when a guarantee drops by the haircut, a market books `max(0, borrow - collateral x (1 - haircut))` of new bad debt, split across the vaults funding it by their share. Vault share tokens used as guarantees elsewhere inherit their vault's loss ratio, which is how a loss jumps into markets that never mention the original asset.

## Click any vault and see the exact path

The worst hit for USDe is a vault called **senPYUSDmain**, curated by Sentora. It has $109.5M lent against the savings version of USDe. Modelled loss: **$18.7M**, along `USDe -> sUSDe -> sUSDe/PYUSD market -> senPYUSDmain`.

![The exact path the loss takes](https://raw.githubusercontent.com/kamalbuilds/undertow-graph/main/docs/img/path.png)

## An agent that acts, not just answers

Showing a number is half the job. The people running a vault need to know what to *do*.

Undertow's agent is a tool-calling LLM whose tools are graph queries: run a shock, read a vault's exposure, walk paths, rank the most systemic assets (vault TVL reachable through the wrapper family, alongside FalkorDB's `algo.pageRank`), and draft a curator action. That last one is a graph search too: for each exposed market, find the largest market with the **same loan asset** whose guarantee sits **outside** the shocked asset's wrapper family.

```cypher
MATCH (m:Market)-[:LENDS]->(:Asset {address: $loan})
MATCH (m)-[:COLLATERAL]->(c:Asset)
WHERE NOT (c)-[:WRAPS*0..4]->(s) AND m.supplyUsd > 1000000
RETURN m.label ORDER BY m.supplyUsd DESC LIMIT 1
```

Ask it "If USDe drops 30%, what should the worst-hit vault do?" and it answers from the graph: set the sUSDe/PYUSD supply cap to zero and reallocate the $109.5M into kBTC/PYUSD. Every Cypher statement it ran is shown right under the answer, so nothing is a black box.

![The agent drafts the curator's move](https://raw.githubusercontent.com/kamalbuilds/undertow-graph/main/docs/img/agent.png)

## Memory that survives the session

Every shock is written back to the graph as a `Scenario` node with `HITS` edges to each vault, carrying the loss, hop count and path. The history is part of the graph the agent queries, so a later session can pull up past scenarios and compare them with a fresh run.

Each chat session gets its own FalkorDB graph (`session_<id>`), using FalkorDB's ability to hold thousands of isolated graphs in one instance. Turns are chained with `NEXT` edges. Conversations are kept apart at the storage level: they do not even share a graph.

## The bug that made the numbers honest

Our first full sweep said a 30% drop in deUSD would cost **$912M**. That number was absurd, and chasing it taught us something about real data.

The culprit was a dead market: sdeUSD/USDC still shows $11.4B borrowed against $0.096 of guarantee, the wreckage of Elixir's collapse. Our model was charging that old, already-realized bad debt to the new shock.

The fix was one line of intent: **count only the bad debt the shock adds**, `max(0, B - C(1-h)) - max(0, B - C)`. The $912M vanished, and every other number in this post is computed with that rule.

## How we know the math is right

A hand-built graph of three markets and four vaults asserts the exact loss for every path: direct, through a wrapper, through a vault that funds a vault, and through a share token reused as a guarantee. We then broke propagation on purpose (one round instead of three). The test went red because the share-token hop disappeared. We restored it and it went green. A test that cannot fail proves nothing; this one fails when it should.

## Why FalkorDB

- **Variable-length paths are the product.** `WRAPS*0..4` and `ALLOCATES*1..4` with `reduce()` along the path replace pages of recursive joins.
- **Fast enough to run on every click.** A full shock, wrapper search, market loss, nested vaults and share-token rounds runs live in the request.
- **Many graphs, one instance.** The exposure graph, the scenario history and a graph per chat session all live side by side.
- **Embedded or server, same code.** We developed against `falkordblite` with no Docker at all, and the same code runs against a FalkorDB server through one environment variable.

## Try it

- **Live:** [undertow-graph.fly.dev](https://undertow-graph.fly.dev). Pick an asset, set the drop, press *Run shock*, click a vault, ask the agent.
- **Code:** [github.com/kamalbuilds/undertow-graph](https://github.com/kamalbuilds/undertow-graph), with the full graph model and every query in the README.

When a digital dollar breaks, the losses hide behind layers of repackaging. Undertow finds where they land.

*Built for FalkorDB Graph Hacks (WeMakeDevs). AI coding assistants were used during the build; every number above was produced by running the code against live Morpho data.*
