import httpx
from backend.config import settings

SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"


async def get_citations(
    arxiv_id: str | None, doi: str | None, limit: int = 50
) -> list[dict]:
    """Fetch papers that this paper cites. Returns list of {title, arxiv_id, doi, year}."""
    paper_id = f"arxiv:{arxiv_id}" if arxiv_id else doi
    if not paper_id:
        return []
    headers: dict = {}
    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SCHOLAR_BASE}/paper/{paper_id}/references",
            params={"fields": "title,externalIds,year", "limit": limit},
            headers=headers,
            timeout=15.0,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for ref in data.get("data", []):
            cited = ref.get("citedPaper") or {}
            if not cited:
                continue
            ext = cited.get("externalIds") or {}
            results.append(
                {
                    "title": cited.get("title", ""),
                    "arxiv_id": ext.get("ArXiv"),
                    "doi": ext.get("DOI"),
                    "year": cited.get("year"),
                }
            )
        return results
