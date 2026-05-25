from pydantic import BaseModel, Field
from datetime import datetime
from app.application.schemas.user import UserResponse
from uuid import UUID
from app.domain.enums.mood_type import MoodType

class CoupleInviteResponse(BaseModel):
    invite_code: str
    couple_id: UUID

class JoinCoupleRequest(BaseModel):
    invite_code: str = Field(min_length=6, max_length=12)

class PartnerPublicResponse(BaseModel):
    id: UUID
    display_name: str
    avatar_url: str | None
    current_mood: MoodType | None 
    mood_updated_at: datetime | None
    is_online: bool = False
    
    model_config = {"from_attributes": True}
    
class CoupleResponse(BaseModel):
    id: UUID
    anniversary_date: datetime | None
    current_streak: int
    longest_streak: int
    invite_code: str
    members: list[PartnerPublicResponse]
    
    model_config = {"from_attributes": True}
    
