"use client"

import { usePashuStore } from "@/store/usePashuStore"
import { motion, AnimatePresence } from "framer-motion"
import { 
  BarChart3, ShieldCheck, AlertTriangle, 
  MapPin, Download, Share2, ClipboardList,
  Search, Info, History
} from "lucide-react"
import { cn } from "@/lib/utils"

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
}

export default function AnalysisPanel() {
  const { analysis, isLoading } = usePashuStore()

  return (
    <aside className="w-[380px] h-screen bg-white border-l border-gray-100 flex flex-col shrink-0">
      <div className="h-14 border-b border-gray-100 flex items-center px-6 bg-white shrink-0">
        <h2 className="font-display text-lg text-gray-800">Analysis</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {!analysis && !isLoading && <EmptyState />}
        {isLoading && <LoadingState />}
        
        {analysis && (
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-4"
          >
            <AnimalDetectionCard data={analysis.animalDetection} />
            
            {analysis.diagnosis && (
              <>
                <DiagnosisCard diagnosis={analysis.diagnosis} />
                <ConfidenceCard confidence={analysis.confidence} />
                <XAICard confidence={analysis.confidence} candidates={analysis.topCandidates} />
                <SimilarCasesCard count={analysis.diagnosis.similar_cases_count} type={analysis.diagnosis.similar_cases_type} candidates={analysis.topCandidates} />
                <PrecautionsCard steps={analysis.diagnosis.immediate_precautions} />
                {analysis.diagnosis.herd_alert && <HerdAlertCard alert={analysis.diagnosis.herd_alert} />}
                <VetLocatorCard urgency={analysis.diagnosis.vet_urgency} />
                <MetadataCard analysis={analysis} />
                <ExportActions />
              </>
            )}
          </motion.div>
        )}
      </div>
    </aside>
  )
}

function EmptyState() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8">
      <div className="w-16 h-16 bg-sage-50 rounded-full flex items-center justify-center mb-4">
        <Search size={28} className="text-sage-300" />
      </div>
      <h3 className="font-display text-xl text-gray-700 mb-2">Ready to Analyze</h3>
      <p className="text-sm text-gray-400">
        Upload a photo or describe symptoms to see AI-driven medical analysis here.
      </p>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="bg-gray-50 h-32 rounded-3xl border border-gray-100" />
      ))}
    </div>
  )
}

function AnalysisCard({ children, title, icon: Icon, className }: any) {
  return (
    <motion.div 
      variants={itemVariants}
      className={cn("bg-white border border-gray-100 rounded-3xl p-5 shadow-sm hover:shadow-md transition-all", className)}
    >
      <div className="flex items-center gap-2 mb-4 opacity-40">
        <Icon size={12} />
        <span className="text-[10px] font-mono uppercase tracking-widest">{title}</span>
      </div>
      {children}
    </motion.div>
  )
}

function AnimalDetectionCard({ data }: any) {
  return (
    <AnalysisCard title="Detected Animal" icon={Search}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🐄</span>
          <div>
            <h4 className="font-display text-2xl text-gray-800 capitalize">{data.animal}</h4>
            <p className="text-xs text-gray-400">{data.method} identification</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-lg font-mono font-bold text-sage-500">{Math.round(data.confidence * 100)}%</span>
        </div>
      </div>
    </AnalysisCard>
  )
}

function DiagnosisCard({ diagnosis }: any) {
  const severityColors: any = {
    "mild": "bg-green-100 text-green-700",
    "moderate": "bg-amber-100 text-amber-700",
    "severe": "bg-orange-100 text-orange-700",
    "emergency": "bg-red-100 text-red-700"
  }

  return (
    <AnalysisCard title="Diagnosis" icon={ClipboardList}>
      <div className="mb-4">
        <div className="flex items-start justify-between gap-4 mb-1">
          <h4 className="font-display text-2xl text-sage-600">{diagnosis.primaryDiagnosis}</h4>
          <span className={cn("px-3 py-1 rounded-full text-[10px] font-bold uppercase", severityColors[diagnosis.severity.toLowerCase()] || "bg-gray-100")}>
            {diagnosis.severity}
          </span>
        </div>
        <p className="text-sm text-gray-500 italic">Differential: {diagnosis.alternativeDiagnoses?.join(", ")}</p>
      </div>
      
      <div className="space-y-2">
        <h5 className="text-[10px] font-bold text-gray-400 uppercase tracking-tight">Matching Symptoms</h5>
        <div className="flex flex-wrap gap-1">
          {diagnosis.matchingSymptoms?.map((s: string) => (
            <span key={s} className="px-2 py-1 bg-sage-50 text-sage-600 rounded-lg text-[10px] border border-sage-100">
              {s}
            </span>
          ))}
        </div>
      </div>
    </AnalysisCard>
  )
}

