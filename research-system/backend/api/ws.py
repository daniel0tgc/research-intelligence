from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.api.events import connect, disconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint. Accepts connection and keeps it alive until disconnect."""
    await connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive — client can send pings
    except WebSocketDisconnect:
        await disconnect(websocket)
