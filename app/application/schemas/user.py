from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
import bleach

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    
    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str)-> str:
        v = bleach.clean(v.strip())
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Nome deve ter entre 2 e 100 caracteres")
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve conter pelo menos 8 caracteres")
        if not any(c.isupper() for c in v):
            raise ValueError("A senha deve conter ao menos uma letra maiúscula")
        if not any(c.isdigit() for c in v):
            raise ValueError("A senha deve ter ao menos um número")
        return v
       
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str