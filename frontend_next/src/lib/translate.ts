export const LANGUAGES: Record<string, {
  code: string
  label: string
  nativeLabel: string
  srCode: string
}> = {
  English:  {code:"en", label:"EN",
             nativeLabel:"English",   srCode:"en-IN"},
  "हिंदी":  {code:"hi", label:"हिं",
             nativeLabel:"हिंदी",     srCode:"hi-IN"},
  "తెలుగు": {code:"te", label:"తె",
             nativeLabel:"తెలుగు",    srCode:"te-IN"},
  "தமிழ்":  {code:"ta", label:"த",
             nativeLabel:"தமிழ்",     srCode:"ta-IN"},
  "ಕನ್ನಡ":  {code:"kn", label:"ಕ",
             nativeLabel:"ಕನ್ನಡ",     srCode:"kn-IN"},
  "മലയാളം":{code:"ml", label:"മ",
             nativeLabel:"മലയാളം",    srCode:"ml-IN"},
  "मराठी":  {code:"mr", label:"मर",
             nativeLabel:"मराठी",     srCode:"mr-IN"},
  "বাংলা":  {code:"bn", label:"বা",
             nativeLabel:"বাংলা",     srCode:"bn-IN"},
  "ਪੰਜਾਬੀ": {code:"pa", label:"ਪੰ",
             nativeLabel:"ਪੰਜਾਬੀ",   srCode:"pa-IN"},
  "ગુજરાતી":{code:"gu", label:"ગુ",
             nativeLabel:"ગુજરાતી",  srCode:"gu-IN"},
}

// Client-side translation via Google Translate
// (free tier, no API key needed for small volume)
export async function translateToEnglish(
  text: string,
  sourceLang: string
): Promise<string> {
  if (sourceLang === "English") return text
  const code = LANGUAGES[sourceLang]?.code || "en"
  try {
    const url = `https://translate.googleapis.com`
              + `/translate_a/single?client=gtx`
              + `&sl=${code}&tl=en&dt=t`
              + `&q=${encodeURIComponent(text)}`
    const res = await fetch(url)
    const data = await res.json()
    return data[0]?.map((d:any) => d[0])
               .join("") || text
  } catch {
    return text
  }
}

export async function translateFromEnglish(
  text: string,
  targetLang: string
): Promise<string> {
  if (targetLang === "English") return text
  const code = LANGUAGES[targetLang]?.code || "en"
  try {
    const url = `https://translate.googleapis.com`
              + `/translate_a/single?client=gtx`
              + `&sl=en&tl=${code}&dt=t`
              + `&q=${encodeURIComponent(text)}`
    const res = await fetch(url)
    const data = await res.json()
    return data[0]?.map((d:any) => d[0])
               .join("") || text
  } catch {
    return text
  }
}

// Emergency keywords in all 10 languages
export const EMERGENCY_KEYWORDS: Record<string, string[]> = {
  en: ["collapsed","not breathing","heavy bleeding",
       "seizure","convulsion","dying","unconscious",
       "not moving","sudden death"],
  hi: ["गिर गई","सांस नहीं","खून बह","बेहोश","मर रहा"],
  te: ["పడిపోయింది","శ్వాస లేదు","రక్తస్రావం","మరణిస్తోంది"],
  ta: ["விழுந்தது","மூச்சு இல்லை","இரத்தம்","இறந்துவிட்டது"],
  kn: ["ಬಿದ್ದಿತು","ಉಸಿರು ಇಲ್ಲ","ರಕ್ತಸ್ರಾವ"],
  ml: ["വീണു","ശ്വാസം ഇല്ല","രക്തസ്രാവം"],
  mr: ["पडली","श्वास नाही","रक्तस्त्राव"],
  bn: ["পড়ে গেছে","শ্বাস নেই","রক্তপাত"],
  pa: ["ਡਿੱਗ ਪਈ","ਸਾਹ ਨਹੀਂ","ਖੂਨ ਵਹਿਣਾ"],
  gu: ["પડી ગઈ","શ્વાસ નથી","રક્તસ્ત્રાવ"],
}

export function checkEmergency(
  text: string,
  lang: string
): boolean {
  const code = LANGUAGES[lang]?.code || "en"
  const lower = text.toLowerCase()
  const keywords = [
    ...(EMERGENCY_KEYWORDS["en"] || []),
    ...(EMERGENCY_KEYWORDS[code] || []),
  ]
  return keywords.some(kw =>
    lower.includes(kw.toLowerCase()))
}
