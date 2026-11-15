from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.truck import Truck
from app.schemas.truck import TruckCreate, TruckResponse

router = APIRouter()


@router.post("/", response_model=TruckResponse)
async def create_truck(
    truck_in: TruckCreate,
    transporter_id: int = Query(default=1, description="Transporter User ID"),
    db: AsyncSession = Depends(get_db)
):
    truck = Truck(
        transporter_id=transporter_id,
        truck_type=truck_in.truck_type,
        registration_number=truck_in.registration_number,
        max_weight_kg=truck_in.max_weight_kg,
        max_volume_cbm=truck_in.max_volume_cbm,
        length_cm=truck_in.length_cm,
        width_cm=truck_in.width_cm,
        height_cm=truck_in.height_cm,
        origin_city=truck_in.origin_city,
        origin_lat=truck_in.origin_lat,
        origin_lng=truck_in.origin_lng,
        destination_city=truck_in.destination_city,
        dest_lat=truck_in.dest_lat,
        dest_lng=truck_in.dest_lng,
        available_date=truck_in.available_date,
        rate_per_km=truck_in.rate_per_km,
        is_active=True,
    )
    db.add(truck)
    await db.commit()
    await db.refresh(truck)
    return truck


@router.get("/", response_model=List[TruckResponse])
async def list_trucks(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Truck).where(Truck.is_active == True)
    if origin:
        query = query.where(Truck.origin_city.ilike(f"%{origin}%"))
    if destination:
        query = query.where(Truck.destination_city.ilike(f"%{destination}%"))
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{truck_id}", response_model=TruckResponse)
async def get_truck(truck_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Truck).where(Truck.id == truck_id))
    truck = result.scalars().first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck
