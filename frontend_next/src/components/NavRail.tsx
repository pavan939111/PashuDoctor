"use client"

import { usePashuStore } from "@/store/usePashuStore"
import { MessageSquare, History, Info, Volume2, VolumeX, MapPin } from "lucide-react"
import { cn } from "@/lib/utils"

const STATES = [
  "Uttar Pradesh", "Madhya Pradesh", "Rajasthan", "Gujarat", 
  "Maharashtra", "Karnataka", "Tamil Nadu", "Andhra Pradesh",
  "West Bengal", "Punjab", "Haryana", "Bihar"
]

export default function NavRail() {
  const { page, setPage, autoSpeak, setAutoSpeak, selectedState } = usePashuStore()

  return (
    <nav className="w-16 h-full bg-white border-r border-gray-200 flex flex-col items-center py-4 z-50">
      {/* Logo */}
      <div className="w-10 h-10 bg-sage-500 rounded-xl flex items-center justify-center text-white mb-8 shadow-sm">
        <span className="text-xl">🐄</span>
      </div>

      {/* Main Nav */}
      <div className="flex flex-col gap-4 flex-1">
        <NavButton 
          icon={<MessageSquare size={22} />} 
          active={page === "chat"} 
          onClick={() => setPage("chat")}
          label="Chat"
        />
        <NavButton 
          icon={<History size={22} />} 
          active={page === "history"} 
          onClick={() => setPage("history")}
          label="History"
        />
        <NavButton 
          icon={<Info size={22} />} 
          active={page === "about"} 
          onClick={() => setPage("about")}
          label="About"
        />
        
        <div className="h-px w-8 bg-gray-100 mx-auto my-2" />
        
        {/* State Selector Placeholder - could be a vertical label or icon */}
        <div className="flex flex-col items-center gap-1 opacity-60">
           <MapPin size={18} className="text-earth-500" />
           <span className="text-[10px] font-mono [writing-mode:vertical-lr] rotate-180 uppercase tracking-tighter">
             {selectedState}
           </span>
        </div>
      </div>

      {/* Footer Nav */}
      <div className="flex flex-col gap-4 mt-auto">
        <NavButton 
          icon={autoSpeak ? <Volume2 size={22} /> : <VolumeX size={22} />} 
          active={autoSpeak}
          onClick={() => setAutoSpeak(!autoSpeak)}
          label={autoSpeak ? "Mute" : "Speak"}
        />
      </div>
    </nav>
  )
}

function NavButton({ 
  icon, 
  active, 
  onClick,
  label
}: { 
  icon: React.ReactNode, 
  active: boolean, 
  onClick: () => void,
  label: string
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={cn(
        "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200",
        active 
          ? "bg-sage-50 text-sage-500 shadow-sm" 
          : "text-gray-400 hover:bg-sage-50/50 hover:text-sage-400"
      )}
    >
      {icon}
    </button>
  )
}
