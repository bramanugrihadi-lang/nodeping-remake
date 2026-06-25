from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# User schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: str = "viewer"


class User(UserBase):
    id: int
    role: str
    
    class Config:
        from_attributes = True


# Target schemas
class TargetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    ip: str = Field(..., min_length=1, max_length=255)
    interval: int = Field(default=60, ge=30, le=3600)
    ping_count: int = Field(default=4, ge=1, le=100)


class TargetCreate(TargetBase):
    pass


class TargetUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    ip: Optional[str] = Field(default=None, min_length=1, max_length=255)
    interval: Optional[int] = Field(default=None, ge=30, le=3600)
    ping_count: Optional[int] = Field(default=None, ge=1, le=100)


class Target(TargetBase):
    id: int
    last_loss: float
    is_online: bool
    
    class Config:
        from_attributes = True


# History schemas
class HistoryItem(BaseModel):
    timestamp: str
    avg_latency: float
    loss: float
    
    class Config:
        from_attributes = True


# Settings schemas
class TelegramSettings(BaseModel):
    token: str
    chat_id: str


class TelegramSettingsResponse(BaseModel):
    token: str = Field(..., description="Masked token (last 4 chars shown)")
    chat_id: str


# Report schemas
class PDFReport(BaseModel):
    id: int
    filename: str
    generated_at: str
    
    class Config:
        from_attributes = True


# Auth schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: User


# Response schemas
class MessageResponse(BaseModel):
    message: str


class SyncStatus(BaseModel):
    targets: List[Target]
    summary: dict
