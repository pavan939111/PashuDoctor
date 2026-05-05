import streamlit as st
import requests

st.title("PashuDoctor: AI Livestock Health Assistant")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Analyze", "Chat", "History"])

if page == "Home":
    st.write("Welcome to PashuDoctor. Use the sidebar to navigate.")

elif page == "Analyze":
    st.header("Analyze Livestock Health")
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)
        if st.button('Analyze'):
            st.write("Analyzing...")
            # Simulate API call
            # response = requests.post("http://backend:8000/api/v1/analyze", files={"file": uploaded_file})
            # st.write(response.json())
            st.success("Analysis Complete: Healthy")

elif page == "Chat":
    st.header("Chat with AI Specialist")
    user_input = st.text_input("Ask a question about your livestock:")
    if st.button('Send'):
        st.write(f"You: {user_input}")
        st.write("AI: This is a placeholder response.")

elif page == "History":
    st.header("Case History")
    st.write("No history available.")
