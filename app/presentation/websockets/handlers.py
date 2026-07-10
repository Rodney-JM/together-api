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
from app.presentation.websockets.manager import ConectionManager, ConnectedClient

logger = get_logger(__name__)

async def _authenticate(token: str, db: AsyncSession) -> User | None:
    try:
        payload = verify_token(token, token_type="access")
        return await UserRepository(db).get_by_id(UUID(payload["sub"]))
    except Exception:
        return None

async def handle_couple_ws(
    ws: WebSocket, token: str, db: AsyncSession,
    redis: aioredis.Redis, manager: ConectionManager
) -> None:
    user = await _authenticate(token, db)
    if not user or not user.couple_id or not user.is_active:
        await ws.close(code=4001, reason="Unauthorized")
        return
    
    uid = str(user.id)
    cid = str(user.couple_id)
    presence = PresenceService(redis)
    watch_cache = WatchStateCache(redis)
    
    client: ConnectedClient = await manager.connect(ws, uid, cid)
    await presence.set_online(uid)
    await manager.broadcast_to_couple(cid, {"type": "presence", "user_id": uid, "online": True}, exclude_user=uid)
    
    try:
        while True:
            raw = await ws.receive_text()
            await _dispatch(raw, client, uid, cid, manager, presence, watch_cache)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(client)
        await presence.set_offline(uid)
        await manager.broadcast_to_couple(cid, {"type": "presence", "user_id": uid, "online": False})

async def _dispatch(
    raw: str, client: ConnectedClient, uid: str, cid: str,
    manager: ConectionManager, presence: PresenceService, watch_cache: WatchStateCache
) -> None:
    try:
        msg: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        await client.send({"type": "error", "detail": "Invalid JSON"})
        return
    
    t = msg.get("type")
    
    if t == "pong":
        await presence.set_online(uid)
    
    elif t == "mood_update":
        await manager.broadcast_to_couple(cid, {
            "type": "mood_updated", "user_id": uid,
            "mood": msg.get("mood"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
    
    elif t == "watch_sync":
        state = {"action": msg.get("action"), "position": msg.get("position", 0),
                 "user_id": uid, "timestamp": datetime.now(timezone.utc).isoformat()}
        await watch_cache.set_state(cid, state)
        await manager.broadcast_to_couple(cid, {"type": "watch_sync", **state}, exclude_user=uid)
    
    elif t == "night_ambient":
        await manager.broadcast_to_couple(cid, {
            "type": "night_ambient", "ambient_sound": msg.get("ambient_sound", "silence"), "user_id": uid
        }, exclude_user=uid)
    
    elif t == "typing":
        await manager.broadcast_to_couple(cid, {"type": "typing", "user_id": uid}, exclude_user=uid)
        
    else:
        await client.send({"type": "error", "detail": f"Unknown event: {t}"})