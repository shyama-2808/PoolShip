from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class Truck(Base):
    __tablename__ = "trucks"

    id = Column(Integer, primary_key=True, index=True)
    transporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    truck_type = Column(String, nullable=False)  # e.g., "Tata Ace", "14-ft Canter", "32-ft Container"
    registration_number = Column(String, unique=True, index=True, nullable=False)
    
    # Capacity constraints
    max_weight_kg = Column(Float, nullable=False)
    max_volume_cbm = Column(Float, nullable=False)
    length_cm = Column(Float, default=420.0)
    width_cm = Column(Float, default=200.0)
    height_cm = Column(Float, default=200.0)
    
    # Corridor / Route
    origin_city = Column(String, nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)

    destination_city = Column(String, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lng = Column(Float, nullable=False)

    available_date = Column(DateTime, nullable=False)
    rate_per_km = Column(Float, default=35.0)  # in INR
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    transporter = relationship("User", backref="trucks")
    pools = relationship("Pool", back_populates="truck")

