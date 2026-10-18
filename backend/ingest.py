"""Load Morpho mainnet vaults, markets, assets and wrapper edges into FalkorDB.

Source of truth: blue-api.morpho.org/graphql (public) and ERC4626 asset() reads over RPC.
Run: uv run python -m backend.ingest
"""
import json
import os
import re
import time
import urllib.request

from backend.db import get_graph

API = "https://blue-api.morpho.org/graphql"
CHAIN = 1
MIN_USD = 10_000


def gql(query: str) -> dict:
    req = urllib.request.Request(API, data=json.dumps({"query": query}).encode(),
                                 headers={"content-type": "application/json"})
    for attempt in range(5):
        try:
            body = json.load(urllib.request.urlopen(req, timeout=90))
        except Exception as e:
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))
            continue
        if "errors" in body:
            raise RuntimeError(f"Morpho API error: {body['errors'][:2]}")
        return body["data"]


def paged(field: str, selection: str, page: int) -> list:
    out, skip = [], 0
    while True:
        d = gql('{ %s(first:%d, skip:%d, where:{chainId_in:[%d]}){ pageInfo{countTotal} items{ %s } } }'
                % (field, page, skip, CHAIN, selection))[field]
        out += d["items"]
        skip += page
        if not d["items"] or skip >= d["pageInfo"]["countTotal"]:
            return out


ASSET = "address symbol price{usd} vault{address}"
MARKET = ("marketId lltv collateralAsset{%s} loanAsset{%s} "
          "state{supplyAssetsUsd borrowAssetsUsd collateralAssetsUsd} badDebt{usd}") % (ASSET, ASSET)
V1 = ("address symbol name listed state{ totalAssetsUsd curators{name} "
      "allocation{ supplyAssetsUsd market{marketId} } }")
V2 = ("address symbol name listed totalAssetsUsd curators{ items{ name } } "
      "adapters{ items{ __typename assetsUsd "
      "... on MetaMorphoAdapter{ metaMorpho{address} } "
      "... on MorphoVaultV2Adapter{ innerVault{address} } "
      "... on MorphoMarketV1Adapter{ positions(first:10){ items{ market{marketId} state{supplyAssetsUsd} } } } } }")


def erc4626_underlying(addresses: list[str]) -> dict[str, str]:
    """asset() selector 0x38d52e0f over JSON-RPC batch. Returns token -> underlying (lowercase)."""
    key = os.environ.get("ALCHEMY_API_KEY")
    rpc = os.environ.get("ETH_RPC_URL") or (f"https://eth-mainnet.g.alchemy.com/v2/{key}" if key else None)
    if not rpc:
        raise RuntimeError("Set ETH_RPC_URL or ALCHEMY_API_KEY to resolve wrapper edges")
    out = {}
    for i in range(0, len(addresses), 50):
        chunk = addresses[i:i + 50]
        batch = [{"jsonrpc": "2.0", "id": j, "method": "eth_call",
                  "params": [{"to": a, "data": "0x38d52e0f"}, "latest"]} for j, a in enumerate(chunk)]
        req = urllib.request.Request(rpc, data=json.dumps(batch).encode(),
                                     headers={"content-type": "application/json"})
        for r in json.load(urllib.request.urlopen(req, timeout=60)):
            res = r.get("result") or ""
            if len(res) == 66 and int(res, 16) != 0:
                out[chunk[r["id"]].lower()] = "0x" + res[-40:].lower()
    return out


def erc20_symbols(addresses: list[str]) -> dict[str, str]:
    """symbol() selector 0x95d89b41; decodes ABI string or bytes32."""
    key = os.environ.get("ALCHEMY_API_KEY")
    rpc = os.environ.get("ETH_RPC_URL") or (f"https://eth-mainnet.g.alchemy.com/v2/{key}" if key else None)
    batch = [{"jsonrpc": "2.0", "id": j, "method": "eth_call",
              "params": [{"to": a, "data": "0x95d89b41"}, "latest"]} for j, a in enumerate(addresses)]
    req = urllib.request.Request(rpc, data=json.dumps(batch).encode(), headers={"content-type": "application/json"})
    out = {}
    for r in json.load(urllib.request.urlopen(req, timeout=60)):
        raw = bytes.fromhex((r.get("result") or "0x")[2:])
        if len(raw) >= 96:
            n = int.from_bytes(raw[32:64], "big")
            out[addresses[r["id"]]] = raw[64:64 + n].decode(errors="ignore")
        elif len(raw) == 32:
            out[addresses[r["id"]]] = raw.rstrip(b"\0").decode(errors="ignore")
    return out


