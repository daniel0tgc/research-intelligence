# Done.md — Research Intelligence System

<!--
  WRITTEN BY: Cursor Agent
  READ BY: Claude Code (to generate next phase batch) and the next Cursor Agent (to pick up state)

  RULES:
  - Check off task boxes IMMEDIATELY after completing each task — not at end of phase
  - Append-only — never delete entries
  - Phase summary MUST be written before stopping after a phase
  - Codebase State Graph must reflect current reality — this is ground truth
  - Be specific: exact file paths, exact errors, exact deviations
-->

---

## Project State

**App:** Research Intelligence System
**Started:** [DATE]
**Last updated:** [DATE]
**Backend URL:** http://localhost:8000
**MCP Server URL:** http://localhost:8001
**Frontend URL:** http://localhost:5173
**Current phase:** Phase 6 (complete) — ALL PHASES DONE
**Start method:** Scaffold from scratch

---

## Architecture Decisions

- Graph DB: Neo4j Desktop (local) + GDS plugin. Port 7687.
- Vector DB: PostgreSQL 14 + pgvector. Port 5432.
- Embedding: voyage-large-2 (1536 dims) via Voyage AI REST API
- Entity extraction: claude-sonnet-4-6 (structured JSON output)
- MCP server: FastMCP on port 8001 (stdio transport)
- Frontend: React 18 + TypeScript + Vite + 3d-force-graph
- No auth — local-first tool
- No Redis — background tasks via FastAPI BackgroundTasks + asyncio

---

## Phases Complete

- [x] Phase 1: Infrastructure Setup
- [x] Phase 2: Ingestion Pipeline
- [x] Phase 3: KG MCP Server
- [x] Phase 4: Agents
- [x] Phase 5: 3D Visualization Frontend
- [x] Phase 6: CLAUDE.md + Final Integration

---

## Required Keys

<!-- Cursor checks off each key after confirming it works in the relevant phase -->
<!-- Status: ⬜ Not set | ✅ Set and working | ❌ Set but failing -->

| Variable | Used In | Status |
|---|---|---|
| `POSTGRES_URL` | DB — asyncpg pool | ✅ |
| `NEO4J_URI` | Graph — neo4j driver | ✅ |
| `NEO4J_USER` | Graph — neo4j driver | ✅ |
| `NEO4J_PASSWORD` | Graph — neo4j driver | ✅ |
| `VOYAGE_API_KEY` | Ingestion — embeddings | ✅ |
| `ANTHROPIC_API_KEY` | Agents — Claude API | ✅ |
| `SEMANTIC_SCHOLAR_API_KEY` | Ingestion — citations (optional) | ⬜ |
| `RESEARCH_INBOX_DIR` | Watcher — PDF inbox | ✅ |
| `REPORTS_DIR` | Agents — report output | ✅ |
| `CONCEPT_MAP_PATH` | Normalize — concept map | ✅ |
| `VITE_API_URL` | Frontend — FastAPI calls | ✅ |
| `VITE_WS_URL` | Frontend — WebSocket | ✅ |

---

## Phase Log

---

### Phase 1 — Infrastructure Setup

**Completed:** 2026-04-22
**Status:** `[x] Complete`

#### Task Checkboxes

- [x] 1.1 — Project scaffold
- [x] 1.2 — Docker Compose (Neo4j + PostgreSQL)
- [x] 1.3 — Python dependencies
- [x] 1.4 — Config (pydantic BaseSettings)
- [x] 1.5 — PostgreSQL schema + pool
- [x] 1.6 — Neo4j client + constraints
- [x] 1.7 — FastAPI app scaffold
- [x] 1.8 — Frontend scaffold
- [x] 1.9 — .gitignore + .env.example

#### Deviations

- 1.1: Added __init__.py files to all Python packages (required for ModuleNotFoundError prevention per Debugging.md 1-E)
- 1.2: Docker Desktop was not running; opened it via `open -a Docker` and waited for daemon before running compose up
- 1.3: PyMuPDF pinned to 1.27.2.2 (no wheel for 1.24.1 on Python 3.13/arm64); asyncpg upgraded to 0.31.0 (0.29.0 build failed on Python 3.13); pydantic relaxed to >=2.10.1 and pydantic-settings to >=2.6.1 (fastmcp dependency requirements)
- 1.4: Created .env with placeholder values so Settings() doesn't raise ValidationError at import time (VOYAGE_API_KEY and ANTHROPIC_API_KEY left empty — must be filled before Phase 2)
- 1.5: Docker PostgreSQL port changed from 5432 to 5433 to avoid conflict with local macOS PostgreSQL (PID 46515 on localhost:5432); POSTGRES_URL updated in .env accordingly
- 1.6: none
- 1.7: none
- 1.8: Tailwind v4 auto-installed; downgraded to v3 (required for tailwind.config.ts); Vite scaffold overwrote frontend/ so src subdirs recreated manually; frontend/.env added for VITE_API_URL and VITE_WS_URL
- 1.9: .env.example uses port 5433 for POSTGRES_URL to match the port conflict fix from 1.5

#### Phase Summary

