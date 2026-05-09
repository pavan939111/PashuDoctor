"use client"

import { useEffect } from "react"
import { usePashuStore } from "@/store/usePashuStore"
import NavRail from "@/components/NavRail"
import ChatPanel from "@/components/ChatPanel"
import AnalysisPanel from "@/components/AnalysisPanel"
import HistoryPage from "@/components/HistoryPage"
import AboutPage from "@/components/AboutPage"

export default function PashuDoctorApp() {
  const { page, isOnline, setOnline } = usePashuStore()

  useEffect(() => {
    const handleOnline = () => setOnline(true)
    const handleOffline = () => setOnline(false)

    window.addEventListener("online", handleOnline)
    window.addEventListener("offline", handleOffline)

    return () => {
      window.removeEventListener("online", handleOnline)
      window.removeEventListener("offline", handleOffline)
    }
  }, [setOnline])

  return (
    <main className="flex h-screen w-full overflow-hidden bg-cream-50">
      <NavRail />
      
      <div className="flex flex-1 overflow-hidden relative">
        {page === "chat" && (
          <>
            <ChatPanel />
            <AnalysisPanel />
          </>
        )}
        
        {page === "history" && <HistoryPage />}
        
        {page === "about" && <AboutPage />}
      </div>
    </main>
  )
}
