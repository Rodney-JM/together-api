from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator, Field
from app.core.security import sanitize_input
from app.domain.enums.letter_status import LetterStatus

class LetterCreateRequest(BaseModel):
    body: str = Field(min_length=10, max_length=10_000)
    
    @field_validator("body", mode="before")
    @classmethod
    def clean(cls, v: str | None) -> str | None:
        return sanitize_input(v.strip()) if v else None
    
class LetterResponse(BaseModel):
    id: UUID
    body: str
    status: LetterStatus
    author_id: UUID
    recipient_id: UUID
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime
    
    model_config = {"from_attributes": True}
    
