"""
Dynamic pricing (Task 9).

    price = base price x multiplier

BASE PRICE: what the shipment's slice of the truck costs for its distance.
    base = shipment km x truck's ₹/km x space share
    space share = the larger of (weight / truck max weight) and (volume / truck max volume)

MULTIPLIER = demand x urgency x fill, kept between MIN_MULTIPLIER and MAX_MULTIPLIER.

  * DEMAND: open shipments per available truck on this route. About 4 per truck is
    normal (factor 1.00). Each extra shipment per truck adds 5%, each one fewer takes
    5% off, kept between 0.80 and 1.25.
  * URGENCY: standard 1.00, express 1.15, urgent 1.30. If you give the hours left until
    the deadline instead, it is worked out: spare time (hours left - driving hours)
    under 6 h is urgent, under 24 h is express, otherwise standard.
  * FILL: how full the truck already is before this shipment joins.
      - nearly empty (under 30%): up to +15% at 0%, because few shippers share
        the truck's fixed cost
      - normal (30% to 75%): 1.00
      - nearly full (over 75%): up to +20% at 100%, because the last space is scarce
"""
from typing import Any, Dict, Optional

from app.services.route_matching import RouteMatchingService

MIN_MULTIPLIER = 0.85
MAX_MULTIPLIER = 1.50

NORMAL_SHIPMENTS_PER_TRUCK = 4.0
DEMAND_STEP = 0.05
DEMAND_MIN, DEMAND_MAX = 0.80, 1.25

URGENCY_FACTORS = {"standard": 1.00, "express": 1.15, "urgent": 1.30}
URGENT_SPARE_HOURS = 6.0
EXPRESS_SPARE_HOURS = 24.0

EMPTY_BELOW_PCT, EMPTY_MAX_EXTRA = 30.0, 0.15
FULL_ABOVE_PCT, FULL_MAX_EXTRA = 75.0, 0.20

AVG_SPEED_KMH = 45.0


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def demand_factor(open_shipments: Optional[int], trucks_available: Optional[int]) -> Dict[str, Any]:
    if open_shipments is None or trucks_available is None:
        return {"factor": 1.0, "why": "No demand numbers given, so demand counts as normal"}
    ratio = open_shipments / max(trucks_available, 1)
    factor = _clamp(1.0 + DEMAND_STEP * (ratio - NORMAL_SHIPMENTS_PER_TRUCK), DEMAND_MIN, DEMAND_MAX)
    level = "high" if ratio > NORMAL_SHIPMENTS_PER_TRUCK else "low" if ratio < NORMAL_SHIPMENTS_PER_TRUCK else "normal"
    return {"factor": round(factor, 4),
            "why": f"{open_shipments} open shipments for {trucks_available} truck(s) = {ratio:.1f} per truck "
                   f"({level} demand; {NORMAL_SHIPMENTS_PER_TRUCK:.0f} is normal)"}


def urgency_level(urgency: Optional[str], hours_until_deadline: Optional[float], drive_hours: float) -> Dict[str, Any]:
    if hours_until_deadline is not None:
        spare = hours_until_deadline - drive_hours
        level = "urgent" if spare < URGENT_SPARE_HOURS else "express" if spare < EXPRESS_SPARE_HOURS else "standard"
        why = (f"{hours_until_deadline:.0f} h until the deadline, {drive_hours:.1f} h of driving, "
               f"so {spare:.1f} h to spare ({level})")
    else:
        level = urgency or "standard"
        why = f"Booked as {level}"
    return {"level": level, "factor": URGENCY_FACTORS[level], "why": why}


def fill_factor(fill_pct: float) -> Dict[str, Any]:
    f = _clamp(fill_pct, 0.0, 100.0)
    if f < EMPTY_BELOW_PCT:
        factor = 1.0 + EMPTY_MAX_EXTRA * (EMPTY_BELOW_PCT - f) / EMPTY_BELOW_PCT
        why = f"Truck is only {f:.0f}% full: few shippers to share its cost"
    elif f > FULL_ABOVE_PCT:
        factor = 1.0 + FULL_MAX_EXTRA * (f - FULL_ABOVE_PCT) / (100.0 - FULL_ABOVE_PCT)
        why = f"Truck is already {f:.0f}% full: the last space is scarce"
    else:
        factor = 1.0
        why = f"Truck is {f:.0f}% full: normal"
    return {"factor": round(factor, 4), "why": why}


def quote(
    shipment_km: float,
    weight_kg: float,
    volume_cbm: float,
    truck_max_weight_kg: float,
    truck_max_volume_cbm: float,
    rate_per_km: float,
    truck_fill_pct: float = 50.0,
    urgency: Optional[str] = "standard",
    hours_until_deadline: Optional[float] = None,
    open_shipments_on_route: Optional[int] = None,
    trucks_available_on_route: Optional[int] = None,
) -> Dict[str, Any]:
    """Price for one shipment, with every factor explained."""
    space_share = max(weight_kg / truck_max_weight_kg, (volume_cbm or 0.0) / truck_max_volume_cbm)
    base = shipment_km * rate_per_km * space_share

    d = demand_factor(open_shipments_on_route, trucks_available_on_route)
    u = urgency_level(urgency, hours_until_deadline, shipment_km / AVG_SPEED_KMH)
    f = fill_factor(truck_fill_pct)
    raw = d["factor"] * u["factor"] * f["factor"]
    multiplier = _clamp(raw, MIN_MULTIPLIER, MAX_MULTIPLIER)

    return {
        "shipment_km": round(shipment_km, 1),
        "space_share_pct": round(space_share * 100.0, 1),
        "base_price": round(base, 2),
        "factors": {
            "demand": d,
            "urgency": u,
            "fill": f,
        },
        "raw_multiplier": round(raw, 4),
        "multiplier": round(multiplier, 4),
        "capped": "at maximum" if raw > MAX_MULTIPLIER else "at minimum" if raw < MIN_MULTIPLIER else None,
        "limits": {"min_multiplier": MIN_MULTIPLIER, "max_multiplier": MAX_MULTIPLIER},
        "price": round(base * multiplier, 2),
    }


def shipment_km(shipment: Dict[str, Any]) -> Optional[float]:
    """Given distance, or road estimate from the coordinates, or None if neither is there."""
    if shipment.get("distance_km"):
        return float(shipment["distance_km"])
    keys = ("origin_lat", "origin_lng", "dest_lat", "dest_lng")
    if all(shipment.get(k) is not None for k in keys):
        return RouteMatchingService.road_distance_km(*(shipment[k] for k in keys))
    return None
