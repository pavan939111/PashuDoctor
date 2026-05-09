import streamlit as st
from utils.api import api_post
from datetime import datetime
from components.multilingual_input import (
    render_language_selector,
    render_speech_text_input,
    render_translated_response,
    render_multilingual_symptom_checklist
)
from services.language_service import LanguageService
from services.speech_service import SpeechService

def show_home_page():
    lang_service = st.session_state.lang_service
    speech_service = st.session_state.speech_service

    # 1. Language Selection Bar (First Element)
    language = render_language_selector()
    ui = lang_service.get_ui_strings(language)
    st.session_state.selected_language = language

    # 2. Header section
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    title_text = lang_service.translate_from_english("AI Livestock Health Assistant", language)
    st.title(f"🐄 PashuDoctor - {title_text}")
    
    subtitle_text = lang_service.translate_from_english("PashuDoctor uses AI to help you identify diseases and get care advice for your animals.", language)
    st.markdown(f"*{subtitle_text}*")
    st.divider()

    # 2. Two-column layout: col1 (input), col2 (results)
    col1, col2 = st.columns([1, 1], gap="large")

    # 3. LEFT COLUMN — Input panel
    with col1:
        st.subheader(f"📝 {ui['describe_symptoms']}")
        
        # a. Image upload
        uploaded_file = st.file_uploader(
            ui["upload_photo"],
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear photo of the sick animal"
        )
        
        if uploaded_file:
            st.image(uploaded_file, width=300)
            # Simple quality indicator
            st.markdown('<p style="color: #2E7D32;">✅ Image ready for analysis</p>', unsafe_allow_html=True)

        # b. Animal type selector
        animal_type = st.selectbox(
            "Animal type (optional — auto-detected from image)",
            ["Auto-detect", "Cow", "Buffalo", "Goat", "Sheep"]
        )

        # c. Symptom input (Combined Speech + Text)
        symptom_text = render_speech_text_input(
            label=ui["describe_symptoms"],
            key="symptom_input",
            language=language,
            height=120,
            placeholder=ui.get("describe_symptoms", "Describe what you see...")
        )
        
        # d. Symptom checklist (expandable)
        with st.expander(f"Quick symptom checklist ({language})"):
            checklist_symptoms = render_multilingual_symptom_checklist(language)

        # e. Combine and Translate symptoms to English for backend
        raw_symptoms = symptom_text
        if checklist_symptoms:
            raw_symptoms += " Symptoms: " + ", ".join(checklist_symptoms)
        
        # Translation to English
        with st.spinner("Preparing symptoms..."):
            trans_res = lang_service.translate_to_english(raw_symptoms, language)
            final_symptoms = trans_res["translated"]

        # f. Analyze button
        if st.button(f"🔍 {ui['analyze_button']}", type="primary", use_container_width=True):
            # 4. Analysis pipeline
            if not uploaded_file and len(symptom_text) < 10 and not checklist_symptoms:
                st.error("Please upload an image or describe symptoms (min 10 characters).")
            else:
                with st.spinner("PashuDoctor is analyzing..."):
                    req_animal = None if animal_type == "Auto-detect" else animal_type.lower()
                    
                    if uploaded_file:
                        files = {"image": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        data = {
                            "user_id": st.session_state.user_id,
                            "symptom_text": final_symptoms,
                            "animal_type": req_animal,
                            "language": language.lower()
                        }
                        response = api_post("/analyze/image", data=data, files=files)
                    else:
                        json_payload = {
                            "user_id": st.session_state.user_id,
                            "symptom_text": final_symptoms,
                            "animal_type": req_animal,
                            "language": language.lower()
                        }
                        response = api_post("/analyze/text-only", json_payload=json_payload)

                    if response.get("success"):
                        st.session_state.case_id = response["case_id"]
                        st.session_state.current_diagnosis = response.get("diagnosis")
                        st.session_state.current_confidence = response.get("confidence")
                        st.session_state.animal_result = response.get("animal_detection")
                        st.session_state.follow_up_questions = response.get("follow_up_questions", [])
                        st.session_state.results_visible = True
                        st.rerun()
                    else:
                        st.error(f"Error: {response.get('error', 'Analysis failed')}")

    # 5. RIGHT COLUMN — Results panel
    with col2:
        st.subheader("📋 Analysis Results")
        if not st.session_state.get("results_visible"):
            st.markdown("""
                <div class="pd-card">
                    <p style="color: #666;">Waiting for symptoms input...<br>
                    Please upload an image or type symptoms and click Analyze.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            diagnosis = st.session_state.current_diagnosis
            confidence = st.session_state.current_confidence
            animal_data = st.session_state.animal_result
            
            # a. Confidence meter
            if confidence:
                score = confidence["percentage"]
                st.metric("Confidence Score", f"{score}%")
                st.progress(score / 100)
                st.info(confidence["message"])

            # b. Animal detection result
            if animal_data:
                st.success(f"🐄 Detected: **{animal_data['animal'].capitalize()}** ({animal_data['confidence']*100:.0f}% match)")

            # c. Diagnosis card (Multilingual)
            if diagnosis and confidence.get("show_prediction"):
                st.markdown('<div class="pd-card">', unsafe_allow_html=True)
                
                # Render translated diagnosis response with tabs, evidence breakdown, and TTS
                render_translated_response(
                    diagnosis=diagnosis,
                    target_language=language,
                    speak=True
                )
                
                # Add PDF Download Button
                from components.ui_components import render_pdf_button
                case_data = {
                    "case_id": st.session_state.case_id,
                    "animal_type": st.session_state.animal_result.get("animal", "unknown") if st.session_state.animal_result else "unknown",
                    "symptoms_text": final_symptoms,
                    "diagnosis": diagnosis,
                    "confidence_score": confidence.get("score", 0),
                    "created_at": datetime.now().isoformat()
                }
                render_pdf_button(case_data, key_suffix="home")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # d. Follow-up questions (Translated)
            if confidence and confidence.get("action") == "ask_more":
                st.warning(f"⚠️ {ui['follow_up_questions']}")
                q_answers = []
                for i, question in enumerate(st.session_state.follow_up_questions):
                    # Translate question to user language
                    q_trans = lang_service.translate_from_english(question, language)
                    
                    ans = render_speech_text_input(
                        label=f"{i+1}. {q_trans}",
                        key=f"fq_{i}",
                        language=language,
                        height=80
                    )
                    
                    if ans:
                        # Translate answer back to English
                        ans_en = lang_service.translate_to_english(ans, language)["translated"]
                        q_answers.append({"question": question, "answer": ans_en})
                
                if st.button(ui["submit_answers"], use_container_width=True):
                    with st.spinner("Refining diagnosis..."):
                        payload = {
                            "case_id": st.session_state.case_id,
                            "user_id": st.session_state.user_id,
                            "question_answers": q_answers,
                            "symptom_text": final_symptoms
                        }
                        res = api_post("/chat/answer-questions", json_payload=payload)
                        if res.get("success"):
                            st.session_state.current_diagnosis = res.get("diagnosis")
                            st.session_state.current_confidence = res.get("confidence")
                            st.session_state.follow_up_questions = res.get("follow_up_questions", [])
                            st.rerun()
                        else:
                            st.error(res.get("error"))

            # e. Action buttons row
            st.divider()
            ca, cb, cc = st.columns(3)
            with ca:
                if st.button("💬 Chat", help="Talk to our AI doctor about this case"):
                    st.session_state.page = "chat"
                    st.rerun()
            with cb:
                if st.button("🔄 New", help="Clear results and start fresh"):
                    st.session_state.case_id = None
                    st.session_state.current_diagnosis = None
                    st.session_state.current_confidence = None
                    st.session_state.results_visible = False
                    st.rerun()
            with cc:
                if st.button("📋 History", help="View your past cases"):
                    st.session_state.page = "history"
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
