import re

WRITE_CLAUSE = re.compile(r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|CALL\s+db\.)", re.I)


def _rows(res) -> list[dict]:
    names = [h[1] if isinstance(h, (list, tuple)) else str(h) for h in res.header]
    return [dict(zip(names, r)) for r in res.result_set]


def _q(g, cypher: str, params: dict | None = None) -> list[dict]:
    return _rows(g.query(cypher, params or {}))


def stats(g) -> dict:
    c = {r["label"]: r["n"] for r in _q(g, "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS n")}
    edges = _q(g, "MATCH ()-[r]->() RETURN count(r) AS n")[0]["n"]
    tvl = _q(g, "MATCH (v:Vault) WHERE NOT ()-[:ALLOCATES]->(v) RETURN sum(v.tvlUsd) AS t")[0]["t"]
    return {"assets": c.get("Asset", 0), "markets": c.get("Market", 0), "vaults": c.get("Vault", 0),
            "curators": c.get("Curator", 0), "scenarios": c.get("Scenario", 0), "edges": edges,
            "tvl_usd": tvl or 0}


def assets(g) -> list:
    return _q(g, """
        MATCH (m:Market)-[:COLLATERAL]->(a:Asset)
        MATCH (s:Asset) WHERE (a)-[:WRAPS*0..4]->(s)
        WITH s, sum(m.collateralUsd) AS usd
        OPTIONAL MATCH (w:Asset)-[:WRAPS*1..4]->(s)
        RETURN s.symbol AS symbol, s.address AS address, usd AS collateral_usd,
               collect(DISTINCT w.symbol) AS wrapped_by
        ORDER BY collateral_usd DESC""")


def paths(g, vault: str, asset: str) -> dict:
    cypher = """
        MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($asset)
        MATCH (v:Vault {address: toLower($vault)})
        MATCH p = (v)-[:ALLOCATES*1..5]->(:Market)-[:COLLATERAL]->(:Asset)-[:WRAPS*0..4]->(s)
        RETURN p ORDER BY length(p) LIMIT 5"""
    out = []
    for r in _q(g, cypher, {"vault": vault, "asset": asset}):
        p = r["p"]
        edges = p.edges()
        usd = [e.properties.get("usd", 0) or 0 for e in edges] + [None]
        nodes = []
        for i, n in enumerate(p.nodes()):
            props = n.properties
            nodes.append({"label": n.labels[0],
                          "name": props.get("symbol") or props.get("label") or props.get("name") or props.get("id"),
                          "usd": usd[i]})
        out.append(nodes)
    return {"paths": out, "cypher": [cypher.strip()]}


def subgraph(g, symbol: str) -> dict:
    cypher = """
        MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($symbol)
        MATCH p1 = (w:Asset)-[:WRAPS*0..4]->(s)
        MATCH (m:Market)-[:COLLATERAL]->(w)
        MATCH p2 = (v:Vault)-[:ALLOCATES]->(m)
        OPTIONAL MATCH p3 = (:Vault)-[:ALLOCATES*1..3]->(v)
        OPTIONAL MATCH p4 = (:Curator)-[:CURATES]->(v)
        RETURN p1, p2, p3, p4"""
    nodes, edges = {}, {}
    for row in g.query(cypher, {"symbol": symbol}).result_set:
        for path in row:
            if path is None:
                continue
            for n in path.nodes():
                p = n.properties
                nodes[n.id] = {"id": n.id, "label": n.labels[0],
                               "name": p.get("symbol") or p.get("label") or p.get("name"),
                               "usd": p.get("tvlUsd") or p.get("collateralUsd") or 0}
            for e in path.edges():
                edges[e.id] = {"source": e.src_node, "target": e.dest_node, "type": e.relation,
                               "usd": e.properties.get("usd", 0)}
    return {"nodes": list(nodes.values()), "edges": list(edges.values()), "cypher": [cypher.strip()]}


def scenarios(g) -> list:
    return _q(g, """
        MATCH (s:Scenario)
        OPTIONAL MATCH (s)-[h:HITS]->(v:Vault)
        WITH s, v, h ORDER BY h.lossUsd DESC
        RETURN s.id AS id, s.asset AS asset, s.haircut AS haircut, s.createdAt AS created_at,
               s.totalLossUsd AS total_loss_usd, s.directVaults AS direct_vaults,
               s.graphVaults AS graph_vaults, collect(v.symbol)[0..3] AS top_vaults
        ORDER BY created_at DESC LIMIT 20""")


