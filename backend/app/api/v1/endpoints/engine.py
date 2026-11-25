"""
/engine endpoints: call each logistics-engine function directly.

Every endpoint here takes plain JSON and returns the engine's answer.
Nothing is read from or saved to the database, so you can try them in
Swagger (/api/v1/docs) as soon as the backend is running.
Each endpoint comes with a ready-made example built from data/sample_data.json.
"""
from datetime import date, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException, Query

from app.core.sample_data import load_sample_data
from app.schemas.engine import (
    AssignTrucksRequest, AssignTrucksResponse,
    CarbonCompareRequest, CarbonRequest, CarbonResponse,
    CompatibilityRequest, CompatibilityResponse,
    PoolCompatibilityRequest, PoolCompatibilityResponse,
    CorridorCheckRequest, CorridorCheckResponse,
    CostSplitRequest, CostSplitResponse,
    DistanceRequest, DistanceResponse,
    EtaRequest, EtaResponse,
    EngineShipment, EngineTruck,
    FindPoolsRequest, FindPoolsResponse,
    HubRouteRequest, HubRouteResponse,
    OptimizeLoadRequest, OptimizeLoadResponse,
    OptimizeStopsRequest, OptimizeStopsResponse,
    PlanPoolRequest, PlanPoolResponse,
    PriceRequest, PriceResponse, PriceScenariosResponse,
    RecurringExpandRequest, RecurringExpandResponse, RecurringPoolsRequest, RecurringPoolsResponse,
    ReturnTripRequest, ReturnTripResponse,
    RoadRouteRequest, RoadRouteResponse,
    RouteMatchRequest, RouteMatchResponse,
)
from app.services import (
    compatibility_rules, delay_predictor, dynamic_pricing, hub_routing, recurring, return_trip, route_optimizer,
)
from app.services.capacity_optimizer import CapacityOptimizer, ShipmentItem, TruckSpec
from app.services.carbon_calculator import CarbonCalculator
from app.services.cost_splitter import CostSplitter, to_paise
from app.services.route_matching import RouteMatchingService

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers: turn API objects into the engine's own types
# ---------------------------------------------------------------------------
def _to_item(s: EngineShipment) -> ShipmentItem:
    volume = s.volume_cbm or (s.length_cm * s.width_cm * s.height_cm) / 1_000_000.0
    return ShipmentItem(
        id=s.id, weight_kg=s.weight_kg, volume_cbm=volume,
        length_cm=s.length_cm, width_cm=s.width_cm, height_cm=s.height_cm,
        is_perishable=s.is_perishable, is_hazardous=s.is_hazardous, is_fragile=s.is_fragile,
        goods_type=s.goods_type, temperature_class=s.temperature_class,
    )


def _to_spec(t: EngineTruck) -> TruckSpec:
    return TruckSpec(
        id=t.id, max_weight_kg=t.max_weight_kg, max_volume_cbm=t.max_volume_cbm,
        length_cm=t.length_cm, width_cm=t.width_cm, height_cm=t.height_cm,
    )


def _optimize(truck: EngineTruck, shipments: List[EngineShipment]) -> Dict[str, Any]:
    res = CapacityOptimizer.optimize_load(_to_spec(truck), [_to_item(s) for s in shipments])
    res["packed_items"] = [
        {"id": i.id, "weight_kg": i.weight_kg, "volume_cbm": round(i.volume_cbm, 3)}
        for i in res["packed_items"]
    ]
    res["unpacked_items"] = [
        {"id": u["item"].id, "weight_kg": u["item"].weight_kg,
         "volume_cbm": round(u["item"].volume_cbm, 3), "reason": u["reason"]}
        for u in res["unpacked_items"]
    ]
    return res


def _assign(trucks: List[EngineTruck], shipments: List[EngineShipment]) -> Dict[str, Any]:
    res = CapacityOptimizer.assign_to_trucks([_to_spec(t) for t in trucks], [_to_item(s) for s in shipments])
    for load in res["trucks"]:
        load["packed_items"] = [
            {"id": i.id, "weight_kg": i.weight_kg, "volume_cbm": round(i.volume_cbm, 3)}
            for i in load["packed_items"]
        ]
    res["leftover_items"] = [
        {"id": u["item"].id, "weight_kg": u["item"].weight_kg,
         "volume_cbm": round(u["item"].volume_cbm, 3), "reason": u["reason"]}
        for u in res["leftover_items"]
    ]
    return res


