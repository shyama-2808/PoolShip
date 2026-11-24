"""
Hub support (Task 12): two-leg journeys when no single truck covers the route.

Example: jute bags from Bengaluru to Kolkata. No truck drives Bengaluru to
Kolkata, but one drives Bengaluru to Hyderabad and another drives Hyderabad to
Kolkata. The goods ride the first truck to the Hyderabad hub, wait, and change
to the second truck.

Steps for one shipment:
  1. DIRECT FIRST: if a truck's route covers the whole trip (same corridor test
     as Task 1), the shipment fits, and the truck gets there before the delivery
     window closes, no hub is needed (mode "direct").
  2. DETOUR: for each hub, the trip pickup -> hub -> drop must not be more than
     `max_detour_pct` longer than pickup -> drop. Hubs far off the way are skipped.
  3. LEG TRUCKS: leg 1 (pickup -> hub) needs a truck whose route covers it, and
     leg 2 (hub -> drop) needs a different truck whose route covers that.
     The shipment must fit in each truck's spare room (weight and volume,
     counting what the truck already carries if `used_weight_kg/used_volume_cbm`
     are given) and the box must fit its hold.
  4. TIMING (45 km/h, same as the return-trip estimate):
       leg 1 truck leaves its origin at its available_date, drives to the pickup,
       then to the hub. The goods are ready to move on `transfer_hours` later.
       Leg 2 truck reaches the hub (from its origin, from its available_date);
       it leaves at whichever is later: goods ready, or truck at the hub.
       It then drives hub -> drop. Late (after delivery_window_end) = rejected.
  5. COST of each leg = leg km x that truck's Rs/km x the share of the truck the
     shipment uses (higher of weight share and volume share), the same base
     price as Task 9. Plus the hub's handling charge (Rs per kg).
  6. BEST: the on-time option that delivers earliest (cheaper first if equal).
     Every hub that didn't work is listed with the reason.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.services.route_matching import RouteMatchingService

AVG_SPEED_KMH = 45.0
DEFAULT_TRANSFER_HOURS = 3.0
DEFAULT_HANDLING_RATE_PER_KG = 1.0
DEFAULT_MAX_DETOUR_PCT = 30.0
_EPS = 1e-9

R = RouteMatchingService


def _km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return R.road_distance_km(lat1, lng1, lat2, lng2)


def _minute(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return (dt + timedelta(seconds=30)).replace(second=0, microsecond=0)


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _volume(s: Dict[str, Any]) -> float:
    return s.get("volume_cbm") or (s.get("length_cm", 100) * s.get("width_cm", 100) * s.get("height_cm", 100)) / 1e6


def _covers(truck: Dict[str, Any], a: Tuple[float, float], b: Tuple[float, float], tol: float) -> Optional[str]:
    """None if the truck's route carries a load from a to b, else why not."""
    leg = {"id": 0, "origin_lat": a[0], "origin_lng": a[1], "dest_lat": b[0], "dest_lng": b[1]}
    res = R.find_matching_shipments(truck, [leg], tol)
    return None if res["matched"] else res["rejected"][0]["reason"]


def _room(truck: Dict[str, Any], s: Dict[str, Any]) -> Optional[str]:
    """None if the shipment fits the truck's spare room, else why not."""
    used_kg = truck.get("used_weight_kg") or 0.0
    used_cbm = truck.get("used_volume_cbm") or 0.0
    if used_kg + s["weight_kg"] > truck["max_weight_kg"] + _EPS:
        return f"has only {truck['max_weight_kg'] - used_kg:.0f} kg spare (shipment is {s['weight_kg']:.0f} kg)"
    if used_cbm + _volume(s) > truck["max_volume_cbm"] + _EPS:
        return f"has only {truck['max_volume_cbm'] - used_cbm:.2f} m3 spare (shipment is {_volume(s):.2f} m3)"
    for dim in ("length_cm", "width_cm", "height_cm"):
        if s.get(dim, 100) > truck.get(dim, 1e9):
            return "the box is bigger than its cargo hold"
    return None


def _share(truck: Dict[str, Any], s: Dict[str, Any]) -> float:
    return max(s["weight_kg"] / truck["max_weight_kg"], _volume(s) / truck["max_volume_cbm"])


def _leg_cost(km: float, truck: Dict[str, Any], s: Dict[str, Any]) -> float:
    return round(km * (truck.get("rate_per_km") or 35.0) * _share(truck, s), 2)


