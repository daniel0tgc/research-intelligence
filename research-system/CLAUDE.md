# Research Intelligence System — Claude Code Guide

## What This Is

A local-first knowledge graph of academic papers. Papers are ingested from PDFs, ArXiv IDs, URLs,
and GitHub repos. The graph is queryable via MCP tools from any Claude Code session in this
workspace or the parent knowledge-framework repo.

**Services (all local):**
- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:5173`
- MCP Server: stdio via `mcp_wrapper.sh` (registered in `.mcp.json`)
- PostgreSQL: `localhost:5433` (port 5433 — local macOS Postgres owns 5432)
- Neo4j: `localhost:7687` (browser: `localhost:7474`, user: `neo4j`, pass: `research123`)

**Start everything:**
```bash
# From research-system/
docker compose up -d                                          # databases
/opt/anaconda3/bin/python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &
cd frontend && npm run dev &
```

---

## Graph Schema

### Node Types

- `(:Paper {id, title, authors, year, abstract, doi, arxiv_id, community_id, community_label})`
- `(:Entity {name, type, description, normalized_name})`
  - `type` values: `Method` | `Dataset` | `Claim` | `Concept` | `Architecture`

### Relationship Types

| Relationship | Direction | Source | Properties |
|---|---|---|---|
| `MENTIONS` | Paper → Entity | Claude extraction | `confidence` |
| `RELATED_TO` | Entity → Entity | Claude extraction | `description` |
| `CITES` | Paper → Paper | Semantic Scholar | — |
| `SIMILAR_TO` | Paper → Paper | pgvector cosine ≥ 0.85 | `score` |

---

## Available MCP Tools

Call via `mcp__research-kg__<tool_name>`:

| Tool | Parameters | Returns |
|---|---|---|
| `add_node` | `id, type, properties` | `{status, id}` |
| `add_edge` | `source, target, type, weight?, properties?` | `{status, source, target}` |
| `get_neighbors` | `node_id, depth?, edge_types?` | `{nodes, edges}` |
| `find_path` | `source_id, target_id, max_hops?` | `[node, ...]` |
| `get_community` | `node_id` | `{community_id, member_ids}` |
| `find_bridges` | `community_a, community_b` | `[{id, title, type}, ...]` |
| `find_structural_holes_tool` | _(none)_ | `[{community_a, community_b, size_a, size_b}, ...]` |
| `get_subgraph` | `node_ids` | `{nodes, edges}` |
| `semantic_search` | `query, limit?` | `[{paper_id, title, score}, ...]` |

**Examples:**
```
mcp__research-kg__semantic_search({"query": "self-supervised learning", "limit": 5})
mcp__research-kg__get_neighbors({"node_id": "<uuid>", "depth": 2})
mcp__research-kg__find_structural_holes_tool({})
```

---

## Key File Locations

| Purpose | Path |
|---|---|
| Connection reports | `reports/connections/connection_report_{paper_id}.md` |
| Gap reports | `reports/gaps/gap_report_{YYYYMMDD}.md` |
| Concept normalization map | `data/concept_map.json` |
| Research inbox (PDF drop) | `~/research-inbox/` |
| Environment variables | `research-system/.env` (never committed) |
| MCP wrapper script | `research-system/mcp_wrapper.sh` |

---

## Ingestion Sources

| Method | Command / UI |
|---|---|
| Drop PDF | Copy any `.pdf` to `~/research-inbox/` — watcher auto-triggers |
| ArXiv ID | `POST http://localhost:8000/ingest/arxiv {"arxiv_id": "1706.03762"}` |
| PDF URL | `POST http://localhost:8000/ingest/url {"url": "https://..."}` |
| GitHub repo | `POST http://localhost:8000/ingest/github {"repo_url": "https://github.com/..."}` |
| UI ingest bar | Top-left of localhost:5173, supports all four modes |

**Ingestion is always queued** — the API returns `{"status": "queued"}` immediately. Actual
processing runs in background (2–5 min for embedding on Voyage AI free tier, 3 RPM / 10K TPM).
WebSocket events at `ws://localhost:8000/ws` broadcast step progress.

---

## Agent Endpoints

| Agent | Trigger | Output |
|---|---|---|
| Connection agent | Auto-fires after each ingestion | `reports/connections/connection_report_{id}.md` |
| Gap agent | `POST /reports/gaps` | `reports/gaps/gap_report_{date}.md` |
| Agenda agent | `GET /agenda` | JSON `{"agenda": "<markdown>"}` |
| Chat agent | `POST /chat {"paper_id": "<id>", "query": "..."}` | Streaming plain text |

---

## Concept Normalization

The system suggests synonym pairs when ingesting new papers. Approve or reject them at
`localhost:5173` → Concepts tab, or directly in `data/concept_map.json`:

```json
{
  "approved": [{"term_a": "BERT", "term_b": "Bidirectional Encoder Representations", "canonical": "BERT"}],
  "pending": []
}
```

---

## Important Implementation Notes

1. **Python interpreter** — always use `/opt/anaconda3/bin/python`, not `python3` or bare `python`.
   System Python at `/usr/bin/python3` is missing all project packages.

2. **PostgreSQL port is 5433** — local macOS PostgreSQL owns port 5432. All `POSTGRES_URL` values
   must use `localhost:5433`.

3. **Neo4j package is 6.1.0** (spec was 5.19.0), **arxiv package is 3.0.0** (spec was 2.1.0),
   **fastmcp is 3.2.4** (spec was 0.4.1). These are newer — API differences are handled in code.

4. **Voyage AI free tier** — 3 RPM / 10K TPM. Ingesting a single paper takes 2–5 minutes due to
   per-batch rate-limit delays. Upgrade at dashboard.voyageai.com to unlock standard limits.

5. **MCP server uses stdio** — logs write to `/tmp/research-kg-mcp.log`. Check there for startup
   errors. The server must not print anything to stdout (breaks the protocol).

6. **graph/queries.py is a facade** — actual Cypher implementations are split across
   `_queries_nodes.py` (create/merge) and `_queries_search.py` (traversal/search) to stay under
   the 200-line file limit. `queries.py` re-exports all functions.

7. **community_id write-back** — `run_louvain()` in `community.py` writes `community_id` back to
   Neo4j nodes after detection. Structural hole detection requires this to be set first.

---

## Embedding Model

`voyage-large-2` (1536 dims) via Voyage AI REST API. All embeddings stored in PostgreSQL
`chunks.embedding vector(1536)` column with ivfflat cosine index. Batch size: 8 chunks per request
with 21-second inter-batch delay to respect free-tier rate limits.
