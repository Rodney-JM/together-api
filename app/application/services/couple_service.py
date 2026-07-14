import string,secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.couple_models.couple import Couple as CoupleModel
from app.infra.repositories.couple_repo import CoupleRepository
from app.domain.models.user import User
from app.infra.repositories.user_repo import UserRepository

from app.core.exceptions import (
    AlreadyInCoupleError,
    ConflictError,
    NotFoundError
)


class CoupleService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.couples = CoupleRepository(db)
        
    
    async def create_invite(self, user: User) -> dict:
        if user.couple_id:
            raise AlreadyInCoupleError()
        alphabet = string.ascii_uppercase + string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        couple = CoupleModel(invite_code=code)
        new_couple = await self.couples.add(couple)
        user.couple_id = new_couple.id
        await self.db.flush()
        return {"invite_code": code, "couple_id": str(couple.id)}
        
        
    async def join_couple(self, user: User, invite_code: str) -> User:
        if user.couple_id:
            raise AlreadyInCoupleError()
        r = await self.db.execute(
            select(CoupleModel).where(
                CoupleModel.invite_code == invite_code.upper(),
                CoupleModel.is_active == True
            )
        )
        
        couple = r.scalar_one_or_none()
        if not couple:
            raise NotFoundError("Código de convite")
        members = [m for m in couple.members if m.id !=user.id]
        if len(members) >= 2:
            raise ConflictError("Esse relacionamento já está completo")
        user.couple_id = couple.id
        await self.db.flush()
        return user