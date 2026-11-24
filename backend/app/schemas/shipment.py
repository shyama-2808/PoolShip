from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from app.models.shipment import ShipmentStatus


class ShipmentBase(BaseModel):
    title: str
    goods_type: str
    weight_kg: float = Field(gt=0, description="Weight in kilograms")
    volume_cbm: Optional[float] = Field(default=None, gt=0, description="Volume in cubic meters")
    length_cm: float = Field(default=100.0, gt=0)
    width_cm: float = Field(default=100.0, gt=0)
    height_cm: float = Field(default=100.0, gt=0)
    
    is_perishable: bool = False
    is_hazardous: bool = False
    is_fragile: bool = False
    temperature_class: Optional[Literal["ambient", "chilled", "frozen"]] = Field(
        default="ambient", description="ambient, chilled (2 to 8 °C) or frozen (-18 °C or colder)"
    )

    origin_address: str
    origin_lat: float
    origin_lng: float

    destination_address: str
    dest_lat: float
    dest_lng: float

    delivery_window_start: Optional[datetime] = None
    delivery_window_end: Optional[datetime] = None


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentResponse(ShipmentBase):
    id: int
    shipper_id: int
    pool_id: Optional[int] = None
    recurring_id: Optional[int] = None
    status: ShipmentStatus
    allocated_cost: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
