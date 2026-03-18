import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
import json
import io
import cv2
import numpy as np
import speech_recognition as sr
from pydub import AudioSegment

# ==========================================
# 1. CORE BRAIN & UTILITIES
# ==========================================
def axom_pro_scanner(image_file):
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pro_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return Image.fromarray(pro_img)

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

if "history" not in st.session_state:
    st.session_state.history = []
if 'role' not in st.session_state:
    st.session_state.role = None

# ==========================================
# 2. THE HANDS: RED PEN PAINTER
# ==========================================
def apply_harsh_marking(uploaded_file, ai_json_instructions):
    try:
        input_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        for action in ai_json_instructions:
            for page in doc:
                text_instances = page.search_for(action["text"])
                for inst in text_instances:
                    if action["action"] == "strike_through":
                        line_mid = (inst.y0 + inst.y1) / 2
                        annot = page.add_line_annot(fitz.Point(inst.x0, line_mid), fitz.Point(inst.x1, line_mid))
                        annot.set_colors(stroke=(1, 0, 0)) 
                        annot.update()
                        page.add_text_annot(fitz.Point(inst.x1 + 5, inst.y0), action["comment"])
        return doc.write()
    except:
        return None

# ==========================================
# 3. IDENTITY & LOGIN GATE
# ==========================================
st.set_page_config(page_title="AXOM Global", layout="wide")

if not st.session_state.role:
    st.markdown("<h1 style='text-align: center;'>🚀 Welcome to AXOM</h1>", unsafe_allow_html=True)
    st.subheader("Select Your Account Type to Begin")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 Student Portal"): st.session_state.role = "Student"
    with col2:
        if st.button("👨‍🏫 Teacher Portal"): st.session_state.role = "Teacher"
    with col3:
        if st.button("👪 Parent Portal"): st.session_state.role = "Parent"
    st.stop()

# Sidebar
with st.sidebar:
    st.success(f"Mode: {st.session_state.role}")
    if st.button("Logout / Change Role"):
        st.session_state.role = None
        st.rerun()
    st.divider()
    st.header("Submission History")
    if not st.session_state.history:
        st.write("No papers marked yet.")
    else:
        for item in reversed(st.session_state.history):
            st.write(f"**{item['filename']}**")
            st.caption(f"{item['timestamp']}")

# ==========================================
# 4. STUDENT PORTAL (MARKING + SPEAKING)
# ==========================================
if st.session_state.role == "Student":
    st.markdown("<div style='background-color: #001F3F; padding: 20px; border-radius: 10px; border-bottom: 5px solid #D4AF37;'><h1 style='color: white; text-align: center; margin: 0;'>AXOM STUDENT PORTAL</h1><p style='color: #D4AF37; text-align: center; font-weight: bold;'>SENIOR EXAMINER AI SYSTEM</p></div><br>", unsafe_allow_html=True)

    if error_message:
        st.error(f"Engine Offline: {error_message}")
        st.stop()

    # --- PART 1: PDF MARKING ---
    st.header("📝 Written Exam Marking")
    uploaded_file = st.file_uploader("Upload Exam Paper (PDF)", type=['pdf'])
    if uploaded_file:
        rigor = st.select_slider("Select Marking Rigor", options=["Standard", "Harsh"])
        tos_agreed = st.checkbox("I agree to the Halal-Ads & Data Privacy Terms")
        if st.button("RUN AXOM ANALYSIS", disabled=not tos_agreed):
            progress_bar = st.progress(0)
            for i in range(10):
                progress_bar.progress((i + 1) / 10)
                time.sleep(0.3)
            with st.spinner("Analyzing..."):
                try:
                    pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                    prompt = f"Mark this paper in {rigor} mode. Format: JSON_START [{{'action': 'strike_through', 'text': 'word', 'comment': 'explanation'}}] JSON_END"
                    response = model.generate_content([prompt] + pdf_parts)
                    report_text = response.text.split("JSON_START")[0] if "JSON_START" in response.text else response.text
                    st.session_state.history.append({"filename": uploaded_file.name, "timestamp": time.strftime("%H:%M:%S")})
                    st.markdown("### Examiner Report")
                    st.write(report_text)
                except Exception as e:
                    st.error(f"Failed: {e}")

    # --- PART 2: SPEAKING LAB ---
    st.markdown("---")
    st.header("🎙️ AXOM Speaking Lab")
    questions = ["Describe a place you visited recently.", "How will technology change education?", "Benefits of learning languages?"]
    current_q = st.selectbox("Choose a Practice Topic:", questions)
    audio_file = st.file_uploader("Upload your Voice Recording (WAV/MP3)", type=['wav', 'mp3'])

    if audio_file:
        with st.spinner("Analyzing your fluency..."):
            try:
                audio = AudioSegment.from_file(audio_file)
                audio.export("temp_voice.wav", format="wav")
                r = sr.Recognizer()
                with sr.AudioFile("temp_voice.wav") as source:
                    audio_data = r.record(source)
                    student_speech = r.recognize_google(audio_data)
                    st.info(f"**Transcribed Speech:** {student_speech}")
                    prompt = f"You are a Senior IELTS Examiner. The student said: '{student_speech}' for question '{current_q}'. Analyze Band Score, Fluency, and Grammar."
                    speaking_response = model.generate_content(prompt)
                    st.success("### Examiner Feedback")
                    st.write(speaking_response.text)
            except Exception as e:
                st.error(f"Audio Error: {e}")

# ==========================================
# 5. OTHER PORTALS
# ==========================================
elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Dashboard")
    st.write("Coming Soon: Class Analytics and Handwriting Clone.")

elif st.session_state.role == "Parent":
    st.title("👪 Parent Dashboard")
    st.write("Coming Soon: Grade Predictor and Progress Tracking.")
