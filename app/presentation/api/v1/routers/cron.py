import hmac

from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import settings
from app.core.logging_config import get_logger
from app.core.dependencies.auth import DBSession

from sqlalchemy import select, update, delete
from app.domain.models.session_models.surprise import Surprise, SurpriseStatus
from app.domain.models.couple_models.couple import Couple
from app.domain.models.ritual import Ritual, RitualStatus
from app.domain.models.couple_models.refresh_token import RefreshToken

logger = get_logger(__name__)

router = APIRouter(prefix="/internal/cron", tags=["Internal Cron"])

def _verify_cron_secret(x_cron_secret: str = Header(...)) -> None:
    if not settings.CRON_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cron secret not configured")
    if not hmac.compare_digest(x_cron_secret, settings.CRON_SECRET):
        logger.warning("cron_secret_mismatch")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron secret")
    

@router.post("/unlock-surprises")
async def unlock_due_surprises(
    db: DBSession,
    x_cron_secret: str = Header(...)
) -> dict:
    _verify_cron_secret(x_cron_secret)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Surprise).where(
            Surprise.status == SurpriseStatus.LOCKED,
            Surprise.unlocks_at <= now
        )
    )
    surprises = result.scalars().all()
    
    unlocked = 0
    for surprise in surprises:
        surprise.status = SurpriseStatus.DELIVERED
        unlocked+=1
        
    logger.info("cron_unlock_surprises", unlocked=unlocked)
    return {"unlocked": unlocked, "ran_at": now.isoformat()}

@router.post("/recalculate-streaks")
async def recalculate_streaks(
    db: DBSession,
    x_cron_secret: str = Header(...),
) -> dict:
    _verify_cron_secret(x_cron_secret)
    
    result = await db.execute(
        select(Couple).where(
            Couple.is_active == True,
        )
    )
    couples = result.scalars().all()
    
    updated = 0
    for couple in couples:
        rituals_r = await db.execute(
            select(Ritual).where(
                Ritual.couple_id == couple.id,
                Ritual.is_active == True
            )
        )
        rituals = rituals_r.scalars().all()
        streaks = [r.current_streak for r in rituals]
        couple.current_streak = min(streaks) if streaks else 0
        if couple.current_streak > couple.longest_streak:
            couple.longest_streak = couple.current_streak
        couple.last_activity_date = datetime.now(timezone.utc)
        updated +=1
    
    logger.info("cron_recalculate_streaks", couples_updated=updated)
    return {"couples_updated": updated, "ran_at": datetime.now(timezone.utc).isoformat()}

@router.post("/cleanup-tokens")
async def cleanup_expired_tokens(
    db: DBSession,
    x_cron_secret: str = Header(...)
) -> dict:
    _verify_cron_secret(x_cron_secret)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        delete(RefreshToken).where(
            (RefreshToken.expires_at < now) | (RefreshToken.revoked == True)
        )
    )
    
    deleted = result.rowcount
    logger.info("cron_cleanup_tokens", deleted=deleted)
    return {"deleted": deleted, "ran_at": now.isoformat()}