"""
/engine endpoints: call each logistics-engine function directly.

Every endpoint here takes plain JSON and returns the engine's answer.
Nothing is read from or saved to the database, so you can try them in
Swagger (/api/v1/docs) as soon as the backend is running.
Each endpoint comes with a ready-made example built from data/sample_data.json.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Body, HTTPException

from app.core.sample_data import load_sample_data
from app.schemas.engine import (
    AssignTrucksRequest, AssignTrucksResponse,
    CarbonRequest, CarbonResponse,
    CompatibilityRequest, CompatibilityResponse,
    CorridorCheckRequest, CorridorCheckResponse,
    CostSplitRequest, CostSplitResponse,
    DistanceRequest, DistanceResponse,
    EngineShipment, EngineTruck,
    FindPoolsRequest, FindPoolsResponse,
    OptimizeLoadRequest, OptimizeLoadResponse,
    PlanPoolRequest, PlanPoolResponse,
    RoadRouteRequest, RoadRouteResponse,
    RouteMatchRequest, RouteMatchResponse,
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
                "is_perishable", "is_hazardous", "is_fragile",
                "origin_lat", "origin_lng", "dest_lat", "dest_lng"}
_T1_EX = {k: v for k, v in _T1.items() if k in _TRUCK_FIELDS}
_T5_EX = {k: v for k, v in next(t for t in _DATA["trucks"] if t["id"] == 5).items() if k in _TRUCK_FIELDS}
_S1_EX = [{k: v for k, v in s.items() if k in _SHIP_FIELDS} for s in _S1]
_ALL_SHIP_EX = [{k: v for k, v in s.items() if k in _SHIP_FIELDS} for s in _DATA["shipments"]]
_POOL_FIELDS = _SHIP_FIELDS | {"origin_address", "destination_address",
                              "delivery_window_start", "delivery_window_end"}
_ALL_POOL_EX = [{k: v for k, v in s.items() if k in _POOL_FIELDS} for s in _DATA["shipments"]]


def _ex(summary: str, value: Any) -> Dict[str, Any]:
    return {"sample": {"summary": summary, "value": value}}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/sample-data", summary="Get the shared sample data (20 shipments, 5 trucks)")
def get_sample_data():
    return load_sample_data()


@router.post("/compatibility", response_model=CompatibilityResponse,
             summary="Can this shipment share a truck with these others?")
def check_compatibility(
    payload: CompatibilityRequest = Body(openapi_examples=_ex(
        "Paint thinner (hazardous) joining mangoes (perishable)",
        {"existing_items": [_S1_EX[2]], "candidate": _S1_EX[3]},
    )),
):
    ok, reason = CapacityOptimizer.check_compatibility(
        [_to_item(s) for s in payload.existing_items], _to_item(payload.candidate)
    )
    return {"compatible": ok, "reason": reason}


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

    # 4. Carbon saved by pooling the packed shipments
    co2 = CarbonCalculator.calculate_savings(trip_km, max(len(packed), 1))

    return {
        "truck_id": truck.id, "truck_route_km": trip_km, "total_trip_cost": total_cost,
        "route": route, "load": load, "cost_split": split, "carbon": co2,
    }
