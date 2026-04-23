import json
import logging
from fastapi import WebSocket
from typing import Any

logger = logging.getLogger(__name__)

_connections: set[WebSocket] = set()


async def connect(ws: WebSocket) -> None:
    """Accept and register a WebSocket connection."""
    await ws.accept()
    _connections.add(ws)
    logger.info("WebSocket connected — %d active connections", len(_connections))


async def disconnect(ws: WebSocket) -> None:
    """Remove a WebSocket connection from the registry."""
    _connections.discard(ws)
    logger.info("WebSocket disconnected — %d active connections", len(_connections))


async def emit(event: dict[str, Any]) -> None:
    """Broadcast an event to all connected WebSocket clients.
    Dead connections are pruned automatically.
    """
    global _connections
    if not _connections:
        return
    dead: set[WebSocket] = set()
    payload = json.dumps(event)
    for ws in _connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    if dead:
        _connections -= dead
        logger.debug("Pruned %d dead WebSocket connections", len(dead))
