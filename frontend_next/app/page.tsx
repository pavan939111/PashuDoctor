"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import ChatInterface from "@/components/ChatInterface";
import { Session, Message } from "@/types";
import { useRouter } from "next/navigation";
import { 
  AlertCircle, 
  ChevronRight,
  ShieldCheck,
  Activity,
  Microscope,
  Stethoscope
} from "lucide-react";
import { cn } from "@/lib/utils";

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("pashudoctor_token");
    const storedUser = localStorage.getItem("pashudoctor_user");
    if (!token || !storedUser) {
      router.push("/login");
    } else {
      setUser(JSON.parse(storedUser));
    }
  }, [router]);

  if (!user) return null;

  const handleNewChat = () => {
    setSession(null);
    setInitialMessages([]);
  };

  const handleSelectCase = async (caseId: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/analyze/${caseId}`);
      const data = await response.json();
      if (data.success) {
        setSession({
          case_id: data.case.id,
          user_id: data.case.user_id,
          animal_type: data.case.animal_type,
          last_diagnosis: data.diagnosis
        });
        const msgs: Message[] = data.chat_history.map((m: any, i: number) => ({
          id: `hist-${i}`,
          role: m.role,
          content: m.content,
          timestamp: new Date(m.created_at)
        }));
        setInitialMessages(msgs);
      }
    } catch (e) {
      console.error("Failed to load case", e);
    }
  };

  return (
    <div className="flex w-full h-full bg-white relative">
      <Sidebar 
        isOpen={isSidebarOpen} 
        setIsOpen={setIsSidebarOpen}
        onSelectCase={handleSelectCase}
      />
      
      <div className={cn(
        "flex-1 flex transition-all duration-500",
        isSidebarOpen ? "ml-80" : "ml-0"
      )}>
        <ChatInterface 
          session={session}
          onSessionUpdate={setSession}
          initialMessages={initialMessages}
        />

        {/* Professional Right Panel: Diagnostic Intelligence */}
        <aside className="hidden 2xl:flex w-[400px] h-full border-l border-stone-100 bg-stone-50/50 flex-col overflow-hidden">
          <div className="p-8 border-b border-stone-100 bg-white/50">
            <h3 className="text-[10px] font-black text-stone-400 uppercase tracking-[0.2em] mb-4">Case Intelligence</h3>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-emerald-600/20">
                <Microscope size={24} />
              </div>
              <div>
                <p className="text-xs font-bold text-stone-400 uppercase tracking-wider leading-none mb-1">Status</p>
                <p className="text-sm font-black text-stone-900 uppercase">Live Analysis</p>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-8 space-y-8">
            {session?.last_diagnosis ? (
              <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
                {/* Confidence Card */}
                <div className="bg-white p-6 rounded-[32px] border border-stone-100 shadow-xl shadow-stone-200/40 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-all">
                    <ShieldCheck size={64} className="text-emerald-600" />
                  </div>
                  <h4 className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-4">Grounding Score</h4>
                  <div className="flex items-end gap-3 mb-4">
                    <span className="text-5xl font-black text-stone-900 tracking-tighter">
                      {Math.round((session.last_diagnosis?.confidence_score || 0) * 100)}
                    </span>
                    <span className="text-lg font-bold text-stone-300 mb-1.5">%</span>
                  </div>
                  <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-500 transition-all duration-1000 ease-out" 
                      style={{ width: `${(session.last_diagnosis?.confidence_score || 0) * 100}%` }}
                    />
                  </div>
                  <p className="mt-4 text-[11px] text-stone-500 font-medium leading-relaxed">
                    Based on **MM-RAG** retrieval from 5,000+ clinical records and veterinary manuals.
                  </p>
                </div>

                {/* Evidence Section */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-stone-400">
                    <Activity size={16} />
                    <h4 className="text-[10px] font-black uppercase tracking-widest">Evidence Mapping</h4>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {session.last_diagnosis?.matching_symptoms?.map((sym: string, i: number) => (
                      <span key={i} className="px-3 py-1.5 bg-stone-100 text-stone-600 text-[11px] font-bold rounded-lg border border-stone-200/50">
                        {sym}
                      </span>
                    )) || <span className="text-xs text-stone-400 italic">No symptoms detected</span>}
                  </div>
                </div>

                {/* Critical Precautions */}
                {session.last_diagnosis?.immediate_precautions?.length > 0 && (
                  <div className="p-6 bg-amber-50 rounded-[32px] border border-amber-100">
                    <div className="flex items-center gap-2 text-amber-700 mb-4">
                      <Stethoscope size={18} />
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-amber-800">Critical Actions</h4>
                    </div>
                    <ul className="space-y-4">
                      {session.last_diagnosis.immediate_precautions.slice(0, 3).map((p: string, i: number) => (
                        <li key={i} className="flex gap-3">
                          <div className="w-5 h-5 bg-amber-200 rounded-full flex items-center justify-center text-[10px] font-bold text-amber-800 flex-shrink-0 mt-0.5">
                            {i+1}
                          </div>
                          <p className="text-[13px] text-amber-900/80 leading-relaxed font-medium">
                            {p}
                          </p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-30 py-20 px-8">
                <div className="w-20 h-20 bg-stone-100 rounded-[32px] flex items-center justify-center mb-6">
                  <AlertCircle size={32} className="text-stone-400" />
                </div>
                <h4 className="text-sm font-black text-stone-900 uppercase mb-2">Awaiting Case</h4>
                <p className="text-xs text-stone-500 font-medium leading-relaxed">
                  Start a clinical diagnosis session to see real-time intelligence mapping and precautions here.
                </p>
              </div>
            )}
          </div>

          {/* Expert Note */}
          <div className="p-8 bg-stone-100/50 border-t border-stone-100">
            <div className="flex items-center gap-2 text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-2">
              <ShieldCheck size={12} /> Certified Evidence
            </div>
            <p className="text-[10px] text-stone-400 leading-relaxed">
              This system uses a **BGE-Reranker** to validate all clinical evidence against verified veterinary manuals.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
