from pydantic import BaseModel, field_validator
from datetime import date, datetime
from uuid import UUID
import bleach

class AlbumCreate(BaseModel):
    title: str
    description: str 
    
    @field_validator("title")
    @classmethod
    def sanitize_title(self, v: str) -> str:
        v = bleach.clean(v.strip())
        if not v:
            raise ValueError("Titulo não pode ser vazio")
        if len(v) > 150:
            raise ValueError("Titulo muito longo")
        return v
    
    @field_validator("description")
    @classmethod
    def sanitize_description(self, v: str | None) -> str | None:
        if v is None:
            return v
        return bleach.clean(v.strip())
    
class AlbumUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    
    @field_validator("title")
    @classmethod
    def sanitize_title(self, v: str | None) -> str | None:
        if v is None:
            return v
        v = bleach.clean(v.strip())
        if not v or len(v)> 200:
            raise ValueError("Título inválido")
        return v

class AlbumResponse(BaseModel):
    id: str
    couple_id: str
    title: str
    description: str | None = None
    cover_memory_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}