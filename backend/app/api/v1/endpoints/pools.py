from datetime import timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.truck import Truck
from app.models.shipment import Shipment, ShipmentStatus
from app.models.pool import Pool, PoolStatus
from app.models.tracking import TrackingEvent
from app.schemas.pool import PoolCreate, PoolResponse, PoolOptimizationResult, OptimizationItem
from app.schemas.engine import EtaResponse, PoolCarbonResponse
from app.services import compatibility_rules, delay_predictor, route_optimizer
from app.services.capacity_optimizer import CapacityOptimizer, ShipmentItem, TruckSpec
from app.services.cost_splitter import CostSplitter
from app.services.carbon_calculator import CarbonCalculator
from app.services.route_matching import RouteMatchingService

router = APIRouter()

# A shipment can join a pool only while it is still looking for a truck
_JOINABLE = (ShipmentStatus.POSTED, ShipmentStatus.MATCHED)


def _road_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return RouteMatchingService.haversine_distance(lat1, lng1, lat2, lng2) * RouteMatchingService.ROAD_FACTOR


def _shipment_km(s: Shipment) -> float:
    """How far this shipment's own truck would drive without pooling."""
    return _road_km(s.origin_lat, s.origin_lng, s.dest_lat, s.dest_lng)


def _truck_km(truck: Truck) -> float:
    return _road_km(truck.origin_lat, truck.origin_lng, truck.dest_lat, truck.dest_lng)


def _plan(truck: Truck, shipments: List[Shipment], split_method: str) -> Dict[str, Any]:
    """
    Run the engine for one truck and these shipments:
    pack the truck, price the trip from its distance, split the price, count CO₂ saved.
    """
    truck_spec = TruckSpec(
        id=truck.id,
        max_weight_kg=truck.max_weight_kg,
        max_volume_cbm=truck.max_volume_cbm,
        length_cm=truck.length_cm,
        width_cm=truck.width_cm,
        height_cm=truck.height_cm,
    )
    items = [
        ShipmentItem(
            id=s.id,
            weight_kg=s.weight_kg,
            volume_cbm=s.volume_cbm or 0.0,  # 0 = work it out from the dimensions
            length_cm=s.length_cm,
            width_cm=s.width_cm,
            height_cm=s.height_cm,
            is_perishable=bool(s.is_perishable),
            is_hazardous=bool(s.is_hazardous),
            is_fragile=bool(s.is_fragile),
            goods_type=s.goods_type,
            temperature_class=s.temperature_class or "ambient",
        )
        for s in shipments
    ]
    load = CapacityOptimizer.optimize_load(truck_spec, items)
    packed = load["packed_items"]

    trip_km = _truck_km(truck)
    total_cost = CostSplitter.trip_cost(trip_km, truck.rate_per_km)

    by_id = {s.id: s for s in shipments}
    shares = CostSplitter.calculate_split(
        total_cost,
        [
            {
                "id": i.id,
                "weight_kg": i.weight_kg,
                "volume_cbm": CapacityOptimizer.item_volume(i),
                "distance_km": _shipment_km(by_id[i.id]),
            }
            for i in packed
        ],
        split_method,
    )
    # Fuel and CO₂: each packed shipment on its own truck vs. this one truck
    carbon = CarbonCalculator.compare_trips([_shipment_km(by_id[i.id]) for i in packed], trip_km)
    return {
        "trip_km": trip_km,
        "total_cost": total_cost,
        "load": load,
        "cost_by_id": {cs["shipment_id"]: cs["allocated_cost"] for cs in shares},
        "carbon": carbon,
    }


async def _get_truck(db: AsyncSession, truck_id: int) -> Truck:
    truck = (await db.execute(select(Truck).where(Truck.id == truck_id))).scalars().first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck


async def _get_shipments(db: AsyncSession, ids: List[int]) -> List[Shipment]:
    ids = list(dict.fromkeys(ids))  # drop repeats, keep order
    found = (await db.execute(select(Shipment).where(Shipment.id.in_(ids)))).scalars().all()
    missing = sorted(set(ids) - {s.id for s in found})
    if missing:
        raise HTTPException(status_code=404, detail=f"Shipments not found: {missing}")
    return sorted(found, key=lambda s: ids.index(s.id))


