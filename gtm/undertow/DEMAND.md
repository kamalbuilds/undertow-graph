# undertow: what users said they want

One block per piece of evidence. The quote is verbatim from the URL; `gtm verify` fetches it.
Minimums: 3 X authors, 2 Reddit/HN/forum threads, 2 blogs or newsletters, 1 paper.

### Depositors want to know whether a flagship vault's exposure is being understated
https://x.com/D2_Finance/status/2035596979603218730
> Is the Morpho FE wrong, or is Core exposure being understated?
who: @D2_Finance
date: 2026-03-22
means: Undertow recomputes exposure from the allocation graph and shows the path (vault to market to wstUSR), so a depositor can check a curator's "unaffected" claim in minutes.

### Distribution partners need the list of vaults exposed to a market, per vault share of exposure
https://x.com/OctavioNotPunk/status/2035720837882323204
> In total, 5 notable vaults are exposed to this market.
who: @OctavioNotPunk
date: 2026-03-22
means: The shock result is a ranked vault list with each vault's share of exposure, which is what Jumper Earn used to decide which deposits to disable.

### Power users compile exposure lists by hand during an incident
https://x.com/KazumaxCrypto/status/2035591205749502110
> Funds that might have exposure to Resolv ... Morpho Vaults that has lend money to RLP, wstUSR (and there is a lot)
who: @KazumaxCrypto
date: 2026-03-22
means: One query replaces the hand-built list; the wrapper chain (wstUSR, RLP, PT-) is expanded automatically so "might have" becomes a computed path.

### Curators name missing collateral monitoring as the failure
https://x.com/Matthew_Graham_/status/2036002083241971984
> Bots auto allocating to downgraded collateral tells you the curator was not monitoring the collateral.
who: @Matthew_Graham_
date: 2026-03-23
means: Undertow's scenario and alert nodes flag allocation into an already-shocked asset and draft the cap cut before the bot reallocates.

### Risk teams hand-trace vault-in-vault exposure after a depeg
https://x.com/omeragoldberg/status/2036478623952023920
> Chaos AI analyzed the vaults impacted by the USR exploit.
who: @omeragoldberg
date: 2026-03-24
means: Vault-in-vault receipt exposure (USD Alpha held receipt tokens of the Resolv USDC vault) must be a first-class edge; Undertow traverses ALLOCATES across vaults to depth 5.

### The protocol's own answer to "who is exposed" is to read each curator's posts
https://x.com/MerlinEgalite/status/2035642775941632389
> For guidance on vaults that may have exposure to USR or Resolv related assets, we recommend following the relevant curator communications.
who: @MerlinEgalite
date: 2026-03-22
means: No protocol-level exposure map exists to point depositors at; Undertow produces one per shocked asset with its evidence path.

### Morpho governance thread: nested exposure is not surfaced by any interface
https://forum.morpho.org/t/rfc-a-user-centric-defi-collateral-transparency-framework-phase-1/2301
> These dark loops are detectable from onchain state but are not surfaced by any existing interface.
who: sigmalabs (Sigma Labs, Morpho forum)
date: 2026-06-08
means: Recursive collateral dependencies are the named gap; Undertow persists them as graph edges and answers shock queries over them.

### Depositors ask whether anyone traces shared dependencies with a tool or with spreadsheets
https://www.reddit.com/r/defi/comments/1x3vf2r/can_defi_protocols_really_be_considered/pfevesy/
> Anyone doing this with a tool, or is it all spreadsheets?
who: u/Bloqarl
date: 2026-10-12
means: The retail question has no tool answer; Undertow's depositor view lists the shared roots behind "diversified" vaults.

### Depositors count wrappers of one asset as one position
https://www.reddit.com/r/defi/comments/1x3vf2r/can_defi_protocols_really_be_considered/pfg8nc5/
> if the answer is all of them then it's really one position in three wrappers.
who: u/Sookkhuii
date: 2026-10-12
means: The unit of exposure is the terminal asset behind the wrappers (USDe to sUSDe to PT-sUSDe), which is the WRAPS traversal Undertow runs.

### Analysts publish exposure maps and say they are incomplete
https://cointelegraph.com/news/defi-sleuths-trace-284m-stream-finance-exposure
> This is not an extensive list; there likely are more stables/vaults affected, and the information presented here is not guaranteed to be accurate
who: Yields and More (YAM)
date: 2025-11-04
means: A hand-built map of $284.9M of Stream debt missed secondary vaults; graph traversal reaches vaults-of-vaults that a manual sweep skips.

### Analysts expect more affected vaults to surface as positions unwind
https://www.theblock.co/news/defi/2025-11-04-analysts-map-285m-in-potential-exposure-across-defi-after-stream-finances-93m-loss-377491
> This map is still incomplete ... We expect more affected vaults to emerge as positions unwind and lending contracts are audited.
who: Yields and More (YAM)
date: 2025-11-04
means: Exposure must be re-computed as positions change; Undertow stores scenarios and reruns them on fresh ingests.

### Curator concentration makes a single curator's miss a system event
https://castlelabs.io/research/reports/vaultification-of-finance
> Three curators controlled 75% of the $6.5 billion risk-curated vault category
who: Castle Labs
date: 2026-05-01
means: The actionable object is the curator: Undertow ends each shock at the curator's cap-cut and reallocation draft.

### Research names token-mediated contagion as the unquantified risk
https://arxiv.org/abs/2602.03981
> a shock to one token may result in significant and uncontrolled contagion effects
who: Shu, Wu, Ibikunle, He (arXiv 2602.03981)
date: 2026-02-03
means: Shocking one token and following the loss is the named research problem; Undertow runs it live on Morpho's allocation graph.
