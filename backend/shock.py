"""Propagate a price shock on one asset through wrappers, markets and nested vaults.

Loss model, per market whose collateral is hit: bad debt = max(0, borrow - collateral * (1 - haircut)),
the instant-depeg case where liquidations cannot clear in time. Bad debt is split across supplying
vaults by their share of market supply, then carried up every vault-of-vault edge by
allocation / child TVL. Vault share tokens used as collateral elsewhere take the vault's loss
ratio as their own haircut, which is how a loss jumps from one vault into an unrelated market.
"""
import time
import uuid

MAX_ROUNDS = 3

Q_WRAPPERS = """
MATCH (s:Asset) WHERE toLower(s.symbol) = toLower($symbol)
MATCH p = (w:Asset)-[:WRAPS*0..4]->(s)
RETURN w.address, w.symbol, length(p), [n IN nodes(p) | n.symbol]
"""

Q_MARKETS = """
MATCH (v:Vault)-[al:ALLOCATES]->(m:Market)-[:COLLATERAL]->(a:Asset)
WHERE a.address IN $addrs
MATCH (m)-[:LENDS]->(l:Asset)
RETURN m.id, m.label, m.borrowUsd, m.supplyUsd, m.collateralUsd, a.address, a.symbol, l.symbol,
       v.address, v.symbol, v.tvlUsd, al.usd
"""

Q_NESTED = """
MATCH p = (parent:Vault)-[:ALLOCATES*1..4]->(child:Vault)
WHERE child.address IN $addrs
RETURN parent.address, parent.symbol, parent.tvlUsd, child.address,
       reduce(x = 1.0, i IN range(0, size(relationships(p)) - 1) |
              x * relationships(p)[i].usd / nodes(p)[i + 1].tvlUsd) AS ratio,
       [n IN nodes(p) | n.symbol], length(p)
"""

Q_SHARES = """
MATCH (a:Asset)-[:SHARE_OF]->(v:Vault) WHERE v.address IN $addrs
RETURN a.address, a.symbol, v.address
"""

Q_CURATORS = """
MATCH (c:Curator)-[:CURATES]->(v:Vault) WHERE v.address IN $addrs
RETURN v.address, collect(c.name)
"""


def _market_loss(borrow: float, supply: float, collateral: float, haircut: float) -> float:
    borrow = min(borrow or 0.0, supply or 0.0)
    return max(0.0, borrow - (collateral or 0.0) * (1.0 - haircut))


