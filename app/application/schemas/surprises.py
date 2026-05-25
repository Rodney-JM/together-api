from pydantic import BaseModel, field_validator, Field
from app.core.security import sanitize_input
from app.domain.enums.surprise_enums import SurpriseType
from app.domain.enums.surprise_enums import SurpriseStatus
from datetime import datetime
from uuid import UUID

class SurpriseCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    message: str | None = Field(None, max_length=300)
    surprise_type: SurpriseType 
    unlocks_at: datetime | None = Field(None)
    
    @field_validator("title", "message", mode="before")
    @classmethod
    def clean(cls, v: str | None) -> str | None:
        return sanitize_input(v.strip()) if v else None
    
class SurpriseResponse(BaseModel):
    id: UUID
    title: str
    message: str | None = None
    surprise_type: SurpriseType
    status: SurpriseStatus
    unlocks_at: datetime | None = None
    opened_at: datetime | None = None
    sender_id: UUID
    media_s3_key: str | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}
    