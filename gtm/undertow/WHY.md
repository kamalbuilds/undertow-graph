# undertow: why we are building it, and why a user picks it

## The one sentence

When one DeFi asset breaks, Undertow shows every vault the loss reaches, the path it travels, and what the curator should move first.

## Who it is for

Morpho and Euler vault curators (Sentora, MEV Capital, Re7 Labs, Steakhouse, Gauntlet, Block Analitica, TelosC, Varlamore), DeFi risk analysts (Yields and More, LlamaRisk, Chaos Labs), and depositors in curated vaults. Each is named with a post of theirs in USERS.md.

## What they do today, and what breaks

During Resolv USR (2026-03-22) curators and power users compiled exposure lists by hand on X: "Funds that might have exposure to Resolv ... Morpho Vaults that has lend money to RLP, wstUSR (and there is a lot)". A depositor asked in public whether a flagship vault's exposure was being understated. After Stream xUSD, the analyst group that mapped $284.9M wrote that its list was not extensive. A symbol alert on the shocked asset finds only markets that list it directly; the loss also travels through wrappers (USDe to sUSDe to a Pendle PT), through vaults that allocate into other vaults, and through vault share tokens posted as collateral.

## Why undertow and not the others

- Symbol alerts and dashboards match one asset to the markets that name it. Undertow follows the wrapper chain, vault-of-vault allocations and vault share collateral, and on live Morpho state reaches 10 vaults and $31.14M for a USDe shock where a symbol match reaches 2 vaults and $10.62M.
- Governance proposals and research models describe or forecast exposure. Undertow computes it on today's allocations and ends in an action: the cap cut and reallocation for each exposed curator.
- Every answer carries its path and its Cypher, so a curator can check the claim against the chain before acting.

## What makes it ours

A FalkorDB graph of Morpho mainnet (252 vaults, 220 markets, 156 assets, 29 curators) with wrapper edges read from ERC-4626 asset() calls, a shock model that books bad debt per market and climbs vault-of-vault edges, persisted Scenario nodes that survive restarts, and per-session graphs for the agent's memory.

## The bar for "it works"

A named curator shocks their own worst asset, sees their vault in the hit list with the path and dollar loss, and receives a cap-cut draft they would send. The USDe, USDS, reUSD and USDC sweep reproduces with `uv run python -m backend.sweep`, and every vault in the result can be re-derived from the cited Cypher.
