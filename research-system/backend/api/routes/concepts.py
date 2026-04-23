import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db.client import get_pool
from backend.db import queries as db
from backend.graph.client import get_session
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ConceptMapping(BaseModel):
    id: str
    term_a: str
    term_b: str
    status: str
    source: str


@router.get("/pending", response_model=list[ConceptMapping])
async def get_pending_concepts() -> list[ConceptMapping]:
    pool = await get_pool()
    rows = await db.get_pending_concept_mappings(pool)
    return [ConceptMapping(**r) for r in rows]


@router.post("/{mapping_id}/approve")
async def approve_concept(mapping_id: str) -> dict:
    """
    Approve a concept mapping:
    1. Mark approved in DB
    2. Write to concept_map.json
    3. Merge Neo4j entity nodes: rename term_b → term_a (canonical) and merge edges
    """
    pool = await get_pool()
    rows = await db.get_pending_concept_mappings(pool)
    mapping = next((r for r in rows if str(r["id"]) == mapping_id), None)
    if not mapping:
        raise HTTPException(status_code=404, detail="Concept mapping not found")

    canonical = mapping["term_a"]
    alias = mapping["term_b"]

    await db.update_concept_mapping_status(pool, mapping_id, "approved")

    # Persist to concept_map.json
    concept_map_path = settings.concept_map_path
    try:
        concept_map: dict = json.loads(concept_map_path.read_text())
    except Exception:
        concept_map = {"approved": [], "pending": []}
    concept_map.setdefault("approved", []).append({
        "term_a": canonical,
        "term_b": alias,
        "canonical": canonical,
    })
    concept_map_path.write_text(json.dumps(concept_map, indent=2))

    # Merge Neo4j entity nodes: redirect all edges from alias node to canonical node, then delete alias
    try:
        async with get_session() as session:
            # Check if both nodes exist
            result = await session.run(
                "MATCH (a:Entity {name: $canonical}) RETURN a LIMIT 1", canonical=canonical
            )
            has_canonical = await result.single() is not None

            result = await session.run(
                "MATCH (b:Entity {name: $alias}) RETURN b LIMIT 1", alias=alias
            )
            has_alias = await result.single() is not None

            if has_alias and has_canonical:
                # Move all relationships from alias to canonical, then delete alias
                await session.run("""
                    MATCH (alias:Entity {name: $alias})
                    MATCH (canonical:Entity {name: $canonical})
                    CALL apoc.refactor.mergeNodes([canonical, alias], {
                        properties: 'discard',
                        mergeRels: true
                    })
                    YIELD node RETURN node
                """, alias=alias, canonical=canonical)
            elif has_alias and not has_canonical:
                # Just rename the alias node to canonical
                await session.run(
                    "MATCH (e:Entity {name: $alias}) SET e.name = $canonical, e.normalized_name = $canonical",
                    alias=alias, canonical=canonical
                )

            logger.info("Merged Neo4j entity '%s' → '%s'", alias, canonical)
    except Exception as e:
        # APOC may not be installed — fall back to manual redirect
        logger.warning("APOC merge failed, using manual redirect: %s", e)
        try:
            async with get_session() as session:
                # Reconnect all MENTIONS edges pointing to alias → canonical
                await session.run("""
                    MATCH (p:Paper)-[r:MENTIONS]->(alias:Entity {name: $alias})
                    MATCH (canonical:Entity {name: $canonical})
                    MERGE (p)-[:MENTIONS]->(canonical)
                    DELETE r
                """, alias=alias, canonical=canonical)
                # Reconnect RELATED_TO edges
                await session.run("""
                    MATCH (alias:Entity {name: $alias})-[r:RELATED_TO]->(other)
                    MATCH (canonical:Entity {name: $canonical})
                    MERGE (canonical)-[:RELATED_TO]->(other)
                    DELETE r
                """, alias=alias, canonical=canonical)
                await session.run("""
                    MATCH (other)-[r:RELATED_TO]->(alias:Entity {name: $alias})
                    MATCH (canonical:Entity {name: $canonical})
                    MERGE (other)-[:RELATED_TO]->(canonical)
                    DELETE r
                """, alias=alias, canonical=canonical)
                # Delete the alias node
                await session.run(
                    "MATCH (e:Entity {name: $alias}) DETACH DELETE e", alias=alias
                )
        except Exception as inner:
            logger.error("Manual Neo4j merge also failed: %s", inner)

    return {"status": "approved", "canonical": canonical, "merged": alias}


@router.post("/{mapping_id}/reject")
async def reject_concept(mapping_id: str) -> dict:
    pool = await get_pool()
    # Match by string comparison of UUID
    rows = await db.get_pending_concept_mappings(pool)
    mapping = next((r for r in rows if str(r["id"]) == mapping_id), None)
    if not mapping:
        raise HTTPException(status_code=404, detail="Concept mapping not found")
    await db.update_concept_mapping_status(pool, mapping_id, "rejected")
    return {"status": "rejected"}