def _reach(truck: Dict[str, Any], via: List[Tuple[float, float]]) -> Tuple[float, Optional[datetime]]:
    """Km from the truck's origin through the points, and when it gets to the last one."""
    km, here = 0.0, (truck["origin_lat"], truck["origin_lng"])
    for p in via:
        km += _km(here[0], here[1], p[0], p[1])
        here = p
    start = R._to_datetime(truck.get("available_date"))
    return km, (start + timedelta(hours=km / AVG_SPEED_KMH)) if start else None


def _soonest(o: Dict[str, Any]):
    """Sort key: earliest delivery first (untimed last), then cheapest."""
    at = o["_at"]
    return (at is None, at.timestamp() if at else 0.0, o.get("total_cost", o.get("cost", 0.0)))


def _trucks_for(trucks, a, b, s, tol, skip_id=None):
    ok, why = [], []
    for t in trucks:
        if t["id"] == skip_id:
            continue
        reason = _covers(t, a, b, tol) or _room(t, s)
        (why if reason else ok).append((t, reason))
    return ok, why


def _direct(s: Dict[str, Any], trucks: List[Dict[str, Any]], tol: float, deadline: Optional[datetime]):
    """Trucks that cover the whole trip and have room (with their timing), and trucks that cover it but are full."""
    pick, drop = (s["origin_lat"], s["origin_lng"]), (s["dest_lat"], s["dest_lng"])
    options = []
    full = [f"truck {t['id']} covers the trip but {_room(t, s)}"
            for t in trucks if not _covers(t, pick, drop, tol) and _room(t, s)]
    ok, _ = _trucks_for(trucks, pick, drop, s, tol)
    for t, _ in ok:
        _, arrive = _reach(t, [pick, drop])
        arrive = _minute(arrive)
        on_time = not (deadline and arrive and arrive > deadline)
        km = _km(*pick, *drop)
        options.append({"truck_id": t["id"], "delivered_at": _iso(arrive), "on_time": on_time,
                        "cost": _leg_cost(km, t, s), "_at": arrive})
    return options, full


