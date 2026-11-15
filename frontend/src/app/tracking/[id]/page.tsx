"use client";

import { useState } from "react";
import { 
  CheckCircle2, 
  Clock, 
  MapPin, 
  Truck, 
  ShieldCheck, 
  Lock, 
  Camera, 
  FileCheck2,
  Navigation
} from "lucide-react";

export default function TrackingPage({ params }: { params: { id: string } }) {
  const [otpInput, setOtpInput] = useState("");
  const [isVerified, setIsVerified] = useState(false);

  const milestones = [
    {
      title: "Consolidated & Dispatched",
      location: "Peenya Hub, Bangalore",
      time: "Today, 06:30 AM",
      completed: true,
      description: "Shipments consolidated into Tata 407 (KA01-EF-9988). Capacity optimization verified.",
    },
    {
      title: "In Transit (En Route)",
      location: "Krishnagiri Toll Plaza (NH 48)",
      time: "Today, 09:45 AM",
      completed: true,
      description: "Truck running on schedule. Distance covered: 140 km.",
    },
    {
      title: "Out for Final Drop",
      location: "Sri City SEZ, Gate 2",
      time: "Estimated 01:30 PM",
      completed: false,
      description: "Driver will initiate delivery handover via secure OTP release.",
    },
    {
      title: "Digital Proof of Delivery (POD)",
      location: "Consignee Warehouse",
      time: "Pending handover",
      completed: false,
      description: "Photo evidence, consignee digital signature, and GST e-way bill closure.",
    }
  ];

  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    if (otpInput === "4829" || otpInput.length === 4) {
      setIsVerified(true);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold text-sky-600 uppercase tracking-widest">Active Consignment</span>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Pool #POOL-884 Tracking</h1>
          <p className="text-xs text-slate-500 mt-0.5">Vehicle: Tata 407 (KA01-EF-9988) · Driver: Suresh Gowda</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
            In Transit (NH 48)
          </span>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Navigation className="w-5 h-5 text-sky-600" /> Milestone Tracking Journey
        </h2>

        <div className="relative pl-6 space-y-8 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
          {milestones.map((m, idx) => (
            <div key={idx} className="relative space-y-1">
              <div className={`absolute -left-6 top-1 w-5 h-5 rounded-full border-2 flex items-center justify-center bg-white ${
                m.completed ? "border-emerald-500 text-emerald-600" : "border-slate-300 text-slate-300"
              }`}>
                {m.completed && <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full" />}
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className={`text-sm font-bold ${m.completed ? "text-slate-900" : "text-slate-400"}`}>
                  {m.title}
                </h3>
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> {m.time}
                </span>
              </div>

              <p className="text-xs font-medium text-slate-600">{m.location}</p>
              <p className="text-xs text-slate-500">{m.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Digital Proof of Delivery Handover */}
      <div className="bg-slate-900 text-white p-6 rounded-2xl space-y-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-400" />
          <h2 className="text-base font-bold">Secure Delivery Handover & OTP Verification</h2>
        </div>
        <p className="text-xs text-slate-400">
          To protect pooled consignments, the driver cannot mark the cargo as delivered without this 4-digit code provided by the receiving business.
        </p>

        {isVerified ? (
          <div className="bg-emerald-950/80 border border-emerald-500 text-emerald-300 p-4 rounded-xl flex items-center gap-3 text-xs">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <p className="font-bold text-sm">Delivery Confirmed & Verified</p>
              <p>Consignment released. Automated GST invoice and e-way bill closure generated.</p>
            </div>
          </div>
        ) : (
          <form onSubmit={handleVerifyOtp} className="flex flex-wrap items-center gap-3">
            <input
              type="text"
              maxLength={4}
              placeholder="Demo OTP: 4829"
              value={otpInput}
              onChange={(e) => setOtpInput(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-white px-3 py-2 rounded-lg text-sm tracking-widest font-mono text-center focus:outline-none focus:border-sky-500"
            />
            <button
              type="submit"
              className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold px-4 py-2 rounded-lg text-xs transition"
            >
              Verify & Release Consignment
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
