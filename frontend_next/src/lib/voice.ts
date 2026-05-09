export async function startRecording(
  langCode: string,
  onResult: (text: string) => void,
  onError: (err: string) => void
): Promise<() => void> {

  if (!("webkitSpeechRecognition" in window)
      && !("SpeechRecognition" in window)) {
    onError("Speech recognition not supported in this browser. Use Chrome.")
    return () => {}
  }

  const SpeechRecognition =
    (window as any).webkitSpeechRecognition
    || (window as any).SpeechRecognition

  const recognition = new SpeechRecognition()
  recognition.continuous = false
  recognition.interimResults = false
  recognition.lang = langCode + "-IN"
    || "en-IN"
  recognition.maxAlternatives = 1

  recognition.onresult = (event: any) => {
    const transcript =
      event.results[0][0].transcript
    onResult(transcript)
  }

  recognition.onerror = (event: any) => {
    const msgs: Record<string,string> = {
      "no-speech": "No speech detected. Try again.",
      "network": "Network error. Check connection.",
      "not-allowed": "Microphone access denied.",
      "aborted": "Recording stopped.",
    }
    onError(msgs[event.error] || event.error)
  }

  recognition.start()
  return () => recognition.stop()
}

export async function speakText(
  text: string,
  langCode: string
): Promise<void> {
  if (!("speechSynthesis" in window)) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(
    text.slice(0, 300))
  const voices = window.speechSynthesis.getVoices()
  const match = voices.find(v =>
    v.lang.startsWith(langCode))
  if (match) utterance.voice = match
  utterance.rate = 0.9
  utterance.pitch = 1.0
  window.speechSynthesis.speak(utterance)
}

// gTTS fallback via backend
export async function speakViaBackend(
  text: string,
  lang: string,
  apiBase: string
): Promise<void> {
  try {
    const res = await fetch(
      `${apiBase}/analyze/tts`,
      {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({text, lang})
      }
    )
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    await audio.play()
  } catch {
    // silently fail
  }
}
