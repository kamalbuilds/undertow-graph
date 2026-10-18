"""Undertow risk-analyst agent.

An OpenRouter chat-completions agent with tool calling over the Undertow
FalkorDB graph. Per-session conversation turns are persisted in a dedicated
FalkorDB graph so the analyst keeps memory across requests.
"""

from __future__ import annotations

import json
import os
import re
import time

import httpx

from backend import queries, shock
from backend.db import get_graph

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-2.5-flash"
MAX_TOOL_ROUNDS = 6
HISTORY_LIMIT = 12
SUMMARY_LIMIT = 4000

SESSION_RE = re.compile(r"[^A-Za-z0-9_-]")

SYSTEM_PROMPT = (
    "You are Undertow, a DeFi risk analyst for Morpho vault curators. "
    "You trace how the failure of one asset propagates through wrappers "
    "(WRAPS), vault-share collateral (SHARE_OF) and vault-of-vault "
    "allocations (ALLOCATES) to the vaults and curators ultimately exposed.\n"
    "Rules:\n"
    "- Answer with the concrete graph path and the dollar figures your tools returned.\n"
    "- Never invent numbers, addresses, symbols or paths. Every figure must come "
    "from a tool result in this conversation.\n"
    "- If a tool returns no data, say the data is missing rather than guessing.\n"
    "- Keep answers tight: the exposure, the path, and the recommended curator action.\n"
    "- When the question is open-ended (which asset is riskiest, what should I watch), call "
    "systemic_assets first, then run_shock on the top result at 30% unless told otherwise.\n"
    "- When asked about a vault by symbol, use query_graph to find its address "
    "(MATCH (v:Vault) WHERE v.symbol = '...' RETURN v.address).\n"
    "- For curator actions call draft_curator_action with the vault and the shocked asset, and "
    "state each step: market, dollars allocated, modelled loss, and where to reallocate."
)

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "run_shock",
            "description": (
                "Haircut an asset and trace the losses through the graph to the "
                "vaults and curators ultimately exposed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Asset symbol, e.g. wstUSR"},
                    "haircut": {
                        "type": "number",
                        "description": "Fractional haircut, e.g. 0.2 for a 20% drop",
                    },
                },
                "required": ["symbol", "haircut"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_exposure",
            "description": "Return a vault's live exposure: TVL, markets, nested vaults and assets.",
            "parameters": {
                "type": "object",
                "properties": {"address": {"type": "string", "description": "Vault address"}},
                "required": ["address"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "paths",
            "description": "Return the graph paths connecting a vault to an asset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vault": {"type": "string", "description": "Vault address"},
                    "asset": {"type": "string", "description": "Asset symbol"},
                },
                "required": ["vault", "asset"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "systemic_assets",
            "description": "Rank assets by systemic importance (PageRank over the asset/market graph).",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "How many assets to return"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "past_scenarios",
            "description": "List previously run shock scenarios stored in graph memory.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_graph",
            "description": "Run a read-only Cypher query against the graph. Writes are rejected.",
            "parameters": {
                "type": "object",
                "properties": {"cypher": {"type": "string", "description": "Read-only Cypher"}},
                "required": ["cypher"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_curator_action",
            "description": "For one vault and one shocked asset, list every market where the vault is exposed "
                           "through the asset's wrapper family, the modelled loss there, and a same-loan-asset "
                           "market outside that family to reallocate into. Returns concrete cap and reallocation steps.",
            "parameters": {
                "type": "object",
                "properties": {"vault": {"type": "string", "description": "Vault address"},
                               "asset": {"type": "string", "description": "Shocked asset symbol"},
                               "haircut": {"type": "number", "description": "Price drop as a fraction, 0..1"}},
                "required": ["vault", "asset"],
            },
        },
    },
]


def _sanitize_session_id(session_id: str) -> str:
    cleaned = SESSION_RE.sub("", session_id or "")[:40]
    if not cleaned:
        raise ValueError("session_id must contain at least one of [A-Za-z0-9_-]")
    return cleaned


def _rows(result) -> list[dict]:
    header = getattr(result, "header", None) or []
    names: list[str] = []
    for column in header:
        if isinstance(column, (list, tuple)) and len(column) >= 2:
            names.append(column[1])
        else:
            names.append(str(column))
    rows: list[dict] = []
    for raw in getattr(result, "result_set", None) or []:
        if isinstance(raw, dict):
            rows.append(raw)
        elif isinstance(raw, (list, tuple)):
            rows.append({names[i] if i < len(names) else str(i): v for i, v in enumerate(raw)})
        else:
            rows.append({"value": raw})
    return rows


def _session_graph(session_id: str):
    return get_graph(name=f"session_{session_id}")


def _load_history(session_id: str) -> list[dict]:
    graph = _session_graph(session_id)
    rows = _rows(
        graph.query(
            "MATCH (t:Turn) "
            "RETURN t.i AS i, t.role AS role, t.content AS content "
            "ORDER BY t.i DESC LIMIT $limit",
            {"limit": HISTORY_LIMIT},
        )
    )
    rows.sort(key=lambda row: row.get("i", 0))
    return [
        {"role": row.get("role", "user"), "content": row.get("content", "")}
        for row in rows
        if row.get("content") is not None
    ]


def _append_turn(session_id: str, role: str, content: str) -> None:
    graph = _session_graph(session_id)
    rows = _rows(graph.query("MATCH (t:Turn) RETURN max(t.i) AS m"))
    current = rows[0].get("m") if rows else None
    index = 0 if current is None else int(current) + 1
    graph.query(
        "CREATE (:Turn {i: $i, role: $role, content: $content, ts: $ts})",
        {"i": index, "role": role, "content": content, "ts": time.time()},
    )
    if index > 0:
        graph.query(
            "MATCH (p:Turn {i: $prev}), (t:Turn {i: $i}) CREATE (p)-[:NEXT]->(t)",
            {"prev": index - 1, "i": index},
        )


def _json_text(value) -> str:
    try:
        text = json.dumps(value, default=str)
    except (TypeError, ValueError):
        text = str(value)
    if len(text) > SUMMARY_LIMIT:
        text = text[:SUMMARY_LIMIT] + "...[truncated]"
    return text


def _collect_cypher(result, bucket: list[str]) -> None:
    if not isinstance(result, dict):
        return
    cypher = result.get("cypher")
    if isinstance(cypher, str):
        bucket.append(cypher)
    elif isinstance(cypher, (list, tuple)):
        bucket.extend(statement for statement in cypher if isinstance(statement, str))


def _draft_curator_action(graph, vault: str, asset: str, haircut: float) -> dict:
    return queries.curator_actions(graph, vault, asset, haircut)


def _dispatch(graph, name: str, args: dict, cypher_bucket: list[str]):
    if name == "run_shock":
        result = shock.run_shock(graph, str(args["symbol"]), float(args["haircut"]))
    elif name == "vault_exposure":
        result = queries.vault_exposure(graph, str(args["address"]))
    elif name == "paths":
        result = queries.paths(graph, str(args["vault"]), str(args["asset"]))
    elif name == "systemic_assets":
        result = queries.systemic_assets(graph, int(args.get("limit", 10)))
    elif name == "past_scenarios":
        result = queries.scenarios(graph)
    elif name == "query_graph":
        cypher = str(args["cypher"])
        cypher_bucket.append(cypher)
        result = queries.run_cypher_readonly(graph, cypher)
    elif name == "draft_curator_action":
        result = _draft_curator_action(graph, str(args["vault"]), str(args["asset"]),
                                       float(args.get("haircut", 0.3)))
    else:
        return {"error": f"unknown tool: {name}"}
    _collect_cypher(result, cypher_bucket)
    return result


def _chat_completion(messages: list[dict], api_key: str, model: str, tools=None) -> dict:
    payload: dict = {"model": model, "messages": messages}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    response = httpx.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60.0,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter HTTP {response.status_code}: {response.text}")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"OpenRouter returned invalid JSON: {response.text}") from exc


def _message(data: dict) -> dict:
    try:
        choice = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"Unexpected OpenRouter response: {json.dumps(data, default=str)[:SUMMARY_LIMIT]}"
        ) from exc
    return choice


def chat(message: str, session_id: str) -> dict:
    session = _sanitize_session_id(session_id)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    model = os.environ.get("UNDERTOW_MODEL", DEFAULT_MODEL)
    graph = get_graph()

    tool_calls_out: list[dict] = []
    cypher_out: list[str] = []

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(_load_history(session))
    messages.append({"role": "user", "content": message})

    reply = ""
    for _ in range(MAX_TOOL_ROUNDS):
        choice = _message(_chat_completion(messages, api_key, model, TOOLS))
        calls = choice.get("tool_calls") or []
        if not calls:
            reply = choice.get("content") or ""
            break

        messages.append(
            {
                "role": "assistant",
                "content": choice.get("content") or "",
                "tool_calls": calls,
            }
        )
        for call in calls:
            function = call.get("function") or {}
            name = function.get("name", "")
            raw_args = function.get("arguments") or "{}"
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            except (json.JSONDecodeError, TypeError, ValueError):
                args = {}
            if not isinstance(args, dict):
                args = {}
            try:
                result = _dispatch(graph, name, args, cypher_out)
            except Exception as exc:  # surfaced to the model, never swallowed
                result = {"error": f"{type(exc).__name__}: {exc}"}
            summary = _json_text(result)
            tool_calls_out.append({"name": name, "args": args, "result_summary": summary})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "name": name,
                    "content": summary,
                }
            )

    if not reply:
        reply = _message(_chat_completion(messages, api_key, model)).get("content") or ""

    _append_turn(session, "user", message)
    _append_turn(session, "assistant", reply)

    return {"reply": reply, "tool_calls": tool_calls_out, "cypher": cypher_out}
