import os
from functools import lru_cache


@lru_cache(maxsize=1)
def client():
    url = os.environ.get("FALKORDB_URL")
    if url:
        from falkordb import FalkorDB
        return FalkorDB.from_url(url)
    from redislite.falkordb_client import FalkorDB
    return FalkorDB(os.environ.get("FALKORDB_LITE_PATH", "data/undertow.db"))


def get_graph(name: str = "undertow"):
    return client().select_graph(name)
