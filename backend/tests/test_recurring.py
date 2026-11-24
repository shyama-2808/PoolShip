"""
Task 11: recurring shipments. Daily and weekly repeats become shipments and enter pools.
"""
import asyncio
import unittest
from datetime import date, datetime

from fastapi.testclient import TestClient

from app.core.sample_data import load_sample_data
from app.main import app
from app.services import recurring
from app.services.recurring import IST

API = "/api/v1"
client = TestClient(app)  # not a context manager, so startup (Postgres table creation) is skipped
DATA = load_sample_data()
RECS = {r["id"]: r for r in DATA["recurring_shipments"]}
WEEK = ("2026-12-01", "2026-12-07")  # Tuesday to Monday


class TestRepeatDates(unittest.TestCase):
    def test_weekly_on_wed_and_sat(self):
        self.assertEqual(recurring.occurrence_dates(RECS[1], *WEEK), [date(2026, 12, 2), date(2026, 12, 5)])
        self.assertEqual(recurring.describe(RECS[1]), "every Wed and Sat")

    def test_daily_gives_every_day(self):
        self.assertEqual(len(recurring.occurrence_dates(RECS[2], *WEEK)), 7)
        self.assertEqual(recurring.describe(RECS[2]), "every day")

    def test_weekly_without_weekdays_uses_start_day(self):
        rec = RECS[1] | {"weekdays": None, "start_date": "2026-12-03"}  # a Thursday
        self.assertEqual(recurring.occurrence_dates(rec, "2026-12-01", "2026-12-20"),
                         [date(2026, 12, 3), date(2026, 12, 10), date(2026, 12, 17)])

    def test_start_and_end_dates_limit_the_repeats(self):
        rec = RECS[2] | {"start_date": "2026-12-03", "end_date": "2026-12-05"}
        self.assertEqual(recurring.occurrence_dates(rec, *WEEK),
                         [date(2026, 12, 3), date(2026, 12, 4), date(2026, 12, 5)])

    def test_copy_has_its_own_id_and_window(self):
        c = recurring.make_occurrence(RECS[2], date(2026, 12, 3))
        self.assertEqual(c["id"], 2003)   # 3rd repeat of recurring shipment 2
        self.assertEqual(c["recurring_id"], 2)
        self.assertEqual(c["delivery_window_start"], "2026-12-03T09:00:00+05:30")
        self.assertEqual(c["delivery_window_end"], "2026-12-04T18:00:00+05:30")  # window_days = 1

    def test_occurrence_number_does_not_depend_on_the_range_asked(self):
        late = recurring.expand([RECS[2]], "2026-12-05", "2026-12-05")
        self.assertEqual(late[0]["id"], 2005)


