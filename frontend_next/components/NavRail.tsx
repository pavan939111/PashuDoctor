"use client";

import React from "react";
import { 
  Home, 
  History, 
  PlusCircle, 
  ShieldAlert, 
  LogOut, 
  Settings,
  Stethoscope
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

export default function NavRail() {
  const pathname = usePathname();
  const router = useRouter();

  const menuItems = [
    { icon: <Home size={22} />, label: "Home", path: "/" },
    { icon: <History size={22} />, label: "History", path: "/history" },
    { icon: <ShieldAlert size={22} />, label: "Health Alerts", path: "/alerts" },
  ];

  const handleLogout = () => {
    localStorage.removeItem("pashudoctor_token");
    router.push("/login");
  };

  if (pathname === "/login") return null;

  return (
    <aside className="w-20 lg:w-24 h-screen bg-emerald-950 border-r border-emerald-900 flex flex-col items-center py-8 z-50 fixed left-0 top-0">
      {/* Logo */}
      <div className="mb-12">
        <div className="bg-emerald-500/20 p-2.5 rounded-2xl border border-emerald-500/30">
          <Stethoscope className="text-emerald-400" size={26} />
        </div>
      </div>

      {/* Main Nav */}
      <nav className="flex-1 flex flex-col gap-8">
        <button 
          onClick={() => router.push("/")}
          className="group relative flex flex-col items-center"
        >
          <div className="bg-emerald-400 p-3 rounded-2xl shadow-lg shadow-emerald-400/20 hover:scale-110 transition-all text-emerald-950">
            <PlusCircle size={24} />
          </div>
          <span className="text-[10px] text-emerald-400 font-bold mt-2 uppercase tracking-tighter opacity-0 group-hover:opacity-100 transition-all">New</span>
        </button>

        <div className="w-8 h-[1px] bg-emerald-900 mx-auto my-2" />

        {menuItems.map((item) => (
          <button
            key={item.path}
            onClick={() => router.push(item.path)}
            className={cn(
              "group relative flex flex-col items-center transition-all",
              pathname === item.path ? "text-white" : "text-emerald-500 hover:text-emerald-300"
            )}
          >
            <div className={cn(
              "p-3 rounded-2xl transition-all group-hover:bg-white/5",
              pathname === item.path && "bg-emerald-800 shadow-inner"
            )}>
              {item.icon}
            </div>
            <span className={cn(
              "text-[10px] font-bold mt-1.5 uppercase tracking-tighter transition-all",
              pathname === item.path ? "opacity-100" : "opacity-0 group-hover:opacity-100"
            )}>
              {item.label}
            </span>
            {pathname === item.path && (
              <div className="absolute -left-4 top-1/2 -translate-y-1/2 w-1.5 h-8 bg-emerald-400 rounded-r-full" />
            )}
          </button>
        ))}
      </nav>

      {/* Footer Nav */}
      <div className="flex flex-col gap-6 pt-8 border-t border-emerald-900">
        <button className="text-emerald-500 hover:text-emerald-300 transition-colors p-3 rounded-2xl hover:bg-white/5">
          <Settings size={22} />
        </button>
        <button 
          onClick={handleLogout}
          className="text-emerald-500 hover:text-rose-400 transition-colors p-3 rounded-2xl hover:bg-rose-500/10"
        >
          <LogOut size={22} />
        </button>
      </div>
    </aside>
  );
}
