"""
Recurring shipments (Task 11).

Many small businesses send the same load on the same route again and again:
"400 kg of cotton bales to Chennai every Wednesday and Saturday".
Instead of posting it by hand each time, the shipper saves it ONCE as a
recurring shipment, and the engine turns every repeat into an ordinary
shipment that goes into pool matching like any other.

A recurring shipment is a normal shipment (goods, weight, pickup, drop) plus:
  * repeat:      "daily" or "weekly"
  * weekdays:    for weekly, which days, e.g. ["wed", "sat"]
                 (left out = the weekday of start_date)
  * start_date / end_date: the first and last day it may repeat (end_date optional)
  * window_start_time / window_end_time / window_days: the delivery window of
    each repeat. "09:00", "18:00", 1 means: from 09:00 on the day itself until
    18:00 the next day. Times are India time (IST, UTC+05:30).

Steps:
  1. DATES: list every day between from_date and to_date (inclusive) that the
     repeat falls on, inside start_date .. end_date.
  2. COPIES: each date becomes its own shipment with its own delivery window.
     Its id is recurring id x 1000 + occurrence number (so 2003 = the 3rd
     repeat of recurring shipment 2), and it keeps `recurring_id`.
  3. POOLS: the copies are added to the other open shipments and grouped with
     the normal pool finder (Task 2). Two copies of the SAME recurring shipment
     never share a pool: each is a separate load for a separate day.
"""
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.services.route_matching import RouteMatchingService

IST = timezone(timedelta(hours=5, minutes=30))
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
ID_STEP = 1000  # occurrence id = recurring id x 1000 + occurrence number

# Fields copied from the recurring shipment onto every copy
SHIPMENT_FIELDS = (
    "title", "goods_type", "weight_kg", "volume_cbm", "length_cm", "width_cm", "height_cm",
    "is_perishable", "is_hazardous", "is_fragile", "temperature_class",
    "origin_address", "origin_lat", "origin_lng", "destination_address", "dest_lat", "dest_lng",
    "shipper_key", "shipper_id",
)


def _to_date(value: Any) -> Optional[date]:
    if value is None or (isinstance(value, date) and not isinstance(value, datetime)):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def _to_time(value: Any) -> time:
    if isinstance(value, time):
        return value
    hh, mm = str(value).split(":")[:2]
    return time(int(hh), int(mm))


def repeat_weekdays(rec: Dict[str, Any]) -> List[int]:
    """Weekday numbers (0 = Monday) the shipment repeats on."""
    if rec.get("repeat", "weekly") == "daily":
        return list(range(7))
    days = rec.get("weekdays")
    if isinstance(days, str):
        days = [d for d in days.split(",") if d.strip()]
    if not days:
        return [_to_date(rec["start_date"]).weekday()]
    return sorted({WEEKDAYS.index(str(d).strip().lower()[:3]) for d in days})


def describe(rec: Dict[str, Any]) -> str:
    """A short plain-words label, e.g. 'every Wed and Sat' or 'every day'."""
    if rec.get("repeat", "weekly") == "daily":
        return "every day"
    names = [WEEKDAYS[i].capitalize() for i in repeat_weekdays(rec)]
    return "every " + (names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1])


def occurrence_dates(rec: Dict[str, Any], from_date: Any, to_date: Any) -> List[date]:
    """Every date from from_date to to_date (both included) the shipment repeats on."""
    start = max(_to_date(from_date), _to_date(rec["start_date"]))
    end = _to_date(to_date)
    if rec.get("end_date"):
        end = min(end, _to_date(rec["end_date"]))
    days = set(repeat_weekdays(rec))
    out, d = [], start
    while d <= end:
        if d.weekday() in days:
            out.append(d)
        d += timedelta(days=1)
    return out


def occurrence_number(rec: Dict[str, Any], day: date) -> int:
    """1 for the first repeat since start_date, 2 for the next, and so on (stable whatever range you ask for)."""
    return len(occurrence_dates({**rec, "end_date": None}, rec["start_date"], day))


