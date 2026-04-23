import re
import logging

import httpx

from backend.ingestion.sources.url import ingest_url
from backend.ingestion.sources.arxiv import ingest_arxiv

logger = logging.getLogger(__name__)

ARXIV_PATTERN = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", re.IGNORECASE)
PDF_LINK_PATTERN = re.compile(r"https?://\S+\.pdf", re.IGNORECASE)


async def ingest_github_repo(repo_url: str) -> list[str]:
    """
    Fetch a GitHub repo's README and extract linked papers.
    Returns list of paper_ids ingested.
    Handles ArXiv links and direct PDF links found in the README.
    """
    raw_url = repo_url.rstrip("/")
    if "github.com" in raw_url:
        raw_url = raw_url.replace("github.com", "raw.githubusercontent.com")
        raw_url += "/main/README.md"

    readme = ""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(raw_url)
        if resp.status_code != 200:
            resp = await client.get(raw_url.replace("/main/", "/master/"))
        if resp.status_code == 200:
            readme = resp.text
        else:
            logger.warning("Could not fetch README from %s (status %d)", repo_url, resp.status_code)
            return []

    paper_ids: list[str] = []
    seen: set[str] = set()

    for arxiv_id in ARXIV_PATTERN.findall(readme):
        if arxiv_id not in seen:
            seen.add(arxiv_id)
            try:
                pid = await ingest_arxiv(arxiv_id)
                paper_ids.append(pid)
            except Exception as exc:
                logger.warning("ArXiv ingest failed for %s: %s", arxiv_id, exc)

    for pdf_url in PDF_LINK_PATTERN.findall(readme):
        if pdf_url not in seen:
            seen.add(pdf_url)
            try:
                pid = await ingest_url(pdf_url)
                paper_ids.append(pid)
            except Exception as exc:
                logger.warning("URL ingest failed for %s: %s", pdf_url, exc)

    return paper_ids
