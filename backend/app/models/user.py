from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from app.db.base import Base


class UserRole(str, Enum):
    SHIPPER = "SHIPPER"
    TRANSPORTER = "TRANSPORTER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.SHIPPER)
    
    # Business / Trust features
    company_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    rating = Column(Integer, default=5)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
