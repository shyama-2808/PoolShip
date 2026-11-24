from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.truck import Truck
from app.models.shipment import Shipment, ShipmentStatus
from app.models.pool import Pool, PoolStatus
from app.schemas.pool import PoolCreate, PoolResponse, PoolOptimizationResult, OptimizationItem
from app.schemas.engine import PoolCarbonResponse
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
    pool or no longer open (409), or doesn't fit the truck (422, with the reason).
    Use POST /pools/optimize first to preview.
    """
    truck = await _get_truck(db, payload.truck_id)
    shipments = await _get_shipments(db, payload.shipment_ids) if payload.shipment_ids else []

    taken = [s.id for s in shipments if s.pool_id is not None or s.status not in _JOINABLE]
    if taken:
        raise HTTPException(status_code=409, detail=f"Shipments already pooled or no longer open: {taken}")

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


@router.get("/{pool_id}", response_model=PoolResponse)
async def get_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    pool = await _load_pool(db, pool_id)
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool


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
