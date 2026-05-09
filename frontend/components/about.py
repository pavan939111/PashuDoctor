import streamlit as st
import pandas as pd
from utils.api import api_get
from services.language_service import LanguageService
from services.speech_service import SpeechService

def show_about_page():
    lang_service = st.session_state.lang_service
    speech_service = st.session_state.speech_service
    language = st.session_state.get("selected_language", "English")
    ui = lang_service.get_ui_strings(language)
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    header_text = lang_service.translate_from_english("About PashuDoctor", language)
    st.markdown(f'<h1 class="pd-header">ℹ️ {header_text}</h1>', unsafe_allow_html=True)

    # Section 1 — What is PashuDoctor
    about_text = "PashuDoctor is a production-grade AI health assistant built specifically for Indian livestock farmers. Our system combines cutting-edge Computer Vision (CLIP) and Large Language Models with a specialized knowledge base of livestock diseases to provide instant, field-ready advice."
    st.markdown(lang_service.translate_from_english(about_text, language))
    
    animals_text = f"**{lang_service.translate_from_english('Supported Animals', language)}:** Cows, Buffaloes, Goats, and Sheep."
    st.markdown(animals_text)

    # Section 2 — How it works (4 steps)
    st.markdown("### ⚙️ How it works")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="pd-card" style="text-align: center; height: 180px;">1️⃣<br><b>Upload</b><br><small>Upload photo or describe symptoms</small></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="pd-card" style="text-align: center; height: 180px;">2️⃣<br><b>Detect</b><br><small>AI identifies animal and assesses quality</small></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="pd-card" style="text-align: center; height: 180px;">3️⃣<br><b>Analyze</b><br><small>Retrieves knowledge from 7,000+ medical records</small></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="pd-card" style="text-align: center; height: 180px;">4️⃣<br><b>Advise</b><br><small>Get diagnosis and precautions instantly</small></div>', unsafe_allow_html=True)

    # Section 3 — Supported diseases table
    st.markdown("### 🩺 Supported Conditions")
    diseases_data = [
        ["Mastitis", "Cow, Buffalo", "Swollen udder, reduced milk, clots in milk", "High"],
        ["FMD (Foot and Mouth Disease)", "All Cattle", "Mouth sores, excessive drooling, lameness", "Very High"],
        ["Lumpy Skin Disease (LSD)", "Cow, Buffalo", "Skin nodules (lumps), fever, leg swelling", "High"],
        ["Black Quarter (BQ)", "Cow, Buffalo", "Swelling in thighs/shoulders, high fever", "Moderate"],
        ["Hemorrhagic Septicemia (HS)", "Buffalo, Cow", "Throat swelling, difficulty breathing", "Moderate"],
        ["PPR (Goat Plague)", "Goat, Sheep", "High fever, nasal discharge, diarrhea", "High"],
        ["Brucellosis", "All Livestock", "Abortion in late pregnancy, joint swelling", "Moderate"]
    ]
    df = pd.DataFrame(diseases_data, columns=["Disease", "Animals Affected", "Common Symptoms", "India Risk Level"])
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Section 4 — Important disclaimer
    st.warning("""
    **⚠️ VETERINARY DISCLAIMER:**
    PashuDoctor is an AI decision-support tool. It is NOT a substitute for professional veterinary advice, 
    diagnosis, or treatment. Medical conditions in animals can deteriorate rapidly. 
    **Always consult a licensed veterinarian before administering any medication or starting any treatment.**
    """)

    # Section 5 — System status
    st.divider()
    st.markdown("### 🛠️ Backend System Status")
    health = api_get("/health")
    
    if health.get("status") == "healthy" or health.get("status") == "unstable":
        status_color = "#2E7D32" if health.get("status") == "healthy" else "#F57C00"
        st.markdown(f"Current Status: <b style='color: {status_color};'>{health.get('status').upper()}</b>", unsafe_allow_html=True)
        
        services = health.get("services", {})
        if services:
            status_list = []
            for name, details in services.items():
                latency = f"{details.get('latency_ms', 0):.0f}ms" if "latency_ms" in details else "N/A"
                status_list.append({
                    "Service": name.replace("_", " ").capitalize(),
                    "Status": "✅ Online" if details.get("status") == "healthy" else "⚠️ Issues",
                    "Latency": latency
                })
            st.table(pd.DataFrame(status_list))
    else:
        st.error("🔴 Backend API is currently unreachable. Please ensure the server is running.")

    # Section 6 — Microphone Test
    st.divider()
    st.markdown(f"### 🎙️ {lang_service.translate_from_english('Test Microphone', language)}")
    if st.button(f"🎤 {lang_service.translate_from_english('Record 5s Sample', language)}", use_container_width=True):
        with st.spinner("Listening..."):
            result = speech_service.record_from_microphone(duration=5)
            if result["success"]:
                st.success(f"✅ {lang_service.translate_from_english('Microphone working. Heard:', language)} {result['text']}")
            else:
                st.error(f"❌ {lang_service.translate_from_english('Microphone issue:', language)} {result['error']}")

    st.markdown('</div>', unsafe_allow_html=True)
