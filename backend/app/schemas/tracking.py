from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TrackingEventBase(BaseModel):
    status: str
    location_name: str
    latitude: float
    longitude: float
    note: Optional[str] = None
    proof_photo_url: Optional[str] = None
    digital_signature: Optional[str] = None
    delivery_otp: Optional[str] = None


class TrackingEventCreate(TrackingEventBase):
    pool_id: int


class TrackingEventResponse(TrackingEventBase):
    id: int
    pool_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