def _cost_split(total: float, shipments: List[Dict[str, Any]], method: str) -> Dict[str, Any]:
    try:
        shares = CostSplitter.calculate_split(total, shipments, split_method=method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"split_method": method, "total_trip_cost": to_paise(total) / 100, "shares": shares}


# ---------------------------------------------------------------------------
# Ready-made examples for Swagger, built from the sample data file
# ---------------------------------------------------------------------------
def _sample(truck_id: int = 1):
    data = load_sample_data()
    truck = next(t for t in data["trucks"] if t["id"] == truck_id)
    route = (truck["origin_lat"], truck["origin_lng"], truck["dest_lat"], truck["dest_lng"])
    matches = RouteMatchingService.find_matching_shipments(truck, data["shipments"])
    ids = {m["shipment_id"] for m in matches["matched"]}
    return data, truck, route, [s for s in data["shipments"] if s["id"] in ids]


_DATA, _T1, _R1, _S1 = _sample(1)
_TRUCK_FIELDS = {"id", "max_weight_kg", "max_volume_cbm", "length_cm", "width_cm", "height_cm",
                 "origin_lat", "origin_lng", "dest_lat", "dest_lng", "rate_per_km"}
_SHIP_FIELDS = {"id", "weight_kg", "volume_cbm", "length_cm", "width_cm", "height_cm",
                "is_perishable", "is_hazardous", "is_fragile", "goods_type", "temperature_class",
                "origin_lat", "origin_lng", "dest_lat", "dest_lng"}
_T1_EX = {k: v for k, v in _T1.items() if k in _TRUCK_FIELDS}
_T5_EX = {k: v for k, v in next(t for t in _DATA["trucks"] if t["id"] == 5).items() if k in _TRUCK_FIELDS}
_S1_EX = [{k: v for k, v in s.items() if k in _SHIP_FIELDS} for s in _S1]
_ALL_SHIP_EX = [{k: v for k, v in s.items() if k in _SHIP_FIELDS} for s in _DATA["shipments"]]
_POOL_FIELDS = _SHIP_FIELDS | {"origin_address", "destination_address",
                              "delivery_window_start", "delivery_window_end"}
_ALL_POOL_EX = [{k: v for k, v in s.items() if k in _POOL_FIELDS} for s in _DATA["shipments"]]
_STOP_FIELDS = {"id", "origin_lat", "origin_lng", "dest_lat", "dest_lng", "origin_address", "destination_address"}
_POOL1_STOPS_EX = [{k: v for k, v in s.items() if k in _STOP_FIELDS}
                   for s in _DATA["shipments"] if s["id"] in (1, 2, 3, 5, 6)]


def _depot(truck: Dict[str, Any], end: bool = False) -> Dict[str, Any]:
    """A truck's start (or end) as a stop point."""
    if end:
        return {"lat": truck["dest_lat"], "lng": truck["dest_lng"], "place": truck.get("destination_city")}
    return {"lat": truck["origin_lat"], "lng": truck["origin_lng"], "place": truck.get("origin_city")}


def _ex(summary: str, value: Any) -> Dict[str, Any]:
    return {"sample": {"summary": summary, "value": value}}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/sample-data", summary="Get the shared sample data (25 shipments, 7 trucks, hubs, recurring shipments)")
def get_sample_data():
    return load_sample_data()


@router.post("/compatibility", response_model=CompatibilityResponse,
             summary="Can this shipment share a truck with these others?")
def check_compatibility(
    payload: CompatibilityRequest = Body(openapi_examples=_ex(
        "Paint thinner (chemicals) joining mangoes (perishable)",
        {"existing_items": [_S1_EX[2]], "candidate": _S1_EX[3]},
    )),
):
    """Checks the candidate against every shipment already in the truck, using the rule table."""
    ok, reason, cautions = compatibility_rules.check_candidate(
        [_to_item(s) for s in payload.existing_items], _to_item(payload.candidate)
    )
    return {"compatible": ok, "reason": reason, "cautions": cautions}


@router.post("/compatibility/pool", response_model=PoolCompatibilityResponse,
             summary="Check a whole pool before creating it (which goods can't share a truck)")
def check_pool_compatibility(
    payload: PoolCompatibilityRequest = Body(openapi_examples=_ex(
        "Mangoes + paint thinner + saree bales (rejected: food with chemicals)",
        {"shipments": [_S1_EX[2], _S1_EX[3], _S1_EX[0]]},
    )),
):
    """
    Every pair of shipments is checked against the rule table (GET /engine/compatibility/rules).
    `compatible` is false if any pair is blocked, and `reason` says which pair and why.
    `cautions` are pairs that may share with care; `flags` gives handling notes for
    fragile, chilled, frozen and hazardous shipments.
    """
    return compatibility_rules.check_pool([_to_item(s) for s in payload.shipments])


