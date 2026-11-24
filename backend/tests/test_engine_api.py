"""Checks every /engine endpoint answers correctly with the shared sample data (no database needed)."""
import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.cost_splitter import CostSplitter
from app.services.route_matching import RouteMatchingService

API = "/api/v1/engine"
client = TestClient(app)  # not used as a context manager, so startup (DB table creation) is skipped


def example(path):
    """The ready-made Swagger example for an endpoint."""
    spec = client.get("/api/v1/openapi.json").json()
    content = spec["paths"][f"{API}{path}"]["post"]["requestBody"]["content"]["application/json"]
    return content["examples"]["sample"]["value"]


class TestEngineApi(unittest.TestCase):
    def test_sample_data_has_20_shipments_and_5_trucks(self):
        data = client.get(f"{API}/sample-data").json()
        self.assertEqual(len(data["shipments"]), 20)
        self.assertEqual(len(data["trucks"]), 5)

    def test_every_post_endpoint_accepts_its_example(self):
        for path in ["/compatibility", "/optimize-load", "/cost-split", "/carbon", "/route/distance",
                     "/route/corridor-check", "/route/match", "/route/pools", "/plan-pool"]:
            with self.subTest(path=path):
                res = client.post(f"{API}{path}", json=example(path))
                self.assertEqual(res.status_code, 200, res.text)

    def test_road_route_offline_estimate(self):
        body = example("/route/road-route") | {"use_osrm": False}
        res = client.post(f"{API}/route/road-route", json=body).json()
        self.assertEqual(res["source"], "estimate")
        self.assertGreater(res["distance_km"], 300)

    def test_demo_truck_1(self):
        res = client.get(f"{API}/demo/1").json()
        self.assertEqual([m["shipment_id"] for m in res["route"]["matched"]], [1, 2, 3, 4, 5, 6])
        left_out = {i["id"] for i in res["load"]["unpacked_items"]}
        self.assertIn(3, left_out)  # mangoes can't ride with paint thinner
        total = sum(s["allocated_cost"] for s in res["cost_split"]["shares"])
        self.assertAlmostEqual(total, res["total_trip_cost"], delta=1)

    def test_demo_all_trucks_and_unknown_truck(self):
        for truck_id in range(1, 6):
            self.assertEqual(client.get(f"{API}/demo/{truck_id}").status_code, 200)
        self.assertEqual(client.get(f"{API}/demo/99").status_code, 404)

    def test_shipment_20_matches_no_truck(self):
        for truck_id in range(1, 6):
            res = client.get(f"{API}/demo/{truck_id}").json()
            self.assertNotIn(20, [m["shipment_id"] for m in res["route"]["matched"]])


class TestEngineFixes(unittest.TestCase):
    def test_volume_split(self):
        res = CostSplitter.calculate_split(
            1000, [{"id": 1, "weight_kg": 1, "volume_cbm": 3}, {"id": 2, "weight_kg": 1, "volume_cbm": 1}], "volume"
        )
        self.assertEqual([r["allocated_cost"] for r in res], [750.0, 250.0])

    def test_unknown_split_method(self):
        with self.assertRaises(ValueError):
            CostSplitter.calculate_split(1000, [{"id": 1, "weight_kg": 1}], "magic")

    def test_wrong_direction_is_rejected(self):
        truck = {"origin_lat": 12.9716, "origin_lng": 77.5946, "dest_lat": 13.0827, "dest_lng": 80.2707}
        chennai_to_blr = {"id": 1, "origin_lat": 13.0827, "origin_lng": 80.2707,
                          "dest_lat": 12.9716, "dest_lng": 77.5946}
        res = RouteMatchingService.find_matching_shipments(truck, [chennai_to_blr])
        self.assertIn("opposite direction", res["rejected"][0]["reason"])

    def test_osrm_url_is_built(self):
        """fetch_osrm_route used to crash on an undefined coord_str and always fall back."""
        seen = {}

        class FakeRes:
            status_code = 200
            def json(self):
                return {"code": "Ok", "routes": [{"distance": 350000, "duration": 18000, "geometry": {}}]}

        class FakeClient:
            def __init__(self, *a, **k): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *a): pass
            async def get(self, url):
                seen["url"] = url
                return FakeRes()

        with patch("httpx.AsyncClient", FakeClient):
            res = asyncio.run(RouteMatchingService.fetch_osrm_route([(77.59, 12.97), (80.27, 13.08)]))
        self.assertIn("/77.59,12.97;80.27,13.08?", seen["url"])
        self.assertEqual(res["distance_km"], 350.0)


