from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base


class PoolStatus(str, Enum):
    OPEN = "OPEN"
    OPTIMIZED = "OPTIMIZED"
    LOCKED = "LOCKED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Pool(Base):
    __tablename__ = "pools"

    id = Column(Integer, primary_key=True, index=True)
    truck_id = Column(Integer, ForeignKey("trucks.id"), nullable=False)
    
    status = Column(SQLEnum(PoolStatus), default=PoolStatus.OPEN, nullable=False)
    
    # Aggregated metrics
    total_distance_km = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    current_weight_kg = Column(Float, default=0.0)
    current_volume_cbm = Column(Float, default=0.0)
    utilization_percentage = Column(Float, default=0.0)
    
    # Environmental impact
    co2_saved_kg = Column(Float, default=0.0)
    diesel_saved_litres = Column(Float, default=0.0)

    # Route polyline encoded or geojson
    route_geometry = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    truck = relationship("Truck", back_populates="pools")
    shipments = relationship("Shipment", back_populates="pool")
    tracking_events = relationship("TrackingEvent", back_populates="pool")