def plan_route(
    shipment: Dict[str, Any],
    trucks: List[Dict[str, Any]],
    hubs: List[Dict[str, Any]],
    corridor_tolerance_km: float = 40.0,
    max_detour_pct: float = DEFAULT_MAX_DETOUR_PCT,
) -> Dict[str, Any]:
    """Direct truck if there is one, else the best two-leg journey through a hub (see the module notes)."""
    s = shipment
    pick, drop = (s["origin_lat"], s["origin_lng"]), (s["dest_lat"], s["dest_lng"])
    deadline = R._to_datetime(s.get("delivery_window_end"))
    direct_km = round(_km(*pick, *drop), 1)
    base = {"shipment_id": s["id"], "from": s.get("origin_address"), "to": s.get("destination_address"),
            "direct_km": direct_km, "deadline": _iso(deadline), "corridor_tolerance_km": corridor_tolerance_km,
            "max_detour_pct": max_detour_pct}

    # 1. A single truck that does the whole trip on time wins
    direct, full = _direct(s, trucks, corridor_tolerance_km, deadline)
    good = sorted([d for d in direct if d["on_time"]], key=_soonest)
    for d in direct:
        d.pop("_at")
    if good:
        best = good[0]
        return {**base, "mode": "direct", "direct_trucks": direct, "best": None, "options": [],
                "rejected_hubs": [],
                "summary": (f"No hub needed: truck {best['truck_id']} covers the whole trip"
                            + (f" and delivers by {best['delivered_at'][:16]}" if best["delivered_at"] else ""))}

    # 2-5. Try every hub
    options, rejected = [], []
    for hub in hubs:
        h = (hub["lat"], hub["lng"])
        name = hub.get("name") or hub.get("city") or f"hub {hub['id']}"
        leg1_km, leg2_km = _km(*pick, *h), _km(*h, *drop)
        if leg1_km < 1 or leg2_km < 1:
            rejected.append({"hub_id": hub["id"], "name": name, "reason": "the hub is the pickup or the drop itself"})
            continue
        extra_pct = (leg1_km + leg2_km - direct_km) / direct_km * 100 if direct_km else 0.0
        if extra_pct > max_detour_pct:
            rejected.append({"hub_id": hub["id"], "name": name,
                             "reason": f"going through it adds {extra_pct:.0f}% to the trip "
                                       f"(limit {max_detour_pct:.0f}%)"})
            continue

        first, first_no = _trucks_for(trucks, pick, h, s, corridor_tolerance_km)
        if not first:
            rejected.append({"hub_id": hub["id"], "name": name,
                             "reason": f"no truck with room goes from {s.get('origin_address') or 'the pickup'} "
                                       f"to {name}"})
            continue
        transfer = float(hub.get("transfer_hours", DEFAULT_TRANSFER_HOURS))
        handling = round(s["weight_kg"] * float(hub.get("handling_rate_per_kg", DEFAULT_HANDLING_RATE_PER_KG)), 2)

        pairs, late, no_second = [], [], True
        for t1, _ in first:
            _, at_hub = _reach(t1, [pick, h])
            ready = at_hub + timedelta(hours=transfer) if at_hub else None
            second, _ = _trucks_for(trucks, h, drop, s, corridor_tolerance_km, skip_id=t1["id"])
            for t2, _ in second:
                no_second = False
                _, t2_at_hub = _reach(t2, [h])
                # no available_date on either truck = no timing, so no on-time check
                leaves = max(ready, t2_at_hub) if ready and t2_at_hub else None
                delivered = leaves + timedelta(hours=leg2_km / AVG_SPEED_KMH) if leaves else None
                opt = _option(s, hub, name, t1, t2, leg1_km, leg2_km, direct_km, transfer, handling,
                              at_hub, ready, leaves, delivered, deadline)
                (late if opt["_late"] else pairs).append(opt)

        if pairs:
            pairs.sort(key=_soonest)
            options.append(pairs[0])
        elif late:
            worst = min(late, key=_soonest)
            rejected.append({"hub_id": hub["id"], "name": name,
                             "reason": f"trucks {worst['legs'][0]['truck_id']} and {worst['legs'][1]['truck_id']} "
                                       f"would deliver at {worst['delivered_at'][:16]}, after the deadline "
                                       f"{_iso(deadline)[:16]}"})
        elif no_second:
            rejected.append({"hub_id": hub["id"], "name": name,
                             "reason": f"no truck with room goes from {name} to "
                                       f"{s.get('destination_address') or 'the drop'}"})

    options.sort(key=_soonest)
    for o in options:
        o.pop("_at"), o.pop("_late")
    best = options[0] if options else None
    if best:
        l1, l2 = best["legs"]
        summary = (f"No single truck covers this trip on time. Go through {best['hub']['name']}: truck "
                   f"{l1['truck_id']} to the hub, wait {best['wait_at_hub_hours']} h, then truck {l2['truck_id']}"
                   + (f", delivered {best['delivered_at'][:16]}" if best["delivered_at"] else "")
                   + f". Total Rs {best['total_cost']}.")
    else:
        why = [f"truck {d['truck_id']} covers the trip but would deliver at {d['delivered_at'][:16]}, too late"
               for d in direct if not d["on_time"] and d["delivered_at"]] + full
        summary = ("No single truck and no hub route can carry this shipment on time"
                   + (": " + "; ".join(why) if why else "") + ".")
    return {**base, "mode": "hub" if best else "none", "direct_trucks": direct, "best": best,
            "options": options, "rejected_hubs": rejected, "summary": summary}


def _option(s, hub, name, t1, t2, leg1_km, leg2_km, direct_km, transfer, handling,
            at_hub, ready, leaves, delivered, deadline) -> Dict[str, Any]:
    at_hub, ready, leaves, delivered = (_minute(x) for x in (at_hub, ready, leaves, delivered))
    c1, c2 = _leg_cost(leg1_km, t1, s), _leg_cost(leg2_km, t2, s)
    total_km = leg1_km + leg2_km
    wait = round((leaves - at_hub).total_seconds() / 3600, 1) if leaves and at_hub else None
    is_late = bool(deadline and delivered and delivered > deadline)
    return {
        "hub": {"id": hub["id"], "name": name, "lat": hub["lat"], "lng": hub["lng"]},
        "legs": [
            {"leg": 1, "truck_id": t1["id"], "from": s.get("origin_address"), "to": name,
             "km": round(leg1_km, 1), "arrives_at": _iso(at_hub), "cost": c1},
            {"leg": 2, "truck_id": t2["id"], "from": name, "to": s.get("destination_address"),
             "km": round(leg2_km, 1), "departs_at": _iso(leaves), "arrives_at": _iso(delivered), "cost": c2},
        ],
        "transfer_hours": transfer,
        "ready_at_hub": _iso(ready),
        "wait_at_hub_hours": wait,
        "total_km": round(total_km, 1),
        "extra_km": round(total_km - direct_km, 1),
        "extra_pct": round((total_km - direct_km) / direct_km * 100, 1) if direct_km else 0.0,
        "delivered_at": _iso(delivered),
        "spare_hours": round((deadline - delivered).total_seconds() / 3600, 1) if deadline and delivered else None,
        "handling_fee": handling,
        "total_cost": round(c1 + c2 + handling, 2),
        "_at": delivered,
        "_late": is_late,
    }
