from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.pool import Pool, PoolStatus
from app.models.tracking import TrackingEvent
from app.schemas.tracking import TrackingEventCreate, TrackingEventResponse

router = APIRouter()


@router.post("/", response_model=TrackingEventResponse, status_code=status.HTTP_201_CREATED)
async def create_tracking_event(
    event_in: TrackingEventCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify pool exists
    res = await db.execute(select(Pool).where(Pool.id == event_in.pool_id))
    pool = res.scalars().first()
    if not pool:
        raise HTTPException(status_code=404, detail="Pool not found")

    event = TrackingEvent(
        pool_id=event_in.pool_id,
        status=event_in.status,
        location_name=event_in.location_name,
        latitude=event_in.latitude,
        longitude=event_in.longitude,
        note=event_in.note,
        proof_photo_url=event_in.proof_photo_url,
        digital_signature=event_in.digital_signature,
        delivery_otp=event_in.delivery_otp,
    )
    db.add(event)

    # Update pool status if event indicates status advancement
    if event_in.status == "IN_TRANSIT":
        pool.status = PoolStatus.IN_TRANSIT
    elif event_in.status == "DELIVERED":
        pool.status = PoolStatus.COMPLETED

    await db.commit()
    await db.refresh(event)
    return event


@router.get("/pool/{pool_id}", response_model=List[TrackingEventResponse])
async def get_pool_tracking_timeline(pool_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrackingEvent)
        .where(TrackingEvent.pool_id == pool_id)
        .order_by(TrackingEvent.timestamp.desc())
    )
    return result.scalars().all()

