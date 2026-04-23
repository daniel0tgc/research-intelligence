CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS papers (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title       TEXT NOT NULL,
  authors     TEXT[],
  year        INTEGER,
  abstract    TEXT,
  doi         TEXT UNIQUE,
  arxiv_id    TEXT UNIQUE,
  source_url  TEXT,
  file_path   TEXT,
  is_read     BOOLEAN NOT NULL DEFAULT FALSE,
  read_at     TIMESTAMPTZ,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  neo4j_node_id TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS chunks (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  paper_id    UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  text        TEXT NOT NULL,
  embedding   vector(1536),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS concept_mappings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  term_a      TEXT NOT NULL,
  term_b      TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
  source      TEXT NOT NULL DEFAULT 'llm',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reviewed_at TIMESTAMPTZ,
  UNIQUE(term_a, term_b)
);

CREATE TABLE IF NOT EXISTS agenda_priorities (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content     TEXT NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO agenda_priorities (id, content)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'No priorities set yet. Use /agenda/priorities to set your current research focus.'
)
ON CONFLICT (id) DO NOTHING;
