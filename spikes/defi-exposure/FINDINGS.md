# Spike: live nested DeFi exposure graph from Morpho's public API

Claim: Morpho's public GraphQL (blue-api.morpho.org/graphql, no key) exposes enough structure to build a >=4-hop exposure graph (vault -> vault -> market -> collateral -> underlying) on Ethereum mainnet today.

Run 2026-10-18 ~14:20 IST. Result: CONFIRMED with caveats.
- 1,830 mainnet markets; 193 with >$100k borrow (markets.json).
- 470 V1 vaults; 41 listed with >$100k, $405M TVL; allocation per market available (vaults.json).
- 537 V2 vaults (top-100 TVL $127M). V2 adapters: MetaMorphoAdapter (V2 -> V1 vault), MorphoVaultV2Adapter (V2 -> V2), MorphoMarketV1Adapter (V2 -> market). Nesting is native.
- Asset.vault marks collateral that is itself a vault share (1 live market: MC-USR).
- Wrapper families present as collateral: USDe/sUSDe/PT-USDe, reUSD/PT-reUSD, USD3/PT-USD3.
- Market.badDebt / realizedBadDebt exist: wstUSR, USR, RLP, PT-RLP carry bad debt (Resolv USR exploit, 2026-03-22).

Negative case: unfiltered markets give absurd numbers (PAXG $17.2B borrow, BONDUSD $5.6B bad debt): junk-priced dead markets. Filter: listed vaults' allocations, cap by vault TVL; never sum raw market state.

Caveats: wrapper -> underlying mapping is not in the API; must be derived (ERC4626 asset() via RPC, PT- prefix parse). Morpho only; cross-protocol (Aave, Euler, Pendle) out of scope for the deadline.
