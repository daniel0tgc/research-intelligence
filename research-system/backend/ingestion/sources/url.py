import tempfile
from pathlib import Path

import httpx

from backend.ingestion.sources.pdf import ingest_pdf


async def ingest_url(url: str) -> str:
    """Download a PDF from a URL and run the standard ingestion pipeline."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            raise ValueError(
                f"URL does not point to a PDF (content-type: {content_type})"
            )
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = Path(tmp.name)
    paper_id = await ingest_pdf(tmp_path)
    tmp_path.unlink(missing_ok=True)
    return paper_id
