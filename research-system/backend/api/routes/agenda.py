import logging
from fastapi import APIRouter
from pydantic import BaseModel
from backend.db.client import get_pool
from backend.db import queries as db

logger = logging.getLogger(__name__)
router = APIRouter()


class AgendaResponse(BaseModel):
    agenda: str


class PrioritiesRequest(BaseModel):
    content: str


@router.get("", response_model=AgendaResponse)
async def get_agenda() -> AgendaResponse:
    """Run the agenda agent and return a structured weekly research agenda."""
    from backend.agents.agenda import run_agenda_agent
    result = await run_agenda_agent()
    return AgendaResponse(agenda=result["agenda"])


@router.post("/priorities")
async def update_priorities(req: PrioritiesRequest) -> dict:
    """Update the user's research priorities used by the agenda agent."""
    pool = await get_pool()
    await db.update_agenda_priorities(pool, req.content)
    return {"status": "ok"}
