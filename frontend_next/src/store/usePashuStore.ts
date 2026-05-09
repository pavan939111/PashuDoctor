import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

interface Message {
  id: string
  role: "user" | "assistant" | "thinking" | "emergency"
  content: string
  contentEn?: string
  language?: string
  imageUrl?: string
  timestamp: Date
}

interface Analysis {
  caseId: string
  animalDetection: {
    animal: string
    confidence: number
    method: string
  }
  diagnosis: {
    primaryDiagnosis: string
    alternativeDiagnoses: string[]
    matchingSymptoms: string[]
    immediatePrecautions: string[]
    urgentWarningSigns: string[]
    herdPrevention: string[]
    farmerAdvice: string
    vetUrgency: string
    severity: string
    formattedResponse: string
  } | null
  confidence: {
    score: number
    percentage: number
    action: string
    message: string
    showPrediction: boolean
    imageSim: number
    textSim: number
    symptomMatch: number
  }
  topCandidates: Array<{
    disease: string
    animal: string
    bodyPart: string
    severity: string
    finalScore: number
    rerankerScore: number
  }>
  followUpQuestions: string[]
  retrievalTimeMs: number
  llmTimeMs: number
  modelUsed: string
  success: boolean
}

interface PashuStore {
  // State
  messages: Message[]
  analysis: Analysis | null
  caseId: string | null
  userId: string
  selectedLanguage: string
  isLoading: boolean
  pendingImage: File | null
  pendingImageUrl: string | null
  autoSpeak: boolean
  isOnline: boolean
  isRecording: boolean
  selectedState: string
  page: "chat" | "history" | "about"
  answeredQuestions: Array<{q:string, a:string}>

  // Actions
  addMessage: (msg: Omit<Message, "id"|"timestamp">) => void
  setAnalysis: (a: Analysis | null) => void
  setCaseId: (id: string | null) => void
  setLanguage: (lang: string) => void
  setLoading: (v: boolean) => void
  setPendingImage: (f: File | null) => void
  setAutoSpeak: (v: boolean) => void
  setOnline: (v: boolean) => void
  setRecording: (v: boolean) => void
  setPage: (p: "chat" | "history" | "about") => void
  clearChat: () => void
  addAnsweredQuestion: (q:string, a:string) => void
}

export const usePashuStore = create<PashuStore>()(
  immer((set) => ({
    messages: [],
    analysis: null,
    caseId: null,
    userId: typeof window !== 'undefined' ? (localStorage.getItem('pashu_user_id') || crypto.randomUUID()) : '',
    selectedLanguage: 'English',
    isLoading: false,
    pendingImage: null,
    pendingImageUrl: null,
    autoSpeak: true,
    isOnline: true,
    isRecording: false,
    selectedState: 'Uttar Pradesh',
    page: 'chat',
    answeredQuestions: [],

    addMessage: (msg) => set((state) => {
      state.messages.push({
        ...msg,
        id: crypto.randomUUID(),
        timestamp: new Date()
      })
    }),

    setAnalysis: (a) => set((state) => {
      state.analysis = a
    }),

    setCaseId: (id) => set((state) => {
      state.caseId = id
    }),

    setLanguage: (lang) => set((state) => {
      state.selectedLanguage = lang
    }),

    setLoading: (v) => set((state) => {
      state.isLoading = v
    }),

    setPendingImage: (f) => set((state) => {
      state.pendingImage = f
      if (state.pendingImageUrl) {
        URL.revokeObjectURL(state.pendingImageUrl)
      }
      state.pendingImageUrl = f ? URL.createObjectURL(f) : null
    }),

    setAutoSpeak: (v) => set((state) => {
      state.autoSpeak = v
    }),

    setOnline: (v) => set((state) => {
      state.isOnline = v
    }),

    setRecording: (v) => set((state) => {
      state.isRecording = v
    }),

    setPage: (p) => set((state) => {
      state.page = p
    }),

    clearChat: () => set((state) => {
      state.messages = []
      state.analysis = null
      state.caseId = null
      state.answeredQuestions = []
    }),

    addAnsweredQuestion: (q, a) => set((state) => {
      state.answeredQuestions.push({ q, a })
    }),
  }))
)

// Persistence
if (typeof window !== 'undefined') {
  const userId = usePashuStore.getState().userId
  localStorage.setItem('pashu_user_id', userId)
}
