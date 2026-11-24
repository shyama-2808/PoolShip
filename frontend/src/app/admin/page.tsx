"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  ShieldCheck, 
  TrendingUp, 
  Leaf, 
  Truck, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle,
  FileText,
  UserCheck,
  Scale,
  Building,
  RefreshCw,
  Search,
  MessageSquare
} from "lucide-react";
import { mockStore, User, Dispute, Pool, Shipment, Truck as TruckType } from "@/lib/mockStore";

export default function AdminDashboard() {
  const [users, setUsers] = useState<User[]>([]);
  const [disputes, setDisputes] = useState<Dispute[]>([]);
  const [pools, setPools] = useState<Pool[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [trucks, setTrucks] = useState<TruckType[]>([]);

  // Resolution Notes for disputes
  const [resolvingDisputeId, setResolvingDisputeId] = useState<number | null>(null);
  const [adminNotes, setAdminNotes] = useState("");

  useEffect(() => {
    const update = () => {
      setUsers(mockStore.getUsers());
      setDisputes(mockStore.getDisputes());
      setPools(mockStore.getPools());
      setShipments(mockStore.getShipments());
      setTrucks(mockStore.getTrucks());
    };
    update();
    const unsub = mockStore.subscribe(update);
    return () => unsub();
  }, []);

  const unverifiedUsers = users.filter((u) => !u.is_verified);
  const totalCo2Kg = pools.reduce((acc, p) => acc + (p.co2_saved_kg || 0), 0);
  const totalSpendSaved = shipments.reduce((acc, s) => acc + (s.allocated_cost ? s.allocated_cost * 0.45 : 0), 0);
  const avgUtilization = pools.length > 0 
    ? Math.round(pools.reduce((acc, p) => acc + (p.overall_utilization_pct || 0), 0) / pools.length) 
    : 78;

  const handleApproveKyc = (userId: number) => {
    mockStore.updateUser({ id: userId, is_verified: true });
    alert("GSTIN and business credentials verified! User can now book pool shares.");
  };

  const handleRejectKyc = (userId: number) => {
    if (confirm("Reject business KYC?")) {
      mockStore.updateUser({ id: userId, is_verified: false });
    }
  };

  const handleResolveDispute = (id: number, status: "APPROVED" | "REJECTED") => {
    mockStore.updateDisputeStatus(id, status, adminNotes || "Adjudicated by platform operations surveyor.");
    setResolvingDisputeId(null);
    setAdminNotes("");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Top Header */}
      <div className="border-b border-slate-200 pb-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="bg-emerald-600 text-white p-2 rounded-xl font-bold">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Admin Platform & Trust Desk</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Oversee KYC/GSTIN verification, resolve freight damage disputes, and analyze fleet efficiency metrics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs bg-slate-100 text-slate-700 font-bold px-3 py-1.5 rounded-lg border border-slate-200">
            {unverifiedUsers.length} Pending Verifications · {disputes.filter((d) => d.status === "UNDER_INVESTIGATION").length} Active Claims
          </span>
        </div>
      </div>

      {/* Analytics KPI Ribbon (Feature 13) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">Total Consolidations (Pools)</p>
          <p className="text-3xl font-black text-slate-900">{pools.length}</p>
          <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3.5 h-3.5" /> High fill corridor routes
          </span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">Avg. Fleet Fill Rate</p>
          <p className="text-3xl font-black text-sky-600">{avgUtilization}%</p>
          <span className="text-xs text-slate-500">vs 40% traditional empty runs</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">CO₂ Reductions (DEFRA)</p>
          <p className="text-3xl font-black text-emerald-600">{Math.round(totalCo2Kg)} kg</p>
          <span className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
            <Leaf className="w-3.5 h-3.5" /> ~{Math.round(totalCo2Kg / 21.77)} Trees Equivalent
          </span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-1">
          <p className="text-xs font-semibold uppercase text-slate-400">Est. MSME Freight Saved</p>
          <p className="text-3xl font-black text-indigo-600">₹{Math.round(totalSpendSaved).toLocaleString()}</p>
          <span className="text-xs text-slate-500">Across {shipments.length} consignments</span>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* KYC & GSTIN Verification Queue (Feature 8) */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Building className="w-5 h-5 text-emerald-600" />
              <h2 className="text-base font-bold text-slate-900">KYC & GSTIN Verification Queue</h2>
            </div>
            <span className="text-xs bg-amber-100 text-amber-800 font-bold px-2.5 py-0.5 rounded-full">
              {unverifiedUsers.length} Pending
            </span>
          </div>

          <p className="text-xs text-slate-500">
            In accordance with platform safety policies, businesses with unverified GSTIN are blocked from confirming pool bookings.
          </p>

          {unverifiedUsers.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs bg-slate-50 rounded-xl">
              All registered MSME shippers and transporters are verified.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 space-y-3">
              {unverifiedUsers.map((u) => (
                <div key={u.id} className="pt-3 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div>
                    <h4 className="font-bold text-slate-900">{u.company_name || u.full_name}</h4>
                    <div className="text-slate-500 space-y-0.5 mt-0.5">
                      <p>Role: <strong className="text-slate-700">{u.role}</strong> · Email: {u.email}</p>
                      <p>GSTIN: <span className="font-mono text-slate-900 font-bold">{u.gst_number || "07AAAAA0000A1Z5"}</span></p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleApproveKyc(u.id)}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded-lg transition shadow-sm flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> Approve GSTIN
                    </button>
                    <button
                      onClick={() => handleRejectKyc(u.id)}
                      className="bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold px-2.5 py-1.5 rounded-lg transition"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Dispute Resolution Desk (Feature 12) */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Scale className="w-5 h-5 text-red-600" />
              <h2 className="text-base font-bold text-slate-900">Cargo Claims & Dispute Desk</h2>
            </div>
            <span className="text-xs bg-red-100 text-red-800 font-bold px-2.5 py-0.5 rounded-full">
              {disputes.length} Total Claims
            </span>
          </div>

          <div className="space-y-3 max-h-[420px] overflow-y-auto">
            {disputes.map((d) => (
              <div key={d.id} className="p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-sm">Claim #{d.id}: {d.claim_type}</span>
                  <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                    d.status === "APPROVED" ? "bg-emerald-100 text-emerald-800" :
                    d.status === "REJECTED" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"
                  }`}>
                    {d.status}
                  </span>
                </div>

                <div className="text-slate-600 space-y-0.5">
                  <p><strong>Claimant:</strong> {d.shipper_name} · <strong>Against:</strong> {d.transporter_name}</p>
                  <p><strong>Amount:</strong> ₹{d.claimed_amount.toLocaleString()}</p>
                  <p className="italic text-slate-500">"{d.description}"</p>
                  {d.admin_notes && (
                    <p className="text-indigo-900 font-medium bg-indigo-50 p-2 rounded-lg mt-1">
                      Admin Note: {d.admin_notes}
                    </p>
                  )}
                </div>

                {d.status === "UNDER_INVESTIGATION" && (
                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between gap-2">
                    {resolvingDisputeId === d.id ? (
                      <div className="w-full space-y-2">
                        <input
                          type="text"
                          placeholder="Enter settlement terms or surveyor findings..."
                          value={adminNotes}
                          onChange={(e) => setAdminNotes(e.target.value)}
                          className="w-full p-2 border border-slate-300 rounded-lg text-xs"
                        />
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => handleResolveDispute(d.id, "APPROVED")}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1 rounded-lg"
                          >
                            Approve Settlement
                          </button>
                          <button
                            onClick={() => handleResolveDispute(d.id, "REJECTED")}
                            className="bg-red-600 hover:bg-red-700 text-white font-bold px-3 py-1 rounded-lg"
                          >
                            Dismiss Claim
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => setResolvingDisputeId(d.id)}
                        className="bg-slate-900 hover:bg-slate-800 text-white font-bold px-3 py-1.5 rounded-lg"
                      >
                        Adjudicate Claim →
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Corridors & Stored Analytics Table (Feature 13) */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-900">Highest Volume Highway Corridors & Capacity Health</h3>
        
        <div className="grid md:grid-cols-3 gap-4">
          {pools.map((p) => (
            <div key={p.id} className="p-4 rounded-xl border border-slate-200 space-y-2 text-xs">
              <span className="font-bold text-indigo-700 block">{p.pool_code}</span>
              <h4 className="font-bold text-slate-900 text-sm">{p.corridor_name}</h4>
              <p className="text-slate-500">Shippers: {p.shippers_count} MSMEs · Distance: {p.total_distance_km} km</p>
              
              <div className="space-y-1 pt-1">
                <div className="flex justify-between">
                  <span>Capacity Utilization:</span>
                  <span className="font-bold text-indigo-600">{p.overall_utilization_pct}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-indigo-600 h-full rounded-full" style={{ width: `${p.overall_utilization_pct}%` }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