def vault_exposure(g, address: str) -> dict:
    q_v = "MATCH (v:Vault {address: toLower($a)}) OPTIONAL MATCH (c:Curator)-[:CURATES]->(v) " \
          "RETURN v.symbol AS symbol, v.name AS name, v.version AS version, v.tvlUsd AS tvl_usd, collect(c.name) AS curators"
    q_m = """
        MATCH (v:Vault {address: toLower($a)})-[:ALLOCATES*1..4]->(m:Market)-[:COLLATERAL]->(c:Asset)
        OPTIONAL MATCH chain = (c)-[:WRAPS*1..4]->(u:Asset) WHERE NOT (u)-[:WRAPS]->()
        RETURN m.id AS market, m.label AS label, c.symbol AS collateral, m.lltv AS lltv,
               m.borrowUsd AS borrow_usd, m.collateralUsd AS collateral_usd,
               [n IN nodes(chain) | n.symbol] AS wraps_to"""
    q_alloc = "MATCH (v:Vault {address: toLower($a)})-[r:ALLOCATES]->(x) " \
              "RETURN labels(x)[0] AS kind, coalesce(x.label, x.symbol) AS target, r.usd AS usd ORDER BY usd DESC"
    q_par = "MATCH (p:Vault)-[r:ALLOCATES*1..4]->(v:Vault {address: toLower($a)}) " \
            "RETURN DISTINCT p.symbol AS parent, p.address AS address"
    v = _q(g, q_v, {"a": address})
    if not v or v[0]["symbol"] is None:
        return {"error": f"vault {address} not in graph"}
    return {**v[0], "allocations": _q(g, q_alloc, {"a": address}),
            "markets": _q(g, q_m, {"a": address}), "parents": _q(g, q_par, {"a": address}),
            "cypher": [q_v, q_m.strip(), q_alloc, q_par]}


def systemic_assets(g, limit: int = 10) -> list:
    """Assets whose failure reaches the most vault TVL, ranked by betweenness over the exposure graph."""
    reach = _q(g, """
        MATCH (s:Asset)
        MATCH (w:Asset)-[:WRAPS*0..4]->(s)
        MATCH (m:Market)-[:COLLATERAL]->(w)
        MATCH (v:Vault)-[al:ALLOCATES]->(m)
        WITH s, count(DISTINCT v) AS vaults, sum(al.usd) AS usd, count(DISTINCT w) AS wrappers
        RETURN s.symbol AS symbol, vaults, usd AS vault_usd_exposed, wrappers
        ORDER BY usd DESC LIMIT $limit""", {"limit": int(limit)})
    pr = {r["symbol"]: r["score"] for r in _q(g, """
        CALL algo.pageRank(NULL, NULL) YIELD node, score
        WITH node, score WHERE node:Asset
        RETURN node.symbol AS symbol, score""")}
    for r in reach:
        r["pagerank"] = round(pr.get(r["symbol"], 0.0), 6)
    return reach


def run_cypher_readonly(g, cypher: str) -> dict:
    if WRITE_CLAUSE.search(cypher):
        return {"error": "read-only: write clauses are not allowed"}
    res = g.ro_query(cypher)
    names = [h[1] if isinstance(h, (list, tuple)) else str(h) for h in res.header]
    return {"header": names, "rows": [list(r) for r in res.result_set[:200]]}


def curator_actions(g, vault: str, asset: str, haircut: float = 0.3) -> dict:
    """Exposed markets for this vault (direct or through child vaults) and a safe same-loan market for each."""
    q_exposed = """
        MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($asset)
        MATCH (v:Vault {address: toLower($vault)})-[:ALLOCATES*0..3]->(holder:Vault)-[al:ALLOCATES]->(m:Market)
              -[:COLLATERAL]->(c:Asset)-[:WRAPS*0..4]->(s)
        MATCH (m)-[:LENDS]->(loan:Asset)
        RETURN DISTINCT holder.address AS holder, holder.symbol AS holder_symbol, m.id AS market, m.label AS label,
               c.symbol AS collateral, loan.address AS loan, loan.symbol AS loan_symbol, al.usd AS allocated_usd,
               m.borrowUsd AS borrow_usd, m.supplyUsd AS supply_usd, m.collateralUsd AS collateral_usd
        ORDER BY allocated_usd DESC"""
    q_safe = """
        MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($asset)
        MATCH (m:Market)-[:LENDS]->(:Asset {address: $loan})
        MATCH (m)-[:COLLATERAL]->(c:Asset)
        WHERE NOT (c)-[:WRAPS*0..4]->(s) AND m.supplyUsd > 1000000 AND m.borrowUsd < m.supplyUsd * 0.9
        RETURN m.id AS market, m.label AS label, c.symbol AS collateral, m.supplyUsd AS supply_usd,
               m.borrowUsd / m.supplyUsd AS utilization
        ORDER BY m.supplyUsd DESC LIMIT 1"""
    steps = []
    for e in _q(g, q_exposed, {"vault": vault, "asset": asset}):
        borrow = min(e["borrow_usd"] or 0, e["supply_usd"] or 0)
        from backend.shock import _market_loss
        bad = _market_loss(e["borrow_usd"], e["supply_usd"], e["collateral_usd"], haircut)
        share = min(1.0, (e["allocated_usd"] or 0) / e["supply_usd"]) if e["supply_usd"] else 0
        safe = _q(g, q_safe, {"asset": asset, "loan": e["loan"]})
        steps.append({
            "vault": e["holder_symbol"], "vault_address": e["holder"], "market": e["label"], "market_id": e["market"],
            "collateral": e["collateral"], "allocated_usd": round(e["allocated_usd"] or 0, 2),
            "modelled_loss_usd": round(min(bad * share, e["allocated_usd"] or 0), 2),
            "action": "set supply cap to 0 on this market and reallocate",
            "reallocate_to": safe[0] if safe else None,
        })
    return {"vault": vault, "asset": asset, "haircut": haircut, "steps": steps,
            "total_modelled_loss_usd": round(sum(s["modelled_loss_usd"] for s in steps), 2),
            "cypher": [q_exposed.strip(), q_safe.strip()]}
