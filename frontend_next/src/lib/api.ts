const BASE = process.env.NEXT_PUBLIC_API_URL

async function post(endpoint: string,
                    body?: any,
                    isFormData?: boolean) {
  const res = await fetch(BASE + endpoint, {
    method: "POST",
    headers: isFormData ? {} : {
      "Content-Type": "application/json"
    },
    body: isFormData ? body : JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || res.statusText)
  }
  return res.json()
}

async function get(endpoint: string,
                   params?: Record<string,string>) {
  const url = new URL(BASE + endpoint)
  if (params) Object.entries(params).forEach(
    ([k,v]) => url.searchParams.set(k,v))
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error(res.statusText)
  return res.json()
}

export const api = {
  analyzeImage: (formData: FormData) =>
    post("/analyze/image", formData, true),

  analyzeText: (body: {
    user_id: string
    symptom_text: string
    animal_type?: string
    language?: string
  }) => post("/analyze/text-only", body),

  chatMessage: (body: {
    case_id: string
    user_id: string
    message: string
    answered_questions: any[]
  }) => post("/chat/message", body),

  answerQuestions: (body: {
    case_id: string
    user_id: string
    question_answers: any[]
    symptom_text: string
  }) => post("/chat/answer-questions", body),

  getHistory: (userId: string, limit=20) =>
    get(`/history/user/${userId}`, {limit: String(limit)}),

  getStats: (userId: string) =>
    get(`/history/user/${userId}/stats`),

  submitFeedback: (body: {
    case_id: string
    feedback_correct: boolean
    farmer_note?: string
  }) => post("/history/feedback", body),

  getHealth: () => get("/history/health"),

  getDiseases: () => get("/history/diseases"),

  storeVector: (body: { case_id: string }) =>
    post("/history/cases/store-vector", body),

  generateReport: (caseId: string) =>
    fetch(`${BASE}/history/generate-report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: caseId })
    }),
}
