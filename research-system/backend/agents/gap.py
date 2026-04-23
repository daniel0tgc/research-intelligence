"""
Gap agent: finds structural holes between research communities
and generates ranked research proposals saved as gap_report_{date}.md.
Run via POST /reports/gaps.
"""
import logging
from datetime import datetime
from anthropic import AsyncAnthropic
from backend.config import settings
from backend.graph.community import find_structural_holes
from backend.graph import queries as graph
from backend.api.events import emit

logger = logging.getLogger(__name__)

GAP_PROMPT = """You are a research strategy advisor identifying high-value research gaps.

Community A papers: {community_a_papers}
Community B papers: {community_b_papers}

These two research clusters have NO cross-connections in the literature. Identify:
1. What experiment or method would create a meaningful bridge between them?
2. Why hasn't this been done (technical barrier, domain gap, or missed opportunity)?
3. What would the impact be if this gap were filled?

Be specific. Name concrete methods, datasets, or experimental approaches."""


async def run_gap_agent() -> str:
    """Find structural holes and generate gap_report.md. Returns path to report, or empty string if no gaps."""
    await emit({"type": "agent_start", "agent": "gap"})

    holes = await find_structural_holes()
    if not holes:
        logger.info("Gap agent: no structural holes found (need more papers from diverse domains)")
        await emit({"type": "agent_done", "agent": "gap", "report_path": ""})
        return ""

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_sections = [f"# Research Gap Report — {date_str}\n"]

    for i, hole in enumerate(holes[:10]):
        ca_papers = await graph.get_community_papers(hole["community_a"], limit=5)
        cb_papers = await graph.get_community_papers(hole["community_b"], limit=5)

        await emit({"type": "agent_step", "agent": "gap", "gap_index": i,
                    "community_a": hole["community_a"], "community_b": hole["community_b"]})

        try:
            message = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": GAP_PROMPT.format(
                    community_a_papers=[p["title"] for p in ca_papers],
                    community_b_papers=[p["title"] for p in cb_papers],
                )}],
            )
            analysis = message.content[0].text
        except Exception as exc:
            logger.warning("Gap agent: Claude call failed for gap %d: %s", i, exc)
            analysis = f"Analysis unavailable: {exc}"

        report_sections.append(
            f"\n## Gap {i + 1}: Community {hole['community_a']} ↔ Community {hole['community_b']}\n"
        )
        report_sections.append(
            f"**Size:** {hole['size_a']} papers ↔ {hole['size_b']} papers\n"
        )
        report_sections.append(analysis)

    report = "\n".join(report_sections)
    report_path = (
        settings.reports_dir / "gaps" / f"gap_report_{datetime.now().strftime('%Y%m%d')}.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)
    logger.info("Gap report saved: %s", report_path)

    await emit({"type": "agent_done", "agent": "gap", "report_path": str(report_path)})
    return str(report_path)
