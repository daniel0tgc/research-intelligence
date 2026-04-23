import asyncio
import logging
from pathlib import Path

from backend.ingestion.extract import extract_text_from_pdf, extract_metadata_from_pdf
from backend.ingestion.chunk import chunk_text
from backend.ingestion.embed import embed_texts
from backend.ingestion.entities import extract_entities_and_relations
from backend.ingestion.normalize import normalize_entity_name, suggest_mappings_for_entities
from backend.db.client import get_pool
from backend.db import queries as db
from backend.graph import queries as graph
from backend.api.events import emit

logger = logging.getLogger(__name__)


async def ingest_pdf(path: Path) -> str:
    """
    Full ingestion pipeline for a PDF file.
    Returns the paper_id (UUID string).
    Steps: extract → chunk → embed → store pgvector → extract entities →
           normalize → Neo4j nodes → similarity edges → emit event
    """
    pool = await get_pool()

    # 1. Extract text and metadata
    await emit({"type": "ingestion_step", "step": "extracting", "file": str(path)})
    text = extract_text_from_pdf(path)
    meta = extract_metadata_from_pdf(path)

    # 2. Store paper row (get ID)
    paper_id = await db.insert_paper(
        pool,
        title=meta.get("title") or path.stem,
        authors=[a.strip() for a in meta.get("author", "").split(";") if a.strip()],
        year=None,
        abstract="",
        doi=None,
        arxiv_id=None,
        source_url=None,
        file_path=str(path),
    )
    logger.info("Paper row created: %s (%s)", paper_id, path.name)

    # 3. Chunk + embed
    await emit({"type": "ingestion_step", "step": "embedding", "paper_id": paper_id})
    chunks = chunk_text(text)
    if chunks:
        embeddings = await embed_texts([c.text for c in chunks])
        for chunk, embedding in zip(chunks, embeddings):
            await db.insert_chunk(pool, paper_id, chunk.index, chunk.text, embedding)
    else:
        embeddings = []
    logger.info("Embedded %d chunks for paper %s", len(chunks), paper_id)

    # 4. Entity extraction
    await emit({"type": "ingestion_step", "step": "extracting_entities", "paper_id": paper_id})
    try:
        extracted = await extract_entities_and_relations(text)
    except Exception as exc:
        logger.warning("Entity extraction failed for %s: %s", paper_id, exc)
        extracted = {"entities": [], "relations": []}
    entities = extracted.get("entities", [])
    relations = extracted.get("relations", [])

    # 5. Normalize entity names + suggest synonyms
    for entity in entities:
        entity["name"] = await normalize_entity_name(entity["name"], pool)
    try:
        await suggest_mappings_for_entities(entities, pool)
    except Exception as exc:
        logger.warning("Synonym suggestion failed for %s: %s", paper_id, exc)

    # 6. Neo4j paper node
    await graph.create_paper_node(
        paper_id,
        meta.get("title") or path.stem,
        [a.strip() for a in meta.get("author", "").split(";") if a.strip()],
        None, "", None, None,
    )

    # 7. Entity + relation nodes
    for entity in entities:
        await graph.create_entity_node(entity["name"], entity["type"], entity.get("description", ""))
        await graph.create_mentions_relation(paper_id, entity["name"], entity["type"])
    for rel in relations:
        await graph.create_entity_relation(
            rel["source"], rel["target"], rel["type"], rel.get("description", "")
        )

    # 8. Similarity edges (compare against papers already in graph)
    paper_embedding = embeddings[0] if embeddings else []
    if paper_embedding:
        try:
            similar = await db.find_similar_papers(pool, paper_embedding, limit=20, threshold=0.85)
            for sim in similar:
                if sim["paper_id"] != paper_id:
                    await graph.create_similarity_edge(paper_id, sim["paper_id"], sim["score"])
        except Exception as exc:
            logger.warning("Similarity edge creation failed for %s: %s", paper_id, exc)

    await emit({"type": "paper_ingested", "paper_id": paper_id, "title": meta.get("title") or path.stem})

    # 9. Trigger connection agent as background task (Phase 4)
    try:
        from backend.agents.connection import run_connection_agent
        asyncio.create_task(run_connection_agent(paper_id))
    except Exception:
        pass  # agent not yet implemented; skip silently until Phase 4

    return paper_id
