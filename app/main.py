import asyncio
import json
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

from .config import get_settings
from .session_manager import SessionManager

app = FastAPI(title="Realtime AI Backend", version="0.1.0")
session_manager = SessionManager()


@app.get("/")
async def root():
    return {
        "message": "Realtime AI Backend is running.",
        "health": "/healthz",
        "websocket": "/ws/session/{session_id}",
    }


@app.get("/favicon.ico")
async def favicon():
    # Avoid noisy 404s when browsers ask for a favicon.
    return Response(status_code=204)


@app.get("/healthz")
async def healthcheck():
    return {"status": "ok", "app": get_settings().app_name}


@app.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str, user_id: Optional[str] = None):
    await websocket.accept()
    user_identifier = user_id or "anonymous"
    runtime = await session_manager.start(session_id, user_identifier)
    await websocket.send_json({"type": "session_started", "session_id": session_id})
    try:
        while True:
            payload = await websocket.receive_text()
            user_payload = _parse_payload(payload)
            stream_queue = await session_manager.handle_user_turn(session_id, user_payload)
            while True:
                token = await stream_queue.get()
                if token == "__END__":
                    break
                await websocket.send_text(token)
            await websocket.send_text("[END_OF_RESPONSE]")
    except WebSocketDisconnect:
        pass
    finally:
        asyncio.create_task(session_manager.summarize_and_finalize(session_id))
        await websocket.close()


def _parse_payload(raw: str) -> str:
    try:
        data = json.loads(raw)
        return data.get("message", raw)
    except json.JSONDecodeError:
        return raw