def delivery_window(rec: Dict[str, Any], day: date) -> Dict[str, datetime]:
    start_t = _to_time(rec.get("window_start_time") or "09:00")
    end_t = _to_time(rec.get("window_end_time") or "18:00")
    days = int(rec.get("window_days", 1) or 0)
    return {
        "delivery_window_start": datetime.combine(day, start_t, IST),
        "delivery_window_end": datetime.combine(day + timedelta(days=days), end_t, IST),
    }


def make_occurrence(rec: Dict[str, Any], day: date) -> Dict[str, Any]:
    """The shipment for one repeat date."""
    n = occurrence_number(rec, day)
    win = delivery_window(rec, day)
    s = {k: rec[k] for k in SHIPMENT_FIELDS if k in rec}
    s.update({
        "id": rec["id"] * ID_STEP + n,
        "recurring_id": rec["id"],
        "occurrence": n,
        "occurrence_date": day.isoformat(),
        "delivery_window_start": win["delivery_window_start"].isoformat(),
        "delivery_window_end": win["delivery_window_end"].isoformat(),
    })
    return s


def expand(recurring: List[Dict[str, Any]], from_date: Any, to_date: Any) -> List[Dict[str, Any]]:
    """Every repeat of every recurring shipment between the two dates, in date order."""
    out = [make_occurrence(r, d) for r in recurring for d in occurrence_dates(r, from_date, to_date)]
    return sorted(out, key=lambda s: (s["occurrence_date"], s["id"]))


def plan_period(
    recurring: List[Dict[str, Any]],
    shipments: List[Dict[str, Any]],
    from_date: Any,
    to_date: Any,
    corridor_tolerance_km: float = 40.0,
) -> Dict[str, Any]:
    """
    Turn the repeats in this period into shipments and pool them together with
    the other open shipments. Says, for each recurring shipment and each date,
    which pool it went into, or why it didn't get one.
    """
    if _to_date(to_date) < _to_date(from_date):
        raise ValueError("to_date is before from_date")
    copies = expand(recurring, from_date, to_date)
    taken = {s["id"] for s in shipments}
    clash = sorted(taken & {c["id"] for c in copies})
    if clash:
        raise ValueError(f"Shipment ids {clash} are also used by repeat copies; one-off ids must be below {ID_STEP}")

    found = RouteMatchingService.find_candidate_pools(shipments + copies, corridor_tolerance_km)
    pool_of = {sid: p for p in found["pools"] for sid in p["shipment_ids"]}
    why = {u["shipment_id"]: u["reason"] for u in found["unmatched"]}

    by_rec: Dict[Any, List[Dict[str, Any]]] = {r["id"]: [] for r in recurring}
    for c in copies:
        pool = pool_of.get(c["id"])
        by_rec[c["recurring_id"]].append({
            "date": c["occurrence_date"],
            "weekday": WEEKDAYS[_to_date(c["occurrence_date"]).weekday()].capitalize(),
            "shipment_id": c["id"],
            "pool_id": pool["pool_id"] if pool else None,
            "pooled_with": [i for i in pool["shipment_ids"] if i != c["id"]] if pool else [],
            "reason": None if pool else why.get(c["id"]),
        })

    summary = []
    for r in recurring:
        rows = by_rec[r["id"]]
        pooled = sum(1 for x in rows if x["pool_id"] is not None)
        summary.append({
            "recurring_id": r["id"],
            "title": r.get("title"),
            "repeat": r.get("repeat", "weekly"),
            "repeats": describe(r),
            "route": f"{r.get('origin_address')} to {r.get('destination_address')}",
            "occurrences": len(rows),
            "pooled": pooled,
            "not_pooled": len(rows) - pooled,
            "dates": rows,
        })

    return {
        "from_date": _to_date(from_date).isoformat(),
        "to_date": _to_date(to_date).isoformat(),
        "corridor_tolerance_km": corridor_tolerance_km,
        "occurrences_created": len(copies),
        "recurring": summary,
        "pools": found["pools"],
        "unmatched": found["unmatched"],
    }