@router.get("/compatibility/rules", summary="The rule table: which goods can't share a truck")
def get_compatibility_rules():
    return compatibility_rules.rule_table()


@router.post("/optimize-load", response_model=OptimizeLoadResponse,
             summary="Pack shipments into one truck (weight, volume, size, compatibility)")
def optimize_load(
    payload: OptimizeLoadRequest = Body(openapi_examples=_ex(
        "Truck 1 (Bengaluru to Chennai) with its 6 corridor shipments",
        {"truck": _T1_EX, "shipments": _S1_EX},
    )),
):
    return _optimize(payload.truck, payload.shipments)


@router.post("/assign-trucks", response_model=AssignTrucksResponse,
             summary="Spread a pool's shipments over several trucks (no truck overloaded)")
def assign_trucks(
    payload: AssignTrucksRequest = Body(openapi_examples=_ex(
        "Bengaluru to Chennai pool (shipments 1 to 6, 3,400 kg) over trucks 1 and 5",
        {"trucks": [_T1_EX, _T5_EX], "shipments": _S1_EX},
    )),
):
    """
    First-fit decreasing: biggest shipments first, each into the first truck
    (in the order you list them) that still has room by weight, volume and size,
    and holds nothing it can't travel with (e.g. food and chemicals).
    Returns each truck's load and fill %, plus leftovers with the reason.
    """
    return _assign(payload.trucks, payload.shipments)


@router.post("/cost-split", response_model=CostSplitResponse,
             summary="Split the trip cost fairly between shippers")
def cost_split(
    payload: CostSplitRequest = Body(openapi_examples=_ex(
        "413 km trip at ₹28/km shared by 3 shippers",
        {"trip_distance_km": 413, "rate_per_km": 28, "split_method": "weight", "shipments": [
            {"id": 1, "weight_kg": 600, "distance_km": 413, "volume_cbm": 1.8},
            {"id": 2, "weight_kg": 450, "distance_km": 340, "volume_cbm": 0.96},
            {"id": 5, "weight_kg": 350, "distance_km": 160, "volume_cbm": 0.99},
        ]},
    )),
):
    """
    Pick split_method per pool: weight, volume, distance or ton_km.
    Send total_trip_cost, or trip_distance_km + rate_per_km to have it worked out.
    Shares are in whole paise and always add up exactly to the trip cost.
    """
    total = payload.total_trip_cost
    if total is None:
        total = CostSplitter.trip_cost(payload.trip_distance_km, payload.rate_per_km)
    return _cost_split(total, [s.model_dump() for s in payload.shipments], payload.split_method)


@router.post("/carbon", response_model=CarbonResponse,
             summary="CO₂ and diesel saved by pooling instead of separate trucks")
def carbon(
    payload: CarbonRequest = Body(openapi_examples=_ex(
        "4 shippers sharing a 413 km trip", {"pooled_route_distance_km": 413, "num_participants": 4, "detour_km": 10},
    )),
):
    return CarbonCalculator.calculate_savings(
        payload.pooled_route_distance_km, payload.num_participants, payload.detour_km
    )


@router.post("/carbon/compare", response_model=CarbonResponse,
             summary="Fuel and CO₂: each shipper's own truck versus one pooled truck")
def carbon_compare(
    payload: CarbonCompareRequest = Body(openapi_examples=_ex(
        "3 shippers (413, 380 and 150 km alone) on one 420 km truck",
        {"separate_trip_km": [413, 380, 150], "pooled_truck_km": 420},
    )),
):
    """
    Litres of diesel, kg CO₂ and percent saved for any pool.
    `separate_trip_km` lists how far each shipper's own truck would drive;
    `pooled_truck_km` is how far the shared truck drives.
    """
    return CarbonCalculator.compare_trips(payload.separate_trip_km, payload.pooled_truck_km)


@router.post("/route/distance", response_model=DistanceResponse,
             summary="Distance between two points")
def route_distance(
    payload: DistanceRequest = Body(openapi_examples=_ex(
        "Bengaluru to Chennai",
        {"origin": {"lat": _R1[0], "lng": _R1[1]}, "destination": {"lat": _R1[2], "lng": _R1[3]}},
    )),
):
    o, d = payload.origin, payload.destination
    straight = RouteMatchingService.haversine_distance(o.lat, o.lng, d.lat, d.lng)
    return {"straight_line_km": round(straight, 1),
            "estimated_road_km": round(straight * RouteMatchingService.ROAD_FACTOR, 1)}


