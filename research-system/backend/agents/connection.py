"""
Connection agent: triggered after paper_ingested event.
Finds embedding neighbors, shared entities, community membership,
and generates a connection_report_{paper_id}.md.
"""
import json
import logging
from anthropic import AsyncAnthropic
from backend.config import settings
from backend.db.client import get_pool
from backend.db import queries as db
from backend.graph import queries as graph
from backend.graph.community import run_louvain
from backend.api.events import emit

logger = logging.getLogger(__name__)

CONNECTION_PROMPT = """You are a research intelligence analyst. Given information about a newly ingested paper and its connections in a knowledge graph, write a concise connection analysis.

Paper: {title}
Embedding neighbors (top 5): {neighbors}
Shared concepts: {concepts}
Community: {community}
Bridge papers: {bridges}

Write a connection_report with these sections:
## {title} — Connection Analysis
### Embedding Neighbors (top 5 with similarity scores)
### Shared Concepts
### Community: [name + 1-sentence description]
### Bridge Papers to Other Communities
### Implied Research Directions

Be specific. Use paper titles and concept names. Do not be vague."""


async def run_connection_agent(paper_id: str) -> None:
    """Full connection agent pipeline. Saves report to reports/connections/."""
    pool = await get_pool()
    await emit({"type": "agent_start", "agent": "connection", "paper_id": paper_id})

    paper = await db.get_paper(pool, paper_id)
    if not paper:
        logger.warning("Connection agent: paper %s not found", paper_id)
        return

    # 1. Find embedding neighbors via pgvector
    chunks = await db.get_paper_chunks(pool, paper_id)
    if not chunks:
        logger.warning("Connection agent: no chunks for paper %s", paper_id)
        return

    avg_embedding = [
        sum(x) / len(x)
        for x in zip(*[c["embedding"] for c in chunks])
    ]
    similar = await db.find_similar_papers(pool, avg_embedding, limit=20, threshold=0.0)
    top_5 = [s for s in similar if s["paper_id"] != paper_id][:5]
    await emit({"type": "agent_step", "agent": "connection",
                "step": "neighbors_found", "count": len(similar)})

    # 2. Find shared entities via Neo4j (depth-2 MENTIONS traversal)
    try:
        neighbors = await graph.get_neighbors(paper_id, depth=2, edge_types=["MENTIONS"])
    except Exception as exc:
        logger.warning("Connection agent: get_neighbors failed: %s", exc)
        neighbors = {"nodes": [], "edges": []}

    # 3. Community detection — get this paper's community
    try:
        communities = await run_louvain()
        node_community = next((c for c in communities if c["node_id"] == paper_id), None)
        community_id = node_community["community_id"] if node_community else None
    except Exception as exc:
        logger.warning("Connection agent: Louvain failed: %s", exc)
        community_id = None

    # 4. Build prompt data
    neighbor_titles = [s.get("title", s["paper_id"]) for s in top_5]
    # get_neighbors returns type as lowercase "entity"
    concept_names = [
        n["title"] for n in neighbors.get("nodes", [])
        if n.get("type") == "entity"
    ][:10]

    # 5. Generate report via Claude
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": CONNECTION_PROMPT.format(
            title=paper["title"],
            neighbors=json.dumps(neighbor_titles),
            concepts=json.dumps(concept_names),
            community=f"Community {community_id}" if community_id is not None else "Unassigned",
            bridges="[]",
        )}],
    )
    report_content = message.content[0].text

    # 6. Save report
    report_path = settings.reports_dir / "connections" / f"connection_report_{paper_id}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_content)
    logger.info("Connection report saved: %s", report_path)

    # 7. Create similarity edges for high-scoring neighbors
    for sim in similar[:10]:
        if sim["paper_id"] != paper_id and sim["score"] >= 0.85:
            try:
                await graph.create_similarity_edge(paper_id, sim["paper_id"], sim["score"])
            except Exception as exc:
                logger.warning("Similarity edge failed: %s", exc)

    await emit({"type": "agent_done", "agent": "connection",
                "paper_id": paper_id, "report_path": str(report_path)})
