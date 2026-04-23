import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db.client import get_pool
from backend.db import queries as db
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
    """Return all pending concept mappings awaiting approval."""
    pool = await get_pool()
    rows = await db.get_pending_concept_mappings(pool)
    return [ConceptMapping(**r) for r in rows]


@router.post("/{mapping_id}/approve")
async def approve_concept(mapping_id: str) -> dict:
    """Approve a concept mapping: update DB status and write to concept_map.json."""
    pool = await get_pool()
    rows = await db.get_pending_concept_mappings(pool)
    mapping = next((r for r in rows if r["id"] == mapping_id), None)
    if not mapping:
        raise HTTPException(status_code=404, detail="Concept mapping not found")

    await db.update_concept_mapping_status(pool, mapping_id, "approved")

    # Persist to concept_map.json
    concept_map_path = settings.concept_map_path
    try:
        concept_map: dict = json.loads(concept_map_path.read_text())
    except Exception:
        concept_map = {"approved": [], "pending": []}

    concept_map.setdefault("approved", []).append({
        "term_a": mapping["term_a"],
        "term_b": mapping["term_b"],
        "canonical": mapping["term_a"],
    })
    concept_map_path.write_text(json.dumps(concept_map, indent=2))
    logger.info("Approved concept mapping: %s ↔ %s", mapping["term_a"], mapping["term_b"])
    return {"status": "approved"}


@router.post("/{mapping_id}/reject")
async def reject_concept(mapping_id: str) -> dict:
    """Reject a concept mapping."""
    pool = await get_pool()
    await db.update_concept_mapping_status(pool, mapping_id, "rejected")
    return {"status": "rejected"}