function ConfidenceCard({ confidence }: any) {
  return (
    <AnalysisCard title="Confidence" icon={ShieldCheck}>
      <div className="mb-4">
        <div className="flex justify-between items-end mb-2">
          <h4 className="text-sm font-medium text-gray-700 capitalize">{confidence.action}</h4>
          <span className="text-2xl font-mono font-bold text-sage-500">{confidence.percentage}%</span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${confidence.percentage}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="h-full bg-sage-500 rounded-full" 
          />
        </div>
      </div>
      <p className="text-xs text-gray-400 leading-relaxed">{confidence.message}</p>
    </AnalysisCard>
  )
}

function XAICard({ confidence, candidates }: any) {
  const factors = [
    { label: "Image Similarity", val: confidence.imageSim || 0 },
    { label: "Symptom Match", val: confidence.symptomMatch || 0 },
    { label: "Knowledge Match", val: confidence.textSim || 0 }
  ]

  return (
    <AnalysisCard title="Why this diagnosis?" icon={BarChart3}>
      <div className="space-y-4">
        {factors.map(f => (
          <div key={f.label}>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-gray-500">{f.label}</span>
              <span className="font-mono text-sage-500">{Math.round(f.val * 100)}%</span>
            </div>
            <div className="w-full h-1 bg-gray-50 rounded-full overflow-hidden">
              <motion.div 
                initial={{ width: 0 }}
                animate={{ width: `${f.val * 100}%` }}
                className="h-full bg-sage-400/50 rounded-full" 
              />
            </div>
          </div>
        ))}
      </div>
    </AnalysisCard>
  )
}

function SimilarCasesCard({ count, type, candidates }: any) {
  return (
    <AnalysisCard title="Evidence" icon={History}>
       <p className="text-xs text-gray-500 mb-3">Found {count} similar historical records for {type}.</p>
       <div className="space-y-2">
         {candidates?.slice(0, 3).map((c: any, i: number) => (
           <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded-xl border border-gray-100">
             <div className="flex items-center gap-2">
               <div className="w-6 h-6 rounded-lg bg-white flex items-center justify-center text-[10px]">🐄</div>
               <span className="text-[10px] font-medium text-gray-700">{c.disease}</span>
             </div>
             <span className="text-[10px] font-mono text-sage-400">{(c.finalScore * 100).toFixed(0)}%</span>
           </div>
         ))}
       </div>
    </AnalysisCard>
  )
}

function PrecautionsCard({ steps }: any) {
  return (
    <AnalysisCard title="Immediate Steps" icon={ClipboardList}>
      <ul className="space-y-3">
        {steps?.map((s: string, i: number) => (
          <li key={i} className="flex gap-3">
            <span className="flex-shrink-0 w-5 h-5 bg-sage-50 text-sage-600 rounded-full flex items-center justify-center text-[10px] font-mono font-bold border border-sage-100">
              {i + 1}
            </span>
            <span className="text-xs text-gray-600 leading-snug">{s}</span>
          </li>
        ))}
      </ul>
    </AnalysisCard>
  )
}

function HerdAlertCard({ alert }: any) {
  return (
    <AnalysisCard title="Herd Alert" icon={AlertTriangle} className="bg-red-50 border-red-100 ring-2 ring-red-50 ring-offset-2">
      <div className="flex items-center gap-3 text-red-600 mb-3">
        <AlertTriangle size={20} className="animate-pulse" />
        <h4 className="font-bold text-sm">CONTAGIOUS CONDITION</h4>
      </div>
      <p className="text-xs text-red-700 leading-relaxed font-medium">
        {alert.prevention_advice || "Isolate this animal from the rest of the herd immediately to prevent spread."}
      </p>
    </AnalysisCard>
  )
}

