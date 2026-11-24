"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Package, 
  MapPin, 
  Weight, 
  CheckCircle2, 
  TrendingDown, 
  Leaf, 
  AlertTriangle,
  Truck,
  ShieldCheck,
  ShieldAlert,
  CreditCard,
  Download,
  Star,
  Plus,
  AlertCircle,
  Eye,
  Info
} from "lucide-react";
import { mockStore, Shipment, Pool, Truck as TruckType, User } from "@/lib/mockStore";
import { translations, Locale } from "@/locales/translations";

export default function ShipperDashboard() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [pools, setPools] = useState<Pool[]>([]);
  const [trucks, setTrucks] = useState<TruckType[]>([]);
  const [lang, setLang] = useState<Locale>("en");

  // Booking Modal
  const [selectedShipment, setSelectedShipment] = useState<Shipment | null>(null);
  const [selectedPool, setSelectedPool] = useState<Pool | null>(null);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [showPaymentSuccess, setShowPaymentSuccess] = useState(false);

  // Review Modal
  const [ratingShipment, setRatingShipment] = useState<Shipment | null>(null);
  const [starCount, setStarCount] = useState(5);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewSubmitted, setReviewSubmitted] = useState(false);

  // Dispute Modal
  const [disputeShipment, setDisputeShipment] = useState<Shipment | null>(null);
  const [disputeType, setDisputeType] = useState("Damaged Goods");
  const [disputeAmount, setDisputeAmount] = useState(5000);
  const [disputeDesc, setDisputeDesc] = useState("");
  const [disputeSubmitted, setDisputeSubmitted] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    title: "Precision Automotive Gear Blanks",
    goods_type: "Hardware",
    weight_kg: 850,
    volume_cbm: 2.5,
    length_cm: 150,
    width_cm: 100,
    height_cm: 100,
    origin_address: "Peenya Industrial Area, Bangalore",
    origin_lat: 13.0285,
    origin_lng: 77.5197,
    destination_address: "Ambattur Industrial Estate, Chennai",
    dest_lat: 13.1143,
    dest_lng: 80.1548,
    is_perishable: false,
    is_hazardous: false,
    is_fragile: true,
    has_insurance: true,
    declared_value: 280000,
  });

  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  useEffect(() => {
    const update = () => {
      setCurrentUser(mockStore.getCurrentUser());
      setShipments(mockStore.getShipments());
      setPools(mockStore.getPools());
      setTrucks(mockStore.getTrucks());
      setLang(mockStore.getLanguage());
    };
    update();
    const unsub = mockStore.subscribe(update);
    return () => unsub();
  }, []);

  const t = translations[lang] || translations.en;

  // Filter shipments for current shipper
  const myShipments = shipments.filter((s) => {
    if (currentUser?.role === "ADMIN") return true;
    if (currentUser?.id) return s.shipper_id === currentUser.id;
    return true;
  }).filter((s) => filterStatus === "ALL" || s.status === filterStatus);

  const handlePostShipment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    mockStore.createShipment({
      shipper_id: currentUser.id,
      pool_id: null,
      title: formData.title,
      goods_type: formData.goods_type,
      weight_kg: Number(formData.weight_kg),
      volume_cbm: Number(formData.volume_cbm),
      length_cm: Number(formData.length_cm),
      width_cm: Number(formData.width_cm),
      height_cm: Number(formData.height_cm),
      origin_address: formData.origin_address,
      origin_lat: formData.origin_lat,
      origin_lng: formData.origin_lng,
      destination_address: formData.destination_address,
      dest_lat: formData.dest_lat,
      dest_lng: formData.dest_lng,
      is_perishable: formData.is_perishable,
      is_hazardous: formData.is_hazardous,
      is_fragile: formData.is_fragile,
      has_insurance: formData.has_insurance,
      declared_value: Number(formData.declared_value),
    });

    alert("Shipment posted successfully! Matched with available truck pools.");
  };

  const handleOpenBooking = (shipment: Shipment) => {
    if (!currentUser?.is_verified) {
      alert("Booking Blocked: Your GSTIN verification is pending with Admin. Please contact Admin or switch persona.");
      return;
    }
    setSelectedShipment(shipment);
    setShowBookingModal(true);
  };

  const handleConfirmBooking = (poolId: number) => {
    if (!selectedShipment) return;
    const ok = mockStore.bookPoolShare(poolId, selectedShipment.id);
    if (ok) {
      setShowBookingModal(false);
      setShowPaymentSuccess(true);
      setTimeout(() => setShowPaymentSuccess(false), 4000);
    }
  };

  const handleReviewSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ratingShipment || !currentUser) return;
    mockStore.addRating({
      pool_id: ratingShipment.pool_id || 1,
      from_user_id: currentUser.id,
      to_user_id: 4, // Transporter
      rating: starCount,
      comment: reviewComment || "On-time delivery and good consignment handling.",
    });
    setReviewSubmitted(true);
    setTimeout(() => {
      setReviewSubmitted(false);
      setRatingShipment(null);
    }, 2000);
  };

  const handleDisputeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!disputeShipment || !currentUser) return;
    mockStore.createDispute({
      pool_id: disputeShipment.pool_id || 1,
      shipment_id: disputeShipment.id,
      shipper_name: currentUser.company_name || currentUser.full_name,
      transporter_name: "Nanjundeshwara Roadlines",
      claim_type: disputeType,
      claimed_amount: Number(disputeAmount),
      description: disputeDesc || "Cargo packaging damaged during transit. Claiming partial loss.",
      photo_url: "/mock/damage-evidence.jpg",
    });
    setDisputeSubmitted(true);
    setTimeout(() => {
      setDisputeSubmitted(false);
      setDisputeShipment(null);
    }, 2500);
  };

  // Download Invoice simulation
  const handleDownloadInvoice = (shipment: Shipment) => {
    const invoiceContent = `
==============================================================
                    POOLSHIP FREIGHT SERVICES
                 GST TAX INVOICE & CONSIGNMENT NOTE
==============================================================
Invoice Number: PS-INV-${shipment.id}
Date: ${new Date().toLocaleDateString("en-IN")}
E-Way Bill No: 281944810023

CONSIGNOR (SHIPPER):
Name: ${currentUser?.company_name || currentUser?.full_name}
GSTIN: ${currentUser?.gst_number || "29AABCP1334M1ZV"}
Origin: ${shipment.origin_address}

CONSIGNEE / DESTINATION:
Destination: ${shipment.destination_address}

CONSIGNMENT DETAILS:
Cargo: ${shipment.title} (${shipment.goods_type})
Weight: ${shipment.weight_kg} kg | Volume: ${shipment.volume_cbm} m3
Declared Value: ₹${(shipment.declared_value || 100000).toLocaleString()}
Transit Insurance: ${shipment.has_insurance ? "Opted (Covered)" : "Not Opted"}

FREIGHT & TAX BREAKDOWN (Ton-Km Proportional Share):
--------------------------------------------------------------
Base Pooled Freight Share:             ₹${(shipment.allocated_cost || 4500).toLocaleString()}
Transit Insurance Premium (0.75%):     ₹${shipment.has_insurance ? Math.round((shipment.declared_value || 100000) * 0.0075) : 0}
CGST (6%):                             ₹${Math.round((shipment.allocated_cost || 4500) * 0.06)}
SGST (6%):                             ₹${Math.round((shipment.allocated_cost || 4500) * 0.06)}
--------------------------------------------------------------
TOTAL PAYABLE AMOUNT:                  ₹${Math.round((shipment.allocated_cost || 4500) * 1.12 + (shipment.has_insurance ? (shipment.declared_value || 100000) * 0.0075 : 0)).toLocaleString()}
--------------------------------------------------------------
Status: PAID (Mock Verified)
Delivery Proof: Handover OTP Verified (${shipment.delivery_otp})
Vehicle Reg: KA-01-MJ-4491 (Tata 407 / 14ft Canter)
Driver: Suresh Gowda (+91 94480 33445)
==============================================================
Thank you for shipping green with PoolShip!
    `;
    const blob = new Blob([invoiceContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `PoolShip-Invoice-${shipment.id}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header & Verification Banner */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900">{t.shipperPortal}</h1>
              {currentUser?.is_verified ? (
                <span className="inline-flex items-center gap-1 text-xs font-bold bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> {t.verifiedBadge}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs font-bold bg-amber-100 text-amber-800 px-2.5 py-1 rounded-full">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-600" /> Verification Pending
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Active Business: <span className="font-semibold text-slate-800">{currentUser?.company_name || currentUser?.full_name}</span> ({currentUser?.email})
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs px-3.5 py-2 rounded-xl flex items-center gap-2 font-medium">
              <Leaf className="w-4 h-4 text-emerald-600" />
              <span>CO₂ Saved to date: <strong>320 kg</strong></span>
            </div>
          </div>
        </div>

        {/* Unverified User Blocker Banner */}
        {!currentUser?.is_verified && (
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-xs text-amber-800 space-y-1">
              <p className="font-bold text-sm">Action Required: Business Account Unverified</p>
              <p>{t.unverifiedNotice}</p>
              <p className="text-[11px] text-amber-700">
                Tip: Switch to <strong>Ramesh Kumar (Shipper)</strong> or <strong>Admin</strong> in the top navbar to verify GSTIN or test booking flows.
              </p>
            </div>
          </div>
        )}

        {showPaymentSuccess && (
          <div className="bg-emerald-600 text-white p-4 rounded-xl shadow-lg flex items-center gap-3 text-sm animate-bounce">
            <CheckCircle2 className="w-5 h-5 text-emerald-200 shrink-0" />
            <div>
              <p className="font-bold">Booking Confirmed & Paid!</p>
              <p className="text-xs text-emerald-100">Consignment locked into truck pool. Free capacity updated on transporter dashboard.</p>
            </div>
          </div>
        )}
      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* Post Shipment Form (Feature 2) */}
        <div className="lg:col-span-5 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Package className="w-5 h-5 text-sky-600" />
            <h2 className="text-base font-bold text-slate-900">{t.postShipment}</h2>
          </div>

          <form onSubmit={handlePostShipment} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">{t.cargoTitle}</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-sky-500 focus:outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">{t.goodsCategory}</label>
                <select
                  value={formData.goods_type}
                  onChange={(e) => setFormData({ ...formData, goods_type: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
                >
                  <option value="Hardware">Hardware / Machined</option>
                  <option value="Textiles">Textiles & Fabrics</option>
                  <option value="FMCG">FMCG / Dry Goods</option>
                  <option value="Electronics">Electronics & PCBs</option>
                  <option value="Perishable">Perishable (Agri/Cold)</option>
                  <option value="Chemicals">Industrial Chemicals</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">{t.weight}</label>
                <input
                  type="number"
                  value={formData.weight_kg}
                  onChange={(e) => setFormData({ ...formData, weight_kg: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">{t.volume}</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.volume_cbm}
                  onChange={(e) => setFormData({ ...formData, volume_cbm: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">Declared Value (₹)</label>
                <input
                  type="number"
                  value={formData.declared_value}
                  onChange={(e) => setFormData({ ...formData, declared_value: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">{t.pickupLocation}</label>
                <input
                  type="text"
                  value={formData.origin_address}
                  onChange={(e) => setFormData({ ...formData, origin_address: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">{t.dropLocation}</label>
                <input
                  type="text"
                  value={formData.destination_address}
                  onChange={(e) => setFormData({ ...formData, destination_address: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  required
                />
              </div>
            </div>

            {/* Special Cargo & Feature 11 Insurance */}
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center gap-4">
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_fragile}
                    onChange={(e) => setFormData({ ...formData, is_fragile: e.target.checked })}
                    className="rounded text-sky-600 mr-1.5"
                  />
                  Fragile
                </label>
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_perishable}
                    onChange={(e) => setFormData({ ...formData, is_perishable: e.target.checked })}
                    className="rounded text-sky-600 mr-1.5"
                  />
                  Perishable
                </label>
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_hazardous}
                    onChange={(e) => setFormData({ ...formData, is_hazardous: e.target.checked })}
                    className="rounded text-sky-600 mr-1.5"
                  />
                  Hazardous
                </label>
              </div>

              <div className="pt-1 border-t border-slate-200 flex items-center justify-between">
                <label className="inline-flex items-center cursor-pointer font-bold text-sky-900">
                  <input
                    type="checkbox"
                    checked={formData.has_insurance}
                    onChange={(e) => setFormData({ ...formData, has_insurance: e.target.checked })}
                    className="rounded text-sky-600 mr-1.5"
                  />
                  Transit Insurance (+0.75%)
                </label>
                <span className="text-[11px] font-semibold text-sky-700">
                  {formData.has_insurance ? `+ ₹${Math.round(formData.declared_value * 0.0075)}` : "None"}
                </span>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-2.5 rounded-xl shadow transition text-sm flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" /> {t.postAndFind}
            </button>
          </form>
        </div>

        {/* My Shipments List (Feature 2 & 3) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold text-slate-900">{t.myShipments}</h2>
              <p className="text-xs text-slate-500">Track consignment status and book available truck capacity</p>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
              {["ALL", "MATCHED", "POOLED", "IN_TRANSIT", "DELIVERED"].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`px-2.5 py-1 rounded-md font-semibold transition ${
                    filterStatus === st ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            {myShipments.length === 0 ? (
              <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-slate-500 text-sm">
                No shipments found matching the selected filter.
              </div>
            ) : (
              myShipments.map((s) => (
                <div key={s.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-slate-900 text-sm">{s.title}</h3>
                        <span className="text-[10px] bg-slate-100 text-slate-600 font-mono px-1.5 py-0.5 rounded">
                          #{s.id}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Category: {s.goods_type} · OTP: <span className="font-mono font-bold text-slate-800">{s.delivery_otp}</span>
                      </p>
                    </div>

                    {/* Status Badge */}
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                      s.status === "DELIVERED" ? "bg-emerald-100 text-emerald-800" :
                      s.status === "IN_TRANSIT" ? "bg-amber-100 text-amber-800" :
                      s.status === "POOLED" ? "bg-sky-100 text-sky-800" : "bg-purple-100 text-purple-800"
                    }`}>
                      {s.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div>
                      <span className="text-slate-400 block">Route</span>
                      <span className="font-semibold text-slate-800 truncate block">{s.origin_address.split(",")[0]} → {s.destination_address.split(",")[0]}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Cargo Payload</span>
                      <span className="font-semibold text-slate-800">{s.weight_kg} kg · {s.volume_cbm} m³</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Allocated Cost</span>
                      <span className="font-bold text-slate-900">
                        {s.allocated_cost ? `₹${s.allocated_cost.toLocaleString()}` : "Pending Match"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Transit Insurance</span>
                      <span className={`font-semibold ${s.has_insurance ? "text-emerald-600" : "text-slate-500"}`}>
                        {s.has_insurance ? "Active (+0.75%)" : "None"}
                      </span>
                    </div>
                  </div>

                  {/* Actions depending on status */}
                  <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 text-xs">
                    <div className="flex items-center gap-2">
                      {s.status === "MATCHED" && (
                        <button
                          onClick={() => handleOpenBooking(s)}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-3 py-1.5 rounded-lg shadow-sm transition flex items-center gap-1.5"
                        >
                          <Truck className="w-3.5 h-3.5" /> Select & Book Truck Pool
                        </button>
                      )}

                      {s.status === "POOLED" && (
                        <span className="text-emerald-700 font-semibold flex items-center gap-1 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Space Reserved in Pool #{s.pool_id}
                        </span>
                      )}

                      {(s.status === "IN_TRANSIT" || s.status === "POOLED" || s.status === "DELIVERED") && (
                        <Link
                          href={`/tracking/${s.id}`}
                          className="text-sky-600 hover:underline font-bold flex items-center gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" /> View Live Tracking →
                        </Link>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {s.status === "DELIVERED" && (
                        <>
                          <button
                            onClick={() => handleDownloadInvoice(s)}
                            className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition"
                            title="Download GST invoice & E-way bill"
                          >
                            <Download className="w-3.5 h-3.5 text-slate-600" /> Invoice (PDF)
                          </button>

                          <button
                            onClick={() => setRatingShipment(s)}
                            className="bg-amber-50 hover:bg-amber-100 text-amber-800 font-semibold px-2.5 py-1.5 rounded-lg flex items-center gap-1 transition border border-amber-200"
                          >
                            <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-400" /> Review
                          </button>
                        </>
                      )}

                      {/* Dispute Trigger */}
                      <button
                        onClick={() => setDisputeShipment(s)}
                        className="text-slate-400 hover:text-red-600 text-[11px] font-medium transition"
                      >
                        Raise Dispute
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Booking Modal (Feature 3 & 4: Space Booking & Mock Payment) */}
      {showBookingModal && selectedShipment && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-bold text-indigo-600 uppercase">Available Highway Corridors</span>
                <h3 className="text-lg font-bold text-slate-900 mt-0.5">Book Truck Share for #{selectedShipment.id}</h3>
              </div>
              <button
                onClick={() => setShowBookingModal(false)}
                className="text-slate-400 hover:text-slate-700 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
              <p><strong>Your Consignment:</strong> {selectedShipment.title} ({selectedShipment.weight_kg} kg, {selectedShipment.volume_cbm} m³)</p>
              <p><strong>Corridor:</strong> {selectedShipment.origin_address} → {selectedShipment.destination_address}</p>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-700 uppercase">Select Matching Truck Pool</h4>
              {pools.map((p) => {
                const tr = trucks.find((t) => t.id === p.truck_id);
                const hasCapacity = tr ? (tr.max_weight_kg - tr.booked_weight_kg) >= selectedShipment.weight_kg : true;

                return (
                  <div key={p.id} className="p-4 rounded-xl border border-slate-200 hover:border-indigo-500 transition space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="text-xs font-bold text-indigo-700">{p.pool_code}</span>
                        <h5 className="font-bold text-slate-900 text-sm">{p.corridor_name}</h5>
                        <p className="text-[11px] text-slate-500">Vehicle: {tr?.truck_type} ({tr?.registration_number}) · Driver: {tr?.driver_name}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-slate-400 block">Your Fair Share</span>
                        <span className="text-base font-extrabold text-emerald-600">₹4,200</span>
                        <span className="text-[10px] text-emerald-700 block font-medium">Save ₹6,800 vs alone</span>
                      </div>
                    </div>

                    {/* Progress Bar of Capacity */}
                    <div className="space-y-1 text-[11px] text-slate-500">
                      <div className="flex justify-between">
                        <span>Current Fill: {p.current_weight_kg} / {tr?.max_weight_kg} kg</span>
                        <span className="font-bold text-indigo-600">{p.overall_utilization_pct}% Full</span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div className="bg-indigo-600 h-full rounded-full" style={{ width: `${p.overall_utilization_pct}%` }} />
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <span className="text-[11px] text-emerald-700 font-semibold flex items-center gap-1">
                        <Leaf className="w-3.5 h-3.5 text-emerald-600" /> Cuts {p.co2_saved_kg} kg CO₂
                      </span>

                      <button
                        disabled={!hasCapacity}
                        onClick={() => handleConfirmBooking(p.id)}
                        className={`text-xs font-bold px-4 py-2 rounded-xl transition ${
                          hasCapacity
                            ? "bg-indigo-600 hover:bg-indigo-700 text-white shadow"
                            : "bg-slate-200 text-slate-400 cursor-not-allowed"
                        }`}
                      >
                        {hasCapacity ? "Confirm & Pay Share (Mock)" : "Truck Full"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Rating & Review Modal (Feature 7) */}
      {ratingShipment && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Rate Delivery Experience</h3>
            <p className="text-xs text-slate-500">Shipment #{ratingShipment.id}: {ratingShipment.title}</p>

            {reviewSubmitted ? (
              <div className="bg-emerald-50 text-emerald-800 p-4 rounded-xl text-center text-xs font-bold">
                Thank you! Rating saved to transporter profile.
              </div>
            ) : (
              <form onSubmit={handleReviewSubmit} className="space-y-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Star Rating</label>
                  <div className="flex items-center gap-2">
                    {[1, 2, 3, 4, 5].map((st) => (
                      <button
                        type="button"
                        key={st}
                        onClick={() => setStarCount(st)}
                        className="p-1 hover:scale-110 transition"
                      >
                        <Star className={`w-6 h-6 ${st <= starCount ? "text-amber-400 fill-amber-400" : "text-slate-300"}`} />
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Feedback Comment</label>
                  <textarea
                    rows={3}
                    value={reviewComment}
                    onChange={(e) => setReviewComment(e.target.value)}
                    placeholder="Punctual driver, smooth handover..."
                    className="w-full p-2.5 border border-slate-300 rounded-lg"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setRatingShipment(null)}
                    className="px-3 py-1.5 rounded-lg border text-slate-600"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold"
                  >
                    Submit Rating
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Dispute Modal (Feature 12) */}
      {disputeShipment && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Raise Claim / Dispute</h3>
            <p className="text-xs text-slate-500">Consignment #{disputeShipment.id}: {disputeShipment.title}</p>

            {disputeSubmitted ? (
              <div className="bg-emerald-50 text-emerald-800 p-4 rounded-xl text-center text-xs font-bold">
                Claim registered! Admin operations desk has been notified.
              </div>
            ) : (
              <form onSubmit={handleDisputeSubmit} className="space-y-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Dispute Type</label>
                  <select
                    value={disputeType}
                    onChange={(e) => setDisputeType(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="Damaged Goods">Damaged Goods in Transit</option>
                    <option value="Severe Delivery Delay">Severe Delivery Delay (Penalty)</option>
                    <option value="Missing Package Count">Missing Package Count</option>
                    <option value="Vehicle Breakdown">Vehicle Breakdown</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Claim Amount (₹)</label>
                  <input
                    type="number"
                    value={disputeAmount}
                    onChange={(e) => setDisputeAmount(Number(e.target.value))}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Description & Evidence</label>
                  <textarea
                    rows={3}
                    value={disputeDesc}
                    onChange={(e) => setDisputeDesc(e.target.value)}
                    placeholder="Provide details of the damaged goods or late delay..."
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setDisputeShipment(null)}
                    className="px-3 py-1.5 rounded-lg border text-slate-600"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold"
                  >
                    Submit Dispute to Admin
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
