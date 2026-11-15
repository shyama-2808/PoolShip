"use client";

import { useState } from "react";
import { 
  ShieldCheck, 
  TrendingUp, 
  Leaf, 
  Truck, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle,
  FileText
} from "lucide-react";

export default function AdminDashboard() {
  const [kycQueue, setKycQueue] = useState([
    {
      id: 1,
      name: "Siddaganga Industrial Tools Pvt Ltd",
      type: "Shipper (MSME)",
      gstin: "29AABCU9603R1ZM",
      pan: "AABCU9603R",
      state: "Karnataka",
      status: "PENDING",
    },
    {
      id: 2,
      name: "Nanjundeshwara Roadlines & Logistics",
      type: "Transporter Fleet",
      gstin: "29AAGFN4432L1ZS",
      truckCount: "6 Trucks",
      state: "Karnataka",
      status: "PENDING",
    }
  ]);

  const verifyUser = (id: number) => {
    setKycQueue(kycQueue.filter((item) => item.id !== id));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Top Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Platform Control & Analytics</h1>
        <p className="text-sm text-slate-500 mt-1">
          Monitor corridor freight consolidation, enforce KYC/GST verification, and manage dispute resolution.
        </p>
      </div>

      {/* Analytics KPI Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">Total Consolidations (Pools)</p>
          <p className="text-2xl font-black text-slate-900">1,482</p>
          <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> +18.4% this month
          </span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">Avg. Fleet Utilization</p>
          <p className="text-2xl font-black text-sky-600">82.4%</p>
          <span className="text-xs text-slate-500">Up from 41% unpooled baseline</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">CO₂ Reductions (DEFRA)</p>
          <p className="text-2xl font-black text-emerald-600">42,850 kg</p>
          <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
            <Leaf className="w-3.5 h-3.5" /> ~1,960 Trees Equivalent
          </span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">Total Freight Spend Saved</p>
          <p className="text-2xl font-black text-indigo-600">₹64.2 Lakhs</p>
          <span className="text-xs text-slate-500">Saved by MSME shippers</span>
        </div>
      </div>

      {/* KYC / GST Verification Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <h2 className="text-lg font-bold text-slate-900">KYC & GSTIN Verification Queue</h2>
          </div>
          <span className="text-xs bg-amber-100 text-amber-800 font-semibold px-2.5 py-1 rounded-full">
            {kycQueue.length} Pending Actions
          </span>
        </div>

        {kycQueue.length === 0 ? (
          <p className="text-sm text-slate-500 py-4 text-center">All pending business verifications completed.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {kycQueue.map((item) => (
              <div key={item.id} className="py-4 flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">{item.name}</h4>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                    <span className="font-semibold text-slate-700">{item.type}</span>
                    <span>GSTIN: <span className="font-mono text-slate-800">{item.gstin}</span></span>
                    <span>State: {item.state}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => verifyUser(item.id)}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1 transition shadow-sm"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approve GSTIN
                  </button>
                  <button
                    onClick={() => verifyUser(item.id)}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1 transition"
                  >
                    <XCircle className="w-3.5 h-3.5" /> Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top Corridors Heatmap Summary */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 className="text-lg font-bold text-slate-900">Highest Volume Pooling Corridors</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-medium">
            <span>Bangalore ↔ Chennai (NH 48)</span>
            <span className="text-slate-500">412 Pools · 91% Avg Fill</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div className="bg-sky-600 h-full rounded-full" style={{ width: "91%" }} />
          </div>

          <div className="flex items-center justify-between text-xs font-medium pt-2">
            <span>Surat ↔ Mumbai / Bhiwandi</span>
            <span className="text-slate-500">388 Pools · 88% Avg Fill</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div className="bg-indigo-600 h-full rounded-full" style={{ width: "88%" }} />
          </div>

          <div className="flex items-center justify-between text-xs font-medium pt-2">
            <span>Delhi ↔ Jaipur (NH 48)</span>
            <span className="text-slate-500">295 Pools · 84% Avg Fill</span>
          </div>
          <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
            <div className="bg-teal-600 h-full rounded-full" style={{ width: "84%" }} />
          </div>
        </div>
      </div>
    </div>
  );
}
