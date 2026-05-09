"use client"

import { useState, useRef, useEffect } from "react"
import { usePashuStore } from "@/store/usePashuStore"
import { api } from "@/lib/api"
import { LANGUAGES, translateToEnglish, translateFromEnglish, checkEmergency } from "@/lib/translate"
import { startRecording, speakText, speakViaBackend } from "@/lib/voice"
import { 
  Send, Mic, Image as ImageIcon, Plus, 
  X, User, Bot, AlertCircle, Phone,
  ChevronDown, Globe, MoreHorizontal, Paperclip
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import ReactMarkdown from "react-markdown"
import toast from "react-hot-toast"

export default function ChatPanel() {
  return (
    <div className="flex flex-col h-screen flex-1 bg-white">
      <TopBar />
      <MessageList />
      <InputArea />
    </div>
  )
}

function TopBar() {
  const { selectedLanguage, setLanguage, isOnline } = usePashuStore()

  return (
    <div className="h-14 border-b border-gray-100 flex items-center justify-between px-6 bg-white shrink-0">
      <div className="flex items-center gap-2">
        <h1 className="font-display text-xl text-sage-600 font-semibold">PashuDoctor</h1>
      </div>
      
      <div className="flex bg-gray-50 p-1 rounded-full border border-gray-100">
        {Object.entries(LANGUAGES).slice(0, 3).map(([label, info]) => (
          <button
            key={label}
            onClick={() => setLanguage(label)}
            className={cn(
              "px-4 py-1 rounded-full text-xs font-medium transition-all",
              selectedLanguage === label 
                ? "bg-white text-sage-600 shadow-sm" 
                : "text-gray-500 hover:text-gray-700"
            )}
          >
            {label}
          </button>
        ))}
        <button className="px-2 text-gray-400">
          <MoreHorizontal size={14} />
        </button>
      </div>

      <div className="flex items-center gap-2">
        <div className={cn(
          "w-2 h-2 rounded-full",
          isOnline ? "bg-green-500" : "bg-amber-500"
        )} />
        <span className="text-[10px] font-mono uppercase tracking-widest text-gray-400">
          {isOnline ? "Online" : "Offline"}
        </span>
      </div>
    </div>
  )
}

function MessageList() {
  const { messages, isLoading } = usePashuStore()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  if (messages.length === 0) {
    return <WelcomeScreen />
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-8 scroll-smooth">
      <div className="max-w-[760px] mx-auto flex flex-col gap-6">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <MessageItem key={msg.id} message={msg} />
          ))}
        </AnimatePresence>
        
        {isLoading && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center shrink-0">
              <Bot size={18} className="text-sage-500" />
            </div>
            <div className="bg-white border border-gray-100 p-4 rounded-2xl rounded-tl-sm shadow-sm flex gap-1">
              <div className="w-1.5 h-1.5 bg-sage-300 rounded-full animate-pulse-dot" />
              <div className="w-1.5 h-1.5 bg-sage-300 rounded-full animate-pulse-dot [animation-delay:0.2s]" />
              <div className="w-1.5 h-1.5 bg-sage-300 rounded-full animate-pulse-dot [animation-delay:0.4s]" />
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}