@router.post("/route/corridor-check", response_model=CorridorCheckResponse,
             summary="Is a pickup and drop along a truck's route?")
def corridor_check(
    payload: CorridorCheckRequest = Body(openapi_examples=_ex(
        "Hosur to Chennai on the Bengaluru to Chennai truck",
        {"pickup": {"lat": 12.7409, "lng": 77.8253}, "drop": {"lat": _R1[2], "lng": _R1[3]},
         "truck_start": {"lat": _R1[0], "lng": _R1[1]}, "truck_end": {"lat": _R1[2], "lng": _R1[3]},
         "corridor_tolerance_km": 40},
    )),
):
    p, d, s, e = payload.pickup, payload.drop, payload.truck_start, payload.truck_end
    pick_off = RouteMatchingService.cross_track_distance(p.lat, p.lng, s.lat, s.lng, e.lat, e.lng)
    drop_off = RouteMatchingService.cross_track_distance(d.lat, d.lng, s.lat, s.lng, e.lat, e.lng)
    on = RouteMatchingService.is_shipment_on_corridor(
        p.lat, p.lng, d.lat, d.lng, s.lat, s.lng, e.lat, e.lng, payload.corridor_tolerance_km
    )
    return {"on_corridor": on, "pickup_offset_km": round(pick_off, 1),
            "drop_offset_km": round(drop_off, 1), "corridor_tolerance_km": payload.corridor_tolerance_km}


@router.post("/route/road-route", response_model=RoadRouteResponse,
             summary="Road distance and time through a list of stops (OSRM, with offline fallback)")
async def road_route(
    payload: RoadRouteRequest = Body(openapi_examples=_ex(
        "Bengaluru to Vellore to Chennai",
        {"stops": [{"lat": _R1[0], "lng": _R1[1]}, {"lat": 12.9165, "lng": 79.1325},
                   {"lat": _R1[2], "lng": _R1[3]}], "use_osrm": True},
    )),
):
    coords = [(p.lng, p.lat) for p in payload.stops]  # OSRM order is (lng, lat)
    if payload.use_osrm:
        res = await RouteMatchingService.fetch_osrm_route(coords)
    else:
        res = RouteMatchingService.estimate_route(coords)
    return {**res, "source": "osrm" if res.get("geometry") else "estimate"}


@router.post("/route/optimize-stops", response_model=OptimizeStopsResponse,
             summary="Best order for a pool's pickups and drops (pickup before drop), with total km")
async def optimize_stops(
    payload: OptimizeStopsRequest = Body(openapi_examples=_ex(
        "Bengaluru to Chennai pool (shipments 1, 2, 3, 5, 6) starting at truck 1's depot",
        {"shipments": _POOL1_STOPS_EX, "start": _depot(_T1), "use_osrm": False},
    )),
):
    """
    Finds the shortest order to visit every pickup and drop, where each shipment's
    pickup comes before its drop. Road km come from OSRM when `use_osrm` is true and
    the internet is reachable; otherwise straight line x 1.25 (`distance_source` says which).
    `as_listed_km` is the trip if you drove all pickups in the order given and then all
    drops, so `km_saved` shows what the sorting gained.
    """
    return await route_optimizer.optimize_stops(
        [s.model_dump() for s in payload.shipments],
        payload.start.model_dump() if payload.start else None,
        payload.end.model_dump() if payload.end else None,
        payload.use_osrm,
    )


@router.get("/demo-stops/{truck_id}", response_model=OptimizeStopsResponse,
            summary="One-click demo: best stop order for what a sample truck carries")
async def demo_stops(truck_id: int, use_osrm: bool = False):
    """Runs plan-pool for the sample truck, then orders the packed shipments' stops from the truck's depot."""
    plan = demo(truck_id)
    data = load_sample_data()
    truck = next(t for t in data["trucks"] if t["id"] == truck_id)
    packed = {p["id"] for p in plan["load"]["packed_items"]}
    shipments = [s for s in data["shipments"] if s["id"] in packed]
    return await route_optimizer.optimize_stops(shipments, _depot(truck), None, use_osrm)


_RETURN_TRUCK_FIELDS = _TRUCK_FIELDS | {"origin_city", "destination_city", "available_date"}


