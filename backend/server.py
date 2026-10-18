"""Undertow HTTP API.

FastAPI surface over the Undertow graph plus the agent endpoint, serving the
static curator console from web/.
"""

from __future__ import annotations

import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import agent
from backend.db import get_graph
from backend.queries import assets, paths, scenarios, stats, subgraph
from backend.shock import run_shock

_graph = None


def graph():
    global _graph
    if _graph is None:
        _graph = get_graph()
    return _graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    graph()
    yield


app = FastAPI(title="Undertow", lifespan=lifespan)


class ShockRequest(BaseModel):
    symbol: str
    haircut: float


class AgentRequest(BaseModel):
    message: str
    session_id: str


@app.get("/api/stats")
def api_stats():
    return stats(graph())


@app.get("/api/assets")
def api_assets():
    return assets(graph())


@app.post("/api/shock")
def api_shock(body: ShockRequest):
    return run_shock(graph(), body.symbol, body.haircut)


@app.get("/api/path")
def api_path(vault: str, asset: str):
    return paths(graph(), vault, asset)


@app.get("/api/subgraph")
def api_subgraph(symbol: str):
    return subgraph(graph(), symbol)


@app.get("/api/scenarios")
def api_scenarios():
    return scenarios(graph())


@app.post("/api/agent")
def api_agent(body: AgentRequest):
    try:
        return agent.chat(body.message, body.session_id)
    except Exception as exc:
        return JSONResponse(status_code=502, content={"error": str(exc)})


app.mount("/", StaticFiles(directory="web", html=True), name="web")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
