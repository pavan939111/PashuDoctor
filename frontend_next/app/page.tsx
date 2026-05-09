"use client";

import React, { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import ChatInterface from "@/components/ChatInterface";
import { Session, Message } from "@/types";
import { useRouter } from "next/navigation";
import { Menu, AlertCircle, LogOut } from "lucide-react";

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  // Authentication Check
  useEffect(() => {
    const token = localStorage.getItem("pashudoctor_token");
    const storedUser = localStorage.getItem("pashudoctor_user");
    
    if (!token || !storedUser) {
      router.push("/login");
    } else {
      setUser(JSON.parse(storedUser));
    }
  }, [router]);

  if (!user) return null; // Prevents flashing content while checking auth

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

        // Convert chat_history to Message objects
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
    <main className="flex w-full h-full bg-white overflow-hidden">
      {/* Sidebar Overlay for Mobile */}
      <Sidebar 
        isOpen={isSidebarOpen} 
        setIsOpen={setIsSidebarOpen}
        onNewChat={handleNewChat}
        onSelectCase={handleSelectCase}
      />
      
      {/* Mobile Sidebar Toggle */}
      {!isSidebarOpen && (
        <button 
          onClick={() => setIsSidebarOpen(true)}
          className="absolute top-4 left-4 z-50 p-2 bg-white border border-stone-200 rounded-lg shadow-sm lg:hidden"
        >
          <Menu size={20} />
        </button>
      )}

      <ChatInterface 
        session={session}
        onSessionUpdate={setSession}
        initialMessages={initialMessages}
      />

      {/* Optional Right Panel for Analysis / Reports (ChatGPT Style) */}
      <div className="hidden xl:flex w-80 h-full border-l border-stone-200 bg-stone-50 flex-col p-6 overflow-y-auto">
        <h3 className="text-xs font-bold text-stone-400 uppercase tracking-widest mb-6">Diagnostic Insights</h3>
        
        {session?.last_diagnosis ? (
          <div className="space-y-6">
            <div className="premium-card p-4">
              <div className="text-[10px] font-bold text-primary uppercase mb-1">Primary Diagnosis</div>
              <div className="text-lg font-bold text-stone-900 leading-tight">
                {session.last_diagnosis?.primary_diagnosis || "Analyzing..."}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-stone-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all duration-1000" 
                    style={{ width: `${(session.last_diagnosis?.confidence_score || 0) * 100}%` }}
                  ></div>
                </div>
                <span className="text-xs font-bold text-stone-500">
                  {Math.round((session.last_diagnosis?.confidence_score || 0) * 100)}%
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-[11px] font-bold text-stone-500 uppercase mb-2">Key Symptoms Identified</h4>
                <div className="space-y-2">
                  {session.last_diagnosis?.matching_symptoms?.slice(0, 5).map((sym: string, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-stone-700">
                      <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                      {sym}
                    </div>
                  )) || <div className="text-xs text-stone-400 italic">No symptoms mapped yet</div>}
                </div>
              </div>

              {session.last_diagnosis?.immediate_precautions?.length > 0 && (
                <div className="p-4 bg-orange-50 rounded-xl border border-orange-100">
                  <h4 className="text-[11px] font-bold text-orange-700 uppercase mb-2">Immediate Precautions</h4>
                  <ul className="text-xs text-orange-800 leading-relaxed list-disc pl-4 space-y-1">
                    {session.last_diagnosis.immediate_precautions.slice(0, 3).map((p: string, i: number) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center opacity-50">
            <div className="w-12 h-12 bg-stone-100 rounded-full flex items-center justify-center mb-4">
              <AlertCircle size={24} className="text-stone-400" />
            </div>
            <p className="text-sm text-stone-500">
              Start a diagnosis to see real-time insights and precautions here.
            </p>
          </div>
        )}
      </div>
    </main>
  );
}
