"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { motion } from "framer-motion"
import { 
  ShieldAlert, Cpu, Heart, CheckCircle2, 
  HelpCircle, Mic, AlertCircle, Info
} from "lucide-react"

export default function AboutPage() {
  const [health, setHealth] = useState<any>(null)
  const [diseases, setDiseases] = useState<any[]>([])

  useEffect(() => {
    async function load() {
      try {
        const [h, d] = await Promise.all([api.getHealth(), api.getDiseases()])
        setHealth(h)
        setDiseases(d.diseases || [])
      } catch (err) {}
    }
    load()
  }, [])

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-gray-50 p-8 custom-scrollbar">
      <div className="max-w-4xl mx-auto pb-20">
        <header className="mb-12">
          <h1 className="font-display text-4xl text-gray-800 mb-2">About PashuDoctor</h1>
          <p className="text-gray-500 font-medium">Empowering Indian farmers with state-of-the-art AI veterinary diagnostics.</p>
        </header>

        {/* Safety Disclaimer */}
        <div className="bg-amber-50 border border-amber-100 p-6 rounded-3xl mb-12 flex gap-4">
           <ShieldAlert className="text-amber-500 shrink-0" size={24} />
           <div>
             <h4 className="font-bold text-amber-800 text-sm mb-1">SAFETY DISCLAIMER</h4>
             <p className="text-xs text-amber-700 leading-relaxed">
               PashuDoctor is an AI-powered assistant designed for informational support only. It is NOT a substitute for professional veterinary medical advice, diagnosis, or treatment. Always seek the advice of a qualified veterinarian with any questions regarding animal health. In emergencies, call 1962 immediately.
             </p>
           </div>
        </div>

        {/* How it works */}
        <section className="mb-16">
          <h2 className="font-display text-2xl text-gray-800 mb-6">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <FeatureCard 
              icon={<Cpu className="text-sage-500" />} 
              title="Multimodal RAG" 
              desc="Combines image recognition with a deep knowledge base of symptoms and medical manuals." 
            />
            <FeatureCard 
              icon={<Heart className="text-red-400" />} 
              title="Farmer-First" 
              desc="Supports 10 Indian languages and voice input for accessibility in remote rural areas." 
            />
            <FeatureCard 
              icon={<CheckCircle2 className="text-blue-500" />} 
              title="Verified by Vets" 
              desc="Our database is curated from ICAR and NDDB manuals to ensure diagnostic reliability." 
            />
            <FeatureCard 
              icon={<HelpCircle className="text-earth-400" />} 
              title="Offline Capability" 
              desc="Caches common diagnoses to provide support even when internet connectivity is poor." 
            />
          </div>
        </section>

        {/* System Health */}
        <section className="mb-16">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-display text-2xl text-gray-800">System Health</h2>
            {health && (
               <span className="px-3 py-1 bg-green-100 text-green-600 rounded-full text-[10px] font-bold uppercase tracking-widest animate-pulse">
                 {health.status}
               </span>
            )}
          </div>
          
          <div className="bg-white border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-6 py-4 font-bold text-gray-400 uppercase text-[10px] tracking-widest">Service</th>
                  <th className="px-6 py-4 font-bold text-gray-400 uppercase text-[10px] tracking-widest">Status</th>
                  <th className="px-6 py-4 font-bold text-gray-400 uppercase text-[10px] tracking-widest">Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {health?.services && Object.entries(health.services).map(([name, status]: any) => (
                  <tr key={name}>
                    <td className="px-6 py-4 font-medium text-gray-700 capitalize">{name.replace("_", " ")}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                         <div className={cn("w-2 h-2 rounded-full", status ? "bg-green-500" : "bg-red-500")} />
                         <span className="text-xs font-mono">{status ? "Operational" : "Offline"}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-400 font-mono">
                      {name === "chromadb" ? `${health.collections?.disease_images} records` : "Ready"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Supported Diseases */}
        <section>
          <h2 className="font-display text-2xl text-gray-800 mb-6">Expertise</h2>
          <div className="flex flex-wrap gap-2">
            {diseases.map((d: any) => (
               <div key={d.name} className="px-4 py-2 bg-white border border-gray-100 rounded-xl text-xs text-gray-600 font-medium hover:border-sage-200 transition-colors shadow-sm">
                 {d.display_name}
               </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, desc }: any) {
  return (
    <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
      <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="font-display text-lg text-gray-800 mb-2">{title}</h3>
      <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
    </div>
  )
}
