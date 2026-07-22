import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import router as analysis_router
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.player import router as player_router
from app.api.friend import router as friend_router
from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.api.ws import chat_ws
from app.config import BASE_DIR, TEMP_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="PingPong Action Analyzer + 乒小Yo", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file serving ──────────────────────────────────────────
TEMPLATE_VIDEO_DIR = BASE_DIR / "scripts" / "input_videos"
TEMPLATE_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/templates", StaticFiles(directory=str(TEMPLATE_VIDEO_DIR)), name="templates")

TEMP_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/segments", StaticFiles(directory=str(TEMP_DIR)), name="segments")

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

STATIC_DIR = BASE_DIR / "static" / "images"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media/static", StaticFiles(directory=str(STATIC_DIR)), name="static_images")

# ── API routes ───────────────────────────────────────────────────
app.include_router(analysis_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(user_router, prefix="/api/user")
app.include_router(player_router, prefix="/api/players")
app.include_router(friend_router, prefix="/api/friends")
app.include_router(chat_router, prefix="/api/chat")
app.include_router(upload_router, prefix="/api/upload")

# ── WebSocket ────────────────────────────────────────────────────
from fastapi import WebSocket as FastAPIWebSocket


@app.websocket("/ws")
async def websocket_endpoint(ws: FastAPIWebSocket):
    await chat_ws.handle(ws)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
