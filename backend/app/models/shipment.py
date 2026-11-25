from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.db.base import Base


class ShipmentStatus(str, Enum):
    POSTED = "POSTED"
    MATCHED = "MATCHED"
    POOLED = "POOLED"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipper_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pool_id = Column(Integer, ForeignKey("pools.id"), nullable=True)
    # Set when this shipment is one repeat of a recurring shipment (Task 11)
    recurring_id = Column(Integer, ForeignKey("recurring_shipments.id"), nullable=True)

    title = Column(String, nullable=False)
    goods_type = Column(String, nullable=False)  # e.g., "textiles", "hardware", "perishable"
    
    # Dimensions & weight
    weight_kg = Column(Float, nullable=False)
    volume_cbm = Column(Float, nullable=True)
    length_cm = Column(Float, default=100.0)
    width_cm = Column(Float, default=100.0)
    height_cm = Column(Float, default=100.0)

    # Constraints / Compatibility rules
    is_perishable = Column(Boolean, default=False)
    is_hazardous = Column(Boolean, default=False)
    is_fragile = Column(Boolean, default=False)
    # "ambient", "chilled" (2 to 8 °C) or "frozen" (-18 °C); chilled and frozen can't share a truck
    temperature_class = Column(String, default="ambient", nullable=True)

    # Locations
    origin_address = Column(String, nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)

    destination_address = Column(String, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lng = Column(Float, nullable=False)

    # Timing
    delivery_window_start = Column(DateTime(timezone=True), nullable=True)
    delivery_window_end = Column(DateTime(timezone=True), nullable=True)

    status = Column(SQLEnum(ShipmentStatus), default=ShipmentStatus.POSTED, nullable=False)
    allocated_cost = Column(Float, nullable=True)  # Allocated share from pool
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    shipper = relationship("User", backref="shipments")
    pool = relationship("Pool", back_populates="shipments")
    recurring = relationship("RecurringShipment", back_populates="shipments")