class TestRepeatsEnterPools(unittest.TestCase):
    def setUp(self):
        self.r = recurring.plan_period(DATA["recurring_shipments"], DATA["shipments"], *WEEK)
        self.by_rec = {x["recurring_id"]: x for x in self.r["recurring"]}

    def test_week_counts(self):
        self.assertEqual(self.r["occurrences_created"], 11)  # 2 + 7 + 1 + 1
        self.assertEqual([(x["occurrences"], x["pooled"]) for x in self.r["recurring"]],
                         [(2, 2), (7, 3), (1, 1), (1, 0)])

    def test_wednesday_bales_join_the_bengaluru_chennai_pool(self):
        wed = self.by_rec[1]["dates"][0]
        self.assertEqual(wed["shipment_id"], 1001)
        self.assertEqual(wed["pooled_with"], [1, 2, 3, 5, 6, 2001])

    def test_saturday_repeats_pool_with_each_other(self):
        sat = self.by_rec[1]["dates"][1]
        self.assertEqual(sat["pooled_with"], [2004])

    def test_snacks_join_the_mumbai_pune_pool(self):
        self.assertEqual(self.by_rec[3]["dates"][0]["pooled_with"], [7, 8, 9, 10])

    def test_two_repeats_of_one_booking_never_share_a_pool(self):
        for p in self.r["pools"]:
            series = [i // 1000 for i in p["shipment_ids"] if i >= 1000]
            self.assertEqual(len(series), len(set(series)), p["shipment_ids"])
        why = {u["shipment_id"]: u["reason"] for u in self.r["unmatched"]}
        self.assertIn("another repeat of the same booking", why[2005])

    def test_lone_route_is_unmatched_with_reason(self):
        mon = self.by_rec[4]["dates"][0]
        self.assertIsNone(mon["pool_id"])
        self.assertEqual(mon["reason"], "no other open shipment travels a similar route")

    def test_one_off_pools_are_unchanged_without_repeats(self):
        alone = recurring.plan_period(DATA["recurring_shipments"], DATA["shipments"], "2026-12-20", "2026-12-20")
        self.assertEqual(alone["pools"][0]["shipment_ids"], [1, 2, 3, 5, 6])


class TestRecurringEngineEndpoints(unittest.TestCase):
    def example(self, path):
        spec = client.get(f"{API}/openapi.json").json()
        return spec["paths"][f"{API}/engine{path}"]["post"]["requestBody"]["content"]["application/json"][
            "examples"]["sample"]["value"]

    def test_expand_example(self):
        res = client.post(f"{API}/engine/recurring/expand", json=self.example("/recurring/expand"))
        self.assertEqual(res.status_code, 200, res.text)
        occ = res.json()["occurrences"]
        self.assertEqual(len(occ), 11)
        self.assertEqual([o["id"] for o in occ[:3]], [2001, 3001, 1001])  # date order

    def test_pools_example_matches_demo(self):
        res = client.post(f"{API}/engine/recurring/pools", json=self.example("/recurring/pools"))
        self.assertEqual(res.status_code, 200, res.text)
        demo = client.get(f"{API}/engine/demo-recurring").json()
        self.assertEqual([p["shipment_ids"] for p in res.json()["pools"]], [p["shipment_ids"] for p in demo["pools"]])
        self.assertEqual(demo["recurring"][0]["repeats"], "every Wed and Sat")

    def test_bad_requests(self):
        body = self.example("/recurring/expand") | {"from_date": "2026-12-07", "to_date": "2026-12-01"}
        self.assertEqual(client.post(f"{API}/engine/recurring/expand", json=body).status_code, 422)
        bad = self.example("/recurring/expand")
        bad["recurring"][0]["weekdays"] = ["funday"]
        self.assertEqual(client.post(f"{API}/engine/recurring/expand", json=bad).status_code, 422)
        clash = self.example("/recurring/pools")
        clash["shipments"][0]["id"] = 1001
        self.assertEqual(client.post(f"{API}/engine/recurring/pools", json=clash).status_code, 400)
        self.assertEqual(client.get(f"{API}/engine/demo-recurring?from_date=2026-12-07&to_date=2026-12-01")
                         .status_code, 400)


try:
    import aiosqlite  # noqa: F401
    HAVE_SQLITE = True
except ImportError:
    HAVE_SQLITE = False


@unittest.skipUnless(HAVE_SQLITE, "pip install aiosqlite to run the database tests")
class TestRecurringInDatabase(unittest.TestCase):
    """POST /recurring and /recurring/generate against a throwaway in-memory database."""

    @classmethod
    def setUpClass(cls):
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import StaticPool
        from app.db.base import Base
        from app.db.session import get_db
        from app.models import Shipment, Truck, User

        cls.engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool,
                                         connect_args={"check_same_thread": False})
        Session = async_sessionmaker(cls.engine, expire_on_commit=False)

        async def setup():
            async with cls.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with Session() as db:
                db.add(User(id=1, email="s@example.com", hashed_password="x", full_name="Shipper"))
                db.add(Truck(id=1, transporter_id=1, truck_type="Tata 407", registration_number="KA01",
                             max_weight_kg=2500, max_volume_cbm=14, origin_city="Bengaluru",
                             origin_lat=12.9716, origin_lng=77.5946, destination_city="Chennai",
                             dest_lat=13.0827, dest_lng=80.2707,
                             available_date=datetime(2026, 12, 1, 6, tzinfo=IST), rate_per_km=28))
                db.add(Shipment(id=1, shipper_id=1, title="Saree bales", goods_type="textiles", weight_kg=600,
                                volume_cbm=1.8, origin_address="Bengaluru", origin_lat=12.9716, origin_lng=77.5946,
                                destination_address="Chennai", dest_lat=13.0827, dest_lng=80.2707,
                                delivery_window_start=datetime(2026, 12, 2, 9, tzinfo=IST),
                                delivery_window_end=datetime(2026, 12, 3, 18, tzinfo=IST)))
                await db.commit()

        asyncio.run(setup())

        async def override_db():
            async with Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_1_save_recurring_and_auto_join_open_pool(self):
        empty = client.post(f"{API}/pools/", json={"truck_id": 1})  # older, but empty: never auto-joined
        self.assertEqual(empty.json()["status"], "OPEN")
        pool = client.post(f"{API}/pools/", json={"truck_id": 1, "shipment_ids": [1], "split_method": "weight"})
        self.assertEqual(pool.status_code, 200, pool.text)
        pool_cost = pool.json()["total_cost"]

        body = {k: v for k, v in RECS[2].items() if k not in ("id", "shipper_key")}
        res = client.post(f"{API}/recurring/", json=body)
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["repeats"], "every day")
        self.assertTrue(res.json()["active"])

        gen = client.post(f"{API}/recurring/generate?from_date=2026-12-01&to_date=2026-12-03")
        self.assertEqual(gen.status_code, 200, gen.text)
        g = gen.json()
        self.assertEqual([c["date"] for c in g["created"]], ["2026-12-01", "2026-12-02", "2026-12-03"])
        first = g["created"][0]
        self.assertEqual(first["title"], "Pipe fittings (daily) (Tue 01 Dec)")
        self.assertEqual(first["pool_id"], pool.json()["id"])         # Dec 1 load joins the open pool
        self.assertIsNone(g["created"][1]["pool_id"])                  # the pool already has a repeat
        self.assertIn("no open pool", g["created"][1]["reason"])
        # Dec 2 and Dec 3 are left; repeats of one booking don't pool with each other
        self.assertEqual(g["candidate_pools"]["pools"], [])
        self.assertEqual(len(g["candidate_pools"]["unmatched"]), 2)

        self.assertEqual(client.get(f"{API}/pools/{empty.json()['id']}").json()["shipments"], [])

        saved = client.get(f"{API}/pools/{first['pool_id']}").json()
        self.assertEqual(len(saved["shipments"]), 2)
        self.assertEqual(saved["current_weight_kg"], 850)
        shares = {s["id"]: s["allocated_cost"] for s in saved["shipments"]}
        self.assertAlmostEqual(sum(shares.values()), pool_cost, places=2)  # the same trip, now shared
        self.assertEqual(shares[first["shipment_id"]], round(pool_cost * 250 / 850, 2))

    def test_2_generate_again_makes_nothing_twice(self):
        g = client.post(f"{API}/recurring/generate?from_date=2026-12-01&to_date=2026-12-04").json()
        self.assertEqual(g["already_there"], 3)
        self.assertEqual([c["date"] for c in g["created"]], ["2026-12-04"])
        made = client.get(f"{API}/shipments/").json()
        self.assertEqual(sum(1 for s in made if s["recurring_id"] == 1), 4)

    def test_3_stopped_recurring_makes_no_more(self):
        res = client.post(f"{API}/recurring/1/stop")
        self.assertFalse(res.json()["active"])
        g = client.post(f"{API}/recurring/generate?from_date=2026-12-05&to_date=2026-12-07").json()
        self.assertEqual(g["created"], [])
        self.assertEqual(client.get(f"{API}/recurring/").json()[0]["id"], 1)
        self.assertEqual(client.get(f"{API}/recurring/99").status_code, 404)

    def test_4_weekly_needs_valid_dates(self):
        body = {k: v for k, v in RECS[1].items() if k not in ("id", "shipper_key")}
        bad = body | {"start_date": "2026-12-10", "end_date": "2026-12-01"}
        self.assertEqual(client.post(f"{API}/recurring/", json=bad).status_code, 422)
        res = client.post(f"{API}/recurring/", json=body)
        self.assertEqual(res.json()["weekdays"], ["wed", "sat"])
        self.assertEqual(res.json()["repeats"], "every Wed and Sat")


if __name__ == "__main__":
    unittest.main()
