"""Shock every collateral root asset and compare a symbol-match alert with graph traversal.
Run: uv run python -m backend.sweep [haircut]"""
import sys

from backend.db import get_graph
from backend.queries import assets
from backend.shock import run_shock

haircut = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
g = get_graph()
rows = []
for a in assets(g):
    r = run_shock(g, a["symbol"], haircut)
    rows.append((a["symbol"], r["direct"]["vaults"], r["direct"]["loss_usd"], r["graph"]["vaults"],
                 r["graph"]["loss_usd"], max([h["hops"] for h in r["hits"]] or [0]), r["scenario_id"]))
g.query("MATCH (s:Scenario) WHERE s.id IN $ids DETACH DELETE s", {"ids": [r[6] for r in rows]})
rows.sort(key=lambda r: -(r[4] - r[2]))
print(f"{'asset':<12}{'alert vaults':>13}{'alert $M':>10}{'graph vaults':>14}{'graph $M':>10}{'hops':>6}")
for s, dv, dl, gv, gl, hops, _ in rows[:15]:
    print(f"{s:<12}{dv:>13}{dl/1e6:>10.2f}{gv:>14}{gl/1e6:>10.2f}{hops:>6}")
