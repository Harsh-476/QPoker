from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.config import settings
from app.managers.lobby_manager import LobbyManager
from app.sockets.handlers import register_socket_handlers


async def periodic_cleanup(lobby_manager: LobbyManager):
    """Run periodic cleanup every 30 seconds"""
    while True:
        try:
            await asyncio.sleep(30)  # Run every 30 seconds
            empty_count = lobby_manager.cleanup_empty_lobbies()
            completed_count = lobby_manager.cleanup_completed_games()
            if empty_count > 0 or completed_count > 0:
                print(f"[cleanup] Removed {empty_count} empty lobbies and {completed_count} completed games")
        except Exception as e:
            print(f"[cleanup] Error during periodic cleanup: {e}")


# Socket.IO server (ASGI)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.cors_origins if settings.cors_origins != "*" else "*",
    logger=settings.debug,
    engineio_logger=settings.debug,
    allow_upgrades=True,
)


def create_app() -> FastAPI:
    app = FastAPI(debug=settings.debug, title="Quantum Poker API")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.cors_origins == "*" else [o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize shared managers on app state
    if not hasattr(app.state, "lobby_manager"):
        app.state.lobby_manager = LobbyManager()

    # Register socket handlers using shared LobbyManager
    register_socket_handlers(sio, lambda: app.state.lobby_manager)

    # Include API routers
    from app.api.routes import router as api_router
    app.include_router(api_router, prefix="/api")
    
    # Add startup event for periodic cleanup
    @app.on_event("startup")
    async def startup_event():
        """Start background cleanup task"""
        asyncio.create_task(periodic_cleanup(app.state.lobby_manager))

    # Build Socket.IO ASGI that forwards non-socket paths to FastAPI
    socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path=settings.socket_path)

    # Attach combined app for uvicorn target
    app.state.asgi = socket_app
    return app


app = create_app()

# For uvicorn entrypoint, we expose `asgi` combined app
asgi = app.state.asgi


# Basic Socket.IO placeholders (to be expanded in sockets module later)
@sio.event
async def connect(sid, environ, auth):
    if settings.debug:
        print(f"[socket] connect: {sid}")


@sio.event
async def disconnect(sid):
    if settings.debug:
        print(f"[socket] disconnect: {sid}")


