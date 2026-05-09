"use client"

import { useEffect, useState } from "react"
import { usePashuStore } from "@/store/usePashuStore"
import { api } from "@/lib/api"
import { motion } from "framer-motion"
import { 
  Calendar, CheckCircle, XCircle, 
  ChevronRight, Filter, SortAsc,
  TrendingUp, Activity, Users, PhoneCall
} from "lucide-react"
import { cn } from "@/lib/utils"
import toast from "react-hot-toast"

export default function HistoryPage() {
  const { userId } = usePashuStore()
  const [history, setHistory] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [hData, sData] = await Promise.all([
          api.getHistory(userId),
          api.getStats(userId)
        ])
        setHistory(hData.cases || [])
        setStats(sData)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [userId])

  if (loading) return <div className="p-8 animate-pulse space-y-4 flex-1">Loading History...</div>

  return (
    <div className="flex-1 h-screen overflow-y-auto bg-gray-50 p-8 custom-scrollbar">
      <div className="max-w-5xl mx-auto">
        <header className="mb-10">
          <h1 className="font-display text-4xl text-gray-800 mb-2">History</h1>
          <p className="text-gray-500">Review your past cases and diagnostic performance.</p>
        </header>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <StatCard icon={<Activity className="text-blue-500" />} label="Total Cases" value={stats?.total_cases || 0} />
          <StatCard icon={<TrendingUp className="text-green-500" />} label="Avg Confidence" value={`${Math.round((stats?.avg_confidence || 0) * 100)}%`} />
          <StatCard icon={<Calendar className="text-sage-500" />} label="This Month" value={stats?.cases_this_month || 0} />
          <StatCard icon={<PhoneCall className="text-red-500" />} label="Vet Referrals" value={stats?.vet_referrals || 0} />
        </div>

        {/* Filters */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex gap-4">
             <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-xs font-medium text-gray-600">
               <Filter size={14} /> Animal: All
             </button>
             <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-xs font-medium text-gray-600">
               <SortAsc size={14} /> Newest First
             </button>
          </div>
          <span className="text-xs text-gray-400 font-mono">{history.length} records found</span>
        </div>

        {/* List */}
        <div className="space-y-4">
          {history.length === 0 ? (
            <div className="bg-white p-12 rounded-3xl text-center border border-dashed border-gray-200">
              <p className="text-gray-400">No diagnostic history found yet.</p>
            </div>
          ) : (
            history.map((item, i) => (
              <CaseRow key={item.case_id} item={item} i={i} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value }: any) {
  return (
    <div className="bg-white p-6 rounded-3xl border border-gray-100 shadow-sm">
      <div className="w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center mb-4">
        {icon}
      </div>
      <p className="text-xs text-gray-400 font-medium mb-1 uppercase tracking-wider">{label}</p>
      <h3 className="text-3xl font-display text-gray-800">{value}</h3>
    </div>
  )
}

function CaseRow({ item, i }: any) {
  const [feedback, setFeedback] = useState<boolean | null>(null)

  const handleFeedback = async (correct: boolean) => {
    try {
      await api.submitFeedback({
        case_id: item.case_id,
        feedback_correct: correct
      })
      
      if (correct) {
        await api.storeVector({ case_id: item.case_id })
        toast.success("Thank you! This helps improve future diagnoses.")
      } else {
        toast.success("Feedback saved")
      }
      
      setFeedback(correct)
    } catch (err) {
      toast.error("Failed to save feedback")
    }
  }

  const severityColors: any = {
    "mild": "bg-green-100 text-green-700",
    "moderate": "bg-amber-100 text-amber-700",
    "severe": "bg-orange-100 text-orange-700",
    "emergency": "bg-red-100 text-red-700"
  }

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: i * 0.05 }}
      className="bg-white p-5 rounded-3xl border border-gray-100 flex items-center gap-6 group hover:border-sage-200 transition-colors"
    >
      <div className="w-14 h-14 bg-sage-50 rounded-2xl flex items-center justify-center shrink-0">
         <span className="text-2xl">🐄</span>
      </div>
      
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-1">
          <h4 className="font-display text-xl text-gray-800">{item.primary_diagnosis}</h4>
          <span className={cn("px-2 py-0.5 rounded-full text-[8px] font-bold uppercase", severityColors[item.severity.toLowerCase()] || "bg-gray-100")}>
            {item.severity}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-400 font-medium">
          <span className="capitalize">{item.animal_type}</span>
          <span className="w-1 h-1 bg-gray-200 rounded-full" />
          <span>{new Date(item.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      <div className="text-right px-6 border-r border-gray-100">
        <p className="text-[10px] text-gray-400 font-bold uppercase mb-1">Confidence</p>
        <p className="text-xl font-mono font-bold text-sage-500">{Math.round(item.confidence_score * 100)}%</p>
      </div>

      <div className="flex gap-2">
        <button 
          onClick={() => handleFeedback(true)}
          className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
            feedback === true ? "bg-green-500 text-white" : "bg-gray-50 text-gray-400 hover:bg-green-50 hover:text-green-500"
          )}
        >
          <CheckCircle size={20} />
        </button>
        <button 
          onClick={() => handleFeedback(false)}
          className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
            feedback === false ? "bg-red-500 text-white" : "bg-gray-50 text-gray-400 hover:bg-red-50 hover:text-red-500"
          )}
        >
          <XCircle size={20} />
        </button>
      </div>
      
      <button className="w-10 h-10 rounded-xl bg-sage-50 text-sage-500 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
        <ChevronRight size={20} />
      </button>
    </motion.div>
  )
}
