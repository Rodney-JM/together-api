from pydantic import BaseModel, field_validator, Field
from datetime import date, datetime
from app.core.security import sanitize_input
from app.domain.enums.memory_category import MemoryCategory
import bleach

class MemoryCreate(BaseModel):
    title: str = Field(None, max_length=200)
    note: str | None = None
    memory_date: date | None = None
    
    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        v = bleach.clean(v.strip())
        if not v or len(v)> 200:
            raise ValueError("Título inválido.")
        return v
    
    @field_validator("note")
    @classmethod
    def sanitize_body(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return bleach.clean(v.strip(), tags=[], strip=True)
    
    
class MemoryUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    note: str | None = None
    memory_date: date | None = None
    
    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return bleach.clean(v.strip())
    
    @field_validator("note")
    @classmethod
    def sanitize_body(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return bleach.clean(v.strip(), tags=[], strip=True)
    
class MemoryResponse(BaseModel):
    id: str 
    album_id: str
    author_id: str
    title: str | None = None
    note: str | None = None
    memory_date: date | None = None
    media_url: str | None = None
    thumbnail_url: str | None = None
    media_type: str | None = None
    created_at: datetime 
    updated_at: datetime
    
    model_config = {"from_attributes": True}
    
class MemoryUploadRequest(BaseModel):
    caption: str | None = Field(None, max_length=500)
    category: MemoryCategory = MemoryCategory.OTHER
    
    @field_validator("caption", mode="before")
    @classmethod
    def clean(cls, v: str | None) -> str | None:
        return sanitize_input(v.strip()) if v else None
    
class MemoryUpdateRequest(BaseModel):
    caption: str | None = Field(None, max_length=500)
    category: MemoryCategory | None = None
    
    @field_validator("caption", mode="before")
    @classmethod
    def clean(cls, v: str | None) -> str | None:
        return sanitize_input(v.strip()) if v else None