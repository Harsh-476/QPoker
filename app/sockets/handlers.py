from __future__ import annotations

from typing import Any

import socketio

from app.managers.lobby_manager import LobbyManager


def register_socket_handlers(sio: socketio.AsyncServer, get_lobby_manager: callable) -> None:
    # Store player_id to lobby_id mapping for disconnect handling
    player_lobbies = {}  # sid -> (lobby_id, player_id)
    @sio.event
    async def join(sid: str, data: dict):
        lobby_id = data.get("lobby_id")
        player_id = data.get("player_id")
        name = data.get("name")
        lm: LobbyManager = get_lobby_manager()
        
        print(f"[socket] join attempt: lobby_id={lobby_id}, player_id={player_id}, name={name}")
        print(f"[socket] available lobbies: {list(lm.lobbies.keys())}")
        
        try:
            # Check if lobby exists
            lobby = lm.get_lobby(lobby_id)
            if not lobby:
                print(f"[socket] lobby {lobby_id} not found in lobby manager")
                await sio.emit("error", {"detail": "Lobby not found"}, to=sid)
                return
            
            print(f"[socket] lobby {lobby_id} found, joining player {player_id}")
            # Join lobby (this will handle already-joined players gracefully)
            lm.join_lobby(lobby_id, player_id, name)
            await sio.enter_room(sid, lobby_id)
            await sio.emit("lobby:update", lm.get_lobby(lobby_id).to_public(), room=lobby_id)
            print(f"[socket] player {player_id} successfully joined lobby {lobby_id}")
            
            # Store mapping for disconnect handling
            player_lobbies[sid] = (lobby_id, player_id)
        except Exception as e:
            print(f"[socket] error joining lobby: {e}")
            await sio.emit("error", {"detail": str(e)}, to=sid)

    @sio.event
    async def start_game(sid: str, data: dict):
        lobby_id = data.get("lobby_id")
        lm: LobbyManager = get_lobby_manager()
        try:
            result = lm.start_game(lobby_id)
            game_state = lm.get_game_state(lobby_id)
            await sio.emit("game:update", {"state": game_state, "result": result}, room=lobby_id)
        except Exception as e:
            await sio.emit("error", {"detail": str(e)}, to=sid)

    @sio.event
    async def action(sid: str, data: dict):
        lobby_id = data.get("lobby_id")
        player_id = data.get("player_id")
        action = data.get("action")
        amount = int(data.get("amount") or 0)
        lm: LobbyManager = get_lobby_manager()
        try:
            result = lm.player_action(lobby_id, player_id, action, amount)
            
            # If betting round is complete and not an auto-win, automatically deal next street
            if result.get("betting_round_complete") and not result.get("auto_win"):
                next_phase = result.get("next_phase")
                if next_phase == "flop":
                    result = lm.deal_flop(lobby_id)
                elif next_phase == "turn":
                    result = lm.deal_turn(lobby_id)
                elif next_phase == "river":
                    result = lm.deal_river(lobby_id)
                elif next_phase == "showdown":
                    result = lm.showdown(lobby_id)
                elif next_phase == "complete":
                    # Hand ended via betting reaching showdown-equivalent; try to start next hand
                    lobby = lm.get_lobby(lobby_id)
                    if lobby and lobby.engine:
                        next_info = lobby.engine.start_next_hand_if_possible()
                        if next_info:
                            # Promote waiting players before starting next hand
                            promotion_result = lm.promote_waiting_players(lobby_id)
                            if promotion_result["promoted_players"]:
                                print(f"[socket] promoted waiting players: {promotion_result['promoted_players']}")
                                # Emit lobby update for promoted players
                                await sio.emit("lobby:update", promotion_result["lobby"], room=lobby_id)
                            await sio.emit("game:update", {"state": lm.get_game_state(lobby_id), "result": next_info}, room=lobby_id)
            
            await sio.emit("game:update", {"state": lm.get_game_state(lobby_id), "result": result}, room=lobby_id)
        except Exception as e:
            await sio.emit("error", {"detail": str(e)}, to=sid)

    @sio.event
    async def deal_next_street(sid: str, data: dict):
        lobby_id = data.get("lobby_id")
        lm: LobbyManager = get_lobby_manager()
        try:
            # Get current game state to determine which street to deal
            game_state = lm.get_game_state(lobby_id)
            result = None
            
            if game_state['phase'] == 'preflop':
                result = lm.deal_flop(lobby_id)
            elif game_state['phase'] == 'flop':
                result = lm.deal_turn(lobby_id)
            elif game_state['phase'] == 'turn':
                result = lm.deal_river(lobby_id)
            elif game_state['phase'] == 'river':
                result = lm.showdown(lobby_id)
            
            if result:
                new_game_state = lm.get_game_state(lobby_id)
                await sio.emit("game:update", {"state": new_game_state, "result": result}, room=lobby_id)
        except Exception as e:
            await sio.emit("error", {"detail": str(e)}, to=sid)

    @sio.event
    async def apply_gate(sid: str, data: dict):
        lobby_id = data.get("lobby_id")
        player_id = data.get("player_id")
        gate = data.get("gate")
        card_indices = data.get("card_indices", [])
        preview_only = data.get("preview_only", False)
        lm: LobbyManager = get_lobby_manager()
        try:
            result = lm.apply_gate(lobby_id, player_id, gate, card_indices, preview_only)
            if not preview_only:
                # Only emit game update for actual gate applications, not previews
                game_state = lm.get_game_state(lobby_id)
                await sio.emit("game:update", {"state": game_state, "result": result}, room=lobby_id)
            else:
                # For previews, just send the result to the requesting player
                await sio.emit("gate_preview", result, to=sid)
        except Exception as e:
            await sio.emit("error", {"detail": str(e)}, to=sid)

    @sio.event
    async def disconnect(sid: str):
        """Handle player disconnect - remove from lobby and cleanup if empty"""
        lm: LobbyManager = get_lobby_manager()
        
        if sid in player_lobbies:
            lobby_id, player_id = player_lobbies[sid]
            print(f"[socket] disconnect: {player_id} from lobby {lobby_id}")
            
            try:
                # Remove player from lobby
                result = lm.leave_lobby(lobby_id, player_id)
                
                # Check if lobby was auto-deleted
                if result.get("lobby_deleted"):
                    print(f"[socket] lobby {lobby_id} auto-deleted: {result.get('message')}")
                else:
                    # Emit lobby update to remaining players
                    await sio.emit("lobby:update", lm.get_lobby(lobby_id).to_public(), room=lobby_id)
                    print(f"[socket] player {player_id} removed from lobby {lobby_id}")
                
                # Remove from tracking
                del player_lobbies[sid]
                
            except Exception as e:
                print(f"[socket] error handling disconnect: {e}")
                # Still remove from tracking even if there's an error
                if sid in player_lobbies:
                    del player_lobbies[sid]