class TestFindPools(unittest.TestCase):
    """Task 2: group shipments into pools by similar route + overlapping delivery windows."""

    BLR, HOSUR, CHENNAI = (12.9716, 77.5946), (12.7409, 77.8253), (13.0827, 80.2707)

    def ship(self, id, start, end, window=("2026-12-02T09:00:00+05:30", "2026-12-03T18:00:00+05:30")):
        return {"id": id, "origin_lat": start[0], "origin_lng": start[1], "dest_lat": end[0],
                "dest_lng": end[1], "delivery_window_start": window[0], "delivery_window_end": window[1]}

    def test_sample_shipments_come_back_grouped(self):
        res = client.get(f"{API}/demo-pools").json()
        groups = sorted(sorted(p["shipment_ids"]) for p in res["pools"])
        self.assertEqual(groups, [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10], [11, 12, 13, 14],
                                  [15, 16, 17], [18, 19]])
        self.assertEqual([u["shipment_id"] for u in res["unmatched"]], [20])

    def test_every_shipment_appears_exactly_once(self):
        res = client.get(f"{API}/demo-pools").json()
        ids = [i for p in res["pools"] for i in p["shipment_ids"]] + [u["shipment_id"] for u in res["unmatched"]]
        self.assertEqual(sorted(ids), list(range(1, 21)))

    def test_shared_window_is_what_everyone_accepts(self):
        res = client.get(f"{API}/demo-pools").json()
        blr_chennai = next(p for p in res["pools"] if 1 in p["shipment_ids"])
        # mangoes (shipment 3) must arrive by 2 Dec 18:00; the others from 2 Dec 09:00
        self.assertEqual(blr_chennai["shared_delivery_window"],
                         {"start": "2026-12-02T09:00:00+05:30", "end": "2026-12-02T18:00:00+05:30"})

    def test_same_route_but_no_common_time_is_unmatched(self):
        a = self.ship(1, self.BLR, self.CHENNAI, ("2026-12-01T09:00:00+05:30", "2026-12-01T18:00:00+05:30"))
        b = self.ship(2, self.HOSUR, self.CHENNAI, ("2026-12-05T09:00:00+05:30", "2026-12-05T18:00:00+05:30"))
        res = RouteMatchingService.find_candidate_pools([a, b])
        self.assertEqual(res["pools"], [])
        self.assertIn("delivery windows don't overlap", res["unmatched"][0]["reason"])

    def test_opposite_direction_is_not_pooled(self):
        res = RouteMatchingService.find_candidate_pools(
            [self.ship(1, self.BLR, self.CHENNAI), self.ship(2, self.CHENNAI, self.HOSUR)])
        self.assertEqual(res["pools"], [])
        self.assertEqual(len(res["unmatched"]), 2)

    def test_missing_windows_mean_any_time(self):
        a, b = self.ship(1, self.BLR, self.CHENNAI), self.ship(2, self.HOSUR, self.CHENNAI)
        for s in (a, b):
            s.pop("delivery_window_start"), s.pop("delivery_window_end")
        res = RouteMatchingService.find_candidate_pools([a, b])
        self.assertEqual(res["pools"][0]["shipment_ids"], [1, 2])

    def test_tighter_tolerance_drops_far_pickups(self):
        # Hosur pickup is ~27 km off the Bengaluru-Chennai path
        res = RouteMatchingService.find_candidate_pools(
            [self.ship(1, self.BLR, self.CHENNAI), self.ship(2, self.HOSUR, self.CHENNAI)],
            corridor_tolerance_km=10)
        self.assertEqual(res["pools"], [])


if __name__ == "__main__":
    unittest.main()
