# Research Intelligence

Local-first knowledge graph for academic papers: ingest from ArXiv, URLs, PDFs, or GitHub; explore relationships in a 3D graph; run agents for connection reports, gap analysis, agenda, and paper-grounded chat. Query the graph from Claude Code via MCP.

## Repository layout

| Path | Purpose |
|------|---------|
| [`research-system/`](research-system/) | Application code (backend, frontend, Docker, MCP) |
| [`research-system/CLAUDE.md`](research-system/CLAUDE.md) | Schema, ports, MCP tools, and operational notes |
| [`Context.md`](Context.md) | Full product / build specification |
| [`Done.md`](Done.md) | Phase checklist and completion log |

## Requirements

- **Docker** — PostgreSQL + pgvector and Neo4j (`research-system/docker-compose.yml`)
- **Python 3.11+** with project dependencies (`research-system/backend/requirements.txt`)
- **Node.js 20+** — frontend build and dev server
- **API keys** (see below) — copy [`research-system/.env.example`](research-system/.env.example) to `research-system/.env` and configure

## Quick start

```bash
cd research-system

# 1. Environment
cp .env.example .env
# Edit .env: POSTGRES_URL (use port 5433 if 5432 is taken), Neo4j password, VOYAGE_API_KEY, ANTHROPIC_API_KEY

cp .env.example frontend/.env
# Set VITE_API_URL and VITE_WS_URL (defaults target localhost:8000)

# 2. Databases
docker compose up -d

# 3. Backend (from research-system/, with venv or conda that has deps installed)
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# 4. Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

- **API:** http://localhost:8000  
- **UI:** http://localhost:5173  

Default Neo4j credentials in compose/docs are often `neo4j` / `research123` — align `NEO4J_PASSWORD` in `.env` with your container.

## API keys

| Variable | Used for |
|----------|-----------|
| `VOYAGE_API_KEY` | Chunk embeddings (`voyage-large-2`) |
| `ANTHROPIC_API_KEY` | Entity extraction and agents |
| `SEMANTIC_SCHOLAR_API_KEY` | Optional; improves citation fetch limits |

## MCP (Claude Code)

The knowledge-graph MCP server runs over stdio via `research-system/mcp_wrapper.sh`. Register it in your workspace `.mcp.json` (see `CLAUDE.md` for tool names and examples).

## Documentation

For ingestion modes, graph schema, rate limits (Voyage free tier), and troubleshooting, read **[`research-system/CLAUDE.md`](research-system/CLAUDE.md)** and **[`Debugging.md`](Debugging.md)**.
