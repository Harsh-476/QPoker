from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.managers.lobby_manager import LobbyManager
from app.models.lobby import LobbyCreate, LobbyPublic
from app.models.player import PlayerCreate
from app.models.action import ActionRequest
from app.models.gate import GateApplyRequest
from app.models.game_state import GameStatePublic
from app.auth import get_current_active_user
from app.models.orm import UserORM


router = APIRouter()


def get_lobby_manager(request: Request) -> LobbyManager:
    # Use the shared lobby manager from app state
    return request.app.state.lobby_manager


@router.get("/lobbies", response_model=list[LobbyPublic])
def list_lobbies(lm: LobbyManager = Depends(get_lobby_manager)):
    return lm.list_lobbies()


@router.get("/lobbies/{lobby_id}", response_model=LobbyPublic)
def get_lobby(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    lobby = lm.get_lobby(lobby_id)
    if not lobby:
        raise HTTPException(status_code=404, detail="Lobby not found")
    return lobby.to_public()


@router.post("/lobbies", response_model=LobbyPublic)
def create_lobby(
    payload: LobbyCreate, 
    lm: LobbyManager = Depends(get_lobby_manager),
    current_user: UserORM = Depends(get_current_active_user)
):
    lobby = lm.create_lobby(payload.name, payload.max_players)
    return lobby.to_public()


@router.post("/lobbies/{lobby_id}/join", response_model=LobbyPublic)
def join_lobby(
    lobby_id: str, 
    payload: PlayerCreate, 
    lm: LobbyManager = Depends(get_lobby_manager),
    current_user: UserORM = Depends(get_current_active_user)
):
    try:
        return lm.join_lobby(lobby_id, str(current_user.id), current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/leave", response_model=LobbyPublic)
def leave_lobby(lobby_id: str, payload: PlayerCreate, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.leave_lobby(lobby_id, payload.player_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/lobbies/{lobby_id}")
def delete_lobby(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        lm.delete_lobby(lobby_id)
        return {"message": "Lobby deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/start")
def start_game(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.start_game(lobby_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lobbies/{lobby_id}/state", response_model=GameStatePublic)
def get_state(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.get_game_state(lobby_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/action")
def player_action(lobby_id: str, payload: ActionRequest, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.player_action(lobby_id, payload.player_id, payload.action, payload.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/gate")
def apply_gate(lobby_id: str, payload: GateApplyRequest, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.apply_gate(lobby_id, payload.player_id, payload.gate, payload.card_indices, payload.preview_only)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/flop")
def deal_flop(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.deal_flop(lobby_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/turn")
def deal_turn(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.deal_turn(lobby_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/river")
def deal_river(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.deal_river(lobby_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/lobbies/{lobby_id}/showdown")
def showdown(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        return lm.showdown(lobby_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/lobbies/{lobby_id}")
def delete_lobby(lobby_id: str, lm: LobbyManager = Depends(get_lobby_manager)):
    try:
        lm.delete_lobby(lobby_id)
        return {"message": "Lobby deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/admin/cleanup/empty")
def cleanup_empty_lobbies(lm: LobbyManager = Depends(get_lobby_manager)):
    """Remove all empty lobbies"""
    count = lm.cleanup_empty_lobbies()
    return {"message": f"Cleaned up {count} empty lobbies"}


@router.post("/admin/cleanup/completed")
def cleanup_completed_games(lm: LobbyManager = Depends(get_lobby_manager)):
    """Remove all completed games"""
    count = lm.cleanup_completed_games()
    return {"message": f"Cleaned up {count} completed games"}


@router.post("/admin/cleanup/all")
def cleanup_all(lm: LobbyManager = Depends(get_lobby_manager)):
    """Remove all empty lobbies and completed games"""
    empty_count = lm.cleanup_empty_lobbies()
    completed_count = lm.cleanup_completed_games()
    total = empty_count + completed_count
    return {"message": f"Cleaned up {total} lobbies ({empty_count} empty, {completed_count} completed)"}


