from __future__ import annotations

import socketio

from app.sockets import events


async def emit_lobby_update(sio: socketio.AsyncServer, lobby_id: str, lobby_public: dict) -> None:
    await sio.emit(events.LOBBY_UPDATE, lobby_public, room=lobby_id)


async def emit_game_update(sio: socketio.AsyncServer, lobby_id: str, payload: dict) -> None:
    await sio.emit(events.GAME_UPDATE, payload, room=lobby_id)


