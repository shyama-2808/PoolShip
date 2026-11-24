from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class RecurringShipment(Base):
    """
    A load the shipper sends again and again on the same route (Task 11).
    POST /recurring/generate turns each repeat date into a normal Shipment
    (Shipment.recurring_id points back here).
    """
    __tablename__ = "recurring_shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipper_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # What is sent each time (same fields as Shipment)
    title = Column(String, nullable=False)
    goods_type = Column(String, nullable=False)
    weight_kg = Column(Float, nullable=False)
    volume_cbm = Column(Float, nullable=True)
    length_cm = Column(Float, default=100.0)
    width_cm = Column(Float, default=100.0)
    height_cm = Column(Float, default=100.0)
    is_perishable = Column(Boolean, default=False)
    is_hazardous = Column(Boolean, default=False)
    is_fragile = Column(Boolean, default=False)
    temperature_class = Column(String, default="ambient")

    origin_address = Column(String, nullable=False)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    destination_address = Column(String, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lng = Column(Float, nullable=False)

    # When it repeats
    repeat = Column(String, nullable=False, default="weekly")   # "daily" or "weekly"
    weekdays = Column(String, nullable=True)                    # weekly: "wed,sat"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    # Delivery window of each repeat (IST): opens window_start_time on the day,
    # closes window_end_time window_days later
    window_start_time = Column(String, default="09:00")
    window_end_time = Column(String, default="18:00")
    window_days = Column(Integer, default=1)

    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    shipper = relationship("User")
    shipments = relationship("Shipment", back_populates="recurring")
