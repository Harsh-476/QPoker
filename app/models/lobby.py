from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class LobbyCreate(BaseModel):
    name: str = Field(..., min_length=1)
    max_players: int = Field(4, ge=2, le=4)


class LobbyPublic(BaseModel):
    lobby_id: str
    name: str
    max_players: int
    players: List[str]
    in_game: bool
    game_id: Optional[str] = None


