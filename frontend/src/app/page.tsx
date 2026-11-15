"use client";

import { useState } from "react";
import Link from "next/link";
import { 
  Truck, 
  Leaf, 
  DollarSign, 
  Route, 
  ShieldCheck, 
  Boxes, 
  ArrowRight, 
  CheckCircle2, 
  TrendingUp,
  MapPin,
  Clock
} from "lucide-react";

export default function HomePage() {
  const [weight, setWeight] = useState(1500); // 1.5 tons
  const [distance, setDistance] = useState(350); // 350 km (e.g. Bangalore -> Chennai)

  // Quick live calculator
  const fullTruckCost = distance * 45; // ~₹15,750
  const pooledShare = Math.round((weight / 4000) * fullTruckCost);
  const savings = fullTruckCost - pooledShare;
  const co2AvoidedKg = Math.round(distance * 0.28 * 2.68 * 0.65); // ~65% trip reduction

  return (
    <div className="space-y-16 pb-20">
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-sky-50 via-white to-slate-50 border-b border-slate-200 py-16 sm:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <div className="inline-flex items-center gap-2 bg-sky-100 text-sky-800 text-xs font-semibold px-3 py-1.5 rounded-full">
            <Leaf className="w-3.5 h-3.5 text-emerald-600" />
            Empowering India's ₹1,00,000 Cr MSME Part-Truckload Market
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl mx-auto leading-tight">
            Stop paying for <span className="text-sky-600">empty air</span> in freight trucks.
          </h1>

          <p className="text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            PoolShip connects small businesses shipping along similar corridors to share one truck, split costs transparently, and slash carbon emissions.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/shipper"
              className="bg-sky-600 hover:bg-sky-700 text-white font-semibold px-6 py-3.5 rounded-xl shadow-md transition flex items-center gap-2"
            >
              Post a Shipment <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/transporter"
              className="bg-white hover:bg-slate-50 text-slate-700 font-semibold px-6 py-3.5 rounded-xl border border-slate-300 shadow-sm transition flex items-center gap-2"
            >
              List Truck & Routes <Truck className="w-4 h-4 text-sky-600" />
            </Link>
          </div>

          {/* Quick Metrics Ribbon */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto pt-10">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-sky-600">30% – 50%</p>
              <p className="text-xs text-slate-500 mt-1 font-medium">Lower Freight Cost</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-emerald-600">85%+</p>
              <p className="text-xs text-slate-500 mt-1 font-medium">Truck Space Utilization</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-teal-600">~60%</p>
              <p className="text-xs text-slate-500 mt-1 font-medium">Carbon Emissions Cut</p>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
              <p className="text-2xl font-bold text-indigo-600">100%</p>
              <p className="text-xs text-slate-500 mt-1 font-medium">GST & Digital POD Verified</p>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Savings & Cost-Split Simulator */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden grid md:grid-cols-12">
          <div className="p-8 md:col-span-6 space-y-6">
            <div>
              <span className="text-xs uppercase tracking-wider font-bold text-sky-600 bg-sky-50 px-2.5 py-1 rounded-md">
                Live Cost Split & CO₂ Simulator
              </span>
              <h2 className="text-2xl font-bold text-slate-900 mt-2">
                See what your business saves per trip
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Based on ton-kilometer proportional consolidation vs. dedicated FTL hire.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm font-medium mb-1">
                  <span>Shipment Weight</span>
                  <span className="text-sky-600 font-bold">{weight} kg ({ (weight / 1000).toFixed(1) } tons)</span>
                </div>
                <input
                  type="range"
                  min="200"
                  max="3500"
                  step="100"
                  value={weight}
                  onChange={(e) => setWeight(Number(e.target.value))}
                  className="w-full accent-sky-600"
                />
              </div>

              <div>
                <div className="flex justify-between text-sm font-medium mb-1">
                  <span>Route Distance (e.g., Bangalore to Chennai)</span>
                  <span className="text-sky-600 font-bold">{distance} km</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="1200"
                  step="25"
                  value={distance}
                  onChange={(e) => setDistance(Number(e.target.value))}
                  className="w-full accent-sky-600"
                />
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
              <span>Standard 4-ton Canter baseline</span>
              <span>Transparent Formula: (Weight × Dist) / Σ(Ton-Km)</span>
            </div>
          </div>

          <div className="bg-slate-900 text-white p-8 md:col-span-6 flex flex-col justify-between space-y-6">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Consolidation Economics</p>
              
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
                  <p className="text-xs text-slate-400">Dedicated Truck (Alone)</p>
                  <p className="text-xl font-bold text-red-400 line-through mt-1">₹{fullTruckCost.toLocaleString()}</p>
                </div>
                <div className="bg-sky-950/60 p-4 rounded-xl border border-sky-600/40">
                  <p className="text-xs text-sky-300">Your Pooled Share</p>
                  <p className="text-2xl font-black text-emerald-400 mt-1">₹{pooledShare.toLocaleString()}</p>
                </div>
              </div>

              <div className="mt-6 bg-slate-800/50 p-4 rounded-xl border border-slate-700 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    <DollarSign className="w-4 h-4 text-emerald-400" /> Direct Spend Saved:
                  </span>
                  <span className="font-bold text-emerald-400">₹{savings.toLocaleString()} ({Math.round((savings / fullTruckCost) * 100)}%)</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-300 flex items-center gap-1.5">
                    <Leaf className="w-4 h-4 text-emerald-400" /> CO₂ Avoided:
                  </span>
                  <span className="font-bold text-emerald-400">{co2AvoidedKg} kg CO₂</span>
                </div>
              </div>
            </div>

            <Link
              href="/shipper"
              className="w-full text-center bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-3 rounded-xl transition"
            >
              Start Pooling Shipments Now
            </Link>
          </div>
        </div>
      </section>

      {/* Core Features Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <h2 className="text-3xl font-extrabold text-slate-900">Engineered for Indian Logistics</h2>
          <p className="text-slate-600 text-base">
            Every feature is tailored to MSME constraints, driver trust, and highway corridor efficiencies.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition">
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center font-bold">
              <Boxes className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Bin-Packing & Capacity Engine</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Automated 3D load consolidation packs trucks to optimal fill rate while obeying weight, volume, and fragile cargo bounds.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition">
            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
              <Route className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">Corridor Route Matching</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              PostGIS-powered corridor algorithms group shipments traveling along common highway trunks (e.g., NH48 Bangalore-Mumbai).
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3 hover:shadow-md transition">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900">GST, OTP & Digital POD</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Zero stranger danger. Validated GSTIN credentials, photo proof-of-delivery, and OTP releases guarantee load security.
            </p>
          </div>
        </div>
      </section>

      {/* Role Navigation Portal */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-slate-100 p-8 rounded-3xl border border-slate-200 space-y-6">
          <h3 className="text-xl font-bold text-slate-800 text-center">Explore Dashboards by Persona</h3>
          <div className="grid md:grid-cols-3 gap-4">
            <Link
              href="/shipper"
              className="bg-white p-5 rounded-xl border border-slate-200 hover:border-sky-500 transition group flex flex-col justify-between"
            >
              <div>
                <span className="text-xs font-bold text-sky-600 uppercase">Shippers (MSMEs)</span>
                <h4 className="text-base font-bold text-slate-900 mt-1">Post Cargo & Join Pools</h4>
                <p className="text-xs text-slate-500 mt-2">Enter dimensions, see matched trucks, track fair cost distribution.</p>
              </div>
              <div className="mt-4 text-xs font-semibold text-sky-600 flex items-center gap-1 group-hover:translate-x-1 transition">
                Open Shipper Portal <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </Link>

            <Link
              href="/transporter"
              className="bg-white p-5 rounded-xl border border-slate-200 hover:border-indigo-500 transition group flex flex-col justify-between"
            >
              <div>
                <span className="text-xs font-bold text-indigo-600 uppercase">Transporters & Drivers</span>
                <h4 className="text-base font-bold text-slate-900 mt-1">Monetize Empty Space</h4>
                <p className="text-xs text-slate-500 mt-2">List empty corridors, accept partial consignments, eliminate deadhead return trips.</p>
              </div>
              <div className="mt-4 text-xs font-semibold text-indigo-600 flex items-center gap-1 group-hover:translate-x-1 transition">
                Open Transporter Portal <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </Link>

            <Link
              href="/admin"
              className="bg-white p-5 rounded-xl border border-slate-200 hover:border-emerald-500 transition group flex flex-col justify-between"
            >
              <div>
                <span className="text-xs font-bold text-emerald-600 uppercase">Admin & Oversight</span>
                <h4 className="text-base font-bold text-slate-900 mt-1">Platform Health & KYC</h4>
                <p className="text-xs text-slate-500 mt-2">Verify business GSTINs, monitor platform CO₂ savings, oversee dispute resolution.</p>
              </div>
              <div className="mt-4 text-xs font-semibold text-emerald-600 flex items-center gap-1 group-hover:translate-x-1 transition">
                Open Admin Dashboard <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
