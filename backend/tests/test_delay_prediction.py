"""
Task 10: delay prediction. ETA from the stop order, a simple traffic model, stop times
and rest breaks; each shipment flagged on_time, at_risk (< 2 h to spare) or late.
"""
import asyncio
import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services import delay_predictor as dp
from app.services import route_optimizer as ro

API = "/api/v1"
client = TestClient(app)
IST = timezone(timedelta(hours=5, minutes=30))


def leg_plan(*legs):
    """A stop plan with a start, then pickup/drop of shipment 1, using given free-flow minutes."""
    stops = [{"seq": 1, "kind": "start", "shipment_id": None, "leg_minutes": 0.0}]
    kinds = ["pickup", "drop"]
    for i, minutes in enumerate(legs):
        stops.append({"seq": i + 2, "kind": kinds[i], "shipment_id": 1, "leg_minutes": float(minutes)})
    return {"stops": stops, "total_km": 0.0}


class TestTrafficModel(unittest.TestCase):
    def test_time_of_day_factors(self):
        self.assertEqual(dp.traffic_factor(datetime(2026, 12, 1, 9, 0, tzinfo=IST)), 1.5)    # morning rush
        self.assertEqual(dp.traffic_factor(datetime(2026, 12, 1, 18, 0, tzinfo=IST)), 1.5)   # evening rush
        self.assertEqual(dp.traffic_factor(datetime(2026, 12, 1, 2, 0, tzinfo=IST)), 0.9)    # night
        self.assertEqual(dp.traffic_factor(datetime(2026, 12, 1, 14, 0, tzinfo=IST)), 1.15)  # day

    def test_same_drive_is_slower_in_rush_hour(self):
        deadlines = {1: None}
        night = dp.predict(leg_plan(0, 60), datetime(2026, 12, 1, 1, 0, tzinfo=IST), deadlines)
        rush = dp.predict(leg_plan(0, 60), datetime(2026, 12, 1, 8, 0, tzinfo=IST), deadlines)
        # 60 free-flow minutes: 54 at night, 90 in rush hour (+30 min loading in both)
        self.assertEqual(night["shipments"][0]["eta"], "2026-12-01T02:24:00+05:30")
        self.assertEqual(rush["shipments"][0]["eta"], "2026-12-01T10:00:00+05:30")

    def test_utc_times_use_the_india_clock(self):
        # 00:30 UTC is 06:00 in India: normal day traffic, not night
        utc = datetime(2026, 12, 1, 0, 30, tzinfo=timezone.utc)
        self.assertEqual(dp.traffic_factor(utc), 1.15)
        r = dp.predict(leg_plan(0, 60), utc, {1: None})
        self.assertEqual(r["departure"], "2026-12-01T06:00:00+05:30")

    def test_live_traffic_number_overrides_the_model(self):
        r = dp.predict(leg_plan(0, 100), datetime(2026, 12, 1, 9, 0, tzinfo=IST), {1: None}, traffic_multiplier=1.0)
        self.assertEqual(r["minutes"]["traffic_delay"], 0)

    def test_rest_break_after_4_hours_of_driving(self):
        r = dp.predict(leg_plan(0, 300), datetime(2026, 12, 1, 0, 0, tzinfo=IST), {1: None}, traffic_multiplier=1.0)
        self.assertEqual(r["minutes"]["rest_breaks"], 30)


class TestDelayFlags(unittest.TestCase):
    START = datetime(2026, 12, 1, 12, 0, tzinfo=IST)

    def flag(self, deadline):
        # 30 min loading + 60 free-flow minutes at 12:00 (x1.15 = 69 min): drop at 13:39
        return dp.predict(leg_plan(0, 60), self.START, {1: deadline}, traffic_multiplier=None)["shipments"][0]

    def test_on_time_at_risk_late(self):
        self.assertEqual(self.flag(datetime(2026, 12, 1, 18, 0, tzinfo=IST))["delay_flag"], "on_time")
        at_risk = self.flag(datetime(2026, 12, 1, 15, 0, tzinfo=IST))
        self.assertEqual((at_risk["delay_flag"], at_risk["minutes_to_spare"], at_risk["likely_late"]),
                         ("at_risk", 81, True))
        late = self.flag(datetime(2026, 12, 1, 13, 0, tzinfo=IST))
        self.assertEqual((late["delay_flag"], late["minutes_to_spare"]), ("late", -39))
        self.assertEqual(self.flag(None)["delay_flag"], "no_deadline")

    def test_pool_flag_is_the_worst(self):
        plan = ro.optimize_stops_offline([
            {"id": 1, "origin_lat": 19.076, "origin_lng": 72.8777, "dest_lat": 18.5204, "dest_lng": 73.8567},
            {"id": 2, "origin_lat": 19.076, "origin_lng": 72.8777, "dest_lat": 18.7546, "dest_lng": 73.4062},
        ], {"lat": 19.076, "lng": 72.8777})
        r = dp.predict(plan, self.START, {1: datetime(2026, 12, 1, 16, 0, tzinfo=IST),
                                          2: datetime(2026, 12, 2, 18, 0, tzinfo=IST)})
        self.assertEqual(r["delay_flag"], "late")
        self.assertEqual(r["late_shipments"], [1])


