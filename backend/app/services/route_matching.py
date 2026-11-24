import math
from typing import List, Dict, Any, Tuple, Optional


class RouteMatchingService:
    """
    Corridor & proximity matching service for PoolShip.
    Matches shippers with transporters whose routes align along common highways.
    """

    EARTH_RADIUS_KM = 6371.0

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
            coord_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
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
        total_dist = 0.0
        for i in range(len(coordinates) - 1):
            lon1, lat1 = coordinates[i]
            lon2, lat2 = coordinates[i+1]
            total_dist += cls.haversine_distance(lat1, lon1, lat2, lon2)
        
        return {
            "distance_km": round(total_dist * 1.25, 2),  # 1.25 road curvature factor
            "duration_minutes": round((total_dist * 1.25) / 45.0 * 60, 1),  # 45 km/h avg truck speed
            "geometry": None,
        }
