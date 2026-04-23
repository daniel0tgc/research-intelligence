import json
from asyncpg import Pool
from backend.config import settings
from backend.db.queries import insert_concept_mapping


async def normalize_entity_name(name: str, pool: Pool) -> str:
    """Look up name in approved concept_map.json. Return canonical or original."""
    concept_map = _load_concept_map()
    name_lower = name.lower()
    for mapping in concept_map.get("approved", []):
        term_a = mapping.get("term_a", "").lower()
        term_b = mapping.get("term_b", "").lower()
        if name_lower in (term_a, term_b):
            return mapping.get("canonical", mapping.get("term_a", name))
    return name


async def suggest_mappings_for_entities(entities: list[dict], pool: Pool) -> None:
    """Ask Claude to find synonym pairs among new entities. Insert as pending mappings."""
    names = [e["name"] for e in entities]
    if len(names) < 2:
        return
    from backend.ingestion.entities import get_client
    client = get_client()
    prompt = (
        "Given these scientific terms, identify any pairs that are synonymous or "
        "refer to the same concept across different research communities. "
        "Only flag clear synonyms, not vague similarities.\n\n"
        f"Terms: {json.dumps(names)}\n\n"
        "Output ONLY valid JSON: [{\"term_a\": \"string\", \"term_b\": \"string\"}]\n"
        "Output empty array [] if no synonyms found."
    )
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        pairs = json.loads(raw)
    except json.JSONDecodeError:
        return
    for pair in pairs:
        if isinstance(pair, dict) and "term_a" in pair and "term_b" in pair:
            await insert_concept_mapping(pool, pair["term_a"], pair["term_b"], source="llm")


def _load_concept_map() -> dict:
    path = settings.concept_map_path
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"approved": [], "pending": []}
