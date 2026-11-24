from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=False)
    
    status = Column(String, nullable=False)  # "PICKED_UP", "IN_TRANSIT", "AT_CHECKPOINT", "DELIVERED"
    location_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    note = Column(String, nullable=True)
    proof_photo_url = Column(String, nullable=True)
    digital_signature = Column(String, nullable=True)
    delivery_otp = Column(String, nullable=True)

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    pool = relationship("Pool", back_populates="tracking_events")