function WelcomeScreen() {
  const { selectedLanguage } = usePashuStore()
  
  const chips = [
    "Cow swelling on udder",
    "Goat has sores in mouth",
    "Buffalo not eating",
    "Vaccination schedule",
    "FMD precautions",
    "Nearby vet helpline",
    "Increase milk yield",
    "LSD prevention"
  ]

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
      >
        <span className="text-5xl block mb-6">🐄</span>
        <h2 className="font-display text-3xl text-gray-800 mb-2">
          Good day, Farmer
        </h2>
        <p className="text-gray-500 max-w-sm mx-auto mb-10 text-sm">
          Describe symptoms or upload a photo to get an AI diagnosis for your livestock.
        </p>
        
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-2xl mx-auto">
          {chips.map((chip, i) => (
            <motion.button
              key={chip}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              className="px-4 py-2 rounded-full border border-gray-200 text-xs font-medium text-gray-600 hover:border-sage-300 hover:bg-sage-50 transition-all text-left truncate"
            >
              {chip}
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  )
}

function MessageItem({ message }: { message: any }) {
  const [showEnglish, setShowEnglish] = useState(false)
  
  const isUser = message.role === "user"
  const isEmergency = message.role === "emergency"

  if (isEmergency) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-red-500 text-white p-6 rounded-3xl flex flex-col items-center text-center shadow-lg shadow-red-200"
      >
        <AlertCircle size={32} className="mb-4" />
        <h3 className="font-display text-4xl mb-2">1962</h3>
        <p className="font-medium mb-4">CRITICAL EMERGENCY DETECTED</p>
        <p className="text-sm opacity-90 mb-6">
          Call the National Animal Helpline immediately. 
          Do not attempt home treatment.
        </p>
        <button className="bg-white text-red-600 px-8 py-3 rounded-full font-bold shadow-sm active:scale-95 transition-transform flex items-center gap-2">
          <Phone size={18} />
          Call Now
        </button>
      </motion.div>
    )
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex w-full gap-3",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center shrink-0">
          <Bot size={18} className="text-sage-500" />
        </div>
      )}

      <div className={cn(
        "max-w-[85%] flex flex-col gap-1",
        isUser ? "items-end" : "items-start"
      )}>
        {!isUser && (
          <span className="text-[10px] font-mono text-sage-600 uppercase tracking-widest px-1">PashuDoctor</span>
        )}
        
        {message.imageUrl && (
          <div className="mb-2 rounded-2xl overflow-hidden border border-gray-100 shadow-sm">
            <img src={message.imageUrl} alt="Uploaded symptom" className="max-w-[200px] h-auto" />
          </div>
        )}

        <div className={cn(
          "px-4 py-3 shadow-sm",
          isUser 
            ? "bg-sage-500 text-white rounded-[20px_20px_4px_20px]" 
            : "bg-white border border-gray-100 rounded-[4px_20px_20px_20px] text-gray-800"
        )}>
          <div className="prose prose-sm prose-slate max-w-none">
            <ReactMarkdown>
              {showEnglish && message.contentEn ? message.contentEn : message.content}
            </ReactMarkdown>
          </div>
          
          {!isUser && message.contentEn && message.contentEn !== message.content && (
            <button 
              onClick={() => setShowEnglish(!showEnglish)}
              className="mt-2 text-[10px] font-bold uppercase tracking-tighter opacity-60 hover:opacity-100 flex items-center gap-1"
            >
              <Globe size={10} />
              {showEnglish ? "View Native" : "View in English"}
            </button>
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-lg bg-sage-500 flex items-center justify-center shrink-0">
          <User size={18} className="text-white" />
        </div>
      )}
    </motion.div>
  )
}

