"use client";

import React from "react";
import { 
  PhoneCall, 
  Wifi, 
  WifiOff, 
  Globe, 
  Bell,
  Search
} from "lucide-react";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();
  const isOnline = true; // Simulating connectivity state

  if (pathname === "/login") return null;

  return (
    <header className="h-20 bg-white/80 backdrop-blur-md border-b border-stone-100 flex items-center justify-between px-8 z-40 fixed top-0 left-20 lg:left-24 right-0">
      <div className="flex items-center gap-6">
        <div className="hidden lg:flex items-center gap-2 bg-stone-100 px-4 py-2 rounded-2xl border border-stone-200">
          <Search size={16} className="text-stone-400" />
          <input 
            type="text" 
            placeholder="Search symptoms or history..." 
            className="bg-transparent border-none text-xs focus:ring-0 w-48 text-stone-600 font-medium"
          />
        </div>
        
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100">
          {isOnline ? <Wifi size={14} className="text-emerald-600" /> : <WifiOff size={14} className="text-rose-500" />}
          <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider">
            {isOnline ? "Server Online" : "Offline Mode"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Multilingual Toggle */}
        <button className="flex items-center gap-2 px-4 py-2 hover:bg-stone-50 rounded-xl transition-colors border border-stone-100 text-stone-600">
          <Globe size={18} />
          <span className="text-xs font-bold uppercase tracking-tight">English (India)</span>
        </button>

        <button className="p-2 text-stone-400 hover:text-emerald-600 transition-colors relative">
          <Bell size={20} />
          <div className="absolute top-2 right-2 w-1.5 h-1.5 bg-rose-500 rounded-full border border-white" />
        </button>

        <div className="h-8 w-[1px] bg-stone-200 mx-2" />

        {/* Emergency Fast-Call */}
        <a 
          href="tel:1962"
          className="flex items-center gap-3 bg-rose-50 text-rose-600 px-5 py-2.5 rounded-2xl border border-rose-100 hover:bg-rose-100 transition-all shadow-sm group"
        >
          <div className="bg-rose-500 text-white p-1 rounded-lg group-hover:animate-bounce">
            <PhoneCall size={16} />
          </div>
          <div className="flex flex-col items-start leading-none">
            <span className="text-[10px] font-bold uppercase tracking-widest opacity-70">Emergency</span>
            <span className="text-sm font-black">1962</span>
          </div>
        </a>
      </div>
    </header>
  );
}
