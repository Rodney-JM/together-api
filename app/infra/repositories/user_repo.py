from uuid import UUID
from sqlalchemy import select

from app.domain.models.user import User
from app.infra.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    model = User
    
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email== email.lower())
        )
        
        return result.scalar_one_or_none()
    
    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> User | None:
        r = await self.session.execute(
            select(User).where(User.stripe_customer_id == stripe_customer_id)
        )
        
        return r.scalar_one_or_none()
    
    async def get_couple_partner(self, user: User) -> User | None:
        if not user.couple_id:
            return None
        result = await self.session.execute(
            select(User).where(
                User.couple_id == user.couple_id,
                User.id != user.id
            )
        )
        
        return result.scalar_one_or_none()