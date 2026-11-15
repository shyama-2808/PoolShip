from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TruckBase(BaseModel):
    truck_type: str
    registration_number: str
    max_weight_kg: float = Field(gt=0)
    max_volume_cbm: float = Field(gt=0)
    length_cm: float = Field(default=420.0, gt=0)
    width_cm: float = Field(default=200.0, gt=0)
    height_cm: float = Field(default=200.0, gt=0)

    origin_city: str
    origin_lat: float
    origin_lng: float

    destination_city: str
    dest_lat: float
    dest_lng: float

    available_date: datetime
    rate_per_km: float = Field(default=35.0, gt=0)


class TruckCreate(TruckBase):
    pass


class TruckResponse(TruckBase):
    id: int
    transporter_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
