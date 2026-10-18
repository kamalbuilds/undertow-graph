"""Self-check for shock propagation on a hand-built graph. Run: uv run python -m backend.test_shock

Graph: USR <-WRAPS- wstUSR. Market M1 (wstUSR collateral) and M2 (USR collateral).
Vault A supplies M1, vault B supplies M2, V2 vault P allocates into A. Share token pA of P
is collateral in M3, supplied by vault C.
"""
import os
import tempfile

os.environ["FALKORDB_LITE_PATH"] = os.path.join(tempfile.mkdtemp(), "t.db")

from backend.db import get_graph  # noqa: E402
from backend.shock import run_shock  # noqa: E402

g = get_graph("shock_test")
g.query("""
CREATE (usr:Asset {address:'usr', symbol:'USR'}), (wst:Asset {address:'wst', symbol:'wstUSR'}),
       (usdc:Asset {address:'usdc', symbol:'USDC'}), (pa:Asset {address:'pa', symbol:'pA'}),
       (wst)-[:WRAPS]->(usr),
       (m1:Market {id:'m1', label:'wstUSR/USDC', borrowUsd:90.0, supplyUsd:100.0, collateralUsd:120.0}),
       (m2:Market {id:'m2', label:'USR/USDC', borrowUsd:50.0, supplyUsd:100.0, collateralUsd:60.0}),
       (m3:Market {id:'m3', label:'pA/USDC', borrowUsd:40.0, supplyUsd:40.0, collateralUsd:50.0}),
       (m1)-[:COLLATERAL]->(wst), (m2)-[:COLLATERAL]->(usr), (m3)-[:COLLATERAL]->(pa),
       (m1)-[:LENDS]->(usdc), (m2)-[:LENDS]->(usdc), (m3)-[:LENDS]->(usdc),
       (a:Vault {address:'a', symbol:'A', tvlUsd:100.0}), (b:Vault {address:'b', symbol:'B', tvlUsd:100.0}),
       (p:Vault {address:'p', symbol:'P', tvlUsd:50.0}), (c:Vault {address:'c', symbol:'C', tvlUsd:40.0}),
       (a)-[:ALLOCATES {usd:100.0}]->(m1), (b)-[:ALLOCATES {usd:100.0}]->(m2),
       (p)-[:ALLOCATES {usd:50.0}]->(a), (c)-[:ALLOCATES {usd:40.0}]->(m3),
       (pa)-[:SHARE_OF]->(p)
""")

r = run_shock(g, "USR", 0.5)
loss = {h["symbol"]: h["loss_usd"] for h in r["hits"]}
print(r["direct"], r["graph"], loss)

# M1: 90 - 120*0.5 = 30, all to A. M2: 50 - 60*0.5 = 20, all to B.
assert abs(loss["A"] - 30) < 1e-6, loss
assert abs(loss["B"] - 20) < 1e-6, loss
# P holds 50 of A's 100 TVL -> 15.
assert abs(loss["P"] - 15) < 1e-6, loss
# pA haircut = 15/50 = 0.3; M3: 40 - 50*0.7 = 5 -> C.
assert abs(loss["C"] - 5) < 1e-6, loss
# Symbol-match alert sees only B.
assert r["direct"]["vaults"] == 1 and r["graph"]["vaults"] == 4, r
assert max(h["hops"] for h in r["hits"]) >= 3
assert g.query("MATCH (:Scenario)-[h:HITS]->() RETURN count(h)").result_set[0][0] == 4
g.delete()
print("shock self-check PASS")
