"""
Empty-return-trip matching (Task 8).

After a truck delivers at its destination it usually drives home EMPTY.
This finds open shipments along that way back, so the return trip earns money too.

Steps:
  1. RETURN ROUTE: from the truck's destination back to its origin (or to a
     different home base if `return_dest_lat/lng` is given).
  2. WHEN: the truck leaves for home after driving out (road km / 45 km/h) and
     unloading (2 hours by default), counted from its `available_date`.
  3. ROUTE MATCH: same corridor test as outbound trucks (Task 1), on the
     reversed route: pickup and drop near the road, in the homeward direction.
  4. ON TIME: the truck must reach the shipment's drop before its delivery
     window closes. Shipments it would deliver late are rejected with the times.
  5. FIT: what's left is packed into the empty truck (weight, volume, size,
     compatibility rules), and the best stop order is worked out.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.services import route_optimizer
from app.services.capacity_optimizer import CapacityOptimizer, ShipmentItem, TruckSpec
from app.services.cost_splitter import CostSplitter
from app.services.route_matching import RouteMatchingService

AVG_SPEED_KMH = route_optimizer.AVG_SPEED_KMH
DEFAULT_UNLOADING_HOURS = 2.0


def _road_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return RouteMatchingService.road_distance_km(lat1, lng1, lat2, lng2)


def _hours(km: float) -> float:
    return km / AVG_SPEED_KMH


def _to_minute(dt: Optional[datetime]) -> Optional[datetime]:
    """Round a time to the nearest minute (estimates don't need seconds)."""
    if dt is None:
        return None
    return (dt + timedelta(seconds=30)).replace(second=0, microsecond=0)


def return_route(truck: Dict[str, Any], unloading_hours: float = DEFAULT_UNLOADING_HOURS) -> Dict[str, Any]:
    """Where and when the truck's trip home starts and ends."""
    home_lat = truck.get("return_dest_lat") or truck["origin_lat"]
    home_lng = truck.get("return_dest_lng") or truck["origin_lng"]
    outbound_km = _road_km(truck["origin_lat"], truck["origin_lng"], truck["dest_lat"], truck["dest_lng"])
    return_km = _road_km(truck["dest_lat"], truck["dest_lng"], home_lat, home_lng)

    available = RouteMatchingService._to_datetime(truck.get("available_date"))
    departs = _to_minute(available + timedelta(hours=_hours(outbound_km) + unloading_hours)) if available else None
    arrives = _to_minute(departs + timedelta(hours=_hours(return_km))) if departs else None
    return {
        "from": {"lat": truck["dest_lat"], "lng": truck["dest_lng"], "place": truck.get("destination_city")},
        "to": {"lat": home_lat, "lng": home_lng,
               "place": truck.get("return_city") or truck.get("origin_city")},
        "outbound_km": round(outbound_km, 1),
        "return_km": round(return_km, 1),
        "departs_at": departs.isoformat() if departs else None,
        "arrives_home_at": arrives.isoformat() if arrives else None,
        "_departs": departs,
    }


def _item(s: Dict[str, Any]) -> ShipmentItem:
    volume = s.get("volume_cbm") or (s.get("length_cm", 100) * s.get("width_cm", 100) * s.get("height_cm", 100)) / 1e6
    return ShipmentItem(
        id=s["id"], weight_kg=s["weight_kg"], volume_cbm=volume,
        length_cm=s.get("length_cm", 100.0), width_cm=s.get("width_cm", 100.0), height_cm=s.get("height_cm", 100.0),
        is_perishable=bool(s.get("is_perishable")), is_hazardous=bool(s.get("is_hazardous")),
        is_fragile=bool(s.get("is_fragile")), goods_type=s.get("goods_type"),
        temperature_class=s.get("temperature_class") or "ambient",
    )


def match_return_loads(
    truck: Dict[str, Any],
    shipments: List[Dict[str, Any]],
    corridor_tolerance_km: float = 40.0,
    unloading_hours: float = DEFAULT_UNLOADING_HOURS,
) -> Dict[str, Any]:
    """Open shipments the truck can carry on its way home (see the module notes for the steps)."""
    rr = return_route(truck, unloading_hours)
    departs: Optional[datetime] = rr.pop("_departs")
    start, home = rr["from"], rr["to"]

    # 3. Route match on the reversed route
    homeward = {"origin_lat": start["lat"], "origin_lng": start["lng"], "dest_lat": home["lat"], "dest_lng": home["lng"]}
    route = RouteMatchingService.find_matching_shipments(homeward, shipments, corridor_tolerance_km)
    by_id = {s["id"]: s for s in shipments}
    rejected = [dict(r) for r in route["rejected"]]

    # 4. On time? Truck drives depot -> pickup -> drop (simple estimate at 45 km/h)
    on_time: List[Dict[str, Any]] = []
    timing: Dict[Any, Dict[str, Any]] = {}
    for m in route["matched"]:
        s = by_id[m["shipment_id"]]
        km_to_drop = (_road_km(start["lat"], start["lng"], s["origin_lat"], s["origin_lng"])
                      + _road_km(s["origin_lat"], s["origin_lng"], s["dest_lat"], s["dest_lng"]))
        drop_at = _to_minute(departs + timedelta(hours=_hours(km_to_drop))) if departs else None
        deadline = RouteMatchingService._to_datetime(s.get("delivery_window_end"))
        timing[s["id"]] = {"estimated_drop_at": drop_at.isoformat() if drop_at else None,
                           "shipment_distance_km": m["shipment_distance_km"]}
        if drop_at and deadline and drop_at > deadline:
            rejected.append({
                "shipment_id": s["id"],
                "reason": (f"On the route, but the truck would only reach the drop around "
                           f"{drop_at.isoformat(timespec='minutes')}, after its delivery window closes at "
                           f"{deadline.isoformat(timespec='minutes')}"),
            })
            continue
        on_time.append(s)

    # 5. Pack the empty truck and order the stops
    spec = TruckSpec(id=truck["id"], max_weight_kg=truck["max_weight_kg"], max_volume_cbm=truck["max_volume_cbm"],
                     length_cm=truck.get("length_cm", 420.0), width_cm=truck.get("width_cm", 200.0),
                     height_cm=truck.get("height_cm", 200.0))
    load = CapacityOptimizer.optimize_load(spec, [_item(s) for s in on_time])
    for u in load["unpacked_items"]:
        rejected.append({"shipment_id": u["item"].id, "reason": f"On the route and on time, but: {u['reason']}"})
    packed_ids = [i.id for i in load["packed_items"]]
    packed = [by_id[i] for i in packed_ids]
    stop_plan = route_optimizer.optimize_stops_offline(packed, start, home) if packed else None

    # The return trip now earns money: its cost is shared by the loads it carries (tonnes x km)
    rate = truck.get("rate_per_km") or 35.0
    trip_cost = CostSplitter.trip_cost(rr["return_km"], rate) if packed else 0.0
    shares = CostSplitter.calculate_split(trip_cost, [
        {"id": s["id"], "weight_kg": s["weight_kg"], "distance_km": timing[s["id"]]["shipment_distance_km"]}
        for s in packed
    ], "ton_km") if packed else []
    pays = {sh["shipment_id"]: sh["allocated_cost"] for sh in shares}
    return {
        "truck_id": truck["id"],
        "return_route": rr,
        "corridor_tolerance_km": corridor_tolerance_km,
        "matched": [
            {"shipment_id": i, "weight_kg": by_id[i]["weight_kg"], **timing[i],
             "from": by_id[i].get("origin_address"), "to": by_id[i].get("destination_address"),
             "pays": pays[i]}
            for i in sorted(packed_ids)
        ],
        "rejected": sorted(rejected, key=lambda r: r["shipment_id"]),
        "load": {
            "total_weight_kg": load["total_packed_weight_kg"],
            "total_volume_cbm": load["total_packed_volume_cbm"],
            "overall_utilization_pct": load["overall_utilization_pct"],
        },
        "stop_plan": stop_plan,
        "return_trip_earnings": trip_cost,
        "is_empty_return": not packed,
    }