@router.post("/optimize", response_model=PoolOptimizationResult)
async def simulate_pool_optimization(
    payload: PoolCreate,
    db: AsyncSession = Depends(get_db)
):
    """Preview a pool without saving anything: what fits, the trip cost and who pays what."""
    truck = await _get_truck(db, payload.truck_id)
    if not payload.shipment_ids:
        raise HTTPException(status_code=400, detail="No matching shipments provided")
    shipments = await _get_shipments(db, payload.shipment_ids)

    plan = _plan(truck, shipments, payload.split_method)
    load, cost_by_id = plan["load"], plan["cost_by_id"]

    packed_out = [
        OptimizationItem(
            id=item.id,
            weight_kg=item.weight_kg,
            volume_cbm=CapacityOptimizer.item_volume(item),
            allocated_cost=cost_by_id.get(item.id, 0.0),
            fits=True,
            reason="Fits within weight, volume and compatibility limits",
        )
        for item in load["packed_items"]
    ]
    unpacked_out = [
        OptimizationItem(
            id=u["item"].id,
            weight_kg=u["item"].weight_kg,
            volume_cbm=CapacityOptimizer.item_volume(u["item"]),
            allocated_cost=0.0,
            fits=False,
            reason=u["reason"],
        )
        for u in load["unpacked_items"]
    ]

    return PoolOptimizationResult(
        truck_id=truck.id,
        split_method=payload.split_method,
        total_weight_kg=load["total_packed_weight_kg"],
        total_volume_cbm=load["total_packed_volume_cbm"],
        weight_utilization_pct=load["weight_utilization_pct"],
        volume_utilization_pct=load["volume_utilization_pct"],
        overall_utilization_pct=load["overall_utilization_pct"],
        total_trip_cost=plan["total_cost"],
        total_co2_saved_kg=plan["carbon"]["co2_saved_kg"],
        total_diesel_saved_litres=plan["carbon"]["diesel_saved_litres"],
        packed_shipments=packed_out,
        unpacked_shipments=unpacked_out,
    )


