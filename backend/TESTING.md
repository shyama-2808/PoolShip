# Testing the PoolShip backend in Postman

This guide walks through every backend path, one at a time. For each one you get:

- the **method** and **URL** to type into Postman,
- a **body** to copy and paste (for POST requests),
- **what you should see**, and what to check to know it is right.

The numbers under "What you should see" come from a real run with the sample data. Your numbers should match unless you changed the data.

---

## 0. Before you start

### Start the backend

From the `poolship` folder:

```
docker compose up
```

Wait until the backend log says `Application startup complete`. To check it is up, open http://localhost:8000/health in your browser. You should see `"status": "healthy"`.

### Load the sample data (only needed once)

Part B below uses the database, so it needs the sample users, trucks and shipments. In a second terminal:

```
cd backend
python scripts/load_sample_data.py
```

It should end with `Done. Users: 5, trucks: 5, new shipments: 25.` Running it again is safe, because anything already there is skipped. If you loaded the older 20-shipment file before, it adds only the 5 new return-trip shipments (21 to 25) and says `new shipments: 5`.

### How to send a request in Postman

1. Click **New → HTTP Request** (or the **+** next to your open tabs).
2. Pick the method from the dropdown on the left: **GET** or **POST**.
3. Paste the URL into the box next to it.
4. For a **POST** request:
   - open the **Body** tab,
   - choose **raw**,
   - change the dropdown on the right from *Text* to **JSON**,
   - paste the body from this guide.
5. Click **Send**. The answer appears at the bottom. The status (for example `200 OK`) is shown on the right, just above the answer.

Tip: make an **Environment** with a variable `base` = `http://localhost:8000/api/v1`. Then you can type `{{base}}/engine/carbon` instead of the full URL.

### Do I need to log in?

No. None of these paths ask for a token yet. Login (B1) works and returns a token, but no other request needs it. You can skip the **Authorization** tab completely.

### Status codes you will see

| Code | Meaning |
|---|---|
| 200 / 201 | Worked |
| 404 | Something you asked for (truck, shipment, pool) doesn't exist |
| 409 | Not allowed right now (for example, the shipment is already in a pool) |
| 422 | Your body is wrong, or the shipments don't fit the truck. The answer says why. |

### Swagger as a shortcut

http://localhost:8000/api/v1/docs lists every path. Each engine path has a ready-made example: click **Try it out** and then **Execute**. Postman is better for saving and repeating requests, which is why this guide uses it.

---

## Part A: Logistics engine (`/engine`), no database needed

These paths only calculate. They never save anything, so you can send them as many times as you like.

### A1. Sample data

**GET** `http://localhost:8000/api/v1/engine/sample-data`

**What you should see:** `shipments` (25 items), `trucks` (5 items) and `users` (5 items). Shipments 21 to 25 go the opposite way to the trucks: they are the return loads for Task 8 (C3).

---

### A2. Can two shipments share a truck? (compatibility)

**POST** `http://localhost:8000/api/v1/engine/compatibility`

Mangoes (perishable) are already in the truck. Can paint thinner (hazardous) join them?

```json
{
  "existing_items": [
    {"id": 3, "weight_kg": 500, "volume_cbm": 1.386, "is_perishable": true}
  ],
  "candidate": {"id": 4, "weight_kg": 300, "volume_cbm": 0.72, "is_hazardous": true}
}
```

**What you should see:**

```json
{"compatible": false,
 "reason": "Perishable food cannot be pooled with hazardous chemicals: chemical leaks or fumes can spoil food (clashes with shipment 3)",
 "cautions": []}
```

**Try also:** change `"is_hazardous": true` to `false`. You should get `"compatible": true`. For the full rule table and checking a whole pool at once, see C1.

---

### A3. Pack one truck (optimize-load)

**POST** `http://localhost:8000/api/v1/engine/optimize-load`

Truck 1 (2,500 kg) gets offered the 6 Bengaluru–Chennai shipments (3,400 kg in total).

```json
{
  "truck": {"id": 1, "max_weight_kg": 2500, "max_volume_cbm": 14},
  "shipments": [
    {"id": 1, "weight_kg": 600,  "volume_cbm": 1.8},
    {"id": 2, "weight_kg": 450,  "volume_cbm": 0.96},
    {"id": 3, "weight_kg": 500,  "volume_cbm": 1.386, "is_perishable": true},
    {"id": 4, "weight_kg": 300,  "volume_cbm": 0.72,  "is_hazardous": true},
    {"id": 5, "weight_kg": 350,  "volume_cbm": 0.99},
    {"id": 6, "weight_kg": 1200, "volume_cbm": 0.72}
  ]
}
```

**What you should see:**
- `packed_items`: shipments 6, 2, 4 and 5, with `total_packed_weight_kg` = **2300**
- `unpacked_items`:
  - 3 (mangoes) with *"Perishable food cannot be pooled with hazardous chemicals: chemical leaks or fumes can spoil food (clashes with shipment 4)"*
  - 1 with *"Exceeds truck weight capacity"*
- `overall_utilization_pct` = **92.0**

**Check:** `total_packed_weight_kg` is never more than `max_weight_kg`.

**Edge case, item too big for the truck:** add `"length_cm": 700` to any shipment (the default truck is 420 cm long). That shipment is left out with *"Item dimensions exceed truck cargo hold dimensions"*.

---

### A4. Spread a pool over several trucks (Task 3)

**POST** `http://localhost:8000/api/v1/engine/assign-trucks`

The same 6 shipments, now with two trucks. Trucks are filled in the order you list them.

```json
{
  "trucks": [
    {"id": 1, "max_weight_kg": 2500, "max_volume_cbm": 14},
    {"id": 5, "max_weight_kg": 5000, "max_volume_cbm": 26}
  ],
  "shipments": [
    {"id": 1, "weight_kg": 600,  "volume_cbm": 1.8},
    {"id": 2, "weight_kg": 450,  "volume_cbm": 0.96},
    {"id": 3, "weight_kg": 500,  "volume_cbm": 1.386, "is_perishable": true},
    {"id": 4, "weight_kg": 300,  "volume_cbm": 0.72,  "is_hazardous": true},
    {"id": 5, "weight_kg": 350,  "volume_cbm": 0.99},
    {"id": 6, "weight_kg": 1200, "volume_cbm": 0.72}
  ]
}
```

