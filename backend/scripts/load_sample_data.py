"""
Loads data/sample_data.json into the PoolShip database through the API.

It creates the 5 sample users (3 shippers, 2 transporters), the 5 trucks and
the 20 shipments. Safe to run more than once: anything already there is skipped.

Usage (backend must be running, e.g. `docker compose up`):
    python scripts/load_sample_data.py
    python scripts/load_sample_data.py --api http://localhost:8000/api/v1

Only uses the Python standard library, so no extra installs are needed.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "sample_data.json"


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
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    password = data["default_password"]

    try:
        call("GET", f"{api}/trucks/")
    except urllib.error.URLError as e:
        sys.exit(f"Cannot reach {api}. Is the backend running? ({e.reason})")

    # 1. Users: register, or log in if the email already exists, to learn each user's database id
    user_ids = {}
    for u in data["users"]:
        body = {k: v for k, v in u.items() if k != "key"} | {"password": password}
        status, res = call("POST", f"{api}/auth/register", body)
        if status == 201:
            user_ids[u["key"]] = res["id"]
            print(f"  + user {u['email']} (id {res['id']})")
        else:
            status, res = call("POST", f"{api}/auth/login", {"email": u["email"], "password": password})
            if status != 200:
                sys.exit(f"Could not create or log in {u['email']}: {res}")
            user_ids[u["key"]] = res["user_id"]
            print(f"  = user {u['email']} already exists (id {res['user_id']})")

    # 2. Trucks: skip any registration number that is already in the database
    _, existing = call("GET", f"{api}/trucks/")
    existing_regs = {t["registration_number"]: t["id"] for t in existing}
    truck_ids = {}
    for t in data["trucks"]:
        if t["registration_number"] in existing_regs:
            truck_ids[t["id"]] = existing_regs[t["registration_number"]]
            print(f"  = truck {t['registration_number']} already exists")
            continue
        body = {k: v for k, v in t.items() if k not in ("id", "transporter_key")}
        owner = user_ids[t["transporter_key"]]
        status, res = call("POST", f"{api}/trucks/?transporter_id={owner}", body)
        if status != 200:
            sys.exit(f"Could not create truck {t['registration_number']}: {res}")
        truck_ids[t["id"]] = res["id"]
        print(f"  + truck {t['registration_number']} {t['origin_city']} to {t['destination_city']} (id {res['id']})")

    # 3. Shipments: skip any (shipper, title) pair that is already in the database
    _, existing = call("GET", f"{api}/shipments/")
    existing_keys = {(s["shipper_id"], s["title"]) for s in existing}
    created = 0
    for s in data["shipments"]:
        owner = user_ids[s["shipper_key"]]
        if (owner, s["title"]) in existing_keys:
            print(f"  = shipment '{s['title']}' already exists")
            continue
        body = {k: v for k, v in s.items() if k not in ("id", "shipper_key")}
        status, res = call("POST", f"{api}/shipments/?shipper_id={owner}", body)
        if status != 200:
            sys.exit(f"Could not create shipment '{s['title']}': {res}")
        created += 1
        print(f"  + shipment '{s['title']}' {s['origin_address']} to {s['destination_address']} (id {res['id']})")

    print(f"\nDone. Users: {len(user_ids)}, trucks: {len(truck_ids)}, new shipments: {created}.")
    print(f"Sample login for any user: password '{password}'.")


if __name__ == "__main__":
    main()
