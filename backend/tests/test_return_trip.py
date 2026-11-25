"""
Task 8: empty-return-trip matching. Find open shipments along a truck's way home.
"""
import unittest

from fastapi.testclient import TestClient

from app.core.sample_data import load_sample_data
from app.main import app
from app.services.return_trip import match_return_loads, return_route

API = "/api/v1/engine"
client = TestClient(app)
DATA = load_sample_data()
T1, T2 = DATA["trucks"][0], DATA["trucks"][1]


class TestReturnTrip(unittest.TestCase):
    def test_truck_1_gets_matched_loads_on_the_way_home(self):
        r = match_return_loads(T1, DATA["shipments"])
        self.assertEqual([m["shipment_id"] for m in r["matched"]], [21, 22, 23])
        self.assertFalse(r["is_empty_return"])
        self.assertEqual(r["load"]["total_weight_kg"], 2050.0)
        self.assertEqual(r["load"]["overall_utilization_pct"], 82.0)
        self.assertEqual(r["return_trip_earnings"], 10155.6)  # 362.7 km x Rs 28 (rounded)
        self.assertAlmostEqual(sum(m["pays"] for m in r["matched"]), r["return_trip_earnings"], places=2)

    def test_return_route_is_reversed_and_timed(self):
        rr = return_route(T1)
        self.assertEqual(rr["from"]["place"], "Chennai")
        self.assertEqual(rr["to"]["place"], "Bengaluru")
        # leaves 1 Dec 06:00, 362.7 km at 45 km/h = 8 h 04 min, plus 2 h unloading
        self.assertEqual(rr["departs_at"], "2026-12-01T16:04:00+05:30")
        self.assertEqual(rr["arrives_home_at"], "2026-12-02T00:08:00+05:30")

    def test_late_and_off_route_shipments_say_why(self):
        r = match_return_loads(T1, DATA["shipments"])
        why = {x["shipment_id"]: x["reason"] for x in r["rejected"]}
        self.assertIn("after its delivery window closes", why[24])   # due by 1 Dec 18:00
        self.assertIn("opposite direction", why[1])                   # outbound shipment
        self.assertIn("away from the truck's route", why[25])         # Pune to Mumbai

    def test_no_time_check_without_available_date(self):
        truck = {k: v for k, v in T1.items() if k != "available_date"}
        r = match_return_loads(truck, DATA["shipments"])
        self.assertIn(24, [m["shipment_id"] for m in r["matched"]])
        self.assertIsNone(r["return_route"]["departs_at"])

    def test_full_truck_leaves_the_rest_with_a_reason(self):
        small = T1 | {"max_weight_kg": 1000}
        r = match_return_loads(small, DATA["shipments"])
        self.assertLessEqual(r["load"]["total_weight_kg"], 1000)
        self.assertTrue(any("weight" in x["reason"] for x in r["rejected"]))

    def test_truck_2_picks_up_pune_to_mumbai(self):
        r = match_return_loads(T2, DATA["shipments"])
        self.assertEqual([m["shipment_id"] for m in r["matched"]], [25])

    def test_truck_with_nothing_on_the_way_returns_empty(self):
        r = match_return_loads(DATA["trucks"][2], DATA["shipments"])  # Delhi to Jaipur
        self.assertTrue(r["is_empty_return"])
        self.assertEqual(r["return_trip_earnings"], 0.0)


class TestReturnTripEndpoints(unittest.TestCase):
    def test_example(self):
        spec = client.get("/api/v1/openapi.json").json()
        ex = spec["paths"][f"{API}/return-trip"]["post"]["requestBody"]["content"][
            "application/json"]["examples"]["sample"]["value"]
        res = client.post(f"{API}/return-trip", json=ex)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual([m["shipment_id"] for m in body["matched"]], [21, 22, 23])
        self.assertEqual(body["return_route"]["from"]["place"], "Chennai")
        self.assertEqual(body["stop_plan"]["stops"][-1]["kind"], "end")

    def test_demo_return(self):
        self.assertEqual(client.get(f"{API}/demo-return/1").json()["load"]["total_weight_kg"], 2050.0)
        self.assertEqual(client.get(f"{API}/demo-return/99").status_code, 404)


if __name__ == "__main__":
    unittest.main()
