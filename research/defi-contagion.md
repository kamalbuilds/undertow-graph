[chatgpt] tool:web.run

Sources:
  https://www.credora.network/blog/posts/defi-risk-score-portfolio-assessment/
  https://www.credora.network/blog/posts/blog-defi-vault-coverage-credora-ratings/
  https://defillama.com/research/report/exponentialfi-report-evaluating-risk-in-defi
  https://defillama.com/research/report/the-year-of-riskaware-defi-credora-ratings-as-the-1t-unlock-primitive
  https://defillama.com/protocols/risk-curators
  https://defillama.com/pro/risk-curators-5jg1yr
  https://www.theblock.co/news/defi/2025-11-04-analysts-map-285m-in-potential-exposure-across-defi-after-stream-finances-93m-loss-377491
  https://www.theblock.co/news/defi/2025-12-22-2026-defi-outlook-383120
  https://www.theblock.co/news/defi/2026-03-22-resolvs-usr-stablecoin-depegs-after-attacker-mints-80-million-unbacked-tokens-extracts-roughly-25-million-394582
  https://www.theblock.co/news/regulation/2026-04-18-kelp-daos-rseth-bridge-apparently-exploited-for-roughly-292-million-in-layerzero-based-attack-397988
  https://www.theblock.co/research/defi-protocols/vaults-oracle-risk-who-decides-who-pays-417418
  https://www.theblock.co/news/defi/2026-05-06-aave-liquidates-kelp-dao-attackers-remaining-rseth-positions-400315
  https://www.theblock.co/news/defi/2026-04-21-industry-of-clowns-defi-grapples-security-tradeoffs-292m-kelp-dao-fallout-398280
  https://www.theblock.co/news/defi/2026-04-20-kelp-dao-shifts-blame-layerzero-398204
  https://www.theblock.co/news/regulation/2026-04-01-crypto-hack-exploit-losses-52-million-396010
  https://www.theblock.co/news/defi/2026-04-20-defi-losses-1-billion-weeks-kelp-dao-exploit-drags-tvl-one-year-low-398154
  https://www.theblock.co/news/ecosystems/2026-05-12-kelp-dao-aave-resume-rseth-401060
  https://www.theblock.co/newsletters/data-and-insights/2026-05-27-data-insights-hype-highs-and-defi-exploits-402601
  https://castlelabs.io/research/reports/vaultification-of-finance
  https://enterprise.defillama.com/research/report/state-of-defi-2025
  https://enterprise.defillama.com/protocols/risk-curators
  https://forum.morpho.org/t/rfc-a-user-centric-defi-collateral-transparency-framework-phase-1/2301
  https://cointelegraph.com/news/defi-sleuths-trace-284m-stream-finance-exposure
  https://www.arunights.com/research/stream-finance-collapse
  https://forum.euler.finance/t/gauntlet-euler-dashboard/1291
  https://forum.euler.finance/t/gauntlet-introduction-to-the-euler-dao/1274
  https://hoge.gg/defi-lending-markets-2026-modularization-curator-risk/
  https://hoge.gg/defi-lending-broke-2026-curator-reckoning/
  https://investors.defillama.com/research/spotlight/white-label-aave-deployment-the-risk-function-an-operator-cannot-rebuild-alone
  https://investors.defillama.com/protocols/risk-curators
  https://investors.defillama.com/protocol/re7-labs
  https://www.eb.global/insights/vaults-are-not-vehicles
  https://tokenintel.org/reports/stream-finance-post-mortem-2026-05-21.html
  https://hindenrank.com/blog/how-does-re7-labs-work
  https://ketjuresearch.com/register/morpho-blue/
  https://thedefianalyst.substack.com/p/risk-curators
  https://blog.web3wagmi.com/best-risk-curators
  https://provectolabs.substack.com/p/what-defi-risk-curation-should-steal
  https://coinradardaily.com/ratings/defi-risk-managers
