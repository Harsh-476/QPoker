from __future__ import annotations

from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    player_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)


class PlayerPublic(BaseModel):
    player_id: str
    name: str
    chips: int
    position: int
    is_dealer: bool
    is_small_blind: bool
    is_big_blind: bool
    is_active: bool


