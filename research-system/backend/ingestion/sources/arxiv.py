import re
import tempfile
import logging
from pathlib import Path

import arxiv

from backend.ingestion.sources.pdf import ingest_pdf
from backend.db.client import get_pool
from backend.db import queries as db
from backend.graph import queries as graph
from backend.ingestion.scholar import get_citations

logger = logging.getLogger(__name__)

_ARXIV_VERSION_RE = re.compile(r"v\d+$")


def _strip_version(arxiv_id: str) -> str:
    """Remove version suffix from arxiv ID (e.g. '1706.03762v5' → '1706.03762')."""
    return _ARXIV_VERSION_RE.sub("", arxiv_id)


async def ingest_arxiv(arxiv_id: str) -> str:
    """
    Fetch paper metadata + PDF from ArXiv by ID (e.g. '2301.07041').
    Downloads PDF to temp file, runs ingest_pdf, then patches metadata and adds citations.
    Returns paper_id.
    """
    clean_id = _strip_version(arxiv_id)
    search = arxiv.Search(id_list=[clean_id])
    client = arxiv.Client()
    results = list(client.results(search))
    if not results:
        raise ValueError(f"ArXiv paper {clean_id} not found")
    paper = results[0]

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    paper.download_pdf(filename=str(tmp_path))

    paper_id = await ingest_pdf(tmp_path)

    pool = await get_pool()
    await db.update_paper_metadata(
        pool,
        paper_id,
        title=paper.title,
        authors=[str(a) for a in paper.authors],
        year=paper.published.year,
        abstract=paper.summary,
        arxiv_id=clean_id,
    )
    await graph.update_paper_node_metadata(
        paper_id,
        title=paper.title,
        authors=[str(a) for a in paper.authors],
        year=paper.published.year,
        abstract=paper.summary,
        arxiv_id=clean_id,
    )

    # Pull citations from Semantic Scholar (best-effort)
    try:
        citations = await get_citations(arxiv_id=clean_id, doi=None)
        for cited in citations:
            if cited.get("arxiv_id"):
                existing = await db.get_paper_by_arxiv_id(pool, cited["arxiv_id"])
                if existing:
                    await graph.create_citation_edge(paper_id, existing["id"])
    except Exception as exc:
        logger.warning("Citation pull failed for %s: %s", clean_id, exc)

    tmp_path.unlink(missing_ok=True)
    return paper_id
