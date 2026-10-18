# Undertow demo, target 2:30 to 3:00

Beat 1 (0:00-0:15) Hook, UI on screen, USDe preselected.
VO: "When a stablecoin breaks, risk alerts look for its name. On Morpho today, an alert on USDe finds two vaults and ten point six million dollars. The real exposure is three times that."

Beat 2 (0:15-0:45) Click Run shock at 30%. Headline: Direct collateral alert $10.6M, 2 vaults; Through the graph $31.1M, 10 vaults.
VO: "Undertow loads all of Morpho mainnet into FalkorDB. Eighteen hundred markets, a thousand vaults, and every wrapper resolved on chain. A thirty percent shock on USDe follows sUSDe, the Pendle tokens on top of it, and vaults that lend into other vaults. Ten vaults. Thirty one million dollars."

Beat 3 (0:45-1:15) Graph pulse; click senPYUSDmain hit, path highlights.
VO: "The worst hit is senPYUSDmain, curated by Sentora. A hundred and nine million dollars sit in the sUSDe PYUSD market. Modelled loss: eighteen point seven million. Here is the exact path: USDe, wrapped into sUSDe, posted as collateral, lent against by this vault."

Beat 4 (1:15-1:35) Open "Show the Cypher".
VO: "Every number comes from a graph query. Variable length wrapper paths, and one reduce over nested vault allocations that carries the loss up each level."

Beat 5 (1:35-2:15) Agent chat: "If USDe depegs 30%, who loses most, and what should the curator do?" Show reply and the Cypher the agent ran.
VO: "The agent works the same graph. It runs the shock, reads the vault's exposure, and searches for a safe place to move the money: the largest PYUSD market whose collateral sits outside the USDe family. Cap sUSDe PYUSD at zero. Reallocate into kBTC PYUSD."

Beat 6 (2:15-2:35) Past scenarios list; switch asset to USDS, run: alert 0 vaults vs graph 19 vaults $20.5M.
VO: "Every shock is saved as a scenario in the graph, so the next session starts from what the last one found. USDS: the name alert sees nothing. The graph finds nineteen vaults and twenty million dollars."

Beat 7 (2:35-2:50) Close on headline.
VO: "Undertow. Follow the loss, not the symbol. Built on FalkorDB."
