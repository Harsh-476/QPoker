from __future__ import annotations

from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    player_id: str = Field(..., min_length=1)
    action: str = Field(..., pattern=r"^(fold|check|call|raise)$")
    amount: int = 0  # used when action == 'raise', represents raise-to amount


