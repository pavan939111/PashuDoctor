"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, Lock, User, AlertCircle, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Store auth data
        localStorage.setItem("pashudoctor_token", data.token);
        localStorage.setItem("pashudoctor_user", JSON.stringify({
          id: data.user_id,
          username: data.username
        }));
        
        // Redirect to home
        router.push("/");
      } else {
        setError(data.detail || "Invalid credentials. Please try again.");
      }
    } catch (err) {
      setError("Unable to connect to the server. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md animate-fade-in">
        {/* Logo Section */}
        <div className="text-center mb-10">
          <div className="w-20 h-20 bg-primary rounded-[2.5rem] flex items-center justify-center mx-auto mb-6 shadow-xl shadow-primary/20 rotate-3">
            <Bot className="text-white" size={40} />
          </div>
          <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight">PashuDoctor AI</h1>
          <p className="text-stone-500 mt-2 font-medium italic">Expert Livestock Healthcare Assistant</p>
        </div>

        {/* Login Form Card */}
        <div className="bg-white p-8 rounded-[2rem] shadow-xl border border-stone-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1.5 bg-primary"></div>
          
          <h2 className="text-xl font-bold text-stone-800 mb-8">Farmer Login</h2>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-stone-500 uppercase tracking-widest ml-1">Username</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-stone-400 group-focus-within:text-primary transition-colors">
                  <User size={18} />
                </div>
                <input 
                  type="text" 
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username (farmer123)"
                  className="w-full pl-11 pr-4 py-4 bg-stone-50 border border-stone-200 rounded-2xl focus:ring-4 focus:ring-primary/10 focus:border-primary transition-all outline-none text-stone-800 placeholder:text-stone-400"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-stone-500 uppercase tracking-widest ml-1">Password</label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-stone-400 group-focus-within:text-primary transition-colors">
                  <Lock size={18} />
                </div>
                <input 
                  type="password" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password (pashu2024)"
                  className="w-full pl-11 pr-4 py-4 bg-stone-50 border border-stone-200 rounded-2xl focus:ring-4 focus:ring-primary/10 focus:border-primary transition-all outline-none text-stone-800 placeholder:text-stone-400"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-600 animate-fade-in">
                <AlertCircle size={20} className="shrink-0" />
                <p className="text-sm font-medium">{error}</p>
              </div>
            )}

            <button 
              type="submit"
              disabled={isLoading}
              className={cn(
                "w-full bg-primary text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-primary/20 flex items-center justify-center gap-3 transition-all hover:bg-accent hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:translate-y-0",
                isLoading && "animate-pulse"
              )}
            >
              {isLoading ? "Validating..." : "Start Investigation"}
              {!isLoading && <ArrowRight size={20} />}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-stone-100 text-center">
            <p className="text-sm text-stone-400">
              New user? <span className="text-primary font-bold hover:underline cursor-pointer">Register Account</span>
            </p>
          </div>
        </div>

        {/* Support Section */}
        <div className="mt-8 text-center text-stone-400 text-xs font-medium space-x-4">
          <span className="hover:text-stone-600 cursor-pointer transition-colors">Privacy Policy</span>
          <span>•</span>
          <span className="hover:text-stone-600 cursor-pointer transition-colors">Emergency Support</span>
          <span>•</span>
          <span className="hover:text-stone-600 cursor-pointer transition-colors">Help Center</span>
        </div>
      </div>
    </div>
  );
}
