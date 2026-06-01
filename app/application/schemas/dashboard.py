from pydantic import BaseModel
from app.domain.enums.mood_type import MoodType
from app.application.schemas.couple import PartnerPublicResponse
from app.application.schemas.special_dates import SpecialDateResponse
from app.application.schemas.memory import MemoryResponse

class DashboardResponse(BaseModel):
    my_mood: MoodType | None
    partner: PartnerPublicResponse | None
    couple_streak: int
    next_special_date: SpecialDateResponse | None
    today_rituals_completed: int
    today_rituals_total: int
    recent_photos: list[MemoryResponse]
    is_premium_active: bool