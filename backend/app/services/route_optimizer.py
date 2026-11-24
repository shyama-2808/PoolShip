"""
Multi-stop route optimisation for a pool (Task 6).

A pool's truck has to visit every pickup and every drop. This finds the order
of stops with the fewest km, with one rule: a shipment's pickup must come
before its drop (you can't deliver what you haven't loaded yet).

Distances between stops:
  * OSRM (free online road-routing service) gives real road km and minutes, or
  * if OSRM can't be reached, straight-line distance x 1.25 at 45 km/h.

How the order is found:
  * up to 6 shipments (12 stops): EXACT. It tries every valid order in a smart
    way (dynamic programming over "which stops are done so far"), so the answer
    is the true shortest.
  * more shipments: GOOD, FAST. Start with "go to the nearest stop you're allowed
    to visit next", then keep moving single stops to a better place in the order
    while that makes the trip shorter.

It also works out the "as listed" order (all pickups in the order given, then
all drops in the order given), so you can see how many km the sorting saved.
"""
from typing import Any, Dict, List, Optional, Tuple

from app.services.route_matching import RouteMatchingService

AVG_SPEED_KMH = 45.0   # same truck speed the offline estimate uses elsewhere
EXACT_LIMIT = 6        # shipments; above this the fast heuristic is used

Matrix = List[List[float]]


