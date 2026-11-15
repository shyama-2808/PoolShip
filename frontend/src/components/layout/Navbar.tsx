import Link from "next/link";
import { Truck, ShieldCheck, UserCheck, Activity, Leaf } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="bg-sky-600 text-white p-2 rounded-lg font-bold flex items-center justify-center">
            <Truck className="w-5 h-5" />
          </div>
          <span className="text-xl font-black tracking-tight text-slate-900">
            Pool<span className="text-sky-600">Ship</span>
          </span>
          <span className="ml-1 text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
            <Leaf className="w-3 h-3" /> Green PTL
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
          <Link href="/shipper" className="hover:text-sky-600 transition flex items-center gap-1.5">
            <UserCheck className="w-4 h-4 text-sky-500" />
            Shipper Portal
          </Link>
          <Link href="/transporter" className="hover:text-sky-600 transition flex items-center gap-1.5">
            <Truck className="w-4 h-4 text-indigo-500" />
            Transporters
          </Link>
          <Link href="/admin" className="hover:text-sky-600 transition flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Admin & Analytics
          </Link>
          <Link href="/tracking/1" className="hover:text-sky-600 transition flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-amber-500" />
            Live Tracking Demo
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/shipper"
            className="text-xs sm:text-sm bg-sky-600 hover:bg-sky-700 text-white font-medium px-4 py-2 rounded-lg shadow-sm transition"
          >
            Post Shipment
          </Link>
        </div>
      </div>
    </header>
  );
}
