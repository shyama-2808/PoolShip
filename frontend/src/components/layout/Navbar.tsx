"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Truck,
  ShieldCheck,
  UserCheck,
  Activity,
  Leaf,
  Bell,
  Globe,
  RotateCcw,
  CheckCircle2,
  ChevronDown,
  User as UserIcon,
  MessageSquare,
  Cpu,
  Menu,
  X
} from "lucide-react";
import { mockStore, User, NotificationItem } from "@/lib/mockStore";
import { translations, Locale } from "@/locales/translations";

export default function Navbar() {
  const pathname = usePathname();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [lang, setLang] = useState<Locale>("en");
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  useEffect(() => {
    const update = () => {
      setCurrentUser(mockStore.getCurrentUser());
      setUsers(mockStore.getUsers());
      setNotifications(mockStore.getNotifications());
      setLang(mockStore.getLanguage());
    };
    update();
    const unsubscribe = mockStore.subscribe(update);
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    setShowMobileMenu(false);
    setShowUserDropdown(false);
    setShowNotifDropdown(false);
  }, [pathname]);

  const t = translations[lang] || translations.en;

  const handleSwitchUser = (userId: number) => {
    mockStore.setCurrentUser(userId);
    setShowUserDropdown(false);
  };

  const handleSwitchLang = (newLang: Locale) => {
    mockStore.setLanguage(newLang);
    setLang(newLang);
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200 shadow-xs w-full max-w-full">
      <div className="w-full max-w-[1600px] mx-auto px-3 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2 xl:gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="bg-sky-600 text-white p-1.5 rounded-lg font-bold flex items-center justify-center shadow-xs">
            <Truck className="w-5 h-5" />
          </div>
          <span className="text-lg xl:text-xl font-black tracking-tight text-slate-900 whitespace-nowrap">
            Pool<span className="text-sky-600">Ship</span>
          </span>
          <span className="hidden 2xl:inline-flex text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200/80 font-semibold px-2 py-0.5 rounded-full items-center gap-1 whitespace-nowrap">
            <Leaf className="w-3 h-3 text-emerald-600 shrink-0" /> {t.greenPtl}
          </span>
        </Link>

        {/* Primary Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-0.5 xl:gap-1.5 text-xs xl:text-sm font-medium text-slate-600 shrink-0">
          <Link
            href="/shipper"
            className={`inline-flex items-center gap-1 xl:gap-1.5 px-2 xl:px-2.5 py-1.5 rounded-lg whitespace-nowrap transition shrink-0 ${
              pathname.startsWith("/shipper")
                ? "text-sky-700 bg-sky-50 font-semibold"
                : "hover:text-sky-600 hover:bg-slate-100/80"
            }`}
          >
            <UserCheck className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-sky-500 shrink-0" />
            <span>{t.shipperPortal}</span>
          </Link>

          <Link
            href="/transporter"
            className={`inline-flex items-center gap-1 xl:gap-1.5 px-2 xl:px-2.5 py-1.5 rounded-lg whitespace-nowrap transition shrink-0 ${
              pathname.startsWith("/transporter")
                ? "text-indigo-700 bg-indigo-50 font-semibold"
                : "hover:text-indigo-600 hover:bg-slate-100/80"
            }`}
          >
            <Truck className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-indigo-500 shrink-0" />
            <span>{t.transporterHub}</span>
          </Link>

          <Link
            href="/admin"
            className={`inline-flex items-center gap-1 xl:gap-1.5 px-2 xl:px-2.5 py-1.5 rounded-lg whitespace-nowrap transition shrink-0 ${
              pathname.startsWith("/admin")
                ? "text-emerald-700 bg-emerald-50 font-semibold"
                : "hover:text-emerald-600 hover:bg-slate-100/80"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-emerald-600 shrink-0" />
            <span>{t.adminConsole}</span>
          </Link>

          <Link
            href="/tracking/101"
            className={`inline-flex items-center gap-1 xl:gap-1.5 px-2 xl:px-2.5 py-1.5 rounded-lg whitespace-nowrap transition shrink-0 ${
              pathname.startsWith("/tracking")
                ? "text-amber-700 bg-amber-50 font-semibold"
                : "hover:text-amber-600 hover:bg-slate-100/80"
            }`}
          >
            <Activity className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-amber-500 shrink-0" />
            <span>{t.liveTracking}</span>
          </Link>

          <Link
            href="/carbon-savings"
            className={`inline-flex items-center gap-1 xl:gap-1.5 px-2 xl:px-2.5 py-1.5 rounded-lg whitespace-nowrap transition shrink-0 ${
              pathname === "/carbon-savings"
                ? "text-teal-700 bg-teal-50 font-semibold"
                : "hover:text-teal-600 hover:bg-slate-100/80"
            }`}
          >
            <Leaf className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-teal-600 shrink-0" />
            <span>{t.carbonDashboard}</span>
          </Link>

          <Link
            href="/engine"
            className={`inline-flex items-center gap-1 xl:gap-1.5 px-2 xl:px-2.5 py-1.5 rounded-lg whitespace-nowrap transition shrink-0 ${
              pathname === "/engine"
                ? "text-purple-700 bg-purple-50 font-semibold"
                : "hover:text-purple-600 hover:bg-slate-100/80"
            }`}
          >
            <Cpu className="w-3.5 h-3.5 xl:w-4 xl:h-4 text-purple-600 shrink-0" />
            <span>{t.smartEngine}</span>
          </Link>
        </nav>

        {/* Right Tools: Language, Persona Switcher, Notifications, Reset, Mobile Hamburger */}
        <div className="flex items-center gap-1.5 xl:gap-2.5 shrink-0">
          {/* Language Switcher */}
          <div className="relative">
            <button
              onClick={() => handleSwitchLang(lang === "en" ? "hi" : lang === "hi" ? "kn" : "en")}
              className="flex items-center gap-1 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1.5 rounded-lg transition whitespace-nowrap shrink-0"
              title="Switch language: English / Hindi / Kannada"
            >
              <Globe className="w-3.5 h-3.5 text-slate-500" />
              <span>{lang.toUpperCase()}</span>
            </button>
          </div>

          {/* Notifications Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowNotifDropdown(!showNotifDropdown)}
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 relative transition shrink-0"
              title={t.notifications}
            >
              <Bell className="w-4 h-4" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse" />
              )}
            </button>

            {showNotifDropdown && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 p-3 z-50 space-y-2">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1">
                    <MessageSquare className="w-3.5 h-3.5 text-sky-600" /> {t.notifications}
                  </span>
                  <span className="text-[11px] text-slate-400">{notifications.length} recent</span>
                </div>
                <div className="max-h-64 overflow-y-auto space-y-2 divide-y divide-slate-50">
                  {notifications.slice(0, 6).map((n) => (
                    <div key={n.id} className="pt-2 text-xs space-y-0.5">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-800">{n.title}</span>
                        <span className="text-[10px] text-slate-400">{n.timestamp}</span>
                      </div>
                      <p className="text-slate-600 text-[11px] leading-tight">{n.message}</p>
                      <span className="inline-block text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">
                        via {n.channel}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Active Persona Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowUserDropdown(!showUserDropdown)}
              className="flex items-center gap-1.5 text-xs font-semibold bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-200 px-2.5 xl:px-3 py-1.5 rounded-lg transition whitespace-nowrap shrink-0"
            >
              <UserIcon className="w-3.5 h-3.5 text-sky-600 shrink-0" />
              <span className="max-w-[85px] xl:max-w-[140px] truncate">
                {currentUser?.full_name.split(" ")[0]}
                <span className="hidden xl:inline"> ({currentUser?.role})</span>
              </span>
              <ChevronDown className="w-3 h-3 text-sky-500 shrink-0" />
            </button>

            {showUserDropdown && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 p-2 z-50 space-y-1">
                <div className="px-2 py-1.5 border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  {t.switchRole}
                </div>
                {users.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => handleSwitchUser(u.id)}
                    className={`w-full text-left px-2.5 py-2 rounded-lg text-xs flex items-center justify-between transition ${currentUser?.id === u.id ? "bg-sky-50 text-sky-800 font-bold" : "hover:bg-slate-50 text-slate-700"
                      }`}
                  >
                    <div>
                      <p className="font-medium">{u.full_name}</p>
                      <p className="text-[10px] text-slate-400">{u.company_name || u.role} · {u.role}</p>
                    </div>
                    {u.is_verified ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    ) : (
                      <span className="text-[9px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-bold">Unverified</span>
                    )}
                  </button>
                ))}

                <div className="pt-2 mt-1 border-t border-slate-100 flex items-center justify-between text-xs px-2">
                  <Link
                    href="/profile"
                    onClick={() => setShowUserDropdown(false)}
                    className="font-bold text-sky-600 hover:text-sky-700 hover:underline flex items-center gap-1"
                  >
                    <UserIcon className="w-3.5 h-3.5" /> View Profile &amp; Reviews
                  </Link>
                  <Link
                    href="/login"
                    onClick={() => setShowUserDropdown(false)}
                    className="text-[11px] text-slate-500 hover:text-slate-800 font-semibold"
                  >
                    Sign In &rarr;
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Data Reset Button */}
          <button
            onClick={() => {
              if (confirm("Reset local storage to original sample dataset (20 shipments, 5 trucks)?")) {
                mockStore.resetToSample();
              }
            }}
            className="p-1.5 text-slate-400 hover:text-slate-700 transition shrink-0"
            title="Reset to initial sample data"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          {/* Mobile Hamburger Toggle (< lg) */}
          <button
            onClick={() => setShowMobileMenu(!showMobileMenu)}
            className="lg:hidden p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition shrink-0"
            aria-label="Toggle navigation menu"
          >
            {showMobileMenu ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Drawer */}
      {showMobileMenu && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-4 py-3 space-y-1 shadow-lg">
          <Link
            href="/shipper"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
              pathname.startsWith("/shipper")
                ? "text-sky-700 bg-sky-50 font-bold"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <UserCheck className="w-4 h-4 text-sky-500" />
            <span>{t.shipperPortal}</span>
          </Link>

          <Link
            href="/transporter"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
              pathname.startsWith("/transporter")
                ? "text-indigo-700 bg-indigo-50 font-bold"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Truck className="w-4 h-4 text-indigo-500" />
            <span>{t.transporterHub}</span>
          </Link>

          <Link
            href="/admin"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
              pathname.startsWith("/admin")
                ? "text-emerald-700 bg-emerald-50 font-bold"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>{t.adminConsole}</span>
          </Link>

          <Link
            href="/tracking/101"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
              pathname.startsWith("/tracking")
                ? "text-amber-700 bg-amber-50 font-bold"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Activity className="w-4 h-4 text-amber-500" />
            <span>{t.liveTracking}</span>
          </Link>

          <Link
            href="/carbon-savings"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
              pathname === "/carbon-savings"
                ? "text-teal-700 bg-teal-50 font-bold"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Leaf className="w-4 h-4 text-teal-600" />
            <span>{t.carbonDashboard}</span>
          </Link>

          <Link
            href="/engine"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition ${
              pathname === "/engine"
                ? "text-purple-700 bg-purple-50 font-bold"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <Cpu className="w-4 h-4 text-purple-600" />
            <span>{t.smartEngine}</span>
          </Link>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs px-1">
            <Link
              href="/profile"
              className="text-sky-600 hover:underline font-bold flex items-center gap-1.5"
            >
              <UserIcon className="w-4 h-4" /> My Profile &amp; Reputation
            </Link>
            <Link
              href="/login"
              className="text-slate-600 hover:text-slate-900 font-semibold"
            >
              Sign In / Register &rarr;
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}