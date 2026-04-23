import voyageai
from backend.config import settings

_client: voyageai.AsyncClient | None = None


def get_client() -> voyageai.AsyncClient:
    global _client
    if _client is None:
        _client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using voyage-large-2. Batches in groups of 8 with delay."""
    import asyncio
    client = get_client()
    all_embeddings: list[list[float]] = []
    # Use batch size of 8 to stay within 10K TPM on free tier (~1500 tokens × 8 = 12K).
    # Add a 21-second delay between batches to respect the 3 RPM free-tier limit.
    batch_size = 8
    for idx, i in enumerate(range(0, len(texts), batch_size)):
        if idx > 0:
            await asyncio.sleep(21)
        batch = texts[i : i + batch_size]
        result = await client.embed(batch, model="voyage-large-2")
        all_embeddings.extend(result.embeddings)
    return all_embeddings
