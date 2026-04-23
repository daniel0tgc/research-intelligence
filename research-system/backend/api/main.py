import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from backend.db.client import get_pool, close_pool
from backend.graph.client import close_driver
from backend.api.routes import ingest, graph, papers, reports, agenda, concepts
from backend.api.ws import router as ws_router
from backend.api.models import ChatRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    loop = asyncio.get_event_loop()
    from backend.ingestion.watcher import start_watcher
    observer = start_watcher(loop)
    yield
    observer.stop()
    observer.join()
    await close_pool()
    await close_driver()


app = FastAPI(title="Research Intelligence System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(papers.router, prefix="/papers", tags=["papers"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(agenda.router, prefix="/agenda", tags=["agenda"])
app.include_router(concepts.router, prefix="/concepts", tags=["concepts"])
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    """Stream a Claude response about a paper or graph question."""
    from backend.agents.chat import stream_chat_response
    return StreamingResponse(
        stream_chat_response(body.paper_id, body.query),
        media_type="text/plain",
    )
