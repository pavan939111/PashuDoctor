import streamlit as st
import os
from uuid import uuid4
from utils.api import api_post, api_get
from components.home import show_home_page
from components.chat import show_chat_page
from components.history import show_history_page
from components.about import show_about_page
from services.language_service import LanguageService
import glob

# 1. Page config (Must be first Streamlit call)
st.set_page_config(
    page_title="PashuDoctor — AI Livestock Health Assistant",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS injection with Premium Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #F5F7F5 0%, #E8F5E9 100%);
    }

    /* Premium Glassmorphism Cards */
    .pd-card {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    .pd-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
    }

    .pd-header {
        color: #1B5E20;
        font-weight: 700;
        font-size: 2.2rem;
        letter-spacing: -0.5px;
        margin-bottom: 1rem;
    }

    /* Custom Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #2E7D32 0%, #43A047 100%);
        color: white;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        border: none;
        font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        width: 100%;
        box-shadow: 0 4px 14px 0 rgba(46, 125, 50, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1B5E20 0%, #2E7D32 100%);
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(46, 125, 50, 0.3);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .main-container {
        animation: fadeIn 0.6s ease-out;
        max-width: 1000px;
        margin: 0 auto;
    }

    /* Status Badges */
    .pd-badge {
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# Page rendering functions (placeholders moved to components)
# show_about_page is imported from components.about

def main():
    # 3. Session state initialization
    if "case_id" not in st.session_state:
        st.session_state.case_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "current_diagnosis" not in st.session_state:
        st.session_state.current_diagnosis = None
    if "answered_questions" not in st.session_state:
        st.session_state.answered_questions = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid4())
    if "current_confidence" not in st.session_state:
        st.session_state.current_confidence = None
    if "image_uploaded" not in st.session_state:
        st.session_state.image_uploaded = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "English"
    if "auto_speak" not in st.session_state:
        st.session_state.auto_speak = False
    
    # 3.1 Singleton Service Initialization
    if "lang_service" not in st.session_state:
        st.session_state.lang_service = LanguageService()
    if "speech_service" not in st.session_state:
        st.session_state.speech_service = SpeechService()

    lang_service = st.session_state.lang_service
    speech_service = st.session_state.speech_service
    language = st.session_state.selected_language
    ui = lang_service.get_ui_strings(language)

    # 3.2 Sidebar Alerts Logic
    active_alerts = []
    if st.session_state.get("user_state") and st.session_state.user_state != "Other":
        alert_res = api_get(f"/alerts/?state={st.session_state.user_state}")
        if alert_res.get("success"):
            active_alerts = alert_res.get("alerts", [])

    # 3.3 Connectivity Logic
    online = is_online()
    conn_status = "Connected" if online else "Offline Mode — Limited features"
    conn_color = "#4CAF50" if online else "#FF9800"

    # 4. Temp file cleanup (one-time on startup)
    if "temp_cleaned" not in st.session_state:
        os.makedirs("temp", exist_ok=True)
        for f in glob.glob("temp/tts_*.mp3") + glob.glob("temp/chat_tts_*.mp3"):
            try: os.remove(f)
            except: pass
        st.session_state.temp_cleaned = True

    # 5. Navigation sidebar
    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="color: #2E7D32; font-size: 2.2rem; margin-bottom: 0;">🐄 PashuDoctor</h1>
                <p style="color: #666; font-size: 0.9rem;">Your AI Livestock Expert</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Connectivity Indicator
        st.sidebar.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; padding: 5px; background: #f0f2f6; border-radius: 20px;">
                <div style="width: 10px; height: 10px; background-color: {conn_color}; border-radius: 50%; margin-right: 10px;"></div>
                <span style="font-size: 0.8rem; font-weight: 600; color: #444;">{conn_status}</span>
            </div>
        """, unsafe_allow_html=True)

        # Display Active Alerts
        if active_alerts:
            st.warning(f"⚠️ **ACTIVE ALERTS in {st.session_state.user_state}**")
            for alert in active_alerts:
                st.markdown(f"• **{alert['disease']}** in {alert['district']}")
            st.markdown("---")
        
        st.markdown(f"### 🛠 {ui.get('navigation', 'Navigation')}")
        if st.button(f"🏠 {ui.get('new_analysis', 'Home / New Analysis')}"):
            st.session_state.page = "home"
            st.rerun()
        if st.button(f"💬 {ui.get('chat_with_doctor', 'Chat with Doctor')}"):
            st.session_state.page = "chat"
            st.rerun()
        if st.button(f"📋 {ui.get('my_cases', 'My Cases History')}"):
            st.session_state.page = "history"
            st.rerun()
        if st.button(f"ℹ️ {ui.get('about', 'About PashuDoctor')}"):
            st.session_state.page = "about"
            st.rerun()
            
        st.markdown("---")
        st.markdown(f"**🌐 Language / भाषा**")
        lang_options = list(lang_service.SUPPORTED_LANGUAGES.keys())
        current_idx = lang_options.index(st.session_state.selected_language)
        
        new_lang = st.selectbox(
            "Language",
            lang_options,
            index=current_idx,
            label_visibility="collapsed",
            key="sidebar_lang_switcher"
        )
        if new_lang != st.session_state.selected_language:
            st.session_state.selected_language = new_lang
            st.rerun()

        st.session_state.auto_speak = st.toggle(
            "🔊 Auto-read responses",
            value=st.session_state.auto_speak
        )

        st.markdown("---")
        st.markdown("### 🔑 Session Details")
        st.info(f"**User ID:**\n`{st.session_state.user_id[:16]}...`")
        if st.session_state.case_id:
            st.success(f"**Active Case:**\n`{st.session_state.case_id[:16]}...`")
        else:
            st.warning("No active analysis")
            
        st.markdown("---")
        st.caption("v1.0.0 | Made for Indian Farmers")

    # 6. Route to page based on st.session_state.page
    if st.session_state.page == "home":
        show_home_page()
    elif st.session_state.page == "chat":
        show_chat_page()
    elif st.session_state.page == "history":
        show_history_page()
    elif st.session_state.page == "about":
        show_about_page()

if __name__ == "__main__":
    main()