**What you should see:**
- `trucks_used`: **2**
- Truck 1 takes `[6, 1, 3]`: 2,300 kg, `overall_utilization_pct` **92.0**, `remaining_weight_kg` 200
- Truck 5 takes `[2, 5, 4]`: 1,100 kg, `overall_utilization_pct` **22.0**
- `leftover_items`: `[]`

**Check:**
- No truck has `overall_utilization_pct` above 100.
- Every shipment appears exactly once, either in a truck or in `leftover_items`.
- Mangoes (3) and paint thinner (4) are in different trucks.

**Edge case, overweight:** add this shipment to the list:

```json
{"id": 99, "weight_kg": 6000, "volume_cbm": 2}
```

It comes back in `leftover_items` with a reason starting *"Too big for every truck even when empty"*. The other shipments are still placed.

**Edge case, no room left:** delete truck 5 from `trucks`. Shipments that don't fit in truck 1 end up in `leftover_items` with a reason starting *"No truck has room left for it"*.

---

### A5. Split the trip cost (Task 4)

**POST** `http://localhost:8000/api/v1/engine/cost-split`

A 413 km trip at ₹28/km, shared by 3 shippers, split by weight:

```json
{
  "trip_distance_km": 413,
  "rate_per_km": 28,
  "split_method": "weight",
  "shipments": [
    {"id": 1, "weight_kg": 600, "distance_km": 413, "volume_cbm": 1.8},
    {"id": 2, "weight_kg": 450, "distance_km": 340, "volume_cbm": 0.96},
    {"id": 5, "weight_kg": 350, "distance_km": 160, "volume_cbm": 0.99}
  ]
}
```

**What you should see:**
- `total_trip_cost`: **11564.0** (413 × 28)
- Shipment 1 pays **4956.0**, shipment 2 pays **3717.0**, shipment 5 pays **2891.0**

**Check:** add up all the `allocated_cost` values. They must equal `total_trip_cost` exactly. Adding up `allocated_paise` must equal `total_trip_cost × 100`.

**Try each method:** change `split_method` and send again.

| split_method | Who pays more |
|---|---|
| `weight` | heavier shipments |
| `volume` | bigger shipments (m³) |
| `distance` | shipments that travel further |
| `ton_km` | weight × distance together |

The total stays the same every time.

**Edge case, rounding:** this body splits ₹100 three ways.

```json
{
  "total_trip_cost": 100,
  "split_method": "weight",
  "shipments": [
    {"id": 1, "weight_kg": 1},
    {"id": 2, "weight_kg": 1},
    {"id": 3, "weight_kg": 1}
  ]
}
```

You should get 33.34 + 33.33 + 33.33 = 100.00, with no paisa lost.

**Edge case, missing cost:** send only `"shipments"`, with no `total_trip_cost` and no distance or rate. You get **422** with *"Give total_trip_cost, or both trip_distance_km and rate_per_km"*.

---

### A6. Fuel and CO₂ saved (Task 5)

How it works: without PoolShip, every shipper hires their own truck for their own trip (**separate trucks**, the baseline). With PoolShip, one truck drives its route once and carries everyone (**pooled truck**). The stated factors are in every answer under `emission_factors`:

- diesel used = km × **0.28 L per km** (about 3.57 km per litre)
- CO₂ = litres × **2.68 kg per litre** (so 0.7504 kg CO₂ per km)
- saved = separate trucks − pooled truck, and percent saved = saved ÷ separate trucks × 100. Fuel % and CO₂ % are always the same number.

Saved never goes below 0. If the pooled truck would drive more than everyone alone, saved is 0.

**A6a. When you know each shipper's own trip (most accurate)**

**POST** `http://localhost:8000/api/v1/engine/carbon/compare`

```json
{"separate_trip_km": [413, 380, 150], "pooled_truck_km": 420}
```

**What you should see:**

| | Separate trucks | Pooled truck | Saved |
|---|---|---|---|
| km | `baseline_truck_km` **943.0** | `pooled_truck_km` **420.0** | `km_avoided` **523.0** |
| diesel (L) | `baseline_diesel_litres` **264.04** | `pooled_diesel_litres` **117.6** | `diesel_saved_litres` **146.44** |
| CO₂ (kg) | `baseline_co2_kg` **707.63** | `pooled_co2_kg` **315.17** | `co2_saved_kg` **392.46** |

`fuel_saved_percentage` and `co2_reduction_percentage` are both **55.5**.

**Check by hand:** 943 × 0.28 = 264.04 L, and 264.04 × 2.68 = 707.63 kg.

**Edge cases:** `"separate_trip_km": []`, a negative km, or a negative `pooled_truck_km` give **422**.

**A6b. When you only know the truck's route**

**POST** `http://localhost:8000/api/v1/engine/carbon`

```json
{"pooled_route_distance_km": 413, "num_participants": 4, "detour_km": 10}
```

This assumes each of the 4 shippers would have driven the whole 413 km alone.

**What you should see:** `baseline_truck_km` **1652.0**, `pooled_truck_km` **423.0**, `km_avoided` **1229.0**, `baseline_diesel_litres` **462.56**, `pooled_diesel_litres` **118.44**, `diesel_saved_litres` **344.12**, `baseline_co2_kg` **1239.66**, `pooled_co2_kg` **317.42**, `co2_saved_kg` **922.24**, `co2_reduction_percentage` **74.4**.

**Check:** with `"num_participants": 1` and no detour, everything saved is **0** (both sides are 115.64 L), because a single shipper saves nothing by pooling.

---

### A7. Distance between two places

**POST** `http://localhost:8000/api/v1/engine/route/distance`

From Bengaluru to Chennai:

```json
{"origin": {"lat": 12.9716, "lng": 77.5946}, "destination": {"lat": 13.0827, "lng": 80.2707}}
```

**What you should see:** `straight_line_km` **290.2**, `estimated_road_km` **362.7** (straight line × 1.25).

---

### A8. Is a pickup on the truck's way? (corridor check)

**POST** `http://localhost:8000/api/v1/engine/route/corridor-check`

Hosur to Chennai, checked against a Bengaluru → Chennai truck:

```json
{
  "pickup": {"lat": 12.7409, "lng": 77.8253},
  "drop": {"lat": 13.0827, "lng": 80.2707},
  "truck_start": {"lat": 12.9716, "lng": 77.5946},
  "truck_end": {"lat": 13.0827, "lng": 80.2707},
  "corridor_tolerance_km": 40
}
```

**What you should see:** `on_corridor` **true**, `pickup_offset_km` **26.8**.

