"""
Request/response shapes for the /engine endpoints.

These endpoints run the logistics engine directly on the data you send.
They do not read or write the database, so they work as soon as the API is up.
Units: weight kg, volume m³ (cbm), dimensions cm, distance km, money ₹.
"""
from datetime import date, datetime
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
    recurring_id: Optional[int] = Field(
        default=None, description="Set on repeats of a recurring shipment; two repeats of the same one never share a pool")


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


# ---- Task 11: recurring shipments -------------------------------------------------
Repeat = Literal["daily", "weekly"]
Weekday = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_HHMM = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


class RecurringShipmentIn(EngineShipmentWithRoute):
    id: int = Field(ge=1, description="Recurring shipment number; its repeats get ids id x 1000 + 1, + 2, ...")
    title: Optional[str] = None
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    repeat: Repeat = Field(default="weekly", description="daily or weekly")
    weekdays: Optional[List[Weekday]] = Field(
        default=None, description="Weekly only: which days, e.g. [\"wed\", \"sat\"]. Leave out = the weekday of start_date.")
    start_date: date = Field(description="First day it may repeat")
    end_date: Optional[date] = Field(default=None, description="Last day it may repeat. Leave out = no end.")
    window_start_time: str = Field(default="09:00", pattern=_HHMM, description="Delivery window opens (IST) on the day itself")
    window_end_time: str = Field(default="18:00", pattern=_HHMM, description="Delivery window closes (IST)")
    window_days: int = Field(default=1, ge=0, le=14,
                             description="Days after the repeat date that the window closes (1 = next day)")

    @model_validator(mode="after")
    def _check(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date is before start_date")
        if self.window_days == 0 and self.window_end_time <= self.window_start_time:
            raise ValueError("window_end_time must be after window_start_time on the same day (or set window_days)")
        return self


class _Period(BaseModel):
    from_date: date = Field(description="First day to create repeats for")
    to_date: date = Field(description="Last day (included)")

    @model_validator(mode="after")
    def _check_period(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date is before from_date")
        if (self.to_date - self.from_date).days > 92:
            raise ValueError("Ask for at most 93 days at a time")
        return self


class RecurringExpandRequest(_Period):
    recurring: List[RecurringShipmentIn] = Field(min_length=1)


class RecurringOccurrence(PoolShipment):
    recurring_id: int
    occurrence: int = Field(description="1 = first repeat since start_date")
    occurrence_date: date
    title: Optional[str] = None


class RecurringExpandResponse(BaseModel):
    from_date: date
    to_date: date
    occurrences: List[RecurringOccurrence] = Field(description="One shipment per repeat date, in date order")


class RecurringPoolsRequest(_Period):
    recurring: List[RecurringShipmentIn] = Field(min_length=1)
    shipments: List[PoolShipment] = Field(default=[], description="Other open (one-off) shipments, ids below 1000")
    corridor_tolerance_km: float = Field(default=40.0, gt=0)


class RecurringDate(BaseModel):
    date: date
    weekday: str
    shipment_id: int
    pool_id: Optional[int] = Field(description="Candidate pool it went into, or null")
    pooled_with: List[int]
    reason: Optional[str] = Field(description="Why it got no pool")


class RecurringSummary(BaseModel):
    recurring_id: int
    title: Optional[str] = None
    repeat: Repeat
    repeats: str = Field(description="In words, e.g. 'every Wed and Sat'")
    route: str
    occurrences: int
    pooled: int
    not_pooled: int
    dates: List[RecurringDate]


class RecurringPoolsResponse(FindPoolsResponse):
    from_date: date
    to_date: date
    occurrences_created: int
    recurring: List[RecurringSummary]


# ---- Task 12: hub support (two-leg journeys) -----------------------------------------
class Hub(BaseModel):
    id: int
    name: Optional[str] = None
    city: Optional[str] = None
    lat: float
    lng: float
    transfer_hours: float = Field(default=3.0, ge=0, description="Unload, sort and reload time at the hub")
    handling_rate_per_kg: float = Field(default=1.0, ge=0, description="Hub charge, Rs per kg")


class HubTruck(TimedTruck):
    used_weight_kg: float = Field(default=0.0, ge=0, description="Already loaded, so only the rest is spare")
    used_volume_cbm: float = Field(default=0.0, ge=0)


class HubRouteRequest(BaseModel):
    shipment: PoolShipment
    trucks: List[HubTruck] = Field(min_length=1)
    hubs: Optional[List[Hub]] = Field(default=None, description="Leave out to use the sample hubs (GET /engine/hubs)")
    corridor_tolerance_km: float = Field(default=40.0, gt=0)
    max_detour_pct: float = Field(default=30.0, gt=0,
                                  description="Skip hubs that make the trip more than this % longer than direct")


class DirectTruck(BaseModel):
    truck_id: int
    delivered_at: Optional[datetime] = None
    on_time: bool
    cost: float


class HubPoint(BaseModel):
    id: int
    name: str
    lat: float
    lng: float


class HubLeg(BaseModel):
    leg: int
    truck_id: int
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    km: float
    departs_at: Optional[datetime] = None
    arrives_at: Optional[datetime] = None
    cost: float = Field(description="Leg km x truck Rs/km x share of the truck used")


class HubOption(BaseModel):
    hub: HubPoint
    legs: List[HubLeg]
    transfer_hours: float
    ready_at_hub: Optional[datetime] = Field(description="Leg 1 arrives + transfer time")
    wait_at_hub_hours: Optional[float] = Field(description="Hours from arriving at the hub to leaving on leg 2")
    total_km: float
    extra_km: float = Field(description="Km more than going direct")
    extra_pct: float
    delivered_at: Optional[datetime] = None
    spare_hours: Optional[float] = Field(description="Hours before the delivery window closes")
    handling_fee: float
    total_cost: float


class HubReject(BaseModel):
    hub_id: int
    name: str
    reason: str


class HubRouteResponse(BaseModel):
    shipment_id: int
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    direct_km: float
    deadline: Optional[datetime] = None
    corridor_tolerance_km: float
    max_detour_pct: float
    mode: Literal["direct", "hub", "none"] = Field(description="direct = one truck does it; hub = change trucks; none = no way")
    summary: str
    direct_trucks: List[DirectTruck] = Field(description="Trucks covering the whole trip (on time or not)")
    best: Optional[HubOption] = None
    options: List[HubOption] = Field(description="Best on-time option per working hub, best first")
    rejected_hubs: List[HubReject]
