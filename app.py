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
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

# ==========================================
# 1. STREAMLIT CONFIG (MUST BE FIRST)
# ==========================================
st.set_page_config(page_title="AXOM Global", page_icon="🚀", layout="wide")

# ==========================================
# 2. CORE UTILITIES & AI ENGINE
# ==========================================
def axom_pro_scanner(image_file):
    """Turns standard photos into High-Contrast B&W Scans."""
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pro_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return Image.fromarray(pro_img)

def axom_speak(text):
    """Converts AI text to a British Examiner Voice and auto-plays it."""
    try:
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error("Audio generation failed, but text is available.")

@st.cache_resource
def load_axom_engine():
    """Initializes Gemini 2.0 Flash securely."""
    try:
        if "GEMINI_KEY" not in st.secrets:
            return None, "Missing GEMINI_KEY in Streamlit Secrets."
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model, None
    except Exception as e:
        return None, str(e)

model, error_message = load_axom_engine()

# --- Initialize Session States ---
if "history" not in st.session_state: st.session_state.history = []
if 'role' not in st.session_state: st.session_state.role = None
if 'live_chat' not in st.session_state: st.session_state.live_chat = None
if 'last_ai_msg' not in st.session_state: st.session_state.last_ai_msg = ""

# ==========================================
# 3. THE PDF RED PEN PAINTER
# ==========================================
def apply_harsh_marking(uploaded_file, ai_json_instructions):
    """Draws red lines and comments directly onto the student's PDF."""
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
# 4. IDENTITY & LOGIN GATE (HALAL UX)
# ==========================================
if not st.session_state.role:
    st.markdown("<h1 style='text-align: center; color: #00ff41;'>🚀 AXOM COMMAND CENTER</h1>", unsafe_allow_html=True)
    st.subheader("Select Your Account Type to Begin")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 Student Portal", use_container_width=True): st.session_state.role = "Student"
    with col2:
        if st.button("👨‍🏫 Teacher Portal", use_container_width=True): st.session_state.role = "Teacher"
    with col3:
        if st.button("👪 Parent Portal", use_container_width=True): st.session_state.role = "Parent"
    st.stop() # Halts execution until a role is selected

# --- Global Sidebar ---
with st.sidebar:
    st.success(f"Active Profile: {st.session_state.role}")
    if st.button("Logout / Switch Role", use_container_width=True):
        st.session_state.role = None
        st.session_state.live_chat = None # Reset chat on logout
        st.rerun()
    
    st.divider()
    st.header("Marking Ledger")
    if not st.session_state.history:
        st.caption("No papers processed yet.")
    for item in reversed(st.session_state.history):
        st.write(f"📄 {item['filename']} ({item['timestamp']})")