class TestEtaEndpoints(unittest.TestCase):
    def test_example_flags_the_frozen_paneer(self):
        spec = client.get(f"{API}/openapi.json").json()
        ex = spec["paths"][f"{API}/engine/eta"]["post"]["requestBody"]["content"]["application/json"][
            "examples"]["sample"]["value"]
        res = client.post(f"{API}/engine/eta", json=ex)
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["eta"], "2026-12-01T17:22:00+05:30")
        self.assertEqual(body["delay_flag"], "at_risk")
        self.assertEqual(body["late_shipments"], [10])
        paneer = next(s for s in body["shipments"] if s["shipment_id"] == 10)
        self.assertEqual((paneer["eta"], paneer["minutes_to_spare"]), ("2026-12-01T16:22:00+05:30", 98))

    def test_every_demo_pool_has_an_eta_and_a_flag(self):
        pools = client.get(f"{API}/engine/demo-eta").json()
        self.assertEqual(len(pools), 5)
        for p in pools:
            self.assertIn(p["delay_flag"], ("on_time", "at_risk", "late"))
            self.assertTrue(p["eta"])
        self.assertTrue(all(p["delay_flag"] == "on_time" for p in pools))
        late = client.get(f"{API}/engine/demo-eta?delay_hours=6").json()
        truck2 = next(p for p in late if p["truck_id"] == 2)
        self.assertEqual((truck2["delay_flag"], truck2["late_shipments"]), ("late", [10]))

    def test_needs_a_start_time(self):
        body = {"truck": {"id": 1, "max_weight_kg": 1000, "max_volume_cbm": 10, "origin_lat": 19.0,
                          "origin_lng": 72.8, "dest_lat": 18.5, "dest_lng": 73.8},
                "shipments": [{"id": 1, "weight_kg": 5, "origin_lat": 19.0, "origin_lng": 72.8,
                               "dest_lat": 18.5, "dest_lng": 73.8}]}
        self.assertEqual(client.post(f"{API}/engine/eta", json=body).status_code, 422)


try:
    import aiosqlite  # noqa: F401
    HAVE_SQLITE = True
except ImportError:
    HAVE_SQLITE = False


@unittest.skipUnless(HAVE_SQLITE, "pip install aiosqlite to run the database tests")
class TestSavedPoolEta(unittest.TestCase):
    """GET /pools/active/eta and /pools/{id}/eta against a throwaway in-memory database."""

    @classmethod
    def setUpClass(cls):
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import StaticPool
        from app.db.base import Base
        from app.db.session import get_db
        from app.models import Pool, Shipment, Truck, User
        from app.models.pool import PoolStatus
        from app.models.tracking import TrackingEvent

        cls.engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool,
                                         connect_args={"check_same_thread": False})
        Session = async_sessionmaker(cls.engine, expire_on_commit=False)
        utc = timezone.utc

        async def setup():
            async with cls.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with Session() as db:
                db.add(User(id=1, email="s@example.com", hashed_password="x", full_name="Shipper"))
                # Mumbai to Pune, leaves 1 Dec 06:00 IST (00:30 UTC)
                db.add(Truck(id=1, transporter_id=1, truck_type="Eicher", registration_number="MH01",
                             max_weight_kg=4000, max_volume_cbm=22, origin_city="Mumbai",
                             origin_lat=19.076, origin_lng=72.8777, destination_city="Pune",
                             dest_lat=18.5204, dest_lng=73.8567,
                             available_date=datetime(2026, 12, 1, 0, 30, tzinfo=utc), rate_per_km=32))
                for id, deadline in [(1, datetime(2026, 12, 2, 12, 30, tzinfo=utc)),    # 2 Dec 18:00 IST
                                     (2, datetime(2026, 12, 1, 3, 30, tzinfo=utc)),     # 1 Dec 09:00 IST
                                     (3, datetime(2026, 12, 2, 12, 30, tzinfo=utc))]:
                    db.add(Shipment(id=id, shipper_id=1, title=f"S{id}", goods_type="textiles", weight_kg=500,
                                    volume_cbm=1, origin_address="Mumbai", origin_lat=19.076, origin_lng=72.8777,
                                    destination_address="Pune", dest_lat=18.5204, dest_lng=73.8567,
                                    delivery_window_end=deadline))
                db.add(Pool(id=1, truck_id=1, status=PoolStatus.OPTIMIZED))
                db.add(Pool(id=2, truck_id=1, status=PoolStatus.IN_TRANSIT))
                db.add(Pool(id=3, truck_id=1, status=PoolStatus.COMPLETED))
                await db.flush()
                for sid, pid in [(1, 1), (2, 1), (3, 2)]:
                    s = await db.get(Shipment, sid)
                    s.pool_id = pid
                # Pool 2's truck was seen at Lonavala at 1 Dec 12:00 IST
                db.add(TrackingEvent(pool_id=2, status="IN_TRANSIT", location_name="Lonavala",
                                     latitude=18.7546, longitude=73.4062,
                                     timestamp=datetime(2026, 12, 1, 6, 30, tzinfo=utc)))
                await db.commit()

        asyncio.run(setup())

        async def override_db():
            async with Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_db

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_every_active_pool_returns_an_eta_and_a_flag(self):
        res = client.get(f"{API}/pools/active/eta")
        self.assertEqual(res.status_code, 200, res.text)
        pools = {p["pool_id"]: p for p in res.json()}
        self.assertEqual(set(pools), {1, 2})  # the completed pool is left out
        self.assertEqual(pools[1]["delay_flag"], "late")         # shipment 2 was due by 09:00
        self.assertEqual(pools[1]["late_shipments"], [2])
        self.assertEqual(pools[2]["delay_flag"], "on_time")

    def test_in_transit_pool_starts_from_its_last_ping(self):
        p = client.get(f"{API}/pools/2/eta").json()
        self.assertEqual(p["timeline"][0]["place"], "Lonavala")
        self.assertEqual(p["departure"], "2026-12-01T12:00:00+05:30")  # 06:30 UTC, shown in India time
        self.assertEqual(p["minutes"]["loading_unloading"], 30)  # already loaded: only the drop

    def test_unknown_pool(self):
        self.assertEqual(client.get(f"{API}/pools/99/eta").status_code, 404)


if __name__ == "__main__":
    unittest.main()
