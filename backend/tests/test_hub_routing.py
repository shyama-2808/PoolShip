"""
Task 12: hub support. When no single truck covers a route, change trucks at a hub.
"""
import unittest

from fastapi.testclient import TestClient

from app.core.sample_data import load_sample_data
from app.main import app
from app.services import hub_routing

API = "/api/v1/engine"
client = TestClient(app)
DATA = load_sample_data()
SHIP = {s["id"]: s for s in DATA["shipments"]}
TRUCKS, HUBS = DATA["trucks"], DATA["hubs"]


class TestHubRoute(unittest.TestCase):
    def setUp(self):
        self.r = hub_routing.plan_route(SHIP[20], TRUCKS, HUBS)  # jute bags, Bengaluru to Kolkata

    def test_bengaluru_to_kolkata_goes_through_hyderabad(self):
        self.assertEqual(self.r["mode"], "hub")
        self.assertEqual(self.r["direct_trucks"], [])
        best = self.r["best"]
        self.assertEqual(best["hub"]["name"], "Hyderabad hub")
        self.assertEqual([leg["truck_id"] for leg in best["legs"]], [4, 6])

    def test_times_and_waiting(self):
        best = self.r["best"]
        self.assertEqual(best["legs"][0]["arrives_at"], "2026-12-02T19:53:00+05:30")  # 625 km at 45 km/h
        self.assertEqual(best["ready_at_hub"], "2026-12-02T22:53:00+05:30")           # + 3 h transfer
        self.assertEqual(best["legs"][1]["departs_at"], "2026-12-05T06:00:00+05:30")   # truck 6 is free then
        self.assertEqual(best["wait_at_hub_hours"], 58.1)
        self.assertEqual(best["delivered_at"], "2026-12-06T14:50:00+05:30")
        self.assertEqual(best["spare_hours"], 51.2)

    def test_distance_and_cost(self):
        best = self.r["best"]
        self.assertEqual(self.r["direct_km"], 1950.9)
        self.assertEqual(best["total_km"], 2102.3)
        self.assertEqual(best["extra_pct"], 7.8)
        self.assertEqual([leg["cost"] for leg in best["legs"]], [1145.82, 3693.38])
        self.assertEqual(best["handling_fee"], 500.0)  # 500 kg x Rs 1
        self.assertEqual(best["total_cost"], 5339.2)

    def test_other_hubs_say_why_not(self):
        why = {h["name"]: h["reason"] for h in self.r["rejected_hubs"]}
        self.assertIn("after the deadline", why["Chennai hub"])          # trucks 1 + 7 arrive 8 Dec 19:44
        self.assertIn("2026-12-08T19:44", why["Chennai hub"])
        self.assertIn("no truck with room goes from Bengaluru", why["Nagpur hub"])
        self.assertIn("adds 48%", why["Pune hub"])

    def test_direct_truck_means_no_hub(self):
        r = hub_routing.plan_route(SHIP[2], TRUCKS, HUBS)  # Hosur to Chennai on truck 1
        self.assertEqual(r["mode"], "direct")
        self.assertEqual(r["direct_trucks"][0]["truck_id"], 1)
        self.assertIsNone(r["best"])

    def test_tighter_deadline_leaves_no_way(self):
        s = SHIP[20] | {"delivery_window_end": "2026-12-06T12:00:00+05:30"}
        r = hub_routing.plan_route(s, TRUCKS, HUBS)
        self.assertEqual(r["mode"], "none")
        why = {h["name"]: h["reason"] for h in r["rejected_hubs"]}
        self.assertIn("after the deadline", why["Hyderabad hub"])

    def test_full_leg_truck_is_skipped(self):
        trucks = [t | {"used_weight_kg": 14800} if t["id"] == 4 else t for t in TRUCKS]
        r = hub_routing.plan_route(SHIP[20], trucks, HUBS)
        self.assertEqual(r["mode"], "none")  # Hyderabad has no first leg now; Chennai is late

    def test_detour_limit(self):
        r = hub_routing.plan_route(SHIP[20], TRUCKS, HUBS, max_detour_pct=5)
        self.assertEqual(r["mode"], "none")
        self.assertTrue(any("limit 5%" in h["reason"] for h in r["rejected_hubs"]))

    def test_no_times_means_no_deadline_check(self):
        s = {k: v for k, v in SHIP[20].items() if k != "delivery_window_end"}
        trucks = [{k: v for k, v in t.items() if k != "available_date"} for t in TRUCKS]
        r = hub_routing.plan_route(s, trucks, HUBS)
        self.assertEqual(r["mode"], "hub")
        self.assertEqual(r["best"]["hub"]["name"], "Hyderabad hub")  # cheaper than Chennai
        self.assertIsNone(r["best"]["delivered_at"])
        self.assertEqual(len(r["options"]), 2)


class TestHubEndpoints(unittest.TestCase):
    def test_example(self):
        spec = client.get("/api/v1/openapi.json").json()
        ex = spec["paths"][f"{API}/hub-route"]["post"]["requestBody"]["content"]["application/json"][
            "examples"]["sample"]["value"]
        res = client.post(f"{API}/hub-route", json=ex)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["mode"], "hub")
        self.assertEqual(body["best"]["legs"][0]["from"], "Bengaluru")
        self.assertEqual(body["best"]["total_cost"], 5339.2)

    def test_demo_hub_counts_what_trucks_already_carry(self):
        body = client.get(f"{API}/demo-hub/20").json()
        self.assertEqual(body["best"]["hub"]["name"], "Hyderabad hub")
        full = client.get(f"{API}/demo-hub/1").json()  # truck 1's own pool leaves only 200 kg spare
        self.assertEqual(full["mode"], "none")
        self.assertIn("truck 1 covers the trip but has only 200 kg spare", full["summary"])
        self.assertEqual(client.get(f"{API}/demo-hub/2").json()["mode"], "direct")
        self.assertEqual(client.get(f"{API}/demo-hub/99").status_code, 404)

    def test_hubs_list(self):
        self.assertEqual([h["city"] for h in client.get(f"{API}/hubs").json()],
                         ["Hyderabad", "Chennai", "Vijayawada", "Nagpur", "Pune"])


if __name__ == "__main__":
    unittest.main()