def run_shock(g, symbol: str, haircut: float) -> dict:
    haircut = max(0.0, min(1.0, float(haircut)))
    cypher = [Q_WRAPPERS.strip(), Q_MARKETS.strip(), Q_NESTED.strip(), Q_SHARES.strip()]
    wrap = g.query(Q_WRAPPERS, {"symbol": symbol}).result_set
    if not wrap:
        raise ValueError(f"No asset named {symbol} in the graph")

    # asset address -> (haircut, hops so far, path labels ending at the shocked asset)
    hit_assets = {}
    for addr, sym, hops, chain in wrap:
        hit_assets[addr] = (haircut, hops, list(reversed(chain)))
    direct_addrs = {addr for addr, sym, hops, _ in wrap if hops == 0}

    vault_loss, vault_info, markets_out = {}, {}, {}
    direct_vaults, direct_loss = set(), 0.0
    frontier = dict(hit_assets)
    for _ in range(MAX_ROUNDS):
        if not frontier:
            break
        rows = g.query(Q_MARKETS, {"addrs": list(frontier)}).result_set
        new_vaults = {}
        by_market = {}
        for mid, label, borrow, supply, coll, a_addr, a_sym, l_sym, v_addr, v_sym, v_tvl, al_usd in rows:
            h, hops, chain = frontier[a_addr]
            loss = _market_loss(borrow, supply, coll, h)
            by_market[mid] = (label, a_sym, l_sym, loss)
            share = min(1.0, (al_usd or 0) / supply) if supply else 0.0
            v_loss = loss * share
            if v_loss <= 0:
                continue
            path = chain + [f"market {label}", v_sym]
            vault_loss[v_addr] = vault_loss.get(v_addr, 0.0) + v_loss
            prev = vault_info.get(v_addr)
            if prev is None or hops + 1 < prev["hops"]:
                vault_info[v_addr] = {"symbol": v_sym, "tvl_usd": v_tvl, "hops": hops + 1, "path": path}
            new_vaults[v_addr] = v_loss
            if a_addr in direct_addrs:
                direct_vaults.add(v_addr)
                direct_loss += v_loss
        for mid, (label, a_sym, l_sym, loss) in by_market.items():
            if loss > 0:
                markets_out[mid] = {"id": mid, "collateral": a_sym, "loan": l_sym, "loss_usd": loss}

        nested = g.query(Q_NESTED, {"addrs": list(new_vaults)}).result_set if new_vaults else []
        for p_addr, p_sym, p_tvl, c_addr, ratio, chain_syms, depth in nested:
            add = new_vaults[c_addr] * min(1.0, ratio or 0.0)
            if add <= 0:
                continue
            vault_loss[p_addr] = vault_loss.get(p_addr, 0.0) + add
            base = vault_info[c_addr]
            hops = base["hops"] + depth
            prev = vault_info.get(p_addr)
            if prev is None or hops < prev["hops"]:
                vault_info[p_addr] = {"symbol": p_sym, "tvl_usd": p_tvl, "hops": hops,
                                      "path": base["path"] + list(reversed(chain_syms[:-1]))}

        # Vault share tokens posted as collateral carry the vault's loss into the next round.
        frontier = {}
        if new_vaults:
            for a_addr, a_sym, v_addr in g.query(Q_SHARES, {"addrs": list(vault_loss)}).result_set:
                tvl = vault_info[v_addr]["tvl_usd"] or 0
                if tvl and a_addr not in hit_assets:
                    h = min(1.0, vault_loss[v_addr] / tvl)
                    entry = (h, vault_info[v_addr]["hops"] + 1, vault_info[v_addr]["path"] + [a_sym])
                    frontier[a_addr] = hit_assets[a_addr] = entry

    curators = dict(g.query(Q_CURATORS, {"addrs": list(vault_loss)}).result_set) if vault_loss else {}
    hits = sorted(
        ({"vault": a, "symbol": vault_info[a]["symbol"], "curator": ", ".join(curators.get(a, [])) or None,
          "loss_usd": round(l, 2), "tvl_usd": vault_info[a]["tvl_usd"], "hops": vault_info[a]["hops"],
          "path": vault_info[a]["path"]} for a, l in vault_loss.items()),
        key=lambda h: -h["loss_usd"])
    total = sum(h["loss_usd"] for h in hits)

    scenario_id = uuid.uuid4().hex[:8]
    g.query("CREATE (:Scenario {id:$id, asset:$asset, haircut:$h, createdAt:$t, totalLossUsd:$total, "
            "directVaults:$dv, graphVaults:$gv})",
            {"id": scenario_id, "asset": symbol, "h": haircut, "t": int(time.time()), "total": total,
             "dv": len(direct_vaults), "gv": len(hits)})
    if hits:
        g.query("MATCH (s:Scenario {id:$id}) UNWIND $rows AS r MATCH (v:Vault {address:r.vault}) "
                "CREATE (s)-[:HITS {lossUsd:r.loss, hops:r.hops, path:r.path}]->(v)",
                {"id": scenario_id, "rows": [{"vault": h["vault"], "loss": h["loss_usd"], "hops": h["hops"],
                                              "path": " → ".join(h["path"])} for h in hits]})
    return {
        "scenario_id": scenario_id, "asset": symbol, "haircut": haircut, "total_loss_usd": round(total, 2),
        "direct": {"vaults": len(direct_vaults), "loss_usd": round(direct_loss, 2)},
        "graph": {"vaults": len(hits), "loss_usd": round(total, 2)},
        "hits": hits,
        "markets": sorted(markets_out.values(), key=lambda m: -m["loss_usd"]),
        "cypher": cypher,
    }
