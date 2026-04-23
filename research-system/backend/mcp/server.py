from fastmcp import FastMCP
from backend.graph import queries as graph
from backend.db.client import get_pool
from backend.db import queries as db
from backend.graph.community import run_louvain, find_structural_holes

mcp = FastMCP("research-kg")

_VALID_NODE_TYPES = {"Paper", "Entity", "Community"}
_VALID_EDGE_TYPES = {"MENTIONS", "RELATED_TO", "CITES", "SIMILAR_TO"}


# ---------------------------------------------------------------------------
# Task 3.2 — add_node and add_edge
# ---------------------------------------------------------------------------

@mcp.tool()
async def add_node(id: str, type: str, properties: dict | None = None) -> dict:
    """Add or update a node in the research knowledge graph.
    type must be one of: Paper, Entity, Community.
    properties is merged into the node (id is always set from the id parameter).
    """
    if type not in _VALID_NODE_TYPES:
        return {"error": f"Invalid node type '{type}'. Must be one of: {sorted(_VALID_NODE_TYPES)}"}
    await graph.upsert_node(id, type, properties or {})
    return {"status": "ok", "id": id}


@mcp.tool()
async def add_edge(
    source: str,
    target: str,
    type: str,
    weight: float = 1.0,
    properties: dict | None = None,
) -> dict:
    """Add or update an edge between two nodes.
    type must be one of: MENTIONS, RELATED_TO, CITES, SIMILAR_TO.
    """
    if type not in _VALID_EDGE_TYPES:
        return {"error": f"Invalid edge type '{type}'. Must be one of: {sorted(_VALID_EDGE_TYPES)}"}
    await graph.upsert_edge(source, target, type, weight, properties or {})
    return {"status": "ok", "source": source, "target": target}


# ---------------------------------------------------------------------------
# Task 3.3 — get_neighbors and find_path
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_neighbors(
    node_id: str, depth: int = 1, edge_types: list[str] | None = None
) -> dict:
    """Return all nodes and edges within `depth` hops of node_id.
    Optionally filter by edge_types (e.g. ["CITES", "SIMILAR_TO"]).
    Returns {"nodes": [...], "edges": [...]}.
    """
    return await graph.get_neighbors(node_id, depth, edge_types or None)


@mcp.tool()
async def find_path(source_id: str, target_id: str, max_hops: int = 4) -> list[dict]:
    """Return the shortest path between two nodes as a list of node dicts.
    Returns empty list if no path exists within max_hops.
    """
    return await graph.find_path(source_id, target_id, max_hops)


# ---------------------------------------------------------------------------
# Task 3.4 — get_community
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_community(node_id: str) -> dict:
    """Return the Louvain community that this node belongs to.
    Runs community detection, then returns the community_id and up to 50 member node IDs.
    Returns {"error": "node not found"} if the node has no community assignment.
    """
    communities = await run_louvain()
    node_community = next(
        (c for c in communities if c["node_id"] == node_id), None
    )
    if not node_community:
        return {"error": "node not found"}
    community_id = node_community["community_id"]
    members = [c["node_id"] for c in communities if c["community_id"] == community_id]
    return {"community_id": community_id, "member_ids": members[:50]}


# ---------------------------------------------------------------------------
# Task 3.5 — find_bridges
# ---------------------------------------------------------------------------

@mcp.tool()
async def find_bridges(community_a: int, community_b: int) -> list[dict]:
    """Find nodes that connect community_a and community_b.
    Returns list of node dicts (papers or entities) that have edges into both communities.
    Requires community_id to be set on nodes (run get_community first to trigger Louvain).
    """
    return await graph.find_bridges(community_a, community_b)


# ---------------------------------------------------------------------------
# Task 3.6 — find_structural_holes
# ---------------------------------------------------------------------------

@mcp.tool()
async def find_structural_holes_tool() -> list[dict]:
    """Identify pairs of research clusters with no cross-edges (structural holes).
    These represent research gaps — areas where no one has bridged two communities.
    Returns list of {community_a, community_b, size_a, size_b}, ordered by total size.
    Requires community_id to be set on nodes (run get_community first to trigger Louvain).
    """
    return await find_structural_holes()


# ---------------------------------------------------------------------------
# Task 3.7 — get_subgraph and semantic_search
# ---------------------------------------------------------------------------

@mcp.tool()
async def get_subgraph(node_ids: list[str]) -> dict:
    """Return all nodes and edges induced by the given node_ids.
    Used to extract a subgraph for visualization or downstream context.
    Returns {"nodes": [...], "edges": [...]}.
    """
    return await graph.get_subgraph(node_ids)


@mcp.tool()
async def semantic_search(query: str, limit: int = 10) -> list[dict]:
    """Search the research graph by semantic similarity to the query string.
    Embeds the query with voyage-large-2 and returns the top matching papers.
    Returns list of {paper_id, title, score}.
    """
    from backend.ingestion.embed import embed_texts
    pool = await get_pool()
    embeddings = await embed_texts([query])
    return await db.find_similar_papers(pool, embeddings[0], limit=limit, threshold=0.0)


if __name__ == "__main__":
    mcp.run(transport="stdio")
