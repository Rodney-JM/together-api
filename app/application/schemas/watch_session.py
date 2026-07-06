from pydantic import BaseModel, Field, field_validator
from app.core.security import sanitize_input
from uuid import UUID
from datetime import datetime

class WatchSessionCreateRequest(BaseModel):
    media_title: str = Field(min_length=1, max_length=200)
    media_url: str | None = Field(None, max_length=1000)
    media_type: str = Field(default="external", max_length=30)
    
    @field_validator("media_title", mode="before")
    @classmethod
    def clean(cls, v: str) -> str | None:
        return sanitize_input(v.strip()) if v else None
    

class WatchSessionResponse(BaseModel):
    id: UUID
    media_title: str
    media_url: str | None
    media_type: str
    is_playing: bool
    current_position_seconds: float
    couple_id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}