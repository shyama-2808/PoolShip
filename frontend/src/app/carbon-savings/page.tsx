"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Leaf, 
  Truck, 
  TrendingDown, 
  Fuel, 
  TreePine, 
  ArrowRight, 
  CheckCircle2,
  BarChart3,
  Globe2,
  Calendar
} from "lucide-react";
import { mockStore, Pool } from "@/lib/mockStore";

export default function CarbonSavingsDashboard() {
  const [pools, setPools] = useState<Pool[]>([]);
  const [activeCorridorFilter, setActiveCorridorFilter] = useState<string>("ALL");

  useEffect(() => {
    const update = () => {
      setPools(mockStore.getPools());
    };
    update();
    const unsub = mockStore.subscribe(update);
    return () => unsub();
  }, []);

  const totalCo2SavedKg = pools.reduce((acc, p) => acc + (p.co2_saved_kg || 0), 0);
  const totalDieselSavedL = pools.reduce((acc, p) => acc + (p.diesel_saved_litres || 0), 0);
  const treesEquivalent = Math.round(totalCo2SavedKg / 21.77); // ~21.77 kg CO2 absorbed per mature tree/year

  const filteredPools = pools.filter((p) =>
    activeCorridorFilter === "ALL" ? true : p.corridor_name.includes(activeCorridorFilter)
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="bg-emerald-600 text-white p-2 rounded-xl">
              <Leaf className="w-5 h-5" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Carbon Savings & Green Logistics</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Quantifying environmental impact of Part-Truckload (PTL) consolidation against solitary dedicated truck baseline.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs bg-emerald-100 text-emerald-800 font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> EPA / DEFRA Diesel Emission Factor Standard
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Total CO₂ Avoided</span>
            <Leaf className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-3xl font-black text-emerald-600">{Math.round(totalCo2SavedKg).toLocaleString()} kg</p>
          <span className="text-xs text-slate-500">Across {pools.length} active consolidated pools</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Diesel Fuel Conserved</span>
            <Fuel className="w-4 h-4 text-sky-600" />
          </div>
          <p className="text-3xl font-black text-sky-600">{Math.round(totalDieselSavedL).toLocaleString()} L</p>
          <span className="text-xs text-slate-500">Based on 0.28 L/km diesel truck baseline</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Trees Equivalent</span>
            <TreePine className="w-4 h-4 text-teal-600" />
          </div>
          <p className="text-3xl font-black text-teal-600">{treesEquivalent.toLocaleString()} Trees</p>
          <span className="text-xs text-slate-500">Annual carbon absorption offset</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider">Emission Reduction</span>
            <TrendingDown className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-3xl font-black text-indigo-600">~62%</p>
          <span className="text-xs text-slate-500">Lower footprint vs 1-truck-per-shipper</span>
        </div>
      </div>

      {/* Methodology & Calculation Formula Banner */}
      <div className="bg-gradient-to-r from-emerald-950 to-slate-900 text-white rounded-2xl p-6 space-y-4">
        <h3 className="text-base font-bold text-emerald-300 flex items-center gap-2">
          <Globe2 className="w-5 h-5" /> How PoolShip Quantifies Green Freight Savings
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed max-w-3xl">
          In typical Indian logistics, 3 independent MSMEs shipping 800 kg each from Bangalore to Chennai book 3 separate partially-empty trucks, driving a combined 3 × 350 km = 1,050 km. With PoolShip, one single truck handles the consolidated load along the same corridor in 365 km (with minor detour pickups).
        </p>

        <div className="grid md:grid-cols-3 gap-4 pt-2 text-xs">
          <div className="bg-white/10 p-3 rounded-xl">
            <span className="text-emerald-400 font-bold block">1. Avoided Distance</span>
            <span className="text-slate-200">Avoided km = (Distance × Shippers) - Pooled km</span>
          </div>
          <div className="bg-white/10 p-3 rounded-xl">
            <span className="text-emerald-400 font-bold block">2. Fuel Conserved</span>
            <span className="text-slate-200">Diesel Saved = Avoided km × 0.28 L/km</span>
          </div>
          <div className="bg-white/10 p-3 rounded-xl">
            <span className="text-emerald-400 font-bold block">3. CO₂ Prevented</span>
            <span className="text-slate-200">CO₂ (kg) = Diesel Saved × 2.68 kg/L</span>
          </div>
        </div>
      </div>

      {/* Per-Pool Breakdown Table (Feature 6) */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">Per-Pool Environmental Impact Ledger</h2>
            <p className="text-xs text-slate-500">Live data calculated from confirmed booking participants</p>
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            <button
              onClick={() => setActiveCorridorFilter("ALL")}
              className={`px-3 py-1 rounded-lg font-semibold transition ${activeCorridorFilter === "ALL" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              All Corridors
            </button>
            <button
              onClick={() => setActiveCorridorFilter("Chennai")}
              className={`px-3 py-1 rounded-lg font-semibold transition ${activeCorridorFilter === "Chennai" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              Bangalore-Chennai
            </button>
            <button
              onClick={() => setActiveCorridorFilter("Bhiwandi")}
              className={`px-3 py-1 rounded-lg font-semibold transition ${activeCorridorFilter === "Bhiwandi" ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              Surat-Mumbai
            </button>
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {filteredPools.map((pool) => (
            <div key={pool.id} className="py-4 flex flex-wrap items-center justify-between gap-4 text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 text-sm">{pool.pool_code}</span>
                  <span className="text-slate-500 font-semibold">{pool.corridor_name}</span>
                </div>
                <div className="flex items-center gap-3 text-slate-500">
                  <span>Distance: {pool.total_distance_km} km</span>
                  <span>Shippers Sharing: <strong>{pool.shippers_count} MSMEs</strong></span>
                  <span>Fill Rate: <strong>{pool.overall_utilization_pct}%</strong></span>
                </div>
              </div>

              <div className="flex items-center gap-6">
                <div className="text-right">
                  <span className="text-slate-400 block text-[11px]">CO₂ Prevented</span>
                  <span className="font-black text-emerald-600 text-base">
                    {pool.co2_saved_kg} kg
                  </span>
                </div>

                <div className="text-right">
                  <span className="text-slate-400 block text-[11px]">Diesel Conserved</span>
                  <span className="font-bold text-sky-600 text-base">
                    {pool.diesel_saved_litres} L
                  </span>
                </div>

                <Link
                  href={`/tracking/${pool.shipment_ids[0] || 101}`}
                  className="bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold px-3 py-1.5 rounded-lg transition"
                >
                  View Route →
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
