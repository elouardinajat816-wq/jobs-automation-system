from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SubscriberBase(BaseModel):
    email: EmailStr
    preferred_country: str = Field(..., min_length=2, max_length=100)


class SubscriberCreate(SubscriberBase):
    pass


class SubscriberUpdate(BaseModel):
    preferred_country: Optional[str] = Field(None, min_length=2, max_length=100)
    active: Optional[bool] = None


class SubscriberResponse(SubscriberBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListingBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    country: str = Field(..., min_length=2, max_length=100)
    details: str = Field(..., min_length=10)
    contact_link: Optional[str] = None


class JobListingCreate(JobListingBase):
    pass


class JobListingResponse(JobListingBase):
    id: int
    notified: bool
    source_email: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class EmailLogResponse(BaseModel):
    id: int
    recipient: str
    job_id: int
    status: str
    error_message: Optional[str]
    sent_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str = "connected"


def hash_password(password: str) -> str:
    """تشفير كلمة المرور"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    return pwd_context.verify(plain_password, hashed_password)
