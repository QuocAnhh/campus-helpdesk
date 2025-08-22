from pydantic import BaseModel, EmailStr
from typing import Optional
import sys
sys.path.append('/app')
from models import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.student

class User(UserBase):
    id: int
    role: UserRole

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User 