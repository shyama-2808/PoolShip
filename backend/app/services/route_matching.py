import math
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

from app.services import compatibility_rules


class RouteMatchingService:
    """
    Corridor & proximity matching service for PoolShip.
    Matches shippers with transporters whose routes align along common highways.
    """

    EARTH_RADIUS_KM = 6371.0
    ROAD_FACTOR = 1.25  # roads are ~25% longer than the straight line between two points

    @classmethod
    def haversine_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great-circle distance between two points on Earth in kilometers."""
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_KM * c

    @classmethod
    def cross_track_distance(
        cls,
        point_lat: float,
        point_lon: float,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
    ) -> float:
        """
        Calculates perpendicular distance (in km) from a point to the great circle path
        connecting route start and end. Used to check if a pickup is along a truck's corridor.
        """
        d13 = cls.haversine_distance(start_lat, start_lon, point_lat, point_lon) / cls.EARTH_RADIUS_KM
        
        # Bearings
        theta13 = math.atan2(
            math.sin(math.radians(point_lon - start_lon)) * math.cos(math.radians(point_lat)),
            math.cos(math.radians(start_lat)) * math.sin(math.radians(point_lat))
            - math.sin(math.radians(start_lat)) * math.cos(math.radians(point_lat)) * math.cos(math.radians(point_lon - start_lon))
        )
        theta12 = math.atan2(
            math.sin(math.radians(end_lon - start_lon)) * math.cos(math.radians(end_lat)),
            math.cos(math.radians(start_lat)) * math.sin(math.radians(end_lat))
            - math.sin(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.cos(math.radians(end_lon - start_lon))
        )
        
        d_xt = math.asin(math.sin(d13) * math.sin(theta13 - theta12))
        return abs(d_xt * cls.EARTH_RADIUS_KM)

    @classmethod
    def is_shipment_on_corridor(
        cls,
        pickup_lat: float,
        pickup_lng: float,
        drop_lat: float,
        drop_lng: float,
        truck_start_lat: float,
        truck_start_lng: float,
        truck_end_lat: float,
        truck_end_lng: float,
        corridor_tolerance_km: float = 25.0
    ) -> bool:
        """Checks if both pickup and drop points are within tolerance distance of the truck corridor."""
        d_pickup = cls.cross_track_distance(
            pickup_lat, pickup_lng, truck_start_lat, truck_start_lng, truck_end_lat, truck_end_lng
        )
        d_drop = cls.cross_track_distance(
            drop_lat, drop_lng, truck_start_lat, truck_start_lng, truck_end_lat, truck_end_lng
        )
        return d_pickup <= corridor_tolerance_km and d_drop <= corridor_tolerance_km

    @classmethod
    async def fetch_osrm_route(cls, coordinates: List[Tuple[float, float]]) -> Optional[Dict[str, Any]]:
        """
        Query OSRM (Open Source Routing Machine) public or self-hosted API.
        coordinates: list of (longitude, latitude) pairs.
        """
        try:
            import httpx
            from app.core.config import settings
            # OSRM wants "lon,lat;lon,lat;..." in the URL
            coord_str = ";".join(f"{lon},{lat}" for lon, lat in coordinates)
            url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{coord_str}?overview=full&geometries=geojson"
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("code") == "Ok" and data.get("routes"):
                        route = data["routes"][0]
                        return {
                            "distance_km": round(route["distance"] / 1000.0, 2),
                            "duration_minutes": round(route["duration"] / 60.0, 1),
                            "geometry": route["geometry"],
                        }
        except Exception:
            pass
        
        # Fallback to Haversine summation if OSRM is unreachable
        return cls.estimate_route(coordinates)

    @classmethod
    def estimate_route(cls, coordinates: List[Tuple[float, float]]) -> Dict[str, Any]:
        """Offline estimate: straight lines between stops x road factor, at 45 km/h."""
        total_dist = 0.0
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i+1]
            total_dist += cls.haversine_distance(lat1, lon1, lat2, lon2)
        
        return {
            "distance_km": round(total_dist * cls.ROAD_FACTOR, 2),
            "duration_minutes": round((total_dist * cls.ROAD_FACTOR) / 45.0 * 60, 1),  # 45 km/h avg truck speed
            "geometry": None,
        }

    @classmethod
    def road_distance_km(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Estimated road distance: straight-line distance x road factor (no internet needed)."""
        return cls.haversine_distance(lat1, lon1, lat2, lon2) * cls.ROAD_FACTOR

    @classmethod
    def find_matching_shipments(
        cls,
        truck: Dict[str, Any],
        shipments: List[Dict[str, Any]],
        corridor_tolerance_km: float = 40.0,
    ) -> Dict[str, Any]:
        """
        Decide which shipments can ride on a truck's route.

        truck: dict with origin_lat, origin_lng, dest_lat, dest_lng
        shipments: dicts with id, origin_lat, origin_lng, dest_lat, dest_lng

        A shipment matches when:
          1. its pickup and drop are both within `corridor_tolerance_km` of the truck's path,
          2. both points lie between the truck's start and end (not past either end), and
          3. it travels the same way as the truck (pickup comes before drop).
        """
        s_lat, s_lng = truck["origin_lat"], truck["origin_lng"]
        e_lat, e_lng = truck["dest_lat"], truck["dest_lng"]
        route_km = cls.haversine_distance(s_lat, s_lng, e_lat, e_lng)

        matched: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for sh in shipments:
            p_lat, p_lng = sh["origin_lat"], sh["origin_lng"]
            d_lat, d_lng = sh["dest_lat"], sh["dest_lng"]

            pickup_off = cls.cross_track_distance(p_lat, p_lng, s_lat, s_lng, e_lat, e_lng)
            drop_off = cls.cross_track_distance(d_lat, d_lng, s_lat, s_lng, e_lat, e_lng)

            reason = None
            if pickup_off > corridor_tolerance_km:
                reason = f"Pickup is {pickup_off:.0f} km away from the truck's route"
            elif drop_off > corridor_tolerance_km:
                reason = f"Drop is {drop_off:.0f} km away from the truck's route"
            else:
                pickup_from_start = cls.haversine_distance(s_lat, s_lng, p_lat, p_lng)
                drop_from_start = cls.haversine_distance(s_lat, s_lng, d_lat, d_lng)
                limit = route_km + corridor_tolerance_km
                beyond_end = (
                    max(pickup_from_start, drop_from_start) > limit
                    or cls.haversine_distance(e_lat, e_lng, p_lat, p_lng) > limit
                    or cls.haversine_distance(e_lat, e_lng, d_lat, d_lng) > limit
                )
                if beyond_end:
                    reason = "Pickup or drop lies outside the truck's start and end points"
                elif pickup_from_start > drop_from_start:
                    reason = "Shipment goes in the opposite direction to the truck"

            if reason:
                rejected.append({"shipment_id": sh["id"], "reason": reason})
            else:
                matched.append({
                    "shipment_id": sh["id"],
                    "pickup_offset_km": round(pickup_off, 1),
                    "drop_offset_km": round(drop_off, 1),
                    "shipment_distance_km": round(
                        cls.road_distance_km(p_lat, p_lng, d_lat, d_lng), 1
                    ),
                })

        return {
            "truck_route_km": round(route_km * cls.ROAD_FACTOR, 1),
            "corridor_tolerance_km": corridor_tolerance_km,
            "matched": matched,
            "rejected": rejected,
        }

    # ------------------------------------------------------------------
    # Shipment-to-shipment pooling (no truck needed)
    # ------------------------------------------------------------------
    @classmethod
    def along_track_distance(
        cls,
        point_lat: float,
        point_lon: float,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float,
    ) -> float:
        """
        How far along the path (start -> end) a point sits, in km.
        Imagine dropping the point straight onto the path: this is the distance
        from `start` to where it lands. Negative means it lands behind `start`.
        """
        d13 = cls.haversine_distance(start_lat, start_lon, point_lat, point_lon) / cls.EARTH_RADIUS_KM
        d_xt = cls.cross_track_distance(
            point_lat, point_lon, start_lat, start_lon, end_lat, end_lon
        ) / cls.EARTH_RADIUS_KM
        cos_ratio = math.cos(d13) / max(math.cos(d_xt), 1e-12)
        d_at = math.acos(max(-1.0, min(1.0, cos_ratio))) * cls.EARTH_RADIUS_KM

        # Is the point ahead of start (same side as end) or behind it?
        bearing_to_point = cls._bearing(start_lat, start_lon, point_lat, point_lon)
        bearing_to_end = cls._bearing(start_lat, start_lon, end_lat, end_lon)
        return d_at if math.cos(bearing_to_point - bearing_to_end) >= 0 else -d_at

    @staticmethod
    def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compass direction (radians) from point 1 to point 2."""
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dl = math.radians(lon2 - lon1)
        return math.atan2(
            math.sin(dl) * math.cos(p2),
            math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl),
        )

    @staticmethod
    def _to_datetime(value: Any) -> Optional[datetime]:
        """Accepts a datetime, an ISO text like '2026-12-02T09:00:00+05:30', or None."""
        if value is None or isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    @classmethod
    def _window(cls, shipment: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime]]:
        return (
            cls._to_datetime(shipment.get("delivery_window_start")),
            cls._to_datetime(shipment.get("delivery_window_end")),
        )

    @staticmethod
    def _overlap(
        a: Tuple[Optional[datetime], Optional[datetime]],
        b: Tuple[Optional[datetime], Optional[datetime]],
    ) -> Optional[Tuple[Optional[datetime], Optional[datetime]]]:
        """
        The time both windows share, or None if they don't share any.
        A missing start or end means "no limit" on that side.
        """
        starts = [t for t in (a[0], b[0]) if t is not None]
        ends = [t for t in (a[1], b[1]) if t is not None]
        start = max(starts) if starts else None
        end = min(ends) if ends else None
        if start is not None and end is not None and start >= end:
            return None
        return (start, end)

    @classmethod
    def route_fit(
        cls,
        shipment: Dict[str, Any],
        path_start: Tuple[float, float],
        path_end: Tuple[float, float],
        tolerance_km: float,
    ) -> Dict[str, Any]:
        """
        Does this shipment follow the common path (path_start -> path_end)?
        Returns {"fits": bool, "reason": str | None, "pickup_offset_km", "drop_offset_km"}.

        It fits when:
          1. pickup and drop are both within `tolerance_km` of the path,
          2. neither lies past the ends of the path (more than `tolerance_km` before
             the start or after the end), and
          3. it travels the same way as the path (pickup comes before drop).
        """
        s_lat, s_lng = path_start
        e_lat, e_lng = path_end
        p_lat, p_lng = shipment["origin_lat"], shipment["origin_lng"]
        d_lat, d_lng = shipment["dest_lat"], shipment["dest_lng"]
        path_km = cls.haversine_distance(s_lat, s_lng, e_lat, e_lng)

        pickup_off = cls.cross_track_distance(p_lat, p_lng, s_lat, s_lng, e_lat, e_lng)
        drop_off = cls.cross_track_distance(d_lat, d_lng, s_lat, s_lng, e_lat, e_lng)
        pickup_at = cls.along_track_distance(p_lat, p_lng, s_lat, s_lng, e_lat, e_lng)
        drop_at = cls.along_track_distance(d_lat, d_lng, s_lat, s_lng, e_lat, e_lng)

        reason = None
        if pickup_off > tolerance_km:
            reason = f"pickup is {pickup_off:.0f} km off the common path"
        elif drop_off > tolerance_km:
            reason = f"drop is {drop_off:.0f} km off the common path"
        elif min(pickup_at, drop_at) < -tolerance_km or max(pickup_at, drop_at) > path_km + tolerance_km:
            reason = "pickup or drop lies beyond the ends of the common path"
        elif pickup_at >= drop_at:
            reason = "it travels in the opposite direction"

        return {
            "fits": reason is None,
            "reason": reason,
            "pickup_offset_km": round(pickup_off, 1),
            "drop_offset_km": round(drop_off, 1),
        }

    @classmethod
    def find_candidate_pools(
        cls,
        shipments: List[Dict[str, Any]],
        corridor_tolerance_km: float = 40.0,
    ) -> Dict[str, Any]:
        """
        Group open shipments into candidate pools, without needing a truck.

        Two shipments have a "similar route" when:
          * ROUTE: both pickup and drop of one lie close to (within
            `corridor_tolerance_km` of) the other's path, in the same direction, and
          * TIME: their delivery windows overlap, and
          * GOODS: they may share a truck (compatibility_rules: e.g. food never
            rides with chemicals).

        How it groups (greedy, simple and predictable):
          1. Sort shipments longest trip first. The longest trip in a group becomes
             its "common path" (the road everyone else rides along).
          2. Take the first shipment not yet in a pool and start a new pool with it.
          3. Walk through the rest and add each one that follows the common path and
             whose delivery window overlaps the pool's shared window. The shared window
             shrinks to the time every member can accept.
          4. A pool needs at least 2 shipments. Shipments left alone are listed as
             unmatched, with the reason.

        Each shipment dict needs: id, origin_lat, origin_lng, dest_lat, dest_lng.
        Optional: delivery_window_start/end (datetime or ISO text), weight_kg, volume_cbm.
        Missing windows count as "any time".
        """
        def trip_km(sh: Dict[str, Any]) -> float:
            return cls.haversine_distance(sh["origin_lat"], sh["origin_lng"], sh["dest_lat"], sh["dest_lng"])

        ordered = sorted(shipments, key=lambda sh: (-trip_km(sh), sh["id"]))
        assigned = set()
        groups: List[Dict[str, Any]] = []

        for anchor in ordered:
            if anchor["id"] in assigned:
                continue
            assigned.add(anchor["id"])
            start = (anchor["origin_lat"], anchor["origin_lng"])
            end = (anchor["dest_lat"], anchor["dest_lng"])
            window = cls._window(anchor)
            members = [(anchor, {"pickup_offset_km": 0.0, "drop_offset_km": 0.0})]

            for other in ordered:
                if other["id"] in assigned:
                    continue
                fit = cls.route_fit(other, start, end, corridor_tolerance_km)
                if not fit["fits"]:
                    continue
                shared = cls._overlap(window, cls._window(other))
                if shared is None:
                    continue
                if compatibility_rules.first_block([m for m, _ in members], other):
                    continue
                if cls._same_series(members, other):
                    continue
                window = shared
                assigned.add(other["id"])
                members.append((other, fit))

            # Anchor first, then the riders in shipment-id order (easier to read)
            members = members[:1] + sorted(members[1:], key=lambda mf: mf[0]["id"])
            groups.append({"anchor": anchor, "window": window, "members": members})

        # Number pools in the order of their lowest shipment id
        groups.sort(key=lambda g: min(m["id"] for m, _ in g["members"]))
        pool_of = {m["id"]: [x for x, _ in g["members"]] for g in groups for m, _ in g["members"]}

        pools: List[Dict[str, Any]] = []
        unmatched: List[Dict[str, Any]] = []
        for g in groups:
            if len(g["members"]) < 2:
                unmatched.append({
                    "shipment_id": g["anchor"]["id"],
                    "reason": cls._why_alone(g["anchor"], shipments, corridor_tolerance_km, pool_of),
                })
                continue
            anchor, (w_start, w_end) = g["anchor"], g["window"]
            pools.append({
                "pool_id": len(pools) + 1,
                "shipment_ids": [m["id"] for m, _ in g["members"]],
                "common_path": {
                    "from": {"lat": anchor["origin_lat"], "lng": anchor["origin_lng"],
                             "place": anchor.get("origin_address")},
                    "to": {"lat": anchor["dest_lat"], "lng": anchor["dest_lng"],
                           "place": anchor.get("destination_address")},
                    "estimated_road_km": round(trip_km(anchor) * cls.ROAD_FACTOR, 1),
                    "based_on_shipment_id": anchor["id"],
                },
                "shared_delivery_window": {
                    "start": w_start.isoformat() if w_start else None,
                    "end": w_end.isoformat() if w_end else None,
                },
                "total_weight_kg": round(sum(m.get("weight_kg") or 0 for m, _ in g["members"]), 1),
                "total_volume_cbm": round(sum(m.get("volume_cbm") or 0 for m, _ in g["members"]), 3),
                "members": [
                    {
                        "shipment_id": m["id"],
                        "pickup_offset_km": fit["pickup_offset_km"],
                        "drop_offset_km": fit["drop_offset_km"],
                        "shipment_distance_km": round(trip_km(m) * cls.ROAD_FACTOR, 1),
                    }
                    for m, fit in g["members"]
                ],
            })

        return {
            "corridor_tolerance_km": corridor_tolerance_km,
            "pools": pools,
            "unmatched": sorted(unmatched, key=lambda u: u["shipment_id"]),
        }

    @staticmethod
    def _same_series(members: List[Tuple[Dict[str, Any], Dict[str, Any]]], other: Dict[str, Any]) -> bool:
        """Two repeats of the same recurring shipment (Task 11) are separate loads, so never one pool."""
        rid = other.get("recurring_id")
        return rid is not None and any(m.get("recurring_id") == rid for m, _ in members)

    @classmethod
    def _why_alone(
        cls,
        shipment: Dict[str, Any],
        all_shipments: List[Dict[str, Any]],
        tol: float,
        pool_of: Optional[Dict[Any, List[Dict[str, Any]]]] = None,
    ) -> str:
        """Explain in plain words why a shipment ended up without a pool."""
        pool_of = pool_of or {}
        same_route_other_time = []
        for other in all_shipments:
            if other["id"] == shipment["id"]:
                continue
            # Similar route either way round: shipment on other's path, or other on shipment's path
            on_other = cls.route_fit(shipment, (other["origin_lat"], other["origin_lng"]),
                                     (other["dest_lat"], other["dest_lng"]), tol)["fits"]
            on_mine = cls.route_fit(other, (shipment["origin_lat"], shipment["origin_lng"]),
                                    (shipment["dest_lat"], shipment["dest_lng"]), tol)["fits"]
            if on_other or on_mine:
                if shipment.get("recurring_id") is not None and other.get("recurring_id") == shipment["recurring_id"]:
                    continue  # another repeat of the same booking doesn't count as a partner
                if cls._overlap(cls._window(shipment), cls._window(other)) is None:
                    same_route_other_time.append(other["id"])
                    continue
                clash = compatibility_rules.first_block(pool_of.get(other["id"], [other]), shipment)
                if clash:
                    return f"shares a route with shipment {other['id']}, but can't join its pool. {clash}"
                rid = shipment.get("recurring_id")
                twin = next((m for m in pool_of.get(other["id"], []) if rid is not None
                             and m.get("recurring_id") == rid), None)
                if twin is not None:
                    return (f"shares a route with shipment {other['id']}, but that pool already carries "
                            f"another repeat of the same booking (shipment {twin['id']})")
                return (f"shares a route with shipment {other['id']}, but that shipment "
                        "was already placed in a pool whose delivery window doesn't fit")
        if same_route_other_time:
            ids = ", ".join(str(i) for i in same_route_other_time)
            return f"shares a route with shipment(s) {ids}, but their delivery windows don't overlap"
        return "no other open shipment travels a similar route"
