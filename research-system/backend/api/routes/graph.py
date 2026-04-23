import logging
from fastapi import APIRouter, Query
from backend.graph import queries as graph
from backend.db.client import get_pool
from backend.db import queries as db
from backend.ingestion.embed import embed_texts

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/full")
async def get_full_graph() -> dict:
    """Return all nodes and edges for the 3D visualization initial load."""
    return await graph.get_full_graph_for_visualization()


@router.get("/search")
async def search_graph(q: str = Query(..., min_length=1)) -> list[dict]:
    """Semantic search over papers. Embeds query with voyage-large-2, returns top matches."""
    from fastapi import HTTPException
    try:
        pool = await get_pool()
        embeddings = await embed_texts([q])
        results = await db.find_similar_papers(pool, embeddings[0], limit=20, threshold=0.0)
        return results
    except Exception as exc:
        logger.error("Search failed for query %r: %s", q, exc)
        raise HTTPException(status_code=503, detail="Search temporarily unavailable — embedding service may be rate-limited. Try again in 20 seconds.")


@router.get("/subgraph")
async def get_subgraph(node_ids: str = Query(...)) -> dict:
    """Return nodes and edges induced by a comma-separated list of node IDs."""
    ids = [nid.strip() for nid in node_ids.split(",") if nid.strip()]
    if not ids:
        return {"nodes": [], "edges": []}
    return await graph.get_subgraph(ids)
