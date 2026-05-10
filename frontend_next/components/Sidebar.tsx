"use client";

import React, { useState, useEffect } from "react";
import { 
  History, 
  Search, 
  Calendar, 
  ChevronRight,
  Filter,
  Activity,
  Trash2
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  onSelectCase: (caseId: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export default function Sidebar({ onSelectCase, isOpen, setIsOpen }: SidebarProps) {
  const [history, setHistory] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${API_URL}/history/user/demo_user`);
        const data = await response.json();
        if (data.cases) setHistory(data.cases);
      } catch (e) {
        console.error("Failed to fetch history", e);
      }
    };
    if (isOpen) fetchHistory();
  }, [isOpen]);

  const filteredHistory = history.filter(item => 
    item.animal_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.primary_diagnosis.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <aside className={cn(
      "h-screen bg-stone-50 border-r border-stone-200 flex flex-col transition-all duration-500 ease-in-out z-30 fixed left-20 lg:left-24",
      isOpen ? "w-80 shadow-2xl shadow-stone-900/5" : "w-0 overflow-hidden border-none"
    )}>
      <div className="p-6 border-b border-stone-200">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <div className="bg-emerald-100 p-2 rounded-xl text-emerald-700">
              <History size={18} />
            </div>
            <h2 className="text-sm font-black text-stone-900 uppercase tracking-widest">Case History</h2>
          </div>
          <button 
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-stone-200 rounded-lg transition-colors text-stone-400"
          >
            <ChevronRight size={18} className="rotate-180" />
          </button>
        </div>

        <div className="relative group">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400 group-focus-within:text-emerald-500 transition-colors" />
          <input 
            type="text" 
            placeholder="Search cases..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-stone-200 rounded-xl text-xs focus:ring-4 focus:ring-emerald-500/5 focus:border-emerald-500/30 transition-all outline-none"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        <div className="flex items-center justify-between px-2 mb-2">
          <span className="text-[10px] font-bold text-stone-400 uppercase tracking-widest flex items-center gap-2">
            <Activity size={12} />
            Diagnostic Logs
          </span>
          <button className="text-[10px] font-bold text-emerald-600 uppercase hover:underline">
            View All
          </button>
        </div>

        <div className="space-y-1">
          {filteredHistory.length > 0 ? (
            filteredHistory.map((item) => (
              <button 
                key={item.case_id}
                onClick={() => onSelectCase(item.case_id)}
                className="w-full group p-4 rounded-2xl bg-white border border-stone-100 hover:border-emerald-200 hover:shadow-lg hover:shadow-emerald-900/5 transition-all flex flex-col gap-1 relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-1 h-full bg-emerald-500 opacity-0 group-hover:opacity-100 transition-all" />
                
                <div className="flex items-center justify-between mb-1">
                  <span className={cn(
                    "text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-widest",
                    item.severity === "high" ? "bg-rose-50 text-rose-600" : "bg-emerald-50 text-emerald-600"
                  )}>
                    {item.animal_type}
                  </span>
                  <span className="text-[10px] text-stone-400 flex items-center gap-1">
                    <Calendar size={10} />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
                
                <div className="text-sm font-bold text-stone-900 line-clamp-1 group-hover:text-emerald-700 transition-colors">
                  {item.primary_diagnosis}
                </div>
                
                <div className="flex items-center justify-between mt-1">
                  <div className="text-[11px] text-stone-500 italic">
                    Confidence: {Math.round(item.confidence_score * 100)}%
                  </div>
                  <ChevronRight size={14} className="text-stone-300 group-hover:text-emerald-500 group-hover:translate-x-1 transition-all" />
                </div>
              </button>
            ))
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-center px-6">
              <div className="w-12 h-12 bg-stone-100 rounded-full flex items-center justify-center mb-4 text-stone-300">
                <Search size={24} />
              </div>
              <p className="text-xs text-stone-400 font-medium">No cases match your search</p>
            </div>
          )}
        </div>
      </div>

      <div className="p-4 bg-white border-t border-stone-200">
        <button className="w-full py-3 bg-stone-100 text-stone-600 rounded-xl text-xs font-bold uppercase tracking-widest hover:bg-stone-200 transition-colors flex items-center justify-center gap-2">
          <Trash2 size={14} />
          Clear All History
        </button>
      </div>
    </aside>
  );
}