def _stops_for(shipments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Stop 2k is shipment k's pickup, stop 2k+1 is its drop."""
    stops = []
    for s in shipments:
        stops.append({"kind": "pickup", "shipment_id": s["id"], "lat": s["origin_lat"], "lng": s["origin_lng"],
                      "place": s.get("origin_address")})
        stops.append({"kind": "drop", "shipment_id": s["id"], "lat": s["dest_lat"], "lng": s["dest_lng"],
                      "place": s.get("destination_address")})
    return stops


def estimate_matrix(points: List[Tuple[float, float]]) -> Tuple[Matrix, Matrix]:
    """Offline km and minutes between every pair of (lat, lng) points."""
    n = len(points)
    km = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = RouteMatchingService.road_distance_km(points[i][0], points[i][1], points[j][0], points[j][1])
            km[i][j] = km[j][i] = d
    minutes = [[d / AVG_SPEED_KMH * 60.0 for d in row] for row in km]
    return km, minutes


async def osrm_matrix(points: List[Tuple[float, float]]) -> Optional[Tuple[Matrix, Matrix]]:
    """Road km and minutes from OSRM's table service, or None if it can't be reached."""
    try:
        import httpx
        from app.core.config import settings
        coords = ";".join(f"{lng},{lat}" for lat, lng in points)  # OSRM wants lng,lat
        url = f"{settings.OSRM_BASE_URL}/table/v1/driving/{coords}?annotations=distance,duration"
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(url)
        data = res.json() if res.status_code == 200 else {}
        if data.get("code") != "Ok":
            return None
        dist, dur = data["distances"], data["durations"]
        if any(v is None for row in dist + dur for v in row):
            return None  # some stop can't be reached by road
        return ([[v / 1000.0 for v in row] for row in dist], [[v / 60.0 for v in row] for row in dur])
    except Exception:
        return None


def _route_km(order: List[int], km: Matrix, start: Optional[int], end: Optional[int]) -> float:
    path = ([start] if start is not None else []) + order + ([end] if end is not None else [])
    return sum(km[a][b] for a, b in zip(path, path[1:]))


def _valid(order: List[int]) -> bool:
    """Every drop (odd stop) comes after its pickup (the even stop before it)."""
    seen = set()
    for s in order:
        if s % 2 == 1 and s - 1 not in seen:
            return False
        seen.add(s)
    return True


def _exact(n_stops: int, km: Matrix, start: Optional[int], end: Optional[int]) -> List[int]:
    """
    Shortest valid order by dynamic programming.
    best[(done, last)] = shortest km that visits exactly the stops in `done`
    (a bit mask) and finishes at stop `last`.
    """
    full = (1 << n_stops) - 1
    best: Dict[Tuple[int, int], float] = {}
    came_from: Dict[Tuple[int, int], int] = {}
    for s in range(0, n_stops, 2):  # the first stop must be a pickup
        best[(1 << s, s)] = km[start][s] if start is not None else 0.0

    for done in range(1, full + 1):
        for last in range(n_stops):
            cost = best.get((done, last))
            if cost is None:
                continue
            for nxt in range(n_stops):
                if done & (1 << nxt):
                    continue
                if nxt % 2 == 1 and not done & (1 << (nxt - 1)):
                    continue  # drop before its pickup: not allowed
                key = (done | (1 << nxt), nxt)
                new = cost + km[last][nxt]
                if new < best.get(key, float("inf")) - 1e-9:
                    best[key] = new
                    came_from[key] = last

    def total(last: int) -> float:
        return best[(full, last)] + (km[last][end] if end is not None else 0.0)

    last = min((s for s in range(n_stops) if (full, s) in best), key=total)
    order, done = [], full
    while True:
        order.append(last)
        prev = came_from.get((done, last))
        done &= ~(1 << last)
        if prev is None:
            break
        last = prev
    return order[::-1]


def _heuristic(n_stops: int, km: Matrix, start: Optional[int], end: Optional[int]) -> List[int]:
    """Nearest allowed stop first, then improve by moving single stops."""
    order: List[int] = []
    here = start
    left = set(range(n_stops))
    while left:
        allowed = [s for s in left if s % 2 == 0 or (s - 1) not in left]
        nxt = min(allowed, key=lambda s: (km[here][s] if here is not None else 0.0, s))
        order.append(nxt)
        left.remove(nxt)
        here = nxt

    improved = True
    while improved:
        improved = False
        current = _route_km(order, km, start, end)
        for i in range(len(order)):
            for j in range(len(order)):
                if i == j:
                    continue
                trial = order[:i] + order[i + 1:]
                trial.insert(j, order[i])
                if _valid(trial) and _route_km(trial, km, start, end) < current - 1e-9:
                    order, current, improved = trial, _route_km(trial, km, start, end), True
    return order


def _describe(order: List[int], stops: List[Dict[str, Any]], km: Matrix, minutes: Matrix,
              start: Optional[int], end: Optional[int], start_pt: Optional[Dict[str, Any]],
              end_pt: Optional[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float, float]:
    """Turn an order of stop numbers into a readable list with leg and running km/minutes."""
    out: List[Dict[str, Any]] = []
    path: List[Tuple[int, Dict[str, Any]]] = []
    if start is not None:
        path.append((start, {"kind": "start", "shipment_id": None, **start_pt}))
    path += [(i, stops[i]) for i in order]
    if end is not None:
        path.append((end, {"kind": "end", "shipment_id": None, **end_pt}))

    total_km = total_min = 0.0
    prev = None
    for seq, (node, stop) in enumerate(path, start=1):
        leg_km = km[prev][node] if prev is not None else 0.0
        leg_min = minutes[prev][node] if prev is not None else 0.0
        total_km += leg_km
        total_min += leg_min
        out.append({
            "seq": seq, "kind": stop["kind"], "shipment_id": stop["shipment_id"],
            "lat": stop["lat"], "lng": stop["lng"], "place": stop.get("place"),
            "leg_km": round(leg_km, 1), "cumulative_km": round(total_km, 1),
            "leg_minutes": round(leg_min, 1), "cumulative_minutes": round(total_min, 1),
        })
        prev = node
    return out, total_km, total_min


def plan_stops(
    shipments: List[Dict[str, Any]],
    km: Matrix,
    minutes: Matrix,
    source: str,
    start: Optional[Dict[str, Any]] = None,
    end: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Order the stops, given a distance matrix whose rows/columns are:
    every stop (pickup, drop, pickup, drop, ...), then the start point (if any), then the end point (if any).
    """
    stops = _stops_for(shipments)
    n = len(stops)
    s_idx = n if start is not None else None
    e_idx = (n + (1 if start is not None else 0)) if end is not None else None

    if n == 0:
        return {"stops": [], "total_km": 0.0, "total_minutes": 0.0, "as_listed_km": 0.0,
                "km_saved": 0.0, "saved_percentage": 0.0, "method": "exact", "distance_source": source}

    exact = len(shipments) <= EXACT_LIMIT
    order = (_exact if exact else _heuristic)(n, km, s_idx, e_idx)
    listed = list(range(0, n, 2)) + list(range(1, n, 2))  # all pickups as given, then all drops
    listed_km = _route_km(listed, km, s_idx, e_idx)

    described, total_km, total_min = _describe(order, stops, km, minutes, s_idx, e_idx, start, end)
    saved = max(0.0, listed_km - total_km)
    return {
        "stops": described,
        "total_km": round(total_km, 1),
        "total_minutes": round(total_min, 1),
        "as_listed_km": round(listed_km, 1),
        "km_saved": round(saved, 1),
        "saved_percentage": round(saved / listed_km * 100.0, 1) if listed_km > 0 else 0.0,
        "method": "exact" if exact else "heuristic",
        "distance_source": source,
    }


def _points(shipments: List[Dict[str, Any]], start: Optional[Dict[str, Any]],
            end: Optional[Dict[str, Any]]) -> List[Tuple[float, float]]:
    pts = [(st["lat"], st["lng"]) for st in _stops_for(shipments)]
    if start is not None:
        pts.append((start["lat"], start["lng"]))
    if end is not None:
        pts.append((end["lat"], end["lng"]))
    return pts


def optimize_stops_offline(shipments: List[Dict[str, Any]], start: Optional[Dict[str, Any]] = None,
                           end: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Best stop order using the offline distance estimate (no internet needed)."""
    km, minutes = estimate_matrix(_points(shipments, start, end))
    return plan_stops(shipments, km, minutes, "estimate", start, end)


async def optimize_stops(shipments: List[Dict[str, Any]], start: Optional[Dict[str, Any]] = None,
                         end: Optional[Dict[str, Any]] = None, use_osrm: bool = True) -> Dict[str, Any]:
    """Best stop order using OSRM road distances, falling back to the offline estimate."""
    if use_osrm and shipments:
        got = await osrm_matrix(_points(shipments, start, end))
        if got is not None:
            return plan_stops(shipments, got[0], got[1], "osrm", start, end)
    return optimize_stops_offline(shipments, start, end)