@router.post("/return-trip", response_model=ReturnTripResponse, response_model_by_alias=True,
             summary="Find loads for a truck's empty trip home")
def match_return_trip(
    payload: ReturnTripRequest = Body(openapi_examples=_ex(
        "Truck 1 (Bengaluru to Chennai) heading home, against all sample shipments",
        {"truck": {k: v for k, v in _T1.items() if k in _RETURN_TRUCK_FIELDS},
         "shipments": _ALL_POOL_EX, "corridor_tolerance_km": 40, "unloading_hours": 2},
    )),
):
    """
    The return route is the truck's destination back to its origin. The truck leaves for
    home after the outbound drive (45 km/h) and `unloading_hours`. A shipment is matched when
    its pickup and drop lie along the way home (same corridor test as outbound), the truck
    reaches its drop before the delivery window closes, and it fits (weight, volume, size,
    compatibility). Everything else is in `rejected` with the reason.
    """
    return return_trip.match_return_loads(
        payload.truck.model_dump(), [s.model_dump() for s in payload.shipments],
        payload.corridor_tolerance_km, payload.unloading_hours,
    )


@router.get("/demo-return/{truck_id}", response_model=ReturnTripResponse, response_model_by_alias=True,
            summary="One-click demo: loads for a sample truck's trip home")
def demo_return(truck_id: int):
    data = load_sample_data()
    truck = next((t for t in data["trucks"] if t["id"] == truck_id), None)
    if not truck:
        raise HTTPException(status_code=404, detail=f"No sample truck {truck_id}. Use 1 to {len(data['trucks'])}.")
    return return_trip.match_return_loads(truck, data["shipments"])


def _price(shipment: Dict[str, Any], truck: Dict[str, Any], **conditions) -> Dict[str, Any]:
    km = dynamic_pricing.shipment_km(shipment)
    volume = shipment.get("volume_cbm") or (
        shipment.get("length_cm", 100) * shipment.get("width_cm", 100) * shipment.get("height_cm", 100)) / 1e6
    return dynamic_pricing.quote(km, shipment["weight_kg"], volume, truck["max_weight_kg"],
                                 truck["max_volume_cbm"], truck["rate_per_km"], **conditions)


@router.post("/price", response_model=PriceResponse,
             summary="Price a shipment from demand, urgency and how full the truck is")
def price(
    payload: PriceRequest = Body(openapi_examples=_ex(
        "Plumbing fittings (shipment 2) on truck 1, urgent, truck 85% full",
        {"shipment": next(s for s in _S1_EX if s["id"] == 2), "truck": _T1_EX, "truck_fill_pct": 85,
         "urgency": "urgent"},
    )),
):
    """
    price = base price x multiplier.
    base price = shipment km x truck ₹/km x the share of the truck it uses.
    multiplier = demand x urgency x fill, kept between 0.85 and 1.50.
    Every factor comes back with a one-line `why`.
    """
    return _price(payload.shipment.model_dump(), payload.truck.model_dump(),
                  truck_fill_pct=payload.truck_fill_pct, urgency=payload.urgency,
                  hours_until_deadline=payload.hours_until_deadline,
                  open_shipments_on_route=payload.open_shipments_on_route,
                  trucks_available_on_route=payload.trucks_available_on_route)


@router.get("/demo-price/{shipment_id}", response_model=PriceScenariosResponse,
            summary="One-click demo: the same sample shipment priced in different situations")
def demo_price(shipment_id: int, truck_id: int = 1):
    data = load_sample_data()
    shipment = next((s for s in data["shipments"] if s["id"] == shipment_id), None)
    truck = next((t for t in data["trucks"] if t["id"] == truck_id), None)
    if not shipment or not truck:
        raise HTTPException(status_code=404, detail="Unknown sample shipment or truck")
    scenarios = [
        ("Normal: standard, truck half full, normal demand", {}),
        ("Urgent", {"urgency": "urgent"}),
        ("Express", {"urgency": "express"}),
        ("Truck nearly empty (5% full)", {"truck_fill_pct": 5}),
        ("Truck nearly full (95% full)", {"truck_fill_pct": 95}),
        ("Busy route (10 shipments, 1 truck)", {"open_shipments_on_route": 10, "trucks_available_on_route": 1}),
        ("Quiet route (1 shipment, 3 trucks): hits the floor",
         {"open_shipments_on_route": 1, "trucks_available_on_route": 3}),
        ("Everything at once: urgent, busy, 100% full (hits the cap)",
         {"urgency": "urgent", "truck_fill_pct": 100, "open_shipments_on_route": 20, "trucks_available_on_route": 1}),
    ]
    out = []
    for name, cond in scenarios:
        q = _price(shipment, truck, **({"truck_fill_pct": 50} | cond))
        out.append({"scenario": name, "price": q["price"], "multiplier": q["multiplier"], "capped": q["capped"]})
    base = _price(shipment, truck)["base_price"]
    return {"shipment_id": shipment_id, "truck_id": truck_id, "base_price": base, "scenarios": out}


