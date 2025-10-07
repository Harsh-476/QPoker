from __future__ import annotations

from typing import Dict, Optional


class PlayerManager:
    """Tracks players per lobby."""

    def __init__(self):
        # lobby_id -> { player_id -> name }
        self._players_by_lobby: Dict[str, Dict[str, str]] = {}

    def join(self, lobby_id: str, player_id: str, name: str) -> None:
        lobby_players = self._players_by_lobby.setdefault(lobby_id, {})
        lobby_players[player_id] = name

    def leave(self, lobby_id: str, player_id: str) -> None:
        lobby_players = self._players_by_lobby.get(lobby_id)
        if not lobby_players:
            return
        lobby_players.pop(player_id, None)
        if not lobby_players:
            self._players_by_lobby.pop(lobby_id, None)

    def get_name(self, lobby_id: str, player_id: str) -> Optional[str]:
        lobby_players = self._players_by_lobby.get(lobby_id)
        if not lobby_players:
            return None
        return lobby_players.get(player_id)
