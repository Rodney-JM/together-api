from pydantic import BaseModel, field_validator, Field
from app.core.security import sanitize_input
from datetime import datetime
from uuid import UUID

class SpecialDateCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    icon: str = Field(default="📅", max_length=10)
    event_date: datetime
    is_recurring_yearly: bool = Field(default=False)
    notify_days_before: int = Field(default=7, ge=0, le=365)
    notes: str | None = Field(None, max_length=300)
    
    @field_validator("title", "notes", mode="before")
    @classmethod
    def clean(cls, v: str | None) -> str | None:
        return sanitize_input(v.strip()) if v else None
    

class SpecialDateUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=150)
    icon: str | None = Field(None, max_length=10)
    event_date: datetime | None = Field(None)
    is_recurring_yearly: bool | None = Field(None)
    notify_days_before: int | None = Field(None, ge=0, le=365)
    notes: str | None = Field(None, max_length=300)
    
class SpecialDateResponse(BaseModel):
    id: UUID
    title: str
    icon: str
    event_date: datetime
    is_recurring_yearly: bool
    notify_days_before: int
    notes: str | None = None
    created_at: datetime
    
    model_config = {"from_attributes": True}    