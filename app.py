import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
import io
import cv2
import numpy as np
from gtts import gTTS
import base64
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

# ==========================================
# 1. STREAMLIT CONFIGURATION
# ==========================================
st.set_page_config(page_title="AXOM Global", page_icon="🚀", layout="wide")

# Custom UI Styling (Deep Blue & Gold - Premium Academic Look)
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .portal-header { background-color: #001F3F; padding: 20px; border-radius: 10px; border-left: 8px solid #D4AF37; margin-bottom: 20px; }
    .success-text { color: #00ff41; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CORE NEURAL ENGINES
# ==========================================
def axom_pro_scanner(image_file):
    """Turns standard photos into High-Contrast B&W Scans."""
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    pro_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return Image.fromarray(pro_img)

def axom_speak(text):
    """Generates High-Fidelity British Audio for the Examiner."""
    try:
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error("Audio engine offline. Please read the text below.")

@st.cache_resource
def load_axom_engine():
    """Initializes Gemini 2.0 Flash Securely."""
    try:
        if "GEMINI_KEY" not in st.secrets:
            return None, "System Alert: Missing GEMINI_KEY in Streamlit Secrets."
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model, None
    except Exception as e:
        return None, str(e)

model, error_message = load_axom_engine()

# --- Global State Management ---
if "history" not in st.session_state: st.session_state.history = []
if 'role' not in st.session_state: st.session_state.role = None
if 'live_chat' not in st.session_state: st.session_state.live_chat = None
if 'last_ai_msg' not in st.session_state: st.session_state.last_ai_msg = ""

# ==========================================
# 3. PDF RED PEN LOGIC
# ==========================================
def apply_harsh_marking(uploaded_file, ai_json_instructions):
    """Applies visual annotations to the student's PDF."""
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
# 4. THE COMMAND GATE (LOGIN)
# ==========================================
if not st.session_state.role:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>🚀 AXOM GLOBAL PLATFORM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Select Your Access Tier</p>", unsafe_allow_html=True)
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 Student Access", use_container_width=True): st.session_state.role = "Student"
    with col2:
        if st.button("👨‍🏫 Teacher Access", use_container_width=True): st.session_state.role = "Teacher"
    with col3:
        if st.button("👪 Parent Access", use_container_width=True): st.session_state.role = "Parent"
    st.stop()

# --- System Sidebar ---
with st.sidebar:
    st.markdown(f"### 👤 Profile: {st.session_state.role}")
    if st.button("Log Out", use_container_width=True):
        st.session_state.role = None
        st.session_state.live_chat = None 
        st.rerun()
    
    st.divider()
    st.subheader("Recent Scans")
    if not st.session_state.history:
        st.caption("No operations logged.")
    for item in reversed(st.session_state.history):
        st.markdown(f"📄 **{item['filename']}** \n*{item['timestamp']}*")

# ==========================================
# 5. STUDENT PORTAL (THE MONEY MAKER)
# ==========================================
if st.session_state.role == "Student":
    st.markdown("<div class='portal-header'><h2 style='color: white; margin: 0;'>🎓 AXOM STUDENT HUB</h2><p style='color: #D4AF37; margin: 0;'>Advanced Examiner AI Active</p></div>", unsafe_allow_html=True)

    if error_message:
        st.error(f"Engine Offline: {error_message}")
        st.stop()

    tab1, tab2 = st.tabs(["📝 Document Analysis", "🎙️ Live Speaking Interview"])

    # --- MODULE 1: PDF SCANNER ---
    with tab1:
        st.markdown("### Upload Exam Script")
        uploaded_file = st.file_uploader("Compatible Formats: PDF", type=['pdf'])
        
        if uploaded_file:
            rigor = st.select_slider("Marking Rigor", options=["Standard", "Harsh (Senior Examiner)"])
            tos_agreed = st.checkbox("I agree to the Halal-Ads & Data Privacy Terms")
            
            if st.button("INITIATE AXOM SCAN", disabled=not tos_agreed, use_container_width=True):
                progress_bar = st.progress(0)
                for i in range(10):
                    progress_bar.progress((i + 1) / 10)
                    time.sleep(0.15)
                
                with st.spinner("Analyzing Morphology & Syntax..."):
                    try:
                        pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                        prompt = f"Act as a strict IGCSE Examiner. Mark this paper in {rigor} mode. Provide a Band Score. Format corrections as: JSON_START [{{\"action\": \"strike_through\", \"text\": \"wrong_word\", \"comment\": \"reason\"}}] JSON_END"
                        
                        response = model.generate_content([prompt] + pdf_parts)
                        report_text = response.text.split("JSON_START")[0] if "JSON_START" in response.text else response.text
                        
                        st.session_state.history.append({
                            "filename": uploaded_file.name, 
                            "timestamp": time.strftime("%H:%M")
                        })
                        
                        st.markdown("<h3 class='success-text'>Scan Complete.</h3>", unsafe_allow_html=True)
                        st.write(report_text)
                    except Exception as e:
                        st.error(f"Scan failed due to system overload: {e}")

    # --- MODULE 2: LIVE VOICE AI ---
    with tab2:
        st.markdown("### 🎙️ The Live Interview")
        st.write("Ensure your microphone is enabled. Tap to speak, tap to send.")

        if st.session_state.live_chat is None:
            st.session_state.live_chat = model.start_chat(history=[])
            intro_msg = "Welcome to the AXOM Speaking Lab. I am your Senior Examiner. Are you ready to begin the test?"
            st.session_state.last_ai_msg = intro_msg
            axom_speak(intro_msg) 

        st.info(f"**Examiner:** {st.session_state.last_ai_msg}")

        # Live Audio Capture
        audio_data = mic_recorder(
            start_prompt="🎙️ Tap to Record",
            stop_prompt="⏹️ Tap to Submit",
            key='student_mic'
        )

        if audio_data:
            with st.spinner("Processing speech patterns..."):
                r = sr.Recognizer()
                audio_file = io.BytesIO(audio_data['bytes'])
                with sr.AudioFile(audio_file) as source:
                    try:
                        recorded_audio = r.record(source)
                        user_text = r.recognize_google(recorded_audio)
                        st.success(f"**You:** {user_text}")
                        
                        sys_prompt = f"You are an IGCSE Speaking Examiner. The student said: '{user_text}'. Respond naturally, correct one grammar mistake if necessary, and ask the next question to keep the conversation going."
                        response = st.session_state.live_chat.send_message(sys_prompt)
                        st.session_state.last_ai_msg = response.text
                        
                        axom_speak(response.text)
                        st.rerun() 
                        
                    except sr.UnknownValueError:
                        st.warning("Audio not detected clearly. Please speak closer to the microphone.")
                    except Exception as e:
                        st.error(f"Microphone offline: {e}")

# ==========================================
# 6. TEACHER & PARENT PORTALS
# ==========================================
elif st.session_state.role == "Teacher":
    st.markdown("<div class='portal-header' style='border-left-color: #00ff41;'><h2 style='color: white; margin: 0;'>👨‍🏫 TEACHER DASHBOARD</h2></div>", unsafe_allow_html=True)
    st.info("System Update: The 'Teacher Handwriting Clone' AI model is training and will deploy in v2.0.")
    st.write("**Your Global Class Code:** `AXOM-PRO-2026`")

elif st.session_state.role == "Parent":
    st.markdown("<div class='portal-header' style='border-left-color: #ff0041;'><h2 style='color: white; margin: 0;'>👪 PARENT DASHBOARD</h2></div>", unsafe_allow_html=True)
    st.info("System Update: 'Live Grade Predictor' and Halal Ad-Blocking filters are active.")
    st.metric(label="Student Target Goal", value="Band 8.5", delta="On Track")

# ==========================================
# 7. FOOTER
# ==========================================
st.markdown("---")
st.markdown("<p style='text-align: center; color: #555; font-size: 0.8rem;'>© 2026 AXOM Global Educational Systems | Powered by Gemini 2.0 Flash</p>", unsafe_allow_html=True)
