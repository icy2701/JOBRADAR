from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from src.models import StatusEnum, SourceEnum

#User schemas

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        # Allows pydantic to read data from SQLAlchemy model objects
        from_attributes=True

#Auth schemas

class Token(BaseModel):
    access_token: str
    token_type: str="bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


#JobApplication schemas

class JobApplicationCreate(BaseModel):
    job_url: str
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    source: Optional[SourceEnum] = SourceEnum.other
    job_description: Optional[str] = None
    notes: Optional[str] = None

class JobApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    status: Optional[StatusEnum] = None
    notes: Optional[str] = None
    date_applied: Optional[datetime] = None

class JobApplicationResponse(BaseModel):
    id: int
    user_id: int
    company_name: Optional[str]
    role_title: Optional[str]
    source: Optional[SourceEnum]
    job_url: Optional[str]
    job_description: Optional[str]
    status: StatusEnum
    date_applied: Optional[datetime]
    notes: Optional[str]
    resume_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True