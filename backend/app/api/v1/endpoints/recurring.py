"""
Recurring shipments (Task 11), saved in the database.

1. POST /recurring/ saves a repeat booking once ("every Wed and Sat").
2. POST /recurring/generate posts a normal shipment for every repeat date in a
   period (default: today and the next 6 days). It never makes the same date twice,
   so it is safe to run every day, by hand or from a scheduler.
   Each new shipment tries to join an open pool straight away (auto_join), and the
   answer also groups every open shipment into candidate pools.
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.pools import join_open_pool
from app.db.session import get_db
from app.models.recurring import RecurringShipment
from app.models.shipment import Shipment, ShipmentStatus
from app.schemas.recurring import GenerateResponse, RecurringCreate, RecurringResponse
from app.services import recurring as rec_service
from app.services.route_matching import RouteMatchingService

router = APIRouter()

_COPY = ("goods_type", "weight_kg", "volume_cbm", "length_cm", "width_cm", "height_cm", "is_perishable",
         "is_hazardous", "is_fragile", "temperature_class", "origin_address", "origin_lat", "origin_lng",
         "destination_address", "dest_lat", "dest_lng")


def _as_dict(r: RecurringShipment) -> Dict[str, Any]:
    return {"id": r.id, "repeat": r.repeat, "weekdays": r.weekdays, "start_date": r.start_date,
            "end_date": r.end_date, "window_start_time": r.window_start_time,
            "window_end_time": r.window_end_time, "window_days": r.window_days}


def _out(r: RecurringShipment) -> RecurringResponse:
    res = RecurringResponse.model_validate(r)
    res.repeats = rec_service.describe(_as_dict(r))
    return res


def _ist_day(dt: Optional[datetime]) -> Optional[date]:
    """The IST calendar day of a stored time (SQLite keeps the wall time without a zone)."""
    if dt is None:
        return None
    return (dt.astimezone(rec_service.IST) if dt.tzinfo else dt).date()


async def _get(db: AsyncSession, recurring_id: int) -> RecurringShipment:
    r = (await db.execute(select(RecurringShipment).where(RecurringShipment.id == recurring_id))).scalars().first()
    if not r:
        raise HTTPException(status_code=404, detail="Recurring shipment not found")
    return r


@router.post("/", response_model=RecurringResponse)
async def create_recurring(payload: RecurringCreate, shipper_id: int = Query(default=1, description="Shipper user id"),
                           db: AsyncSession = Depends(get_db)):
    """Save a repeat booking. Nothing is posted until POST /recurring/generate runs."""
    data = payload.model_dump()
    data["weekdays"] = ",".join(payload.weekdays) if payload.weekdays else None
    r = RecurringShipment(shipper_id=shipper_id, active=True, **data)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return _out(r)


@router.get("/", response_model=List[RecurringResponse])
async def list_recurring(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(RecurringShipment).order_by(RecurringShipment.id))).scalars().all()
    return [_out(r) for r in rows]


@router.get("/{recurring_id}", response_model=RecurringResponse)
async def get_recurring(recurring_id: int, db: AsyncSession = Depends(get_db)):
    return _out(await _get(db, recurring_id))


@router.post("/{recurring_id}/stop", response_model=RecurringResponse)
async def stop_recurring(recurring_id: int, db: AsyncSession = Depends(get_db)):
    """Stop future repeats. Shipments already posted stay as they are."""
    r = await _get(db, recurring_id)
    r.active = False
    await db.commit()
    await db.refresh(r)
    return _out(r)


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    from_date: Optional[date] = Query(default=None, description="Default: today (IST)"),
    to_date: Optional[date] = Query(default=None, description="Default: 6 days after from_date"),
    auto_join: bool = Query(default=True, description="Put each new shipment into a matching open pool if one has room"),
    db: AsyncSession = Depends(get_db),
):
    """
    For every active recurring shipment, post a shipment (status POSTED, with
    `recurring_id`) for each repeat date from `from_date` to `to_date` that doesn't
    have one yet. With `auto_join`, each new shipment joins the first open pool whose
    truck goes its way, whose delivery window overlaps, and that still has room
    (cost shares are worked out again). `candidate_pools` groups all open shipments
    that are still not in a pool, so the rest can be pooled with POST /pools.
    """
    from_date = from_date or datetime.now(rec_service.IST).date()
    to_date = to_date or from_date + timedelta(days=6)
    if to_date < from_date or (to_date - from_date).days > 92:
        raise HTTPException(status_code=400, detail="to_date must be 0 to 92 days after from_date")

    recs = (await db.execute(
        select(RecurringShipment).where(RecurringShipment.active.is_(True)).order_by(RecurringShipment.id)
    )).scalars().all()

    created, already = [], 0
    for r in recs:
        have = {_ist_day(s.delivery_window_start) for s in (await db.execute(
            select(Shipment).where(Shipment.recurring_id == r.id))).scalars().all()}
        for day in rec_service.occurrence_dates(_as_dict(r), from_date, to_date):
            if day in have:
                already += 1
                continue
            win = rec_service.delivery_window(_as_dict(r), day)
            s = Shipment(shipper_id=r.shipper_id, recurring_id=r.id, title=f"{r.title} ({day:%a %d %b})",
                         status=ShipmentStatus.POSTED, **{k: getattr(r, k) for k in _COPY}, **win)
            db.add(s)
            await db.flush()
            await db.refresh(s)  # read back as stored, so its times compare like the other rows
            joined = await join_open_pool(db, s) if auto_join else {"pool_id": None, "reason": "auto_join is off"}
            created.append({"shipment_id": s.id, "recurring_id": r.id, "date": day, "title": s.title, **joined})
    await db.commit()

    open_rows = (await db.execute(
        select(Shipment).where(Shipment.pool_id.is_(None),
                               Shipment.status.in_((ShipmentStatus.POSTED, ShipmentStatus.MATCHED)))
        .order_by(Shipment.id)
    )).scalars().all()
    pools = RouteMatchingService.find_candidate_pools([
        {"id": s.id, "recurring_id": s.recurring_id, "weight_kg": s.weight_kg, "volume_cbm": s.volume_cbm,
         "goods_type": s.goods_type, "is_perishable": s.is_perishable, "is_hazardous": s.is_hazardous,
         "is_fragile": s.is_fragile, "temperature_class": s.temperature_class,
         "origin_lat": s.origin_lat, "origin_lng": s.origin_lng, "dest_lat": s.dest_lat, "dest_lng": s.dest_lng,
         "origin_address": s.origin_address, "destination_address": s.destination_address,
         "delivery_window_start": s.delivery_window_start, "delivery_window_end": s.delivery_window_end}
        for s in open_rows
    ])
    return {"from_date": from_date, "to_date": to_date, "created": created, "already_there": already,
            "candidate_pools": pools}
