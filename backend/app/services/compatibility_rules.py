"""
Compatibility rules: which goods may share a truck (Task 7).

How it works, in three steps:

1. Every shipment is put into one or more GOODS GROUPS, from its goods_type text
   (e.g. "chemicals") and its flags (is_perishable, is_hazardous, is_fragile,
   temperature_class). Example: paint thinner with goods_type "chemicals" -> {"hazardous"}.

2. The RULE TABLE lists pairs of groups and what happens when they meet:
     - "block":   they can't share a truck at all (the pool is rejected, with the reason)
     - "caution": they may share, but the loader gets a handling note

3. Two temperature-controlled shipments must also want the SAME temperature,
   because a refrigerated truck keeps one temperature for its whole hold.

Shipments can be the engine's ShipmentItem objects or plain dicts; both work.
"""
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# 1. Goods groups
# ---------------------------------------------------------------------------
# goods_type words (lower case) that put a shipment in each group.
# A flag can also put a shipment in a group (see groups_of below).
GOODS_GROUPS: Dict[str, Dict[str, Any]] = {
    "perishable": {
        "label": "perishable food",
        "goods_types": {"perishable", "food", "fruits", "vegetables", "dairy", "meat", "fish", "frozen food"},
    },
    "dry_food": {
        "label": "grains and spices",
        "goods_types": {"grains", "spices", "pulses", "flour", "sugar", "tea", "coffee"},
    },
    "medicine": {
        "label": "medicines",
        "goods_types": {"pharmaceuticals", "pharma", "medicines", "medical"},
    },
    "hazardous": {
        "label": "hazardous chemicals",
        "goods_types": {"chemicals", "hazardous", "paint", "pesticides", "fertilizer", "fuel", "gas", "acids"},
    },
    "construction": {
        "label": "heavy construction material",
        "goods_types": {"construction", "cement", "granite", "stone", "marble", "bricks", "sand"},
    },
    "fragile": {
        "label": "fragile goods",
        "goods_types": {"glassware", "glass", "ceramics", "electronics"},
    },
    "temperature_controlled": {
        "label": "temperature-controlled goods",
        "goods_types": set(),  # only from temperature_class
    },
}

# ---------------------------------------------------------------------------
# 2. Rule table: goods that can't (or can only carefully) share a truck
# ---------------------------------------------------------------------------
RULES: List[Dict[str, str]] = [
    {"a": "perishable", "b": "hazardous", "severity": "block",
     "why": "chemical leaks or fumes can spoil food"},
    {"a": "dry_food", "b": "hazardous", "severity": "block",
     "why": "chemical leaks or fumes can contaminate food grains and spices"},
    {"a": "medicine", "b": "hazardous", "severity": "block",
     "why": "chemical leaks or fumes can contaminate medicines"},
    {"a": "temperature_controlled", "b": "hazardous", "severity": "block",
     "why": "chemicals must not ride in a closed refrigerated hold"},
    {"a": "fragile", "b": "construction", "severity": "caution",
     "why": "heavy stone or building material can crush fragile goods: load the fragile goods last, "
            "on top or in a separate bay, and strap them down"},
]

# Temperature classes and what each needs from the truck
TEMPERATURE_CLASSES: Dict[str, str] = {
    "ambient": "no temperature control",
    "chilled": "refrigerated truck at 2 to 8 °C",
    "frozen": "freezer truck at -18 °C or colder",
}

# Handling notes shown for a flagged shipment, whatever it rides with
FLAG_NOTES: Dict[str, str] = {
    "fragile": "Fragile: load last, keep on top, do not stack anything on it",
    "chilled": "Chilled: needs a refrigerated truck at 2 to 8 °C",
    "frozen": "Frozen: needs a freezer truck at -18 °C or colder",
    "hazardous": "Hazardous: needs hazard labels and a spill kit on board",
}


def _get(item: Any, key: str, default: Any = None) -> Any:
    """Read a field from a dict or an object."""
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _id(item: Any) -> Any:
    return _get(item, "id", _get(item, "shipment_id"))


def temperature_class(item: Any) -> str:
    value = (_get(item, "temperature_class") or "ambient").lower()
    return value if value in TEMPERATURE_CLASSES else "ambient"


def groups_of(item: Any) -> Set[str]:
    """Which goods groups a shipment belongs to (from goods_type and flags)."""
    goods = (_get(item, "goods_type") or "").strip().lower()
    groups = {name for name, g in GOODS_GROUPS.items() if goods in g["goods_types"]}
    if _get(item, "is_perishable"):
        groups.add("perishable")
    if _get(item, "is_hazardous"):
        groups.add("hazardous")
    if _get(item, "is_fragile"):
        groups.add("fragile")
    if temperature_class(item) != "ambient":
        groups.add("temperature_controlled")
    return groups


