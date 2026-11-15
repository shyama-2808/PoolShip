"use client";

import { useState } from "react";
import { 
  Package, 
  MapPin, 
  Weight, 
  Calendar, 
  CheckCircle, 
  TrendingDown, 
  Leaf, 
  AlertCircle,
  Truck
} from "lucide-react";

export default function ShipperDashboard() {
  const [formData, setFormData] = useState({
    title: "Electronic Components & Spares",
    goods_type: "Hardware",
    weight_kg: 850,
    volume_cbm: 2.8,
    origin_address: "Peenya Industrial Area, Bangalore",
    destination_address: "Ambattur Industrial Estate, Chennai",
    is_perishable: false,
    is_hazardous: false,
    is_fragile: true,
  });

  const [postedShipments, setPostedShipments] = useState([
    {
      id: 101,
      title: "Textile Rolls (Cotton Fabrics)",
      origin: "Surat, Gujarat",
      destination: "Bhiwandi, Maharashtra",
      weight: "1,200 kg",
      volume: "4.2 m³",
      status: "POOLED",
      poolId: "POOL-882",
      truck: "14ft Canter (MH04-AB-1234)",
      cost: "₹7,200",
      savings: "₹5,800 (45%)",
      co2Saved: "92 kg",
    },
    {
      id: 102,
      title: "Auto Ancillary Machined Castings",
      origin: "Bommasandra, Bangalore",
      destination: "Sri City, Andhra Pradesh",
      weight: "650 kg",
      volume: "1.5 m³",
      status: "MATCHED",
      poolId: "POOL-884",
      truck: "Tata 407 (KA01-EF-9988)",
      cost: "₹4,100",
      savings: "₹3,400 (45%)",
      co2Saved: "58 kg",
    }
  ]);

  const [successMsg, setSuccessMsg] = useState("");

  const handlePost = (e: React.FormEvent) => {
    e.preventDefault();
    const newEntry = {
      id: Date.now(),
      title: formData.title,
      origin: formData.origin_address,
      destination: formData.destination_address,
      weight: `${formData.weight_kg} kg`,
      volume: `${formData.volume_cbm} m³`,
      status: "MATCHED",
      poolId: "POOL-" + Math.floor(100 + Math.random() * 900),
      truck: "Tata Ace (KA05-XY-7711)",
      cost: "₹5,200",
      savings: "₹4,100 (44%)",
      co2Saved: "74 kg",
    };
    setPostedShipments([newEntry, ...postedShipments]);
    setSuccessMsg("Shipment posted! AI Route Engine found 2 matching truck corridors.");
    setTimeout(() => setSuccessMsg(""), 5000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Shipper Portal</h1>
          <p className="text-sm text-slate-500 mt-1">
            Post partial loads, match with verified trucks on your route, and track transparent ton-km cost splits.
          </p>
        </div>
        <div className="flex items-center gap-3 bg-emerald-50 text-emerald-800 text-xs px-3 py-1.5 rounded-lg border border-emerald-200 font-semibold">
          <Leaf className="w-4 h-4 text-emerald-600" />
          Cumulative CO₂ Avoided: 224 kg
        </div>
      </div>

      {successMsg && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-800 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
          <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <div className="grid lg:grid-cols-12 gap-8">
        {/* Post Shipment Form */}
        <div className="lg:col-span-5 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Package className="w-5 h-5 text-sky-600" />
            <h2 className="text-lg font-bold text-slate-900">Post a Shipment (Partial Load)</h2>
          </div>

          <form onSubmit={handlePost} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Cargo Title / Description</label>
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
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Goods Category</label>
                <select
                  value={formData.goods_type}
                  onChange={(e) => setFormData({ ...formData, goods_type: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white"
                >
                  <option value="Hardware">Hardware / Machined</option>
                  <option value="Textiles">Textiles & Garments</option>
                  <option value="FMCG">FMCG / Dry Goods</option>
                  <option value="Electronics">Electronics</option>
                  <option value="Perishable">Perishable (Agri/Food)</option>
                  <option value="Chemicals">Industrial Chemicals</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Weight (kg)</label>
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
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Est. Volume (m³)</label>
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
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Special Attributes</label>
                <div className="flex items-center gap-2 pt-2">
                  <label className="inline-flex items-center text-xs">
                    <input
                      type="checkbox"
                      checked={formData.is_fragile}
                      onChange={(e) => setFormData({ ...formData, is_fragile: e.target.checked })}
                      className="rounded text-sky-600 mr-1"
                    />
                    Fragile
                  </label>
                  <label className="inline-flex items-center text-xs">
                    <input
                      type="checkbox"
                      checked={formData.is_perishable}
                      onChange={(e) => setFormData({ ...formData, is_perishable: e.target.checked })}
                      className="rounded text-sky-600 mr-1"
                    />
                    Perishable
                  </label>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Pickup Location</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    value={formData.origin_address}
                    onChange={(e) => setFormData({ ...formData, origin_address: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Drop Location</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    value={formData.destination_address}
                    onChange={(e) => setFormData({ ...formData, destination_address: e.target.value })}
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm"
                    required
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-2.5 rounded-xl shadow transition text-sm"
            >
              Post & Find Pool Matches
            </button>
          </form>
        </div>

        {/* Active Shipments & Matched Pools */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Your Active Shipments & Matched Pools</h2>
            <span className="text-xs text-slate-500">{postedShipments.length} consignments</span>
          </div>

          <div className="space-y-4">
            {postedShipments.map((s) => (
              <div key={s.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">{s.title}</h3>
                    <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                      <Truck className="w-3.5 h-3.5 text-sky-500" /> Assigned: {s.truck} ({s.poolId})
                    </p>
                  </div>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                    s.status === "POOLED" ? "bg-emerald-100 text-emerald-800" : "bg-sky-100 text-sky-800"
                  }`}>
                    {s.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400 block">Route</span>
                    <span className="font-semibold text-slate-800">{s.origin.split(",")[0]} → {s.destination.split(",")[0]}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Payload</span>
                    <span className="font-semibold text-slate-800">{s.weight} ({s.volume})</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Allocated Cost</span>
                    <span className="font-bold text-slate-900">{s.cost}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Shipper Savings</span>
                    <span className="font-bold text-emerald-600 flex items-center gap-0.5">
                      <TrendingDown className="w-3.5 h-3.5" /> {s.savings}
                    </span>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <span className="flex items-center gap-1 text-emerald-700 font-medium">
                    <Leaf className="w-3.5 h-3.5" /> Avoided {s.co2Saved} CO₂ via consolidated truck sharing
                  </span>
                  <a href={`/tracking/${s.id}`} className="text-sky-600 hover:underline font-semibold">
                    View Live Tracking →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
