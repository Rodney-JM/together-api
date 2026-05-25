from pydantic import BaseModel, field_validator, Field
from app.core.security import sanitize_input
from app.domain.enums.ritual_status import RitualStatus
from datetime import datetime
from uuid import UUID

class RitualCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str | None = Field(None, max_length=300)
    icon: str = Field(default="✨", max_length=10)
    
    @field_validator("title", "description", mode="before")
    @classmethod
    def clean(cls, v: str | None) -> str | None:
        return sanitize_input(v.strip()) if v else None

class RitualUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=300)
    icon: str | None = Field(None, max_length=10)
    is_active: bool | None = Field(None)

class RitualResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    icon: str
    is_active: bool
    current_streak: int
    longest_streak: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class RitualEntryRequest(BaseModel):
    status: RitualStatus = RitualStatus.COMPLETED
    note: str | None = Field(None, max_length=300)
    
    @field_validator("note", mode="before")
    @classmethod
    def clean(cls, v: str | None) -> str | None:
        return sanitize_input(v.strip()) if v else None

class RitualWithStatusResponse(BaseModel):
    ritual: RitualResponse
    my_status: RitualStatus | None
    partner_status: RitualStatus | None