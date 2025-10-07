from __future__ import annotations

from fastapi import Request

from app.managers.lobby_manager import LobbyManager


def get_lobby_manager(request: Request) -> LobbyManager:
    # Attach a singleton LobbyManager to app state
    if not hasattr(request.app.state, "lobby_manager"):
        request.app.state.lobby_manager = LobbyManager()
    return request.app.state.lobby_manager  # type: ignore[attr-defined]


