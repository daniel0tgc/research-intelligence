import logging
import re
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.db.client import get_pool
from backend.db import queries as db
from backend.config import settings

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


@router.get("/{paper_id}/card")
async def get_paper_card(paper_id: str) -> dict:
    """
    Return a structured card for the side panel:
    paper metadata + top 3 connections from connection report + external links.
    """
    pool = await get_pool()
    row = await db.get_paper(pool, paper_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

    # Build external links
    arxiv_url = None
    if row.get("arxiv_id"):
        arxiv_url = f"https://arxiv.org/abs/{row['arxiv_id']}"
    elif row.get("source_url"):
        arxiv_url = row["source_url"]

    semantic_scholar_url = (
        f"https://www.semanticscholar.org/search?q={row['title'].replace(' ', '+')}&sort=Relevance"
    )

    # Try Semantic Scholar API to get a real paper URL
    if not arxiv_url and row.get("title"):
        try:
            headers = {}
            if settings.semantic_scholar_api_key:
                headers["x-api-key"] = settings.semantic_scholar_api_key
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    "https://api.semanticscholar.org/graph/v1/paper/search",
                    params={"query": row["title"], "fields": "externalIds,url", "limit": 1},
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    if data:
                        ext = data[0].get("externalIds", {})
                        if ext.get("ArXiv"):
                            arxiv_url = f"https://arxiv.org/abs/{ext['ArXiv']}"
                        elif ext.get("DOI"):
                            arxiv_url = f"https://doi.org/{ext['DOI']}"
                        semantic_scholar_url = data[0].get("url", semantic_scholar_url)
        except Exception:
            pass

    # Parse top connections from connection report
    top_connections: list[dict] = []
    report_path = settings.reports_dir / "connections" / f"connection_report_{paper_id}.md"
    if report_path.exists():
        report_text = report_path.read_text()
        # Extract neighbor paper titles from the markdown table
        table_rows = re.findall(r'\|\s*"?([^|"]{5,80})"?\s*\|[^|]+\|[^|]+\|', report_text)
        seen = set()
        for title in table_rows[:5]:
            title = title.strip().strip('"')
            if title and title not in seen and "Paper" not in title and "---" not in title:
                seen.add(title)
                top_connections.append({"title": title})

        # Extract community label
        community_match = re.search(r'### Community[:\s]+(.+)', report_text)
        community_label = community_match.group(1).strip() if community_match else None
    else:
        community_label = None

    return {
        "id": str(row["id"]),
        "title": row["title"],
        "authors": row.get("authors") or [],
        "year": row.get("year"),
        "abstract": row.get("abstract") or "",
        "is_read": row.get("is_read", False),
        "arxiv_url": arxiv_url,
        "semantic_scholar_url": semantic_scholar_url,
        "top_connections": top_connections[:3],
        "community_label": community_label,
    }


@router.patch("/{paper_id}/read")
async def mark_as_read(paper_id: str) -> dict:
    """Mark a paper as read and set read_at timestamp."""
    pool = await get_pool()
    paper = await db.get_paper(pool, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")
    await db.mark_paper_read(pool, paper_id)
    return {"status": "ok"}
