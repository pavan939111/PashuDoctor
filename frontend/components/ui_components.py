import streamlit as st
import time
from datetime import datetime
import urllib.parse

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

def render_severity_badge(severity: str):
    """Renders a prominent severity badge with specific instructions"""
    sev = severity.lower()
    if sev == "mild":
        color = "#2E7D32" # Green
        label = "🟢 MILD — Monitor at home"
    elif sev == "moderate":
        color = "#F57C00" # Orange
        label = "🟡 MODERATE — Visit vet within 48 hours"
    elif sev == "severe":
        color = "#D32F2F" # Red
        label = "🔴 SEVERE — Visit vet today"
    elif sev == "emergency":
        color = "#B71C1C" # Dark Red
        label = "🚨 EMERGENCY — Call vet immediately"
    else:
        color = "#9E9E9E"
        label = f"Status: {severity.upper()}"
        
    st.markdown(f"""
        <div style="background-color: {color}; color: white; padding: 12px 20px; border-radius: 10px; font-weight: 800; font-size: 1.1rem; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
            {label}
        </div>
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

        # WhatsApp Sharing & Summary
        diag = case_data.get("diagnosis", {})
        precautions = diag.get("immediate_precautions", [])
        precautions_text = ", ".join(precautions[:3]) if precautions else "No specific precautions"
        
        pdf_text_summary = (
            f"📍 PashuDoctor Report\n"
            f"🆔 Case ID: {case_data.get('case_id', 'case')[:8]}\n"
            f"🐄 Animal: {case_data.get('animal_type', 'unknown')}\n"
            f"🩺 Diagnosis: {diag.get('primary_diagnosis', 'unknown')}\n"
            f"📊 Confidence: {int(case_data.get('confidence_score', 0)*100)}%\n"
            f"🔴 Severity: {diag.get('severity', 'unknown').upper()}\n"
            f"🏥 Vet Urgency: {diag.get('vet_urgency', 'Monitor')}\n"
            f"🛡️ Precautions: {precautions_text}\n"
            f"Generated by PashuDoctor AI"
        )
        
        encoded = urllib.parse.quote(pdf_text_summary)
        wa_url = f"https://wa.me/?text={encoded}"

        share_col1, share_col2 = st.columns(2)
        with share_col1:
            st.link_button(
                "🟢 Share on WhatsApp",
                wa_url,
                use_container_width=True,
                help="Send report summary to your vet via WhatsApp"
            )
        with share_col2:
            with st.popover("📋 Copy Text Summary", use_container_width=True):
                st.code(pdf_text_summary, language=None)
                st.info("👆 Use the copy button in the top right of the text box above.")
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
def render_case_timeline(timeline_data: list):
    """Renders a vertical timeline of diagnostic and follow-up events"""
    if not timeline_data:
        st.info("No timeline data available.")
        return

    st.markdown("### 📅 Case Progress Timeline")
    
    # Custom CSS for vertical timeline
    st.markdown("""
        <style>
        .timeline-container {
            position: relative;
            padding-left: 30px;
            margin-bottom: 20px;
        }
        .timeline-container::before {
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #E0E0E0;
        }
        .timeline-item {
            position: relative;
            margin-bottom: 20px;
        }
        .timeline-dot {
            position: absolute;
            left: -25px;
            top: 5px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #2E7D32;
            border: 2px solid white;
            box-shadow: 0 0 0 2px #2E7D32;
        }
        .timeline-content {
            background: white;
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid #F0F0F0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .timeline-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        .timeline-day {
            font-weight: 700;
            color: #2E7D32;
            font-size: 0.8rem;
            text-transform: uppercase;
        }
        .timeline-time {
            color: #9E9E9E;
            font-size: 0.75rem;
        }
        .timeline-event {
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 3px;
        }
        .timeline-note {
            font-size: 0.85rem;
            color: #616161;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    for item in timeline_data:
        day = item.get("day", 1)
        event = item.get("event", "Event")
        note = item.get("note", "")
        ts = item.get("timestamp", "")
        if ts:
            ts_dt = datetime.fromisoformat(ts)
            ts_str = ts_dt.strftime("%b %d, %H:%M")
        else:
            ts_str = ""
            
        st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <span class="timeline-day">Day {day}</span>
                        <span class="timeline-time">{ts_str}</span>
                    </div>
                    <div class="timeline-event">{event}</div>
                    <div class="timeline-note">{note}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_emergency_alert():
    """Full-screen styled emergency alert with helplines"""
    st.markdown("""
        <div style="background-color: #B71C1C; color: white; padding: 40px; border-radius: 15px; text-align: center; margin: 20px 0; border: 5px solid #FF5252; animation: blinker 1.5s linear infinite;">
            <div style="font-size: 5rem; margin-bottom: 10px;">🚨</div>
            <h1 style="color: white; font-size: 2.5rem; margin-bottom: 10px;">EMERGENCY DETECTED</h1>
            <p style="font-size: 1.3rem; font-weight: 500; margin-bottom: 25px;">Please take immediate action to save your animal.</p>
            
            <div style="background-color: rgba(255,255,255,0.15); padding: 25px; border-radius: 10px; margin-bottom: 20px;">
                <h3 style="color: white; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 10px;">VETERINARY HELPLINES</h3>
                <div style="font-size: 2.2rem; font-weight: 900; margin-bottom: 10px;">📞 1962</div>
                <p style="font-size: 0.9rem; opacity: 0.9;">National Animal Disease Reporting & Referral Service</p>
            </div>
            
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 15px; font-size: 0.85rem;">
                <div style="background: rgba(0,0,0,0.2); padding: 8px 15px; border-radius: 5px;">Delhi: 1800-11-2354</div>
                <div style="background: rgba(0,0,0,0.2); padding: 8px 15px; border-radius: 5px;">UP: 1800-180-5141</div>
                <div style="background: rgba(0,0,0,0.2); padding: 8px 15px; border-radius: 5px;">Tamil Nadu: 1800-425-5878</div>
                <div style="background: rgba(0,0,0,0.2); padding: 8px 15px; border-radius: 5px;">Karnataka: 1800-425-0012</div>
            </div>
        </div>
        <style>
            @keyframes blinker {
                50% { border-color: transparent; }
            }
        </style>
    """, unsafe_allow_html=True)

def render_herd_alert(alert_data: dict):
    """Renders a pulsing red banner and isolation checklist for contagious diseases"""
    if not alert_data or not alert_data.get("is_contagious"):
        return

    st.markdown("""
        <style>
        .herd-alert-banner {
            background-color: #B71C1C;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            font-weight: 800;
            font-size: 1.2rem;
            margin-bottom: 20px;
            border: 4px solid #FF5252;
            animation: pulse-red 1.5s infinite;
        }
        @keyframes pulse-red {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(183, 28, 28, 0.7); }
            70% { transform: scale(1.02); box-shadow: 0 0 0 15px rgba(183, 28, 28, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(183, 28, 28, 0); }
        }
        .isolation-checklist {
            background-color: #FFEBEE;
            border-left: 5px solid #B71C1C;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 25px;
        }
        .checklist-item {
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            font-weight: 500;
            color: #B71C1C;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f'<div class="herd-alert-banner">🚨 CONTAGIOUS DISEASE — ISOLATE ANIMAL NOW</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="isolation-checklist">
            <h4 style="color: #B71C1C; margin-top: 0;">🚧 ISOLATION PROTOCOL</h4>
            <p style="font-size: 0.95rem; margin-bottom: 15px;">{alert_data.get("alert_message")}</p>
            <div class="checklist-item">✅ Move to separate enclosure (min 50ft away)</div>
            <div class="checklist-item">✅ Disinfect shared water/food areas</div>
            <div class="checklist-item">✅ Check all other animals for symptoms</div>
            <div class="checklist-item">✅ Report to local authority (Call 1962)</div>
            <div class="checklist-item">✅ Do NOT sell or move animals from farm</div>
        </div>
    """, unsafe_allow_html=True)
