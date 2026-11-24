"""
Request/response shapes for the /engine endpoints.

These endpoints run the logistics engine directly on the data you send.
They do not read or write the database, so they work as soon as the API is up.
Units: weight kg, volume m³ (cbm), dimensions cm, distance km, money ₹.
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class EngineShipment(BaseModel):
    id: int
    weight_kg: float = Field(gt=0)
    volume_cbm: Optional[float] = Field(default=None, gt=0, description="If left out, worked out from the dimensions")
    length_cm: float = Field(default=100.0, gt=0)
    width_cm: float = Field(default=100.0, gt=0)
    height_cm: float = Field(default=100.0, gt=0)
    is_perishable: bool = False
    is_hazardous: bool = False
    is_fragile: bool = False
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None


class EngineShipmentWithRoute(EngineShipment):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float


class EngineTruck(BaseModel):
    id: int
    max_weight_kg: float = Field(gt=0)
    max_volume_cbm: float = Field(gt=0)
    length_cm: float = Field(default=420.0, gt=0)
    width_cm: float = Field(default=200.0, gt=0)
    height_cm: float = Field(default=200.0, gt=0)
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    dest_lat: Optional[float] = None
    dest_lng: Optional[float] = None
    rate_per_km: float = Field(default=35.0, gt=0, description="₹ per km")


class EngineTruckWithRoute(EngineTruck):
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float


# ---- 1. Compatibility -------------------------------------------------------
class CompatibilityRequest(BaseModel):
    existing_items: List[EngineShipment] = Field(description="Shipments already in the truck")
    candidate: EngineShipment = Field(description="Shipment we want to add")


class CompatibilityResponse(BaseModel):
    compatible: bool
    reason: str


# ---- 2. Load optimisation (bin-packing) ---------------------------------------
class OptimizeLoadRequest(BaseModel):
    truck: EngineTruck
    shipments: List[EngineShipment]


class PackedItem(BaseModel):
    id: int
    weight_kg: float
    volume_cbm: float


class UnpackedItem(PackedItem):
    reason: str


class OptimizeLoadResponse(BaseModel):
    truck_id: int
    total_packed_weight_kg: float
    total_packed_volume_cbm: float
    weight_utilization_pct: float
    volume_utilization_pct: float
    overall_utilization_pct: float
    packed_items: List[PackedItem]
    unpacked_items: List[UnpackedItem]


# ---- 3. Cost split ------------------------------------------------------------
class CostSplitShipment(BaseModel):
    id: int
    weight_kg: float = Field(ge=0)
    distance_km: float = Field(default=1.0, ge=0, description="How far this shipment travels")
    volume_cbm: Optional[float] = Field(default=None, ge=0)


class CostSplitRequest(BaseModel):
    total_trip_cost: float = Field(gt=0, description="Total ₹ for the truck trip")
    shipments: List[CostSplitShipment]
    split_method: Literal["ton_km", "weight", "volume"] = "ton_km"


class CostShare(BaseModel):
    shipment_id: int
    share_ratio: float
    allocated_cost: float
    savings_vs_dedicated_trip: float
    savings_percentage: Optional[float] = None
    ton_km: Optional[float] = None


class CostSplitResponse(BaseModel):
    split_method: str
    total_trip_cost: float
    shares: List[CostShare]


# ---- 4. Carbon ----------------------------------------------------------------
class CarbonRequest(BaseModel):
    pooled_route_distance_km: float = Field(gt=0)
    num_participants: int = Field(ge=1, description="Number of shippers sharing the truck")
    detour_km: float = Field(default=0.0, ge=0)


class CarbonResponse(BaseModel):
    baseline_truck_km: float
    pooled_truck_km: float
    km_avoided: float
    diesel_saved_litres: float
    co2_saved_kg: float
    co2_reduction_percentage: float


# ---- 5. Route helpers ---------------------------------------------------------
class Point(BaseModel):
    lat: float
    lng: float


class DistanceRequest(BaseModel):
    origin: Point
    destination: Point


class DistanceResponse(BaseModel):
    straight_line_km: float
    estimated_road_km: float


class CorridorCheckRequest(BaseModel):
    pickup: Point
    drop: Point
    truck_start: Point
    truck_end: Point
    corridor_tolerance_km: float = Field(default=25.0, gt=0)


class CorridorCheckResponse(BaseModel):
    on_corridor: bool
    pickup_offset_km: float
    drop_offset_km: float
    corridor_tolerance_km: float


class RoadRouteRequest(BaseModel):
    stops: List[Point] = Field(min_length=2, description="Stops in driving order")
    use_osrm: bool = Field(
        default=True,
        description="Ask the online OSRM map service. If false or offline, uses a straight-line estimate.",
    )


class RoadRouteResponse(BaseModel):
    distance_km: float
    duration_minutes: float
    source: Literal["osrm", "estimate"]
    geometry: Optional[dict] = None


class RouteMatchRequest(BaseModel):
    truck: EngineTruckWithRoute
    shipments: List[EngineShipmentWithRoute]
    corridor_tolerance_km: float = Field(default=40.0, gt=0)


class RouteMatch(BaseModel):
    shipment_id: int
    pickup_offset_km: float
    drop_offset_km: float
    shipment_distance_km: float


class RouteReject(BaseModel):
    shipment_id: int
    reason: str


class RouteMatchResponse(BaseModel):
    truck_route_km: float
    corridor_tolerance_km: float
    matched: List[RouteMatch]
    rejected: List[RouteReject]


# ---- Route matching: group shipments into pools (no truck needed) ------------
class PoolShipment(EngineShipmentWithRoute):
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    delivery_window_start: Optional[datetime] = Field(default=None, description="Earliest delivery time. Leave out for 'any time'.")
    delivery_window_end: Optional[datetime] = Field(default=None, description="Latest delivery time. Leave out for 'any time'.")


class FindPoolsRequest(BaseModel):
    shipments: List[PoolShipment] = Field(description="Open shipments to group")
    corridor_tolerance_km: float = Field(default=40.0, gt=0, description="How far (km) a pickup or drop may be from the common path")


class PathPoint(Point):
    place: Optional[str] = None


class CommonPath(BaseModel):
    from_: PathPoint = Field(alias="from")
    to: PathPoint
    estimated_road_km: float
    based_on_shipment_id: int


class DeliveryWindow(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class PoolMember(BaseModel):
    shipment_id: int
    pickup_offset_km: float = Field(description="Distance from the pickup to the common path")
    drop_offset_km: float = Field(description="Distance from the drop to the common path")
    shipment_distance_km: float


class CandidatePool(BaseModel):
    pool_id: int
    shipment_ids: List[int]
    common_path: CommonPath
    shared_delivery_window: DeliveryWindow
    total_weight_kg: float
    total_volume_cbm: float
    members: List[PoolMember]


class UnmatchedShipment(BaseModel):
    shipment_id: int
    reason: str


class FindPoolsResponse(BaseModel):
    corridor_tolerance_km: float
    pools: List[CandidatePool]
    unmatched: List[UnmatchedShipment]


# ---- 6. Whole pipeline --------------------------------------------------------
class PlanPoolRequest(BaseModel):
    truck: EngineTruckWithRoute
    shipments: List[EngineShipmentWithRoute]
    corridor_tolerance_km: float = Field(default=40.0, gt=0)
    split_method: Literal["ton_km", "weight", "volume"] = "ton_km"


class PlanPoolResponse(BaseModel):
    truck_id: int
    truck_route_km: float
    total_trip_cost: float
    route: RouteMatchResponse
    load: OptimizeLoadResponse
    cost_split: CostSplitResponse
    carbon: CarbonResponse
