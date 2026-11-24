from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.pool import PoolStatus
from app.schemas.shipment import ShipmentResponse
from app.schemas.truck import TruckResponse
from app.schemas.engine import SplitMethod


class PoolBase(BaseModel):
    truck_id: int


class PoolCreate(PoolBase):
    shipment_ids: List[int] = []
    split_method: SplitMethod = Field(
        default="ton_km",
        description="How the trip cost is shared: weight, volume, distance or ton_km",
    )


class PoolResponse(BaseModel):
    id: int
    truck_id: int
    status: PoolStatus
    split_method: Optional[str] = None
    total_distance_km: float
    total_cost: float
    current_weight_kg: float
    current_volume_cbm: float
    utilization_percentage: float
    co2_saved_kg: float
    diesel_saved_litres: float
    route_geometry: Optional[str] = None
    created_at: datetime
    shipments: List[ShipmentResponse] = []
    truck: Optional[TruckResponse] = None

    class Config:
        from_attributes = True


class OptimizationItem(BaseModel):
    id: int
    weight_kg: float
    volume_cbm: float
    allocated_cost: float
    fits: bool
    reason: Optional[str] = None


class PoolOptimizationResult(BaseModel):
    truck_id: int
    split_method: str
    total_weight_kg: float
    total_volume_cbm: float
    weight_utilization_pct: float
    volume_utilization_pct: float
    overall_utilization_pct: float
    total_trip_cost: float
    total_co2_saved_kg: float
    total_diesel_saved_litres: float
    packed_shipments: List[OptimizationItem]
    unpacked_shipments: List[OptimizationItem]
