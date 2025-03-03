from dataclasses import dataclass
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String)
    partner_id = Column(String)
    comment = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime, nullable=True)

@dataclass
class ReviewCreate(BaseModel):
    client_id: str
    partner_id: str
    comment: str

@dataclass
class ReviewResponse(BaseModel):
    id: int
    client_id: str
    partner_id: str
    comment: str
    created_at: datetime
    updated_at: Optional[datetime] = None

@dataclass
class ReviewUpdate(BaseModel):
    comment: Optional[str] = None 