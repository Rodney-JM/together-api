import redis.asyncio as aioredis

from app.infra.cache.client import _k_premium

class PremiumCache:
    TTL = 300
    
    def __init__(self, r: aioredis.Redis):
        self.r = r
        
    async def set(self, uid: str, is_premium: bool) -> None:
        await self.r.setex(_k_premium(uid), self.TTL, "1" if is_premium else "0")
        
    async def get(self, uid: str) -> bool | None:
        val = await self.r.get(_k_premium(uid))
        if val is None:
            return None
        return val ==  "1"
    
    async def invalidate(self, uid: str) -> None:
        await self.r.delete(_k_premium(uid))