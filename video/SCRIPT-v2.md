# Undertow film v2, target 2:25

One sentence: When a digital dollar breaks, the losses hide behind layers of repackaging. Undertow finds where they land.

Protagonist: Maya, one savings deposit of $10,000, start to finish (illustrative figures in Acts 1 to 3, real data from Act 4 on).
Jargon budget (2): "savings vault" (a pool that lends your money out for interest), "guarantee" (what a borrower locks up so the loan is safe). "Digital dollar" is defined on first use.

## Act 1: the setup (animation, 0:00-0:25)
Scene: Maya's coin drops into a glass vault; the vault hands it to a borrower, who locks a gold guarantee into the vault in return.
VO: "When a digital dollar breaks, the losses hide. Undertow finds where they land. Here is how they hide. Maya puts ten thousand dollars into a savings vault. The vault lends her money to borrowers and pays her interest. To borrow, each borrower locks up a guarantee worth more than the loan. If they don't pay back, the vault keeps the guarantee."
Captions: "Savings vault: lends your money out for interest" / "Guarantee: what a borrower locks up"

## Act 2: the hidden layers (animation, 0:25-0:50)
Scene (bespoke mechanism): the guarantee opens like nesting boxes. Innermost: a coin labelled "USDe". Wrapped in a box labelled "sUSDe, savings version", then in a box labelled "PT-sUSDe, fixed-term version". Only the outer label is visible on the vault shelf.
VO: "Those guarantees are often digital dollars: crypto tokens built to always be worth one dollar. But rarely the plain one. A digital dollar called USDe gets repackaged into a savings version, then into a fixed-term version. Each layer gets a new name, and the vault only sees the outside one."

## Act 3: the bad day (animation, 0:50-1:10)
Scene: the inner coin cracks and drops 30 percent; a crack runs out through each box; the guarantee shrinks below the loan; a red gap opens in Maya's vault, her balance ticks down. A magnifying glass labelled "Warning system: search for 'USDe'" sweeps the shelf, sees only outer labels, shows "nothing found". The caption under it turns red: "Missed".
VO: "Then USDe drops thirty percent. Every layer drops with it. The guarantees are now worth less than the loans, and the hole lands in Maya's savings. The usual warning system searches for the name USDe. Maya's vault only holds the outer layer, with a different name. Nothing gets flagged."

## Act 4: it already happened (source proof, 1:10-1:22)
Scene: real screenshot video/v2/src/theblock.png, headline highlighted, held 4 s.
VO: "This has happened before. Last November, one crypto fund's ninety three million dollar loss spread through lending pools like this one, and analysts had to piece together two hundred and eighty five million dollars of linked debt across seven networks."

## Act 5: the product (1:22-1:40)
Scene: the nesting boxes unfold into a graph: vaults, loans, guarantees and layers as connected dots; a light travels hop by hop from the cracked coin to Maya's vault.
VO: "Undertow loads every savings vault, loan and layer on Morpho, one of the largest of these lending networks, into a FalkorDB graph. Each repackaging is one more hop, and nobody knows in advance how many hops there are. In a graph, that is a single path query that walks every hop, re-run live on every what-if."

## Act 6: live demo on today's real data (1:40-2:15)
1. WHY: "What if USDe dropped thirty percent today?" DO: press the button (callout: "Simulate a 30% drop"). SEE: callout on the two big numbers.
   VO: "Here is today's real data. If USDe dropped thirty percent right now, a name search would flag two vaults and ten point six million dollars. Undertow follows every layer and finds ten vaults and thirty one million. Each of those vaults holds savers like Maya that the name search missed."
   Callout: "Name search: $10.6M, 2 vaults" vs "Undertow: $31.1M, 10 vaults"
2. WHY: "Which vault is hit hardest, and how?" DO: click the top vault. SEE: path lights up.
   VO: "The worst hit loses eighteen point seven million. Its path skips the fixed-term layer: USDe, its savings version, the loan pool, the vault."
3. WHY: "What should that vault's manager do?" DO: ask the assistant. SEE: its answer, highlighted.
   VO: "Ask the assistant and it answers from the same graph: stop lending into that pool, and move the money to the largest one whose guarantee has nothing to do with USDe."

## Act 7: close (2:15-2:25)
Scene: second digital dollar run, label "Second digital dollar", name search 0 vaults vs Undertow 19 vaults, $20.5M; end card with the one sentence and the repo URL.
VO: "For a second digital dollar, the name search finds nothing at all. Undertow finds nineteen vaults. When a digital dollar breaks, Undertow finds where the losses land."
