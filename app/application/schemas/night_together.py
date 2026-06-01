from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from app.domain.enums.night_session_status import NightSessionStatus

class NightSessionRequest(BaseModel):
    ambient_sound: str = Field(default="silence", max_length=50)
    
class NightSessionResponse(BaseModel):
    id: UUID
    status: NightSessionStatus
    ambient_sound: str
    user1_id: UUID | None
    user1_joined_at: datetime | None
    user2_id: UUID
    user2_joined_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
    