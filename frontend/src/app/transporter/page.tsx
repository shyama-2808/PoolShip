"use client";

import { useState } from "react";
import { 
  Truck, 
  Plus, 
  MapPin, 
  Gauge, 
  CheckCircle, 
  AlertTriangle,
  RotateCcw,
  IndianRupee,
  Layers
} from "lucide-react";

export default function TransporterDashboard() {
  const [trucks, setTrucks] = useState([
    {
      id: 1,
      regNo: "KA-01-MJ-4491",
      type: "14ft Eicher Canter (4 Ton)",
      route: "Bangalore → Chennai",
      date: "Tomorrow, 06:00 AM",
      capacityKg: 4000,
      capacityCbm: 16.0,
      bookedKg: 3100,
      bookedCbm: 13.2,
      utilizationPct: 78,
      earnings: "₹18,500",
      shippersCount: 3,
      isReturnTripCandidate: true,
    },
    {
      id: 2,
      regNo: "MH-12-PQ-8820",
      type: "Tata 407 (2.5 Ton)",
      route: "Pune → Mumbai (JNPT Port)",
      date: "Nov 16, 09:00 AM",
      capacityKg: 2500,
      capacityCbm: 10.0,
      bookedKg: 1850,
      bookedCbm: 8.0,
      utilizationPct: 74,
      earnings: "₹11,200",
      shippersCount: 2,
      isReturnTripCandidate: false,
    }
  ]);

  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Top Banner */}
      <div className="border-b border-slate-200 pb-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Transporter Fleet Hub</h1>
          <p className="text-sm text-slate-500 mt-1">
            Fill deadhead cargo space, aggregate pooled shipments along your route, and eliminate empty return trips.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(!showAddModal)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2 rounded-xl text-sm shadow transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Add Truck / Route
        </button>
      </div>

      {/* Fleet & Active Route Capacity Meter */}
      <div className="grid md:grid-cols-2 gap-6">
        {trucks.map((truck) => (
          <div key={truck.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">{truck.type}</span>
                <h3 className="text-lg font-bold text-slate-900">{truck.regNo}</h3>
              </div>
              <span className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold px-3 py-1 rounded-full">
                {truck.shippersCount} Shippers Pooled
              </span>
            </div>

            <div className="space-y-1 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-slate-400" />
                <span className="font-semibold text-slate-800">{truck.route}</span>
                <span className="text-slate-400">({truck.date})</span>
              </div>
            </div>

            {/* Visual Fill Meter */}
            <div className="space-y-2 bg-slate-50 p-4 rounded-xl border border-slate-100">
              <div className="flex justify-between items-center text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <Gauge className="w-4 h-4 text-sky-500" /> Truck Cargo Hold Fill Rate:
                </span>
                <span className="font-bold text-indigo-600">{truck.utilizationPct}% Full</span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    truck.utilizationPct >= 80 ? "bg-emerald-500" : "bg-sky-500"
                  }`}
                  style={{ width: `${truck.utilizationPct}%` }}
                />
              </div>

              <div className="flex justify-between text-[11px] text-slate-500 pt-1">
                <span>Weight: {truck.bookedKg} / {truck.capacityKg} kg</span>
                <span>Vol: {truck.bookedCbm} / {truck.capacityCbm} m³</span>
                <span>Remaining: {truck.capacityKg - truck.bookedKg} kg</span>
              </div>
            </div>

            {/* Earnings & Return Trip Notice */}
            <div className="flex items-center justify-between pt-2">
              <div>
                <span className="text-xs text-slate-400 block">Total Pool Revenue</span>
                <span className="text-lg font-extrabold text-slate-900 flex items-center">
                  {truck.earnings}
                </span>
              </div>

              {truck.isReturnTripCandidate && (
                <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                  <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
                  <span>Return match: Chennai → BLR (2 shippers waiting)</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