# ==========================================
# 5. THE STUDENT PORTAL (CORE ENGINE)
# ==========================================
if st.session_state.role == "Student":
    st.markdown("<div style='background-color: #001F3F; padding: 20px; border-radius: 10px; border-left: 10px solid #00ff41;'><h2 style='color: white; margin: 0;'>🎓 STUDENT HUB</h2><p style='color: #D4AF37; margin: 0;'>Senior Examiner AI Active</p></div><br>", unsafe_allow_html=True)

    if error_message:
        st.error(f"Engine Offline: {error_message}")
        st.stop()

    tab1, tab2 = st.tabs(["📝 Written Exam Marking", "🎙️ Live Speaking Lab"])

    # --- TAB 1: PDF EXAM MARKING ---
    with tab1:
        st.header("Upload Written Work")
        uploaded_file = st.file_uploader("Upload Exam Paper (PDF format)", type=['pdf'])
        
        if uploaded_file:
            rigor = st.select_slider("Select Marking Rigor", options=["Standard", "Harsh"])
            tos_agreed = st.checkbox("I agree to the Halal-Ads & Data Privacy Terms")
            
            if st.button("RUN AXOM ANALYSIS", disabled=not tos_agreed, use_container_width=True):
                progress_bar = st.progress(0)
                for i in range(10):
                    progress_bar.progress((i + 1) / 10)
                    time.sleep(0.2)
                
                with st.spinner("AI Scanning Syntax & Descriptors..."):
                    try:
                        pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                        prompt = f"Act as a Senior IGCSE Examiner. Mark this paper in {rigor} mode. Provide a Band Score, Task Response critique, and Cohesion analysis. Format corrections as: JSON_START [{{\"action\": \"strike_through\", \"text\": \"wrong_word\", \"comment\": \"reason\"}}] JSON_END"
                        
                        response = model.generate_content([prompt] + pdf_parts)
                        full_text = response.text
                        
                        report_text = full_text.split("JSON_START")[0] if "JSON_START" in full_text else full_text
                        
                        st.session_state.history.append({
                            "filename": uploaded_file.name, 
                            "timestamp": time.strftime("%H:%M")
                        })
                        
                        st.success("Analysis Complete.")
                        st.markdown("### Official Examiner Report")
                        st.write(report_text)
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

    # --- TAB 2: LIVE SPEAKING AI ---
    with tab2:
        st.header("🎙️ AXOM Live Interview")
        st.write("Click the microphone, speak naturally, and the Examiner will reply instantly.")

        # Initialize the AI Examiner's brain if it hasn't started yet
        if st.session_state.live_chat is None:
            st.session_state.live_chat = model.start_chat(history=[])
            intro_msg = "Hello, I am your AXOM Speaking Examiner. Are you ready to begin your mock test?"
            st.session_state.last_ai_msg = intro_msg
            axom_speak(intro_msg) # Speak the intro

        # Display what the AI just said
        st.info(f"**Examiner says:** {st.session_state.last_ai_msg}")

        # The Live Microphone
        audio_data = mic_recorder(
            start_prompt="Tap to Speak 🎙️",
            stop_prompt="Tap to Send ⏹️",
            key='student_mic'
        )

        if audio_data:
            with st.spinner("AXOM is processing your speech..."):
                r = sr.Recognizer()
                audio_file = io.BytesIO(audio_data['bytes'])
                with sr.AudioFile(audio_file) as source:
                    recorded_audio = r.record(source)
                    try:
                        # 1. Transcribe Student Speech
                        user_text = r.recognize_google(recorded_audio)
                        st.success(f"**You said:** {user_text}")
                        
                        # 2. Send to Gemini and get response
                        sys_prompt = f"You are an IGCSE Speaking Examiner. The student just said: '{user_text}'. Respond naturally to continue the conversation, assess their English slightly, and ask the next question."
                        response = st.session_state.live_chat.send_message(sys_prompt)
                        st.session_state.last_ai_msg = response.text
                        
                        # 3. Speak the AI response aloud
                        axom_speak(response.text)
                        st.rerun() # Refresh UI to show new state
                        
                    except sr.UnknownValueError:
                        st.error("Examiner: I couldn't quite catch that. Could you speak a bit louder?")
                    except Exception as e:
                        st.error(f"Audio processing error: {e}")

# ==========================================
# 6. TEACHER & PARENT PORTALS (Upcoming Sprints)
# ==========================================
elif st.session_state.role == "Teacher":
    st.markdown("<div style='background-color: #003F1F; padding: 20px; border-radius: 10px;'><h2 style='color: white;'>👨‍🏫 TEACHER DASHBOARD</h2></div><br>", unsafe_allow_html=True)
    st.info("Module 1: Handwriting Clone & Auto-Grader infrastructure is being prepared.")
    st.write("Generate Class Code: `AXOM-PRO-2026`")

elif st.session_state.role == "Parent":
    st.markdown("<div style='background-color: #3F001F; padding: 20px; border-radius: 10px;'><h2 style='color: white;'>👪 PARENT DASHBOARD</h2></div><br>", unsafe_allow_html=True)
    st.info("Module 1: Grade Predictor & Ad Safeguard infrastructure is being prepared.")
    st.metric(label="Student: Ibrahim_CEO | Target Grade", value="Band 8.5")

# ==========================================
# 7. FOOTER
# ==========================================
st.markdown("---")
st.markdown("<p style='text-align: center; color: grey; font-size: 0.8rem;'>© 2026 AXOM Global Educational Systems | Powered by Gemini 2.0 Flash</p>", unsafe_allow_html=True)
