import json
from anthropic import AsyncAnthropic
from backend.config import settings

ENTITY_EXTRACTION_PROMPT = """You are a scientific knowledge graph builder.
Extract all of the following from the provided paper text:
(a) methods/models/architectures
(b) datasets
(c) core claims (max 5)
(d) theoretical concepts
(e) explicit relationships between any of the above entities

Output ONLY valid JSON matching this exact schema:
{{
  "entities": [{{"name": "string", "type": "Method|Dataset|Claim|Concept|Architecture", "description": "string"}}],
  "relations": [{{"source": "string", "target": "string", "type": "string", "description": "string"}}]
}}

Paper text:
{text}"""

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def extract_entities_and_relations(text: str) -> dict:
    """Run entity/relation extraction. Returns {"entities": [...], "relations": [...]}"""
    client = get_client()
    truncated = " ".join(text.split()[:8000])
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": ENTITY_EXTRACTION_PROMPT.format(text=truncated),
            }
        ],
    )
    raw = message.content[0].text.strip()
    # Strip markdown code fences if Claude wraps the JSON
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)
