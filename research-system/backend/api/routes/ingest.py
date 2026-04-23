from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from pydantic import BaseModel

from backend.ingestion.sources.pdf import ingest_pdf
from backend.ingestion.sources.arxiv import ingest_arxiv
from backend.ingestion.sources.url import ingest_url
from backend.ingestion.sources.github import ingest_github_repo

router = APIRouter()


class ArxivRequest(BaseModel):
    arxiv_id: str


class UrlRequest(BaseModel):
    url: str


class GithubRequest(BaseModel):
    repo_url: str


@router.post("/arxiv")
async def ingest_arxiv_route(
    req: ArxivRequest, background_tasks: BackgroundTasks
) -> dict:
    background_tasks.add_task(ingest_arxiv, req.arxiv_id)
    return {"status": "queued", "arxiv_id": req.arxiv_id}


@router.post("/url")
async def ingest_url_route(
    req: UrlRequest, background_tasks: BackgroundTasks
) -> dict:
    background_tasks.add_task(ingest_url, req.url)
    return {"status": "queued", "url": req.url}


@router.post("/github")
async def ingest_github_route(
    req: GithubRequest, background_tasks: BackgroundTasks
) -> dict:
    background_tasks.add_task(ingest_github_repo, req.repo_url)
    return {"status": "queued", "repo_url": req.repo_url}


@router.post("/pdf")
async def ingest_pdf_route(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict:
    import tempfile
    import shutil
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
    background_tasks.add_task(ingest_pdf, tmp_path)
    return {"status": "queued", "filename": file.filename}
