from __future__ import annotations

from typing import Dict, Optional

from app.managers.lobby_manager import LobbyManager, Lobby


class GameManager:
    """Thin wrapper to manage active games by lobby id."""

    def __init__(self, lobby_manager: Optional[LobbyManager] = None):
        self.lobby_manager = lobby_manager or LobbyManager()

    def get_lobby(self, lobby_id: str) -> Lobby:
        lobby = self.lobby_manager.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")
        return lobby

    def ensure_started(self, lobby_id: str) -> None:
        lobby = self.get_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")

    def state(self, lobby_id: str) -> Dict:
        self.ensure_started(lobby_id)
        return self.lobby_manager.get_game_state(lobby_id)


