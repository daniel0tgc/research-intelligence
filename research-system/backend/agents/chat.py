"""
Embedded chat agent: answers questions about a specific paper or the graph.
Loads paper subgraph as context, streams response via async generator.
"""
import json
import logging
from typing import AsyncGenerator
from anthropic import AsyncAnthropic
from backend.config import settings
from backend.db.client import get_pool
from backend.db import queries as db
from backend.graph import queries as graph
from backend.ingestion.embed import embed_texts

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are a research intelligence assistant with access to a knowledge graph of academic papers. You answer questions about specific papers, their connections to other research, and what they imply for the user's research agenda.

When answering:
- Reference specific paper titles and entity names from the context
- Note connections and contradictions between papers
- If asked about gaps, reference the structural hole information provided
- Be precise and cite evidence from the graph context"""


async def get_paper_context(paper_id: str, query: str) -> str:
    """Build context string from paper data and graph neighborhood for the chat agent."""
    pool = await get_pool()
    paper = await db.get_paper(pool, paper_id)
    if not paper:
        return ""

    try:
        neighbors = await graph.get_neighbors(paper_id, depth=2)
    except Exception as exc:
        logger.warning("Chat agent: get_neighbors failed: %s", exc)
        neighbors = {"nodes": [], "edges": []}

    chunks = await db.get_paper_chunks(pool, paper_id)

    # Find most relevant chunks to the query via embedding similarity
    relevant: list[dict] = []
    if chunks and query:
        try:
            query_embedding = (await embed_texts([query]))[0]
            relevant = await db.find_similar_chunks(pool, query_embedding, limit=5)
        except Exception as exc:
            logger.warning("Chat agent: chunk similarity search failed: %s", exc)

    return json.dumps(
        {
            "paper": {
                "title": paper["title"],
                "abstract": paper["abstract"],
                "authors": paper["authors"],
            },
            "neighbors": neighbors,
            "relevant_passages": [r["text"] for r in relevant],
        },
        indent=2,
    )


async def stream_chat_response(
    paper_id: str | None, query: str
) -> AsyncGenerator[str, None]:
    """Async generator that yields streamed text chunks from Claude."""
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    context = ""
    if paper_id:
        try:
            context = await get_paper_context(paper_id, query)
        except Exception as exc:
            logger.warning("Chat agent: context build failed: %s", exc)

    user_content = f"Context:\n{context}\n\nQuestion: {query}" if context else query
    messages = [{"role": "user", "content": user_content}]

    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=CHAT_SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text
