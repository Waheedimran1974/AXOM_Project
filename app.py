import streamlit as st
import google.generativeai as genai
from PIL import Image

# Secure Configuration
genai.configure(api_key=st.secrets["GEMINI_KEY"])
model = genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="AXOM Global", layout="wide", page_icon="🚀")

with st.sidebar:
    st.title("Settings")
    subject = st.selectbox("Target Subject", ["IGCSE English 0510", "Physics", "Chemistry", "Mathematics"])
    mode = st.radio("Grading Mode", ["Strict (Cambridge)", "Feedback Only", "Quick Score"])
    st.divider()
    st.write("📈 **Profit Rate:** $0.998 / page")

st.title("🚀 AXOM: Senior Examiner AI")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📄 Upload Student Work")
    uploaded_file = st.file_uploader("Upload Image/PDF", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    content_to_analyze = None
    
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            # If it's a PDF, we tell Gemini to read the raw data
            content_to_analyze = {"mime_type": "application/pdf", "data": uploaded_file.read()}
            st.success("PDF Exam Paper Loaded successfully.")
        else:
            # If it's an Image, we show it and prepare it
            image = Image.open(uploaded_file)
            st.image(image, caption="Student Submission", use_container_width=True)
            content_to_analyze = image

with col2:
    st.markdown("### 📊 AI Analysis Results")
    if content_to_analyze and st.button("RUN SENIOR EXAMINER AI"):
        with st.spinner(f"Analyzing {subject} standards..."):
            try:
                prompt = f"You are a Senior Cambridge Examiner for {subject}. Analyze this paper, give a total score, and provide 3 tips for A*."
                
                # We send the specific content (Image or PDF) to the AI
                response = model.generate_content([prompt, content_to_analyze])
                st.markdown(response.text)
                st.success("Analysis Complete.")
            except Exception as e:
                st.error(f"Analysis Failed: {e}")
