import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
import json
import io
import cv2
import numpy as np
from gtts import gTTS
import base64

# ==========================================
# 1. CORE BRAIN & UTILITIES
# ==========================================
def axom_pro_scanner(image_file):
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pro_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return Image.fromarray(pro_img)

def speak_text(text):
    """Converts text to speech and returns an audio player."""
    tts = gTTS(text=text, lang='en', tld='co.uk') # British Accent for IGCSE
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    # Convert to base64 for streamlit audio player
    b64 = base64.b64encode(fp.getvalue()).decode()
    md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
    st.markdown(md, unsafe_allow_html=True)

@st.cache_resource
def load_axom_engine():
    try:
        if "GEMINI_KEY" not in st.secrets:
            return None, "Missing API Key in Streamlit Secrets."
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model, None
    except Exception as e:
        return None, str(e)

model, error_message = load_axom_engine()

# Initialize Session States
if "history" not in st.session_state: st.session_state.history = []
if 'role' not in st.session_state: st.session_state.role = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# ==========================================
# 2. IDENTITY & LOGIN GATE
# ==========================================
st.set_page_config(page_title="AXOM Global", layout="wide")

if not st.session_state.role:
    st.markdown("<h1 style='text-align: center;'>🚀 AXOM COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.subheader("Select Your Account Type to Begin")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 Student Portal"): st.session_state.role = "Student"
    with col2:
        if st.button("👨‍🏫 Teacher Portal"): st.session_state.role = "Teacher"
    with col3:
        if st.button("👪 Parent Portal"): st.session_state.role = "Parent"
    st.stop()

# Sidebar Logic
with st.sidebar:
    st.success(f"User: {st.session_state.role}")
    if st.button("Logout"):
        st.session_state.role = None
        st.session_state.chat_history = []
        st.rerun()
    st.divider()
    st.header("Marking History")
    for item in reversed(st.session_state.history):
        st.write(f"📝 {item['filename']}")

# ==========================================
# 3. THE STUDENT PORTAL
# ==========================================
if st.session_state.role == "Student":
    # Branding
    st.markdown("<div style='background-color: #001F3F; padding: 15px; border-radius: 10px; border-left: 10px solid #00ff41;'><h1 style='color: white; margin: 0;'>STUDENT HUB</h1></div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📝 Written Exam Marking", "🎙️ Live Speaking Lab"])

    # --- TAB 1: PDF MARKING ---
    with tab1:
        uploaded_file = st.file_uploader("Upload Exam Paper (PDF)", type=['pdf'])
        if uploaded_file:
            rigor = st.select_slider("Marking Rigor", options=["Standard", "Harsh"])
            if st.button("RUN ANALYSIS"):
                with st.spinner("AXOM Engine Scanning..."):
                    pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                    prompt = f"Mark this paper in {rigor} mode. Give clear Band scores."
                    response = model.generate_content([prompt] + pdf_parts)
                    st.markdown("### Examiner Report")
                    st.write(response.text)
                    st.session_state.history.append({"filename": uploaded_file.name})

    # --- TAB 2: INTERACTIVE SPEAKING ---
    with tab2:
        st.header("🤖 Live AI Examiner")
        st.write("The AI will speak. Use your device's 'Dictation' or Type to respond.")
        
        # Initialize Chat Session if empty
        if not st.session_state.chat_history:
            initial_msg = "Hello! I am your AXOM Examiner. Today we will practice your speaking. Are you ready to begin?"
            st.session_state.chat_history.append({"role": "assistant", "content": initial_msg})
            speak_text(initial_msg)

        # Display Chat
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Input logic
        if user_input := st.chat_input("Your response..."):
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"): st.write(user_input)
            
            with st.chat_message("assistant"):
                # Use Gemini to generate a response as an examiner
                chat = model.start_chat(history=[{"role": m["role"], "parts": [m["content"]]} for m in st.session_state.chat_history[:-1]])
                response = chat.send_message(user_input)
                ai_text = response.text
                st.write(ai_text)
                st.session_state.chat_history.append({"role": "assistant", "content": ai_text})
                speak_text(ai_text)

# ==========================================
# 4. TEACHER & PARENT (Next Sprints)
# ==========================================
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Dashboard")
    st.info("Module 1: Handwriting Scanner - Coming tonight.")

elif st.session_state.role == "Parent":
    st.title("👪 Parent Dashboard")
    st.info("Module 1: Weekly Progress Tracker - Coming tonight.")
