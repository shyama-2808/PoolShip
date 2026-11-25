"""
Calls every /engine endpoint once with sample data and prints a short summary.
Use it to check the logistics engine works end to end through the API.

Usage (backend must be running):
    python scripts/try_engine.py
    python scripts/try_engine.py --api http://localhost:8000/api/v1

Only uses the Python standard library, so no extra installs are needed.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request


def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000/api/v1", help="API base URL")
    api = ap.parse_args().api.rstrip("/")

    try:
        _, spec = call("GET", f"{api}/openapi.json")
    except urllib.error.URLError as e:
        sys.exit(f"Cannot reach {api}. Is the backend running? ({e.reason})")

    failures = 0

    def report(name, status, result, summary):
        nonlocal failures
        ok = status == 200
        failures += not ok
        print(f"[{'OK' if ok else 'FAIL'}] {name}")
        print("      " + (summary(result) if ok else f"HTTP {status}: {result}"))

    # 1. Every POST /engine/... endpoint, using the example shipped with it
    summaries = {
        "/engine/compatibility": lambda r: f"compatible={r['compatible']} ({r['reason']})",
        "/engine/optimize-load": lambda r: (
            f"packed {[i['id'] for i in r['packed_items']]}, "
            f"left out {[(i['id'], i['reason']) for i in r['unpacked_items']]}, "
            f"utilisation {r['overall_utilization_pct']}%"),
        "/engine/assign-trucks": lambda r: "; ".join(
            [f"truck {t['truck_id']} takes {t['shipment_ids']} ({t['overall_utilization_pct']}% full)"
             for t in r["trucks"]] + [f"left over {[i['id'] for i in r['leftover_items']]}"]),
        "/engine/cost-split": lambda r: f"trip Rs {r['total_trip_cost']} by {r['split_method']}: " + ", ".join(
            f"shipment {s['shipment_id']} pays Rs {s['allocated_cost']}" for s in r["shares"]),
        "/engine/carbon": lambda r: f"{r['co2_saved_kg']} kg CO2 and {r['diesel_saved_litres']} L diesel saved",
        "/engine/carbon/compare": lambda r: (
            f"separate {r['baseline_diesel_litres']} L vs pooled {r['pooled_diesel_litres']} L: "
            f"{r['co2_saved_kg']} kg CO2 saved ({r['co2_reduction_percentage']}%)"),
        "/engine/route/distance": lambda r: f"{r['straight_line_km']} km straight, ~{r['estimated_road_km']} km by road",
        "/engine/route/corridor-check": lambda r: (
            f"on_corridor={r['on_corridor']} (pickup {r['pickup_offset_km']} km off, drop {r['drop_offset_km']} km off)"),
        "/engine/route/road-route": lambda r: f"{r['distance_km']} km, {r['duration_minutes']} min (source: {r['source']})",
        "/engine/route/match": lambda r: (
            f"matched {[m['shipment_id'] for m in r['matched']]}, rejected {len(r['rejected'])}"),
        "/engine/route/pools": lambda r: (
            f"pools {[p['shipment_ids'] for p in r['pools']]}, "
            f"unmatched {[u['shipment_id'] for u in r['unmatched']]}"),
        "/engine/compatibility/pool": lambda r: f"compatible={r['compatible']} ({r['reason']})",
        "/engine/route/optimize-stops": lambda r: (
            f"{r['total_km']} km in best order vs {r['as_listed_km']} km as listed "
            f"(saves {r['km_saved']} km, {r['method']}, {r['distance_source']})"),
        "/engine/return-trip": lambda r: (
            f"home from {r['return_route']['from']['place']} at {r['return_route']['departs_at']}: "
            f"carries {[m['shipment_id'] for m in r['matched']]}, earns Rs {r['return_trip_earnings']}"),
        "/engine/price": lambda r: (
            f"base Rs {r['base_price']} x {r['multiplier']} = Rs {r['price']}"
            + (f" (capped {r['capped']})" if r["capped"] else "")),
        "/engine/eta": lambda r: (
            f"ETA {r['eta']}, flag {r['delay_flag']}, likely late {r['late_shipments']}"),
        "/engine/recurring/expand": lambda r: (
            f"{len(r['occurrences'])} repeat shipments: {[o['id'] for o in r['occurrences']]}"),
        "/engine/recurring/pools": lambda r: "; ".join(
            f"recurring {x['recurring_id']} ({x['repeats']}): {x['pooled']} of {x['occurrences']} pooled"
            for x in r["recurring"]),
        "/engine/hub-route": lambda r: r["summary"],
        "/engine/plan-pool": lambda r: (
            f"packed {[i['id'] for i in r['load']['packed_items']]}, trip Rs {r['total_trip_cost']}, "
            f"CO2 saved {r['carbon']['co2_saved_kg']} kg"),
    }
    for full_path, ops in spec["paths"].items():
        path = full_path[full_path.find("/engine"):]  # drop the "/api/v1" prefix
        if "/engine" not in full_path or "post" not in ops:
            continue
        examples = ops["post"]["requestBody"]["content"]["application/json"].get("examples", {})
        body = next(iter(examples.values()))["value"]
        status, result = call("POST", f"{api}{path}", body)
        report(f"POST {path}", status, result, summaries.get(path, lambda r: "ok"))

    # 2. Sample data + the one-click demo for each sample truck
    status, data = call("GET", f"{api}/engine/sample-data")
    report("GET /engine/sample-data", status, data,
           lambda d: f"{len(d['shipments'])} shipments, {len(d['trucks'])} trucks, {len(d['users'])} users")
    for t in (data["trucks"] if status == 200 else []):
        status, r = call("GET", f"{api}/engine/demo/{t['id']}")
        report(f"GET /engine/demo/{t['id']} ({t['origin_city']} to {t['destination_city']})", status, r,
               lambda r: (
                   f"on route {[m['shipment_id'] for m in r['route']['matched']]}, "
                   f"packed {[i['id'] for i in r['load']['packed_items']]}, "
                   f"left out {[(i['id'], i['reason']) for i in r['load']['unpacked_items']]}, "
                   f"trip Rs {r['total_trip_cost']}, CO2 saved {r['carbon']['co2_saved_kg']} kg"))

    status, r = call("GET", f"{api}/engine/demo-pools")
    report("GET /engine/demo-pools (group all sample shipments)", status, r,
           lambda r: (f"pools {[p['shipment_ids'] for p in r['pools']]}, "
                      f"unmatched {[(u['shipment_id'], u['reason']) for u in r['unmatched']]}"))

    # 3. Phase 3 one-click demos
    for t in (data["trucks"] if status == 200 else []):
        s, r = call("GET", f"{api}/engine/demo-return/{t['id']}")
        report(f"GET /engine/demo-return/{t['id']} (way home)", s, r,
               lambda r: (f"carries {[m['shipment_id'] for m in r['matched']]} home, "
                          f"{r['load']['overall_utilization_pct']}% full, earns Rs {r['return_trip_earnings']}"))
    s, r = call("GET", f"{api}/engine/demo-price/2")
    report("GET /engine/demo-price/2 (same shipment, different situations)", s, r,
           lambda r: "; ".join(f"{x['scenario'].split(':')[0]}: Rs {x['price']}" for x in r["scenarios"]))
    s, r = call("GET", f"{api}/engine/demo-eta")
    report("GET /engine/demo-eta (every sample pool)", s, r,
           lambda r: "; ".join(f"truck {p['truck_id']} ETA {p['eta'][:16]} {p['delay_flag']}" for p in r))

    # 4. Phase 4 one-click demos
    s, r = call("GET", f"{api}/engine/demo-recurring")
    report("GET /engine/demo-recurring (repeats for 1 to 7 Dec enter pools)", s, r,
           lambda r: "; ".join(f"recurring {x['recurring_id']}: {x['pooled']} of {x['occurrences']} pooled"
                               for x in r["recurring"]))
    s, r = call("GET", f"{api}/engine/demo-hub/20")
    report("GET /engine/demo-hub/20 (Bengaluru to Kolkata, no direct truck)", s, r, lambda r: r["summary"])

    print(f"\n{'All engine endpoints work.' if failures == 0 else f'{failures} call(s) failed.'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
