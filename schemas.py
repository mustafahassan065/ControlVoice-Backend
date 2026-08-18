from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    plan: str
    onboarding_completed: Optional[int] = 0
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
    onboarding_required: Optional[bool] = False

class RecordingOut(BaseModel):
    id: int
    user_id: int
    audio_url: str
    duration: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True