"""
Task 6: multi-stop route. Order a pool's pickups and drops (pickup before its drop)
with the fewest km, using OSRM road distances or the offline estimate.
"""
import itertools
import random
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.sample_data import load_sample_data
from app.main import app
from app.services import route_optimizer as ro

API = "/api/v1/engine"
client = TestClient(app)

DATA = load_sample_data()
SHIP = {s["id"]: s for s in DATA["shipments"]}
T1 = DATA["trucks"][0]
DEPOT = {"lat": T1["origin_lat"], "lng": T1["origin_lng"], "place": "Bengaluru"}


def pickup_before_drop(stops):
    seen = set()
    for s in stops:
        if s["kind"] == "pickup":
            seen.add(s["shipment_id"])
        if s["kind"] == "drop" and s["shipment_id"] not in seen:
            return False
    return True


class TestStopOrder(unittest.TestCase):
    def test_sample_pool_is_shorter_than_as_listed(self):
        r = ro.optimize_stops_offline([SHIP[i] for i in (1, 2, 3, 5, 6)], DEPOT)
        self.assertEqual(r["method"], "exact")
        self.assertEqual(r["distance_source"], "estimate")
        self.assertEqual(r["total_km"], 409.9)
        self.assertEqual(r["as_listed_km"], 871.2)
        self.assertEqual(r["km_saved"], 461.3)
        self.assertLess(r["total_km"], r["as_listed_km"])
        self.assertTrue(pickup_before_drop(r["stops"]))
        places = [s["place"] for s in r["stops"]]
        self.assertEqual(places[:6], ["Bengaluru", "Bengaluru", "Bengaluru", "Hosur", "Kolar", "Vellore"])
        self.assertEqual(r["stops"][-1]["cumulative_km"], r["total_km"])
        self.assertEqual(len(r["stops"]), 11)  # start + 5 pickups + 5 drops

    def test_exact_matches_trying_every_order(self):
        rng = random.Random(3)
        for _ in range(30):
            n = rng.randint(1, 4)
            ships = [{"id": i, "origin_lat": rng.uniform(12, 14), "origin_lng": rng.uniform(77, 80),
                      "dest_lat": rng.uniform(12, 14), "dest_lng": rng.uniform(77, 80)} for i in range(n)]
            km, _ = ro.estimate_matrix(ro._points(ships, DEPOT, None))
            best = min(ro._route_km(list(p), km, 2 * n, None)
                       for p in itertools.permutations(range(2 * n)) if ro._valid(list(p)))
            self.assertAlmostEqual(ro.optimize_stops_offline(ships, DEPOT)["total_km"], round(best, 1), 1)

    def test_many_shipments_use_the_heuristic_and_stay_valid(self):
        r = ro.optimize_stops_offline(list(SHIP.values()), DEPOT)
        self.assertEqual(r["method"], "heuristic")
        self.assertTrue(pickup_before_drop(r["stops"]))
        self.assertLess(r["total_km"], r["as_listed_km"])
        self.assertEqual(len(r["stops"]), 1 + 2 * len(SHIP))

    def test_end_point_is_last(self):
        end = {"lat": 12.9716, "lng": 77.5946, "place": "back to Bengaluru"}
        r = ro.optimize_stops_offline([SHIP[1], SHIP[5]], DEPOT, end)
        self.assertEqual(r["stops"][-1]["kind"], "end")
        self.assertTrue(pickup_before_drop(r["stops"]))

    def test_uses_osrm_when_it_answers_and_falls_back_when_it_does_not(self):
        import asyncio
        ships = [SHIP[1], SHIP[2]]
        n = len(ro._points(ships, DEPOT, None))
        fake = ([[10.0] * n for _ in range(n)], [[15.0] * n for _ in range(n)])

        async def ok(points):
            return fake

        async def down(points):
            return None

        with patch.object(ro, "osrm_matrix", ok):
            r = asyncio.run(ro.optimize_stops(ships, DEPOT))
        self.assertEqual(r["distance_source"], "osrm")
        self.assertEqual(r["total_km"], 40.0)  # 4 legs of 10 km
        with patch.object(ro, "osrm_matrix", down):
            r = asyncio.run(ro.optimize_stops(ships, DEPOT))
        self.assertEqual(r["distance_source"], "estimate")


class TestStopEndpoints(unittest.TestCase):
    def test_example_returns_order_and_total_km(self):
        spec = client.get("/api/v1/openapi.json").json()
        ex = spec["paths"][f"{API}/route/optimize-stops"]["post"]["requestBody"]["content"][
            "application/json"]["examples"]["sample"]["value"]
        res = client.post(f"{API}/route/optimize-stops", json=ex)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["total_km"], 409.9)
        self.assertLess(body["total_km"], body["as_listed_km"])

    def test_demo_stops_for_every_sample_truck(self):
        for truck_id in range(1, 6):
            res = client.get(f"{API}/demo-stops/{truck_id}")
            self.assertEqual(res.status_code, 200, res.text)
            body = res.json()
            self.assertTrue(pickup_before_drop(body["stops"]))
            self.assertLessEqual(body["total_km"], body["as_listed_km"])

    def test_plan_pool_includes_stop_plan(self):
        res = client.get(f"{API}/demo/1").json()
        self.assertIsNotNone(res["stop_plan"])
        packed = {i["id"] for i in res["load"]["packed_items"]}
        self.assertEqual({s["shipment_id"] for s in res["stop_plan"]["stops"] if s["kind"] == "drop"}, packed)

    def test_drop_needs_coordinates(self):
        res = client.post(f"{API}/route/optimize-stops", json={"shipments": [{"id": 1}]})
        self.assertEqual(res.status_code, 422)


if __name__ == "__main__":
    unittest.main()
