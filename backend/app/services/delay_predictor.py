"""
Delay prediction (Task 10).

ETA = departure time + driving time (with traffic) + time spent at each stop + rest breaks.

  * DRIVING TIME per leg comes from the stop plan (Task 6): OSRM's road time, or the
    offline estimate at 45 km/h.
  * TRAFFIC (simple model, no paid traffic API needed): driving is slower or faster
    depending on the clock. Each leg is driven in 30-minute slices and every slice is
    multiplied by the factor for the hour it is driven in:
        08:00-11:00 and 17:00-21:00  rush hour   x1.50
        23:00-05:00                  night       x0.90
        any other time               normal day  x1.15
    If you have a live traffic number (e.g. 1.3 = 30% slower than free flow) pass it
    as `traffic_multiplier` and it is used for every slice instead.
  * STOPS: 30 minutes at each pickup and drop for loading or unloading.
  * REST: the driver takes a 30-minute break after every 4 hours of driving.

DELAY FLAG for each shipment, from the spare time between its ETA and the end of its
delivery window:
    late      ETA is after the window closes
    at_risk   ETA is less than 2 hours before the window closes
    on_time   2 hours or more to spare
    no_deadline  the shipment has no delivery window end
The pool's flag is the worst of its shipments'.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.services.route_matching import RouteMatchingService

# Traffic follows the local clock. PoolShip runs in India, so times are read in IST
# (a database may hand back times in UTC, where 06:00 IST would look like 00:30 "night").
LOCAL_TZ = timezone(timedelta(hours=5, minutes=30), "IST")

RUSH_HOURS = (range(8, 11), range(17, 21))
NIGHT_HOURS = (23, 0, 1, 2, 3, 4)
RUSH_FACTOR, NIGHT_FACTOR, DAY_FACTOR = 1.50, 0.90, 1.15
SLICE_MINUTES = 30.0

STOP_MINUTES = 30.0
DRIVE_BEFORE_BREAK_MINUTES = 240.0
BREAK_MINUTES = 30.0

AT_RISK_MINUTES = 120.0
_FLAG_ORDER = {"no_deadline": 0, "on_time": 1, "at_risk": 2, "late": 3}


def traffic_factor(when: datetime) -> float:
    """How much slower than free flow the roads are at this clock time (India time)."""
    h = when.astimezone(LOCAL_TZ).hour if when.tzinfo else when.hour
    if any(h in r for r in RUSH_HOURS):
        return RUSH_FACTOR
    if h in NIGHT_HOURS:
        return NIGHT_FACTOR
    return DAY_FACTOR


def _to_minute(dt: datetime) -> datetime:
    return (dt + timedelta(seconds=30)).replace(second=0, microsecond=0)


def _drive(start: datetime, free_flow_minutes: float, traffic_multiplier: Optional[float]) -> float:
    """Minutes to drive a leg that takes `free_flow_minutes` on empty roads, starting at `start`."""
    taken = 0.0
    left = free_flow_minutes
    while left > 1e-9:
        piece = min(SLICE_MINUTES, left)
        factor = traffic_multiplier if traffic_multiplier else traffic_factor(start + timedelta(minutes=taken))
        taken += piece * factor
        left -= piece
    return taken


def predict(
    stop_plan: Dict[str, Any],
    departure: datetime,
    deadlines: Dict[Any, Optional[datetime]],
    traffic_multiplier: Optional[float] = None,
    already_loaded: Optional[set] = None,
) -> Dict[str, Any]:
    """
    Walk the stop plan from `departure` and time every stop.
    deadlines: shipment id -> end of its delivery window (or None).
    already_loaded: shipments already on the truck (a truck on the road), so their
    pickup takes no loading time.
    """
    already_loaded = already_loaded or set()
    if departure.tzinfo is not None:
        departure = departure.astimezone(LOCAL_TZ)  # show every time in India time
    clock = departure
    driven_since_break = 0.0
    total_drive = total_traffic_delay = total_stop = total_break = 0.0
    timeline: List[Dict[str, Any]] = []
    eta_by_shipment: Dict[Any, datetime] = {}
    arrive = departure

    for stop in stop_plan["stops"]:
        free = stop["leg_minutes"]
        if free > 0:
            drive = _drive(clock, free, traffic_multiplier)
            total_traffic_delay += drive - free
            # rest breaks: one every DRIVE_BEFORE_BREAK_MINUTES of driving
            breaks = int((driven_since_break + drive) // DRIVE_BEFORE_BREAK_MINUTES)
            driven_since_break = (driven_since_break + drive) % DRIVE_BEFORE_BREAK_MINUTES
            clock += timedelta(minutes=drive + breaks * BREAK_MINUTES)
            total_drive += drive
            total_break += breaks * BREAK_MINUTES
        arrive = clock
        if stop["kind"] == "drop" or (stop["kind"] == "pickup" and stop["shipment_id"] not in already_loaded):
            clock += timedelta(minutes=STOP_MINUTES)
            total_stop += STOP_MINUTES
        if stop["kind"] == "drop":
            eta_by_shipment[stop["shipment_id"]] = arrive
        timeline.append({
            "seq": stop["seq"], "kind": stop["kind"], "shipment_id": stop["shipment_id"],
            "place": stop.get("place"), "arrives_at": _to_minute(arrive).isoformat(),
            "leaves_at": _to_minute(clock).isoformat(),
        })

    shipments = []
    for sid, eta in eta_by_shipment.items():
        deadline = RouteMatchingService._to_datetime(deadlines.get(sid))
        if deadline is None:
            flag, spare = "no_deadline", None
        else:
            spare = (deadline - eta).total_seconds() / 60.0
            flag = "late" if spare < 0 else "at_risk" if spare < AT_RISK_MINUTES else "on_time"
        shipments.append({
            "shipment_id": sid,
            "eta": _to_minute(eta).isoformat(),
            "deadline": deadline.isoformat() if deadline else None,
            "minutes_to_spare": round(spare) if spare is not None else None,
            "delay_flag": flag,
            "likely_late": flag in ("late", "at_risk"),
        })
    shipments.sort(key=lambda s: s["shipment_id"])

    pool_flag = max((s["delay_flag"] for s in shipments), key=_FLAG_ORDER.get, default="no_deadline")
    finish = _to_minute(arrive if timeline else departure)  # arrival at the last stop
    return {
        "departure": _to_minute(departure).isoformat(),
        "eta": finish.isoformat(),
        "delay_flag": pool_flag,
        "likely_late": pool_flag in ("late", "at_risk"),
        "late_shipments": [s["shipment_id"] for s in shipments if s["likely_late"]],
        "minutes": {
            "free_flow_driving": round(sum(s["leg_minutes"] for s in stop_plan["stops"])),
            "traffic_delay": round(total_traffic_delay),
            "loading_unloading": round(total_stop),
            "rest_breaks": round(total_break),
        },
        "total_km": stop_plan["total_km"],
        "traffic_model": ("fixed multiplier x%.2f" % traffic_multiplier) if traffic_multiplier else
                         "time of day: rush x1.50, night x0.90, day x1.15",
        "shipments": shipments,
        "timeline": timeline,
    }
