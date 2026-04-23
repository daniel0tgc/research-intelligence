import asyncio
import voyageai
from backend.config import settings

_client: voyageai.AsyncClient | None = None
# Global semaphore: only one embedding call in flight at a time across all concurrent ingestions
_embed_lock = asyncio.Semaphore(1)


def get_client() -> voyageai.AsyncClient:
    global _client
    if _client is None:
        _client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
    return _client


async def _embed_batch_with_retry(client, batch: list[str], max_retries: int = 5) -> list[list[float]]:
    """Embed one batch with exponential backoff on RateLimitError."""
    delay = 22
    for attempt in range(max_retries):
        try:
            result = await client.embed(batch, model="voyage-large-2")
            return result.embeddings
        except voyageai.error.RateLimitError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)
            delay = min(delay * 2, 120)
    return []


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts using voyage-large-2. Serializes globally to respect 3 RPM free-tier limit."""
    client = get_client()
    all_embeddings: list[list[float]] = []
    batch_size = 8
    for idx, i in enumerate(range(0, len(texts), batch_size)):
        batch = texts[i:i + batch_size]
        async with _embed_lock:
            if idx > 0:
                await asyncio.sleep(22)
            embeddings = await _embed_batch_with_retry(client, batch)
            all_embeddings.extend(embeddings)
    return all_embeddings
