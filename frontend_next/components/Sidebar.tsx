"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Plus, 
  History, 
  PhoneCall, 
  Settings, 
  LogOut,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";

interface SidebarProps {
  onNewChat: () => void;
  onSelectCase: (caseId: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export default function Sidebar({ onNewChat, onSelectCase, isOpen, setIsOpen }: SidebarProps) {
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${API_URL}/history/user/demo_user`);
        const data = await response.json();
        if (data.cases) {
          setHistory(data.cases);
        }
      } catch (e) {
        console.error("Failed to fetch history", e);
      }
    };
    if (isOpen) fetchHistory();
  }, [isOpen]);

  const handleLogout = () => {
    localStorage.removeItem("pashudoctor_token");
    localStorage.removeItem("pashudoctor_user");
    window.location.href = "/login";
  };

  return (
    <aside className={cn(
      "h-full bg-stone-50 border-r border-stone-200 flex flex-col transition-all duration-300 relative",
      isOpen ? "w-72" : "w-0 overflow-hidden border-none"
    )}>
      {/* ... (Previous header and history items) */}
      <div className="p-4 border-b border-stone-200">
        <button 
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-primary text-white py-3 rounded-xl hover:bg-accent transition-colors shadow-sm"
        >
          <Plus size={20} />
          <span className="font-medium">New Diagnosis</span>
        </button>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <div className="text-[11px] font-bold text-stone-400 uppercase tracking-wider mb-2 px-2 flex items-center gap-2">
          <History size={12} />
          Recent Cases
        </div>
        
        <div className="space-y-1">
          {history.length > 0 ? (
            history.map((item) => (
              <button 
                key={item.case_id}
                onClick={() => onSelectCase(item.case_id)}
                className="w-full text-left p-3 rounded-lg hover:bg-stone-200/50 transition-colors group"
              >
                <div className="text-sm font-medium text-stone-800 line-clamp-1">
                  {item.animal_type} investigation
                </div>
                <div className="text-[11px] text-stone-500">
                  {item.primary_diagnosis} • {new Date(item.created_at).toLocaleDateString()}
                </div>
              </button>
            ))
          ) : (
            <div className="p-4 text-xs text-stone-400 text-center italic">
              No recent cases found
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-stone-200 bg-stone-100/50 space-y-2">
        <div className="bg-white p-3 rounded-xl border border-red-100 shadow-sm">
          <div className="text-[10px] text-red-500 font-bold uppercase mb-1">Emergency</div>
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-stone-900">1962</span>
            <PhoneCall size={18} className="text-red-500" />
          </div>
        </div>
        
        <div className="flex items-center justify-between pt-2">
          <button className="p-2 text-stone-500 hover:bg-stone-200 rounded-lg transition-colors">
            <Settings size={20} />
          </button>
          <button 
            onClick={handleLogout}
            className="p-2 text-stone-500 hover:bg-stone-200 rounded-lg transition-colors group"
          >
            <LogOut size={20} className="group-hover:text-red-500 transition-colors" />
          </button>
        </div>
      </div>
    </aside>
  );
}
