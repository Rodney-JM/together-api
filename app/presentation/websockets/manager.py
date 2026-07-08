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