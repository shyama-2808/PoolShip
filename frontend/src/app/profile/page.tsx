"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  User as UserIcon,
  ShieldCheck,
  Star,
  Building,
  Mail,
  Phone,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Truck,
  Package,
  Award,
  ArrowRight,
  MessageSquare
} from "lucide-react";
import { mockStore, User, Rating, Shipment, Truck as TruckType } from "@/lib/mockStore";

export default function ProfilePage() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [ratings, setRatings] = useState<Rating[]>([]);
  const [userRatingStats, setUserRatingStats] = useState<{ ratings: Rating[]; average: number; count: number }>({
    ratings: [],
    average: 5.0,
    count: 0
  });
  const [userShipments, setUserShipments] = useState<Shipment[]>([]);
  const [userTrucks, setUserTrucks] = useState<TruckType[]>([]);
  const [activeTab, setActiveTab] = useState<"reviews" | "activity" | "compliance">("reviews");

  useEffect(() => {
    const update = () => {
      const u = mockStore.getCurrentUser();
      setCurrentUser(u);
      setUsers(mockStore.getUsers());
      if (u) {
        const stats = mockStore.getUserRatings(u.id);
        setUserRatingStats(stats);
        setRatings(stats.ratings);
        setUserShipments(mockStore.getShipments().filter((s) => s.shipper_id === u.id));
        setUserTrucks(mockStore.getTrucks().filter((t) => t.transporter_id === u.id));
      }
    };
    update();
    const unsub = mockStore.subscribe(update);
    return () => unsub();
  }, []);

  if (!currentUser) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center text-slate-500">
        Loading profile...
      </div>
    );
  }

  // Star breakdown
  const starCounts = [5, 4, 3, 2, 1].map((s) => ({
    stars: s,
    count: ratings.filter((r) => r.rating === s).length
  }));

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Profile Header Banner */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white font-black text-2xl flex items-center justify-center shadow-md">
            {currentUser.full_name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-black text-slate-900">{currentUser.full_name}</h1>
              <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                currentUser.role === "SHIPPER" ? "bg-sky-100 text-sky-800" :
                currentUser.role === "TRANSPORTER" ? "bg-indigo-100 text-indigo-800" : "bg-purple-100 text-purple-800"
              }`}>
                {currentUser.role}
              </span>
              {currentUser.is_verified ? (
                <span className="inline-flex items-center gap-1 text-xs bg-emerald-100 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> GSTIN Verified
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs bg-amber-100 text-amber-800 font-bold px-2.5 py-0.5 rounded-full">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600" /> KYC Verification Pending
                </span>
              )}
            </div>

            <p className="text-sm text-slate-500 flex items-center gap-2">
              <Building className="w-4 h-4 text-slate-400" />
              {currentUser.company_name || "Individual Operator"}
            </p>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1">
              <span className="flex items-center gap-1">
                <Mail className="w-3.5 h-3.5 text-slate-400" /> {currentUser.email}
              </span>
              {currentUser.phone && (
                <span className="flex items-center gap-1">
                  <Phone className="w-3.5 h-3.5 text-slate-400" /> {currentUser.phone}
                </span>
              )}
              {currentUser.gst_number && (
                <span className="flex items-center gap-1 font-mono">
                  <FileText className="w-3.5 h-3.5 text-slate-400" /> GSTIN: {currentUser.gst_number}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Reputation Score Card */}
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200/80 p-5 rounded-2xl flex items-center gap-4 shrink-0 shadow-xs">
          <div className="text-center">
            <span className="text-3xl font-black text-amber-900 block">{userRatingStats.average}</span>
            <div className="flex items-center justify-center gap-0.5 text-amber-500 mt-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`w-3.5 h-3.5 ${star <= Math.round(userRatingStats.average) ? "fill-amber-400 text-amber-400" : "text-slate-300"}`}
                />
              ))}
            </div>
            <span className="text-[10px] text-amber-800/80 font-bold mt-1 block">
              {userRatingStats.count} {userRatingStats.count === 1 ? "Review" : "Reviews"}
            </span>
          </div>
          <div className="h-10 w-px bg-amber-200" />
          <div className="text-xs text-amber-950 space-y-0.5">
            <p className="font-bold flex items-center gap-1">
              <Award className="w-4 h-4 text-amber-600" /> Trust Score
            </p>
            <p className="text-[11px] text-amber-800">100% On-Time Handover</p>
            <p className="text-[11px] text-amber-800">Verified MSME Member</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-3 border-b border-slate-200 text-sm font-bold pb-2">
        <button
          onClick={() => setActiveTab("reviews")}
          className={`px-4 py-2 rounded-xl transition ${
            activeTab === "reviews" ? "bg-sky-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Customer Reviews &amp; Ratings ({ratings.length})
        </button>
        <button
          onClick={() => setActiveTab("activity")}
          className={`px-4 py-2 rounded-xl transition ${
            activeTab === "activity" ? "bg-sky-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          Consignment Activity ({currentUser.role === "SHIPPER" ? userShipments.length : userTrucks.length})
        </button>
        <button
          onClick={() => setActiveTab("compliance")}
          className={`px-4 py-2 rounded-xl transition ${
            activeTab === "compliance" ? "bg-sky-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          KYC &amp; Compliance Details
        </button>
      </div>

      {/* Tab 1: Reviews & Ratings */}
      {activeTab === "reviews" && (
        <div className="grid md:grid-cols-12 gap-6">
          {/* Rating Breakdown Bar */}
          <div className="md:col-span-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Rating Distribution</h3>
            <div className="space-y-2">
              {starCounts.map((sc) => {
                const pct = ratings.length > 0 ? (sc.count / ratings.length) * 100 : 0;
                return (
                  <div key={sc.stars} className="flex items-center gap-2 text-xs">
                    <span className="w-12 font-medium text-slate-600 flex items-center gap-0.5">
                      {sc.stars} <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                    </span>
                    <div className="flex-1 bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-amber-400 h-full rounded-full transition-all" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="w-8 text-right text-slate-400">{sc.count}</span>
                  </div>
                );
              })}
            </div>

            <div className="pt-4 border-t border-slate-100 text-xs text-slate-500 space-y-1">
              <p className="font-semibold text-slate-700">Verified Marketplace Feedback</p>
              <p className="text-[11px] leading-relaxed">
                Reviews can only be submitted after successful OTP and digital POD completion along active highway corridors.
              </p>
            </div>
          </div>

          {/* Reviews List */}
          <div className="md:col-span-8 space-y-3">
            {ratings.length === 0 ? (
              <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-slate-500 text-sm space-y-2">
                <MessageSquare className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="font-semibold text-slate-700">No public reviews yet</p>
                <p className="text-xs text-slate-400">Complete pooled freight trips to build your verified reputation profile.</p>
              </div>
            ) : (
              ratings.map((r) => {
                const author = users.find((u) => u.id === r.from_user_id);
                return (
                  <div key={r.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center">
                          {author?.full_name ? author.full_name[0] : "U"}
                        </div>
                        <div>
                          <span className="font-bold text-slate-900 text-xs block">{author?.full_name || "Verified Peer"}</span>
                          <span className="text-[10px] text-slate-400">{author?.company_name || author?.role}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 text-amber-500">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Star
                            key={star}
                            className={`w-3.5 h-3.5 ${star <= r.rating ? "fill-amber-400 text-amber-400" : "text-slate-300"}`}
                          />
                        ))}
                      </div>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed italic">
                      &ldquo;{r.comment}&rdquo;
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-50">
                      <span>Pool Reference: #{r.pool_id}</span>
                      <span>{new Date(r.created_at).toLocaleDateString("en-IN")}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Activity */}
      {activeTab === "activity" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-900 text-sm">
            {currentUser.role === "SHIPPER" ? "Posted Consignments" : "Registered Fleet & Corridors"}
          </h3>

          {currentUser.role === "SHIPPER" ? (
            <div className="divide-y divide-slate-100 text-xs">
              {userShipments.map((s) => (
                <div key={s.id} className="py-3 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="font-bold text-slate-800">{s.title}</span>
                    <span className="text-slate-400 block">{s.origin_address} &rarr; {s.destination_address} ({s.weight_kg} kg)</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      s.status === "DELIVERED" ? "bg-emerald-100 text-emerald-800" :
                      s.status === "IN_TRANSIT" ? "bg-amber-100 text-amber-800" : "bg-sky-100 text-sky-800"
                    }`}>
                      {s.status}
                    </span>
                    <Link href={`/tracking/${s.id}`} className="text-sky-600 hover:underline font-semibold flex items-center gap-1">
                      Track <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-slate-100 text-xs">
              {userTrucks.map((t) => (
                <div key={t.id} className="py-3 flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="font-bold text-slate-800">{t.truck_type} &bull; {t.registration_number}</span>
                    <span className="text-slate-400 block">{t.origin_city} &rarr; {t.destination_city} ({t.max_weight_kg} kg capacity)</span>
                  </div>
                  <span className="text-emerald-600 font-bold">
                    {Math.round((t.booked_weight_kg / t.max_weight_kg) * 100)}% Fill Rate
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Compliance & KYC */}
      {activeTab === "compliance" && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <h3 className="font-bold text-slate-900 text-sm">Regulatory &amp; GST Compliance Record</h3>

          <div className="grid md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-1">
              <span className="text-slate-400 font-medium">15-Digit GST Identification Number (GSTIN)</span>
              <p className="font-mono text-sm font-bold text-slate-900">{currentUser.gst_number || "29AABCU9603R1ZM"}</p>
              <p className="text-[10px] text-emerald-600 font-semibold">&bull; State Code: 29 (Karnataka) &bull; Format Validated</p>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-1">
              <span className="text-slate-400 font-medium">Platform KYC Status</span>
              <p className="text-sm font-bold text-emerald-700 flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                {currentUser.is_verified ? "Approved & Cleared for Cargo Booking" : "Under Review by Admin Operations"}
              </p>
              <p className="text-[10px] text-slate-500">Verified through Ministry of Corporate Affairs / GST Portal Sandbox</p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-sky-50 border border-sky-200 text-xs text-sky-900 space-y-1">
            <span className="font-bold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-sky-600" /> E-Way Bill Auto-Generation Guarantee
            </span>
            <p className="text-[11px] leading-relaxed text-sky-800">
              In accordance with Rule 138 of the CGST Rules, consignments exceeding ₹50,000 value automatically generate valid 12-digit E-Way Bill documents upon pool dispatch.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

