import streamlit as st
import httpx
import json
import os
import base64
import time
import urllib.parse
from uuid import uuid4
from datetime import datetime
import tempfile

# ═══════════════════════════════════════════
# SECTION 1 — PAGE CONFIG & CSS
# ═══════════════════════════════════════════

st.set_page_config(
    page_title="PashuDoctor",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Fraunces:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── RESET ── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"] { display: none !important; }

.main .block-container {
  padding: 0 !important;
  max-width: 100vw !important;
}

/* ── SIDEBAR STYLING ── */
[data-testid="stSidebar"] {
  background-color: #F8F9FA !important;
  color: #1C1917 !important;
  border-right: 1px solid #EAE8E4 !important;
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  padding: 32px 16px !important;
  gap: 0 !important;
}
.sidebar-title {
  font-family: 'Fraunces', serif;
  font-size: 24px;
  font-weight: 500;
  color: #1C1917;
  margin-bottom: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  letter-spacing: -0.5px;
}
.sidebar-item {
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
  color: #57534E;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
  border: 1px solid transparent;
}
.sidebar-item:hover {
  background: #FFFFFF;
  color: #3D7A52;
  border-color: #EAE8E4;
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.sidebar-sep {
  height: 1px;
  background: #EAE8E4;
  margin: 24px 0;
}
.sidebar-label {
  font-size: 11px;
  font-weight: 600;
  color: #525252;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 16px;
  margin-left: 4px;
}

/* ── ROOT LAYOUT ── */
.pd-root {
  display: flex;
  justify-content: center;
  background: #F9F7F4;
  min-height: 100vh;
}

.pd-container {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  min-height: 100vh;
  box-shadow: 0 0 40px rgba(0,0,0,0.03);
}

/* top bar */
.pd-topbar {
  height: 64px;
  background: #FFFFFF;
  border-bottom: 1px solid #F0EDE8;
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 16px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.pd-topbar-logo {
  font-family: 'Fraunces', serif;
  font-size: 22px;
  font-weight: 500;
  color: #3D7A52;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* welcome screen */
.pd-welcome {
  text-align: center;
  padding: 80px 24px 20px;
}
.pd-welcome-icon {
  font-size: 52px;
  display: block;
  margin-bottom: 24px;
}
.pd-welcome-title {
  font-family: 'Fraunces', serif;
  font-size: 36px;
  color: #1C1917;
  margin-bottom: 14px;
  letter-spacing: -0.5px;
}
.pd-welcome-sub {
  color: #78716C;
  font-size: 16px;
  max-width: 480px;
  margin: 0 auto 48px;
  line-height: 1.6;
}

/* chips */
[data-testid="stVerticalBlock"] div.stButton > button {
  border-radius: 24px !important;
  font-size: 14px !important;
  color: #44403C !important;
  border: 1px solid #EAE8E4 !important;
  background: #FFFFFF !important;
  transition: all 0.2s !important;
  padding: 8px 20px !important;
}
[data-testid="stVerticalBlock"] div.stButton > button:hover {
  border-color: #3D7A52 !important;
  color: #3D7A52 !important;
  background: #F4FAF6 !important;
  transform: translateY(-1px);
}

/* input area */
.pd-input-area {
  padding: 24px 32px 32px;
  background: #FFFFFF;
  border-top: 1px solid #F0EDE8;
}
[data-testid="stTextArea"] textarea {
  border-radius: 14px !important;
  border: 1.5px solid #EAE8E4 !important;
  font-size: 15px !important;
  padding: 14px !important;
  line-height: 1.6 !important;
  background: #FFFFFF !important;
  color: #1C1917 !important;
}
[data-testid="stTextArea"] textarea:focus {
  border-color: #3D7A52 !important;
  box-shadow: 0 0 0 3px rgba(61,122,82,0.08) !important;
}

/* hide default file uploader section but keep button */
[data-testid="stFileUploader"] section {
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
}
[data-testid="stFileUploader"] section > div {
  display: none !important;
}
[data-testid="stFileUploader"] button {
  width: 42px !important;
  height: 42px !important;
  border-radius: 12px !important;
  background: #F4F8F4 !important;
  color: #3D7A52 !important;
  border: 1px solid #EBF2EC !important;
  font-size: 20px !important;
}

/* messages */
.msg-ai-bubble {
  background: #FFFFFF;
  border: 1px solid #F0EDE8;
  padding: 16px 20px;
  border-radius: 4px 20px 20px 20px;
  max-width: 85%;
  font-size: 15px;
  line-height: 1.7;
}
.msg-user {
  background: #3D7A52;
  color: #FFFFFF;
  padding: 14px 20px;
  border-radius: 20px 20px 4px 20px;
  max-width: 80%;
  font-size: 15px;
  line-height: 1.6;
}
/* feature cards */
.feat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin: 32px 40px;
}
.feat-card {
  background: #FDFDFD;
  border: 1px solid #F0EDE8;
  border-radius: 16px;
  padding: 20px;
  text-align: left;
  transition: all 0.3s;
}
.feat-card:hover {
  border-color: #3D7A52;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.feat-icon {
  font-size: 24px;
  margin-bottom: 12px;
  display: block;
}
.feat-title {
  font-weight: 600;
  font-size: 15px;
  color: #1C1917;
  margin-bottom: 4px;
}
.feat-desc {
  font-size: 13px;
  color: #78716C;
  line-height: 1.4;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════
# SECTION 2 — ALL IMPORTS & CONSTANTS
# ═══════════════════════════════════════════

# Conditional imports with fallback
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

LANGUAGES = {
    "English": {"code": "en", "sr": "en-IN",
                "gtts": "en", "label": "EN"},
    "हिंदी":   {"code": "hi", "sr": "hi-IN",
                "gtts": "hi", "label": "हिं"},
    "తెలుగు":  {"code": "te", "sr": "te-IN",
                "gtts": "te", "label": "తె"},
    "தமிழ்":   {"code": "ta", "sr": "ta-IN",
                "gtts": "ta", "label": "த"},
    "ಕನ್ನಡ":   {"code": "kn", "sr": "kn-IN",
                "gtts": "kn", "label": "ಕ"},
    "മലയാളം": {"code": "ml", "sr": "ml-IN",
                "gtts": "ml", "label": "മ"},
    "मराठी":   {"code": "mr", "sr": "mr-IN",
                "gtts": "mr", "label": "मर"},
    "বাংলা":   {"code": "bn", "sr": "bn-IN",
                "gtts": "bn", "label": "বা"},
    "ਪੰਜਾਬੀ":  {"code": "pa", "sr": "pa-IN",
                "gtts": "pa", "label": "ਪੰ"},
    "ગુજરાતી": {"code": "gu", "sr": "gu-IN",
                "gtts": "gu", "label": "ગુ"},
}

ANIMAL_ICONS = {
    "cow": "🐄", "buffalo": "🦬",
    "goat": "🐐", "sheep": "🐑",
    "unknown": "❓"
}

EMERGENCY_KEYWORDS = {
    "en": ["collapsed","not breathing","heavy bleeding",
           "seizure","convulsion","dying","dead","unconscious"],
    "hi": ["गिर गई","सांस नहीं","खून बह","बेहोश","मर रहा"],
    "te": ["పడిపోయింది","శ్వాస లేదు","రక్తస్రావం"],
    "ta": ["விழுந்தது","மூச்சு இல்லை","இரத்தம்"],
    "kn": ["ಬಿದ್ದಿತು","ಉಸಿರು ಇಲ್ಲ"],
    "ml": ["വീണു","ശ്വാസം ഇല്ല"],
    "mr": ["पडली","श्वास नाही"],
    "bn": ["পড়ে গেছে","শ্বাস নেই"],
    "pa": ["ਡਿੱਗ ਪਈ","ਸਾਹ ਨਹੀਂ"],
    "gu": ["પડી ગઈ","શ્વાસ નથી"],
}

CHIPS = [
    ("🔬", "Analyze FMD",
     "Analyze my animal for foot and mouth disease symptoms"),
    ("🥛", "Mastitis Check",
     "Check this animal for mastitis symptoms"),
    ("🌡️", "Fever Analysis",
     "My animal has high fever, help diagnose the cause"),
    ("🐛", "Skin Disease",
     "Analyze this animal for skin disease or lumpy skin"),
    ("🚨", "Emergency Help",
     "My animal has severe symptoms, what should I do?"),
    ("🔍", "Similar Cases",
     "Find similar disease cases from the database"),
    ("📊", "Herd Alert",
     "Should I isolate this animal from my herd?"),
    ("💉", "Prevention",
     "What vaccines does my animal need?"),
]

CONTAGIOUS = [
    "foot_and_mouth","lumpy_skin_disease",
    "ppr","hemorrhagic_septicemia","blackquarter"
]

VET_STATE_NUMBERS = {
    "Telangana":"040-23490007",
    "Andhra Pradesh":"0866-2474933",
    "Maharashtra":"022-27560232",
    "Punjab":"0172-2740843",
    "Gujarat":"079-22861609",
    "Karnataka":"080-22253131",
    "Tamil Nadu":"044-25384913",
    "Uttar Pradesh":"0522-2740158",
}

# ═══════════════════════════════════════════
# SECTION 3 — HELPER FUNCTIONS
# ═══════════════════════════════════════════

def init_session():
    defaults = {
        "chat_history": [],
        "case_id": None,
        "last_analysis": None,
        "selected_language": "English",
        "user_id": str(uuid4())[:8],
        "pending_image": None,
        "pending_image_b64": None,
        "pending_image_name": None,
        "is_loading": False,
        "input_text": "",
        "chip_inject": None,
        "answered_questions": [],
        "pending_questions": [],
        "page": "chat",
        "auto_speak": False,
        "state_location": "Telangana",
        "recording": False,
        "last_uploaded_name": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def api_post(endpoint, json_data=None,
             files=None, data=None) -> dict:
    try:
        with httpx.Client(timeout=120) as client:
            if files:
                r = client.post(
                    f"{API_BASE}{endpoint}",
                    files=files, data=data)
            else:
                r = client.post(
                    f"{API_BASE}{endpoint}",
                    json=json_data)
            if r.status_code >= 400:
                try:
                    detail = r.json().get(
                        "detail", r.text[:200])
                except:
                    detail = r.text[:200]
                return {"success": False,
                        "error": str(detail)}
            return r.json()
    except httpx.ConnectError:
        return {"success": False,
                "error": "Cannot connect to API. "
                         "Run: make run"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def api_get(endpoint, params=None) -> dict:
    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(
                f"{API_BASE}{endpoint}",
                params=params)
            return r.json()
    except:
        return {}

def is_online() -> bool:
    try:
        httpx.get("https://8.8.8.8", timeout=2)
        return True
    except:
        return False

def translate_to_english(text: str,
                          lang_name: str) -> str:
    if lang_name == "English":
        return text
    lang_code = LANGUAGES[lang_name]["code"]
    if TRANSLATOR_AVAILABLE and is_online():
        try:
            return GoogleTranslator(
                source=lang_code,
                target="en").translate(text) or text
        except:
            pass
    if ARGOS_AVAILABLE:
        try:
            return argostranslate.translate\
                .translate(text, lang_code, "en") or text
        except:
            pass
    return text

def translate_from_english(text: str,
                            lang_name: str) -> str:
    if lang_name == "English":
        return text
    lang_code = LANGUAGES[lang_name]["code"]
    if TRANSLATOR_AVAILABLE and is_online():
        try:
            return GoogleTranslator(
                source="en",
                target=lang_code).translate(text) or text
        except:
            pass
    if ARGOS_AVAILABLE:
        try:
            return argostranslate.translate\
                .translate(text, "en", lang_code) or text
        except:
            pass
    return text

def speak_text(text: str, lang_name: str) -> None:
    if not GTTS_AVAILABLE:
        return
    try:
        lang_code = LANGUAGES[lang_name]["gtts"]
        tts = gTTS(text=text[:500], lang=lang_code,
                   slow=False)
        tmp = tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False)
        tts.save(tmp.name)
        with open(tmp.name, "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3",
                 autoplay=True)
        os.unlink(tmp.name)
    except:
        pass

def check_emergency(text: str,
                    lang_name: str) -> bool:
    lang_code = LANGUAGES[lang_name]["code"]
    text_lower = text.lower()
    keywords = (EMERGENCY_KEYWORDS.get("en", []) +
                EMERGENCY_KEYWORDS.get(lang_code, []))
    return any(kw.lower() in text_lower
               for kw in keywords)

def record_voice(lang_name: str) -> dict:
    if not SR_AVAILABLE:
        return {"success": False,
                "error": "SpeechRecognition not installed"}
    lang_code = LANGUAGES[lang_name]["sr"]
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(
                source, duration=1)
            audio = recognizer.listen(
                source, timeout=8,
                phrase_time_limit=15)
        text = recognizer.recognize_google(
            audio, language=lang_code)
        translated = translate_to_english(
            text, lang_name)
        return {
            "success": True,
            "original": text,
            "translated": translated
        }
    except sr.UnknownValueError:
        if WHISPER_AVAILABLE:
            return {"success": False,
                    "error": "no_speech",
                    "fallback": "whisper"}
        return {"success": False,
                "error": "No speech detected"}
    except sr.RequestError:
        return {"success": False,
                "error": "Speech API error"}
    except OSError:
        return {"success": False,
                "error": "No microphone found"}

def img_to_b64(image_bytes) -> str:
    return base64.b64encode(image_bytes).decode()

def format_diagnosis_for_chat(resp: dict,
                               lang: str) -> str:
    if not resp or not resp.get("diagnosis"):
        if resp and resp.get("follow_up_questions"):
            qs = resp["follow_up_questions"]
            lines = ["I need a few more details to "
                     "make an accurate diagnosis:\n"]
            for i, q in enumerate(qs[:3], 1):
                lines.append(f"{i}. {q}")
            en_text = "\n".join(lines)
        else:
            en_text = ("I couldn't make a confident "
                       "diagnosis. Please provide more "
                       "information or a clearer photo.")
        return translate_from_english(en_text, lang)

    d = resp["diagnosis"]
    conf = resp.get("confidence", {})
    pct = conf.get("percentage", 0)
    disease = (d.get("primary_diagnosis", "Unknown")
               .replace("_", " ").title())
    severity = d.get("severity", "unknown").title()
    urgency = d.get("vet_urgency", "").replace(
        "_", " ")
    advice = d.get("farmer_advice", "")
    precs = d.get("immediate_precautions", [])[:3]
    warns = d.get("urgent_warning_signs", [])[:2]

    lines = [
        f"**Diagnosis: {disease}** ({pct}% confidence)",
        f"Severity: {severity} | Vet urgency: {urgency}",
        "",
    ]
    if advice:
        lines.append(advice)
    if precs:
        lines.append("\n**Immediate steps:**")
        for p in precs:
            lines.append(f"• {p}")
    if warns:
        lines.append("\n**Watch for:**")
        for w in warns:
            lines.append(f"⚠ {w}")
    lines.append(
        "\n*Please consult a licensed veterinarian. "
        "National Helpline: 1962 (Free, 24/7)*")

    en_text = "\n".join(lines)
    return translate_from_english(en_text, lang)

# ═══════════════════════════════════════════
# SECTION 4 — INTEGRATED ANALYSIS RENDERER
# ═══════════════════════════════════════════

def render_analysis_report(resp: dict):
    if not resp:
        return
    lang = st.session_state.selected_language

    with st.expander(f"📊 {translate_from_english('Diagnostic Report', lang)}", expanded=True):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # CARD 1 — Animal
            animal = resp.get("animal_detection", {})
            atype = animal.get("animal", "unknown")
            aconf = animal.get("confidence", 0)
            aicon = ANIMAL_ICONS.get(atype, "❓")
            st.markdown(f"""
            <div class="a-card">
              <div class="a-card-label">{translate_from_english("Detected Animal", lang)}</div>
              <div class="a-card-val" style="font-size:24px">{aicon} {translate_from_english(atype.title(), lang)}</div>
              <div class="a-card-sub">{aconf*100:.0f}% {translate_from_english("confidence", lang)}</div>
            </div>
            """, unsafe_allow_html=True)

            # CARD 2 — Diagnosis
            diag = resp.get("diagnosis")
            if diag:
                disease_raw = diag.get("primary_diagnosis","").replace("_"," ").title()
                disease = translate_from_english(disease_raw, lang)
                severity = diag.get("severity","unknown")
                sev_label = translate_from_english(severity.title(), lang)
                sev_class = {"mild":"sev-mild","moderate":"sev-moderate","severe":"sev-severe","emergency":"sev-emergency"}.get(severity, "sev-moderate")
                st.markdown(f"""
                <div class="a-card">
                  <div class="a-card-label">{translate_from_english("Diagnosis", lang)}</div>
                  <div class="a-card-val" style="font-size:20px; font-weight:bold">{disease}</div>
                  <div class="sev-badge {sev_class}">{sev_label}</div>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            # CARD 3 — Confidence
            conf = resp.get("confidence", {})
            pct = conf.get("percentage", 0)
            st.markdown(f"""
            <div class="a-card">
              <div class="a-card-label">{translate_from_english("AI Confidence", lang)}</div>
              <div class="a-card-val" style="font-size:24px">{pct}%</div>
              <div class="conf-track"><div class="conf-fill" style="width:{pct}%"></div></div>
            </div>
            """, unsafe_allow_html=True)

            # CARD 4 — Herd Alert
            if diag and diag.get("primary_diagnosis", "") in CONTAGIOUS:
                st.markdown(f"""
                <div class="herd-alert" style="margin-top:10px; border-left:5px solid #DC2626; background:#FEF2F2; padding:10px">
                  <div class="herd-alert-title" style="color:#DC2626; font-weight:bold">⚠️ {translate_from_english("Contagious Alert", lang)}</div>
                  <div class="herd-alert-body" style="font-size:13px; margin-top:5px">{translate_from_english("Isolate this animal immediately to protect your herd.", lang)}</div>
                </div>
                """, unsafe_allow_html=True)

        # Immediate Steps
        if diag and diag.get("immediate_precautions"):
            precs = diag.get("immediate_precautions", [])[:3]
            prec_html = "".join(f'<li>{p}</li>' for p in precs)
            st.markdown(f"""
            <div class="a-card">
              <div class="a-card-label">Immediate Steps</div>
              <ul style="font-size:13px; color:#44403C; padding-left:18px; margin-top:8px">
                {prec_html}
              </ul>
            </div>
            """, unsafe_allow_html=True)

        # Helpline & Action
        st.markdown(f"""
        <div class="vet-card" style="display:flex; align-items:center; justify-content:space-between">
          <div>
            <div class="a-card-sub">National Animal Helpline</div>
            <div class="vet-number" style="font-size:24px">1962</div>
          </div>
          <a href="https://wa.me/" target="_blank" style="text-decoration:none">
            <button class="pd-chip" style="background:#3D7A52; color:white; border:none">Share on WhatsApp</button>
          </a>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════
# SECTION 5 — SEND MESSAGE HANDLER
# ═══════════════════════════════════════════

def handle_send(text: str, image_bytes,
                image_name: str, lang: str):

    # Translate to English
    en_text = translate_to_english(text, lang)

    # Emergency check
    if check_emergency(en_text, lang):
        em_msg = (
            "🚨 **EMERGENCY DETECTED**\n\n"
            "Call **1962** immediately — "
            "Free, 24/7, all languages.\n\n"
            "Do NOT attempt home treatment.\n"
            "Keep the animal calm and still."
        )
        em_translated = translate_from_english(
            em_msg, lang)
        st.session_state.chat_history.append({
            "role": "emergency",
            "content": em_translated,
        })
        st.session_state.is_loading = False
        return

    # Add user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": text,
        "content_en": en_text,
        "language": lang,
        "image_bytes": image_bytes,
        "image_name": image_name,
    })

    # Show loading
    st.session_state.is_loading = True
    st.session_state.chat_history.append({
        "role": "thinking", "content": ""
    })
    st.rerun()

def process_api_call():
    history = st.session_state.chat_history
    last_user = next(
        (m for m in reversed(history)
         if m["role"] == "user"), None)
    if not last_user:
        return

    en_text = last_user.get("content_en",
                             last_user["content"])
    image_bytes = last_user.get("image_bytes")
    lang = last_user.get("language", "English")
    case_id = st.session_state.case_id

    # Remove thinking message
    st.session_state.chat_history = [
        m for m in st.session_state.chat_history
        if m.get("role") != "thinking"
    ]

    if case_id:
        # Continue chat
        resp = api_post("/chat/message", json_data={
            "case_id": case_id,
            "user_id": st.session_state.user_id,
            "message": en_text,
            "answered_questions":
                st.session_state.answered_questions
        })
        if resp.get("success"):
            ai_text = resp.get("response", "")
            translated = translate_from_english(
                ai_text, lang)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": translated,
                "content_en": ai_text,
                "language": lang,
            })
            # Check if analysis updated
            if resp.get("diagnosis_updated") and resp.get("diagnosis"):
                if st.session_state.last_analysis:
                    st.session_state.last_analysis["diagnosis"] = resp["diagnosis"]
                else:
                    st.session_state.last_analysis = {"diagnosis": resp["diagnosis"]}
                # Add a marker to the message that analysis was updated
                st.session_state.chat_history[-1]["analysis"] = resp["diagnosis"]
    else:
        # New analysis
        if image_bytes:
            files = [("images", (
                last_user.get("image_name","photo.jpg"),
                image_bytes,
                "image/jpeg"
            ))]
            form_data = {
                "user_id": st.session_state.user_id,
                "symptom_text": en_text,
                "language": "english"
            }
            resp = api_post(
                "/analyze/image",
                files=files,
                data=form_data)
        else:
            resp = api_post("/analyze/text-only", json_data={
                "user_id": st.session_state.user_id,
                "symptom_text": en_text,
                "language": "english"
            })

        if resp.get("success"):
            st.session_state.case_id = resp.get(
                "case_id")
            st.session_state.last_analysis = resp
            st.session_state.pending_questions = resp.get(
                "follow_up_questions", [])

            ai_text = format_diagnosis_for_chat(
                resp, lang)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": ai_text,
                "content_en": ai_text,
                "language": lang,
                "analysis": resp  # store analysis for integrated rendering
            })

            if (st.session_state.auto_speak
                    and GTTS_AVAILABLE):
                speak_text(
                    ai_text[:300], lang)
        else:
            err = resp.get("error", "Unknown error")
            err_msg = translate_from_english(
                f"Sorry, I encountered an error: {err}",
                lang)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": err_msg,
                "language": lang,
            })

    st.session_state.is_loading = False
    st.session_state.pending_image = None
    st.session_state.pending_image_b64 = None
    st.session_state.pending_image_name = None