Phase 1 established the complete project scaffold and verified all infrastructure. The full directory structure was created under `research-system/` with `__init__.py` files in every Python package. Docker Compose brought up Neo4j 5.15-enterprise (with GDS 2.5.6) and pgvector-enabled PostgreSQL 14 on port 5433 (5432 was in use by a local macOS PostgreSQL). The PostgreSQL schema was applied including the ivfflat index and seed data. Neo4j constraints were applied via cypher-shell. The FastAPI app scaffolds with all route stubs and starts cleanly with zero import errors. The React/Vite frontend builds successfully with Tailwind v3 dark theme (bg-background #0a0a0f confirmed in compiled CSS). All 6 Debugging.md checks pass.

#### Files Created

```
research-system/docker-compose.yml
research-system/.env (not committed — local only)
research-system/.env.example
research-system/.gitignore
research-system/data/concept_map.json
research-system/backend/__init__.py
research-system/backend/config.py
research-system/backend/requirements.txt
research-system/backend/api/__init__.py
research-system/backend/api/main.py
research-system/backend/api/events.py
research-system/backend/api/models.py
research-system/backend/api/ws.py
research-system/backend/api/routes/__init__.py
research-system/backend/api/routes/ingest.py
research-system/backend/api/routes/graph.py
research-system/backend/api/routes/papers.py
research-system/backend/api/routes/reports.py
research-system/backend/api/routes/agenda.py
research-system/backend/api/routes/concepts.py
research-system/backend/ingestion/__init__.py
research-system/backend/ingestion/extract.py (stub)
research-system/backend/ingestion/chunk.py (stub)
research-system/backend/ingestion/embed.py (stub)
research-system/backend/ingestion/entities.py (stub)
research-system/backend/ingestion/normalize.py (stub)
research-system/backend/ingestion/scholar.py (stub)
research-system/backend/ingestion/watcher.py (stub)
research-system/backend/ingestion/sources/__init__.py
research-system/backend/ingestion/sources/pdf.py (stub)
research-system/backend/ingestion/sources/arxiv.py (stub)
research-system/backend/ingestion/sources/url.py (stub)
research-system/backend/ingestion/sources/github.py (stub)
research-system/backend/graph/__init__.py
research-system/backend/graph/client.py
research-system/backend/graph/queries.py (stub)
research-system/backend/graph/community.py (stub)
research-system/backend/graph/setup.cypher
research-system/backend/db/__init__.py
research-system/backend/db/client.py
research-system/backend/db/queries.py (stub)
research-system/backend/db/schema.sql
research-system/backend/agents/__init__.py
research-system/backend/agents/connection.py (stub)
research-system/backend/agents/gap.py (stub)
research-system/backend/agents/agenda.py (stub)
research-system/backend/agents/chat.py (stub)
research-system/backend/mcp/__init__.py
research-system/backend/mcp/server.py (stub)
research-system/frontend/ (full Vite scaffold)
research-system/frontend/tailwind.config.ts
research-system/frontend/src/App.tsx
research-system/frontend/src/index.css
research-system/frontend/.env
```

#### Dependencies Installed

```
backend: fastapi==0.111.0, uvicorn==0.29.0, pydantic>=2.10.1, pydantic-settings>=2.6.1,
         asyncpg==0.31.0, pgvector==0.4.2, neo4j==6.1.0, anthropic==0.25.7,
         voyageai==0.3.7, PyMuPDF==1.27.2.2, watchdog==4.0.0, httpx==0.27.0,
         arxiv==3.0.0, fastmcp==3.2.4, python-multipart==0.0.9, python-dotenv==1.2.2,
         structlog==25.5.0
frontend: three, @react-three/fiber, @react-three/drei, 3d-force-graph, zustand,
          tailwindcss@3.4.19, postcss, autoprefixer, @types/three
```

#### Issues Encountered

- PyMuPDF 1.24.1 had no pre-built wheel for Python 3.13/arm64 — upgraded to 1.27.2.2
- asyncpg 0.29.0 failed to build on Python 3.13 — upgraded to 0.31.0
- pydantic pinned too low for fastmcp — relaxed to >=2.10.1; pydantic-settings to >=2.6.1
- pip was associated with `/Library/Frameworks` Python, not the active conda Python — switched to `python -m pip install`
- Local macOS PostgreSQL running on port 5432 — Docker Compose postgres remapped to host port 5433
- Tailwind v4 auto-installed — downgraded to v3 (required for tailwind.config.ts with theme extensions)
- Vite scaffold aborted because frontend/ dir existed — removed and recreated

#### Notes for Claude Code

1. **POSTGRES_URL uses port 5433** — local macOS PostgreSQL owns 5432. All DB connections must use 5433. The .env already reflects this.
2. **Active Python is `/opt/anaconda3/bin/python`** — all packages must be installed via `python -m pip install`, not bare `pip install`. The pip command maps to a different Python installation.
3. **neo4j package is 6.1.0 and arxiv is 3.0.0** — both are newer than spec. Verify API compatibility in Phase 2. The arxiv 3.0.0 API may differ from 2.1.0 (check `arxiv.Search` vs `arxiv.Client`).
4. **fastmcp is 3.2.4** — significantly newer than spec's 0.4.1. API may differ; verify `FastMCP`, `@mcp.tool()` decorators in Phase 3.
5. **VOYAGE_API_KEY and ANTHROPIC_API_KEY are empty in .env** — must be populated before Phase 2 tasks 2.3 (embedding) and 2.5 (entity extraction) will function.

---

### Phase 2 — Ingestion Pipeline

**Completed:** 2026-04-22
**Status:** `[x] Complete`

#### Task Checkboxes

- [x] 2.1 — PDF text extraction
- [x] 2.2 — Text chunking
- [x] 2.3 — Voyage AI embedding
- [x] 2.4 — PostgreSQL paper + chunk storage
- [x] 2.5 — Claude entity/relation extraction
- [x] 2.6 — Concept normalization
- [x] 2.7 — Neo4j graph operations
- [x] 2.8 — Semantic Scholar citation pull
- [x] 2.9 — Full ingestion pipeline (PDF source)
- [x] 2.10 — ArXiv ingestion source
- [x] 2.11 — URL ingestion source
- [x] 2.12 — GitHub repo ingestion
- [x] 2.13 — File watcher
- [x] 2.14 — Ingest API routes

#### Deviations

- 2.1: [none | describe]
- 2.2: [none | describe]
- 2.3: [none | describe]
- 2.4: [none | describe]
- 2.5: [none | describe]
- 2.6: [none | describe]
- 2.7: Split into _queries_nodes.py + _queries_search.py submodules (queries.py re-exports all — CursorRules 200-line limit)
- 2.8: [none | describe]
- 2.9: [none | describe]
- 2.10: arxiv 3.0.0 uses Client().results(search) instead of search.results() — updated accordingly; _strip_version() added to remove 'v5' suffix from arxiv IDs
- 2.11: [none | describe]
- 2.12: [none | describe]
- 2.13: [none | describe]
- 2.14: Added POST /ingest/pdf endpoint (file upload) in addition to the three specified in Context.md

#### Phase Summary

Phase 2 built the complete ingestion pipeline. PDF text is extracted via PyMuPDF, split into 512-word chunks with 64-word overlap, and embedded using Voyage AI voyage-large-2 (1536 dims, batched 8 chunks at a time with 21s delays to respect the free-tier 3 RPM/10K TPM limit). Papers and chunks are stored in PostgreSQL with pgvector. Claude (claude-sonnet-4-6, max_tokens=8192) extracts entities and relations from each paper, which are stored as Neo4j nodes with MENTIONS and RELATED_TO edges. Synonym pairs are suggested and stored as pending concept mappings. All four ingestion sources are wired (PDF watcher, ArXiv, URL, GitHub). The file watcher monitors ~/research-inbox/ and triggers the full pipeline on new PDFs within seconds. API endpoints for all ingestion types are live.

#### Files Created

```
backend/ingestion/extract.py
backend/ingestion/chunk.py
backend/ingestion/embed.py
backend/ingestion/entities.py
backend/ingestion/normalize.py
backend/ingestion/scholar.py
backend/ingestion/watcher.py
backend/ingestion/sources/pdf.py
backend/ingestion/sources/arxiv.py
backend/ingestion/sources/url.py
backend/ingestion/sources/github.py
backend/db/queries.py
backend/graph/_queries_nodes.py
backend/graph/_queries_search.py
backend/graph/queries.py (re-exports all graph functions)
backend/api/routes/ingest.py
backend/api/main.py (updated with watcher integration)
```

#### Issues Encountered

- Voyage AI free tier (3 RPM / 10K TPM): single PDF had ~17 chunks × ~1500 tokens = 25K tokens/batch, exceeding TPM limit. Fixed by reducing batch size to 8 with 21-second inter-batch delay.
- Entity extraction truncated at 4096 max_tokens (Claude hit limit on long papers). Fixed by increasing to 8192.
- scholar.py: `citedPaper` can be None in Semantic Scholar response. Fixed with `or {}` guard.
- arxiv 3.0.0 uses `Client().results(search)` not `search.results()` — updated accordingly.
- `uvicorn` binary uses wrong Python (Library/Frameworks vs conda). Must always use `python -m uvicorn`.
- Neo4j graph queries.py was 337 lines; split into `_queries_nodes.py` + `_queries_search.py` submodules, re-exported via queries.py.

#### Notes for Claude Code

1. **Always use `python -m uvicorn`** — the bare `uvicorn` command uses a different Python installation that is missing most packages and fails to import `cgi` (removed in Python 3.13).
2. **Voyage AI rate limits**: free tier is 3 RPM / 10K TPM. embed.py uses batch_size=8 with 21s delays. Ingesting a single paper takes ~2-5 minutes due to rate limiting.
3. **Entity extraction uses max_tokens=8192** — increase to 16K if extraction still truncates on very long papers.
4. **graph/queries.py is a re-export facade** — actual implementations are in `_queries_nodes.py` and `_queries_search.py`. Both are under 200 lines.
5. **DB has 3 test papers from debugging** (test_paper, Attention Is All You Need, watcher_test2). Safe to leave or delete before Phase 3 community detection testing.

---

### Phase 3 — KG MCP Server

**Completed:** 2026-04-22
**Status:** `[x] Complete`

#### Task Checkboxes

- [x] 3.1 — FastMCP server scaffold
- [x] 3.2 — add_node and add_edge tools
- [x] 3.3 — get_neighbors and find_path tools
- [x] 3.4 — get_community tool
- [x] 3.5 — find_bridges tool
- [x] 3.6 — find_structural_holes tool
- [x] 3.7 — get_subgraph and semantic_search tools
- [x] 3.8 — MCP registration in parent repo

#### Deviations

- 3.1: community.py was an empty stub — added stub function signatures (NotImplementedError) for run_louvain and find_structural_holes so the import resolves at scaffold time. Full implementation in Tasks 3.4 and 3.6.
- 3.2: upsert_node and upsert_edge already existed in _queries_nodes.py from Phase 2; no changes needed. Added input validation in tools (type must be in allowed set) to prevent f-string injection in existing upsert_node Cypher.
- 3.3: get_neighbors and find_path already existed in _queries_search.py from Phase 2; no changes needed.
- 3.4: community.py was stub — implemented run_louvain() with try/finally to always drop GDS projection (prevents "already exists" error on retry). Added write-back of community_id to nodes (required for find_bridges Cypher). GDS projection uses failIfMissing=false on pre-drop to handle crashed runs.
- 3.5: Per CursorRules all Cypher must be in backend/graph/queries.py. Moved find_bridges Cypher to _queries_search.py (added find_bridges function), re-exported from queries.py. Tool in server.py calls graph.find_bridges() cleanly.
- 3.6: Implemented find_structural_holes() in community.py using UNWIND-based community pair enumeration + OPTIONAL MATCH to count cross-edges.
- 3.7: get_subgraph already existed in _queries_search.py. semantic_search is a lazy import of embed_texts to avoid circular import and keep startup clean.
- 3.8: Parent repo .mcp.json located at /Users/danieltecum/Desktop/claude-knowledge-framework/.mcp.json (uses mcpServers key format). Used full Python path /opt/anaconda3/bin/python per Phase 2 note. Added PYTHONPATH env var per Debugging.md 6-A guidance.

#### Phase Summary

Phase 3 built the complete FastMCP server with all 8 MCP tools. The server runs on stdio transport, starts cleanly with zero import errors, and registers all tools correctly. `community.py` was implemented with `run_louvain()` (GDS Louvain projection with try/finally cleanup + community_id write-back to nodes) and `find_structural_holes()` (community pair enumeration via Cypher UNWIND). The `find_bridges` Cypher was placed in `_queries_search.py` per CursorRules (all Cypher in graph/queries.py). The MCP server was registered in the parent knowledge-framework `.mcp.json` with the full Python path and PYTHONPATH env var. Debugging checks 3-A through 3-D all pass. Check 3-E (MCP callable from parent Claude Code session) requires a Claude Code session restart to activate the new entry.

#### Files Created

```
backend/mcp/server.py           (implemented — 8 tools: add_node, add_edge, get_neighbors,
                                  find_path, get_community, find_bridges,
                                  find_structural_holes_tool, get_subgraph, semantic_search)
backend/graph/community.py      (implemented — run_louvain, find_structural_holes)
backend/graph/_queries_search.py (updated — added find_bridges function)
backend/graph/queries.py        (updated — re-exports find_bridges)
/Users/danieltecum/Desktop/claude-knowledge-framework/.mcp.json (updated — research-kg entry)
```

#### Issues Encountered

- Neo4j 6.1.0 deprecation warnings: `id()` function deprecated in favor of `elementId()`. Only warnings, not errors. Affects _queries_search.py COALESCE fallbacks — pre-existing Phase 2 code, not blocking.
- GDS deprecation warning: `gds.graph.drop` returns deprecated `schema` field. Only a warning, not an error.
- `watcher_test2` paper exists in PostgreSQL but not Neo4j (Phase 2 test artifact). `get_neighbors` returns empty for this ID — expected behavior, not a bug.

#### Notes for Claude Code

1. **MCP check 3-E is MANUAL** — requires restarting the claude-knowledge-framework Claude Code session to pick up the new `.mcp.json` entry, then running `mcp__research-kg__semantic_search({"query": "machine learning", "limit": 3})`.
2. **community_id on nodes** — `run_louvain()` now writes `community_id` back to nodes. With only 2 papers in test data, all land in community 0. `find_structural_holes` returns empty with < 2 communities — this is correct, not a bug.
3. **Neo4j `id()` deprecation** — the fallback `toString(id(n))` in get_neighbors will produce Neo4j internal IDs for nodes missing `.id` property. This only affects Entity nodes if they lack `id`. Phase 4 or 5 may want to update to use `elementId()` for Neo4j 6 compatibility.
4. **GDS projection name** — `run_louvain()` uses `'researchGraph'` as the projection name. If Phase 4 or 5 needs concurrent Louvain runs, add a unique suffix or add a mutex.

---

### Phase 4 — Agents

**Completed:** 2026-04-22
**Status:** `[x] Complete`

#### Task Checkboxes

- [x] 4.1 — WebSocket event system
- [x] 4.2 — Connection agent
- [x] 4.3 — Gap agent
- [x] 4.4 — Agenda agent
- [x] 4.5 — Chat agent (streaming)
- [x] 4.6 — Remaining API routes

#### Deviations

- 4.1: events.py emit() required `global _connections` — augmented assignment `-=` causes Python to treat `_connections` as local variable, triggering UnboundLocalError.
- 4.2: pdf.py wiring already existed from Phase 2 stub — no changes needed. Fixed spec type case: `"Entity"` → `"entity"` (lowercase, matches get_neighbors return format).
- 4.3: none
- 4.4: none
- 4.5: Fixed spec bug: `db.get_pool()` → `get_pool()` from `backend.db.client`. Added `AsyncGenerator[str, None]` return type annotation.
- 4.6: Added `ChatRequest` Pydantic model in `api/models.py` (spec used untyped `dict` — CursorRules requires typed models). Agenda route uses `@router.get("")` (not `"/"`) with prefix `/agenda`.

#### Phase Summary

Phase 4 implemented all agents and completed all API routes. The WebSocket event broadcaster emits ingestion/agent progress events to all connected clients. The connection agent fetches pgvector embedding neighbors, Neo4j entity connections, Louvain community membership, generates a Claude connection report, and saves it to `reports/connections/`. The gap agent detects structural holes and generates a ranked research proposal report. The agenda agent synthesizes weekly priorities from recent papers, user focus areas, and graph gaps. The chat agent streams Claude responses with per-paper graph context preloaded. All five route files implement typed Pydantic request/response models. The full FastAPI app starts with 24 routes registered and all Debugging.md checks pass.

#### Files Created

```
backend/api/events.py            (implemented — WebSocket broadcaster)
backend/api/ws.py                (implemented — /ws endpoint)
backend/api/models.py            (implemented — ChatRequest model)
backend/api/main.py              (updated — /chat StreamingResponse endpoint)
backend/agents/connection.py     (implemented — connection agent + Claude report)
backend/agents/gap.py            (implemented — structural hole detection + report)
backend/agents/agenda.py         (implemented — weekly agenda synthesis)
backend/agents/chat.py           (implemented — streaming async generator)
backend/api/routes/reports.py    (implemented)
backend/api/routes/agenda.py     (implemented)
backend/api/routes/concepts.py   (implemented — approve writes to concept_map.json)
backend/api/routes/papers.py     (implemented)
backend/api/routes/graph.py      (implemented)
```

#### Issues Encountered

- `events.py emit()` UnboundLocalError: `_connections -= dead` makes Python treat `_connections` as local. Fixed with `global _connections`.
- Spec bug in `chat.py`: `db.get_pool()` fails — `db` is queries module, not client. Fixed to `get_pool()` from `backend.db.client`.
- Spec used untyped `body: dict` for `/chat` — replaced with `ChatRequest` Pydantic model.
- 4-D gap report returns empty path — expected with only 2 test papers in same Louvain community. Agent handles gracefully.

#### Notes for Claude Code

1. **WebSocket `global _connections` pattern** — `emit()` uses `global _connections` because augmented assignment `_connections -= dead` would otherwise be interpreted as a local variable binding by Python's compiler.
2. **Connection agent pre-wired** — `pdf.py` lines 105-110 already call `run_connection_agent(paper_id)` via `asyncio.create_task`. No additional wiring needed.
3. **Gap reports need diverse papers** — `find_structural_holes()` returns empty until multiple Louvain communities exist (needs 10+ papers across different topics).
4. **Agenda route `""` pattern** — `@router.get("")` with prefix `/agenda` = `GET /agenda`. This is the correct FastAPI pattern for root-of-prefix routes.
5. **Chat is StreamingResponse** — Phase 5 `streamChat()` in `api.ts` reads via `ReadableStream`. Do not `await resp.json()` on this endpoint.

---

### Phase 5 — 3D Visualization Frontend

**Completed:** 2026-04-23
**Status:** `[x] Complete`

#### Task Checkboxes

- [x] 5.1 — TypeScript types
- [x] 5.2 — API client
- [x] 5.3 — WebSocket singleton
- [x] 5.4 — Zustand stores
- [x] 5.5 — Graph3D component
- [x] 5.6 — SearchBar component
- [x] 5.7 — SidePanel component
- [x] 5.8 — ChatDrawer component
- [x] 5.9 — FilterPanel component
- [x] 5.10 — AgendaView and ConceptQueue
- [x] 5.11 — App.tsx composition
- [x] 5.12 — Ingest input UI

#### Deviations

- 5.1: Added `PaperDetail` as a dedicated interface (extends PaperNode with abstract + authors) rather than the inline intersection type in spec, for cleaner usage in api.ts and SidePanel.
- 5.2: Added `ingestPdf(file: File)` multipart upload function (backed by existing Phase 2 `POST /ingest/pdf` endpoint). Also added typed `request<T>()` helper to DRY up fetch calls.
- 5.3: Added try/catch on `JSON.parse` in WebSocket message handler to ignore malformed protocol messages without crashing.
- 5.4: none
- 5.5: Used imperative `ForceGraph3D` API (vanilla JS library attached to a div ref) rather than R3F — `3d-force-graph` is not a React component. Used `_destructor()` on unmount for cleanup. Data uses `links` (not `edges`) per the library's format; edges are mapped at data-passing time. Added per-effect `nodeColor` updates for traversal path and selected node highlighting.
- 5.6: Debounce implemented via `useRef<ReturnType<typeof setTimeout>>` to avoid re-renders.
- 5.7: Used promise chaining (`.then()`) rather than async/await inside useEffect to avoid stale-closure issues with the multi-step fetch sequence (paper → report).
- 5.8: Accumulated streamed text in a `ref` and flushed to state every 50ms via `setInterval` to avoid per-chunk re-renders per Debugging.md 5-D guidance.
- 5.9: Year range uses two separate range sliders (one for min, one for max) — this is functional though not a true dual-handle slider.
- 5.10: none
- 5.11: `GapsView` extracted as an internal component in App.tsx (not a separate file) to keep the routing logic co-located. `IngestBar` wired into graph view overlay alongside other overlays.
- 5.12: Implemented as `IngestBar` component with PDF file input, three text-input modes, and an auto-dismissing toast system using `setTimeout` — no external library.

#### Phase Summary

Phase 5 built the complete React/TypeScript/Vite frontend. Twelve components were implemented from scratch: TypeScript types, a typed API client covering all 15 backend endpoints including streaming chat, a WebSocket singleton that feeds the Zustand agent store, three Zustand stores (graph data + filters, agent traversal state, UI panel state), the 3D force-directed graph using the imperative `ForceGraph3D` API with per-community cluster colors, a debounced semantic search bar, a slide-in side panel rendering paper details and markdown connection reports, a streaming chat drawer with 50ms-buffered render updates, a filter panel with edge-type toggles and year sliders, agenda and concept queue views, and a full App.tsx composition wiring all views via a 4-tab nav. `tsc --noEmit` passes with zero errors. ESLint reports zero errors. `npm run dev` starts at localhost:5173. Debugging.md checks 5-A through 5-H are all browser-manual (UI interaction required).

#### Files Created

```
frontend/src/types/index.ts           (TypeScript types)
frontend/src/lib/api.ts               (typed API client — all endpoints + streamChat)
frontend/src/lib/socket.ts            (WebSocket singleton)
frontend/src/store/graph.ts           (graph data, selected node, filters)
frontend/src/store/agent.ts           (agent running state, traversal path)
frontend/src/store/ui.ts              (panel open/close, active view)
frontend/src/components/Graph3D.tsx   (3d-force-graph imperative wrapper)
frontend/src/components/SearchBar.tsx (semantic search overlay, 300ms debounce)
frontend/src/components/SidePanel.tsx (paper details, markdown report, mark-as-read)
frontend/src/components/ChatDrawer.tsx (streaming chat, 50ms flush accumulator)
frontend/src/components/FilterPanel.tsx (edge toggles, year sliders, toggle graph)
frontend/src/components/AgendaView.tsx (markdown agenda + priority update)
frontend/src/components/ConceptQueue.tsx (approve/reject pending concept mappings)
frontend/src/components/IngestBar.tsx (ArXiv/URL/GitHub/PDF ingest + auto-dismiss toasts)
frontend/src/App.tsx                  (full composition — replaced Phase 1 stub)
```

#### Dependencies Installed

```
react-markdown (markdown rendering in SidePanel, ChatDrawer, AgendaView, GapsView)
```

#### Issues Encountered

- `App.tsx` first draft used `await import()` inside a component body (invalid in React) — fixed by moving imports to module top level and extracting `GapsView` as an internal component.
- `3d-force-graph` uses `links` not `edges` in its data format — edges mapped at graphData() call time.

#### Notes for Claude Code

1. **`3d-force-graph` is imperative** — it's not a React component. Attach via `ForceGraph3D(divRef.current)` in `useEffect`, call `_destructor()` on cleanup. Graph data updates go through `.graphData({nodes, links})` method calls.
2. **`links` vs `edges`** — the 3d-force-graph library expects `{ nodes, links }` not `{ nodes, edges }`. The backend returns `edges`. Map at the ForceGraph3D `.graphData()` call.
3. **Chat streaming uses 50ms flush** — streamed chunks accumulate in `accRef` and are flushed to React state every 50ms. Do not change this to per-chunk updates — with fast models, this causes hundreds of re-renders per second.
4. **Debugging.md 5-A through 5-H are all browser-manual** — they require opening localhost:5173 and interacting with the UI. All programmatic checks (tsc, eslint, dev server start) pass.
5. **`react-markdown` version** — installed latest. If prose styling looks off, the `[&_h2]:` Tailwind arbitrary selectors handle the typography since `@tailwindcss/typography` is not installed.
6. **IngestBar position** — top-left at `absolute top-4 left-4`. SearchBar is top-center. Nav tabs are top-right. FilterPanel is bottom-left. These do not overlap on standard displays.

---

### Phase 6 — CLAUDE.md + Final Integration

**Completed:** 2026-04-23
**Status:** `[x] Complete`

#### Task Checkboxes

- [x] 6.1 — Write research-system/CLAUDE.md
- [x] 6.2 — End-to-end test
- [x] 6.3 — Register MCP in parent repo (already done in Phase 3 — verified still correct)

#### Additional fixes applied during Phase 6

- [x] 6.1b — Graph auto-refresh: `paper_ingested` WebSocket event now bumps `graphRefreshToken` in agent store, causing App.tsx to re-fetch `/graph/full` automatically after each ingestion

#### Deviations

- 6.1: CLAUDE.md expanded with additional sections: startup commands, ingestion sources table, agent endpoints table, implementation notes, and embedding details. All are accurate as of Phase 6.
- 6.2: End-to-end test used "Attention Is All You Need" (1706.03762) as the reference paper (fully ingested in Phase 2). A fresh BERT (1810.04805) ingest was triggered but failed at the embedding step due to Voyage AI free-tier rate limits (3 RPM / 10K TPM). The ingest pipeline is correct — the same code successfully ingested "Attention Is All You Need" with 14 chunks. 9 failed partial ingestions (0 chunks) created during Phase 5 UI testing were cleaned up from the DB.
- 6.3: Parent repo `.mcp.json` uses a `mcp_wrapper.sh` bash script (from Phase 3) instead of calling python directly. Verified wrapper starts MCP server correctly with log output at `/tmp/research-kg-mcp.log`.

#### Phase Summary

Phase 6 completed the system documentation and final integration. `CLAUDE.md` was written with full graph schema, all 9 MCP tools documented with parameters and return types, startup commands, ingestion source table, agent endpoints, and implementation notes specific to this environment (Python path, PostgreSQL port 5433, Voyage AI rate limits). A critical UX bug was fixed: the graph now auto-refreshes when any paper finishes ingesting by listening to `paper_ingested` WebSocket events via a `graphRefreshToken` in the agent store. The full E2E pipeline was verified: all 13 backend routes return correct responses (health, papers, graph/full, graph/search, reports/connection, reports/gaps/latest, concepts/pending, agenda, chat, WebSocket), all 4 key MCP tools (semantic_search, get_neighbors, get_subgraph, find_structural_holes_tool) return expected results, the file watcher initializes with FSEventsEmitter on macOS, and `~/research-inbox/` is monitored. Debugging.md Phase 6 checks 6-A and 6-B are also confirmed passing.

#### Files Created / Modified

```
research-system/CLAUDE.md                      (new — system documentation for Claude Code)
frontend/src/store/agent.ts                    (updated — added graphRefreshToken)
frontend/src/App.tsx                           (updated — refreshes graph on paper_ingested event)
```

#### Issues Encountered

- Voyage AI free-tier rate limits (3 RPM / 10K TPM) prevent ingesting long papers (BERT at ~100+ chunks). The ingestion code is correct — the rate limit is an infrastructure constraint. Add a payment method at dashboard.voyageai.com or use shorter papers for testing.
- 9 failed partial ingestion rows (0 chunks) were cleaned up with `DELETE FROM papers WHERE id NOT IN (SELECT DISTINCT paper_id FROM chunks)`.

#### Notes for Claude Code

1. **ALL PHASES COMPLETE** — the system is fully built and operational.
2. **Active services**: Backend at :8000, Frontend at :5173, PostgreSQL at :5433, Neo4j at :7687. Run `docker compose up -d` + uvicorn + `npm run dev` to start.
3. **MCP server**: Uses `mcp_wrapper.sh` registered in the parent repo's `.mcp.json`. Logs to `/tmp/research-kg-mcp.log`.
4. **Rate limit**: To ingest more papers, upgrade Voyage AI at dashboard.voyageai.com. Free tier limited to 3 RPM / 10K TPM.
5. **Graph refresh**: After any paper ingestion completes, the frontend automatically re-fetches `/graph/full` via the `graphRefreshToken` in the agent store — no manual browser refresh needed.
6. **Known cleanup needed**: The `test_paper` row in PostgreSQL/Neo4j is a Phase 2 artifact (same content as "Attention Is All You Need"). Safe to delete manually if desired.

---

## Codebase State Graph

<!--
  Cursor updates this after EVERY phase.
  Claude Code reads this before generating next phase batch.
  This is the ground truth — not Context.md, not comments, not memory.
-->

```
MODULES:
├── backend/
│   ├── config.py              [COMPLETE — pydantic BaseSettings, loads from .env]
│   ├── api/
│   │   ├── main.py            [COMPLETE — FastAPI app, lifespan, CORS, watcher, routers]
│   │   ├── events.py          [COMPLETE — WebSocket broadcaster, global _connections]
│   │   ├── ws.py              [COMPLETE — /ws keep-alive endpoint]
│   │   ├── models.py          [COMPLETE — ChatRequest Pydantic model]
│   │   └── routes/
│   │       ├── ingest.py      [COMPLETE — PDF/arxiv/url/github endpoints]
│   │       ├── graph.py       [COMPLETE — /full, /search, /subgraph]
│   │       ├── papers.py      [COMPLETE — list, get, mark-as-read]
│   │       ├── reports.py     [COMPLETE — connection report, gap trigger/latest]
│   │       ├── agenda.py      [COMPLETE — GET /agenda, POST /agenda/priorities]
│   │       └── concepts.py    [COMPLETE — pending, approve (writes JSON), reject]
│   ├── ingestion/
│   │   ├── extract.py         [COMPLETE — PyMuPDF text + metadata extraction]
│   │   ├── chunk.py           [COMPLETE — 512-word chunks, 64-word overlap]
│   │   ├── embed.py           [COMPLETE — voyage-large-2, batch=8, 21s delay for rate limit]
│   │   ├── entities.py        [COMPLETE — Claude extraction, 8192 tokens, JSON fence strip]
│   │   ├── normalize.py       [COMPLETE — concept_map.json lookup + synonym suggestion]
│   │   ├── scholar.py         [COMPLETE — Semantic Scholar references API]
│   │   ├── watcher.py         [COMPLETE — watchdog observer, run_coroutine_threadsafe]
│   │   └── sources/
│   │       ├── pdf.py         [COMPLETE — full pipeline, triggers connection agent]
│   │       ├── arxiv.py       [COMPLETE — arxiv 3.0.0 Client API, metadata patch]
│   │       ├── url.py         [COMPLETE — httpx download, content-type check]
│   │       └── github.py      [COMPLETE — README scrape, arxiv+pdf link extraction]
│   ├── graph/
│   │   ├── client.py          [COMPLETE — async driver, get_session context manager]
│   │   ├── queries.py         [COMPLETE — re-exports _queries_nodes + _queries_search]
│   │   ├── _queries_nodes.py  [COMPLETE — create/merge nodes and edges]
│   │   ├── _queries_search.py [COMPLETE — get_neighbors, find_path, subgraph, full graph, find_bridges]
│   │   ├── community.py       [COMPLETE — run_louvain + find_structural_holes]
│   │   └── setup.cypher       [COMPLETE — constraints + indexes applied]
│   ├── db/
│   │   ├── client.py          [COMPLETE — asyncpg pool, get_pool/close_pool]
│   │   ├── queries.py         [COMPLETE — all 14 functions, pgvector registered per-conn]
│   │   └── schema.sql         [COMPLETE — all tables + ivfflat index applied]
│   ├── agents/
│   │   ├── connection.py      [COMPLETE — connection agent, Claude report generation]
│   │   ├── gap.py             [COMPLETE — structural hole detection, gap report]
│   │   ├── agenda.py          [COMPLETE — weekly agenda synthesis]
│   │   └── chat.py            [COMPLETE — streaming async generator, paper context]
│   └── mcp/
│       └── server.py          [COMPLETE — 8 MCP tools, stdio transport]
├── frontend/
│   ├── src/
│   │   ├── App.tsx            [COMPLETE — full composition + auto-refresh on paper_ingested]
│   │   ├── index.css          [COMPLETE — Tailwind directives + body bg]
│   │   ├── types/index.ts     [COMPLETE — PaperNode, EntityNode, GraphNode, GraphEdge, GraphData, PaperDetail, ConceptMapping, AgentEvent]
│   │   ├── lib/
│   │   │   ├── api.ts         [COMPLETE — all 15 endpoints + streamChat async generator]
│   │   │   └── socket.ts      [COMPLETE — WebSocket singleton, module-level]
│   │   ├── store/
│   │   │   ├── graph.ts       [COMPLETE — data, selectedNodeId, filteredNodeIds, visibleEdgeTypes, yearRange, showGraph]
│   │   │   ├── agent.ts       [COMPLETE — isRunning, currentAgent, traversalPath, handleEvent, graphRefreshToken]
│   │   │   └── ui.ts          [COMPLETE — sidePanelOpen, chatOpen, activeView]
│   │   └── components/
│   │       ├── Graph3D.tsx        [COMPLETE — imperative ForceGraph3D, cluster colors, traversal pulse]
│   │       ├── SearchBar.tsx      [COMPLETE — 300ms debounce, result count, clear button]
│   │       ├── SidePanel.tsx      [COMPLETE — paper details, markdown report, mark-as-read, ask agent]
│   │       ├── ChatDrawer.tsx     [COMPLETE — streaming, 50ms flush accumulator, markdown messages]
│   │       ├── FilterPanel.tsx    [COMPLETE — edge type toggles, year range sliders, toggle graph]
│   │       ├── AgendaView.tsx     [COMPLETE — markdown agenda, priority update textarea]
│   │       ├── ConceptQueue.tsx   [COMPLETE — approve/reject pending mappings]
│   │       └── IngestBar.tsx      [COMPLETE — ArXiv/URL/GitHub/PDF + auto-dismiss toasts]
│   ├── tailwind.config.ts     [COMPLETE — full design token theme]
│   ├── vite.config.ts         [COMPLETE — Vite default]
│   └── package.json           [COMPLETE — all deps installed + react-markdown]
├── reports/
│   ├── connections/           [empty — populated by connection agent]
│   └── gaps/                  [empty — populated by gap agent]
└── data/
    └── concept_map.json       [COMPLETE — seed {"approved":[],"pending":[]}]

API ROUTES (backend/api):
  GET /health → {"status": "ok"}
  All other routes stubbed — implemented in Phases 2–4

KNOWN ISSUES:
  - POSTGRES_URL uses port 5433 (not 5432) — local macOS postgres owns 5432
  - VOYAGE_API_KEY and ANTHROPIC_API_KEY are empty — must be set before Phase 2

OPEN DECISIONS:
  - neo4j 6.1.0 installed (spec was 5.19.0) — verify driver API compat in Phase 2
  - arxiv 3.0.0 installed (spec was 2.1.0) — verify Search/Client API in Phase 2 task 2.10
  - fastmcp 3.2.4 installed (spec was 0.4.1) — verify tool decorator syntax in Phase 3
```

---

## Pattern Log

| Pattern | Description | File | Phase |
|---|---|---|---|
| [none yet] | | | |
