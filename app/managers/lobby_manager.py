from __future__ import annotations

import secrets
from typing import Dict, List, Optional

from app.config import settings
from app.utils.helpers import slugify_name
from app.game_logic.poker_engine import PokerEngine
from app.db import get_session
from app.models.orm import LobbyORM, PlayerORM


class Lobby:
    def __init__(self, lobby_id: str, name: str, max_players: int = 4):
        self.lobby_id = lobby_id
        self.name = name
        self.max_players = max_players
        self.players: Dict[str, str] = {}  # player_id -> name
        self.waiting_players: Dict[str, str] = {}  # player_id -> name (players waiting to join ongoing game)
        self.in_game: bool = False
        self.engine: Optional[PokerEngine] = None

    def to_public(self) -> dict:
        return {
            "lobby_id": self.lobby_id,
            "name": self.name,
            "max_players": self.max_players,
            "players": list(self.players.keys()),
            "waiting_players": list(self.waiting_players.keys()),
            "player_names": self.players,
            "waiting_player_names": self.waiting_players,
            "in_game": self.in_game,
            "game_id": self.lobby_id if self.in_game else None,
        }


class LobbyManager:
    def __init__(self):
        self.lobbies: Dict[str, Lobby] = {}

    def create_lobby(self, name: str, max_players: int = 4) -> Lobby:
        lobby_id = slugify_name(name)
        # ensure uniqueness by suffixing number if needed
        original = lobby_id
        suffix = 1
        while lobby_id in self.lobbies:
            lobby_id = f"{original}-{suffix}"
            suffix += 1
        lobby = Lobby(lobby_id=lobby_id, name=name, max_players=max_players)
        self.lobbies[lobby_id] = lobby
        # Persist lobby in DB if not present
        with get_session() as s:
            if s.get(LobbyORM, lobby_id) is None:
                s.add(LobbyORM(lobby_id=lobby_id, name=name, in_game=False, max_players=max_players))
        return lobby

    def list_lobbies(self) -> List[dict]:
        return [l.to_public() for l in self.lobbies.values()]

    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        return self.lobbies.get(lobby_id)

    def join_lobby(self, lobby_id: str, user_id: str, name: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        
        # Check if user is already in the game or waiting
        if user_id in lobby.players or user_id in lobby.waiting_players:
            return lobby.to_public()
        
        # If game is ongoing, add to waiting list
        if lobby.in_game:
            if len(lobby.waiting_players) >= lobby.max_players:
                raise ValueError("Waiting list is full")
            lobby.waiting_players[user_id] = name
            return lobby.to_public()
        
        # If game hasn't started, add to active players
        if len(lobby.players) >= lobby.max_players:
            raise ValueError("Lobby is full")
        lobby.players[user_id] = name
        return lobby.to_public()

    def promote_waiting_players(self, lobby_id: str) -> dict:
        """Promote waiting players to active players when there's space"""
        lobby = self._require_lobby(lobby_id)
        promoted = []
        
        # Promote waiting players to active players if there's space
        while len(lobby.players) < lobby.max_players and lobby.waiting_players:
            user_id, name = lobby.waiting_players.popitem()
            lobby.players[user_id] = name
            promoted.append(user_id)
        
        return {
            "promoted_players": promoted,
            "lobby": lobby.to_public()
        }

    def leave_lobby(self, lobby_id: str, user_id: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        lobby.players.pop(user_id, None)
        lobby.waiting_players.pop(user_id, None)  # Remove from waiting list too
        if lobby.engine and user_id in lobby.engine.players:
            # Mark player inactive in-engine if already started
            lobby.engine.players[user_id].is_active = False
        
        # Auto-cleanup: Remove lobby if it becomes empty
        if len(lobby.players) == 0:
            del self.lobbies[lobby_id]
            # Remove from DB as well
            with get_session() as s:
                obj = s.get(LobbyORM, lobby_id)
                if obj:
                    s.delete(obj)
            return {"lobby_deleted": True, "message": "Lobby deleted (no players left)"}
        
        return lobby.to_public()

    def delete_lobby(self, lobby_id: str):
        """Delete a lobby completely"""
        if lobby_id not in self.lobbies:
            raise ValueError("Lobby not found")
        del self.lobbies[lobby_id]
        with get_session() as s:
            obj = s.get(LobbyORM, lobby_id)
            if obj:
                s.delete(obj)
    
    def cleanup_empty_lobbies(self):
        """Remove lobbies that have no players"""
        empty_lobbies = []
        for lobby_id, lobby in self.lobbies.items():
            if len(lobby.players) == 0:
                empty_lobbies.append(lobby_id)
        
        for lobby_id in empty_lobbies:
            del self.lobbies[lobby_id]
        
        return len(empty_lobbies)
    
    def cleanup_completed_games(self):
        """Remove lobbies where games have completed"""
        completed_lobbies = []
        for lobby_id, lobby in self.lobbies.items():
            if lobby.in_game and lobby.engine and lobby.engine.game_state.get('phase') == 'complete':
                # Remove completed games immediately
                completed_lobbies.append(lobby_id)
        
        for lobby_id in completed_lobbies:
            del self.lobbies[lobby_id]
        
        return len(completed_lobbies)

    def start_game(self, lobby_id: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        if lobby.in_game:
            raise ValueError("Game already started")
        if len(lobby.players) < 2:
            raise ValueError("Need at least 2 players to start")
        player_ids = list(lobby.players.keys())
        player_names = [lobby.players[pid] for pid in player_ids]
        engine = PokerEngine(
            player_ids=player_ids,
            player_names=player_names,
            starting_chips=settings.starting_chips,
            small_blind=settings.small_blind,
            big_blind=settings.big_blind,
        )
        lobby.engine = engine
        lobby.in_game = True
        return engine.start_new_hand()

    def get_game_state(self, lobby_id: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")
        return lobby.engine.get_game_state()

    def player_action(self, lobby_id: str, player_id: str, action: str, amount: int = 0) -> dict:
        lobby = self._require_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")
        result = lobby.engine.player_action(player_id, action, amount)
        
        # Check for auto-win after action
        if result.get("auto_win"):
            auto_win_result = lobby.engine.handle_auto_win(result["winner"])
            result.update(auto_win_result)
            
            # Promote waiting players after auto-win
            promotion_result = self.promote_waiting_players(lobby_id)
            if promotion_result["promoted_players"]:
                print(f"[lobby] promoted waiting players after auto-win: {promotion_result['promoted_players']}")
            
            # Auto-cleanup: Remove lobby after game completion
            if result.get("phase") == "complete":
                del self.lobbies[lobby_id]
                result["lobby_deleted"] = True
                result["message"] = "Game completed and lobby cleaned up"
        
        return result

    def apply_gate(self, lobby_id: str, player_id: str, gate: str, indices: List[int], preview_only: bool) -> dict:
        lobby = self._require_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")
        return lobby.engine.apply_quantum_gate(player_id, gate, indices, preview_only)

    def deal_flop(self, lobby_id: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")
        result = lobby.engine.deal_flop()
        
        # Check for auto-win
        if result.get("auto_win"):
            auto_win_result = lobby.engine.handle_auto_win(result["winner"])
            result.update(auto_win_result)
        
        return result

    def deal_turn(self, lobby_id: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")
        result = lobby.engine.deal_turn()
        
        # Check for auto-win
        if result.get("auto_win"):
            auto_win_result = lobby.engine.handle_auto_win(result["winner"])
            result.update(auto_win_result)
        
        return result

    def deal_river(self, lobby_id: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")
        result = lobby.engine.deal_river()
        
        # Check for auto-win
        if result.get("auto_win"):
            auto_win_result = lobby.engine.handle_auto_win(result["winner"])
            result.update(auto_win_result)
        
        return result

    def showdown(self, lobby_id: str) -> dict:
        lobby = self._require_lobby(lobby_id)
        if not lobby.engine:
            raise ValueError("Game not started")
        result = lobby.engine.showdown()
        
        # Promote waiting players after showdown
        promotion_result = self.promote_waiting_players(lobby_id)
        if promotion_result["promoted_players"]:
            print(f"[lobby] promoted waiting players after showdown: {promotion_result['promoted_players']}")
        
        return result

    def _require_lobby(self, lobby_id: str) -> Lobby:
        lobby = self.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")
        return lobby


