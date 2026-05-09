import streamlit as st
import time

def render_confidence_badge(score: float):
    """Renders a colored confidence indicator pill"""
    pct = int(score * 100)
    if score >= 0.90:
        color = "#2E7D32" # Dark Green
        label = "HIGH CONFIDENCE"
        icon = "🟢"
    elif score >= 0.75:
        color = "#1976D2" # Blue
        label = "LIKELY"
        icon = "🔵"
    elif score >= 0.50:
        color = "#F57C00" # Orange
        label = "POSSIBLE"
        icon = "🟡"
    else:
        color = "#D32F2F" # Red
        label = "LOW"
        icon = "🔴"
    
    st.markdown(f"""
        <span style="background-color: {color}; color: white; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.85rem; letter-spacing: 0.5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {icon} {label} ({pct}%)
        </span>
    """, unsafe_allow_html=True)

def render_disease_card(diagnosis: dict):
    """Renders a comprehensive, formatted diagnosis card for medical results"""
    st.markdown('<div class="pd-card">', unsafe_allow_html=True)
    
    # Header
    st.markdown(f"<h2 style='color: #2E7D32; margin-bottom: 5px;'>{diagnosis.get('primary_diagnosis', 'Diagnosing...')}</h2>", unsafe_allow_html=True)
    
    # Badges Row
    severity = diagnosis.get("severity", "unknown").lower()
    sev_colors = {
        "mild": "#4CAF50",
        "moderate": "#FF9800",
        "severe": "#F44336",
        "emergency": "#B71C1C"
    }
    sev_color = sev_colors.get(severity, "#9E9E9E")
    
    urgency = diagnosis.get("vet_urgency", "Monitor")
    
    st.markdown(f"""
        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
            <span style="background-color: {sev_color}; color: white; padding: 2px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">{severity.upper()} SEVERITY</span>
            <span style="background-color: #F5F7F5; border: 1px solid #2E7D32; color: #2E7D32; padding: 2px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">🚨 URGENCY: {urgency.upper()}</span>
        </div>
    """, unsafe_allow_html=True)

    # Content Sections
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 🔍 Matching Symptoms")
        for sym in diagnosis.get("matching_symptoms", []):
            st.markdown(f"- {sym}")
            
    with c2:
        st.markdown("#### 🛡️ Immediate Precautions")
        for i, prec in enumerate(diagnosis.get("immediate_precautions", []), 1):
            st.markdown(f"{i}. {prec}")
            
    st.divider()
    
    st.markdown("#### ⚠️ Critical Warning Signs")
    for ws in diagnosis.get("urgent_warning_signs", []):
        st.markdown(f'<li style="color: #B71C1C; font-weight: 500;">{ws}</li>', unsafe_allow_html=True)
        
    with st.expander("🩺 Herd-Level Prevention Advice"):
        for hp in diagnosis.get("herd_prevention", []):
            st.markdown(f"- {hp}")
            
    # Vet Disclaimer
    st.markdown("""
        <div style="background-color: #FFF3E0; border-left: 5px solid #FF9800; padding: 15px; border-radius: 4px; margin-top: 20px; font-size: 0.9rem;">
            <b style="color: #E65100;">⚖️ VETERINARY DISCLAIMER:</b><br>
            This AI-generated analysis is for informational purposes for Indian farmers and is NOT a substitute for professional 
            veterinary medical advice. <b>Please consult a licensed veterinarian immediately before administering any treatment.</b>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_animal_badge(animal: str, confidence: float):
    """Shows detected animal with icon and confidence percentage"""
    icons = {
        "cow": "🐄",
        "buffalo": "🦬",
        "goat": "🐐",
        "sheep": "🐑",
        "unknown": "❓"
    }
    icon = icons.get(animal.lower(), "❓")
    pct = int(confidence * 100)
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; background-color: white; padding: 8px 16px; border-radius: 50px; border: 2px solid #2E7D32; width: fit-content; margin-bottom: 10px;">
            <span style="font-size: 1.4rem; margin-right: 12px;">{icon}</span>
            <span style="font-weight: 600; color: #2E7D32;">{animal.capitalize()} Detected ({pct}%)</span>
        </div>
    """, unsafe_allow_html=True)

def render_chat_message(role: str, content: str):
    """Custom styled chat bubbles for the doctor-farmer conversation"""
    if role == "user":
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
                <div style="background-color: #E3F2FD; color: #1565C0; padding: 12px 18px; border-radius: 18px 18px 2px 18px; max-width: 85%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    {content}
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 1rem;">
                <div style="background-color: #E8F5E9; color: #1B5E20; padding: 12px 18px; border-radius: 18px 18px 18px 2px; max-width: 85%; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 4px solid #2E7D32;">
                    <div style="display: flex; align-items: center; margin-bottom: 6px; border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <span style="font-size: 1.2rem; margin-right: 8px;">🐄</span>
                        <b style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;">PashuDoctor AI</b>
                    </div>
                    <div style="font-size: 1rem; line-height: 1.5;">{content}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

