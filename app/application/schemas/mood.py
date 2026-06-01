from pydantic import BaseModel, Field
from datetime import datetime
from app.domain.enums.mood_type import MoodType
from uuid import UUID

class MoodUpdateRequest(BaseModel):
    mood: MoodType
    
class MoodResponse(BaseModel):
    user_id: UUID
    mood: MoodType
    updated_at: datetime