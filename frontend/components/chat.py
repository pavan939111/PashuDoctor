import streamlit as st
from utils.api import api_post
import os
import uuid
from components.multilingual_input import (
    render_speech_text_input,
    render_translated_response
)
from services.language_service import LanguageService
from services.speech_service import SpeechService

def show_chat_page():
    lang_service = st.session_state.lang_service
    speech_service = st.session_state.speech_service
    
    language = st.session_state.get("selected_language", "English")
    ui = lang_service.get_ui_strings(language)
    # 1. Header
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.title("💬 Chat with PashuDoctor")
    
    if not st.session_state.get("case_id"):
        st.warning("No active case. Please start a new analysis to enable chat.")
        if st.button("Start New Analysis"):
            st.session_state.page = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Layout for right-side panel
    main_col, side_col = st.columns([2, 1], gap="medium")

    with main_col:
        # 2. Case context banner
        diagnosis = st.session_state.get("current_diagnosis")
        confidence = st.session_state.get("current_confidence")
        animal = st.session_state.get("animal_result", {}).get("animal", "Unknown")
        
        diag_name = diagnosis['primary_diagnosis'] if diagnosis else 'Diagnosing...'
        conf_pct = confidence['percentage'] if confidence else 0
        
        st.markdown(f"""
            <div style="background-color: #E8F5E9; padding: 1rem; border-radius: 8px; border-left: 5px solid #2E7D32; margin-bottom: 1rem;">
                <b>🐄 Animal:</b> {animal.capitalize()} | 
                <b>🩺 Status:</b> {diag_name} | 
                <b>📊 Confidence:</b> {conf_pct}%
            </div>
        """, unsafe_allow_html=True)

        # 3. Chat display area
        # Pre-populate history if it's the first message and we have a diagnosis
        if not st.session_state.chat_history and diagnosis:
            assistant_en = f"I've analyzed the symptoms. My primary diagnosis is **{diagnosis['primary_diagnosis']}**. {diagnosis['farmer_advice']}"
            assistant_translated = assistant_en
            if language != "English":
                assistant_translated = lang_service.translate_from_english(assistant_en, language)

            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": assistant_translated,
                "content_en": assistant_en,
                "language": language
            })

        for msg in st.session_state.chat_history:
            role = msg["role"]
            content = msg["content"]
            content_en = msg.get("content_en", "")
            
            with st.chat_message(role, avatar="🐄" if role == "assistant" else None):
                st.markdown(content)
                if language != "English" and content_en and content_en != content:
                    with st.expander("View in English"):
                        st.markdown(content_en)

        # 4. Follow-up questions display (Translated)
        pending_questions = st.session_state.get("follow_up_questions", [])
        if pending_questions:
            with st.expander(f"❓ {ui['follow_up_questions']}", expanded=True):
                q_answers = []
                for i, q in enumerate(pending_questions):
                    # Translate question
                    q_trans = lang_service.translate_from_english(q, language)
                    
                    ans = render_speech_text_input(
                        label=f"{i+1}. {q_trans}",
                        key=f"chat_fq_{i}",
                        language=language,
                        height=80
                    )
                    
                    if ans:
                        # Translate answer back to English
                        ans_en = lang_service.translate_to_english(ans, language)["translated"]
                        q_answers.append({"question": q, "answer": ans_en})
                
                if st.button(ui["submit_answers"], type="primary", use_container_width=True):
                    if q_answers:
                        with st.spinner("Updating analysis..."):
                            payload = {
                                "case_id": st.session_state.case_id,
                                "user_id": st.session_state.user_id,
                                "question_answers": q_answers,
                                "symptom_text": "" # Server handles enrichment
                            }
                            res = api_post("/chat/answer-questions", json_payload=payload)
                            if res.get("success"):
                                # Record in chat history (Bilingual)
                                history_en = "\n".join([f"Q: {qa['question']}\nA: {qa['answer']}" for qa in q_answers])
                                history_trans = history_en
                                if language != "English":
                                    history_trans = lang_service.translate_from_english(history_en, language)

                                st.session_state.chat_history.append({
                                    "role": "user", 
                                    "content": history_trans,
                                    "content_en": history_en,
                                    "language": language
                                })
                                
                                st.session_state.current_diagnosis = res.get("diagnosis")
                                st.session_state.current_confidence = res.get("confidence")
                                st.session_state.follow_up_questions = res.get("follow_up_questions", [])
                                
                                if res.get("diagnosis"):
                                    assistant_en = f"Thank you. Based on that, I've updated the diagnosis: **{res['diagnosis']['primary_diagnosis']}**."
                                    assistant_trans = assistant_en
                                    if language != "English":
                                        assistant_trans = lang_service.translate_from_english(assistant_en, language)
                                        
                                    st.session_state.chat_history.append({
                                        "role": "assistant", 
                                        "content": assistant_trans,
                                        "content_en": assistant_en,
                                        "language": language
                                    })
                                st.rerun()

        # 5. Chat input (Multilingual Speech + Text)
        with st.container():
            st.divider()
            prompt = render_speech_text_input(
                label=ui["chat_with_doctor"],
                key="chat_input_main",
                language=language,
                height=80,
                placeholder=ui.get("chat_placeholder", "Type or speak your message...")
            )
            
            if st.button(ui.get("send", "Send Message"), type="primary", use_container_width=True) and prompt:
                # 1. Translate user message to English
                with st.spinner("Translating..."):
                    en_message = lang_service.translate_to_english(prompt, language)["translated"]

                # 2. Add to history
                st.session_state.chat_history.append({
                    "role": "user", 
                    "content": prompt,
                    "content_en": en_message,
                    "language": language
                })
                
                # 3. Generate assistant response
                with st.chat_message("assistant", avatar="🐄"):
                    with st.spinner(ui.get("processing", "PashuDoctor is thinking...")):
                        payload = {
                            "case_id": st.session_state.case_id,
                            "user_id": st.session_state.user_id,
                            "message": en_message,
                            "answered_questions": []
                        }
                        response = api_post("/chat/message", json_payload=payload)
                        
                        if response.get("success"):
                            assistant_en = response["response"]
                            assistant_trans = lang_service.translate_from_english(assistant_en, language)
                            
                            st.markdown(assistant_trans)
                            
                            # Save to history
                            st.session_state.chat_history.append({
                                "role": "assistant", 
                                "content": assistant_trans,
                                "content_en": assistant_en,
                                "language": language
                            })
                            
                            # Handle auto-speak
                            if st.session_state.get("auto_speak"):
                                with st.spinner("🔊..."):
                                    audio_path = f"temp/chat_tts_{uuid.uuid4()}.mp3"
                                    os.makedirs("temp", exist_ok=True)
                                    if lang_service.text_to_speech(assistant_trans, language, audio_path):
                                        with open(audio_path, "rb") as f:
                                            st.audio(f.read(), format="audio/mp3", autoplay=True)
                            
                            if response.get("diagnosis_updated"):
                                st.toast("✅ Diagnosis updated!")
                        else:
                            st.error(response.get("error", "I'm having trouble connecting."))
                st.rerun()

    with side_col:
        # 6. Sidebar panel (right side)
        if diagnosis:
            st.markdown('<div class="pd-card">', unsafe_allow_html=True)
            st.markdown("### Current Diagnosis")
            st.markdown(f"**{diagnosis['primary_diagnosis']}**")
            
            score = confidence["percentage"] if confidence else 0
            st.progress(score / 100)
            st.caption(f"Confidence: {score}%")
            
            urgency = diagnosis.get("vet_urgency", "High")
            color = "#d32f2f" if urgency.lower() == "high" else "#f57c00" if urgency.lower() == "moderate" else "#2e7d32"
            st.markdown(f"""
                <div style="background-color: {color}; color: white; padding: 5px 10px; border-radius: 5px; text-align: center; font-weight: bold;">
                    {urgency.upper()} PRIORITY
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.session_state.auto_speak = st.toggle("🔊 Auto-read responses", value=st.session_state.get("auto_speak", False))
            
            with st.expander("📋 View Full Details", expanded=False):
                st.markdown(f"**Advice:**\n{diagnosis['farmer_advice']}")
                st.markdown("**Precautions:**")
                for p in diagnosis.get('immediate_precautions', []):
                    st.markdown(f"- {p}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Analysis in progress...")

    # 7. Bottom action bar
    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🔄 New Analysis", use_container_width=True):
            # Clear critical session state
            st.session_state.case_id = None
            st.session_state.chat_history = []
            st.session_state.current_diagnosis = None
            st.session_state.current_confidence = None
            st.session_state.page = "home"
            st.rerun()
    with b2:
        if st.button("📋 View All History", use_container_width=True):
            st.session_state.page = "history"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
