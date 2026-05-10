"use client";

import React, { useState } from "react";
import { 
  ShieldCheck, 
  ArrowRight, 
  Stethoscope, 
  Globe, 
  PhoneCall 
} from "lucide-react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [email, setEmail] = useState("demo_user@pashudoctor.ai");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate auth for demo
    setTimeout(() => {
      localStorage.setItem("pashudoctor_token", "demo_token");
      localStorage.setItem("pashudoctor_user", JSON.stringify({ name: "Demo Farmer", region: "Rajasthan" }));
      router.push("/");
    }, 800);
  };

  return (
    <div className="min-h-screen bg-stone-50 flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-emerald-50 rounded-full blur-3xl opacity-60" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-amber-50 rounded-full blur-3xl opacity-60" />

      <div className="max-w-5xl w-full grid md:grid-cols-2 bg-white rounded-[32px] shadow-2xl shadow-emerald-900/5 border border-stone-100 overflow-hidden relative z-10">
        {/* Left Side: Branding & Info */}
        <div className="p-12 bg-emerald-900 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white via-transparent to-transparent pointer-events-none" />
          
          <div>
            <div className="flex items-center gap-3 mb-8">
              <div className="bg-white/10 p-2 rounded-xl backdrop-blur-md">
                <Stethoscope className="text-emerald-400" size={28} />
              </div>
              <span className="text-2xl font-bold tracking-tight">PashuDoctor</span>
            </div>
            
            <h1 className="text-4xl font-bold leading-tight mb-6">
              Professional AI Healthcare <br /> 
              <span className="text-emerald-400">for your Livestock.</span>
            </h1>
            
            <p className="text-emerald-100/80 leading-relaxed mb-8 max-w-md">
              Secure, AI-powered diagnostic support for cattle, buffalo, goats, and sheep. 
              Built to assist farmers across 10+ Indian languages.
            </p>

            <div className="space-y-4">
              {[
                { icon: <ShieldCheck size={18} />, text: "Grounded Medical Knowledge" },
                { icon: <Globe size={18} />, text: "Multi-language Support" },
                { icon: <PhoneCall size={18} />, text: "Direct Helpline Integration" }
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 text-sm text-emerald-100/90">
                  <div className="p-1 bg-white/10 rounded-full">{item.icon}</div>
                  {item.text}
                </div>
              ))}
            </div>
          </div>

          <div className="mt-12 flex items-center gap-4 pt-8 border-t border-white/10">
            <div className="flex -space-x-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="w-8 h-8 rounded-full border-2 border-emerald-900 bg-emerald-800 flex items-center justify-center text-[10px] font-bold">
                  U{i}
                </div>
              ))}
            </div>
            <p className="text-xs text-emerald-200/60">Trusted by 5,000+ Farmers nationwide.</p>
          </div>
        </div>

        {/* Right Side: Login Form */}
        <div className="p-12 flex flex-col justify-center">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-stone-900 mb-2">Welcome Back</h2>
            <p className="text-stone-500 text-sm">Please enter your credentials to continue.</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-xs font-bold text-stone-400 uppercase tracking-wider mb-2">Email Address</label>
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-4 bg-stone-50 border border-stone-200 rounded-2xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none text-stone-800"
                placeholder="farmer@example.com"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-stone-400 uppercase tracking-wider mb-2">Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-4 bg-stone-50 border border-stone-200 rounded-2xl focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all outline-none text-stone-800"
                placeholder="••••••••"
                required
              />
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 cursor-pointer text-stone-500 hover:text-emerald-600 transition-colors">
                <input type="checkbox" className="rounded border-stone-300 text-emerald-600 focus:ring-emerald-500" />
                Remember me
              </label>
              <button type="button" className="text-emerald-600 font-medium hover:underline">Forgot password?</button>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-emerald-900 text-white p-4 rounded-2xl font-bold shadow-xl shadow-emerald-900/10 hover:bg-emerald-800 hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-70"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  Sign In to PashuDoctor
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <p className="text-center mt-8 text-sm text-stone-500">
            Don't have an account? <button className="text-emerald-600 font-bold hover:underline">Register your Farm</button>
          </p>
        </div>
      </div>
    </div>
  );
}