def flags_of(item: Any) -> List[str]:
    """Flags worth telling the loader about: fragile, chilled, frozen, hazardous."""
    groups = groups_of(item)
    flags = []
    if "fragile" in groups:
        flags.append("fragile")
    if temperature_class(item) != "ambient":
        flags.append(temperature_class(item))
    if "hazardous" in groups:
        flags.append("hazardous")
    return flags


def _describe(item: Any, group: str) -> str:
    goods = _get(item, "goods_type")
    label = GOODS_GROUPS[group]["label"]
    return f"shipment {_id(item)} ({goods})" if goods else f"shipment {_id(item)} ({label})"


def check_pair(a: Any, b: Any) -> List[Dict[str, Any]]:
    """Every rule broken when shipments a and b share a truck (empty list = fine)."""
    ga, gb = groups_of(a), groups_of(b)
    found: List[Dict[str, Any]] = []
    for rule in RULES:
        for x, y, gx, gy in ((a, b, ga, gb), (b, a, gb, ga)):
            if rule["a"] in gx and rule["b"] in gy:
                found.append({
                    "shipment_ids": [_id(x), _id(y)],
                    "severity": rule["severity"],
                    "rule": f"{rule['a']} + {rule['b']}",
                    "reason": (f"{GOODS_GROUPS[rule['a']]['label'].capitalize()} cannot be pooled with "
                               f"{GOODS_GROUPS[rule['b']]['label']}: {rule['why']}"
                               if rule["severity"] == "block" else
                               f"{GOODS_GROUPS[rule['a']]['label'].capitalize()} riding with "
                               f"{GOODS_GROUPS[rule['b']]['label']}: {rule['why']}"),
                })
                break  # one hit per rule is enough
    ta, tb = temperature_class(a), temperature_class(b)
    if "ambient" not in (ta, tb) and ta != tb:
        found.append({
            "shipment_ids": [_id(a), _id(b)],
            "severity": "block",
            "rule": "temperature mismatch",
            "reason": (f"Temperature mismatch: shipment {_id(a)} is {ta} and shipment {_id(b)} is {tb}, "
                       "but a truck keeps one temperature for its whole hold"),
        })
    return found


def check_candidate(existing: Iterable[Any], candidate: Any) -> Tuple[bool, str, List[str]]:
    """
    Can `candidate` join a truck that already holds `existing`?
    Returns (ok, reason, cautions). `reason` is "Compatible" when ok.
    """
    cautions: List[str] = []
    for other in existing:
        for hit in check_pair(candidate, other):
            if hit["severity"] == "block":
                return False, f"{hit['reason']} (clashes with shipment {_id(other)})", []
            cautions.append(hit["reason"])
    return True, "Compatible", cautions


def check_pool(items: List[Any]) -> Dict[str, Any]:
    """
    Check a whole pool before it is created.
    Every pair of shipments is checked against the rule table.
    compatible is False when any pair is blocked; `reason` then names the first clash.
    """
    conflicts: List[Dict[str, Any]] = []
    cautions: List[Dict[str, Any]] = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            for hit in check_pair(a, b):
                (conflicts if hit["severity"] == "block" else cautions).append(hit)
    flags = [
        {"shipment_id": _id(s), "flags": f, "handling": [FLAG_NOTES[x] for x in f]}
        for s in items if (f := flags_of(s))
    ]
    if conflicts:
        first = conflicts[0]
        reason = (f"Shipments {first['shipment_ids'][0]} and {first['shipment_ids'][1]} can't share a truck. "
                  f"{first['reason']}")
    else:
        reason = "All shipments can share a truck"
    return {
        "compatible": not conflicts,
        "reason": reason,
        "conflicts": conflicts,
        "cautions": cautions,
        "flags": flags,
    }


def rule_table() -> Dict[str, Any]:
    """The rules in a readable form (for GET /engine/compatibility/rules)."""
    return {
        "goods_groups": [
            {"group": name, "label": g["label"], "goods_types": sorted(g["goods_types"])}
            for name, g in GOODS_GROUPS.items()
        ],
        "flag_groups": {
            "is_perishable": "perishable",
            "is_hazardous": "hazardous",
            "is_fragile": "fragile",
            "temperature_class chilled/frozen": "temperature_controlled",
        },
        "rules": [
            {"group_a": r["a"], "group_b": r["b"], "severity": r["severity"], "why": r["why"]} for r in RULES
        ] + [{"group_a": "chilled", "group_b": "frozen", "severity": "block",
              "why": "a truck keeps one temperature for its whole hold"}],
        "temperature_classes": TEMPERATURE_CLASSES,
        "flag_notes": FLAG_NOTES,
    }


def first_block(existing: Iterable[Any], candidate: Any) -> Optional[str]:
    """The reason `candidate` can't join `existing`, or None if it can."""
    ok, reason, _ = check_candidate(existing, candidate)
    return None if ok else reason
