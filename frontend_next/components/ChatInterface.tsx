"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Send, 
  Image as ImageIcon, 
  Mic, 
  MicOff,
  User,
  Bot,
  Volume2,
  AlertCircle,
  X,
  ClipboardCheck,
  Zap,
  Info
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { Message, Session } from "@/types";
import SafetyBadge from "./SafetyBadge";

interface ChatInterfaceProps {
  session: Session | null;
  onSessionUpdate: (session: Session) => void;
  initialMessages?: Message[];
}

export default function ChatInterface({ session, onSessionUpdate, initialMessages = [] }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  useEffect(() => {
    const syncId = `${initialMessages.length}-${initialMessages[0]?.id || "none"}`;
    setMessages(initialMessages);
  }, [initialMessages]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (text: string, imageFile?: File) => {
    if (!text && !imageFile) return;

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const currentCaseId = session?.case_id;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text || "Uploaded an image for analysis",
      timestamp: new Date(),
      image_url: imageFile ? URL.createObjectURL(imageFile) : undefined
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    const aiMsgId = (Date.now() + 1).toString();
    const aiMsg: Message = {
      id: aiMsgId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      is_streaming: true,
    };
    setMessages(prev => [...prev, aiMsg]);

    try {
      if (!currentCaseId) {
        const formData = new FormData();
        formData.append("user_id", "demo_user");
        formData.append("symptom_text", text || "Image analysis request");
        if (imageFile) formData.append("images", imageFile);

        const endpoint = imageFile ? "/analyze/image" : "/analyze/text-only";
        const response = await fetch(`${API_URL}${endpoint}`, {
          method: "POST",
          body: imageFile ? formData : JSON.stringify({ user_id: "demo_user", symptom_text: text, animal_type: null }),
          headers: imageFile ? {} : { "Content-Type": "application/json" }
        });

        const result = await response.json();
        if (result.success) {
          onSessionUpdate({
            case_id: result.case_id,
            user_id: "demo_user",
            animal_type: result.animal_detection?.animal,
            last_diagnosis: result.diagnosis
          });

          const initialReply = result.diagnosis?.formatted_response || result.confidence?.message || "Analysis complete.";
          setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: initialReply, is_streaming: false } : m));
        }
      } else {
        const response = await fetch(`${API_URL}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ case_id: currentCaseId, user_id: "demo_user", message: text }),
        });

        if (!response.body) throw new Error("No response body");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") break;
              try {
                const parsed = JSON.parse(data);
                fullContent += parsed.text;
                setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: fullContent } : m));
              } catch (e) {}
            }
          }
        }
        setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, is_streaming: false } : m));
      }
    } catch (error: any) {
      setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: `Error: ${error.message}`, is_streaming: false } : m));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-white h-full">
      {/* Scrollable Chat Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-2xl mx-auto py-20">
            <div className="w-20 h-20 bg-emerald-50 rounded-[32px] flex items-center justify-center mb-8 border border-emerald-100 shadow-sm">
              <Bot className="text-emerald-600" size={40} />
            </div>
            <h2 className="text-3xl font-bold text-stone-900 mb-3 tracking-tight">Namaste, Farmer</h2>
            <p className="text-stone-500 text-base mb-10 max-w-sm mx-auto leading-relaxed">
              Upload a photo or describe symptoms to start a clinical-grade investigation.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
              {[
                { title: "Symptom Diagnosis", desc: "My cow has a fever and foot blisters", icon: <AlertCircle size={18} /> },
                { title: "Disease Prevention", desc: "How to prevent Lumpy Skin Disease?", icon: <ShieldAlert size={18} /> },
                { title: "Milk Production", desc: "Is production drop normal in summer?", icon: <Zap size={18} /> },
                { title: "General Inquiry", desc: "Show common diseases in Sheep", icon: <Info size={18} /> }
              ].map((item, i) => (
                <button 
                  key={i}
                  onClick={() => handleSendMessage(item.desc)}
                  className="group text-left p-5 rounded-3xl border border-stone-100 bg-stone-50 hover:border-emerald-200 hover:bg-emerald-50/30 transition-all shadow-sm active:scale-95"
                >
                  <div className="flex items-center gap-2 mb-2 text-emerald-700 font-bold text-xs uppercase tracking-wider">
                    {item.icon}
                    {item.title}
                  </div>
                  <p className="text-sm text-stone-600 group-hover:text-stone-900 transition-colors leading-snug">"{item.desc}"</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div 
            key={msg.id}
            className={cn(
              "flex gap-4 max-w-4xl mx-auto group",
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            )}
          >
            <div className={cn(
              "w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 mt-1 shadow-sm border",
              msg.role === "user" ? "bg-white border-stone-200 text-stone-400" : "bg-emerald-900 border-emerald-800 text-white"
            )}>
              {msg.role === "user" ? <User size={20} /> : <Bot size={20} />}
            </div>
            
            <div className={cn(
              "max-w-[85%] space-y-2",
              msg.role === "user" ? "items-end" : "items-start"
            )}>
              <div className={cn(
                "p-5 md:p-6 rounded-[28px] shadow-sm",
                msg.role === "user" 
                  ? "bg-emerald-900 text-white rounded-tr-none" 
                  : "bg-white border border-stone-100 text-stone-800 rounded-tl-none ring-1 ring-stone-950/5"
              )}>
                <div className={cn(
                  "prose prose-sm max-w-none",
                  msg.role === "user" ? "prose-invert" : "prose-stone prose-headings:text-emerald-900"
                )}>
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
                
                {msg.image_url && (
                  <div className="mt-4 rounded-2xl overflow-hidden border border-white/10 shadow-lg">
                    <img src={msg.image_url} alt="Diagnostic Reference" className="w-full h-auto object-cover max-h-[300px]" />
                  </div>
                )}
                
                {msg.is_streaming && msg.content === "" && (
                  <div className="flex items-center gap-1.5 py-2">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></div>
                  </div>
                )}
              </div>

              {msg.role === "assistant" && !msg.is_streaming && (
                <div className="flex items-center gap-4 px-4">
                  <button className="flex items-center gap-1.5 text-[10px] font-bold text-stone-400 uppercase tracking-widest hover:text-emerald-600 transition-colors">
                    <Volume2 size={14} /> Listen
                  </button>
                  <div className="h-3 w-[1px] bg-stone-200" />
                  <button className="flex items-center gap-1.5 text-[10px] font-bold text-stone-400 uppercase tracking-widest hover:text-emerald-600 transition-colors">
                    <ClipboardCheck size={14} /> Copy Report
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-6 md:p-8 bg-gradient-to-t from-white via-white to-transparent">
        <div className="max-w-4xl mx-auto">
          {pendingFile && (
            <div className="mb-4 flex items-center gap-4 p-4 bg-emerald-50 rounded-[24px] border border-emerald-100 animate-in slide-in-from-bottom-4">
              <div className="w-20 h-20 rounded-2xl overflow-hidden border-2 border-white shadow-md">
                <img src={URL.createObjectURL(pendingFile)} alt="Preview" className="w-full h-full object-cover" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-black text-emerald-900 uppercase tracking-widest">Image Attached</p>
                <p className="text-sm text-emerald-700/70 truncate">{pendingFile.name}</p>
              </div>
              <button onClick={() => setPendingFile(null)} className="p-3 bg-white text-stone-400 hover:text-rose-500 rounded-2xl shadow-sm transition-all">
                <X size={20} />
              </button>
            </div>
          )}
          
          <div className="relative flex items-end gap-2 bg-white p-3 rounded-[32px] border border-stone-200 shadow-xl shadow-stone-200/40 focus-within:ring-4 focus-within:ring-emerald-500/5 focus-within:border-emerald-500/30 transition-all">
            <input type="file" ref={fileInputRef} onChange={(e) => setPendingFile(e.target.files?.[0] || null)} className="hidden" accept="image/*" />
            
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="p-4 text-stone-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-2xl transition-all"
            >
              <ImageIcon size={24} />
            </button>

            <textarea 
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendMessage(input, pendingFile || undefined); setPendingFile(null); } }}
              placeholder="Describe what you see on your animal..."
              className="flex-1 bg-transparent border-none focus:ring-0 py-4 text-base font-medium placeholder:text-stone-400 resize-none max-h-32"
            />

            <div className="flex items-center gap-2 pr-2 pb-1">
              <button 
                onClick={() => setIsRecording(!isRecording)}
                className={cn("p-4 rounded-2xl transition-all", isRecording ? "bg-rose-500 text-white animate-pulse" : "text-stone-400 hover:text-stone-600 hover:bg-stone-100")}
              >
                {isRecording ? <MicOff size={24} /> : <Mic size={24} />}
              </button>
              
              <button 
                onClick={() => { handleSendMessage(input, pendingFile || undefined); setPendingFile(null); }}
                disabled={(!input.trim() && !pendingFile) || isLoading}
                className="bg-emerald-900 text-white p-4 rounded-2xl disabled:opacity-30 disabled:grayscale transition-all hover:bg-emerald-800 shadow-lg shadow-emerald-900/20 active:scale-95"
              >
                <Send size={24} />
              </button>
            </div>
          </div>
          <p className="mt-4 text-center text-[10px] text-stone-400 font-bold uppercase tracking-[0.2em]">
            PashuDoctor AI — High Precision Livestock Diagnostic Copilot
          </p>
        </div>
      </div>
    </div>
  );
}

interface ShieldAlert props {}
function ShieldAlert({ size }: { size: number }) {
  return <Zap size={size} />;
}
