import logging
from backend.graph.client import get_session

logger = logging.getLogger(__name__)


async def run_louvain() -> list[dict]:
    """Run Louvain community detection via Neo4j GDS.
    Projects the graph, streams community assignments, writes community_id
    back to each node, drops the projection, and returns
    list of {node_id, community_id}.
    """
    async with get_session() as session:
        # Silently drop any stale projection from a previous crashed run
        try:
            await session.run("CALL gds.graph.drop('researchGraph', false)")
        except Exception:
            pass

        try:
            await session.run("""
                CALL gds.graph.project('researchGraph', ['Paper', 'Entity'],
                    {MENTIONS:    {orientation: 'UNDIRECTED'},
                     RELATED_TO:  {orientation: 'UNDIRECTED'},
                     SIMILAR_TO:  {orientation: 'UNDIRECTED'}})
            """)

            result = await session.run("""
                CALL gds.louvain.stream('researchGraph')
                YIELD nodeId, communityId
                RETURN gds.util.asNode(nodeId).id AS node_id,
                       communityId                AS community_id
            """)
            records: list[dict] = [
                {"node_id": r["node_id"], "community_id": r["community_id"]}
                async for r in result
                if r["node_id"] is not None
            ]

            # Write community assignments back to nodes so Cypher queries
            # can filter by community_id (required by find_bridges et al.)
            if records:
                await session.run(
                    """
                    UNWIND $assignments AS a
                    MATCH (n {id: a.node_id})
                    SET n.community_id = a.community_id
                    """,
                    assignments=records,
                )

            return records

        except Exception as exc:
            logger.warning("Louvain community detection failed: %s", exc)
            return []
        finally:
            try:
                await session.run("CALL gds.graph.drop('researchGraph', false)")
            except Exception:
                pass


async def find_structural_holes() -> list[dict]:
    """Find community pairs with no cross-edges (structural holes / research gaps).
    Requires community_id to be set on Paper nodes — run run_louvain() first.
    Returns list of {community_a, community_b, size_a, size_b},
    ordered by combined size descending (most significant gaps first).
    """
    async with get_session() as session:
        result = await session.run("""
            MATCH (p:Paper) WHERE p.community_id IS NOT NULL
            WITH p.community_id AS cid, count(p) AS size
            WITH collect({id: cid, size: size}) AS all_communities
            WHERE size(all_communities) > 1
            UNWIND all_communities AS c1
            UNWIND all_communities AS c2
            WITH c1, c2 WHERE c1.id < c2.id
            OPTIONAL MATCH (a:Paper {community_id: c1.id})-[r]-(b:Paper {community_id: c2.id})
            WITH c1, c2, count(r) AS bridge_count
            WHERE bridge_count = 0
            RETURN c1.id AS community_a,
                   c2.id AS community_b,
                   c1.size AS size_a,
                   c2.size AS size_b
            ORDER BY (c1.size + c2.size) DESC
            LIMIT 20
        """)
        return [
            {
                "community_a": r["community_a"],
                "community_b": r["community_b"],
                "size_a": r["size_a"],
                "size_b": r["size_b"],
            }
            async for r in result
        ]
