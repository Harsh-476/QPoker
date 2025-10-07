"""
Application configuration settings.

Loaded from environment variables with sane defaults so the backend can run
out of the box for development. These settings are intentionally small and
focused to support the minimal viable API and Socket.IO server wiring.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _get_env_bool(var_name: str, default: bool) -> bool:
    value = os.getenv(var_name)
    if value is None:
        return default
    value_lower = value.strip().lower()
    return value_lower in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    # HTTP server
    host: str = os.getenv("QP_HOST", "0.0.0.0")
    port: int = int(os.getenv("QP_PORT", "8000"))
    debug: bool = _get_env_bool("QP_DEBUG", True)

    # CORS
    cors_origins: str = os.getenv("QP_CORS_ORIGINS", "*")

    # Game defaults
    starting_chips: int = int(os.getenv("QP_STARTING_CHIPS", "1000"))
    small_blind: int = int(os.getenv("QP_SMALL_BLIND", "10"))
    big_blind: int = int(os.getenv("QP_BIG_BLIND", "20"))

    # Socket.IO
    socket_path: str = os.getenv("QP_SOCKET_PATH", "/ws/socket.io")
    allow_sid_cookie: bool = _get_env_bool("QP_SOCKET_COOKIE", False)

    # Qiskit
    use_qiskit_simulator: bool = _get_env_bool("QP_USE_QISKIT_SIM", True)


settings = Settings()