def render_progress_steps(current_step: int):
    """Visual pipeline indicator for the diagnostic process"""
    steps = ["Upload", "Detect", "Retrieve", "Analyze", "Ready"]
    cols = st.columns(len(steps))
    for i, step in enumerate(steps, 1):
        with cols[i-1]:
            if i < current_step:
                st.markdown(f"<p style='text-align: center; color: #2E7D32; font-weight: bold; margin-bottom: 0;'>{step}</p><p style='text-align: center; margin-top: -5px;'>✅</p>", unsafe_allow_html=True)
            elif i == current_step:
                st.markdown(f"<p style='text-align: center; color: #1976D2; font-weight: bold; margin-bottom: 0;'>{step}</p><p style='text-align: center; margin-top: -5px;'>🔄</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='text-align: center; color: #9E9E9E; margin-bottom: 0;'>{step}</p><p style='text-align: center; margin-top: -5px;'>⏳</p>", unsafe_allow_html=True)

def render_symptom_checklist(selected_symptoms: list) -> list:
    """Renders an interactive symptom checklist and returns the current selection"""
    st.markdown("### 📋 Symptom Checklist")
    new_selection = []
    
    groups = {
        "Common": ["Fever", "Loss of appetite", "Lethargy"],
        "Physical": ["Lumps", "Wounds", "Swelling", "Skin lesions"],
        "Output": ["Reduced milk", "Abnormal milk", "Diarrhoea"]
    }
    
    for group, symptoms in groups.items():
        with st.expander(f"{group} Symptoms", expanded=True):
            for sym in symptoms:
                if st.checkbox(sym, value=(sym in selected_symptoms), key=f"check_{sym}"):
                    new_selection.append(sym)
    return new_selection

from utils.report_utils import generate_pdf_report

def render_pdf_button(case_data: dict, key_suffix: str = ""):
    """Renders a button to generate and download a PDF report"""
    if not case_data:
        return
        
    try:
        pdf_bytes = generate_pdf_report(case_data)
        st.download_button(
            label="📄 Download Medical Report (PDF)",
            data=pdf_bytes,
            file_name=f"PashuDoctor_Report_{case_data.get('case_id', 'case')[:8]}.pdf",
            mime="application/pdf",
            key=f"pdf_btn_{key_suffix}"
        )
    except Exception as e:
        st.error(f"Error generating PDF: {e}")

def show_error_state(error_msg: str):
    """Full-page styled error state with actions"""
    st.markdown(f"""
        <div style="background-color: #FFEBEE; border: 1px solid #FFCDD2; padding: 40px; border-radius: 12px; text-align: center; margin: 20px 0; box-shadow: 0 4px 20px rgba(183, 28, 28, 0.1);">
            <div style="font-size: 4rem; margin-bottom: 10px;">🛑</div>
            <h2 style="color: #B71C1C;">Connection Error</h2>
            <p style="color: #D32F2F; font-size: 1.1rem; font-weight: 500;">{error_msg}</p>
            <p style="color: #666; margin-top: 20px;">Please check if the PashuDoctor Backend is running and your internet is active.</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Reload Application", use_container_width=True):
        st.rerun()

def show_loading_state(message: str):
    """Animated loading state that cycles through background tasks"""
    placeholder = st.empty()
    tasks = [
        ("🔍", "Analyzing image details..."),
        ("📚", "Searching medical database..."),
        ("🧠", "Consulting AI knowledge base..."),
        ("📝", "Generating diagnosis report...")
    ]
    
    # We cycle once to show progress then leave it on a generic state
    for icon, task in tasks:
        with placeholder.container():
            st.markdown(f"""
                <div style="text-align: center; padding: 60px 20px;">
                    <div style="font-size: 4rem; animation: pulse 2s infinite;">{icon}</div>
                    <h3 style="color: #2E7D32; margin-top: 20px;">{task}</h3>
                    <p style="color: #666; font-style: italic;">{message}</p>
                </div>
                <style>
                    @keyframes pulse {{
                        0% {{ transform: scale(1); opacity: 1; }}
                        50% {{ transform: scale(1.1); opacity: 0.7; }}
                        100% {{ transform: scale(1); opacity: 1; }}
                    }}
                </style>
            """, unsafe_allow_html=True)
        time.sleep(0.8)
