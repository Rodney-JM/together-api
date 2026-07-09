from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class ConnectedClient:
    def __init__(self, ws: WebSocket, user_id: str, couple_id: str):
        self.ws = ws
        self.user_id = user_id
        self.couple_id = couple_id
        self._ping_task: asyncio.Task | None = None
        
    async def send(self, data: dict[str, Any]) -> bool:
        try:
            await self.ws.send_text(json.dumps(data))
            return True
        except Exception:
            return False
        
    async def start_ping(self) -> None:
        self._ping_task = asyncio.create_task(self._ping_loop())
        
    async def _ping_loop(self) -> None:
        while True:
            await asyncio.sleep(30)
            if not await self.send({"type": "ping"}):
                break
            
    def stop_ping(self) -> None:
        if self._ping_task:
            self._ping_task.cancel()
            
        
class ConectionManager:
    def __init__(self):
        self._rooms: dict[str, list[ConnectedClient]] = defaultdict(list)
    
    async def connect(self, ws: WebSocket, user_id: str, couple_id: str) -> ConnectedClient:
        await ws.accept()
        client = ConnectedClient(ws, user_id, couple_id)
        self._rooms[couple_id].append(client)
        await client.start_ping()
        logger.info("ws_connected", user_id=user_id, couple_id=couple_id)
        return client 
    
    async def disconnect(self, client: ConnectedClient) -> None:
        client.stop_ping()
        room = self._rooms.get(client.couple_id, [])
        if client in room:
            room.remove(client)
        if not room:
            self._rooms.pop(client.couple_id, None)
        logger.info("ws_disconnected", user_id=client.user_id)
    
    async def broadcast_to_couple(
        self, couple_id: str, event: dict[str, Any], exclude_user: str | None = None
    ) -> None:
        dead = []
        for client in self._rooms.get(couple_id, []):
            if exclude_user and client.user_id == exclude_user:
                continue
            if not await client.send(event):
                dead.append(client)
        for c in dead:
            await self.disconnect(c)
            
    
    def get_online_users_in_couple(self, couple_id: str) -> list[str]:
        return [c.user_id for c in self._rooms.get(couple_id, [])]
    
    def is_user_connected(self, user_id: str, couple_id: str) -> bool:
        return any(c.user_id == user_id for c in self._rooms.get(couple_id, []))

ws_manager = ConectionManager()