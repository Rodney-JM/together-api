from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.schemas.night_together import (
    NightSessionRequest,
    NightSessionResponse,
)
from app.application.services.domain_services.night_service import NightService
from app.core.dependencies.auth import require_couple
from app.domain.models.user import User
from app.infra.db.session import get_db_session

router = APIRouter(prefix="/night", tags=["Night"])

CoupleUser = Annotated[User, Depends(require_couple)]


@router.post("/start-or-join", response_model=NightSessionResponse)
async def start_or_join(
    payload: NightSessionRequest,
    user: CoupleUser,
    db: AsyncSession = Depends(get_db_session),
) -> NightSessionResponse:
    service = NightService(db)
    return await service.start_or_join(user, payload)


@router.post("/{session_id}/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(
    session_id: UUID,
    user: CoupleUser,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = NightService(db)
    await service.end(user, session_id)


@router.get("/active", response_model=NightSessionResponse | None)
async def get_active(
    user: CoupleUser,
    db: AsyncSession = Depends(get_db_session),
) -> NightSessionResponse | None:
    service = NightService(db)
    return await service.get_active(user)