_T2 = next(t for t in _DATA["trucks"] if t["id"] == 2)
_T2_SHIPS = [s for s in _ALL_POOL_EX if s["id"] in (7, 8, 9, 10)]


@router.post("/eta", response_model=EtaResponse,
             summary="ETA for a pool and which shipments are likely to be late")
async def eta(
    payload: EtaRequest = Body(openapi_examples=_ex(
        "Truck 2 (Mumbai to Pune) leaving 4 hours late at 10:00: the frozen paneer is at risk",
        {"truck": {k: v for k, v in _T2.items() if k in _RETURN_TRUCK_FIELDS}, "shipments": _T2_SHIPS,
         "departure_time": "2026-12-01T10:00:00+05:30", "use_osrm": False},
    )),
):
    """
    Orders the stops (Task 6), then times them: driving with a time-of-day traffic model
    (rush hour x1.5, night x0.9, day x1.15), 30 min at each stop, a 30 min break every
    4 hours of driving. Each shipment's ETA is compared with the end of its delivery window:
    `late` if after it, `at_risk` if less than 2 hours before it, else `on_time`.
    """
    truck = payload.truck.model_dump()
    shipments = [s.model_dump() for s in payload.shipments]
    plan = await route_optimizer.optimize_stops(shipments, _depot(truck), None, payload.use_osrm)
    res = delay_predictor.predict(
        plan, payload.departure_time or payload.truck.available_date,
        {s["id"]: s.get("delivery_window_end") for s in shipments}, payload.traffic_multiplier,
    )
    return {"truck_id": truck["id"], **res}


@router.get("/demo-eta", response_model=List[EtaResponse],
            summary="One-click demo: ETA and delay flag for every sample truck's pool")
def demo_eta(delay_hours: float = 0.0):
    """
    Each sample truck's pool (what /engine/demo/{truck_id} packs) leaves at the truck's
    available_date plus `delay_hours`. Try delay_hours=4 to see shipments become at risk.
    """
    data = load_sample_data()
    by_id = {s["id"]: s for s in data["shipments"]}
    out = []
    for t in data["trucks"]:
        plan = demo(t["id"])["stop_plan"]
        if not plan:
            continue
        drops = [s["shipment_id"] for s in plan["stops"] if s["kind"] == "drop"]
        depart = RouteMatchingService._to_datetime(t["available_date"]) + timedelta(hours=delay_hours)
        res = delay_predictor.predict(plan, depart, {i: by_id[i].get("delivery_window_end") for i in drops})
        out.append({"pool_id": t["id"], "truck_id": t["id"], "status": "demo", **res})
    return out


@router.post("/route/match", response_model=RouteMatchResponse,
             summary="Which shipments are along this truck's route?")
def route_match(
    payload: RouteMatchRequest = Body(openapi_examples=_ex(
        "Truck 1 against all 20 sample shipments",
        {"truck": _T1_EX, "shipments": _ALL_SHIP_EX, "corridor_tolerance_km": 40},
    )),
):
    return RouteMatchingService.find_matching_shipments(
        payload.truck.model_dump(), [s.model_dump() for s in payload.shipments],
        payload.corridor_tolerance_km,
    )


@router.post("/route/pools", response_model=FindPoolsResponse,
             summary="Group open shipments into candidate pools (similar route + overlapping delivery windows)")
def find_pools(
    payload: FindPoolsRequest = Body(openapi_examples=_ex(
        "All 20 sample shipments",
        {"shipments": _ALL_POOL_EX, "corridor_tolerance_km": 40},
    )),
):
    """
    No truck needed. Shipments are pooled when their pickups and drops sit close to a
    common path (going the same way) and their delivery windows overlap.
    Shipments that fit no pool come back in `unmatched` with the reason.
    """
    return RouteMatchingService.find_candidate_pools(
        [s.model_dump() for s in payload.shipments], payload.corridor_tolerance_km
    )


@router.get("/demo-pools", response_model=FindPoolsResponse,
            summary="One-click demo: group all 20 sample shipments into pools")
