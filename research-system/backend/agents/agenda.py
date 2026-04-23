"""
Agenda agent: synthesizes weekly research priorities using the knowledge graph
and the user's stated current focus.
"""
import logging
from datetime import datetime, timedelta
from anthropic import AsyncAnthropic
from backend.config import settings
from backend.db.client import get_pool
from backend.db import queries as db
from backend.graph.community import find_structural_holes

logger = logging.getLogger(__name__)

AGENDA_PROMPT = """You are a research strategy advisor for a company builder doing deep research.

Current research priorities:
{priorities}

Papers ingested this week:
{recent_papers}

Top structural holes in the knowledge graph (research gaps):
{gaps}

Synthesize a weekly research agenda:

## This Week's Research Agenda

### Top 3 Gaps to Investigate (ordered by strategic importance)
[For each: what the gap is, why it matters now, one specific action]

### Suggested Reading Order
[5 papers from recent ingestions, ordered by relevance to priorities]

### One Concrete Experiment to Run
[Specific, actionable, tied to the gaps above]

Be direct. No filler. Each recommendation must connect to the priorities stated above."""


async def run_agenda_agent() -> dict:
    """Generate weekly agenda. Returns {"agenda": str}."""
    pool = await get_pool()

    priorities = await db.get_agenda_priorities(pool)
    one_week_ago = datetime.now() - timedelta(days=7)
    recent_papers = await db.get_papers_since(pool, one_week_ago)

    try:
        gaps = await find_structural_holes()
    except Exception as exc:
        logger.warning("Agenda agent: find_structural_holes failed: %s", exc)
        gaps = []

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": AGENDA_PROMPT.format(
            priorities=priorities,
            recent_papers=[
                {"title": p["title"], "is_read": p["is_read"]}
                for p in recent_papers
            ],
            gaps=[
                {
                    "community_a": g["community_a"],
                    "community_b": g["community_b"],
                    "size_a": g["size_a"],
                    "size_b": g["size_b"],
                }
                for g in gaps[:5]
            ],
        )}],
    )
    agenda = message.content[0].text
    logger.info("Agenda generated (%d chars)", len(agenda))
    return {"agenda": agenda}
