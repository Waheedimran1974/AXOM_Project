import streamlit as st
import google.generativeai as genai
import re
import time
import io
import base64
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder

# ==========================================
# 1. SYSTEM CONFIGURATION & THEME
# ==========================================
st.set_page_config(page_title="AXOM Global Systems", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .welcome-note { 
        font-size: 2rem; 
        font-weight: bold; 
        color: #D4AF37; 
        text-align: center; 
        padding: 40px; 
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .portal-header { 
        background-color: #001F3F; 
        padding: 20px; 
        border-left: 10px solid #D4AF37; 
        margin-bottom: 20px; 
    }
    .stButton>button { 
        border-radius: 0px; 
        font-weight: bold; 
        height: 60px;
        transition: 0.3s; 
        text-transform: uppercase;
        border: 1px solid #1e293b;
    }
    .stButton>button:hover { border: 1px solid #D4AF37; color: #D4AF37; background-color: #001F3F; }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Initialization ---
states = {
    'logged_in': False,
    'user_email': None,
    'user_name': None,
    'board': None,
    'subject': None,
    'menu_choice': "DASHBOARD",
    'last_ai_msg': ""
}
for key, value in states.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 2. CORE UTILITIES
# ==========================================
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@(gmail\.com|googlemail\.com|yahoo\.com|icloud\.com|apple\.com)$"
    return re.match(pattern, email)

def axom_speak(text):
    try:
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
        st.markdown(md, unsafe_allow_html=True)
    except:
        pass

# ==========================================
# 3. PHASE 1: LOGIN GATE
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>AXOM TERMINAL ACCESS</h1>", unsafe_allow_html=True)
    
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        email = st.text_input("AUTHORIZED EMAIL (GOOGLE, YAHOO, APPLE)")
        name = st.text_input("FULL NAME")
        
        if st.button("AUTHENTICATE SYSTEM", use_container_width=True):
            if is_valid_email(email) and name:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_name = name.upper()
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID EMAIL DOMAIN")
    st.stop()

# ==========================================
# 4. PHASE 2: ONBOARDING (BOARD & SUBJECT)
# ==========================================
if st.session_state.board is None:
    st.markdown(f"<div class='welcome-note'>WELCOME TO AXOM {st.session_state.user_name}</div>", unsafe_allow_html=True)
    
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        board = st.selectbox("SELECT EXAMINATION BOARD", ["CAMBRIDGE IGCSE/A-LEVEL", "EDEXCEL", "OXFORD AQA", "IB", "SAUDI NATIONAL"])
        subject = st.selectbox("SELECT PRIMARY SUBJECT", ["ENGLISH", "MATHEMATICS", "PHYSICS", "CHEMISTRY", "BIOLOGY", "BUSINESS STUDIES"])
        
        if st.button("INITIALIZE DASHBOARD", use_container_width=True):
            st.session_state.board = board
            st.session_state.subject = subject
            st.rerun()
    st.stop()

# ==========================================
# 5. PHASE 3: MAIN DASHBOARD GRID
# ==========================================

# Top Navigation Bar
st.markdown(f"""
    <div class='portal-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h2 style='margin:0; color: white;'>AXOM COMMAND CENTER</h2>
            <div style='text-align: right;'>
                <span style='color: #D4AF37; font-weight: bold;'>{st.session_state.user_name}</span><br>
                <span style='font-size: 0.8rem;'>{st.session_state.board} | {st.session_state.subject}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar Control
with st.sidebar:
    st.title("SETTINGS")
    if st.button("SIGN OUT", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# 12-BUTTON COMMAND GRID
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("PAST PAPER CHECKER", use_container_width=True): st.session_state.menu_choice = "PAPER CHECKER"
    if st.button("SCHEDULES OF CLASSES", use_container_width=True): st.session_state.menu_choice = "SCHEDULES"
    if st.button("CLASSROOMS (AXON)", use_container_width=True): st.session_state.menu_choice = "CLASSROOMS"
    if st.button("LEADERBOARD CHART", use_container_width=True): st.session_state.menu_choice = "LEADERBOARD"

with col2:
    if st.button("HISTORY", use_container_width=True): st.session_state.menu_choice = "HISTORY"
    if st.button("REPORTS", use_container_width=True): st.session_state.menu_choice = "REPORTS"
    if st.button("INTERACTIVE AI SYSTEM", use_container_width=True): st.session_state.menu_choice = "AI CHAT"
    if st.button("SUBSCRIPTION SETTINGS", use_container_width=True): st.session_state.menu_choice = "SUBSCRIPTION"

with col3:
    if st.button("FLASHCARDS", use_container_width=True): st.session_state.menu_choice = "FLASHCARDS"
    if st.button("MAP OF REPORT", use_container_width=True): st.session_state.menu_choice = "REPORT MAP"
    if st.button("AI REVISION (VOICE)", use_container_width=True): st.session_state.menu_choice = "AI REVISION"
    if st.button("PERSONAL SETTINGS", use_container_width=True): st.session_state.menu_choice = "SETTINGS"

st.divider()

# ==========================================
# 6. DYNAMIC MODULE LOADER
# ==========================================
current_view = st.session_state.menu_choice
st.markdown(f"<h3 style='color: #D4AF37;'>ACTIVE MODULE: {current_view}</h3>", unsafe_allow_html=True)

if current_view == "CLASSROOMS":
    st.markdown("""
        <div style='background-color: #001F3F; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
            <h4 style='margin:0; color: #D4AF37;'>AXON LIVE HD VIDEO PORTAL</h4>
            <p style='font-size: 0.8rem; color: #ccc;'>Powered by Daily.co Global Mesh Network</p>
        </div>
    """, unsafe_allow_html=True)

    # --- CONFIGURATION ---
    # In production, you would generate these rooms via the Daily API.
    # For now, use your static room URL from your Daily Dashboard.
    DAILY_ROOM_URL = "https://axom.daily.co/Main-Classroom" 
    
    # Customizing the interface: 
    # we add parameters to hide the Daily branding and auto-join with the user's name
    daily_config = f"{DAILY_ROOM_URL}?user_name={st.session_state.user_name}&is_knocking_enabled=true"

    # The Daily Prebuilt UI works beautifully in a 700px height frame
    st.components.v1.iframe(daily_config, height=700, scrolling=True)
    
    st.caption("Tip: Use the 'Background Effects' menu in the bottom bar to maintain a professional study environment.")
elif current_view == "AI REVISION":
    st.write("VOICE REVISION SYSTEM ACTIVE. SPEAK TO BEGIN YOUR SESSION.")
    audio = mic_recorder(start_prompt="START TALKING", stop_prompt="FINISH REVISION", key='rev_mic')
    # AI logic would process bytes here

elif current_view == "PAPER CHECKER":
    st.file_uploader("UPLOAD PDF SCRIPT", type=['pdf'])
    st.button("INITIATE EXAMINER MARKING")

elif current_view == "REPORT MAP":
    st.info("VISUALIZING PERFORMANCE DATA ACROSS GLOBAL CANDIDATES...")
    # Placeholder for mapping logic

elif current_view == "SETTINGS":
    st.write(f"ID: {st.session_state.user_email}")
    if st.button("UPDATE BOARD/SUBJECT"):
        st.session_state.board = None
        st.rerun()

else:
    st.warning(f"THE {current_view} MODULE IS UNDERGOING FINAL CALIBRATION FOR THE 2026 SESSION.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #555; font-size: 0.7rem;'>COPYRIGHT 2026 AXOM GLOBAL EDUCATIONAL SYSTEMS | POWERED BY GEMINI 2.0 FLASH</p>", unsafe_allow_html=True)
