"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Truck,
  ShieldCheck,
  UserCheck,
  Building,
  Mail,
  Lock,
  Phone,
  FileText,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Sparkles
} from "lucide-react";
import { mockStore, User } from "@/lib/mockStore";

export default function LoginPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"signin" | "register">("signin");

  // Sign in form state
  const [loginEmail, setLoginEmail] = useState("ramesh.kumar@peenya-metals.in");
  const [loginPassword, setLoginPassword] = useState("password123");
  const [loginError, setLoginError] = useState("");

  // Register form state
  const [regData, setRegData] = useState({
    full_name: "",
    email: "",
    role: "SHIPPER" as "SHIPPER" | "TRANSPORTER",
    company_name: "",
    phone: "",
    gst_number: "",
  });
  const [regError, setRegError] = useState("");
  const [regSuccess, setRegSuccess] = useState(false);

  const demoUsers = [
    {
      id: 1,
      name: "Ramesh Kumar",
      role: "SHIPPER",
      company: "Peenya Industrial Tools",
      email: "ramesh.kumar@peenya-metals.in",
      desc: "Posts cargo, books pool shares, downloads GST invoices",
      route: "/shipper"
    },
    {
      id: 2,
      name: "Vijay Transport",
      role: "TRANSPORTER",
      company: "VRL Highway Express",
      email: "vijay@vrl-logistics.in",
      desc: "Registers corridors, tracks load fill rate, completes trips",
      route: "/transporter"
    },
    {
      id: 3,
      name: "Priya Sharma",
      role: "ADMIN",
      company: "PoolShip Trust Operations",
      email: "admin@poolship.in",
      desc: "Verifies 15-char GSTINs, resolves disputes, monitors fleet analytics",
      route: "/admin"
    },
    {
      id: 4,
      name: "Suresh Electronics",
      role: "SHIPPER (Unverified)",
      company: "Suresh Audio Parts",
      email: "suresh@sureshelec.in",
      desc: "Demonstrates KYC blocking on booking attempts until verified",
      route: "/shipper"
    }
  ];

  const handleDemoLogin = (userId: number, targetRoute: string) => {
    mockStore.setCurrentUser(userId);
    router.push(targetRoute);
  };

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");

    const user = mockStore.loginUserByEmail(loginEmail);
    if (!user) {
      setLoginError("No account found with this email. Try one of the quick demo personas below or register.");
      return;
    }

    if (user.role === "SHIPPER") router.push("/shipper");
    else if (user.role === "TRANSPORTER") router.push("/transporter");
    else router.push("/admin");
  };

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault();
    setRegError("");

    if (!regData.full_name || !regData.email || !regData.company_name) {
      setRegError("Please fill in all required profile fields.");
      return;
    }

    if (regData.gst_number && regData.gst_number.trim().length !== 15) {
      setRegError("Indian GSTIN must be exactly 15 alphanumeric characters (e.g. 29AABCU9603R1ZM).");
      return;
    }

    const newUser = mockStore.registerUser({
      full_name: regData.full_name.trim(),
      email: regData.email.trim(),
      role: regData.role,
      company_name: regData.company_name.trim(),
      phone: regData.phone.trim() || "+91 98000 12345",
      gst_number: regData.gst_number.trim().toUpperCase() || "29AABCU9603R1ZM",
    });

    setRegSuccess(true);
    setTimeout(() => {
      if (newUser.role === "SHIPPER") router.push("/shipper");
      else router.push("/transporter");
    }, 1200);
  };

  return (
    <div className="min-h-[85vh] py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto flex flex-col justify-center space-y-8">
      {/* Page Title */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-1.5 bg-sky-100 text-sky-800 text-xs font-bold px-3 py-1 rounded-full">
          <Truck className="w-3.5 h-3.5 text-sky-600" />
          PoolShip Access Portal (Member 2 &bull; Feature 1)
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
          Welcome to <span className="text-sky-600">PoolShip</span>
        </h1>
        <p className="text-sm text-slate-500 max-w-lg mx-auto">
          Sign in to your role-based dashboard, register your MSME business or highway transport fleet, or test with pre-configured personas.
        </p>
      </div>

      <div className="grid lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Form (Sign in or Register) */}
        <div className="lg:col-span-7 bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
          {/* Tab Selector */}
          <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-bold">
            <button
              onClick={() => { setActiveTab("signin"); setLoginError(""); }}
              className={`flex-1 py-2.5 rounded-lg transition ${
                activeTab === "signin" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Sign In Existing User
            </button>
            <button
              onClick={() => { setActiveTab("register"); setRegError(""); }}
              className={`flex-1 py-2.5 rounded-lg transition ${
                activeTab === "register" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500 hover:text-slate-900"
              }`}
            >
              Create New Business Account
            </button>
          </div>

          {activeTab === "signin" ? (
            <form onSubmit={handleSignIn} className="space-y-4 text-xs">
              {loginError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{loginError}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Business Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    required
                    placeholder="e.g. ramesh.kumar@peenya-metals.in"
                    className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl text-xs focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Account Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    required
                    className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl text-xs focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full bg-sky-600 hover:bg-sky-700 text-white font-bold py-3 rounded-xl transition flex items-center justify-center gap-2 shadow-sm text-sm"
              >
                Sign In &amp; Launch Dashboard <ArrowRight className="w-4 h-4" />
              </button>

              <div className="text-center text-[11px] text-slate-400 pt-2">
                Tip: You can also click any of the 4 demo personas on the right for instant 1-click access!
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4 text-xs">
              {regError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{regError}</span>
                </div>
              )}

              {regSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Account registered! Redirecting to your customized dashboard...</span>
                </div>
              )}

              {/* Role selection */}
              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Select Platform Role</label>
                <div className="grid grid-cols-2 gap-3">
                  <label className={`flex items-center gap-2.5 p-3 rounded-xl border cursor-pointer transition ${
                    regData.role === "SHIPPER" ? "border-sky-500 bg-sky-50/80 text-sky-900 font-bold" : "border-slate-200 hover:bg-slate-50 text-slate-700"
                  }`}>
                    <input
                      type="radio"
                      name="role"
                      value="SHIPPER"
                      checked={regData.role === "SHIPPER"}
                      onChange={() => setRegData({ ...regData, role: "SHIPPER" })}
                      className="hidden"
                    />
                    <UserCheck className="w-4 h-4 text-sky-600" />
                    <div>
                      <p className="text-xs">Shipper (MSME)</p>
                      <p className="text-[10px] text-slate-400 font-normal">I want to send cargo</p>
                    </div>
                  </label>

                  <label className={`flex items-center gap-2.5 p-3 rounded-xl border cursor-pointer transition ${
                    regData.role === "TRANSPORTER" ? "border-indigo-500 bg-indigo-50/80 text-indigo-900 font-bold" : "border-slate-200 hover:bg-slate-50 text-slate-700"
                  }`}>
                    <input
                      type="radio"
                      name="role"
                      value="TRANSPORTER"
                      checked={regData.role === "TRANSPORTER"}
                      onChange={() => setRegData({ ...regData, role: "TRANSPORTER" })}
                      className="hidden"
                    />
                    <Truck className="w-4 h-4 text-indigo-600" />
                    <div>
                      <p className="text-xs">Transporter</p>
                      <p className="text-[10px] text-slate-400 font-normal">I have truck capacity</p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Full Name</label>
                  <input
                    type="text"
                    value={regData.full_name}
                    onChange={(e) => setRegData({ ...regData, full_name: e.target.value })}
                    required
                    placeholder="e.g. Anand Murthy"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Company / Trade Name</label>
                  <input
                    type="text"
                    value={regData.company_name}
                    onChange={(e) => setRegData({ ...regData, company_name: e.target.value })}
                    required
                    placeholder="e.g. Murthy Logistics &amp; Fab"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Business Email</label>
                  <input
                    type="email"
                    value={regData.email}
                    onChange={(e) => setRegData({ ...regData, email: e.target.value })}
                    required
                    placeholder="anand@murthyfab.in"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:border-sky-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Mobile Phone</label>
                  <input
                    type="tel"
                    value={regData.phone}
                    onChange={(e) => setRegData({ ...regData, phone: e.target.value })}
                    placeholder="+91 98450 11223"
                    className="w-full px-3 py-2 border border-slate-300 rounded-xl focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700 flex items-center justify-between">
                  <span>15-Digit GSTIN (for Instant KYC)</span>
                  <span className="text-[10px] text-slate-400 font-normal">State code + PAN + entity</span>
                </label>
                <div className="relative">
                  <FileText className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    maxLength={15}
                    value={regData.gst_number}
                    onChange={(e) => setRegData({ ...regData, gst_number: e.target.value.toUpperCase() })}
                    placeholder="e.g. 29ABCDE1234F1Z5"
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-xl font-mono uppercase focus:outline-none focus:border-sky-500"
                  />
                </div>
                <span className="text-[10px] text-slate-400 block">
                  New registrations undergo automated verification with the Admin verification queue.
                </span>
              </div>

              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl transition flex items-center justify-center gap-2 shadow-sm text-sm"
              >
                Create Account &amp; Submit KYC <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}
        </div>

        {/* Right Column: 1-Click Demo Personas */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900 text-white p-6 rounded-3xl shadow-lg space-y-4 border border-slate-800">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <div>
                <h3 className="font-bold text-sm">1-Click Demo Access</h3>
                <p className="text-[11px] text-slate-400">Instantly switch between testing personas</p>
              </div>
            </div>

            <div className="space-y-2.5">
              {demoUsers.map((u) => (
                <button
                  key={u.id}
                  onClick={() => handleDemoLogin(u.id, u.route)}
                  className="w-full text-left p-3.5 rounded-2xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 hover:border-sky-500 transition group space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-white group-hover:text-sky-400 transition">{u.name}</span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                      u.role.includes("SHIPPER") ? "bg-sky-950 text-sky-300 border border-sky-800" :
                      u.role.includes("TRANSPORTER") ? "bg-indigo-950 text-indigo-300 border border-indigo-800" :
                      "bg-purple-950 text-purple-300 border border-purple-800"
                    }`}>
                      {u.role}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 font-medium">{u.company}</p>
                  <p className="text-[10px] text-slate-400 leading-tight">{u.desc}</p>
                  <div className="pt-1 text-[10px] text-sky-400 font-bold flex items-center gap-1 group-hover:translate-x-1 transition">
                    Launch {u.name.split(" ")[0]}&apos;s View &rarr;
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