# ═══════════════════════════════════════════
# SECTION 6 — MAIN RENDER
# ═══════════════════════════════════════════

def render_chat_page():
    lang = st.session_state.selected_language

    # Greeting logic
    hour = datetime.now().hour
    greeting = ("Good morning" if hour < 12
                else "Good afternoon"
                if hour < 17 else "Good evening")
    greeting_translated = translate_from_english(greeting, lang)

    # ── TOPBAR ──
    with st.container():
        # Clean, unified top bar row
        t_col1, t_col2, t_col3 = st.columns([6, 1.5, 2.5])
        
        with t_col1:
            st.markdown("""
            <div class="pd-topbar-logo">
              <span>🐄</span> PashuDoctor
            </div>
            """, unsafe_allow_html=True)
            
        with t_col2:
            conn = is_online()
            dot = "🟢" if conn else "🟠"
            conn_label = "Connected" if conn else "Offline"
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:6px; font-size:11px; color:#78716C; margin-top:14px">
              {dot} {conn_label}
            </div>
            """, unsafe_allow_html=True)
            
        with t_col3:
            lang_names = list(LANGUAGES.keys())
            sel_idx = lang_names.index(st.session_state.selected_language)
            st.markdown('<div style="margin-top:4px">', unsafe_allow_html=True)
            new_lang = st.selectbox(
                "Language", lang_names, index=sel_idx, 
                label_visibility="collapsed", key="lang_select_top"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if new_lang != st.session_state.selected_language:
                st.session_state.selected_language = new_lang
                st.rerun()

    st.markdown('<div style="margin-bottom:24px; border-bottom:1px solid #F0EDE8"></div>', unsafe_allow_html=True)

    # ── CHAT SCROLL AREA ──
    chat_container = st.container()
    with chat_container:
        history = st.session_state.chat_history

        if not history:
            # Welcome screen
            welcome_title = translate_from_english(
                f"{greeting_translated}, Farmer", lang)
            welcome_sub = translate_from_english(
                "Describe your animal's symptoms or "
                "upload a photo to begin diagnosis",
                lang)
            st.markdown(f"""
            <div class="pd-welcome">
              <span class="pd-welcome-icon">🐄</span>
              <div class="pd-welcome-title">
                {welcome_title}
              </div>
              <div class="pd-welcome-sub">
                {welcome_sub}
              </div>
            </div>
            
            <div class="feat-grid">
              <div class="feat-card">
                <span class="feat-icon">📸</span>
                <div class="feat-title">{translate_from_english("Photo Analysis", lang)}</div>
                <div class="feat-desc">{translate_from_english("Upload clear photos of symptoms for AI diagnosis", lang)}</div>
              </div>
              <div class="feat-card">
                <span class="feat-icon">🎙️</span>
                <div class="feat-title">{translate_from_english("Voice Support", lang)}</div>
                <div class="feat-desc">{translate_from_english("Talk to me in your local language", lang)}</div>
              </div>
              <div class="feat-card">
                <span class="feat-icon">🏥</span>
                <div class="feat-title">{translate_from_english("Vet Support", lang)}</div>
                <div class="feat-desc">{translate_from_english("Get urgent precautions and helpline numbers", lang)}</div>
              </div>
              <div class="feat-card">
                <span class="feat-icon">🌍</span>
                <div class="feat-title">{translate_from_english("Multi-Language", lang)}</div>
                <div class="feat-desc">{translate_from_english("Supports Hindi, Telugu, Tamil, and more", lang)}</div>
              </div>
            </div>

            <div style="text-align:center; margin-top:40px; margin-bottom:16px">
              <div style="font-size:12px; font-weight:700; color:#A8A29E; text-transform:uppercase; letter-spacing:1px">
                {translate_from_english("Quick Start", lang)}
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Quick action chips - centered and elegant
            st.markdown('<div style="display:flex; justify-content:center; flex-wrap:wrap; gap:8px; margin-bottom:40px; padding:0 40px">', unsafe_allow_html=True)
            chip_cols = st.columns(4)
            for i, (icon, label, prompt) in enumerate(CHIPS[:8]):
                with chip_cols[i % 4]:
                    translated_label = translate_from_english(label, lang)
                    if st.button(
                        f"{icon} {translated_label}",
                        key=f"chip_btn_{i}",
                        use_container_width=True
                    ):
                        st.session_state.chip_inject = prompt
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        else:
            # Render messages
            for msg in history:
                role = msg.get("role")
                content = msg.get("content", "")
                img_bytes = msg.get("image_bytes")

                if role == "user":
                    img_html = ""
                    if img_bytes:
                        b64 = img_to_b64(img_bytes)
                        img_html = (
                            f'<img class="msg-img-thumb"'
                            f' src="data:image/jpeg;'
                            f'base64,{b64}" />'
                        )
                    st.markdown(f"""
                    <div class="msg-user-wrap">
                      <div class="msg-user">
                        {img_html}
                        {content}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                elif role == "thinking":
                    st.markdown("""
                    <div class="thinking-wrap">
                      <div class="msg-ai-avatar">🐄</div>
                      <div class="thinking-dots">
                        <div class="t-dot"></div>
                        <div class="t-dot"></div>
                        <div class="t-dot"></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                elif role == "emergency":
                    st.markdown(f"""
                    <div class="msg-ai-wrap">
                      <div class="msg-ai-avatar">🚨</div>
                      <div class="emergency-card">
                        <div class="emergency-title">
                          Emergency Detected
                        </div>
                        <div class="emergency-num">
                          1962
                        </div>
                        <div style="font-size:13px;
                                    margin-top:6px">
                          {content}
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                elif role == "assistant":
                    ml = msg.get("language", "English")
                    en = msg.get("content_en", "")
                    show_toggle = (
                        ml != "English" and en
                        and en != content)
                    st.markdown(f"""
                    <div class="msg-ai-wrap">
                      <div class="msg-ai-avatar">🐄</div>
                      <div class="msg-ai-bubble">
                        <div class="msg-ai-label">
                          PashuDoctor
                        </div>
                        {content}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Audio Playback for Farmers
                    if st.button(f"🔊 {translate_from_english('Listen', lang)}", key=f"speak_{msg.get('content_en','')[:10]}"):
                        speak_text(content, lang)
                    
                    # INTEGRATED ANALYSIS
                    if msg.get("analysis"):
                        render_analysis_report(msg["analysis"])
                    
                    if show_toggle:
                        with st.expander(
                                "View in English"):
                            st.markdown(en)

    # ── INPUT AREA ──
    st.markdown('<div class="pd-input-area">'
                '<div class="pd-input-inner">',
                unsafe_allow_html=True)

    # Image preview
    if st.session_state.pending_image_b64:
        b64 = st.session_state.pending_image_b64
        st.markdown(f"""
        <div class="input-img-preview">
          <img src="data:image/jpeg;base64,{b64}" />
        </div>
        """, unsafe_allow_html=True)
        if st.button("✕ Remove image",
                     key="remove_img"):
            st.session_state.pending_image = None
            st.session_state.pending_image_b64 = None
            st.session_state.pending_image_name = None
            st.rerun()

    # Text input
    placeholder = translate_from_english(
        "Describe symptoms or ask anything...", lang)
    
    # Value conflict fix: pop before render
    injected = st.session_state.pop("chip_inject", None) or ""
    
    input_val = st.text_area(
        "Message",
        value=injected,
        placeholder=placeholder,
        height=100,
        max_chars=1000,
        key="main_input",
        label_visibility="collapsed"
    )

    # Compact Toolbar row
    t1, t2, t3, t4, t5, t_send = st.columns([0.8, 0.8, 0.8, 0.8, 5, 1.8])
    
    with t1:
        uploaded = st.file_uploader(
            "📎", type=["jpg","jpeg","png","webp"],
            key="img_upload", label_visibility="collapsed"
        )
        if uploaded and uploaded.name != st.session_state.get("last_uploaded_name"):
            img_bytes = uploaded.read()
            st.session_state.pending_image = img_bytes
            st.session_state.pending_image_b64 = img_to_b64(img_bytes)
            st.session_state.pending_image_name = uploaded.name
            st.session_state.last_uploaded_name = uploaded.name
            st.rerun()

    with t2:
        if st.button("🎤" if not st.session_state.recording else "🔴", key="voice_btn"):
            st.session_state.recording = not st.session_state.recording
            st.rerun()

    with t3:
        if st.button("🔊" if st.session_state.auto_speak else "🔇", key="speak_toggle"):
            st.session_state.auto_speak = not st.session_state.auto_speak
            st.rerun()

    with t4:
        if st.button("✚", key="new_chat_btn"):
            st.session_state.chat_history = []
            st.session_state.case_id = None
            st.session_state.last_analysis = None
            st.session_state.pending_image = None
            st.session_state.pending_image_b64 = None
            st.session_state.answered_questions = []
            st.rerun()

    with t_send:
        can_send = bool(input_val.strip() or st.session_state.pending_image)
        if st.button("Send ↑", key="send_btn", disabled=not can_send, type="primary", use_container_width=True):
            handle_send(
                text=input_val.strip(),
                image_bytes=st.session_state.pending_image,
                image_name=st.session_state.get("pending_image_name","photo.jpg"),
                lang=lang
            )

    st.markdown(
        '<div class="input-footer">'
        'PashuDoctor AI · Not a substitute for '
        'veterinary advice · 1962 helpline 24/7'
        '</div></div></div>',
        unsafe_allow_html=True)

    # Handle voice recording
    if st.session_state.recording:
        with st.spinner(
            "🎤 Listening... speak now"):
            result = record_voice(lang)
        st.session_state.recording = False
        if result["success"]:
            st.success(
                f"Heard: {result['original']}")
            st.session_state.chip_inject = \
                result["translated"]
        else:
            err = result.get("error",
                             "Could not hear")
            st.warning(f"Voice: {err}")
        st.rerun()

    # Process API if loading
    if st.session_state.is_loading:
        process_api_call()
        st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🐄 PashuDoctor</div>', unsafe_allow_html=True)
        
        # New Chat Button
        if st.button("＋ New Chat", key="side_new_chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.case_id = None
            st.session_state.last_analysis = None
            st.session_state.pending_image = None
            st.session_state.pending_image_b64 = None
            st.session_state.answered_questions = []
            st.rerun()

        st.markdown('<div class="sidebar-sep"></div>', unsafe_allow_html=True)
        
        # History Section
        st.markdown('<div class="sidebar-label">Recent Diagnoses</div>', unsafe_allow_html=True)
        
        # Fetch actual history from API (GET)
        resp = api_get(f"/history/{st.session_state.user_id}")
        if resp.get("success") and resp.get("cases"):
            for case in resp["cases"][:8]:
                c_id = case["case_id"][:8]
                diag = case["primary_diagnosis"].replace("_", " ").title()
                date = case["created_at"].split("T")[0]
                if st.button(f"📄 {diag}", key=f"hist_{c_id}", use_container_width=True):
                    # In a real app, we would load the case state here
                    st.info(f"Loading {diag}...")
        else:
            st.markdown('<div style="font-size:13px; color:#404040; font-style:italic; margin-left:16px">No recent cases</div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-sep"></div>', unsafe_allow_html=True)
        
        # Settings
        st.markdown('<div class="sidebar-label">Settings</div>', unsafe_allow_html=True)
        
        st.session_state.auto_speak = st.toggle("🔊 Auto-speak", value=st.session_state.auto_speak)
        
        st.markdown('<div class="sidebar-sep"></div>', unsafe_allow_html=True)
        
        # Emergency
        st.markdown("""
        <div style="background:#FFFFFF; border-radius:12px; padding:12px; border:1px solid #FEE2E2">
          <div style="font-size:11px; color:#ef4444; font-weight:600; margin-bottom:4px">EMERGENCY HELPLINE</div>
          <div style="font-size:20px; color:#1C1917; font-weight:700">1962</div>
          <div style="font-size:11px; color:#78716C; margin-top:4px">Available 24/7 (Free)</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    init_session()
    
    # Render Sidebar first
    render_sidebar()

    # Center-focused container for the whole app
    st.markdown('<div class="pd-root"><div class="pd-container">', unsafe_allow_html=True)
    
    render_chat_page()
    
    st.markdown('</div></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
