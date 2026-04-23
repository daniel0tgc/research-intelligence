import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ReportContent(BaseModel):
    content: str


@router.get("/connection/{paper_id}", response_model=ReportContent)
async def get_connection_report(paper_id: str) -> ReportContent:
    """Return the connection report markdown for a given paper, or empty string if not yet generated."""
    report_path = settings.reports_dir / "connections" / f"connection_report_{paper_id}.md"
    if not report_path.exists():
        return ReportContent(content="")
    return ReportContent(content=report_path.read_text())


@router.post("/gaps")
async def trigger_gap_report(background_tasks: BackgroundTasks) -> dict:
    """Queue the gap agent to run in the background. Returns immediately."""
    from backend.agents.gap import run_gap_agent
    background_tasks.add_task(run_gap_agent)
    return {"status": "queued"}


@router.get("/gaps/latest", response_model=ReportContent)
async def get_latest_gap_report() -> ReportContent:
    """Return the most recently generated gap report, or empty string if none exists yet."""
    gaps_dir = settings.reports_dir / "gaps"
    if not gaps_dir.exists():
        return ReportContent(content="")
    reports = sorted(gaps_dir.glob("gap_report_*.md"), reverse=True)
    if not reports:
        return ReportContent(content="")
    return ReportContent(content=reports[0].read_text())
