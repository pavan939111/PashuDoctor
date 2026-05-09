import streamlit as st
from utils.api import api_get, api_post, api_delete
from datetime import datetime
from services.language_service import LanguageService

def show_history_page():
    lang_service = st.session_state.lang_service
    language = st.session_state.get("selected_language", "English")
    ui = lang_service.get_ui_strings(language)
    user_id = st.session_state.user_id
    
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    header_text = lang_service.translate_from_english("My Cases", language)
    st.title(f"📋 {header_text}")
    st.markdown(lang_service.translate_from_english("Your livestock health consultation history", language))
    
    # 2. Stats row
    stats_res = api_get(f"/history/{user_id}/stats")
    if stats_res.get("success") is not False:
        stats = stats_res
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(lang_service.translate_from_english("Total Cases", language), stats.get("total_cases", 0))
        col2.metric(lang_service.translate_from_english("This Month", language), stats.get("cases_this_month", 0))
        
        avg_conf = stats.get("avg_confidence", 0)
        col3.metric(lang_service.translate_from_english("Avg Confidence", language), f"{avg_conf*100:.0f}%")
        col4.metric(lang_service.translate_from_english("Vet Referrals", language), stats.get("vet_referrals", 0))
    else:
        st.warning(lang_service.translate_from_english("Could not load statistics.", language))

    st.divider()

    # 3. Filter row
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        animal_filter = st.selectbox("Animal", ["All", "Cow", "Buffalo", "Goat", "Sheep"])
    with filter_col2:
        disease_filter = st.selectbox("Disease", ["All", "Mastitis", "FMD", "LSD", "BQ", "HS", "PPR"])
    with filter_col3:
        sort_by = st.selectbox("Sort by", ["Newest first", "Oldest first", "Highest confidence", "Lowest confidence"])

    # 4. Load Cases
    history_res = api_get(f"/history/{user_id}?limit=50")
    if history_res.get("success") is False:
        st.error(history_res.get("error", "Failed to load history"))
        return

    cases = history_res.get("cases", [])
    
    if not cases:
        st.info("No cases yet. Start your first analysis!")
        if st.button("🔍 Start New Analysis"):
            st.session_state.page = "home"
            st.rerun()
        return

    # Apply Filtering
    filtered_cases = cases
    if animal_filter != "All":
        filtered_cases = [c for c in filtered_cases if c["animal_type"].lower() == animal_filter.lower()]
    if disease_filter != "All":
        filtered_cases = [c for c in filtered_cases if disease_filter.lower() in c["primary_diagnosis"].lower()]

    # Apply Sorting
    if sort_by == "Newest first":
        filtered_cases.sort(key=lambda x: x["created_at"], reverse=True)
    elif sort_by == "Oldest first":
        filtered_cases.sort(key=lambda x: x["created_at"])
    elif sort_by == "Highest confidence":
        filtered_cases.sort(key=lambda x: x["confidence_score"], reverse=True)
    elif sort_by == "Lowest confidence":
        filtered_cases.sort(key=lambda x: x["confidence_score"])

    # 5. Cases list
    for case in filtered_cases:
        with st.container():
            st.markdown('<div class="pd-card">', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1.5, 2, 1])
            
            with c1:
                st.markdown(f"### 🐄 {case['animal_type'].capitalize()}")
                st.caption(f"📅 {case['created_at'][:10]}")
            
            with c2:
                st.markdown(f"**🩺 {case['primary_diagnosis']}**")
                urgency = case.get("vet_urgency", "monitor").lower()
                
                # Urgency Badge Logic
                colors = {
                    "immediate": "#d32f2f",      # Red
                    "within 24 hours": "#f57c00", # Orange
                    "within a week": "#fbc02d",   # Yellow
                    "monitor": "#2e7d32"         # Green
                }
                color = colors.get(urgency, "#2e7d32")
                st.markdown(f"""
                    <span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold;">
                        {urgency.upper()}
                    </span>
                """, unsafe_allow_html=True)
            
            with c3:
                conf = int(case['confidence_score'] * 100)
                st.metric("Confidence", f"{conf}%")
            
            # Action Buttons Row
            st.markdown("<br>", unsafe_allow_html=True)
            a1, a2, a3 = st.columns(3)
            
            case_id = case["case_id"]
            
            if a1.button("👁️ View Details", key=f"view_{case_id}"):
                st.session_state[f"expand_{case_id}"] = not st.session_state.get(f"expand_{case_id}", False)
            
            if a2.button("💬 Chat", key=f"chat_{case_id}"):
                st.session_state.case_id = case_id
                # Attempt to load state if possible, otherwise chat will load it
                st.session_state.page = "chat"
                st.rerun()
                
            if a3.button("🗑️ Delete", key=f"del_{case_id}"):
                api_delete(f"/history/{user_id}/{case_id}")
                st.rerun()

            # 6. Case Details Expander (Manual Toggle)
            if st.session_state.get(f"expand_{case_id}"):
                with st.status("Loading case details...", expanded=True):
                    detail = api_get(f"/analyze/{case_id}")
                    if detail.get("success") is not False:
                        diag = detail.get("diagnosis", {})
                        
                        col_left, col_right = st.columns(2)
                        with col_left:
                            st.markdown("#### 🔍 Diagnosis Findings")
                            st.write(diag.get("formatted_response", "No details available."))
                            
                            st.markdown("**Symptoms Matched:**")
                            for sym in diag.get("matching_symptoms", []):
                                st.markdown(f"- {sym}")
                        
                        with col_right:
                            st.markdown("#### 🛡️ Precautions")
                            for p in diag.get("immediate_precautions", []):
                                st.info(p)
                            
                            st.markdown("#### 🐄 Herd Prevention")
                            for h in diag.get("herd_prevention", []):
                                st.success(h)
                            
                            # Add PDF Download Button
                            from components.ui_components import render_pdf_button
                            case_detail_data = {
                                "case_id": case_id,
                                "animal_type": case["animal_type"],
                                "symptoms_text": detail.get("symptoms_text", "See details below."),
                                "diagnosis": diag,
                                "confidence_score": case["confidence_score"],
                                "created_at": case["created_at"]
                            }
                            render_pdf_button(case_detail_data, key_suffix=f"hist_{case_id}")

                        # Feedback Section
                        if detail.get("feedback_correct") is None:
                            st.divider()
                            st.markdown("**Was this diagnosis helpful?**")
                            fb1, fb2 = st.columns(2)
                            if fb1.button("✅ Yes, Correct", key=f"fb_pos_{case_id}"):
                                api_post("/history/feedback", json_payload={"case_id": case_id, "feedback_correct": True})
                                st.toast("Thank you for your feedback!")
                                st.rerun()
                            if fb2.button("❌ No, Incorrect", key=f"fb_neg_{case_id}"):
                                actual = st.text_input("What was the actual diagnosis?", key=f"actual_{case_id}")
                                if st.button("Submit Feedback", key=f"fb_sub_{case_id}"):
                                    api_post("/history/feedback", json_payload={"case_id": case_id, "feedback_correct": False, "farmer_note": actual})
                                    st.toast("Thank you for your feedback!")
                                    st.rerun()
                    else:
                        st.error("Failed to load details.")

            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
