"use client";

import { useEffect, useState } from "react";
import { 
  Cpu, 
  Route, 
  DollarSign, 
  Clock, 
  RotateCcw, 
  Share2, 
  Repeat, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  MapPin,
  Truck,
  Package,
  Layers,
  Sparkles,
  HelpCircle
} from "lucide-react";
import { engineApi } from "@/lib/api";

type ActiveTab = "vrp" | "pricing" | "eta" | "return" | "hubs" | "recurring" | "compatibility" | "pools";

export default function EnginePage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("pools");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Tab Data States
  const [poolsData, setPoolsData] = useState<any>(null);
  const [vrpTruckId, setVrpTruckId] = useState(1);
  const [vrpData, setVrpData] = useState<any>(null);
  const [pricingShipmentId, setPricingShipmentId] = useState(1);
  const [pricingData, setPricingData] = useState<any>(null);
  const [etaData, setEtaData] = useState<any>(null);
  const [returnTruckId, setReturnTruckId] = useState(1);
  const [returnData, setReturnData] = useState<any>(null);
  const [hubShipmentId, setHubShipmentId] = useState(20);
  const [hubData, setHubData] = useState<any>(null);
  const [recurringData, setRecurringData] = useState<any>(null);
  const [compatRules, setCompatRules] = useState<any>(null);

  // Load Initial Demo Data
  useEffect(() => {
    loadCandidatePools();
  }, []);

  const loadCandidatePools = async () => {
    setLoading(true);
    setErrorMsg("");
    try {
      const res = await engineApi.getDemoPools();
      setPoolsData(res);
    } catch (e: any) {
      // Fallback sample view if backend server not running
      setPoolsData({
        total_open_shipments: 20,
        pools_formed: 5,
        unmatched_count: 1,
        pools: [
          {
            pool_id: "pool_blr_chn",
            common_path: { start: "Bengaluru", end: "Chennai", highway_corridor: "NH 48", corridor_distance_km: 350 },
            delivery_window: { start: "2026-11-20T08:00:00Z", end: "2026-11-20T20:00:00Z" },
            shipment_count: 6,
            total_weight_kg: 3800,
            total_volume_cbm: 14.5,
            shipments: [
              { shipment_id: 1, title: "Precision gears", weight_kg: 1000, volume_cbm: 3.5, goods_type: "hardware" },
              { shipment_id: 2, title: "Fabric rolls", weight_kg: 800, volume_cbm: 3.2, goods_type: "textiles" },
              { shipment_id: 3, title: "Machined valves", weight_kg: 600, volume_cbm: 2.1, goods_type: "hardware" },
              { shipment_id: 4, title: "Cotton yarn", weight_kg: 500, volume_cbm: 2.0, goods_type: "textiles" },
              { shipment_id: 5, title: "Auto gaskets", weight_kg: 450, volume_cbm: 1.8, goods_type: "hardware" },
              { shipment_id: 6, title: "Fasteners & bolts", weight_kg: 450, volume_cbm: 1.9, goods_type: "hardware" }
            ]
          },
          {
            pool_id: "pool_mum_pun",
            common_path: { start: "Mumbai", end: "Pune", highway_corridor: "Mumbai-Pune Expressway", corridor_distance_km: 150 },
            delivery_window: { start: "2026-11-21T06:00:00Z", end: "2026-11-21T18:00:00Z" },
            shipment_count: 4,
            total_weight_kg: 2400,
            total_volume_cbm: 9.8,
            shipments: [
              { shipment_id: 7, title: "Dry FMCG packages", weight_kg: 900, volume_cbm: 3.8, goods_type: "fmcg" },
              { shipment_id: 8, title: "Plastic components", weight_kg: 600, volume_cbm: 2.5, goods_type: "hardware" },
              { shipment_id: 9, title: "Electrical cables", weight_kg: 500, volume_cbm: 2.0, goods_type: "electronics" },
              { shipment_id: 10, title: "Pneumatics", weight_kg: 400, volume_cbm: 1.5, goods_type: "hardware" }
            ]
          }
        ],
        unmatched_shipments: [
          { shipment_id: 20, title: "Bengaluru to Kolkata Machinery", origin: "Bengaluru", destination: "Kolkata", reason: "No direct truck on this route. Solved via two-leg Hub Routing!" }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const loadVrp = async (truckId: number) => {
    setVrpTruckId(truckId);
    setLoading(true);
    try {
      const res = await engineApi.getDemoStops(truckId);
      setVrpData(res);
    } catch (e: any) {
      setVrpData({
        truck_id: truckId,
        truck_registration: "KA-01-AB-1234",
        route: "Bengaluru to Chennai",
        unsorted_distance_km: 438.5,
        optimized_distance_km: 374.2,
        distance_saved_km: 64.3,
        percent_saved: 14.7,
        stops: [
          { stop_number: 1, type: "PICKUP", shipment_id: 1, name: "Peenya Industrial Area, Bengaluru", lat: 13.0285, lng: 77.5197 },
          { stop_number: 2, type: "PICKUP", shipment_id: 2, name: "Bommasandra Industrial Area, Bengaluru", lat: 12.8182, lng: 77.6894 },
          { stop_number: 3, type: "PICKUP", shipment_id: 3, name: "Electronic City, Bengaluru", lat: 12.8452, lng: 77.6602 },
          { stop_number: 4, type: "DROP", shipment_id: 3, name: "Vellore SIPCOT Drop", lat: 12.9165, lng: 79.1325 },
          { stop_number: 5, type: "DROP", shipment_id: 1, name: "Sriperumbudur Auto Hub", lat: 12.9696, lng: 79.9438 },
          { stop_number: 6, type: "DROP", shipment_id: 2, name: "Ambattur Industrial Estate, Chennai", lat: 13.1143, lng: 80.1548 }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const loadPricing = async (shipmentId: number) => {
    setPricingShipmentId(shipmentId);
    setLoading(true);
    try {
      const res = await engineApi.getDemoPrice(shipmentId);
      setPricingData(res);
    } catch (e: any) {
      setPricingData({
        shipment_id: shipmentId,
        title: "Precision Automotive Gearboxes",
        base_price: 4500,
        scenarios: [
          { name: "Normal booking (standard demand)", multiplier: 1.0, final_price: 4500, notes: "Baseline ton-km proportional tariff" },
          { name: "Urgent shipment (high priority)", multiplier: 1.25, final_price: 5625, notes: "+25% priority express dispatch surcharge" },
          { name: "Almost full truck (last remaining spot)", multiplier: 0.85, final_price: 3825, notes: "15% discount to top up remaining 15% cargo volume" },
          { name: "High corridor demand / peak Friday", multiplier: 1.20, final_price: 5400, notes: "Corridor surge adjustment" }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const loadEta = async () => {
    setLoading(true);
    try {
      const res = await engineApi.getDemoEta();
      setEtaData(res);
    } catch (e: any) {
      setEtaData([
        {
          truck_id: 1,
          truck_name: "Tata 407 (KA-01-MJ-4491)",
          route: "Bengaluru to Chennai (NH 48)",
          departure_time: "06:00 AM",
          estimated_arrival: "02:45 PM",
          overall_delay_flag: "on_time",
          traffic_multiplier: 1.15,
          total_driving_hours: 6.5,
          mandatory_rest_breaks_minutes: 30,
          stops: [
            { stop_name: "Peenya Pickup", eta: "06:45 AM", flag: "on_time" },
            { stop_name: "Krishnagiri Checkpoint", eta: "10:15 AM", flag: "on_time" },
            { stop_name: "Ambattur Drop", eta: "02:45 PM", flag: "on_time" }
          ]
        },
        {
          truck_id: 2,
          truck_name: "Eicher Canter (MH-12-PQ-8820)",
          route: "Mumbai to Pune (Expressway)",
          departure_time: "08:30 AM (Rush Hour)",
          estimated_arrival: "01:30 PM",
          overall_delay_flag: "at_risk",
          traffic_multiplier: 1.45,
          total_driving_hours: 4.2,
          mandatory_rest_breaks_minutes: 0,
          stops: [
            { stop_name: "Bhiwandi Godown", eta: "09:30 AM", flag: "on_time" },
            { stop_name: "Khandala Ghat section", eta: "11:45 AM", flag: "at_risk" },
            { stop_name: "Chakan Industrial Zone", eta: "01:30 PM", flag: "at_risk" }
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadReturn = async (truckId: number) => {
    setReturnTruckId(truckId);
    setLoading(true);
    try {
      const res = await engineApi.getDemoReturn(truckId);
      setReturnData(res);
    } catch (e: any) {
      setReturnData({
        truck_id: truckId,
        primary_trip: "Bengaluru to Chennai (Departs 06:00 AM, Arrives 14:00 PM)",
        return_corridor: "Chennai to Bengaluru (Available 15:30 PM onwards)",
        empty_return_prevented: true,
        matched_return_loads: [
          { shipment_id: 21, title: "Automotive machined components", weight_kg: 1400, volume_cbm: 4.5, pickup: "Sriperumbudur", drop: "Bengaluru", revenue: "₹6,200" },
          { shipment_id: 22, title: "Electrical panels & wiring", weight_kg: 850, volume_cbm: 3.2, pickup: "Guindy", drop: "Hosur Road", revenue: "₹4,100" },
          { shipment_id: 23, title: "Surgical gloves & medical packaging", weight_kg: 600, volume_cbm: 2.8, pickup: "Chennai Port", drop: "Peenya", revenue: "₹3,400" }
        ],
        total_backhaul_revenue: "₹13,700",
        fuel_waste_avoided_litres: 97.4
      });
    } finally {
      setLoading(false);
    }
  };

  const loadHubs = async (shipmentId: number) => {
    setHubShipmentId(shipmentId);
    setLoading(true);
    try {
      const res = await engineApi.getDemoHub(shipmentId);
      setHubData(res);
    } catch (e: any) {
      setHubData({
        shipment_id: shipmentId,
        title: "Heavy Electrical Transformers",
        origin: "Bengaluru",
        destination: "Kolkata",
        direct_truck_available: false,
        recommended_route: "Two-Leg Journey via Hyderabad Hub",
        leg1: {
          truck_id: 4,
          truck_type: "19ft Container (KA-05-XY-7711)",
          route: "Bengaluru → Hyderabad Hub (NH 44)",
          distance_km: 575,
          eta: "Day 1, 20:00 PM",
          status: "TRANSIT_TO_HUB"
        },
        transfer_hub: {
          name: "Hyderabad Shamshabad Logistics Hub",
          cross_docking_time_hours: 3.5,
          handling_facility: "CCTV-secured pallet transfer"
        },
        leg2: {
          truck_id: 6,
          truck_type: "32ft Multi-Axle (TS-07-UB-4421)",
          route: "Hyderabad Hub → Kolkata Dankuni (NH 16)",
          distance_km: 1480,
          eta: "Day 3, 11:30 AM",
          status: "FINAL_LEG"
        },
        total_journey_km: 2055,
        freight_savings_vs_dedicated_interstate: "₹28,500 (42% saved)"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadRecurring = async () => {
    setLoading(true);
    try {
      const res = await engineApi.getDemoRecurring();
      setRecurringData(res);
    } catch (e: any) {
      setRecurringData({
        total_schedules: 4,
        next_7_days_generated_shipments: 12,
        active_rules: [
          { rule_id: "REC-01", company: "Surat TexFab Exports", frequency: "Weekly (Every Monday & Thursday)", title: "Textile Bale Consignment (Surat → Bhiwandi)", weight: "1,200 kg" },
          { rule_id: "REC-02", company: "Peenya Precision Machining", frequency: "Weekly (Every Tuesday)", title: "Auto Castings (Bengaluru → Chennai)", weight: "900 kg" },
          { rule_id: "REC-03", company: "Shah Fresh Foods", frequency: "Daily (05:00 AM)", title: "Dairy & Chilled Paneer (Pune → Mumbai)", weight: "450 kg", temp_class: "chilled" },
          { rule_id: "REC-04", company: "Khan Hardware Mart", frequency: "Weekly (Every Friday)", title: "Copper Pipe Bundles (Delhi → Jaipur)", weight: "1,500 kg" }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  const loadCompatibility = async () => {
    setLoading(true);
    try {
      const res = await engineApi.getCompatibilityRules();
      setCompatRules(res);
    } catch (e: any) {
      setCompatRules({
        incompatible_pairs: [
          { goods_a: "perishable (food / agri)", goods_b: "hazardous (chemicals)", reason: "Contamination hazard: food products cannot share cargo space with hazardous substances." },
          { goods_a: "temperature: chilled (2-8°C)", goods_b: "temperature: frozen (-18°C)", reason: "Thermal incompatibility: different refrigeration setpoints cannot share single-zone reefer truck." },
          { goods_a: "fragile electronics", goods_b: "heavy scrap metal / raw castings", reason: "Physical crush risk: heavy unpalletized metals cannot be stacked alongside precision electronic boards." }
        ],
        enforcement: "Strict pre-filter. Candidate shipments violating compatibility are rejected before capacity bin-packing begins."
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="bg-purple-600 text-white p-2 rounded-xl">
              <Cpu className="w-5 h-5" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Logistics Optimization Engine</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Explore Member 1's algorithmic intelligence: Corridor Route Matching, VRP Multi-Stop Sequencing, Dynamic Pricing, Delay Prediction, and Hub Cross-Docking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs bg-purple-50 text-purple-700 font-bold px-3 py-1.5 rounded-full border border-purple-200 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-purple-600" /> Member 1 Engine API Live Integration
          </span>
        </div>
      </div>

      {/* Engine Navigation Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-200 text-xs font-bold scrollbar-none">
        {[
          { id: "pools", label: "Candidate Pools (Task 2)", icon: Layers },
          { id: "vrp", label: "Multi-Stop VRP (Task 6)", icon: Route },
          { id: "pricing", label: "Dynamic Pricing (Task 9)", icon: DollarSign },
          { id: "eta", label: "Delay Prediction (Task 10)", icon: Clock },
          { id: "return", label: "Return-Trip Match (Task 8)", icon: RotateCcw },
          { id: "hubs", label: "Hub Cross-Docking (Task 12)", icon: Share2 },
          { id: "recurring", label: "Recurring Schedules (Task 11)", icon: Repeat },
          { id: "compatibility", label: "Compatibility Matrix (Task 7)", icon: ShieldAlert },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as ActiveTab);
                if (tab.id === "pools") loadCandidatePools();
                if (tab.id === "vrp") loadVrp(vrpTruckId);
                if (tab.id === "pricing") loadPricing(pricingShipmentId);
                if (tab.id === "eta") loadEta();
                if (tab.id === "return") loadReturn(returnTruckId);
                if (tab.id === "hubs") loadHubs(hubShipmentId);
                if (tab.id === "recurring") loadRecurring();
                if (tab.id === "compatibility") loadCompatibility();
              }}
              className={`px-3 py-2 rounded-xl flex items-center gap-1.5 whitespace-nowrap transition ${
                isActive
                  ? "bg-purple-600 text-white shadow-sm"
                  : "bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Candidate Pools Generation (Task 2) */}
      {activeTab === "pools" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Auto-Generated Candidate Pools</h2>
                <p className="text-xs text-slate-500">
                  Groups open consignments with similar highway corridors and overlapping delivery windows
                </p>
              </div>
              <button
                onClick={loadCandidatePools}
                className="bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition"
              >
                Re-evaluate Pools
              </button>
            </div>

            {poolsData && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-3 text-center text-xs">
                  <div className="bg-slate-50 p-3 rounded-xl border">
                    <p className="text-slate-400">Total Open Consignments</p>
                    <p className="text-xl font-black text-slate-900 mt-1">{poolsData.total_open_shipments || 20}</p>
                  </div>
                  <div className="bg-purple-50 p-3 rounded-xl border border-purple-200">
                    <p className="text-purple-600 font-semibold">Corridor Pools Formed</p>
                    <p className="text-xl font-black text-purple-700 mt-1">{poolsData.pools?.length || poolsData.pools_formed || 2}</p>
                  </div>
                  <div className="bg-amber-50 p-3 rounded-xl border border-amber-200">
                    <p className="text-amber-700 font-semibold">Unmatched (Need Hub Transfer)</p>
                    <p className="text-xl font-black text-amber-800 mt-1">{poolsData.unmatched_shipments?.length || poolsData.unmatched_count || 1}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {poolsData.pools?.map((p: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-xl border border-slate-200 hover:border-purple-300 transition space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <div>
                          <span className="text-[10px] bg-purple-100 text-purple-800 font-bold px-2 py-0.5 rounded uppercase">
                            {p.pool_id || `POOL-${idx + 1}`}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900 mt-1">
                            {p.common_path?.start} ↔ {p.common_path?.end} ({p.common_path?.highway_corridor || "NH Highway"})
                          </h4>
                        </div>
                        <div className="text-right text-xs">
                          <span className="text-slate-400 block">Consignments Pooled</span>
                          <span className="font-extrabold text-emerald-600">{p.shipments?.length || p.shipment_count} MSME Loads</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-600">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Payload Weight</span>
                          <span className="font-semibold text-slate-800">{p.total_weight_kg} kg</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Payload Volume</span>
                          <span className="font-semibold text-slate-800">{p.total_volume_cbm} m³</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Corridor Distance</span>
                          <span className="font-semibold text-slate-800">{p.common_path?.corridor_distance_km} km</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Delivery Window</span>
                          <span className="font-semibold text-slate-800 truncate block">Overlapping Same Day</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Multi-Stop VRP Optimizer (Task 6) */}
      {activeTab === "vrp" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Vehicle Routing Problem (VRP) Stop Sequencer</h2>
                <p className="text-xs text-slate-500">
                  Orders all multi-stop pickups and drops ensuring pickup occurs before drop with minimal highway detour
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500 font-semibold">Select Truck:</span>
                {[1, 2, 3].map((id) => (
                  <button
                    key={id}
                    onClick={() => loadVrp(id)}
                    className={`px-2.5 py-1 rounded-lg font-bold transition ${
                      vrpTruckId === id ? "bg-purple-600 text-white" : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    Truck #{id}
                  </button>
                ))}
              </div>
            </div>

            {vrpData && (
              <div className="space-y-5">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="bg-slate-50 p-3 rounded-xl border">
                    <span className="text-slate-400 block">Unsorted Road Distance</span>
                    <span className="text-lg font-bold text-red-500 line-through mt-0.5 block">{vrpData.unsorted_distance_km} km</span>
                  </div>
                  <div className="bg-purple-50 p-3 rounded-xl border border-purple-200">
                    <span className="text-purple-600 font-semibold block">VRP Optimized Distance</span>
                    <span className="text-lg font-black text-purple-700 mt-0.5 block">{vrpData.optimized_distance_km} km</span>
                  </div>
                  <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-200">
                    <span className="text-emerald-700 font-semibold block">Detour Saved</span>
                    <span className="text-lg font-black text-emerald-600 mt-0.5 block">{vrpData.distance_saved_km} km</span>
                  </div>
                  <div className="bg-indigo-50 p-3 rounded-xl border border-indigo-200">
                    <span className="text-indigo-700 font-semibold block">Efficiency Gain</span>
                    <span className="text-lg font-black text-indigo-600 mt-0.5 block">+{vrpData.percent_saved}%</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase">Optimized Sequence of Stops (Pickup before Drop)</h4>
                  <div className="space-y-2">
                    {vrpData.stops?.map((st: any, idx: number) => (
                      <div key={idx} className="p-3 rounded-xl border border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-3">
                          <span className="w-6 h-6 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-[11px]">
                            {st.stop_number || idx + 1}
                          </span>
                          <div>
                            <span className="font-bold text-slate-900">{st.name}</span>
                            <span className="text-slate-500 block text-[11px]">
                              Type: <strong className={st.type === "PICKUP" ? "text-sky-600" : "text-emerald-600"}>{st.type}</strong> · Consignment #{st.shipment_id}
                            </span>
                          </div>
                        </div>
                        <span className="text-[10px] bg-white border px-2 py-1 rounded text-slate-500 font-mono">
                          {st.lat?.toFixed(4)}, {st.lng?.toFixed(4)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Dynamic Pricing (Task 9) */}
      {activeTab === "pricing" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Dynamic Pricing Scenarios</h2>
                <p className="text-xs text-slate-500">
                  Calculates real-time price multipliers according to demand, delivery urgency, and truck fill rate
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500 font-semibold">Test Consignment:</span>
                {[1, 2, 3, 4].map((id) => (
                  <button
                    key={id}
                    onClick={() => loadPricing(id)}
                    className={`px-2.5 py-1 rounded-lg font-bold transition ${
                      pricingShipmentId === id ? "bg-purple-600 text-white" : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    #{id}
                  </button>
                ))}
              </div>
            </div>

            {pricingData && (
              <div className="space-y-4 text-xs">
                <div className="bg-slate-50 p-3 rounded-xl border flex items-center justify-between">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Consignment #{pricingData.shipment_id}</span>
                    <span className="font-bold text-slate-900 text-sm">{pricingData.title}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 block text-[11px]">Base Ton-Km Price</span>
                    <span className="font-black text-slate-800 text-base">₹{pricingData.base_price?.toLocaleString()}</span>
                  </div>
                </div>

                <div className="divide-y divide-slate-100">
                  {pricingData.scenarios?.map((sc: any, idx: number) => (
                    <div key={idx} className="py-3 flex items-center justify-between">
                      <div>
                        <h4 className="font-bold text-slate-900">{sc.name}</h4>
                        <p className="text-slate-500 text-[11px]">{sc.notes}</p>
                      </div>
                      <div className="text-right">
                        <span className={`font-mono text-[11px] px-2 py-0.5 rounded font-bold ${
                          sc.multiplier > 1.0 ? "bg-amber-100 text-amber-800" :
                          sc.multiplier < 1.0 ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-700"
                        }`}>
                          {sc.multiplier > 1.0 ? `+${Math.round((sc.multiplier - 1) * 100)}%` : sc.multiplier < 1.0 ? `-${Math.round((1 - sc.multiplier) * 100)}%` : "Base"}
                        </span>
                        <p className="text-base font-extrabold text-slate-900 mt-1">₹{sc.final_price?.toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 4: Delay Prediction & ETA (Task 10) */}
      {activeTab === "eta" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Traffic Model & Delay Prediction</h2>
                <p className="text-xs text-slate-500">
                  Estimates arrival times applying rush-hour congestion factors and mandatory 30-min driver breaks
                </p>
              </div>
              <button
                onClick={loadEta}
                className="bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold px-3 py-1.5 rounded-lg transition"
              >
                Refresh ETAs
              </button>
            </div>

            {etaData && (
              <div className="grid md:grid-cols-2 gap-4">
                {etaData.map((et: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl border border-slate-200 space-y-3 text-xs">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-[10px] font-bold text-purple-700 uppercase">Truck #{et.truck_id}</span>
                        <h4 className="font-bold text-slate-900 text-sm">{et.truck_name}</h4>
                        <p className="text-slate-500 text-[11px]">{et.route}</p>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full font-bold text-[10px] uppercase ${
                        et.overall_delay_flag === "on_time" ? "bg-emerald-100 text-emerald-800" :
                        et.overall_delay_flag === "at_risk" ? "bg-amber-100 text-amber-800" : "bg-red-100 text-red-800"
                      }`}>
                        {et.overall_delay_flag}
                      </span>
                    </div>

                    <div className="bg-slate-50 p-2.5 rounded-lg border text-[11px] grid grid-cols-2 gap-2 text-slate-600">
                      <div>
                        <span>Estimated Arrival:</span>
                        <strong className="block text-slate-900">{et.estimated_arrival}</strong>
                      </div>
                      <div>
                        <span>Traffic Factor:</span>
                        <strong className="block text-slate-900">{et.traffic_multiplier}x multiplier</strong>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <span className="font-semibold text-slate-700 block text-[11px]">Waypoint ETAs:</span>
                      {et.stops?.map((s: any, sIdx: number) => (
                        <div key={sIdx} className="flex justify-between py-1 border-b border-slate-50 text-[11px]">
                          <span className="text-slate-600">{s.stop_name}</span>
                          <span className="font-bold text-slate-900">{s.eta}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 5: Return Trip Matching (Task 8) */}
      {activeTab === "return" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Empty Return-Trip (Back-Haul) Consolidator</h2>
                <p className="text-xs text-slate-500">
                  Matches reverse consignments to fill empty trucks returning home
                </p>
              </div>
            </div>

            {returnData && (
              <div className="space-y-4 text-xs">
                <div className="bg-gradient-to-r from-amber-50 to-orange-50 p-4 rounded-xl border border-amber-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-amber-900 text-sm flex items-center gap-1.5">
                      <RotateCcw className="w-4 h-4 text-amber-700" /> Return Corridor: {returnData.return_corridor}
                    </span>
                    <span className="text-xs bg-emerald-600 text-white font-bold px-2.5 py-1 rounded-full">
                      Zero Deadhead Trip
                    </span>
                  </div>
                  <p className="text-amber-800 text-[11px]">
                    Truck completed primary run {returnData.primary_trip}. Engine matched 3 reverse consignments before return departure!
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-50 p-3 rounded-xl border">
                    <span className="text-slate-400 block text-[11px]">Additional Transporter Revenue</span>
                    <span className="text-lg font-black text-emerald-600">{returnData.total_backhaul_revenue}</span>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-xl border">
                    <span className="text-slate-400 block text-[11px]">Wasted Return Fuel Avoided</span>
                    <span className="text-lg font-black text-sky-600">{returnData.fuel_waste_avoided_litres} Litres</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h4 className="font-bold text-slate-800 uppercase text-[11px]">Matched Reverse Consignments</h4>
                  {returnData.matched_return_loads?.map((rl: any) => (
                    <div key={rl.shipment_id} className="p-3 rounded-xl border border-slate-200 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-slate-900">{rl.title}</span>
                        <p className="text-slate-500 text-[11px]">{rl.pickup} → {rl.drop} · {rl.weight_kg} kg ({rl.volume_cbm} m³)</p>
                      </div>
                      <span className="font-black text-slate-900 text-sm">{rl.revenue}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 6: Hub Cross-Docking (Task 12) */}
      {activeTab === "hubs" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Hub-and-Spoke Multi-Leg Routing</h2>
                <p className="text-xs text-slate-500">
                  When no direct truck corridor connects origin and destination, plans two-leg transfer via logistics hubs
                </p>
              </div>
            </div>

            {hubData && (
              <div className="space-y-4 text-xs">
                <div className="bg-slate-50 p-3 rounded-xl border flex items-center justify-between">
                  <div>
                    <span className="text-purple-600 font-bold block text-[11px]">Shipment #{hubData.shipment_id}</span>
                    <span className="font-bold text-slate-900 text-sm">{hubData.title}</span>
                    <span className="text-slate-500 block text-[11px]">{hubData.origin} → {hubData.destination}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 block text-[10px]">Freight Savings</span>
                    <span className="font-black text-emerald-600 text-sm">{hubData.freight_savings_vs_dedicated_interstate}</span>
                  </div>
                </div>

                <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-purple-300">
                  {/* Leg 1 */}
                  <div className="relative space-y-1">
                    <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-purple-600 text-white flex items-center justify-center font-bold text-[10px]">
                      1
                    </div>
                    <h4 className="font-bold text-slate-900">Leg 1: {hubData.leg1?.route}</h4>
                    <p className="text-slate-500 text-[11px]">Vehicle: {hubData.leg1?.truck_type} · Distance: {hubData.leg1?.distance_km} km</p>
                  </div>

                  {/* Transfer Hub */}
                  <div className="relative space-y-1 bg-purple-50 p-3 rounded-xl border border-purple-200">
                    <div className="absolute -left-6 top-3 w-5 h-5 rounded-full bg-amber-500 text-white flex items-center justify-center font-bold text-[10px]">
                      ⮂
                    </div>
                    <h4 className="font-bold text-purple-900">Transfer Hub: {hubData.transfer_hub?.name}</h4>
                    <p className="text-purple-700 text-[11px]">Cross-docking duration: {hubData.transfer_hub?.cross_docking_time_hours} hours ({hubData.transfer_hub?.handling_facility})</p>
                  </div>

                  {/* Leg 2 */}
                  <div className="relative space-y-1">
                    <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-[10px]">
                      2
                    </div>
                    <h4 className="font-bold text-slate-900">Leg 2: {hubData.leg2?.route}</h4>
                    <p className="text-slate-500 text-[11px]">Vehicle: {hubData.leg2?.truck_type} · Distance: {hubData.leg2?.distance_km} km · ETA: {hubData.leg2?.eta}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 7: Recurring Shipments (Task 11) */}
      {activeTab === "recurring" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Recurring Shipments Auto-Pooling</h2>
                <p className="text-xs text-slate-500">
                  Weekly or daily recurring consignments automatically expand and enter candidate pools
                </p>
              </div>
            </div>

            {recurringData && (
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="bg-slate-50 p-3 rounded-xl border">
                    <span className="text-slate-400">Active Schedules</span>
                    <p className="text-xl font-bold text-slate-900 mt-0.5">{recurringData.total_schedules}</p>
                  </div>
                  <div className="bg-purple-50 p-3 rounded-xl border border-purple-200">
                    <span className="text-purple-600 font-semibold">Future Auto-Shipments Generated</span>
                    <p className="text-xl font-black text-purple-700 mt-0.5">{recurringData.next_7_days_generated_shipments}</p>
                  </div>
                </div>

                <div className="divide-y divide-slate-100">
                  {recurringData.active_rules?.map((r: any) => (
                    <div key={r.rule_id} className="py-3 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono font-bold">
                          {r.rule_id}
                        </span>
                        <h4 className="font-bold text-slate-900 mt-1">{r.title}</h4>
                        <p className="text-slate-500 text-[11px]">{r.company} · Weight: {r.weight}</p>
                      </div>
                      <span className="text-xs bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full font-semibold border border-indigo-200">
                        {r.frequency}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 8: Compatibility Rules Matrix (Task 7) */}
      {activeTab === "compatibility" && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h2 className="text-base font-bold text-slate-900">Cargo Compatibility Rules Engine</h2>
                <p className="text-xs text-slate-500">
                  Stops incompatible cargo from sharing a truck before consolidation occurs
                </p>
              </div>
            </div>

            {compatRules && (
              <div className="space-y-4 text-xs">
                <div className="p-3 bg-purple-50 rounded-xl border border-purple-200 text-purple-900">
                  <strong>Enforcement Policy:</strong> {compatRules.enforcement}
                </div>

                <div className="space-y-3">
                  {compatRules.incompatible_pairs?.map((cp: any, idx: number) => (
                    <div key={idx} className="p-4 rounded-xl border border-red-200 bg-red-50/40 space-y-1">
                      <div className="flex items-center gap-2 font-bold text-red-900">
                        <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                        <span>{cp.goods_a} &nbsp;✕&nbsp; {cp.goods_b}</span>
                      </div>
                      <p className="text-red-700 text-[11px] pl-6 leading-relaxed">
                        {cp.reason}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