**Try also:** set `"corridor_tolerance_km": 10`. Now `on_corridor` is **false**, because Hosur is about 27 km off the route.

---

### A9. Road distance through several stops

**POST** `http://localhost:8000/api/v1/engine/route/road-route`

From Bengaluru to Vellore to Chennai:

```json
{
  "stops": [
    {"lat": 12.9716, "lng": 77.5946},
    {"lat": 12.9165, "lng": 79.1325},
    {"lat": 13.0827, "lng": 80.2707}
  ],
  "use_osrm": false
}
```

**What you should see:** `source` **"estimate"**, `distance_km` about **364**.

With `"use_osrm": true`, the backend asks the free OSRM map service on the internet. If that works, `source` is `"osrm"` and you also get the road `geometry`. If the backend can't reach the internet, it quietly falls back to `"estimate"`.

---

### A10. Which shipments are on a truck's route?

**POST** `http://localhost:8000/api/v1/engine/route/match`

```json
{
  "truck": {"id": 1, "max_weight_kg": 2500, "max_volume_cbm": 14,
            "origin_lat": 12.9716, "origin_lng": 77.5946, "dest_lat": 13.0827, "dest_lng": 80.2707},
  "shipments": [
    {"id": 1,  "weight_kg": 600, "origin_lat": 12.9716, "origin_lng": 77.5946, "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 2,  "weight_kg": 450, "origin_lat": 12.7409, "origin_lng": 77.8253, "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 7,  "weight_kg": 900, "origin_lat": 19.076,  "origin_lng": 72.8777, "dest_lat": 18.5204, "dest_lng": 73.8567},
    {"id": 50, "weight_kg": 300, "origin_lat": 13.0827, "origin_lng": 80.2707, "dest_lat": 12.9716, "dest_lng": 77.5946}
  ],
  "corridor_tolerance_km": 40
}
```

**What you should see:**
- `matched`: shipments **1 and 2**
- `rejected`:
  - 7, because Mumbai → Pune is far off the route
  - 50, because it goes Chennai → Bengaluru, which is the *opposite direction*

To try all 25 sample shipments at once, use Swagger's example for this path, or the one-click demo in A13.

---

### A11. Group shipments into pools (no truck needed)

**POST** `http://localhost:8000/api/v1/engine/route/pools`

```json
{
  "shipments": [
    {"id": 1, "weight_kg": 600, "origin_lat": 12.9716, "origin_lng": 77.5946, "dest_lat": 13.0827, "dest_lng": 80.2707,
     "delivery_window_start": "2026-12-02T09:00:00+05:30", "delivery_window_end": "2026-12-03T18:00:00+05:30"},
    {"id": 2, "weight_kg": 450, "origin_lat": 12.7409, "origin_lng": 77.8253, "dest_lat": 13.0827, "dest_lng": 80.2707,
     "delivery_window_start": "2026-12-02T09:00:00+05:30", "delivery_window_end": "2026-12-03T18:00:00+05:30"},
    {"id": 3, "weight_kg": 500, "origin_lat": 12.7409, "origin_lng": 77.8253, "dest_lat": 13.0827, "dest_lng": 80.2707,
     "delivery_window_start": "2026-12-08T09:00:00+05:30", "delivery_window_end": "2026-12-08T18:00:00+05:30"}
  ],
  "corridor_tolerance_km": 40
}
```

**What you should see:**
- One pool with `shipment_ids` **[1, 2]**
- `unmatched`: shipment **3**, because it has the same route but must arrive on 8 Dec, so the delivery windows don't overlap

**Check:** every shipment appears exactly once, either in a pool or in `unmatched`.

---

### A12. Whole engine in one call (plan-pool)

**POST** `http://localhost:8000/api/v1/engine/plan-pool`

This runs route match → pack the truck → split the cost → count CO₂.

```json
{
  "truck": {"id": 1, "max_weight_kg": 2500, "max_volume_cbm": 14, "rate_per_km": 28,
            "origin_lat": 12.9716, "origin_lng": 77.5946, "dest_lat": 13.0827, "dest_lng": 80.2707},
  "shipments": [
    {"id": 1, "weight_kg": 600, "volume_cbm": 1.8,  "origin_lat": 12.9716, "origin_lng": 77.5946, "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 2, "weight_kg": 450, "volume_cbm": 0.96, "origin_lat": 12.7409, "origin_lng": 77.8253, "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 5, "weight_kg": 350, "volume_cbm": 0.99, "origin_lat": 12.9165, "origin_lng": 79.1325, "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 7, "weight_kg": 900, "volume_cbm": 2.4,  "origin_lat": 19.076,  "origin_lng": 72.8777, "dest_lat": 18.5204, "dest_lng": 73.8567}
  ],
  "corridor_tolerance_km": 40,
  "split_method": "distance"
}
```

**What you should see:**
- `route.matched`: 1, 2 and 5 (7 is rejected as off-route)
- `load.packed_items`: 1, 2 and 5
- `cost_split.shares`: three shares that add up exactly to `total_trip_cost`
- `carbon`: separate vs pooled litres and kg, with `co2_saved_kg` greater than 0
- `stop_plan`: the best order to visit the packed shipments' pickups and drops, starting at the truck's depot (see C2)

---

### A13. One-click demos (GET, no body)