def demo_pools():
    return RouteMatchingService.find_candidate_pools(load_sample_data()["shipments"])


@router.post("/plan-pool", response_model=PlanPoolResponse,
             summary="Run the whole engine: match route, pack truck, split cost, count CO₂")
def plan_pool(
    payload: PlanPoolRequest = Body(openapi_examples=_ex(
        "Truck 1 against all 20 sample shipments",
        {"truck": _T1_EX, "shipments": _ALL_SHIP_EX, "corridor_tolerance_km": 40, "split_method": "ton_km"},
    )),
):
    return _plan(payload)


@router.get("/demo/{truck_id}", response_model=PlanPoolResponse,
            summary="One-click demo: run plan-pool for a sample truck against all sample shipments")
def demo(truck_id: int):
    data = load_sample_data()
    truck = next((t for t in data["trucks"] if t["id"] == truck_id), None)
    if not truck:
        raise HTTPException(status_code=404, detail=f"No sample truck {truck_id}. Use 1 to {len(data['trucks'])}.")
    return _plan(PlanPoolRequest(truck=truck, shipments=data["shipments"]))


def _plan(payload: PlanPoolRequest) -> Dict[str, Any]:
    truck = payload.truck
    # 1. Route matching: keep only shipments along the truck's corridor
    route = RouteMatchingService.find_matching_shipments(
        truck.model_dump(), [s.model_dump() for s in payload.shipments], payload.corridor_tolerance_km
    )
    distance_by_id = {m["shipment_id"]: m["shipment_distance_km"] for m in route["matched"]}
    on_route = [s for s in payload.shipments if s.id in distance_by_id]

    # 2. Load optimisation: what physically and safely fits
    load = _optimize(truck, on_route)

    # 3. Cost split: truck trip price shared by what was packed
    trip_km = route["truck_route_km"]
    total_cost = CostSplitter.trip_cost(trip_km, truck.rate_per_km)
    packed = load["packed_items"]
    split = _cost_split(
        total_cost,
        [{"id": p["id"], "weight_kg": p["weight_kg"], "volume_cbm": p["volume_cbm"],
          "distance_km": distance_by_id[p["id"]]} for p in packed],
        payload.split_method,
    ) if packed else {"split_method": payload.split_method, "total_trip_cost": total_cost, "shares": []}

    # 4. Fuel and CO₂: each packed shipment on its own truck vs. this one truck
    co2 = CarbonCalculator.compare_trips([distance_by_id[p["id"]] for p in packed], trip_km)

    # 5. Stop order: pickups and drops of what was packed, starting at the truck's depot
    packed_ids = {p["id"] for p in packed}
    stop_plan = route_optimizer.optimize_stops_offline(
        [s.model_dump() for s in payload.shipments if s.id in packed_ids], _depot(truck.model_dump()),
    ) if packed else None

    return {
        "truck_id": truck.id, "truck_route_km": trip_km, "total_trip_cost": total_cost,
        "route": route, "load": load, "cost_split": split, "carbon": co2, "stop_plan": stop_plan,
    }


# ---------------------------------------------------------------------------
# Phase 4, Task 11: recurring shipments
# ---------------------------------------------------------------------------
_REC_EX = [{k: v for k, v in r.items() if k != "shipper_key"} for r in _DATA.get("recurring_shipments", [])]
_WEEK = {"from_date": "2026-12-01", "to_date": "2026-12-07"}


def _recurring_plan(recs: List[Dict[str, Any]], shipments: List[Dict[str, Any]], from_date, to_date,
                    tol: float) -> Dict[str, Any]:
    try:
        return recurring.plan_period(recs, shipments, from_date, to_date, tol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recurring/expand", response_model=RecurringExpandResponse,
             summary="Turn recurring shipments into one shipment per repeat date")
def recurring_expand(
    payload: RecurringExpandRequest = Body(openapi_examples=_ex(
        "The 4 sample recurring shipments over the week 1 to 7 Dec 2026",
        {"recurring": _REC_EX, **_WEEK},
    )),
):
    """
    Lists every date from `from_date` to `to_date` that each recurring shipment repeats on
    (daily, or weekly on its `weekdays`), and makes a shipment for each date with its own
    delivery window (IST). Copy ids are recurring id x 1000 + occurrence number.
    """
    recs = [r.model_dump() for r in payload.recurring]
    return {"from_date": payload.from_date, "to_date": payload.to_date,
            "occurrences": recurring.expand(recs, payload.from_date, payload.to_date)}


