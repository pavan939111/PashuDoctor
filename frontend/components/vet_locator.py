import streamlit as st

HELPLINES = {
    "National Animal Disease Helpline": "1962",
    "Kisan Call Centre": "1800-180-1551",
    "ICAR Helpline": "1800-180-1551"
}

STATE_VET_NUMBERS = {
    "Telangana":      "040-23490007",
    "Andhra Pradesh": "0866-2474933",
    "Maharashtra":    "022-27560232",
    "Punjab":         "0172-2740843",
    "Gujarat":        "079-22861609",
    "Rajasthan":      "0141-2227624",
    "Karnataka":      "080-22253131",
    "Tamil Nadu":     "044-25384913",
    "Uttar Pradesh":  "0522-2740158",
    "West Bengal":    "033-22376754",
    "Bihar":          "0612-2217073",
    "Madhya Pradesh": "0755-2558836"
}

def render_vet_locator(district: str = "your area", state: str = "India", urgency: str = "monitor"):
    """Renders a comprehensive veterinary help locator and helpline directory"""
    
    st.markdown("---")
    st.markdown("### 🏥 Find Veterinary Help")
    
    # 1. Urgent Action Alert
    if urgency in ["immediate", "within_24h", "emergency"]:
        st.markdown(f"""
            <div style="background-color: #B71C1C; color: white; padding: 20px; border-radius: 12px; border-left: 8px solid #FF5252; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(183, 28, 28, 0.3);">
                <h2 style="color: white; margin-top: 0; font-weight: 800;">🚨 URGENT ACTION REQUIRED</h2>
                <p style="margin-bottom: 15px; font-size: 1.1rem; opacity: 0.9;">This condition is critical and requires professional veterinary care immediately.</p>
                <div style="font-size: 2rem; font-weight: 900; text-align: center; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                    <a href="tel:1962" style="color: white; text-decoration: none;">📞 Call 1962 NOW (Free, 24/7)</a>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # 2. Helpline Cards
    st.markdown("#### 📞 National Emergency Helplines")
    cols = st.columns(3)
    for i, (name, number) in enumerate(HELPLINES.items()):
        with cols[i]:
            st.markdown(f"""
                <div style="background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); text-align: center; height: 100%;">
                    <p style="font-weight: 700; color: #2E7D32; margin-bottom: 10px; min-height: 50px;">{name}</p>
                    <p style="font-size: 1.3rem; font-weight: 800; color: #1565C0; margin-bottom: 0;">{number}</p>
                    <p style="font-size: 0.8rem; color: #666; margin-top: 5px;">Available 24/7</p>
                </div>
            """, unsafe_allow_html=True)

    # 3. State-Specific Support
    if state in STATE_VET_NUMBERS:
        st.markdown(f"""
            <div style="margin-top: 25px; padding: 15px; background: linear-gradient(90deg, #E3F2FD 0%, #BBDEFB 100%); border-radius: 10px; border-left: 6px solid #1565C0; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="font-weight: 700; color: #0D47A1; font-size: 1.1rem;">📍 {state} Veterinary Control Room:</span>
                </div>
                <div>
                    <a href="tel:{STATE_VET_NUMBERS[state]}" style="font-weight: 800; font-size: 1.4rem; color: #0D47A1; text-decoration: none;">📞 {STATE_VET_NUMBERS[state]}</a>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 4. Maps & Government Links
    st.markdown("<h4 style='margin-top: 30px;'>📍 Find Nearby Facilities</h4>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        maps_url = f"https://www.google.com/maps/search/veterinary+hospital+near+{district}+{state}+India"
        st.link_button(
            "📍 Find Nearest Vet on Google Maps",
            maps_url,
            use_container_width=True
        )
        
    with c2:
        st.link_button(
            "🏛️ Government Vet Clinics (DAHD India)",
            "https://dahd.nic.in/veterinary-hospitals",
            use_container_width=True
        )
