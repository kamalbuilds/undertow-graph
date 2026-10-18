# undertow: design

What the user sees and does, screen by screen, and the visual system it uses.

## The core loop

Pick an asset, set the haircut, run the shock. The headline number appears first (dollars at risk and vaults hit), then the graph of the path the loss travelled, then the ranked list of vaults hit. The agent panel answers follow-up questions and drafts the curator action. Every run is saved as a scenario that can be reopened later.

## Screens

One screen, three working regions.
- Shock panel: asset search, haircut slider, Run shock button, and the headline result with the exact Cypher that produced it behind a disclosure.
- Graph: the shocked asset on the left, wrappers, markets, vaults and curators to the right, each hop coloured by how far it sits from the shock (amber at the first layer, red at the second).
- Vaults hit: a ranked list with vault, curator, hop count, vault TVL and dollars lost.
- Agent: a chat that runs shocks, reads a vault's exposure, walks a path and drafts the cap cut and reallocation; each answer cites the paths and figures its tools returned.
- Past scenarios: the saved runs with asset, haircut, vaults hit and total loss.

## States (empty, loading, error, success)

- Empty: the stats strip shows the live graph counts (markets, vaults, TVL); the asset list is searchable and the Run button stays disabled until an asset is chosen.
- Loading: Run shock shows the running state beside the button and the headline holds its previous figure until the new one lands.
- Error: a failed shock, path, scenario or agent call prints the server message in an error line beside the control that failed.
- Success: headline, graph and ranked list share one result; the Cypher disclosure shows the statements that were run.

## Visual system

Dark teal ground (#07131a) with panel #0c1f29 and text #e6f1f5. Accent #3ee0c5 for actions, amber #f4a259 for first-layer loss and red #e4572e for second-layer loss, so colour carries distance from the shock. Figures set in IBM Plex Mono with tabular numerals, the headline scaling with the viewport. Controls use 4px radii and a short ease-out press response. The page holds at 375 and 1440 pixel widths.
