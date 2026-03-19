import streamlit as st
import google.generativeai as genai
from PIL import Image
import pymupdf as fitz 
import time
import io
import cv2
import numpy as np
from gtts import gTTS
import base64
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr

# ==========================================
# 1. SYSTEM CONFIGURATION & THEME
# ==========================================
st.set_page_config(page_title="AXOM Global Systems", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .portal-header { 
        background-color: #001F3F; 
        padding: 25px; 
        border-radius: 0px; 
        border-left: 10px solid #D4AF37; 
        margin-bottom: 25px; 
    }
    .status-active { color: #00ff41; font-weight: bold; font-size: 0.8rem; letter-spacing: 1px; }
    .stButton>button { border-radius: 0px; font-weight: bold; transition: 0.3s; text-transform: uppercase; }
    .stButton>button:hover { border: 1px solid #D4AF37; color: #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CORE ENGINES
# ==========================================
def axom_speak(text):
    """Audio output for examiner feedback."""
    try:
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
        st.markdown(md, unsafe_allow_html=True)
    except Exception:
        pass

@st.cache_resource
def load_axom_engine():
    """AI Model Initialization."""
    try:
        api_key = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash'), None
    except Exception as e:
        return None, str(e)

model, error_message = load_axom_engine()

# --- State Management ---
if 'role' not in st.session_state: st.session_state.role = None
if 'subject' not in st.session_state: st.session_state.subject = "English"
if 'history' not in st.session_state: st.session_state.history = []
if 'live_chat' not in st.session_state: st.session_state.live_chat = None
if 'last_ai_msg' not in st.session_state: st.session_state.last_ai_msg = ""

# ==========================================
# 3. AUTHENTICATION INTERFACE
# ==========================================
if not st.session_state.role:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>AXOM GLOBAL SYSTEMS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Advanced Academic Intelligence | June 2026 Series</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("STUDENT PORTAL", use_container_width=True): st.session_state.role = "Student"
    with col2:
        if st.button("TEACHER CONTROL", use_container_width=True): st.session_state.role = "Teacher"
    with col3:
        if st.button("PARENT OBSERVER", use_container_width=True): st.session_state.role = "Parent"
    st.stop()

# ==========================================
# 4. NAVIGATION CONTROL
# ==========================================
with st.sidebar:
    st.title("AXOM NAV")
    st.session_state.subject = st.selectbox("Current Subject", ["English", "Math", "Physics", "Biology", "Business"])
    st.divider()
    if st.button("LOG OUT", use_container_width=True):
        st.session_state.role = None
        st.rerun()

# ==========================================
# 5. STUDENT PORTAL
# ==========================================
if st.session_state.role == "Student":
    st.markdown(f"""<div class='portal-header'>
        <h2 style='color: white; margin: 0;'>STUDENT HUB: {st.session_state.subject.upper()}</h2>
        <p class='status-active'>SYSTEM STATUS: AI AGENT ONLINE</p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Document Analysis", "Speaking Lab", "AXON Live Class"])

    with tab1:
        st.subheader(f"Academic Analysis: {st.session_state.subject}")
        uploaded_file = st.file_uploader("Upload PDF Exam Script", type=['pdf'])
        
        if uploaded_file:
            rigor = st.select_slider("Marking Rigor", options=["Standard", "Harsh Examiner Mode"])
            if st.button("INITIATE SCAN"):
                with st.spinner("Analyzing Morphology and Logic..."):
                    pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                    sys_prompt = f"Act as a {rigor} Senior Examiner for {st.session_state.subject}. Mark this paper. Provide a Band Score. Be extremely specific on errors."
                    response = model.generate_content([sys_prompt] + pdf_parts)
                    st.success("Analysis Complete")
                    st.markdown(response.text)

  with tab2:
        st.subheader("AXON LIVE SPEAKING EXAM")
        
        # Initialize Exam State
        if 'exam_active' not in st.session_state:
            st.session_state.exam_active = False

        # --- THE COMMAND BUTTON ---
        if not st.session_state.exam_active:
            if st.button("START LIVE SPEAKING EXAM", use_container_width=True):
                st.session_state.exam_active = True
                st.session_state.live_chat = model.start_chat(history=[])
                
                # Initial Examiner Greeting
                intro_text = f"Welcome to the AXON Global Speaking Exam for {st.session_state.subject}. I am your Senior Examiner. Please state your name and candidate number to begin."
                st.session_state.last_ai_msg = intro_text
                axom_speak(intro_text)
                st.rerun()
        else:
            if st.button("END EXAM & GENERATE REPORT", type="primary", use_container_width=True):
                st.session_state.exam_active = False
                st.rerun()

        # --- THE INTERACTION ZONE ---
        if st.session_state.exam_active:
            st.info(f"EXAMINER: {st.session_state.last_ai_msg}")
            
            # The Mic Recorder acts as the "Live Trigger"
            audio_data = mic_recorder(
                start_prompt="LISTEN MODE: ON (Speak Now)",
                stop_prompt="PROCESS RESPONSE",
                key='live_mic_stream'
            )

            if audio_data:
                with st.spinner("Examiner is evaluating..."):
                    try:
                        # 1. Prepare Multimodal Payload (Audio + Instructions)
                        prompt_instructions = f"""
                        You are a strict {st.session_state.subject} Examiner. 
                        1. Listen to the attached audio.
                        2. Transcribe it internally.
                        3. If there is a major error, briefly correct it.
                        4. Ask the next logical exam question.
                        Maintain a professional, formal tone.
                        """
                        
                        audio_payload = [
                            {"mime_type": "audio/webm", "data": audio_data['bytes']},
                            prompt_instructions
                        ]

                        # 2. Get AI Response
                        response = st.session_state.live_chat.send_message(audio_payload)
                        st.session_state.last_ai_msg = response.text
                        
                        # 3. Speak the Response Immediately
                        axom_speak(response.text)
                        
                        # 4. Refresh to show new text
                        st.rerun()

                    except Exception as e:
                        st.error(f"Connection Interrupted: {e}") 
    
with tab3:
        st.subheader("AXON Virtual Suite")
        st.write("Join the encrypted video session for live instruction.")
        room_id = f"AXOM-GLOBAL-{st.session_state.subject}-2026"
        jitsi_url = f"https://meet.jit.si/{room_id}#config.startWithAudioMuted=true"
        
        if st.button("LAUNCH AXON VIDEO ROOM"):
            st.components.v1.iframe(jitsi_url, height=700, scrolling=True)

# ==========================================
# 6. MANAGEMENT INTERFACES
# ==========================================
elif st.session_state.role == "Teacher":
    st.markdown("<div class='portal-header'><h2 style='color: white; margin: 0;'>TEACHER COMMAND CENTER</h2></div>", unsafe_allow_html=True)
    st.write(f"Managing Subject: {st.session_state.subject}")
    st.button("GENERATE DEEP STUDENT REPORT")
    st.button("VIEW PERFORMANCE ANALYTICS")

elif st.session_state.role == "Parent":
    st.markdown("<div class='portal-header'><h2 style='color: white; margin: 0;'>PARENT DASHBOARD</h2></div>", unsafe_allow_html=True)
    st.metric(label="Engagement Score", value="94%", delta="Target: Band 8.5")
    st.info("Live Status: Student is currently active in AXON session.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #555; font-size: 0.7rem;'>COPYRIGHT 2026 AXOM GLOBAL EDUCATIONAL SYSTEMS | ALL RIGHTS RESERVED</p>", unsafe_allow_html=True)
