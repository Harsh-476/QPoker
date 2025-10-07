from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class GatePreviewRequest(BaseModel):
    player_id: str = Field(..., min_length=1)
    gate: str = Field(..., pattern=r"^(X|Z|CNOT|H)$")
    card_indices: List[int] = Field(..., min_items=1, max_items=2)


class GateApplyRequest(GatePreviewRequest):
    preview_only: bool = False


