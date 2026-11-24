from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.truck import Truck
from app.models.shipment import Shipment, ShipmentStatus
from app.models.pool import Pool, PoolStatus
from app.schemas.pool import PoolCreate, PoolResponse, PoolOptimizationResult, OptimizationItem
from app.services.capacity_optimizer import CapacityOptimizer, ShipmentItem, TruckSpec
from app.services.cost_splitter import CostSplitter
from app.services.carbon_calculator import CarbonCalculator
from app.services.route_matching import RouteMatchingService

router = APIRouter()


@router.post("/optimize", response_model=PoolOptimizationResult)
async def simulate_pool_optimization(
    payload: PoolCreate,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Truck
    res_truck = await db.execute(select(Truck).where(Truck.id == payload.truck_id))
    truck = res_truck.scalars().first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    # 2. Fetch Shipments
    res_shipments = await db.execute(select(Shipment).where(Shipment.id.in_(payload.shipment_ids)))
    shipments = res_shipments.scalars().all()
    if not shipments:
        raise HTTPException(status_code=400, detail="No matching shipments provided")

    truck_spec = TruckSpec(
        id=truck.id,
        max_weight_kg=truck.max_weight_kg,
        max_volume_cbm=truck.max_volume_cbm,
        length_cm=truck.length_cm,
        width_cm=truck.width_cm,
        height_cm=truck.height_cm,
    )

    candidate_items = [
        ShipmentItem(
            id=s.id,
            weight_kg=s.weight_kg,
            volume_cbm=s.volume_cbm or 0.1,
            length_cm=s.length_cm,
            width_cm=s.width_cm,
            height_cm=s.height_cm,
            is_perishable=s.is_perishable,
            is_hazardous=s.is_hazardous,
            is_fragile=s.is_fragile,
        )
        for s in shipments
    ]

    # 3. Run Bin-Packing Optimization
    optimization_res = CapacityOptimizer.optimize_load(truck_spec, candidate_items)
    packed_items = optimization_res["packed_items"]

    # 4. Calculate Distance & Route Cost
    distance_km = RouteMatchingService.haversine_distance(
        truck.origin_lat, truck.origin_lng, truck.dest_lat, truck.dest_lng
    ) * 1.25  # Road network factor
    total_trip_cost = round(distance_km * truck.rate_per_km, 2)

    # 5. Calculate Cost Split for packed shipments
    shipments_for_cost = [
        {
            "id": item.id,
            "weight_kg": item.weight_kg,
            "distance_km": distance_km,
            "volume_cbm": item.volume_cbm,
        }
        for item in packed_items
    ]
    cost_splits = {
        cs["shipment_id"]: cs["allocated_cost"]
        for cs in CostSplitter.calculate_split(total_trip_cost, shipments_for_cost)
    }

    # 6. Calculate Carbon Savings
    carbon_res = CarbonCalculator.calculate_savings(
        pooled_route_distance_km=distance_km,
        num_participants=len(packed_items)
    )

    packed_out = [
        OptimizationItem(
            id=item.id,
            weight_kg=item.weight_kg,
            volume_cbm=item.volume_cbm,
            allocated_cost=cost_splits.get(item.id, 0.0),
            fits=True,
            reason="Fits within weight, volume and compatibility limits",
        )
        for item in packed_items
    ]

    unpacked_out = [
        OptimizationItem(
            id=u["item"].id,
            weight_kg=u["item"].weight_kg,
            volume_cbm=u["item"].volume_cbm,
            allocated_cost=0.0,
            fits=False,
            reason=u["reason"],
        )
        for u in optimization_res["unpacked_items"]
    ]

    return PoolOptimizationResult(
        truck_id=truck.id,
        total_weight_kg=optimization_res["total_packed_weight_kg"],
        total_volume_cbm=optimization_res["total_packed_volume_cbm"],
        weight_utilization_pct=optimization_res["weight_utilization_pct"],
        volume_utilization_pct=optimization_res["volume_utilization_pct"],
        overall_utilization_pct=optimization_res["overall_utilization_pct"],
        total_trip_cost=total_trip_cost,
        total_co2_saved_kg=carbon_res["co2_saved_kg"],
        total_diesel_saved_litres=carbon_res["diesel_saved_litres"],
        packed_shipments=packed_out,
        unpacked_shipments=unpacked_out,
    )


@router.post("/", response_model=PoolResponse)
async def create_pool(
    payload: PoolCreate,
    db: AsyncSession = Depends(get_db)
):
    res_truck = await db.execute(select(Truck).where(Truck.id == payload.truck_id))
    truck = res_truck.scalars().first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    distance_km = RouteMatchingService.haversine_distance(
        truck.origin_lat, truck.origin_lng, truck.dest_lat, truck.dest_lng
    ) * 1.25
    total_cost = round(distance_km * truck.rate_per_km, 2)

    pool = Pool(
        truck_id=truck.id,
        status=PoolStatus.OPEN,
        total_distance_km=distance_km,
        total_cost=total_cost,
    )
    db.add(pool)
    await db.commit()
    await db.refresh(pool)
    return pool


@router.get("/{pool_id}", response_model=PoolResponse)
async def get_pool(pool_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Pool)
        .options(selectinload(Pool.shipments), selectinload(Pool.truck))
        .where(Pool.id == pool_id)
    )
    pool = result.scalars().first()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")
    return pool

