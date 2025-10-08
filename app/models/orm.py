from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db import Base


class UserORM(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    game_actions = relationship("GameActionORM", back_populates="user")
    game_records = relationship("GameRecordORM", back_populates="winner")


class PlayerORM(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    games_played = Column(Integer, default=0, nullable=False)
    wins = Column(Integer, default=0, nullable=False)


class LobbyORM(Base):
    __tablename__ = "lobbies"

    lobby_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    in_game = Column(Boolean, default=False, nullable=False)
    max_players = Column(Integer, default=4, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GameRecordORM(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True)
    lobby_id = Column(String, ForeignKey("lobbies.lobby_id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    winner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    pot_amount = Column(Integer, default=0, nullable=False)
    
    # Relationships
    winner = relationship("UserORM", back_populates="game_records")


class GameActionORM(Base):
    __tablename__ = "game_actions"

    id = Column(String, primary_key=True)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action_type = Column(String, nullable=False)
    amount = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("UserORM", back_populates="game_actions")