function InputArea() {
  const { 
    userId, caseId, setCaseId, selectedLanguage, 
    isLoading, setLoading, addMessage, setAnalysis,
    pendingImage, setPendingImage, pendingImageUrl,
    isRecording, setRecording, autoSpeak
  } = usePashuStore()
  
  const [text, setText] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSend = async () => {
    if (!text && !pendingImage) return
    
    const currentText = text
    const currentImage = pendingImage
    const currentImageUrl = pendingImageUrl
    
    setText("")
    setPendingImage(null)
    setLoading(true)

    // Add user message
    addMessage({
      role: "user",
      content: currentText,
      imageUrl: currentImageUrl || undefined
    })

    try {
      let response
      if (currentImage) {
        const formData = new FormData()
        formData.append("user_id", userId)
        formData.append("images", currentImage)
        formData.append("symptom_text", currentText || "Analyzing image")
        formData.append("language", selectedLanguage.toLowerCase())
        if (caseId) formData.append("case_id", caseId)
        
        response = await api.analyzeImage(formData)
      } else {
        response = await api.analyzeText({
          user_id: userId,
          symptom_text: currentText,
          language: selectedLanguage.toLowerCase()
        })
      }

      setCaseId(response.case_id)
      setAnalysis(response)

      // Add assistant message
      if (response.diagnosis) {
        addMessage({
          role: "assistant",
          content: response.diagnosis.formatted_response,
          language: selectedLanguage
        })
        
        if (autoSpeak) {
          speakViaBackend(response.diagnosis.formatted_response, LANGUAGES[selectedLanguage].code, process.env.NEXT_PUBLIC_API_URL!)
        }
      } else if (response.follow_up_questions?.length > 0) {
        const q = response.follow_up_questions[0]
        addMessage({
          role: "assistant",
          content: q,
          language: selectedLanguage
        })
        if (autoSpeak) speakText(q, LANGUAGES[selectedLanguage].code)
      }

      // Check Emergency
      if (checkEmergency(currentText, selectedLanguage)) {
        addMessage({
          role: "emergency",
          content: "1962"
        })
      }

    } catch (err: any) {
      toast.error(err.message || "Failed to get diagnosis")
      addMessage({
        role: "assistant",
        content: "I encountered an error. Please try again or call 1962 if the animal is in critical condition."
      })
    } finally {
      setLoading(false)
    }
  }

  const handleVoice = async () => {
    if (isRecording) return
    
    setRecording(true)
    startRecording(
      LANGUAGES[selectedLanguage].code,
      (result) => {
        setText(prev => prev + " " + result)
        setRecording(false)
      },
      (err) => {
        toast.error(err)
        setRecording(false)
      }
    )
  }

  return (
    <div className="shrink-0 pb-6 px-6">
      <div className="max-w-[760px] mx-auto">
        <AnimatePresence>
          {pendingImageUrl && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="mb-4 flex"
            >
              <div className="relative">
                <img src={pendingImageUrl} className="w-20 h-20 object-cover rounded-xl border-2 border-sage-500 shadow-md" />
                <button 
                  onClick={() => setPendingImage(null)}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-white border border-gray-100 rounded-full flex items-center justify-center text-red-500 shadow-sm"
                >
                  <X size={14} />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className={cn(
          "bg-white border-2 rounded-3xl shadow-sm transition-all duration-300",
          isLoading ? "opacity-60 pointer-events-none" : "border-gray-100 focus-within:border-sage-500/50 focus-within:ring-8 focus-within:ring-sage-50"
        )}>
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder={isRecording ? "Listening..." : `Describe symptoms in ${selectedLanguage}...`}
            className="w-full bg-transparent border-none focus:ring-0 p-5 text-gray-700 font-body text-base resize-none"
          />
          
          <div className="flex items-center justify-between px-4 pb-4">
            <div className="flex items-center gap-2">
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={(e) => e.target.files?.[0] && setPendingImage(e.target.files[0])}
                className="hidden" 
                accept="image/*"
              />
              <IconButton 
                icon={<Paperclip size={20} />} 
                onClick={() => fileInputRef.current?.click()} 
              />
              <IconButton 
                icon={<Mic size={20} />} 
                active={isRecording}
                onClick={handleVoice} 
              />
              <IconButton 
                icon={<Plus size={20} />} 
                onClick={() => usePashuStore.getState().clearChat()} 
              />
            </div>
            
            <div className="flex items-center gap-4">
               <span className="text-[10px] font-mono text-gray-300 uppercase tracking-widest">
                 {text.length}/1000
               </span>
               <button 
                 onClick={handleSend}
                 disabled={!text && !pendingImage}
                 className="w-12 h-12 bg-sage-500 text-white rounded-2xl flex items-center justify-center shadow-lg shadow-sage-200 hover:bg-sage-600 transition-colors disabled:opacity-30"
               >
                 <Send size={20} />
               </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function IconButton({ icon, onClick, active }: { icon: any, onClick: () => void, active?: boolean }) {
  return (
    <button 
      onClick={onClick}
      className={cn(
        "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
        active 
          ? "bg-red-50 text-red-500 animate-pulse" 
          : "text-gray-400 hover:bg-sage-50 hover:text-sage-500"
      )}
    >
      {icon}
    </button>
  )
}