@router.post("/", response_model=PoolResponse)
async def create_pool(
    payload: PoolCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a pool on a truck and put the given shipments in it.

    Each shipment is linked to the pool (status POOLED) and gets its cost share
    saved in `allocated_cost`, using the pool's `split_method`. The pool stores
    the trip cost, load, fill % and CO₂ saved.

    Refused (nothing saved) if a shipment doesn't exist (404), is already in a
    pool or no longer open (409), holds goods that can't share a truck, e.g.
    food with chemicals (422, with the clashing pairs), or doesn't fit the
    truck (422, with the reason).
    Use POST /pools/optimize first to preview.
    """
    truck = await _get_truck(db, payload.truck_id)
    shipments = await _get_shipments(db, payload.shipment_ids) if payload.shipment_ids else []

    taken = [s.id for s in shipments if s.pool_id is not None or s.status not in _JOINABLE]
    if taken:
        raise HTTPException(status_code=409, detail=f"Shipments already pooled or no longer open: {taken}")

    # Compatibility check before pooling: e.g. perishables + chemicals is rejected
    compat = compatibility_rules.check_pool(shipments)
    if not compat["compatible"]:
        raise HTTPException(status_code=422, detail={
            "message": compat["reason"],
            "conflicts": compat["conflicts"],
        })

    plan = _plan(truck, shipments, payload.split_method)
    load = plan["load"]
    if load["unpacked_items"]:
        raise HTTPException(status_code=422, detail={
            "message": "Some shipments don't fit this truck. Remove them or pick another truck.",
            "does_not_fit": [{"id": u["item"].id, "reason": u["reason"]} for u in load["unpacked_items"]],
        })

    pool = Pool(
        truck_id=truck.id,
        status=PoolStatus.OPTIMIZED if shipments else PoolStatus.OPEN,
        split_method=payload.split_method,
        total_distance_km=round(plan["trip_km"], 2),
        total_cost=plan["total_cost"],
        current_weight_kg=load["total_packed_weight_kg"],
        current_volume_cbm=load["total_packed_volume_cbm"],
        utilization_percentage=load["overall_utilization_pct"],
        co2_saved_kg=plan["carbon"]["co2_saved_kg"],
        diesel_saved_litres=plan["carbon"]["diesel_saved_litres"],
    )
    db.add(pool)
    await db.flush()  # gives the pool its id

    for s in shipments:
        s.pool_id = pool.id
        s.status = ShipmentStatus.POOLED
        s.allocated_cost = plan["cost_by_id"][s.id]

    await db.commit()
    return await _load_pool(db, pool.id)


async def _load_pool(db: AsyncSession, pool_id: int) -> Pool:
    result = await db.execute(
        select(Pool)
        .options(selectinload(Pool.shipments), selectinload(Pool.truck))
        .where(Pool.id == pool_id)
        .execution_options(populate_existing=True)
    )
    return result.scalars().first()


# Pools that are planned or on the road (not finished, not cancelled)
_ACTIVE = (PoolStatus.OPEN, PoolStatus.OPTIMIZED, PoolStatus.LOCKED, PoolStatus.IN_TRANSIT)


async def _pool_eta(db: AsyncSession, pool: Pool) -> Dict[str, Any]:
    """
    ETA and delay flag for a saved pool.
    Planned pool: the truck leaves its origin at its available_date and does every pickup and drop.
    In transit with a tracking ping: it leaves from the last ping at the ping's time, with
    everything already loaded, so only the drops take time.
    """
    truck = pool.truck
    ships = sorted(pool.shipments, key=lambda s: s.id)
    start = {"lat": truck.origin_lat, "lng": truck.origin_lng, "place": truck.origin_city}
    departure = truck.available_date
    loaded: set = set()
    rows = [{"id": s.id, "origin_lat": s.origin_lat, "origin_lng": s.origin_lng, "dest_lat": s.dest_lat,
             "dest_lng": s.dest_lng, "origin_address": s.origin_address,
             "destination_address": s.destination_address} for s in ships]

    if pool.status == PoolStatus.IN_TRANSIT:
        last: Optional[TrackingEvent] = (await db.execute(
            select(TrackingEvent).where(TrackingEvent.pool_id == pool.id)
            .order_by(TrackingEvent.timestamp.desc()).limit(1)
        )).scalars().first()
        if last is not None:
            start = {"lat": last.latitude, "lng": last.longitude, "place": last.location_name}
            departure = last.timestamp
            loaded = {s.id for s in ships}
            for r in rows:  # already on board: "pick up" where the truck is now
                r["origin_lat"], r["origin_lng"], r["origin_address"] = last.latitude, last.longitude, "on board"

    if departure is not None and departure.tzinfo is None:
        departure = departure.replace(tzinfo=timezone.utc)  # SQLite drops the time zone
    plan = route_optimizer.optimize_stops_offline(rows, start)
    deadlines = {}
    for s in ships:
        end = s.delivery_window_end
        deadlines[s.id] = end.replace(tzinfo=timezone.utc) if end is not None and end.tzinfo is None else end
    res = delay_predictor.predict(plan, departure, deadlines, already_loaded=loaded)
    return {"pool_id": pool.id, "truck_id": pool.truck_id, "status": pool.status.value, **res}


@router.get("/active/eta", response_model=List[EtaResponse])
async def get_active_pool_etas(db: AsyncSession = Depends(get_db)):
    """ETA and delay flag for every active pool that has shipments (open, optimized, locked or in transit)."""
    result = await db.execute(
        select(Pool).options(selectinload(Pool.shipments), selectinload(Pool.truck))
        .where(Pool.status.in_(_ACTIVE)).order_by(Pool.id)
    )
    return [await _pool_eta(db, p) for p in result.scalars().all() if p.shipments]


@router.get("/{pool_id}", response_model=PoolResponse)
async def get_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    pool = await _load_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool


@router.get("/{pool_id}/eta", response_model=EtaResponse)
async def get_pool_eta(pool_id: int, db: AsyncSession = Depends(get_db)):
    """
    When the pool's truck should reach each drop, and whether each shipment is likely late.
    Traffic: time-of-day model (rush hour x1.5, night x0.9, day x1.15), 30 min per stop,
    30 min break every 4 h of driving. Flags: late, at_risk (under 2 h to spare), on_time.
    """
    pool = await _load_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    if not pool.shipments:
        raise HTTPException(status_code=400, detail="Pool has no shipments yet, so there is nothing to time")
    return await _pool_eta(db, pool)


@router.get("/{pool_id}/carbon", response_model=PoolCarbonResponse)
async def get_pool_carbon(pool_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fuel and CO₂ for a saved pool: every shipment on its own truck (baseline)
    versus the pool's one truck. Gives litres, kg CO₂ and percent saved, the
    emission factors used, and each shipment's separate trip.
    """
    pool = await _load_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")

    shipments = sorted(pool.shipments, key=lambda s: s.id)
    trips = [(s.id, _shipment_km(s)) for s in shipments]
    result = CarbonCalculator.compare_trips([km for _, km in trips], _truck_km(pool.truck))
    return {
        "pool_id": pool.id,
        "truck_id": pool.truck_id,
        **result,
        "separate_trips": [
            {"shipment_id": sid, **CarbonCalculator.trip_emissions(km)} for sid, km in trips
        ],
    }
