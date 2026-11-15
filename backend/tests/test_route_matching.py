import unittest
from app.services.route_matching import RouteMatchingService


class TestRouteMatching(unittest.TestCase):
    def test_haversine_bangalore_to_chennai(self):
        # Bangalore (~12.9716, 77.5946) to Chennai (~13.0827, 80.2707) is ~290 km direct
        dist = RouteMatchingService.haversine_distance(12.9716, 77.5946, 13.0827, 80.2707)
        self.assertAlmostEqual(dist, 290.0, delta=20.0)

    def test_corridor_tolerance(self):
        # Route: Bangalore to Chennai
        # Point near route: Hosur (~12.7409, 77.8253) -> close to corridor
        is_on_route = RouteMatchingService.is_shipment_on_corridor(
            pickup_lat=12.7409,
            pickup_lng=77.8253,
            drop_lat=13.0827,
            drop_lng=80.2707,
            truck_start_lat=12.9716,
            truck_start_lng=77.5946,
            truck_end_lat=13.0827,
            truck_end_lng=80.2707,
            corridor_tolerance_km=40.0
        )
        self.assertTrue(is_on_route)


if __name__ == "__main__":
    unittest.main()
