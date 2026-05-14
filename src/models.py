from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import enum

class StatusEnum(str,enum.Enum):
    saved      = "saved"
    applied    = "applied"
    interview  = "interview"
    offer      = "offer"
    rejected   = "rejected"
    withdrawn  = "withdrawn"

class SourceEnum(str, enum.Enum):
    linkedin   = "linkedin"
    indeed     = "indeed"
    monster    = "monster"
    stepstone  = "stepstone"
    xing       = "xing"
    other      = "other"


class User(Base):

    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    applications    = relationship("JobApplication", back_populates="owner")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)

    company_name    = Column(String, nullable=False)
    role_title      = Column(String, nullable=False)
    source          = Column(Enum(SourceEnum), default=SourceEnum.other)
    job_url         = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)

    status          = Column(Enum(StatusEnum), default=StatusEnum.saved)
    date_applied    = Column(DateTime(timezone=True), nullable=True)
    notes           = Column(Text, nullable=True)
    resume_url      = Column(String, nullable=True)

    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    owner           = relationship("User", back_populates="applications")
