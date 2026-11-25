"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Truck, 
  Plus, 
  MapPin, 
  Gauge, 
  CheckCircle2, 
  AlertTriangle,
  RotateCcw,
  IndianRupee,
  Layers,
  Phone,
  Navigation,
  ArrowRight,
  ShieldCheck,
  PackageCheck,
  Star
} from "lucide-react";
import { mockStore, Truck as TruckType, Pool, Shipment, User } from "@/lib/mockStore";
import { translations, Locale } from "@/locales/translations";

export default function TransporterDashboard() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [trucks, setTrucks] = useState<TruckType[]>([]);
  const [pools, setPools] = useState<Pool[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [lang, setLang] = useState<Locale>("en");

  const [showAddTruckModal, setShowAddTruckModal] = useState(false);
  const [ratingShipment, setRatingShipment] = useState<Shipment | null>(null);
  const [starCount, setStarCount] = useState(5);
  const [ratingComment, setRatingComment] = useState("");

  // Form state for adding new truck
  const [newTruckData, setNewTruckData] = useState({
    truck_type: "14ft Eicher Canter",
    registration_number: "KA-04-MK-9901",
    max_weight_kg: 4000,
    max_volume_cbm: 16.0,
    length_cm: 420,
    width_cm: 200,
    height_cm: 200,
    origin_city: "Bangalore",
    origin_lat: 12.9716,
    origin_lng: 77.5946,
    destination_city: "Hyderabad",
    dest_lat: 17.3850,
    dest_lng: 78.4867,
    available_date: "2026-11-28T06:00:00Z",
    rate_per_km: 36,
    driver_name: "Raghavendra Rao",
    driver_phone: "+91 94490 88776",
    is_return_trip: false,
  });

  useEffect(() => {
    const update = () => {
      setCurrentUser(mockStore.getCurrentUser());
      setTrucks(mockStore.getTrucks());
      setPools(mockStore.getPools());
      setShipments(mockStore.getShipments());
      setLang(mockStore.getLanguage());
    };
    update();
    const unsub = mockStore.subscribe(update);
    return () => unsub();
  }, []);

  const t = translations[lang] || translations.en;

  const handleCreateTruck = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;
    mockStore.createTruck({
      transporter_id: currentUser.id,
      truck_type: newTruckData.truck_type,
      registration_number: newTruckData.registration_number,
      max_weight_kg: Number(newTruckData.max_weight_kg),
      max_volume_cbm: Number(newTruckData.max_volume_cbm),
      length_cm: Number(newTruckData.length_cm),
      width_cm: Number(newTruckData.width_cm),
      height_cm: Number(newTruckData.height_cm),
      origin_city: newTruckData.origin_city,
      origin_lat: newTruckData.origin_lat,
      origin_lng: newTruckData.origin_lng,
      destination_city: newTruckData.destination_city,
      dest_lat: newTruckData.dest_lat,
      dest_lng: newTruckData.dest_lng,
      available_date: newTruckData.available_date,
      rate_per_km: Number(newTruckData.rate_per_km),
      driver_name: newTruckData.driver_name,
      driver_phone: newTruckData.driver_phone,
      is_return_trip: newTruckData.is_return_trip,
    });
    setShowAddTruckModal(false);
  };

  const handleSubmitShipperRating = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser || !ratingShipment) return;
    mockStore.addRating({
      pool_id: ratingShipment.pool_id || 1,
      from_user_id: currentUser.id,
      to_user_id: ratingShipment.shipper_id,
      rating: starCount,
      comment: ratingComment || "Punctual handover and packaging compliant with highway cargo standards.",
    });
    setRatingShipment(null);
    setRatingComment("");
    setStarCount(5);
  };

  const handleUpdateStatus = (poolId: number, status: Pool["status"]) => {
    mockStore.updatePoolStatus(poolId, status);
  };

  const handleToggleWaypoint = (poolId: number, idx: number, completed: boolean) => {
    mockStore.updateWaypoint(poolId, idx, completed);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900">{t.transporterHub}</h1>
            <span className="text-xs bg-indigo-100 text-indigo-800 font-bold px-2.5 py-0.5 rounded-full">
              Fleet Operations
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Transporter: <span className="font-semibold text-slate-800">{currentUser?.company_name || currentUser?.full_name}</span> · Monetize deadhead space & eliminate empty return runs.
          </p>
        </div>

        <button
          onClick={() => setShowAddTruckModal(true)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-sm shadow transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> {t.listTruck}
        </button>
      </div>

      {/* Fleet Grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {trucks.map((truck) => {
          const pool = pools.find((p) => p.truck_id === truck.id);
          const pooledShipments = pool ? shipments.filter((s) => pool.shipment_ids.includes(s.id)) : [];
          const weightPct = Math.round((truck.booked_weight_kg / truck.max_weight_kg) * 100);
          const volPct = Math.round((truck.booked_volume_cbm / truck.max_volume_cbm) * 100);
          const isHighFill = weightPct >= 75 || volPct >= 75;

          return (
            <div key={truck.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-start justify-between border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">{truck.truck_type}</span>
                      {truck.is_return_trip && (
                        <span className="text-[10px] bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded flex items-center gap-1">
                          <RotateCcw className="w-3 h-3 text-amber-600" /> Return Run
                        </span>
                      )}
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 mt-0.5">{truck.registration_number}</h3>
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                      <Phone className="w-3 h-3 text-slate-400" /> Driver: <strong>{truck.driver_name}</strong> ({truck.driver_phone})
                    </p>
                  </div>

                  <div className="text-right">
                    <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                      pool?.status === "IN_TRANSIT" ? "bg-amber-100 text-amber-800" :
                      pool?.status === "LOCKED" ? "bg-indigo-100 text-indigo-800" :
                      pool?.status === "COMPLETED" ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
                    }`}>
                      {pool?.status || "OPEN"}
                    </span>
                    <p className="text-[11px] text-slate-400 mt-1">₹{truck.rate_per_km}/km</p>
                  </div>
                </div>

                {/* Corridor Info */}
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-xs flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-sky-500" />
                    <span className="font-bold text-slate-800">{truck.origin_city} → {truck.destination_city}</span>
                  </div>
                  <span className="text-slate-500">Departure: {new Date(truck.available_date).toLocaleDateString("en-IN")}</span>
                </div>

                {/* Live Fill Meter (Feature 3) */}
                <div className="space-y-2 bg-indigo-50/50 p-4 rounded-xl border border-indigo-100">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-slate-800 flex items-center gap-1.5">
                      <Gauge className="w-4 h-4 text-indigo-600" /> Cargo Fill Rate:
                    </span>
                    <span className={`font-black ${isHighFill ? "text-emerald-600" : "text-indigo-600"}`}>
                      {Math.max(weightPct, volPct)}% Occupied
                    </span>
                  </div>

                  <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isHighFill ? "bg-emerald-500" : "bg-indigo-600"
                      }`}
                      style={{ width: `${Math.min(100, Math.max(weightPct, volPct))}%` }}
                    />
                  </div>

                  <div className="grid grid-cols-2 text-[11px] text-slate-600 pt-1">
                    <span>Weight: <strong>{truck.booked_weight_kg}</strong> / {truck.max_weight_kg} kg</span>
                    <span className="text-right">Volume: <strong>{truck.booked_volume_cbm.toFixed(1)}</strong> / {truck.max_volume_cbm} m³</span>
                  </div>

                  <div className="text-[11px] text-indigo-900 font-semibold pt-1 border-t border-indigo-100 flex justify-between">
                    <span>Remaining Payload Space:</span>
                    <span>{truck.max_weight_kg - truck.booked_weight_kg} kg free</span>
                  </div>
                </div>

                {/* Pooled Shipments in this truck */}
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between font-bold text-slate-700">
                    <span>Consolidated Loads ({pooledShipments.length} Shippers):</span>
                    <span className="text-emerald-600 font-bold">
                      Revenue: ₹{pool ? Math.round(pool.total_trip_cost).toLocaleString() : (truck.booked_weight_kg * 4).toLocaleString()}
                    </span>
                  </div>

                  {pooledShipments.length === 0 ? (
                    <p className="text-slate-400 italic text-[11px]">No shipments pooled yet. Open for bookings along corridor.</p>
                  ) : (
                    <div className="divide-y divide-slate-100 max-h-36 overflow-y-auto space-y-1">
                      {pooledShipments.map((s) => (
                        <div key={s.id} className="pt-1.5 flex items-center justify-between text-[11px]">
                          <div>
                            <span className="font-semibold text-slate-800">{s.title}</span>
                            <span className="text-slate-400 block">{s.weight_kg} kg · OTP: {s.delivery_otp}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900">₹{s.allocated_cost?.toLocaleString()}</span>
                            <button
                              onClick={() => setRatingShipment(s)}
                              className="bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 transition"
                              title="Leave performance review for this shipper"
                            >
                              <Star className="w-3 h-3 text-amber-500 fill-amber-500" /> Rate Shipper
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Milestone Checkpoint Manager (Feature 5) */}
                {pool && pool.waypoints && (
                  <div className="space-y-2 pt-2 border-t border-slate-100 text-xs">
                    <span className="font-bold text-slate-700 flex items-center gap-1">
                      <Navigation className="w-3.5 h-3.5 text-sky-600" /> Highway Stop Waypoints:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      {pool.waypoints.slice(0, 4).map((wp, idx) => (
                        <label
                          key={idx}
                          className={`flex items-center gap-2 p-2 rounded-lg border text-[11px] cursor-pointer transition ${
                            wp.completed ? "bg-emerald-50 border-emerald-300 text-emerald-900 font-semibold" : "bg-slate-50 border-slate-200 text-slate-600"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={wp.completed}
                            onChange={(e) => handleToggleWaypoint(pool.id, idx, e.target.checked)}
                            className="rounded text-emerald-600"
                          />
                          <span className="truncate">{wp.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* State Transition Actions */}
              <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
                {pool ? (
                  <div className="flex items-center gap-2">
                    {pool.status === "LOCKED" && (
                      <button
                        onClick={() => handleUpdateStatus(pool.id, "IN_TRANSIT")}
                        className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-3 py-1.5 rounded-lg transition"
                      >
                        Start Transit (Depart Origin)
                      </button>
                    )}

                    {pool.status === "IN_TRANSIT" && (
                      <button
                        onClick={() => handleUpdateStatus(pool.id, "COMPLETED")}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded-lg transition"
                      >
                        Arrived & Complete Pool
                      </button>
                    )}

                    <Link
                      href={`/tracking/${pooledShipments[0]?.id || 101}`}
                      className="text-sky-600 hover:underline font-bold flex items-center gap-1 ml-1"
                    >
                      Open Live Tracking →
                    </Link>
                  </div>
                ) : (
                  <span className="text-slate-400 text-xs italic">Awaiting AI pool locking...</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Truck Modal */}
      {showAddTruckModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">List New Truck / Route</h3>
              <button onClick={() => setShowAddTruckModal(false)} className="text-slate-400 hover:text-slate-700 font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateTruck} className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Truck Model</label>
                  <select
                    value={newTruckData.truck_type}
                    onChange={(e) => setNewTruckData({ ...newTruckData, truck_type: e.target.value })}
                    className="w-full p-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="14ft Eicher Canter">14ft Eicher Canter (4 Ton)</option>
                    <option value="Tata 407 (Medium Duty)">Tata 407 (2.5 Ton)</option>
                    <option value="Tata Ace (Chhota Hathi)">Tata Ace (1 Ton)</option>
                    <option value="19ft Container Truck">19ft Container (7.5 Ton)</option>
                    <option value="32ft Multi-Axle">32ft Multi-Axle (15 Ton)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Vehicle Registration No.</label>
                  <input
                    type="text"
                    value={newTruckData.registration_number}
                    onChange={(e) => setNewTruckData({ ...newTruckData, registration_number: e.target.value })}
                    className="w-full p-2 border border-slate-300 rounded-lg uppercase font-mono"
                    placeholder="KA-01-AB-1234"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Max Weight (kg)</label>
                  <input
                    type="number"
                    value={newTruckData.max_weight_kg}
                    onChange={(e) => setNewTruckData({ ...newTruckData, max_weight_kg: Number(e.target.value) })}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Max Volume (m³)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={newTruckData.max_volume_cbm}
                    onChange={(e) => setNewTruckData({ ...newTruckData, max_volume_cbm: Number(e.target.value) })}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Origin City</label>
                  <input
                    type="text"
                    value={newTruckData.origin_city}
                    onChange={(e) => setNewTruckData({ ...newTruckData, origin_city: e.target.value })}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Destination City</label>
                  <input
                    type="text"
                    value={newTruckData.destination_city}
                    onChange={(e) => setNewTruckData({ ...newTruckData, destination_city: e.target.value })}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Driver Name</label>
                  <input
                    type="text"
                    value={newTruckData.driver_name}
                    onChange={(e) => setNewTruckData({ ...newTruckData, driver_name: e.target.value })}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Rate per km (₹)</label>
                  <input
                    type="number"
                    value={newTruckData.rate_per_km}
                    onChange={(e) => setNewTruckData({ ...newTruckData, rate_per_km: Number(e.target.value) })}
                    className="w-full p-2 border border-slate-300 rounded-lg"
                    required
                  />
                </div>
              </div>

              <div className="pt-2">
                <label className="inline-flex items-center cursor-pointer font-bold text-amber-800">
                  <input
                    type="checkbox"
                    checked={newTruckData.is_return_trip}
                    onChange={(e) => setNewTruckData({ ...newTruckData, is_return_trip: e.target.checked })}
                    className="rounded text-amber-600 mr-2"
                  />
                  Mark as Empty Return-Trip (Prioritize for back-haul discount)
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setShowAddTruckModal(false)}
                  className="px-3 py-2 rounded-lg border text-slate-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold"
                >
                  Register Truck & Route
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rate Shipper Modal (Task 7) */}
      {ratingShipment && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <Star className="w-5 h-5 text-amber-500 fill-amber-500" />
                <h3 className="font-bold text-slate-900">Rate &amp; Review Shipper</h3>
              </div>
              <button
                onClick={() => setRatingShipment(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                &times;
              </button>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1">
              <p className="font-bold text-slate-800">{ratingShipment.title}</p>
              <p className="text-slate-500">Shipper ID: #{ratingShipment.shipper_id} &bull; {ratingShipment.weight_kg} kg payload</p>
            </div>

            <form onSubmit={handleSubmitShipperRating} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-600 font-semibold mb-1">
                  Overall Shipper Rating:
                </label>
                <div className="flex items-center gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setStarCount(star)}
                      className="p-1 text-amber-400 hover:scale-110 transition"
                    >
                      <Star className={`w-6 h-6 ${star <= starCount ? "fill-amber-400 text-amber-400" : "text-slate-300"}`} />
                    </button>
                  ))}
                  <span className="font-bold text-slate-700 ml-2">{starCount} / 5 Stars</span>
                </div>
              </div>

              <div>
                <label className="block text-slate-600 font-semibold mb-1">
                  Feedback on Cargo Packaging &amp; Loading Coordination:
                </label>
                <textarea
                  rows={3}
                  value={ratingComment}
                  onChange={(e) => setRatingComment(e.target.value)}
                  placeholder="e.g. Excellent pallet packaging, exact weight declared, punctual warehouse handover."
                  className="w-full border rounded-lg p-2.5 text-xs text-slate-800"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
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
                  Submit Shipper Review
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