@router.post("/recurring/pools", response_model=RecurringPoolsResponse,
             summary="Repeats of recurring shipments enter pools automatically, with the one-off shipments")
def recurring_pools(
    payload: RecurringPoolsRequest = Body(openapi_examples=_ex(
        "Sample recurring shipments + all 25 one-off shipments, week of 1 Dec 2026",
        {"recurring": _REC_EX, "shipments": _ALL_POOL_EX, **_WEEK, "corridor_tolerance_km": 40},
    )),
):
    """
    Each repeat in the period becomes a shipment and goes through the normal pool finder
    (POST /engine/route/pools) together with `shipments`. Two repeats of the same recurring
    shipment never share a pool. `recurring` says, for every repeat date, which pool it
    joined and with whom, or why it got none.
    """
    return _recurring_plan([r.model_dump() for r in payload.recurring],
                           [s.model_dump() for s in payload.shipments],
                           payload.from_date, payload.to_date, payload.corridor_tolerance_km)


@router.get("/demo-recurring", response_model=RecurringPoolsResponse,
            summary="One-click demo: the sample recurring shipments entering pools for a week")
def demo_recurring(from_date: date = Query(date(2026, 12, 1)), to_date: date = Query(date(2026, 12, 7))):
    if to_date < from_date or (to_date - from_date).days > 92:
        raise HTTPException(status_code=400, detail="to_date must be 0 to 92 days after from_date")
    data = load_sample_data()
    return _recurring_plan(data["recurring_shipments"], data["shipments"], from_date, to_date, 40.0)


# ---------------------------------------------------------------------------
# Phase 4, Task 12: hub support (two-leg journeys)
# ---------------------------------------------------------------------------
_HUB_TRUCK_FIELDS = _RETURN_TRUCK_FIELDS | {"used_weight_kg", "used_volume_cbm"}


@router.get("/hubs", summary="The sample hubs where goods can change trucks")
def get_hubs():
    return load_sample_data()["hubs"]


@router.post("/hub-route", response_model=HubRouteResponse, response_model_by_alias=True,
             summary="No direct truck? Plan a two-leg journey through a hub")
def hub_route(
    payload: HubRouteRequest = Body(openapi_examples=_ex(
        "Jute bags Bengaluru to Kolkata (shipment 20): no truck goes all the way",
        {"shipment": next(s for s in _ALL_POOL_EX if s["id"] == 20),
         "trucks": [{k: v for k, v in t.items() if k in _HUB_TRUCK_FIELDS} for t in _DATA["trucks"]],
         "corridor_tolerance_km": 40, "max_detour_pct": 30},
    )),
):
    """
    1. If one truck covers the whole trip, fits it and is on time, the answer is `direct`.
    2. Otherwise every hub is tried: pickup to hub on one truck, hub to drop on another.
       A hub is skipped if it makes the trip more than `max_detour_pct` longer, if no truck
       with room covers a leg, or if the goods would arrive after the delivery window.
    3. `best` is the on-time option that delivers earliest. Times use 45 km/h from each
       truck's available_date, plus the hub's transfer time. Cost = each leg's km x the
       truck's Rs/km x the share of the truck used, plus the hub's Rs/kg handling.
    """
    hubs = [h.model_dump() for h in payload.hubs] if payload.hubs else load_sample_data()["hubs"]
    return hub_routing.plan_route(payload.shipment.model_dump(), [t.model_dump() for t in payload.trucks],
                                  hubs, payload.corridor_tolerance_km, payload.max_detour_pct)


@router.get("/demo-hub/{shipment_id}", response_model=HubRouteResponse, response_model_by_alias=True,
            summary="One-click demo: direct truck or hub journey for a sample shipment (try 20)")
def demo_hub(shipment_id: int):
    """
    Uses the sample trucks and hubs. Each truck's spare room counts what its own
    demo pool (GET /engine/demo/{truck_id}) already loads, except this shipment.
    """
    data = load_sample_data()
    shipment = next((s for s in data["shipments"] if s["id"] == shipment_id), None)
    if not shipment:
        raise HTTPException(status_code=404, detail=f"No sample shipment {shipment_id}")
    trucks = []
    for t in data["trucks"]:
        packed = [p for p in demo(t["id"])["load"]["packed_items"] if p["id"] != shipment_id]
        trucks.append({**t, "used_weight_kg": sum(p["weight_kg"] for p in packed),
                       "used_volume_cbm": sum(p["volume_cbm"] for p in packed)})
    return hub_routing.plan_route(shipment, trucks, data["hubs"])
