from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.shipment import ShipmentCreate, ShipmentResponse

router = APIRouter()


@router.post("/", response_model=ShipmentResponse)
async def create_shipment(
    shipment_in: ShipmentCreate,
    shipper_id: int = Query(default=1, description="Shipper User ID"),
    db: AsyncSession = Depends(get_db)
):
    shipment = Shipment(
        shipper_id=shipper_id,
        title=shipment_in.title,
        goods_type=shipment_in.goods_type,
        weight_kg=shipment_in.weight_kg,
        volume_cbm=shipment_in.volume_cbm or (
            (shipment_in.length_cm * shipment_in.width_cm * shipment_in.height_cm) / 1_000_000.0
        ),
        length_cm=shipment_in.length_cm,
        width_cm=shipment_in.width_cm,
        height_cm=shipment_in.height_cm,
        is_perishable=shipment_in.is_perishable,
        is_hazardous=shipment_in.is_hazardous,
        is_fragile=shipment_in.is_fragile,
        origin_address=shipment_in.origin_address,
        origin_lat=shipment_in.origin_lat,
        origin_lng=shipment_in.origin_lng,
        destination_address=shipment_in.destination_address,
        dest_lat=shipment_in.dest_lat,
        dest_lng=shipment_in.dest_lng,
        delivery_window_start=shipment_in.delivery_window_start,
        delivery_window_end=shipment_in.delivery_window_end,
        status=ShipmentStatus.POSTED,
    )
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)
    return shipment


@router.get("/", response_model=List[ShipmentResponse])
async def list_shipments(
    status: Optional[ShipmentStatus] = None,
    shipper_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Shipment)
    if status:
        query = query.where(Shipment.status == status)
    if shipper_id:
        query = query.where(Shipment.shipper_id == shipper_id)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    shipment = result.scalars().first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

