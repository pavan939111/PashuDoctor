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
  X
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
  
  // Sync messages when initialMessages changes (e.g. on case select)
  const lastSyncId = useRef<string>("");
  useEffect(() => {
    // Only sync if we haven't synced this specific set of history messages yet
    // We use the length and the last message content as a simple heuristic
    const syncId = `${initialMessages.length}-${initialMessages[0]?.id || "none"}`;
    if (syncId !== lastSyncId.current) {
      setMessages(initialMessages);
      lastSyncId.current = syncId;
    }
  }, [initialMessages]);

  const [input, setInput] = useState("");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (text: string, imageFile?: File) => {
    if (!text && !imageFile) return;

    // 1. Prepare Request Data
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const currentCaseId = session?.case_id;

    // 2. Add User Message to UI
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

    // 3. Add placeholder AI message
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
      // 4. Initial Turn (Image or first text) vs Follow-up
      if (!currentCaseId) {
        // FIRST TURN: Call /analyze/image or /analyze/text-only
        const formData = new FormData();
        formData.append("user_id", "demo_user");
        formData.append("symptom_text", text || "Image analysis request");
        if (imageFile) {
          formData.append("images", imageFile);
        }

        const endpoint = imageFile ? "/analyze/image" : "/analyze/text-only";
        
        // Note: For text-only we use the same FormData approach for simplicity or switch to JSON
        let response;
        if (imageFile) {
          response = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            body: formData,
          });
        } else {
          response = await fetch(`${API_URL}/analyze/text-only`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_id: "demo_user",
              symptom_text: text,
              animal_type: null,
            }),
          });
        }

        const result = await response.json();
        if (result.success) {
          // Update session with new case_id
          onSessionUpdate({
            case_id: result.case_id,
            user_id: "demo_user",
            animal_type: result.animal_detection?.animal,
            last_diagnosis: result.diagnosis
          });

          // Display initial AI response (non-streaming for first turn analysis)
          const initialReply = result.diagnosis?.formatted_response || result.confidence?.message || "Analysis complete.";
          setMessages(prev => prev.map(m => 
            m.id === aiMsgId ? { ...m, content: initialReply, is_streaming: false } : m
          ));
        } else {
          throw new Error(result.error || "Analysis failed");
        }

      } else {
        // FOLLOW-UP TURN: Call /chat/stream
        const response = await fetch(`${API_URL}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            case_id: currentCaseId,
            user_id: "demo_user",
            message: text,
          }),
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
                setMessages(prev => prev.map(m => 
                  m.id === aiMsgId ? { ...m, content: fullContent } : m
                ));
              } catch (e) {}
            }
          }
        }
        setMessages(prev => prev.map(m => 
          m.id === aiMsgId ? { ...m, is_streaming: false } : m
        ));
      }

    } catch (error: any) {
      console.error("Chat error:", error);
      setMessages(prev => prev.map(m => 
        m.id === aiMsgId ? { ...m, content: `Error: ${error.message || "Something went wrong"}`, is_streaming: false } : m
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPendingFile(file);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-white relative">
      {/* ... (Previous Header and Messages components remain the same) */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-stone-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-bold">P</div>
          <div>
            <h1 className="text-sm font-bold text-stone-800">PashuDoctor AI</h1>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
              <span className="text-[10px] text-stone-500 font-medium uppercase tracking-wider">Expert Copilot</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <SafetyBadge status="active" />
          <button className="flex items-center gap-1.5 text-[12px] font-semibold text-stone-600 bg-stone-100 px-3 py-1.5 rounded-full hover:bg-stone-200 transition-colors">
            English
          </button>
        </div>
      </header>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6"
      >
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto animate-fade-in">
            <div className="w-16 h-16 bg-stone-50 rounded-3xl flex items-center justify-center mb-6 shadow-sm border border-stone-100">
              <Bot className="text-primary" size={32} />
            </div>
            <h2 className="text-2xl font-bold text-stone-900 mb-2">Namaste, Farmer</h2>
            <p className="text-stone-500 text-sm mb-8">
              Describe your animal's symptoms or upload a photo to begin a professional health investigation.
            </p>
            <div className="grid grid-cols-1 gap-3 w-full">
              {[
                "My cow has a fever and isn't eating.",
                "How to prevent Foot and Mouth Disease?",
                "Is milk production drop normal in summer?"
              ].map((text, i) => (
                <button 
                  key={i}
                  onClick={() => handleSendMessage(text)}
                  className="text-left p-4 rounded-2xl border border-stone-200 hover:border-primary/30 hover:bg-stone-50 transition-all text-sm text-stone-700"
                >
                  "{text}"
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div 
            key={msg.id}
            className={cn(
              "flex gap-4 animate-fade-in",
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            )}
          >
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1",
              msg.role === "user" ? "bg-stone-100 text-stone-600" : "bg-primary/10 text-primary"
            )}>
              {msg.role === "user" ? <User size={18} /> : <Bot size={18} />}
            </div>
            
            <div className={msg.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}>
              <div className="prose prose-sm max-w-none prose-stone prose-headings:text-stone-900 prose-p:text-stone-700">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              
              {msg.image_url && (
                <div className="mt-3 rounded-lg overflow-hidden border border-stone-200">
                  <img src={msg.image_url} alt="Attachment" className="max-w-full h-auto" />
                </div>
              )}
              
              {msg.is_streaming && msg.content === "" && (
                <div className="flex items-center h-6">
                  <span className="thinking-dot"></span>
                  <span className="thinking-dot"></span>
                  <span className="thinking-dot"></span>
                </div>
              )}

              {msg.role === "assistant" && !msg.is_streaming && (
                <div className="mt-3 pt-3 border-t border-stone-100 flex items-center justify-between">
                  <button className="text-stone-400 hover:text-primary transition-colors">
                    <Volume2 size={16} />
                  </button>
                  <div className="text-[10px] text-stone-400 font-medium">AI generated</div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="p-6 pt-0">
        <div className="max-w-4xl mx-auto">
          {pendingFile && (
            <div className="mb-3 flex items-center gap-3 p-3 bg-stone-50 rounded-2xl border border-stone-200 animate-in slide-in-from-bottom-2">
              <div className="w-16 h-16 rounded-lg overflow-hidden border border-stone-200 bg-white">
                <img 
                  src={URL.createObjectURL(pendingFile)} 
                  alt="Pending" 
                  className="w-full h-full object-cover" 
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-stone-900 truncate">{pendingFile.name}</p>
                <p className="text-[10px] text-stone-500 uppercase tracking-wider">Ready to analyze</p>
              </div>
              <button 
                onClick={() => setPendingFile(null)}
                className="p-2 text-stone-400 hover:text-red-500 transition-colors"
              >
                <X size={20} />
              </button>
            </div>
          )}
          
          <div className="relative flex items-end gap-2 bg-stone-50 p-2 rounded-2xl border border-stone-200 focus-within:border-primary/50 focus-within:bg-white transition-all shadow-sm">
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept="image/*"
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              className="p-3 text-stone-400 hover:text-stone-600 transition-colors"
            >
              <ImageIcon size={22} />
            </button>
            <textarea 
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(input, pendingFile || undefined);
                  setPendingFile(null);
                }
              }}
              placeholder="Describe symptoms here..."
              className="flex-1 bg-transparent border-none focus:ring-0 py-3 text-sm resize-none"
            />
            <button 
              onClick={() => setIsRecording(!isRecording)}
              className={cn(
                "p-3 rounded-xl transition-all",
                isRecording ? "bg-red-50 text-red-500 animate-pulse" : "text-stone-400 hover:text-stone-600"
              )}
            >
              {isRecording ? <MicOff size={22} /> : <Mic size={22} />}
            </button>
            <button 
              onClick={() => {
                handleSendMessage(input, pendingFile || undefined);
                setPendingFile(null);
              }}
              disabled={(!input.trim() && !pendingFile && !isLoading) || isLoading}
              className="bg-primary text-white p-3 rounded-xl disabled:opacity-50 disabled:bg-stone-300 transition-all hover:bg-accent"
            >
              <Send size={22} />
            </button>
          </div>
          <div className="mt-2 text-center">
            <span className="text-[10px] text-stone-400 font-medium">
              PashuDoctor can make mistakes. Always consult a local vet.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
