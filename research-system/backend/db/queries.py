from datetime import datetime
from asyncpg import Pool


async def insert_paper(
    pool: Pool,
    title: str,
    authors: list[str],
    year: int | None,
    abstract: str,
    doi: str | None,
    arxiv_id: str | None,
    source_url: str | None,
    file_path: str | None,
) -> str:
    """Insert a paper row. Returns the new paper UUID as string."""
    row = await pool.fetchrow(
        """
        INSERT INTO papers (title, authors, year, abstract, doi, arxiv_id, source_url, file_path)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id::text
        """,
        title,
        authors,
        year,
        abstract,
        doi,
        arxiv_id,
        source_url,
        file_path,
    )
    return row["id"]


async def update_paper_metadata(
    pool: Pool,
    paper_id: str,
    title: str,
    authors: list[str],
    year: int | None,
    abstract: str,
    arxiv_id: str | None,
) -> None:
    """Overwrite authoritative metadata fields on an existing paper row."""
    await pool.execute(
        """
        UPDATE papers
        SET title = $2, authors = $3, year = $4, abstract = $5, arxiv_id = $6
        WHERE id = $1::uuid
        """,
        paper_id,
        title,
        authors,
        year,
        abstract,
        arxiv_id,
    )


async def insert_chunk(
    pool: Pool,
    paper_id: str,
    chunk_index: int,
    text: str,
    embedding: list[float],
) -> str:
    """Insert a chunk with its embedding. Returns chunk UUID."""
    from pgvector.asyncpg import register_vector
    async with pool.acquire() as conn:
        await register_vector(conn)
        row = await conn.fetchrow(
            """
            INSERT INTO chunks (paper_id, chunk_index, text, embedding)
            VALUES ($1::uuid, $2, $3, $4)
            RETURNING id::text
            """,
            paper_id,
            chunk_index,
            text,
            embedding,
        )
    return row["id"]


async def find_similar_chunks(
    pool: Pool, embedding: list[float], limit: int = 20
) -> list[dict]:
    """Return top-N chunks by cosine similarity."""
    from pgvector.asyncpg import register_vector
    async with pool.acquire() as conn:
        await register_vector(conn)
        rows = await conn.fetch(
            """
            SELECT c.id::text, c.paper_id::text, c.chunk_index, c.text,
                   1 - (c.embedding <=> $1) AS score
            FROM chunks c
            ORDER BY c.embedding <=> $1
            LIMIT $2
            """,
            embedding,
            limit,
        )
    return [dict(r) for r in rows]


async def find_similar_papers(
    pool: Pool,
    embedding: list[float],
    limit: int = 20,
    threshold: float = 0.85,
) -> list[dict]:
    """Return paper_ids of papers whose best chunk exceeds threshold similarity."""
    from pgvector.asyncpg import register_vector
    async with pool.acquire() as conn:
        await register_vector(conn)
        rows = await conn.fetch(
            """
            SELECT p.id::text AS paper_id, p.title,
                   MAX(1 - (c.embedding <=> $1)) AS score
            FROM chunks c
            JOIN papers p ON p.id = c.paper_id
            GROUP BY p.id, p.title
            HAVING MAX(1 - (c.embedding <=> $1)) >= $3
            ORDER BY score DESC
            LIMIT $2
            """,
            embedding,
            limit,
            threshold,
        )
    return [dict(r) for r in rows]


async def mark_paper_read(pool: Pool, paper_id: str) -> None:
    await pool.execute(
        "UPDATE papers SET is_read = TRUE, read_at = NOW() WHERE id = $1::uuid",
        paper_id,
    )


async def get_paper(pool: Pool, paper_id: str) -> dict | None:
    row = await pool.fetchrow(
        """
        SELECT id::text, title, authors, year, abstract, doi, arxiv_id,
               source_url, file_path, is_read, read_at, ingested_at
        FROM papers WHERE id = $1::uuid
        """,
        paper_id,
    )
    return dict(row) if row else None


async def get_paper_by_arxiv_id(pool: Pool, arxiv_id: str) -> dict | None:
    row = await pool.fetchrow(
        "SELECT id::text, title, arxiv_id FROM papers WHERE arxiv_id = $1",
        arxiv_id,
    )
    return dict(row) if row else None


async def get_all_papers(pool: Pool) -> list[dict]:
    rows = await pool.fetch(
        "SELECT id::text, title, year, is_read, ingested_at FROM papers ORDER BY ingested_at DESC"
    )
    return [dict(r) for r in rows]


async def get_papers_since(pool: Pool, since: datetime) -> list[dict]:
    rows = await pool.fetch(
        """
        SELECT id::text, title, year, is_read, ingested_at
        FROM papers WHERE ingested_at >= $1 ORDER BY ingested_at DESC
        """,
        since,
    )
    return [dict(r) for r in rows]


async def get_paper_chunks(pool: Pool, paper_id: str) -> list[dict]:
    """Return all chunks for a paper including their embeddings."""
    from pgvector.asyncpg import register_vector
    async with pool.acquire() as conn:
        await register_vector(conn)
        rows = await conn.fetch(
            """
            SELECT id::text, chunk_index, text, embedding
            FROM chunks WHERE paper_id = $1::uuid ORDER BY chunk_index
            """,
            paper_id,
        )
    return [dict(r) for r in rows]


async def insert_concept_mapping(
    pool: Pool, term_a: str, term_b: str, source: str = "llm"
) -> str:
    """Insert a pending concept mapping. Returns UUID. Silently ignores duplicates."""
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO concept_mappings (term_a, term_b, source)
            VALUES ($1, $2, $3)
            ON CONFLICT (term_a, term_b) DO NOTHING
            RETURNING id::text
            """,
            term_a,
            term_b,
            source,
        )
        return row["id"] if row else ""
    except Exception:
        return ""


async def get_pending_concept_mappings(pool: Pool) -> list[dict]:
    rows = await pool.fetch(
        "SELECT id::text, term_a, term_b, status, source, created_at FROM concept_mappings WHERE status = 'pending' ORDER BY created_at"
    )
    return [dict(r) for r in rows]


async def update_concept_mapping_status(
    pool: Pool, mapping_id: str, status: str
) -> None:
    await pool.execute(
        "UPDATE concept_mappings SET status = $2, reviewed_at = NOW() WHERE id = $1::uuid",
        mapping_id,
        status,
    )


async def get_agenda_priorities(pool: Pool) -> str:
    row = await pool.fetchrow(
        "SELECT content FROM agenda_priorities ORDER BY updated_at DESC LIMIT 1"
    )
    return row["content"] if row else ""


async def update_agenda_priorities(pool: Pool, content: str) -> None:
    await pool.execute(
        """
        UPDATE agenda_priorities SET content = $1, updated_at = NOW()
        WHERE id = '00000000-0000-0000-0000-000000000001'::uuid
        """,
        content,
    )