def pt_underlying(symbol: str, by_symbol: dict[str, str]) -> str | None:
    m = re.match(r"^PT-(.+?)-\d{1,2}[A-Z]{3}\d{4}$", symbol)
    return by_symbol.get(m.group(1).lower()) if m else None


def cached(name: str, fetch):
    os.makedirs("data", exist_ok=True)
    path = f"data/morpho_{name}.json"
    if os.environ.get("UNDERTOW_REFRESH") != "1" and os.path.exists(path):
        return json.load(open(path))
    rows = fetch()
    json.dump(rows, open(path, "w"))
    return rows


def main():
    t0 = time.time()
    markets = {m["marketId"]: m for m in cached("markets", lambda: paged("markets", MARKET, 500))}
    v1 = cached("v1", lambda: paged("vaults", V1, 100))
    v2 = cached("v2", lambda: paged("vaultV2s", V2, 5))
    print(f"fetched markets={len(markets)} v1={len(v1)} v2={len(v2)} in {time.time()-t0:.0f}s", flush=True)

    vaults, alloc_vm, alloc_vv, curates = {}, [], [], []
    for v in v1:
        tvl = (v["state"] or {}).get("totalAssetsUsd") or 0
        if tvl < MIN_USD:
            continue
        a = v["address"].lower()
        vaults[a] = {"address": a, "symbol": v["symbol"], "name": v["name"], "version": "v1",
                     "tvlUsd": tvl, "listed": bool(v["listed"])}
        for c in v["state"]["curators"] or []:
            curates.append({"curator": c["name"], "vault": a})
        for al in v["state"]["allocation"] or []:
            usd = min(al["supplyAssetsUsd"] or 0, tvl)
            if usd >= MIN_USD and al["market"]["marketId"] in markets:
                alloc_vm.append({"vault": a, "market": al["market"]["marketId"], "usd": usd})
    for v in v2:
        tvl = v.get("totalAssetsUsd") or 0
        if tvl < MIN_USD:
            continue
        a = v["address"].lower()
        vaults[a] = {"address": a, "symbol": v["symbol"], "name": v["name"], "version": "v2",
                     "tvlUsd": tvl, "listed": bool(v["listed"])}
        for c in (v.get("curators") or {}).get("items") or []:
            curates.append({"curator": c["name"], "vault": a})
        for ad in (v.get("adapters") or {}).get("items") or []:
            kind = ad["__typename"]
            if kind == "MetaMorphoAdapter" and ad.get("metaMorpho"):
                alloc_vv.append({"parent": a, "child": ad["metaMorpho"]["address"].lower(),
                                 "usd": min(ad.get("assetsUsd") or 0, tvl)})
            elif kind == "MorphoVaultV2Adapter" and ad.get("innerVault"):
                alloc_vv.append({"parent": a, "child": ad["innerVault"]["address"].lower(),
                                 "usd": min(ad.get("assetsUsd") or 0, tvl)})
            elif kind == "MorphoMarketV1Adapter":
                for p in (ad.get("positions") or {}).get("items") or []:
                    usd = min((p.get("state") or {}).get("supplyAssetsUsd") or 0, tvl)
                    if usd >= MIN_USD and p["market"]["marketId"] in markets:
                        alloc_vm.append({"vault": a, "market": p["market"]["marketId"], "usd": usd})
    alloc_vv = [e for e in alloc_vv if e["child"] in vaults and e["usd"] >= MIN_USD]

    used = {e["market"] for e in alloc_vm}
    mrows, assets = [], {}
    for mid in used:
        m = markets[mid]
        if not m["collateralAsset"]:
            continue
        s = m["state"] or {}
        for side in ("collateralAsset", "loanAsset"):
            x = m[side]
            assets[x["address"].lower()] = {"address": x["address"].lower(), "symbol": x["symbol"],
                                            "priceUsd": (x.get("price") or {}).get("usd") or 0,
                                            "shareOf": ((x.get("vault") or {}).get("address") or "").lower()}
        mrows.append({"id": mid, "lltv": int(m["lltv"]) / 1e18,
                      "supplyUsd": s.get("supplyAssetsUsd") or 0, "borrowUsd": s.get("borrowAssetsUsd") or 0,
                      "collateralUsd": s.get("collateralAssetsUsd") or 0,
                      "badDebtUsd": (m.get("badDebt") or {}).get("usd") or 0,
                      "collateral": m["collateralAsset"]["address"].lower(),
                      "loan": m["loanAsset"]["address"].lower(),
                      "label": f'{m["collateralAsset"]["symbol"]}/{m["loanAsset"]["symbol"]}'})

    wraps = []
    under = cached("wraps", lambda: erc4626_underlying(sorted(assets)))
    by_symbol = {a["symbol"].lower(): addr for addr, a in assets.items()}
    for addr, a in list(assets.items()):
        u = under.get(addr) or pt_underlying(a["symbol"], by_symbol)
        if u and u != addr:
            if u not in assets:
                assets[u] = {"address": u, "symbol": u[:10], "priceUsd": 0, "shareOf": ""}
            wraps.append({"wrapper": addr, "underlying": u})
    unknown = sorted(a for a, x in assets.items() if x["symbol"] == a[:10])
    if unknown:
        for a, sym in cached("symbols", lambda: erc20_symbols(unknown)).items():
            if sym:
                assets[a]["symbol"] = sym

    g = get_graph()
    try:
        g.delete()
    except Exception as e:
        if "empty key" not in str(e).lower() and "invalid graph" not in str(e).lower():
            raise
    g = get_graph()
    for label, key in (("Asset", "address"), ("Vault", "address"), ("Market", "id"), ("Curator", "name")):
        try:
            g.query(f"CREATE INDEX FOR (n:{label}) ON (n.{key})")
        except Exception as e:
            if "already indexed" not in str(e):
                raise
    g.query("UNWIND $rows AS r MERGE (a:Asset {address:r.address}) SET a.symbol=r.symbol, a.priceUsd=r.priceUsd",
            {"rows": list(assets.values())})
    g.query("UNWIND $rows AS r CREATE (:Vault {address:r.address, symbol:r.symbol, name:r.name, "
            "version:r.version, tvlUsd:r.tvlUsd, listed:r.listed})", {"rows": list(vaults.values())})
    g.query("UNWIND $rows AS r MATCH (c:Asset {address:r.collateral}), (l:Asset {address:r.loan}) "
            "CREATE (m:Market {id:r.id, label:r.label, lltv:r.lltv, supplyUsd:r.supplyUsd, borrowUsd:r.borrowUsd, "
            "collateralUsd:r.collateralUsd, badDebtUsd:r.badDebtUsd}) "
            "CREATE (m)-[:COLLATERAL]->(c) CREATE (m)-[:LENDS]->(l)", {"rows": mrows})
    g.query("UNWIND $rows AS r MATCH (v:Vault {address:r.vault}), (m:Market {id:r.market}) "
            "CREATE (v)-[:ALLOCATES {usd:r.usd}]->(m)", {"rows": alloc_vm})
    g.query("UNWIND $rows AS r MATCH (p:Vault {address:r.parent}), (c:Vault {address:r.child}) "
            "CREATE (p)-[:ALLOCATES {usd:r.usd}]->(c)", {"rows": alloc_vv})
    g.query("UNWIND $rows AS r MATCH (w:Asset {address:r.wrapper}), (u:Asset {address:r.underlying}) "
            "MERGE (w)-[:WRAPS]->(u)", {"rows": wraps})
    g.query("UNWIND $rows AS r MATCH (a:Asset {address:r.address}), (v:Vault {address:r.shareOf}) "
            "MERGE (a)-[:SHARE_OF]->(v)", {"rows": [a for a in assets.values() if a["shareOf"]]})
    g.query("UNWIND $rows AS r MERGE (c:Curator {name:r.curator}) WITH c, r MATCH (v:Vault {address:r.vault}) "
            "MERGE (c)-[:CURATES]->(v)", {"rows": curates})

    counts = g.query("MATCH (n) RETURN labels(n)[0], count(n)").result_set
    rels = g.query("MATCH ()-[r]->() RETURN type(r), count(r)").result_set
    print("nodes", counts, "\nrels", rels, f"\nwraps resolved={len(wraps)} total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
