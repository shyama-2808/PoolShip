from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.engine import FindPoolsResponse

Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_HHMM = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


class RecurringBase(BaseModel):
    title: str
    goods_type: str
    weight_kg: float = Field(gt=0)
    volume_cbm: Optional[float] = Field(default=None, gt=0)
    length_cm: float = Field(default=100.0, gt=0)
    width_cm: float = Field(default=100.0, gt=0)
    height_cm: float = Field(default=100.0, gt=0)
    is_perishable: bool = False
    is_hazardous: bool = False
    is_fragile: bool = False
    temperature_class: Optional[Literal["ambient", "chilled", "frozen"]] = "ambient"

    origin_address: str
    origin_lat: float
    origin_lng: float
    destination_address: str
    dest_lat: float
    dest_lng: float

    repeat: Literal["daily", "weekly"] = Field(default="weekly", description="daily or weekly")
    weekdays: Optional[List[Weekday]] = Field(
        default=None, description='Weekly only: e.g. ["wed", "sat"]. Leave out = the weekday of start_date.')
    start_date: date
    end_date: Optional[date] = Field(default=None, description="Leave out = keeps repeating")
    window_start_time: str = Field(default="09:00", pattern=_HHMM, description="Delivery window opens (IST)")
    window_end_time: str = Field(default="18:00", pattern=_HHMM, description="Delivery window closes (IST)")
    window_days: int = Field(default=1, ge=0, le=14, description="Days after the repeat date the window closes")


class RecurringCreate(RecurringBase):
    @model_validator(mode="after")
    def _check(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date is before start_date")
        if self.window_days == 0 and self.window_end_time <= self.window_start_time:
            raise ValueError("window_end_time must be after window_start_time on the same day (or set window_days)")
        return self


class RecurringResponse(RecurringBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    shipper_id: int
    active: bool
    repeats: str = Field(default="", description="In words, e.g. 'every Wed and Sat'")
    created_at: Optional[datetime] = None

    @field_validator("weekdays", mode="before")
    @classmethod
    def _split(cls, v):
        if isinstance(v, str):
            return [d for d in v.split(",") if d]
        return v


class GeneratedShipment(BaseModel):
    shipment_id: int
    recurring_id: int
    date: date
    title: str
    pool_id: Optional[int] = Field(description="Open pool it joined straight away, or null")
    reason: str


class GenerateResponse(BaseModel):
    from_date: date
    to_date: date
    created: List[GeneratedShipment] = Field(description="New shipments posted for repeat dates")
    already_there: int = Field(description="Repeat dates skipped because their shipment was made before")
    candidate_pools: FindPoolsResponse = Field(
        description="All open shipments not yet in a pool, grouped into candidate pools (same as /engine/route/pools)")
