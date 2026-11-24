"""
Request/response shapes for the /engine endpoints.

These endpoints run the logistics engine directly on the data you send.
They do not read or write the database, so they work as soon as the API is up.
Units: weight kg, volume m³ (cbm), dimensions cm, distance km, money ₹.
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

# How a pool's trip cost is shared between shippers
SplitMethod = Literal["weight", "volume", "distance", "ton_km"]
# Temperature a shipment must travel at
TemperatureClass = Literal["ambient", "chilled", "frozen"]


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
    goods_type: Optional[str] = Field(
        default=None, description="e.g. textiles, perishable, chemicals, grains, construction (see /engine/compatibility/rules)"
    )
    temperature_class: TemperatureClass = Field(
        default="ambient", description="ambient, chilled (2 to 8 °C) or frozen (-18 °C or colder)"
    )
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
    cautions: List[str] = Field(default=[], description="Allowed, but with a handling note")


class PoolCompatibilityRequest(BaseModel):
    shipments: List[EngineShipment] = Field(min_length=1, description="Shipments you want to pool together")


class Conflict(BaseModel):
    shipment_ids: List[int]
    severity: Literal["block", "caution"]
    rule: str
    reason: str


class ShipmentFlags(BaseModel):
    shipment_id: int
    flags: List[str] = Field(description="fragile, chilled, frozen, hazardous")
    handling: List[str]


class PoolCompatibilityResponse(BaseModel):
    compatible: bool = Field(description="False if any two shipments can't share a truck")
    reason: str
    conflicts: List[Conflict] = Field(description="Pairs that can't share a truck")
    cautions: List[Conflict] = Field(description="Pairs that may share, with care")
    flags: List[ShipmentFlags]


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


# ---- 2b. Spread a pool over several trucks (first-fit decreasing) --------------
class AssignTrucksRequest(BaseModel):
    trucks: List[EngineTruck] = Field(min_length=1, description="Trucks to fill, preferred first")
    shipments: List[EngineShipment] = Field(description="The pool's shipments")


class TruckLoad(BaseModel):
    truck_id: int
    shipment_ids: List[int]
    packed_items: List[PackedItem]
    total_weight_kg: float
    total_volume_cbm: float
    remaining_weight_kg: float
    remaining_volume_cbm: float
    weight_utilization_pct: float
    volume_utilization_pct: float
    overall_utilization_pct: float = Field(description="Fill %: the higher of weight % and volume %")


class AssignTrucksResponse(BaseModel):
    trucks_used: int
    trucks: List[TruckLoad]
    leftover_items: List[UnpackedItem] = Field(description="Shipments that fit no truck, with the reason")


# ---- 3. Cost split ------------------------------------------------------------
class CostSplitShipment(BaseModel):
    id: int
    weight_kg: float = Field(ge=0)
    distance_km: float = Field(default=1.0, ge=0, description="How far this shipment travels")
    volume_cbm: Optional[float] = Field(default=None, ge=0)


class CostSplitRequest(BaseModel):
    total_trip_cost: Optional[float] = Field(
        default=None, gt=0,
        description="Total ₹ for the truck trip. Leave out to work it out as trip_distance_km × rate_per_km.",
    )
    trip_distance_km: Optional[float] = Field(default=None, gt=0, description="Truck trip length (km)")
    rate_per_km: Optional[float] = Field(default=None, gt=0, description="Truck's ₹ per km")
    shipments: List[CostSplitShipment] = Field(min_length=1)
    split_method: SplitMethod = Field(
        default="ton_km",
        description="weight (kg), volume (m³), distance (km travelled) or ton_km (tonnes × km)",
    )

    @model_validator(mode="after")
    def _need_a_cost(self):
        if self.total_trip_cost is None and (self.trip_distance_km is None or self.rate_per_km is None):
            raise ValueError("Give total_trip_cost, or both trip_distance_km and rate_per_km")
        return self


class CostShare(BaseModel):
    shipment_id: int
    share_ratio: float
    allocated_cost: float = Field(description="₹ this shipper pays")
    allocated_paise: int = Field(description="Same amount in paise; these add up exactly to the trip cost")
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


class CarbonCompareRequest(BaseModel):
    separate_trip_km: List[float] = Field(
        min_length=1,
        description="Each shipper's own trip in km (what their own truck would drive without pooling)",
    )
    pooled_truck_km: float = Field(ge=0, description="Km the one shared truck drives, detours included")

    @model_validator(mode="after")
    def _no_negative_trips(self):
        if any(k < 0 for k in self.separate_trip_km):
            raise ValueError("separate_trip_km values must be 0 or more")
        return self


class EmissionFactors(BaseModel):
    diesel_litres_per_km: float
    km_per_litre: float
    kg_co2_per_litre_diesel: float
    kg_co2_per_km: float
    source: str


class CarbonResponse(BaseModel):
    """Separate trucks (baseline) versus one pooled truck."""
    num_shipments: int
    baseline_trucks: int
    baseline_truck_km: float
    pooled_truck_km: float
    km_avoided: float
    baseline_diesel_litres: float
    pooled_diesel_litres: float
    diesel_saved_litres: float
    baseline_co2_kg: float
    pooled_co2_kg: float
    co2_saved_kg: float
    fuel_saved_percentage: float
    co2_reduction_percentage: float
    emission_factors: EmissionFactors


class SeparateTrip(BaseModel):
    shipment_id: int
    km: float
    diesel_litres: float
    co2_kg: float


class PoolCarbonResponse(CarbonResponse):
    pool_id: int
    truck_id: int
    separate_trips: List[SeparateTrip]


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


# ---- Task 6: multi-stop route (order pickups and drops) -----------------------
class StopShipment(BaseModel):
    id: int
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None


class OptimizeStopsRequest(BaseModel):
    shipments: List[StopShipment] = Field(min_length=1, description="The pool's shipments")
    start: Optional[PathPoint] = Field(default=None, description="Where the truck starts (e.g. its depot). Leave out to start at the best pickup.")
    end: Optional[PathPoint] = Field(default=None, description="Where the truck must finish. Leave out to finish at the last drop.")
    use_osrm: bool = Field(
        default=True,
        description="Ask the online OSRM map service for road km. If false or offline, uses straight line x 1.25.",
    )


class RouteStop(BaseModel):
    seq: int = Field(description="1 = first stop")
    kind: Literal["start", "pickup", "drop", "end"]
    shipment_id: Optional[int] = None
    lat: float
    lng: float
    place: Optional[str] = None
    leg_km: float = Field(description="Km from the previous stop")
    cumulative_km: float
    leg_minutes: float
    cumulative_minutes: float


class OptimizeStopsResponse(BaseModel):
    stops: List[RouteStop] = Field(description="Stops in the order to drive them; every pickup comes before its drop")
    total_km: float
    total_minutes: float = Field(description="Driving time only (OSRM, or 45 km/h estimate)")
    as_listed_km: float = Field(description="Km if you drove all pickups as listed, then all drops as listed")
    km_saved: float
    saved_percentage: float
    method: Literal["exact", "heuristic"] = Field(description="exact up to 6 shipments, heuristic above")
    distance_source: Literal["osrm", "estimate"]


# ---- Task 8: loads for the empty trip home -------------------------------------
class TimedTruck(EngineTruckWithRoute):
    origin_city: Optional[str] = None
    destination_city: Optional[str] = None
    available_date: Optional[datetime] = Field(
        default=None, description="When the truck leaves on its outbound trip. Leave out to skip the on-time check.")


class ReturnTripTruck(TimedTruck):
    return_dest_lat: Optional[float] = Field(default=None, description="Home base if not the origin")
    return_dest_lng: Optional[float] = None
    return_city: Optional[str] = None


class ReturnTripRequest(BaseModel):
    truck: ReturnTripTruck
    shipments: List[PoolShipment] = Field(description="Open shipments to look through")
    corridor_tolerance_km: float = Field(default=40.0, gt=0)
    unloading_hours: float = Field(default=2.0, ge=0, description="Time to unload at the destination before heading home")


class ReturnRoute(BaseModel):
    from_: PathPoint = Field(alias="from")
    to: PathPoint
    outbound_km: float
    return_km: float
    departs_at: Optional[datetime] = Field(description="Outbound drive (45 km/h) + unloading, after available_date")
    arrives_home_at: Optional[datetime] = None


class ReturnMatch(BaseModel):
    shipment_id: int
    weight_kg: float
    shipment_distance_km: float
    estimated_drop_at: Optional[datetime] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    pays: float = Field(description="₹ share of the return trip (tonnes x km)")


class ReturnLoad(BaseModel):
    total_weight_kg: float
    total_volume_cbm: float
    overall_utilization_pct: float


class ReturnTripResponse(BaseModel):
    truck_id: int
    return_route: ReturnRoute
    corridor_tolerance_km: float
    matched: List[ReturnMatch] = Field(description="Shipments the truck can carry home: on the route, on time and fitting")
    rejected: List[RouteReject]
    load: ReturnLoad
    stop_plan: Optional[OptimizeStopsResponse] = None
    return_trip_earnings: float = Field(description="Return km x rate, now paid by the matched shippers instead of nobody")
    is_empty_return: bool


# ---- Task 9: dynamic pricing -----------------------------------------------------
Urgency = Literal["standard", "express", "urgent"]


class PriceShipment(EngineShipment):
    distance_km: Optional[float] = Field(default=None, gt=0, description="Leave out to estimate it from the coordinates")


class PriceRequest(BaseModel):
    shipment: PriceShipment
    truck: EngineTruck
    truck_fill_pct: float = Field(default=50.0, ge=0, le=100, description="How full the truck already is before this shipment")
    urgency: Urgency = "standard"
    hours_until_deadline: Optional[float] = Field(
        default=None, gt=0, description="If given, urgency is worked out from it instead")
    open_shipments_on_route: Optional[int] = Field(default=None, ge=0, description="Demand: open shipments on this route")
    trucks_available_on_route: Optional[int] = Field(default=None, ge=0, description="Supply: trucks on this route")

    @model_validator(mode="after")
    def _need_distance(self):
        s = self.shipment
        if s.distance_km is None and None in (s.origin_lat, s.origin_lng, s.dest_lat, s.dest_lng):
            raise ValueError("Give shipment.distance_km, or its origin and destination coordinates")
        return self


class PriceFactor(BaseModel):
    factor: float
    why: str


class UrgencyFactor(PriceFactor):
    level: Urgency


class PriceFactors(BaseModel):
    demand: PriceFactor
    urgency: UrgencyFactor
    fill: PriceFactor


class PriceLimits(BaseModel):
    min_multiplier: float
    max_multiplier: float


class PriceResponse(BaseModel):
    shipment_km: float
    space_share_pct: float = Field(description="Share of the truck it uses: higher of weight % and volume %")
    base_price: float = Field(description="₹ = km x rate x space share")
    factors: PriceFactors
    raw_multiplier: float = Field(description="demand x urgency x fill, before the limits")
    multiplier: float = Field(description="raw_multiplier kept between the limits")
    capped: Optional[Literal["at maximum", "at minimum"]] = None
    limits: PriceLimits
    price: float = Field(description="₹ = base_price x multiplier")


class PriceScenario(BaseModel):
    scenario: str
    price: float
    multiplier: float
    capped: Optional[str] = None


class PriceScenariosResponse(BaseModel):
    shipment_id: int
    truck_id: int
    base_price: float
    scenarios: List[PriceScenario]


# ---- Task 10: ETA and delay prediction ---------------------------------------------
DelayFlag = Literal["on_time", "at_risk", "late", "no_deadline"]


class EtaRequest(BaseModel):
    truck: TimedTruck
    shipments: List[PoolShipment] = Field(min_length=1, description="The pool's shipments (with delivery windows)")
    departure_time: Optional[datetime] = Field(
        default=None, description="When the truck leaves its depot. Leave out to use truck.available_date.")
    traffic_multiplier: Optional[float] = Field(
        default=None, gt=0, description="Live traffic number (1.3 = 30% slower than empty roads). "
                                        "Leave out to use the time-of-day model.")
    use_osrm: bool = Field(default=False, description="Road times from OSRM instead of the 45 km/h estimate")

    @model_validator(mode="after")
    def _need_a_start_time(self):
        if self.departure_time is None and self.truck.available_date is None:
            raise ValueError("Give departure_time or truck.available_date")
        return self


class ShipmentEta(BaseModel):
    shipment_id: int
    eta: datetime = Field(description="When the truck reaches this shipment's drop")
    deadline: Optional[datetime] = Field(description="End of its delivery window")
    minutes_to_spare: Optional[int] = Field(description="Negative = minutes late")
    delay_flag: DelayFlag
    likely_late: bool = Field(description="True when late or at_risk (under 2 hours to spare)")


class TimelineStop(BaseModel):
    seq: int
    kind: Literal["start", "pickup", "drop", "end"]
    shipment_id: Optional[int] = None
    place: Optional[str] = None
    arrives_at: datetime
    leaves_at: datetime


class EtaMinutes(BaseModel):
    free_flow_driving: int
    traffic_delay: int
    loading_unloading: int
    rest_breaks: int


class EtaResponse(BaseModel):
    pool_id: Optional[int] = None
    truck_id: Optional[int] = None
    status: Optional[str] = None
    departure: datetime
    eta: datetime = Field(description="Arrival at the last stop")
    delay_flag: DelayFlag = Field(description="Worst flag of the pool's shipments")
    likely_late: bool
    late_shipments: List[int] = Field(description="Shipments that are late or at risk")
    minutes: EtaMinutes
    total_km: float
    traffic_model: str
    shipments: List[ShipmentEta]
    timeline: List[TimelineStop]


# ---- 6. Whole pipeline --------------------------------------------------------
class PlanPoolRequest(BaseModel):
    truck: EngineTruckWithRoute
    shipments: List[EngineShipmentWithRoute]
    corridor_tolerance_km: float = Field(default=40.0, gt=0)
    split_method: SplitMethod = Field(
        default="ton_km",
        description="weight (kg), volume (m³), distance (km travelled) or ton_km (tonnes × km)",
    )


class PlanPoolResponse(BaseModel):
    truck_id: int
    truck_route_km: float
    total_trip_cost: float
    route: RouteMatchResponse
    load: OptimizeLoadResponse
    cost_split: CostSplitResponse
    carbon: CarbonResponse
    stop_plan: Optional[OptimizeStopsResponse] = Field(
        default=None, description="Best order to visit the packed shipments' pickups and drops (offline estimate)"
    )
