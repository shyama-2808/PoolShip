"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  CheckCircle2,
  Clock,
  MapPin,
  Truck,
  ShieldCheck,
  Navigation,
  ArrowLeft,
  FileCheck2,
  Camera,
  PenTool,
  RotateCcw,
  Download,
  AlertCircle
} from "lucide-react";
import { mockStore, Shipment, Pool, Truck as TruckType } from "@/lib/mockStore";

export default function TrackingPage(_props: any) {
  const routeParams = useParams();
  const [shipment, setShipment] = useState<Shipment | null>(null);
  const [pool, setPool] = useState<Pool | null>(null);
  const [truck, setTruck] = useState<TruckType | null>(null);

  // Proof of Delivery OTP & Signature & Photo
  const [enteredOtp, setEnteredOtp] = useState("");
  const [podStatusMsg, setPodStatusMsg] = useState("");
  const [podSuccess, setPodSuccess] = useState(false);
  const [podPhoto, setPodPhoto] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasSignature, setHasSignature] = useState(false);

  useEffect(() => {
    const update = () => {
      const paramId = routeParams?.id;
      const sId = Number(paramId) || 101;
      const s = mockStore.getShipmentById(sId) || mockStore.getShipments()[0];
      setShipment(s);
      if (s?.pool_id) {
        const p = mockStore.getPoolById(s.pool_id);
        setPool(p || null);
        if (p) {
          const tr = mockStore.getTruckById(p.truck_id);
          setTruck(tr || null);
        }
      }
    };
    update();
    const unsub = mockStore.subscribe(update);
    return () => unsub();
  }, [routeParams?.id]);

  // Canvas signature helpers
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    setIsDrawing(true);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
    ctx.beginPath();
    ctx.moveTo(clientX - rect.left, clientY - rect.top);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#0f172a";
    ctx.lineTo(clientX - rect.left, clientY - rect.top);
    ctx.stroke();
    setHasSignature(true);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearSignature = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
  };

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => {
      setPodPhoto(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleSimulatePhoto = () => {
    // Generates a mock delivery handover placeholder SVG data URI
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="240" viewBox="0 0 400 240"><rect width="400" height="240" fill="#0f172a"/><rect x="20" y="20" width="360" height="200" fill="#1e293b" rx="8" stroke="#334155" stroke-width="2"/><text x="200" y="90" fill="#38bdf8" font-family="sans-serif" font-size="16" font-weight="bold" text-anchor="middle">POOLSHIP CARGO HANDOVER PROOF</text><text x="200" y="125" fill="#94a3b8" font-family="sans-serif" font-size="12" text-anchor="middle">Consignment Pallet Verified at Destination Warehouse</text><text x="200" y="155" fill="#4ade80" font-family="monospace" font-size="13" text-anchor="middle">GPS: 12.9716 N, 77.5946 E &bull; ${new Date().toLocaleDateString()}</text><text x="200" y="185" fill="#e2e8f0" font-family="sans-serif" font-size="11" text-anchor="middle">Cargo Intact &amp; Packaging Undamaged</text></svg>`;
    const dataUri = `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
    setPodPhoto(dataUri);
  };

  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    if (!shipment) return;

    const signatureData = hasSignature && canvasRef.current ? canvasRef.current.toDataURL() : "Signed digitally by consignee receiver";
    const res = mockStore.verifyOtpAndDeliver(
      shipment.id,
      enteredOtp,
      signatureData,
      podPhoto || undefined
    );
    setPodStatusMsg(res.message);
    if (res.success) {
      setPodSuccess(true);
    }
  };

  if (!shipment) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center text-slate-500">
        Loading consignment data...
      </div>
    );
  }

  const waypoints = pool?.waypoints || [
    { name: shipment.origin_address, lat: shipment.origin_lat, lng: shipment.origin_lng, type: "PICKUP", completed: true },
    { name: "Highway Transit Corridor", lat: 12.8, lng: 78.5, type: "CHECKPOINT", completed: shipment.status === "IN_TRANSIT" || shipment.status === "DELIVERED" },
    { name: shipment.destination_address, lat: shipment.dest_lat, lng: shipment.dest_lng, type: "DROP", completed: shipment.status === "DELIVERED" }
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Breadcrumb & Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <Link href="/shipper" className="text-xs font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1 transition">
          <ArrowLeft className="w-4 h-4" /> Back to My Shipments
        </Link>
        <span className="text-xs bg-slate-100 text-slate-600 font-mono px-2.5 py-1 rounded">
          Tracking ID: PS-TRK-{shipment.id}
        </span>
      </div>

      {/* Hero Overview */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-6">
        <div className="space-y-1">
          <span className="text-xs font-bold text-sky-600 uppercase tracking-wider">Live Pooled Consignment</span>
          <h1 className="text-2xl font-black text-slate-900">{shipment.title}</h1>
          <p className="text-xs text-slate-500">
            Pool: <strong className="text-slate-800">{pool?.pool_code || "POOL-PENDING"}</strong> · Corridor: {pool?.corridor_name || `${shipment.origin_address.split(",")[0]} → ${shipment.destination_address.split(",")[0]}`}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-xs text-slate-400 block">Current Status</span>
            <span className={`text-sm font-black px-3 py-1 rounded-full inline-block mt-0.5 ${shipment.status === "DELIVERED" ? "bg-emerald-100 text-emerald-800" :
              shipment.status === "IN_TRANSIT" ? "bg-amber-100 text-amber-800 animate-pulse" :
                shipment.status === "POOLED" ? "bg-sky-100 text-sky-800" : "bg-purple-100 text-purple-800"
              }`}>
              {shipment.status === "IN_TRANSIT" ? "🚛 In Transit (Highway)" : shipment.status}
            </span>
          </div>
        </div>
      </div>

      {/* Visual Interactive Map Representation (Feature 5) */}
      <div className="bg-slate-900 text-white rounded-2xl overflow-hidden shadow-xl border border-slate-800">
        <div className="p-4 bg-slate-800/80 border-b border-slate-700 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-emerald-400" />
            <span className="font-bold">Live Highway Corridor Map (OSRM / OpenStreetMap Engine)</span>
          </div>
          <span className="text-slate-400">Total Distance: {pool?.total_distance_km || 348} km</span>
        </div>

        {/* SVG Schematic Corridor Map with animated truck pin */}
        <div className="relative p-6 sm:p-10 bg-gradient-to-b from-slate-900 to-slate-950 flex flex-col justify-center items-center min-h-[220px]">
          <div className="w-full max-w-2xl relative">
            {/* Highway Route Polyline */}
            <div className="h-2 w-full bg-slate-800 rounded-full relative overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 via-sky-500 to-amber-500 transition-all duration-1000 rounded-full"
                style={{
                  width: shipment.status === "DELIVERED" ? "100%" : shipment.status === "IN_TRANSIT" ? "65%" : "20%"
                }}
              />
            </div>

            {/* Waypoint Markers */}
            <div className="flex justify-between items-center -mt-4 relative">
              {waypoints.map((wp, idx) => {
                const isReached = wp.completed;
                return (
                  <div key={idx} className="flex flex-col items-center group relative cursor-pointer">
                    <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition ${isReached ? "bg-emerald-500 border-white text-white shadow-lg shadow-emerald-500/50" : "bg-slate-800 border-slate-600 text-slate-400"
                      }`}>
                      {isReached ? <CheckCircle2 className="w-3.5 h-3.5" /> : <span className="text-[10px]">{idx + 1}</span>}
                    </div>
                    <span className="text-[11px] font-semibold text-slate-300 mt-2 max-w-[100px] text-center truncate">
                      {wp.name.split(" ")[0]}
                    </span>
                    <span className="text-[9px] text-slate-500">
                      {wp.type}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-8 text-xs text-slate-400 flex items-center gap-4">
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Completed Waypoint</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" /> Current Highway Corridor</span>
            <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-slate-700" /> Planned Drop</span>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-12 gap-8">
        {/* Milestone Timeline Journey */}
        <div className="lg:col-span-7 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Clock className="w-4 h-4 text-sky-600" /> Milestone Tracking Timeline
          </h2>

          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {waypoints.map((wp, idx) => (
              <div key={idx} className="relative space-y-1 text-xs">
                <div className={`absolute -left-6 top-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center bg-white ${wp.completed ? "border-emerald-500 text-emerald-600" : "border-slate-300 text-slate-300"
                  }`}>
                  {wp.completed && <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full" />}
                </div>

                <div className="flex items-center justify-between">
                  <h3 className={`font-bold ${wp.completed ? "text-slate-900" : "text-slate-400"}`}>
                    {wp.name}
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${wp.completed ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-400"
                    }`}>
                    {wp.completed ? "Checked In" : "Pending"}
                  </span>
                </div>
                <p className="text-slate-500">
                  {wp.type === "PICKUP" ? "Consignment pallet loaded into shared cargo hold." :
                    wp.type === "DROP" ? "Final destination warehouse delivery point." : "Highway corridor toll plaza check."}
                </p>
              </div>
            ))}
          </div>

          {/* Assigned Driver & Truck Info */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-600 text-white p-2 rounded-lg">
                <Truck className="w-4 h-4" />
              </div>
              <div>
                <p className="font-bold text-slate-900">{truck?.driver_name || "Suresh Gowda"} ({truck?.truck_type || "14ft Canter"})</p>
                <p className="text-slate-500">Reg: {truck?.registration_number || "KA-01-MJ-4491"} · Phone: {truck?.driver_phone || "+91 94480 33445"}</p>
              </div>
            </div>
            <a
              href={`tel:${truck?.driver_phone || "+919448033445"}`}
              className="bg-white hover:bg-slate-100 border border-slate-300 px-3 py-1.5 rounded-lg font-semibold text-slate-800 transition"
            >
              Call Driver
            </a>
          </div>
        </div>

        {/* Digital Proof of Delivery (Feature 9) */}
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                <h2 className="text-base font-bold">Digital Proof of Delivery (POD)</h2>
              </div>
              <span className="text-[10px] bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded font-mono font-bold">
                OTP: {shipment.delivery_otp}
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              To guarantee zero cargo loss in shared pools, the driver cannot mark the goods delivered without the receiver's secure OTP and digital signature.
            </p>

            {podStatusMsg && (
              <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${podSuccess ? "bg-emerald-950/80 border border-emerald-500 text-emerald-300" : "bg-red-950/80 border border-red-500 text-red-300"
                }`}>
                {podSuccess ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
                <span>{podStatusMsg}</span>
              </div>
            )}

            {shipment.status === "DELIVERED" ? (
              <div className="bg-emerald-950/50 border border-emerald-500/40 p-4 rounded-xl space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-4 h-4" /> Handover Completed &amp; Verified
                  </div>
                  <span className="text-[10px] bg-emerald-900 text-emerald-200 px-2 py-0.5 rounded font-mono font-bold">
                    OTP: {shipment.delivery_otp}
                  </span>
                </div>
                <p className="text-slate-300">
                  Delivered on {shipment.delivered_at ? new Date(shipment.delivered_at).toLocaleDateString("en-IN") : new Date().toLocaleDateString("en-IN")}. Consignee signature, photo evidence, and OTP archived into audit ledger.
                </p>

                {/* E-Way Bill Number Badge */}
                <div className="bg-slate-800/80 px-3 py-2 rounded-lg border border-slate-700 flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-400">E-Way Bill Number:</span>
                  <span className="font-bold text-sky-400 tracking-wider">EWB-2026{shipment.id.toString().padStart(6, "0")}</span>
                </div>

                {/* POD Evidence Previews */}
                <div className="pt-2 border-t border-slate-800 grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-[10px] text-slate-400 block mb-1">Consignee Signature</span>
                    {shipment.proof_signature && shipment.proof_signature.startsWith("data:") ? (
                      <img src={shipment.proof_signature} alt="Signature" className="h-12 w-full bg-white rounded border border-slate-700 object-contain p-1" />
                    ) : (
                      <div className="h-12 w-full bg-slate-800 text-[10px] text-slate-400 flex items-center justify-center rounded border border-slate-700">
                        Digital Signature Archived
                      </div>
                    )}
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block mb-1">Unloading Proof Photo</span>
                    {shipment.proof_photo ? (
                      <img src={shipment.proof_photo} alt="Dropoff Photo" className="h-12 w-full bg-slate-800 rounded border border-slate-700 object-cover" />
                    ) : (
                      <div className="h-12 w-full bg-slate-800 text-[10px] text-slate-400 flex items-center justify-center rounded border border-slate-700">
                        Physical Inspection OK
                      </div>
                    )}
                  </div>
                </div>

                <Link
                  href="/shipper"
                  className="inline-block mt-1 w-full text-center bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold px-3 py-2 rounded-lg text-xs transition shadow-sm"
                >
                  Download GST Invoice in Shipper Portal &rarr;
                </Link>
              </div>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    4-Digit Receiver Handover OTP
                  </label>
                  <input
                    type="text"
                    maxLength={4}
                    value={enteredOtp}
                    onChange={(e) => setEnteredOtp(e.target.value)}
                    placeholder={`Enter OTP (e.g. ${shipment.delivery_otp})`}
                    className="w-full bg-slate-800 border border-slate-700 text-white px-3 py-2.5 rounded-lg font-mono text-center tracking-widest text-sm focus:outline-none focus:border-sky-500"
                    required
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">
                    (Receiver gives this code to the driver upon unloading cargo)
                  </span>
                </div>

                {/* Dropoff Photo Evidence Upload (Task 9) */}
                <div>
                  <div className="flex items-center justify-between text-slate-300 font-semibold mb-1">
                    <span className="flex items-center gap-1">
                      <Camera className="w-3.5 h-3.5 text-emerald-400" /> Unloading / Handover Photo Proof
                    </span>
                    {podPhoto && (
                      <button
                        type="button"
                        onClick={() => setPodPhoto(null)}
                        className="text-[10px] text-red-400 hover:text-red-300"
                      >
                        Remove
                      </button>
                    )}
                  </div>

                  {podPhoto ? (
                    <div className="relative rounded-lg overflow-hidden border border-slate-700 bg-slate-800 p-1">
                      <img src={podPhoto} alt="POD Preview" className="w-full h-24 object-cover rounded" />
                      <div className="text-[10px] text-emerald-400 font-medium text-center mt-1">
                        &check; Photo Attached &amp; Geo-tagged
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-2 gap-2">
                      <label className="cursor-pointer flex flex-col items-center justify-center p-2.5 border border-dashed border-slate-700 hover:border-sky-500 rounded-lg bg-slate-800/60 transition text-center">
                        <Camera className="w-4 h-4 text-slate-400 mb-1" />
                        <span className="text-[10px] text-slate-300 font-medium">Upload File</span>
                        <input type="file" accept="image/*" onChange={handlePhotoUpload} className="hidden" />
                      </label>
                      <button
                        type="button"
                        onClick={handleSimulatePhoto}
                        className="flex flex-col items-center justify-center p-2.5 border border-slate-700 hover:border-emerald-500 rounded-lg bg-slate-800/60 transition text-center"
                      >
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 mb-1" />
                        <span className="text-[10px] text-slate-300 font-medium">Simulate Photo</span>
                      </button>
                    </div>
                  )}
                  <span className="text-[10px] text-slate-400 block mt-1">Accepts cargo condition photo or receiver handover snap</span>
                </div>

                {/* Digital Signature Pad */}
                <div>
                  <div className="flex items-center justify-between text-slate-300 font-semibold mb-1">
                    <span className="flex items-center gap-1">
                      <PenTool className="w-3.5 h-3.5 text-sky-400" /> Consignee Digital Signature
                    </span>
                    <button
                      type="button"
                      onClick={clearSignature}
                      className="text-[10px] text-slate-400 hover:text-white flex items-center gap-1"
                    >
                      <RotateCcw className="w-3 h-3" /> Clear
                    </button>
                  </div>
                  <div className="bg-white rounded-lg overflow-hidden border border-slate-700">
                    <canvas
                      ref={canvasRef}
                      width={320}
                      height={100}
                      className="w-full h-20 touch-none cursor-crosshair bg-white"
                      onMouseDown={startDrawing}
                      onMouseMove={draw}
                      onMouseUp={stopDrawing}
                      onMouseLeave={stopDrawing}
                      onTouchStart={startDrawing}
                      onTouchMove={draw}
                      onTouchEnd={stopDrawing}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 block mt-1">Sign above using mouse or touch</span>
                </div>

                <button
                  type="submit"
                  className="w-full bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold py-2.5 rounded-xl transition flex items-center justify-center gap-2 shadow-lg"
                >
                  <FileCheck2 className="w-4 h-4" /> Verify OTP &amp; Mark Delivered
                </button>
              </form>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
