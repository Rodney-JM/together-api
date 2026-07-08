from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.core.security import verify_token
from app.domain.models.user import User
from app.infra.cache.presence import PresenceService
from app.infra.cache.watch import WatchStateCache
from app.infra.repositories.user_repo import UserRepository
from app.presentation.websockets