from typing import Any, Dict, Sequence


class CarbonCalculator:
    """
    Fuel and CO2: separate trucks versus one pooled truck.

    Without PoolShip, every shipper hires their own truck for their own trip
    ("separate trucks"). With PoolShip, one truck drives its route once and
    carries them all ("pooled truck"). Fuel = km x litres per km, and
    CO2 = litres x kg CO2 per litre. The difference is what pooling saves.
    """

    # Stated emission factors (medium-duty diesel truck, Indian freight):
    DIESEL_LITRES_PER_KM = 0.28          # about 3.57 km per litre
    KG_CO2_PER_LITRE_DIESEL = 2.68       # burning 1 L of diesel gives 2.68 kg CO2 (DEFRA / EPA)
    AVG_CO2_KG_PER_KM = DIESEL_LITRES_PER_KM * KG_CO2_PER_LITRE_DIESEL  # 0.7504 kg CO2 per km

    @classmethod
    def emission_factors(cls) -> Dict[str, Any]:
        """The numbers every result is based on, so anyone can check the maths."""
        return {
            "diesel_litres_per_km": cls.DIESEL_LITRES_PER_KM,
            "km_per_litre": round(1 / cls.DIESEL_LITRES_PER_KM, 2),
            "kg_co2_per_litre_diesel": cls.KG_CO2_PER_LITRE_DIESEL,
            "kg_co2_per_km": round(cls.AVG_CO2_KG_PER_KM, 4),
            "source": "Medium-duty diesel truck at 0.28 L/km; diesel emission factor 2.68 kg CO2/L (DEFRA / EPA)",
        }

    @classmethod
    def trip_emissions(cls, km: float) -> Dict[str, float]:
        """Diesel and CO2 for one truck driving `km` kilometres."""
        km = max(0.0, km)
        litres = km * cls.DIESEL_LITRES_PER_KM
        return {
            "km": round(km, 2),
            "diesel_litres": round(litres, 2),
            "co2_kg": round(litres * cls.KG_CO2_PER_LITRE_DIESEL, 2),
        }

    @classmethod
    def compare_trips(cls, separate_trip_km: Sequence[float], pooled_truck_km: float) -> Dict[str, Any]:
        """
        THE Task 5 function: litres, kg CO2 and percent saved for any pool.

        Args:
            separate_trip_km: each shipper's own trip length, i.e. the km their
                own truck would drive if they did not pool (one entry per shipment).
            pooled_truck_km: km the one shared truck drives (its route plus any detour).

        Returns baseline (separate trucks), pooled and saved numbers, plus the
        emission factors used. Savings never go below 0: if pooling would make
        the truck drive more than the shippers would alone, saved is 0.
        """
        n = len(separate_trip_km)
        if n == 0:
            pooled_truck_km = 0.0  # nobody on the truck, so nothing to compare

        baseline = cls.trip_emissions(sum(max(0.0, k) for k in separate_trip_km))
        pooled = cls.trip_emissions(pooled_truck_km)

        def saved(key: str) -> float:
            return round(max(0.0, baseline[key] - pooled[key]), 2)

        co2_saved = saved("co2_kg")
        pct = (co2_saved / baseline["co2_kg"] * 100.0) if baseline["co2_kg"] > 0 else 0.0

        return {
            "num_shipments": n,
            "baseline_trucks": n,
            "baseline_truck_km": baseline["km"],
            "pooled_truck_km": pooled["km"],
            "km_avoided": saved("km"),
            "baseline_diesel_litres": baseline["diesel_litres"],
            "pooled_diesel_litres": pooled["diesel_litres"],
            "diesel_saved_litres": saved("diesel_litres"),
            "baseline_co2_kg": baseline["co2_kg"],
            "pooled_co2_kg": pooled["co2_kg"],
            "co2_saved_kg": co2_saved,
            # Fuel and CO2 move together (CO2 = litres x 2.68), so the two percentages are equal
            "fuel_saved_percentage": round(pct, 1),
            "co2_reduction_percentage": round(pct, 1),
            "emission_factors": cls.emission_factors(),
        }

    @classmethod
    def calculate_savings(
        cls,
        pooled_route_distance_km: float,
        num_participants: int,
        detour_km: float = 0.0
    ) -> Dict[str, Any]:
        """
        Shortcut when you only know the truck's route: assume each of the
        `num_participants` shippers would have driven the whole route alone.

        Args:
            pooled_route_distance_km: Distance driven by the single consolidated truck.
            num_participants: Number of independent shippers sharing this truck.
            detour_km: Extra kilometers incurred due to multiple pick-up/drop-off stops.
        """
        n = max(0, num_participants)
        return cls.compare_trips([pooled_route_distance_km] * n, pooled_route_distance_km + detour_km)