| URL | What you should see |
|---|---|
| `GET http://localhost:8000/api/v1/engine/demo/1` | Bengaluru → Chennai: on route [1–6], packed [6, 2, 4, 5], mangoes (3) and shipment 1 left out, trip ₹10,155.60 |
| `GET http://localhost:8000/api/v1/engine/demo/2` | Mumbai → Pune: all of [7, 8, 9, 10] packed, trip ₹4,806.40 |
| `GET http://localhost:8000/api/v1/engine/demo/3` | Delhi → Jaipur: 14 left out with *"Item dimensions exceed truck cargo hold dimensions"* (a 7 m pipe) |
| `GET http://localhost:8000/api/v1/engine/demo/4` | Bengaluru → Hyderabad: [15, 16, 17] packed, trip ₹34,375.00 |
| `GET http://localhost:8000/api/v1/engine/demo/5` | Coimbatore → Chennai: [18, 19] packed, trip ₹18,700.50 |
| `GET http://localhost:8000/api/v1/engine/demo/99` | **404**: *"No sample truck 99"* |
| `GET http://localhost:8000/api/v1/engine/demo-pools` | Pools [1, 2, 3, 5, 6], [7–10], [11–14], [15–17], [18, 19], [21–24]; unmatched 4 (paint thinner can't join the pool with the mangoes, see C1), 20 and 25 |

Each demo's `carbon` part compares the packed shipments on their own trucks with the one truck:

| Demo | Separate trucks | Pooled truck | Diesel saved | CO₂ saved |
|---|---|---|---|---|
| demo/1 | 1017.0 km, 284.76 L | 362.7 km, 101.56 L | **183.2 L** | **490.99 kg (64.3%)** |
| demo/2 | 439.6 km, 123.09 L | 150.2 km, 42.06 L | **81.03 L** | **217.17 kg (65.8%)** |
| demo/3 | 727.1 km, 203.59 L | 296.9 km, 83.13 L | **120.46 L** | **322.83 kg (59.2%)** |
| demo/4 | 1243.4 km, 348.15 L | 625.0 km, 175.0 L | **173.15 L** | **464.05 kg (49.7%)** |
| demo/5 | 957.3 km, 268.04 L | 534.3 km, 149.6 L | **118.44 L** | **317.42 kg (44.2%)** |

demo/2 says 217.17 kg while the saved pool in B9a says 217.16 kg. That is only rounding: the demo rounds each trip's km to one decimal first.

---

## Part B: Paths that use the database

Run `python scripts/load_sample_data.py` first (see section 0).

**Your ids may differ.** If you had created data before, the trucks and shipments may not be numbered 1–5 and 1–25. Check with B3 and B5 and use your own ids.

**Pools change the data.** Once a shipment is in a pool, it can't join another pool. To start fresh, stop the backend and run `docker compose down -v` (this **deletes all data**). Then run `docker compose up` and load the sample data again.

### B1. Log in

**POST** `http://localhost:8000/api/v1/auth/login`

```json
{"email": "textiles@example.com", "password": "Poolship@123"}
```

**What you should see:** `access_token` (a long string), `"token_type": "bearer"`, `"role": "SHIPPER"` and your `user_id`.

**Edge case:** use a wrong password. You should get **401** *"Incorrect email or password"*.

The other sample logins are `foods@example.com`, `hardware@example.com`, `south@example.com` and `north@example.com` (the last two are transporters). They all use the same password.

### B2. Register a new user

**POST** `http://localhost:8000/api/v1/auth/register`

```json
{"email": "newshop@example.com", "password": "Test@1234", "full_name": "New Shop", "role": "SHIPPER", "company_name": "New Shop Pvt Ltd"}
```

**What you should see:** **201**, with your new user's `id`, `"is_verified": false` and `"rating": 5`. Sending the same email again gives **400** *"User with this email already exists"*.

### B3. Trucks

| Request | What you should see |
|---|---|
| `GET http://localhost:8000/api/v1/trucks/` | All 5 trucks |
| `GET http://localhost:8000/api/v1/trucks/?origin=Bengaluru` | Only the Bengaluru trucks (1 and 4) |
| `GET http://localhost:8000/api/v1/trucks/2` | Eicher 14 ft, Mumbai → Pune, 4,000 kg, ₹32/km |
| `GET http://localhost:8000/api/v1/trucks/999` | **404** *"Truck not found"* |

### B4. Add a truck

**POST** `http://localhost:8000/api/v1/trucks/?transporter_id=4`

```json
{
  "truck_type": "Tata 407", "registration_number": "KA05TEST01",
  "max_weight_kg": 2500, "max_volume_cbm": 14,
  "origin_city": "Bengaluru", "origin_lat": 12.9716, "origin_lng": 77.5946,
  "destination_city": "Mysuru", "dest_lat": 12.2958, "dest_lng": 76.6394,
  "available_date": "2026-12-05T06:00:00+05:30", "rate_per_km": 30
}
```

**What you should see:** the truck with its new `id` and `"is_active": true`. The `registration_number` must be new each time you send this.

### B5. Shipments

| Request | What you should see |
|---|---|
| `GET http://localhost:8000/api/v1/shipments/` | All 25 shipments |
| `GET http://localhost:8000/api/v1/shipments/?status=POSTED` | Shipments not yet in a pool |
| `GET http://localhost:8000/api/v1/shipments/7` | Denim rolls, Mumbai → Pune, `"status": "POSTED"`, `"pool_id": null` |

### B6. Add a shipment

**POST** `http://localhost:8000/api/v1/shipments/?shipper_id=1`

```json
{
  "title": "Cotton bales", "goods_type": "textiles", "weight_kg": 400,
  "length_cm": 120, "width_cm": 100, "height_cm": 100,
  "origin_address": "Mumbai", "origin_lat": 19.076, "origin_lng": 72.8777,
  "destination_address": "Pune", "dest_lat": 18.5204, "dest_lng": 73.8567
}
```

**What you should see:** the new shipment with `"status": "POSTED"` and `volume_cbm` **1.2**, which is worked out from the size because none was given, and `"temperature_class": "ambient"`. For cold goods add `"temperature_class": "chilled"` (2 to 8 °C) or `"frozen"`; any other word gives **422**.

### B7. Preview a pool (saves nothing)

**POST** `http://localhost:8000/api/v1/pools/optimize`

```json
{"truck_id": 2, "shipment_ids": [7, 8, 9, 10], "split_method": "weight"}
```

**What you should see:**
- `total_trip_cost` **4806.09**
- `overall_utilization_pct` **70.0**
- `unpacked_shipments`: `[]`
- in `packed_shipments`, each shipment's `allocated_cost`: 7 → **1544.82**, 8 → **1201.52**, 9 → **1373.17**, 10 → **686.58**

**Check:** 1544.82 + 1201.52 + 1373.17 + 686.58 = 4806.09 exactly.

**Edge case, mangoes + paint thinner + overweight:**

```json
{"truck_id": 1, "shipment_ids": [1, 2, 3, 4, 5, 6], "split_method": "weight"}
```

`unpacked_shipments` should list 3 (*"Perishable food cannot be pooled with hazardous chemicals: chemical leaks or fumes can spoil food (clashes with shipment 4)"*) and 1 (*"Exceeds truck weight capacity"*). Their `allocated_cost` is 0.

### B8. Create a pool (saves it)

**POST** `http://localhost:8000/api/v1/pools/`

```json
{"truck_id": 2, "shipment_ids": [7, 8, 9, 10], "split_method": "weight"}
```

**What you should see:**
- the pool's `id` (note it down for B9 and B10)
- `"status": "OPTIMIZED"`, `"split_method": "weight"`
- `total_cost` **4806.09**, `current_weight_kg` **2800**, `utilization_percentage` **70.0**, `co2_saved_kg` **217.16**, `diesel_saved_litres` **81.03**
- `shipments`: 4 shipments, each with `"status": "POOLED"`, `pool_id` = the new pool's id, and its own `allocated_cost` (the same numbers as B7)
- `truck`: the full truck details

**Check:** the shipments' `allocated_cost` values add up exactly to `total_cost`.

**Edge cases:**

| Send this | What you should see |
|---|---|
| The same body again | **409** *"Shipments already pooled or no longer open: [7, 8, 9, 10]"* |
| `{"truck_id": 1, "shipment_ids": [1, 2, 3, 4, 5, 6]}` | **422**, refused by the compatibility check before packing: `detail.message` is *"Shipments 3 and 4 can't share a truck. Perishable food cannot be pooled with hazardous chemicals: chemical leaks or fumes can spoil food"* and `detail.conflicts` lists the pair [3, 4]. Nothing is saved. |
| `{"truck_id": 1, "shipment_ids": [1, 2, 4, 5, 6]}` | **422**, too heavy (2,900 kg): `detail.does_not_fit` lists 1 with *"Exceeds truck weight capacity"*. Nothing is saved. |
| `{"truck_id": 1, "shipment_ids": [999]}` | **404** *"Shipments not found: [999]"* |
| `{"truck_id": 999, "shipment_ids": [1]}` | **404** *"Truck not found"* |
| `{"truck_id": 1, "shipment_ids": [2, 4, 5, 6], "split_method": "magic"}` | **422**, because the split method must be weight, volume, distance or ton_km |
| `{"truck_id": 1}` | An empty pool with `"status": "OPEN"` (allowed) |

To see a successful pool with a different split, use `{"truck_id": 1, "shipment_ids": [2, 4, 5, 6], "split_method": "distance"}`. These four fit in truck 1.

After B8, `GET http://localhost:8000/api/v1/shipments/7` shows `"status": "POOLED"`, its `pool_id`, and `allocated_cost` **1544.82**.

### B9. Look at a pool

**GET** `http://localhost:8000/api/v1/pools/1`

Use your pool's id instead of 1.

**What you should see:** the same pool as B8, with its shipments and truck. A pool id that doesn't exist gives **404** *"Pool not found"*.

### B9a. Fuel and CO₂ for a saved pool (Task 5)

**GET** `http://localhost:8000/api/v1/pools/1/carbon`

Use your B8 pool's id instead of 1. No body.

**What you should see** (for the B8 pool, truck 2 with shipments 7, 8, 9, 10):

| | Separate trucks (4) | Pooled truck (1) | Saved |
|---|---|---|---|
| km | `baseline_truck_km` **439.59** | `pooled_truck_km` **150.19** | `km_avoided` **289.4** |
| diesel (L) | `baseline_diesel_litres` **123.08** | `pooled_diesel_litres` **42.05** | `diesel_saved_litres` **81.03** |
| CO₂ (kg) | `baseline_co2_kg` **329.86** | `pooled_co2_kg` **112.7** | `co2_saved_kg` **217.16** |

`co2_reduction_percentage` and `fuel_saved_percentage` are **65.8**. `emission_factors` shows 0.28 L/km and 2.68 kg/L.

`separate_trips` lists each shipment's own truck: 7 → **150.19 km**, 42.05 L, 112.7 kg; 8 → **130.08 km**, 36.42 L, 97.61 kg; 9 → **82.61 km**, 23.13 L, 61.99 kg; 10 → **76.71 km**, 21.48 L, 57.56 kg.

**Check:** `co2_saved_kg` and `diesel_saved_litres` are the same as the pool showed in B8. The four trip km add up to `baseline_truck_km`.

**Edge cases:** an empty pool (`{"truck_id": 1}` in B8) gives all zeros and `"separate_trips": []`. A pool id that doesn't exist gives **404** *"Pool not found"*.

### B10. Tracking

**POST** `http://localhost:8000/api/v1/tracking/`

Put your pool's id in `pool_id`:

```json
{"pool_id": 1, "status": "IN_TRANSIT", "location_name": "Lonavala", "latitude": 18.7546, "longitude": 73.4062, "note": "Crossed the ghat"}
```

**What you should see:** **201** with the event and a `timestamp`. The pool's status changes to `IN_TRANSIT`, which you can check with B9. Sending `"status": "DELIVERED"` changes the pool to `COMPLETED`.

**GET** `http://localhost:8000/api/v1/tracking/pool/1` lists the pool's events, newest first.

### B11. Dashboard numbers

**GET** `http://localhost:8000/api/v1/analytics/summary`

**What you should see:** if the B8 pool is your only pool: `total_pools` **1**, `total_shipments_pooled` **4** (only shipments that are in a pool are counted), `average_truck_utilization_pct` **70.0**, `total_co2_saved_kg` **217.16**, `total_diesel_saved_litres` **81.03**, and `emission_factors`. Each extra pool you create changes them; an empty pool counts as a pool with 0% fill.

---

## Part C: Phase 3 smart engine (Tasks 6 to 10)

C1 to C4 and C5a, C5b use the engine only (no database). C5c uses the pool you saved in B8.

### C1. Which goods can't share a truck? (Task 7, compatibility rules)

How it works: every shipment is put into **goods groups** from its `goods_type` word and its flags. For example `"grains"` counts as food and `"chemicals"` or `"is_hazardous": true` counts as hazardous chemicals. A **rule table** then says which groups can't share a truck (**block**) and which may share with a handling note (**caution**):

| Group A | Group B | Result | Why |
|---|---|---|---|
| perishable food | hazardous chemicals | block | chemical leaks or fumes can spoil food |
| grains and spices | hazardous chemicals | block | same, for dry food |
| medicines | hazardous chemicals | block | same, for medicines |
| temperature-controlled goods | hazardous chemicals | block | no chemicals in a closed refrigerated hold |
| chilled | frozen | block | a truck keeps one temperature for its whole hold |
| fragile goods | heavy construction material | caution | load fragile goods last, on top, strapped down |

Shipments now have a `temperature_class` field: `ambient` (default), `chilled` (2 to 8 °C) or `frozen` (-18 °C or colder). In the sample data the frozen paneer (10) is `frozen`.

The check runs **before pooling** in three places: `POST /pools` refuses the pool (B8), the automatic grouping in A11 and A13 skips a shipment that would clash, and packing a truck (A3, A4) leaves it out with the reason.

**C1a. See the rule table:** **GET** `http://localhost:8000/api/v1/engine/compatibility/rules`. You get `goods_groups` (which words go in each group), `rules` (the table above) and `flag_notes`.

**C1b. Check a whole pool before creating it**

**POST** `http://localhost:8000/api/v1/engine/compatibility/pool`

Mangoes, paint thinner and saree bales:

```json
{
  "shipments": [
    {"id": 3, "weight_kg": 500, "goods_type": "perishable", "is_perishable": true},
    {"id": 4, "weight_kg": 300, "goods_type": "chemicals", "is_hazardous": true},
    {"id": 1, "weight_kg": 600, "goods_type": "textiles"}
  ]
}
```

**What you should see:**
- `compatible` **false**
- `reason` *"Shipments 3 and 4 can't share a truck. Perishable food cannot be pooled with hazardous chemicals: chemical leaks or fumes can spoil food"*
- `conflicts`: one entry, `shipment_ids` **[3, 4]**, `severity` **"block"**, `rule` **"perishable + hazardous"**
- `flags`: shipment 4 has `["hazardous"]` with the note *"Hazardous: needs hazard labels and a spill kit on board"*

**Try also:**

| Change | What you should see |
|---|---|
| Remove shipment 4 | `compatible` **true**, `reason` *"All shipments can share a truck"* |
| Remove the flags, keep only `"goods_type": "perishable"` and `"chemicals"` | still **false** (the goods type alone is enough) |
| `[{"id": 10, "weight_kg": 400, "temperature_class": "frozen"}, {"id": 30, "weight_kg": 200, "temperature_class": "chilled"}]` | **false**, *"Temperature mismatch: shipment 10 is frozen and shipment 30 is chilled, but a truck keeps one temperature for its whole hold"* |
| `[{"id": 15, "weight_kg": 300, "is_fragile": true}, {"id": 16, "weight_kg": 6000, "goods_type": "construction"}]` | **true**, with one entry in `cautions` (*"...can crush fragile goods: load the fragile goods last..."*) |
| `"temperature_class": "warm"` | **422** |

**C1c. In a saved pool:** see the first edge case in B8. Mangoes plus paint thinner gives **422** and nothing is saved.

---

### C2. Best order for pickups and drops (Task 6, multi-stop route)

How it works: the truck has to visit every pickup and every drop, and a pickup must always come before its drop. The engine gets the road km between every pair of stops from **OSRM** (a free online map service). If OSRM can't be reached, or you send `"use_osrm": false`, it uses straight line × 1.25. Up to 6 shipments it checks every valid order, so the answer is the true shortest (`method: "exact"`). With more shipments it uses a fast "nearest next stop, then improve" method (`method: "heuristic"`).

`as_listed_km` is the trip if you drove all pickups in the order given and then all drops. `km_saved` shows what the sorting gained.

**POST** `http://localhost:8000/api/v1/engine/route/optimize-stops`

The Bengaluru → Chennai pool (shipments 1, 2, 3, 5, 6), starting at truck 1's depot:

```json
{
  "shipments": [
    {"id": 1, "origin_address": "Bengaluru", "origin_lat": 12.9716, "origin_lng": 77.5946, "destination_address": "Chennai", "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 2, "origin_address": "Hosur", "origin_lat": 12.7409, "origin_lng": 77.8253, "destination_address": "Chennai", "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 3, "origin_address": "Kolar", "origin_lat": 13.136, "origin_lng": 78.1292, "destination_address": "Chennai", "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 5, "origin_address": "Vellore", "origin_lat": 12.9165, "origin_lng": 79.1325, "destination_address": "Chennai", "dest_lat": 13.0827, "dest_lng": 80.2707},
    {"id": 6, "origin_address": "Bengaluru", "origin_lat": 12.9716, "origin_lng": 77.5946, "destination_address": "Sriperumbudur", "dest_lat": 12.9675, "dest_lng": 79.9419}
  ],
  "start": {"lat": 12.9716, "lng": 77.5946, "place": "Bengaluru"},
  "use_osrm": false
}
```

**What you should see:** `total_km` **409.9**, `as_listed_km` **871.2**, `km_saved` **461.3** (`saved_percentage` **53.0**), `method` **"exact"**, `distance_source` **"estimate"**, `total_minutes` **546.5**. The `stops` come in this order:

| seq | kind | shipment | place | cumulative_km |
|---|---|---|---|---|
| 1 | start | | Bengaluru | 0.0 |
| 2, 3 | pickup | 6, 1 | Bengaluru | 0.0 |
| 4 | pickup | 2 | Hosur | 44.8 |
| 5 | pickup | 3 | Kolar | 113.4 |
| 6 | pickup | 5 | Vellore | 252.7 |
| 7 | drop | 6 | Sriperumbudur | 362.5 |
| 8 to 11 | drop | 5, 3, 2, 1 | Chennai | 409.9 |

**Check:** every shipment's pickup comes before its drop, and the last stop's `cumulative_km` equals `total_km`.

**Try also:** `"use_osrm": true`. If the backend can reach the internet, `distance_source` becomes **"osrm"** and the km are real road km, so the numbers differ a little. If not, you quietly get the same answer as above. Add `"end": {"lat": 12.9716, "lng": 77.5946, "place": "Bengaluru"}` to make the truck finish back at its depot. Leaving out `start` lets the truck begin at whichever pickup is best.

**One-click demo:** **GET** `http://localhost:8000/api/v1/engine/demo-stops/1` orders what demo/1 packs (shipments 2, 4, 5, 6): `total_km` **380.8** versus `as_listed_km` **1228.3**. Trucks 3, 4 and 5 show `km_saved` 0, because their sample shipments are already listed in the best order. `GET /engine/demo/1` and `plan-pool` now also include this as `stop_plan`.

---

### C3. Loads for the empty trip home (Task 8, return-trip matching)

How it works:
1. The **return route** is the truck's destination back to its origin.
2. The truck leaves for home after its outbound drive (road km at 45 km/h) plus unloading (`unloading_hours`, 2 by default), counted from its `available_date`.
3. A shipment is matched when its pickup and drop lie along the way home (the same corridor test as A10), **and** the truck reaches its drop before its delivery window closes, **and** it fits (weight, volume, size, C1 rules).
4. The return trip's cost (return km × ₹/km) is now paid by the matched shippers, split by tonnes × km.

The sample data has 5 shipments going the "wrong" way for this: 21 to 24 go Chennai → Bengaluru (truck 1's way home) and 25 goes Pune → Mumbai (truck 2's way home).

**GET** `http://localhost:8000/api/v1/engine/demo-return/1` (no body)

**What you should see:**
- `return_route`: from **Chennai** to **Bengaluru**, `return_km` **362.7**, `departs_at` **2026-12-01T16:04:00+05:30** (06:00 + 8 h 04 min of driving + 2 h unloading), `arrives_home_at` **2026-12-02T00:08:00+05:30**
- `matched`: shipments **21, 22, 23**, which pay ₹**4,245.23**, ₹**4,341.54** and ₹**1,568.83**
- `load`: `total_weight_kg` **2050**, `overall_utilization_pct` **82.0**
- `return_trip_earnings` **10155.6** (the three shares add up to this exactly), `is_empty_return` **false**
- `rejected` includes 24 with *"On the route, but the truck would only reach the drop around 2026-12-02T00:08+05:30, after its delivery window closes at 2026-12-01T18:00+05:30"*, 25 (*"Pickup is 638 km away from the truck's route"*), and the outbound shipments 1 to 6 (*"...opposite direction..."*)
- `stop_plan`: Chennai → pickup 21 (Chennai) → pickup 22 (Sriperumbudur) → pickup 23 (Vellore) → drop 22 (Hosur) → drops 21 and 23 (Bengaluru), **380.8 km**

| Other demos | What you should see |
|---|---|
| `GET .../engine/demo-return/2` | Pune → Mumbai: carries **[25]**, 30.0% full, earns ₹**4,806.40** |
| `GET .../engine/demo-return/3`, `/4`, `/5` | nothing on the way home: `matched` [] and `is_empty_return` **true** |
| `GET .../engine/demo-return/99` | **404** |

**POST version:** **POST** `http://localhost:8000/api/v1/engine/return-trip` takes `{"truck": {...}, "shipments": [...], "corridor_tolerance_km": 40, "unloading_hours": 2}`. Swagger's example is truck 1 against all 25 sample shipments and gives the same answer as demo-return/1. **Try also:** remove `available_date` from the truck. The on-time check is skipped, so 24 is matched too. Or set the truck's `max_weight_kg` to 1000: some loads come back in `rejected` with *"Exceeds truck weight capacity"*.

---

### C4. Dynamic pricing (Task 9)

How it works: **price = base price × multiplier**.

- **Base price** = shipment km × the truck's ₹/km × the share of the truck it uses (the larger of its weight % and volume %).
- **Multiplier** = demand × urgency × fill, kept between **0.85** and **1.50**:

| Factor | Rule |
|---|---|
| demand | open shipments per available truck on the route. 4 per truck is normal (×1.00). Each extra one adds 5%, each one fewer takes 5% off. Kept between 0.80 and 1.25 |
| urgency | standard ×1.00, express ×1.15, urgent ×1.30. Or send `hours_until_deadline`: under 6 h to spare after driving is urgent, under 24 h is express |
| fill (before this shipment) | under 30% full: up to ×1.15 at 0% (few shippers share the truck's cost). 30 to 75%: ×1.00. Over 75%: up to ×1.20 at 100% (the last space is scarce) |

**POST** `http://localhost:8000/api/v1/engine/price`

Plumbing fittings (shipment 2, Hosur → Chennai) on truck 1, booked urgent, with the truck already 85% full:

```json
{
  "shipment": {"id": 2, "weight_kg": 450, "volume_cbm": 0.96, "origin_lat": 12.7409, "origin_lng": 77.8253, "dest_lat": 13.0827, "dest_lng": 80.2707},
  "truck": {"id": 1, "max_weight_kg": 2500, "max_volume_cbm": 14, "rate_per_km": 28},
  "truck_fill_pct": 85,
  "urgency": "urgent"
}
```

**What you should see:** `shipment_km` **334.7**, `space_share_pct` **18.0** (450 ÷ 2500), `base_price` **1686.83**, `factors.urgency.factor` **1.3**, `factors.fill.factor` **1.08**, `factors.demand.factor` **1.0**, `multiplier` **1.404**, `price` **2368.31**. Each factor has a `why`, for example *"Truck is already 85% full: the last space is scarce"*.

**Check by hand:** 334.65 km × ₹28 × 0.18 = ₹1,686.83, and 1,686.83 × 1.3 × 1.08 = ₹2,368.31.

**Try also:** add `"open_shipments_on_route": 20, "trucks_available_on_route": 1`. Now the raw multiplier is 1.755, so `multiplier` is held at **1.5**, `capped` is **"at maximum"** and `price` is **2530.24**. Send `"distance_km": 100` in the shipment instead of the coordinates and it uses 100 km. With neither, you get **422**.

**One-click demo:** **GET** `http://localhost:8000/api/v1/engine/demo-price/2` prices the same shipment in different situations:

| scenario | multiplier | price (₹) |
|---|---|---|
| Normal: standard, truck half full, normal demand | 1.0 | **1686.83** |
| Urgent | 1.3 | **2192.88** |
| Express | 1.15 | **1939.85** |
| Truck nearly empty (5% full) | 1.125 | **1897.68** |
| Truck nearly full (95% full) | 1.16 | **1956.72** |
| Busy route (10 shipments, 1 truck) | 1.25 | **2108.53** |
| Quiet route (1 shipment, 3 trucks): hits the floor | 0.85 | **1433.8** (`capped` "at minimum") |
| Everything at once: urgent, busy, 100% full | 1.5 | **2530.24** (`capped` "at maximum") |

**Check:** urgent, nearly empty and nearly full are all dearer than normal, and no multiplier is below 0.85 or above 1.5.

---

### C5. ETA and delay prediction (Task 10)

How it works: **ETA = departure + driving with traffic + time at stops + rest breaks.**

- The stops are put in the best order first (C2).
- **Traffic** (a simple model, no paid traffic service needed): each leg is driven in 30-minute slices, and each slice is slowed by the clock time it is driven at. Rush hour (08:00 to 11:00 and 17:00 to 21:00) is ×1.50, night (23:00 to 05:00) is ×0.90 and the rest of the day is ×1.15. If you have a live traffic number, send `traffic_multiplier` (1.3 = 30% slower) and it is used instead.
- **Stops:** 30 min at every pickup and drop. **Rest:** a 30 min break after every 4 h of driving.
- **Delay flag** per shipment, from the time left between its ETA and the end of its delivery window: **late** (after it), **at_risk** (less than 2 h before it) or **on_time**. `likely_late` is true for late and at_risk. The pool's `delay_flag` is the worst of its shipments.

**C5a. Every sample pool (one click):** **GET** `http://localhost:8000/api/v1/engine/demo-eta`

**What you should see:** 5 pools, each with an `eta` and a `delay_flag`. All five are **on_time**:

| truck | eta | delay_flag |
|---|---|---|
| 1 | 2026-12-01T21:37+05:30 | on_time |
| 2 | 2026-12-01T14:22+05:30 | on_time |
| 3 | 2026-12-02T17:54+05:30 | on_time |
| 4 | 2026-12-03T03:31+05:30 | on_time |
| 5 | 2026-12-04T00:17+05:30 | on_time |

`minutes` splits each into `free_flow_driving`, `traffic_delay`, `loading_unloading` and `rest_breaks`. For truck 1 that is 508, 159, 240 and 60. `timeline` gives arrival and leaving times for every stop.

**Try also:** `GET .../engine/demo-eta?delay_hours=4`. Truck 2 becomes **at_risk** with `late_shipments` **[10]** (the frozen paneer must arrive by 18:00). With `?delay_hours=6` it is **late**.

**C5b. Your own pool:** **POST** `http://localhost:8000/api/v1/engine/eta`. Swagger's example is truck 2 with shipments 7, 8, 9, 10 leaving 4 hours late:

```json
{
  "truck": {"id": 2, "max_weight_kg": 4000, "max_volume_cbm": 22, "origin_city": "Mumbai",
            "origin_lat": 19.076, "origin_lng": 72.8777, "dest_lat": 18.5204, "dest_lng": 73.8567,
            "available_date": "2026-12-01T06:00:00+05:30"},
  "shipments": [
    {"id": 7, "weight_kg": 900, "origin_address": "Mumbai", "origin_lat": 19.076, "origin_lng": 72.8777, "destination_address": "Pune", "dest_lat": 18.5204, "dest_lng": 73.8567, "delivery_window_end": "2026-12-02T18:00:00+05:30"},
    {"id": 8, "weight_kg": 700, "origin_address": "Navi Mumbai", "origin_lat": 19.033, "origin_lng": 73.0297, "destination_address": "Pune", "dest_lat": 18.5204, "dest_lng": 73.8567, "delivery_window_end": "2026-12-02T18:00:00+05:30"},
    {"id": 9, "weight_kg": 800, "origin_address": "Mumbai", "origin_lat": 19.076, "origin_lng": 72.8777, "destination_address": "Lonavala", "dest_lat": 18.7546, "dest_lng": 73.4062, "delivery_window_end": "2026-12-03T18:00:00+05:30"},
    {"id": 10, "weight_kg": 400, "origin_address": "Khopoli", "origin_lat": 18.7856, "origin_lng": 73.3459, "destination_address": "Pune", "dest_lat": 18.5204, "dest_lng": 73.8567, "delivery_window_end": "2026-12-01T18:00:00+05:30"}
  ],
  "departure_time": "2026-12-01T10:00:00+05:30",
  "use_osrm": false
}
```

**What you should see:** `eta` **2026-12-01T17:22:00+05:30**, `delay_flag` **"at_risk"**, `late_shipments` **[10]**. The paneer's entry has `eta` **2026-12-01T16:22:00+05:30**, `deadline` 18:00 and `minutes_to_spare` **98**, which is under 2 hours, so it is at risk. Leave out `departure_time` to leave at the truck's `available_date` (06:00): everything becomes on_time. With neither, you get **422**.

**C5c. Saved pools (uses the database):**

| Request | What you should see |
|---|---|
| **GET** `http://localhost:8000/api/v1/pools/active/eta` | One entry for every pool that is open, optimized, locked or in transit and has shipments, each with `eta` and `delay_flag`. Completed and cancelled pools are left out. |
| **GET** `http://localhost:8000/api/v1/pools/1/eta` (your B8 pool) | Truck 2 with 7, 8, 9, 10 leaving at its available date: `eta` **2026-12-01T14:22:00+05:30**, `delay_flag` **"on_time"**, the same as truck 2 in C5a |
| **GET** `.../pools/999/eta` | **404** *"Pool not found"* |
| An empty pool | **400** *"Pool has no shipments yet..."* |

**In transit:** after a tracking ping (B10) puts the pool `IN_TRANSIT`, its ETA starts from the ping's place and time instead of the depot. Everything counts as already on board, so only the drops take stop time.

---

## Quick checklist

- [ ] `/health` says healthy
- [ ] A2: mangoes + paint thinner gives `compatible: false`
- [ ] A3: truck 1 packs 2,300 kg, never over 2,500
- [ ] A4: two trucks, no truck over 100%, nothing left over; the 6,000 kg shipment is left over
- [ ] A5: shares add up exactly to the trip cost for weight, volume, distance and ton_km; ₹100 ÷ 3 = 33.34 + 33.33 + 33.33
- [ ] A13: all five demos return 200; demo/99 returns 404
- [ ] B7: preview shares add up to 4806.09
- [ ] B8: pool saved, shipments POOLED with their shares; repeating gives 409; overweight gives 422
- [ ] A6: carbon/compare gives 264.04 L vs 117.6 L and 392.46 kg CO₂ saved (55.5%)
- [ ] B9a: pool carbon shows separate vs pooled litres and kg, 65.8% saved, same CO₂ as the pool
- [ ] B9 to B11: pool, tracking and summary look right
- [ ] C1: mangoes + paint thinner pool gives `compatible: false` with the reason; POST /pools refuses it with 422
- [ ] C2: optimize-stops gives 409.9 km versus 871.2 km as listed, every pickup before its drop
- [ ] C3: demo-return/1 carries 21, 22, 23 home (82% full, ₹10,155.60); 24 is rejected as too late
- [ ] C4: demo-price/2 shows urgent, nearly empty and nearly full all dearer than ₹1,686.83, never above ×1.5
- [ ] C5: demo-eta gives all five pools an ETA and a flag; `?delay_hours=4` makes truck 2 at_risk for shipment 10

If anything doesn't match, run `python scripts/try_engine.py`. It calls every engine path and prints OK or FAIL for each.
