from pydantic import BaseModel, field_validator
from datetime import date, datetime
from fastapi import UploadFile
import bleach

class MemoryCreate(BaseModel):
    title: str
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
    title: str | None = None
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