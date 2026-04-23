"""Graph traversal and search operations."""
from backend.graph.client import get_session


async def get_neighbors(
    node_id: str, depth: int = 1, edge_types: list[str] | None = None
) -> dict:
    """Return nodes and edges within depth hops of node_id."""
    async with get_session() as session:
        if edge_types:
            type_filter = "|".join(edge_types)
            result = await session.run(
                f"""
                MATCH path = (start {{id: $node_id}})-[r:{type_filter}*1..{depth}]-(neighbor)
                WITH collect(DISTINCT start) + collect(DISTINCT neighbor) AS all_nodes,
                     [rel IN relationships(path) | rel] AS all_rels
                UNWIND all_nodes AS n
                WITH collect(DISTINCT {{
                    id: coalesce(n.id, toString(id(n))),
                    title: coalesce(n.title, n.name, ''),
                    type: CASE WHEN 'Paper' IN labels(n) THEN 'paper' ELSE 'entity' END,
                    community_id: n.community_id}}) AS nodes, all_rels
                UNWIND all_rels AS r2
                RETURN nodes,
                       collect(DISTINCT {{
                           source: coalesce(startNode(r2).id, toString(id(startNode(r2)))),
                           target: coalesce(endNode(r2).id, toString(id(endNode(r2)))),
                           type: type(r2)}}) AS edges
                """,
                node_id=node_id,
            )
        else:
            result = await session.run(
                f"""
                MATCH path = (start {{id: $node_id}})-[*1..{depth}]-(neighbor)
                WITH collect(DISTINCT start) + collect(DISTINCT neighbor) AS all_nodes,
                     [rel IN relationships(path) | rel] AS all_rels
                UNWIND all_nodes AS n
                WITH collect(DISTINCT {{
                    id: coalesce(n.id, toString(id(n))),
                    title: coalesce(n.title, n.name, ''),
                    type: CASE WHEN 'Paper' IN labels(n) THEN 'paper' ELSE 'entity' END,
                    community_id: n.community_id}}) AS nodes, all_rels
                UNWIND all_rels AS r2
                RETURN nodes,
                       collect(DISTINCT {{
                           source: coalesce(startNode(r2).id, toString(id(startNode(r2)))),
                           target: coalesce(endNode(r2).id, toString(id(endNode(r2)))),
                           type: type(r2)}}) AS edges
                """,
                node_id=node_id,
            )
        record = await result.single()
        if not record:
            return {"nodes": [], "edges": []}
        return {"nodes": record["nodes"], "edges": record["edges"]}


async def find_path(source_id: str, target_id: str, max_hops: int = 4) -> list[dict]:
    """Return shortest path between two nodes as list of node dicts."""
    async with get_session() as session:
        result = await session.run(
            """
            MATCH path = shortestPath(
                (a {id: $source})-[*1..$max_hops]-(b {id: $target})
            )
            UNWIND nodes(path) AS n
            RETURN collect({
                id: coalesce(n.id, toString(id(n))),
                title: coalesce(n.title, n.name, ''),
                type: CASE WHEN 'Paper' IN labels(n) THEN 'paper' ELSE 'entity' END
            }) AS path_nodes
            """,
            source=source_id, target=target_id, max_hops=max_hops,
        )
        record = await result.single()
        return record["path_nodes"] if record else []


async def get_subgraph(node_ids: list[str]) -> dict:
    """Return all nodes and edges induced by the given node_ids."""
    async with get_session() as session:
        result = await session.run(
            """
            MATCH (n) WHERE n.id IN $ids
            OPTIONAL MATCH (n)-[r]-(m) WHERE m.id IN $ids
            WITH collect(DISTINCT {
                    id: n.id,
                    title: coalesce(n.title, n.name, ''),
                    type: CASE WHEN 'Paper' IN labels(n) THEN 'paper' ELSE 'entity' END,
                    community_id: n.community_id}) AS nodes,
                 collect(DISTINCT {
                    source: coalesce(startNode(r).id, ''),
                    target: coalesce(endNode(r).id, ''),
                    type: type(r)}) AS edges
            RETURN nodes, edges
            """,
            ids=node_ids,
        )
        record = await result.single()
        if not record:
            return {"nodes": [], "edges": []}
        edges = [e for e in record["edges"] if e.get("source") and e.get("target")]
        return {"nodes": record["nodes"], "edges": edges}


async def get_full_graph_for_visualization() -> dict:
    """Return all nodes and edges. For frontend initial load."""
    async with get_session() as session:
        node_result = await session.run(
            """
            MATCH (n) WHERE n.id IS NOT NULL
            RETURN n.id AS id,
                   coalesce(n.title, n.name, '') AS title,
                   CASE WHEN 'Paper' IN labels(n) THEN 'paper' ELSE 'entity' END AS type,
                   n.year AS year, n.is_read AS is_read, n.community_id AS community_id
            """
        )
        nodes = [dict(r) async for r in node_result]
        edge_result = await session.run(
            """
            MATCH (a)-[r]->(b) WHERE a.id IS NOT NULL AND b.id IS NOT NULL
            RETURN a.id AS source, b.id AS target, type(r) AS type,
                   coalesce(r.score, r.confidence, 1.0) AS weight
            """
        )
        edges = [dict(r) async for r in edge_result]
    return {"nodes": nodes, "edges": edges}


async def find_bridges(community_a: int, community_b: int) -> list[dict]:
    """Return nodes that bridge community_a and community_b.
    Requires community_id to be set on nodes (run run_louvain first).
    Returns up to 20 bridge node dicts: {id, title, type}.
    """
    async with get_session() as session:
        result = await session.run(
            """
            MATCH (a)-[]->(bridge)-[]->(b)
            WHERE a.community_id = $ca AND b.community_id = $cb
            RETURN DISTINCT
                bridge.id                   AS id,
                coalesce(bridge.title, bridge.name, '') AS title,
                labels(bridge)[0]           AS type
            LIMIT 20
            """,
            ca=community_a,
            cb=community_b,
        )
        return [dict(r) async for r in result]


async def get_community_papers(community_id: int, limit: int = 10) -> list[dict]:
    """Return papers belonging to a given Louvain community."""
    async with get_session() as session:
        result = await session.run(
            """
            MATCH (p:Paper {community_id: $community_id})
            RETURN p.id AS id, p.title AS title, p.year AS year
            LIMIT $limit
            """,
            community_id=community_id, limit=limit,
        )
        return [dict(r) async for r in result]