function VetLocatorCard({ urgency }: any) {
  return (
    <AnalysisCard title="Veterinary Care" icon={MapPin} className="bg-blue-50 border-blue-100">
       <div className="flex justify-between items-start mb-4">
         <div>
           <h4 className="font-display text-2xl text-blue-700">1962</h4>
           <p className="text-[10px] font-bold text-blue-500 uppercase">National Helpline</p>
         </div>
         <span className="px-2 py-1 bg-blue-100 text-blue-600 rounded-lg text-[10px] font-bold uppercase">
           {urgency}
         </span>
       </div>
       <button className="w-full bg-white border border-blue-200 text-blue-600 py-2 rounded-xl text-xs font-bold hover:bg-blue-100 transition-colors flex items-center justify-center gap-2">
         <MapPin size={14} />
         Find Nearest Clinic
       </button>
    </AnalysisCard>
  )
}

function MetadataCard({ analysis }: any) {
  return (
    <div className="p-4 flex flex-col gap-2 opacity-30">
      <div className="flex justify-between text-[8px] font-mono uppercase tracking-widest">
        <span>Model</span>
        <span>{analysis.modelUsed}</span>
      </div>
      <div className="flex justify-between text-[8px] font-mono uppercase tracking-widest">
        <span>Processing</span>
        <span>{Math.round(analysis.retrievalTimeMs + analysis.llmTimeMs)}ms</span>
      </div>
      <div className="flex justify-between text-[8px] font-mono uppercase tracking-widest">
        <span>Ref ID</span>
        <span>{analysis.caseId.slice(0, 8)}...</span>
      </div>
    </div>
  )
}

function ExportActions() {
  const { analysis } = usePashuStore()
  
  if (!analysis || !analysis.diagnosis) return null

  const formatWhatsApp = () => {
    const d = analysis.diagnosis
    const toTitleCase = (str: string) => str.replace(/\w\S*/g, (txt) => txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase());

    return [
      "🐄 *PashuDoctor AI Report*",
      "",
      `*Animal:* ${analysis.animalDetection.animal}`,
      `*Diagnosis:* ${toTitleCase(d.primaryDiagnosis.replace(/_/g, " "))}`,
      `*Confidence:* ${analysis.confidence.percentage}%`,
      `*Severity:* ${d.severity}`,
      `*Vet Urgency:* ${toTitleCase(d.vetUrgency.replace(/_/g, " "))}`,
      "",
      "*Immediate Steps:*",
      ...(d.immediate_precautions || []).slice(0, 3).map((p: string) => `• ${p}`),
      "",
      "📞 *National Vet Helpline: 1962* (Free, 24/7)",
      "",
      "_Generated by PashuDoctor AI_",
      "_Not a substitute for veterinary advice_"
    ].join("\n")
  }

  const waUrl = `https://wa.me/?text=${encodeURIComponent(formatWhatsApp())}`

  const downloadPDF = async () => {
    try {
      const res = await api.generateReport(analysis.caseId)
      if (!res.ok) throw new Error("Failed to generate report")
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `pashudoctor_${analysis.caseId.slice(0, 8)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      toast.success("Report downloaded")
    } catch (err) {
      toast.error("Failed to download report")
    }
  }

  return (
    <div className="flex gap-3 pb-8">
      <button 
        onClick={downloadPDF}
        className="flex-1 bg-gray-900 text-white py-3 rounded-2xl text-xs font-bold flex items-center justify-center gap-2 hover:bg-gray-800 transition-colors"
      >
        <Download size={14} />
        PDF
      </button>
      <a 
        href={waUrl} 
        target="_blank" 
        rel="noopener noreferrer"
        className="flex-1 bg-white border border-gray-200 text-gray-700 py-3 rounded-2xl text-xs font-bold flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors"
      >
        <Share2 size={14} />
        WhatsApp
      </a>
    </div>
  )
}
