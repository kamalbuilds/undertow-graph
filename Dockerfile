FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY backend backend
COPY web web
COPY data/morpho_markets.json data/morpho_v1.json data/morpho_v2.json data/morpho_wraps.json data/morpho_symbols.json data/
ENV FALKORDB_LITE_PATH=/app/data/undertow.db PORT=8080
RUN uv run python -m backend.ingest
EXPOSE 8080
CMD ["uv", "run", "python", "-m", "backend.server"]
