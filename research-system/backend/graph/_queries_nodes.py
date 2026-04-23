"""Node and edge creation/mutation operations."""
from backend.graph.client import get_session


async def create_paper_node(
    paper_id: str,
    title: str,
    authors: list[str],
    year: int | None,
    abstract: str,
    doi: str | None,
    arxiv_id: str | None,
) -> None:
    """Create or merge a Paper node."""
    async with get_session() as session:
        await session.run(
            """
            MERGE (p:Paper {id: $id})
            SET p.title = $title, p.authors = $authors, p.year = $year,
                p.abstract = $abstract, p.doi = $doi, p.arxiv_id = $arxiv_id
            """,
            id=paper_id, title=title, authors=authors, year=year,
            abstract=abstract, doi=doi, arxiv_id=arxiv_id,
        )


async def update_paper_node_metadata(
    paper_id: str, title: str, authors: list[str],
    year: int | None, abstract: str, arxiv_id: str | None,
) -> None:
    """Update metadata on an existing Paper node."""
    async with get_session() as session:
        await session.run(
            """
            MATCH (p:Paper {id: $id})
            SET p.title = $title, p.authors = $authors, p.year = $year,
                p.abstract = $abstract, p.arxiv_id = $arxiv_id
            """,
            id=paper_id, title=title, authors=authors,
            year=year, abstract=abstract, arxiv_id=arxiv_id,
        )


async def create_entity_node(name: str, entity_type: str, description: str) -> None:
    """Create or merge an Entity node."""
    async with get_session() as session:
        await session.run(
            "MERGE (e:Entity {name: $name, type: $type}) SET e.description = $description",
            name=name, type=entity_type, description=description,
        )


async def create_mentions_relation(
    paper_id: str, entity_name: str, entity_type: str, confidence: float = 1.0
) -> None:
    """Create MENTIONS edge from Paper to Entity."""
    async with get_session() as session:
        await session.run(
            """
            MATCH (p:Paper {id: $paper_id})
            MATCH (e:Entity {name: $name, type: $type})
            MERGE (p)-[r:MENTIONS]->(e)
            SET r.confidence = $confidence
            """,
            paper_id=paper_id, name=entity_name, type=entity_type, confidence=confidence,
        )


async def create_entity_relation(
    source_name: str, target_name: str, relation_type: str, description: str
) -> None:
    """Create RELATED_TO edge between Entity nodes."""
    async with get_session() as session:
        await session.run(
            """
            MATCH (a:Entity {name: $source})
            MATCH (b:Entity {name: $target})
            MERGE (a)-[r:RELATED_TO]->(b)
            SET r.type = $rel_type, r.description = $description
            """,
            source=source_name, target=target_name,
            rel_type=relation_type, description=description,
        )


async def create_citation_edge(citing_paper_id: str, cited_paper_id: str) -> None:
    """Create CITES edge between Paper nodes."""
    async with get_session() as session:
        await session.run(
            """
            MATCH (a:Paper {id: $citing})
            MATCH (b:Paper {id: $cited})
            MERGE (a)-[:CITES]->(b)
            """,
            citing=citing_paper_id, cited=cited_paper_id,
        )


async def create_similarity_edge(
    paper_id_a: str, paper_id_b: str, score: float
) -> None:
    """Create or update SIMILAR_TO edge between Paper nodes."""
    async with get_session() as session:
        await session.run(
            """
            MATCH (a:Paper {id: $id_a})
            MATCH (b:Paper {id: $id_b})
            MERGE (a)-[r:SIMILAR_TO]->(b)
            SET r.score = $score
            """,
            id_a=paper_id_a, id_b=paper_id_b, score=score,
        )


async def upsert_node(node_id: str, node_type: str, properties: dict) -> None:
    """Add or update a node. Used by MCP add_node tool."""
    props = {k: v for k, v in properties.items() if k != "id"}
    params: dict = {"node_id": node_id, **props}
    set_clause = ", ".join(f"n.{k} = ${k}" for k in props)
    async with get_session() as session:
        query = f"MERGE (n:{node_type} {{id: $node_id}})"
        if set_clause:
            query += f" SET {set_clause}"
        await session.run(query, **params)


async def upsert_edge(
    source_id: str, target_id: str, edge_type: str,
    weight: float, properties: dict,
) -> None:
    """Add or update an edge. Used by MCP add_edge tool."""
    props = {f"p_{k}": v for k, v in properties.items()}
    set_clause = ", ".join(f"r.{k} = $p_{k}" for k in properties)
    params: dict = {"source": source_id, "target": target_id, "weight": weight, **props}
    async with get_session() as session:
        query = f"""
            MATCH (a {{id: $source}})
            MATCH (b {{id: $target}})
            MERGE (a)-[r:{edge_type}]->(b)
            SET r.weight = $weight
        """
        if set_clause:
            query += f" SET {set_clause}"
        await session.run(query, **params)
