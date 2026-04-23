import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db.client import get_pool
from backend.db import queries as db

logger = logging.getLogger(__name__)
router = APIRouter()


class PaperSummary(BaseModel):
    id: str
    title: str
    year: int | None
    is_read: bool


class PaperDetail(BaseModel):
    id: str
    title: str
    authors: list[str] | None
    year: int | None
    abstract: str | None
    doi: str | None
    arxiv_id: str | None
    source_url: str | None
    file_path: str | None
    is_read: bool


@router.get("", response_model=list[PaperSummary])
async def list_papers() -> list[PaperSummary]:
    """Return all papers (id, title, year, is_read)."""
    pool = await get_pool()
    rows = await db.get_all_papers(pool)
    return [PaperSummary(**r) for r in rows]


@router.get("/{paper_id}", response_model=PaperDetail)
async def get_paper(paper_id: str) -> PaperDetail:
    """Return full paper details by ID."""
    pool = await get_pool()
    row = await db.get_paper(pool, paper_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    return PaperDetail(**row)


@router.patch("/{paper_id}/read")
async def mark_as_read(paper_id: str) -> dict:
    """Mark a paper as read and set read_at timestamp."""
    pool = await get_pool()
    paper = await db.get_paper(pool, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    await db.mark_paper_read(pool, paper_id)
    return {"status": "ok"}