[gpt-5-6 - 26.3s - https://chatgpt.com/c/6ad490ce-c570-83ec-82a5-8a02d9a94f9b]
# DeFi recursive-exposure risk: research brief

*Research cutoff: 18 October 2026. Key distinction: direct protocol losses, estimated exposure, and realized bad debt are different measures.*

## 1. Stream Finance / xUSD, November 2025

On 4 November, Stream Finance disclosed a **$93 million loss** at an external fund manager and suspended deposits and withdrawals. The contagion came from xUSD being reused as collateral across lending markets, with some markets maintaining a $1 valuation despite the depeg. <Link url="https://www.theblock.co/news/defi/2025-11-04-analysts-map-285m-in-potential-exposure-across-defi-after-stream-finances-93m-loss-377491" title="The Block's contemporaneous investigation"/>.

**Who mapped it?** Yields and More (YAM) published the widely cited exposure map. Its analysis traced onchain lending positions, collateral reuse, and cross-protocol dependencies. The published reporting establishes the map's scope, but doesn't establish that the entire process was manual or identify a complete automated pipeline. <Link url="https://cointelegraph.com/news/defi-sleuths-trace-284m-stream-finance-exposure" title="Cointelegraph's coverage of YAM's investigation"/>.

| Exposure | Reported amount | What it means |
|---|---:|---|
| Total Stream-linked debt | ~$285M | YAM's estimate across at least seven networks, excluding some indirect derivative exposure |
| TelosC | $123.6M | Largest identified curator exposure |
| Elixir / deUSD | $68M | USDC lent to Stream; approximately 65% of deUSD backing |
| MEV Capital | $25.4M | Identified Stream-linked lending exposure |
| Re7 Labs, Varlamore | Additional exposure | Positions across curated lending markets |

Source for all figures: <Link url="https://www.theblock.co/news/defi/2025-11-04-analysts-map-285m-in-potential-exposure-across-defi-after-stream-finances-93m-loss-377491" title="The Block, 4 November 2025"/>.

Morpho, Euler and Silo were among the affected lending venues. The important distinction is that $285M was an exposure estimate, **not $285M of confirmed losses**. Elixir's deUSD added another contagion path because its backing depended heavily on Stream, while the two synthetic-dollar systems had circular collateral links. <Link url="https://www.theblock.co/news/defi/2025-12-22-2026-defi-outlook-383120" title="The Block's analysis of the circular exposure"/>.

## 2. Further contagion events in 2026

| Date | Event and downstream exposure |
|---|---|
| **22 March** | **Resolv / USR:** approximately 80M unbacked USR minted; roughly $25M extracted. Subsequent reporting identified bad debt across Morpho and Fluid, with some estimates around $10M and $21M respectively. <Link url="https://www.theblock.co/news/defi/2026-03-22-resolvs-usr-stablecoin-depegs-after-attacker-mints-80-million-unbacked-tokens-extracts-roughly-25-million" title="The Block"/>; <Link url="https://castlelabs.io/research/reports/vaultification-of-finance" title="Castle Labs"/>. |
| **18 April** | **Kelp DAO / rsETH:** bridge exploit of approximately $292M; stolen rsETH was used as Aave collateral, creating an estimated $190M bad-debt position. <Link url="https://www.theblock.co/news/defi/2026-04-18-kelp-daos-rseth-bridge-apparently-exploited-for-roughly-292-million-in-layerzero-based-attack-397988" title="Exploit reporting"/>; <Link url="https://www.theblock.co/news/ecosystems/2026-05-12-kelp-dao-aave-resume-rseth-operations-as-recovery-from-292-million-exploit-progresses" title="Recovery update"/>. |
| **6 July** | **Lazy Summer / Block Analitica:** secondary reporting describes approximately $6.04M extracted from two USDC vaults through overvalued donated tokens in a strategy. This was a vault-strategy exploit rather than a stablecoin depeg. <Link url="https://coinradardaily.com/ratings/defi-risk-managers" title="Incident summary"/>. |

These events demonstrate different failure modes: recursive collateral, privileged minting and bridge verification. They should not be combined into one aggregate loss figure.

## 3. Who says the tooling is inadequate?

The strongest directly relevant public evidence I found is the June 2026 Morpho governance proposal, [A User-centric DeFi Collateral Transparency Framework](https://forum.morpho.org/t/rfc-a-user-centric-defi-collateral-transparency-framework-phase-1/2301).

It argues that isolated markets can still share hidden dependencies through collateral composed of other vault tokens. Its proposed DeFi Integration Graph and Yield Tree Decomposition are intended to identify recursive exposure, leverage loops and hidden dependencies from live onchain data.

I could **not verify attributable X/forum quotations explicitly complaining about missing nested-exposure tooling** from Steakhouse, Gauntlet, MEV Capital, Re7, Block Analitica or LlamaRisk. I would not attribute the Morpho proposal's criticism to those firms without primary-source evidence.

## 4. Existing tools and the remaining gap

- **[DeFiLlama](https://defillama.com/protocols/risk-curators):** tracks protocols, TVL and curator-level activity. It is useful for discovery, but aggregate TVL is not a recursive exposure graph.
- **[Exponential](https://defillama.com/research/report/exponentialfi-report-evaluating-risk-in-defi):** offers a structured risk framework spanning protocols, assets and markets. That is different from tracing every nested collateral dependency.
- **[Credora](https://www.credora.network/blog/posts/blog-defi-vault-coverage-credora-ratings/):** provides risk ratings used in vault coverage underwriting. Ratings and coverage pricing do not themselves establish a complete live dependency graph.
- **[Chaos Labs](https://forum.morpho.org/t/rfc-a-user-centric-defi-collateral-transparency-framework-phase-1/2301):** performs protocol risk analysis, including oracle and leverage-loop risks. The cited proposal argues that systematic, shared visibility into these signals remains missing.
- **[Hypernative](https://www.hypernative.io/):** focuses on real-time threat detection and security monitoring; that is not equivalent to calculating recursive economic exposure.
- **[Gauntlet's Euler dashboard](https://forum.euler.finance/t/gauntlet-euler-dashboard/1291):** surfaces market-level risk metrics, including value at risk and liquidations at risk, rather than a universal cross-protocol collateral graph.

**Opportunity:** build a continuously updated graph that resolves vault shares into underlying assets, follows collateral through lending and rehypothecation loops, quantifies exposures by curator and lender, and simulates a depeg or exploit across the entire dependency tree. The key differentiator is not another risk score. It is **showing exactly where the same underlying risk appears multiple times, and how much capital each failure can reach**.
