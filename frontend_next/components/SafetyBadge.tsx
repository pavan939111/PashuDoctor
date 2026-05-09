"use client";

import React from "react";
import { ShieldCheck, ShieldAlert, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface SafetyBadgeProps {
  status: "active" | "warning" | "error";
  className?: string;
}

export default function SafetyBadge({ status, className }: SafetyBadgeProps) {
  return (
    <div className={cn(
      "flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider shadow-sm border",
      status === "active" && "bg-green-50 text-green-700 border-green-100",
      status === "warning" && "bg-orange-50 text-orange-700 border-orange-100",
      status === "error" && "bg-red-50 text-red-700 border-red-100",
      className
    )}>
      {status === "active" && <ShieldCheck size={14} />}
      {status === "warning" && <Activity size={14} className="animate-pulse" />}
      {status === "error" && <ShieldAlert size={14} />}
      
      <span>AI Safety: {status === "active" ? "Guarded" : status}</span>
    </div>
  );
}
