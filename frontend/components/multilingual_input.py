import streamlit as st
import os
import uuid
from uuid import uuid4
from services.language_service import LanguageService
from services.speech_service import SpeechService

# Initialize services
language_service = LanguageService()
speech_service = SpeechService()

def render_language_selector() -> str:
    """
    Renders a language selector dropdown and saves to session state.
    """
    st.markdown("**Select your language / अपनी भाषा चुनें**")
    
    options = list(language_service.SUPPORTED_LANGUAGES.keys())
    
    # Get default index
    current_lang = st.session_state.get("selected_language", "English")
    default_idx = options.index(current_lang) if current_lang in options else 0
    
    selected = st.selectbox(
        "Language Selector",
        options,
        index=default_idx,
        label_visibility="collapsed",
        format_func=lambda x: f"{language_service.SUPPORTED_LANGUAGES[x]['flag']} {x}"
    )
    
    st.session_state.selected_language = selected
    return selected

def render_speech_text_input(
    label: str,
    key: str,
    language: str,
    height: int = 120,
    placeholder: str = ""
) -> str:
    """
    Renders a combined text area and voice input button.
    """
    # Manage session state for the text
    state_key = f"{key}_text"
    if state_key not in st.session_state:
        st.session_state[state_key] = ""

    col_text, col_mic = st.columns([4, 1])

    with col_text:
        text_value = st.text_area(
            label,
            value=st.session_state[state_key],
            height=height,
            placeholder=placeholder,
            key=f"{key}_textarea"
        )
        # Update session state if user types
        st.session_state[state_key] = text_value

    with col_mic:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Using the streamlit-mic-recorder component as requested
        # Note: streamlit_record returns a dict or None
        result = speech_service.streamlit_record(language)

        if result:
            if result.get("success"):
                # Append transcribed text to existing text
                current_text = st.session_state[state_key]
                new_text = result["original_text"]
                translated = result["translated_text"]
                
                # We use the translated text for the main input if not English
                final_append = translated if language != "English" else new_text
                
                st.session_state[state_key] = (current_text + " " + final_append).strip()
                
                st.success(f"Heard: {new_text}")
                if language != "English":
                    st.info(f"Translated: {translated}")
                
                st.rerun()
            else:
                error = result.get("error")
                if error == "no_speech_detected":
                    st.warning("No speech detected. Try again.")
                elif error == "no_microphone":
                    st.error("No microphone found.")
                else:
                    st.error(f"Error: {error}")

    # Below input show character count and language tag
    st.caption(f"{len(text_value)}/1000 chars | [{language}]")

    return text_value

def render_translated_response(
    diagnosis: dict,
    target_language: str,
    speak: bool = True
) -> None:
    """
    Renders an English response with an optional translation, evidence, and TTS.
    """
    if not diagnosis:
        return

    english_response = diagnosis.get("formatted_response", "")
    if not english_response:
        return

    if target_language == "English":
        st.markdown(english_response)
        return

    with st.spinner("Translating response..."):
        translated = language_service.translate_from_english(
            english_response, target_language
        )

    # Show both versions in tabs
    tab1, tab2 = st.tabs([
        f"{language_service.SUPPORTED_LANGUAGES[target_language]['flag']} {target_language}",
        "[EN] English"
    ])
    
    with tab1:
        st.markdown(translated)
        
        # Evidence Section
        st.divider()
        st.markdown(f"### 🔍 {language_service.translate_from_english('Diagnosis Evidence', target_language)}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**📍 {language_service.translate_from_english('Similar Cases Found', target_language)}:**")
            st.write(f"{diagnosis.get('similar_cases_count', 0)} {diagnosis.get('similar_cases_type', 'cases')}")
            
            st.write(f"**✅ {language_service.translate_from_english('Matched Symptoms', target_language)}:**")
            st.write(", ".join(diagnosis.get("matching_symptoms", [])))

        with col2:
            st.write(f"**📊 {language_service.translate_from_english('Confidence Breakdown', target_language)}:**")
            
            img_conf = diagnosis.get('image_confidence', 0.0)
            st.caption(f"Image Similarity: {int(img_conf*100)}%")
            st.progress(img_conf)
            
            sym_conf = diagnosis.get('symptom_confidence', 0.0)
            st.caption(f"Symptom Match: {int(sym_conf*100)}%")
            st.progress(sym_conf)
            
            knw_conf = diagnosis.get('knowledge_confidence', 0.0)
            st.caption(f"Knowledge Match: {int(knw_conf*100)}%")
            st.progress(knw_conf)

        if diagnosis.get("differential_reasoning"):
            st.info(f"**⚖️ {language_service.translate_from_english('Expert Reasoning', target_language)}:**\n{diagnosis.get('differential_reasoning')}")

        if speak:
            if st.button("🔊 Read aloud", key=f"tts_{uuid.uuid4()}"):
                with st.spinner("Generating audio..."):
                    temp_dir = "temp"
                    os.makedirs(temp_dir, exist_ok=True)
                    audio_path = os.path.join(temp_dir, f"tts_{uuid4()}.mp3")
                    
                    success = language_service.text_to_speech(
                        translated, target_language, audio_path
                    )
                    
                    if success:
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    else:
                        st.error("Could not generate audio.")

    with tab2:
        st.markdown(english_response)
        st.divider()
        st.markdown("### 🔍 Diagnosis Evidence (English)")
        st.write(f"**Similar cases found:** {diagnosis.get('similar_cases_count', 0)} {diagnosis.get('similar_cases_type', 'cases')}")
        st.write(f"**Matched symptoms:** {', '.join(diagnosis.get('matching_symptoms', []))}")
        if diagnosis.get("differential_reasoning"):
            st.info(f"**Reasoning:** {diagnosis.get('differential_reasoning')}")

def render_multilingual_symptom_checklist(
    language: str
) -> list:
    """
    Renders a checklist of symptoms in the target language and returns English keys.
    """
    common_symptoms = [
        "Swollen udder", "Clots in milk", "Reduced milk yield", "Fever", 
        "Skin nodules/lumps", "Mouth blisters", "Foot lesions", "Drooling",
        "Lameness", "Nasal discharge", "Difficulty breathing", "Sudden death"
    ]
    
    st.write(f"**Check symptoms ({language}):**")
    
    # Translate symptoms to target language
    translated_symptoms = []
    if language == "English":
        translated_symptoms = common_symptoms
    else:
        for s in common_symptoms:
            translated_symptoms.append(language_service.translate_from_english(s, language))
    
    # Create mapping
    symptom_map = dict(zip(translated_symptoms, common_symptoms))
    
    # Render checkbox multi-select
    selected_translated = []
    cols = st.columns(2)
    for i, s_trans in enumerate(translated_symptoms):
        col = cols[i % 2]
        if col.checkbox(s_trans, key=f"symptom_{i}_{language}"):
            selected_translated.append(s_trans)
            
    # Return selected symptoms in English
    return [symptom_map[s] for s in selected_translated]
