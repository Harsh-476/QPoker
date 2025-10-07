from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel


class GameStatePublic(BaseModel):
    hand_number: int
    phase: str
    dealer_position: int
    current_player: str
    pot: int
    current_bet: int
    community_cards: List[str]
    players: Dict[str, dict]
    betting_state: dict


