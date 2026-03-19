import streamlit as st
import google.generativeai as genai
import re
import time
import io
import base64
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. CORE CONFIGURATION
# ==========================================
st.set_page_config(page_title="AXOM Global Terminal", layout="wide")

# Custom Dark Theme with Gold Accents
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .portal-header { background-color: #001F3F; padding: 25px; border-left: 10px solid #D4AF37; margin-bottom: 25px; }
    .welcome-note { font-size: 2.2rem; font-weight: bold; color: #D4AF37; text-align: center; padding: 30px; text-transform: uppercase; }
    .stButton>button { border-radius: 0px; height: 65px; font-weight: bold; text-transform: uppercase; transition: 0.4s; }
    .stButton>button:hover { border: 1px solid #D4AF37; color: #D4AF37; background-color: #001F3F; }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Logic ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'board' not in st.session_state: st.session_state.board = None
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "DASHBOARD"

# ==========================================
# 2. UTILITY FUNCTIONS
# ==========================================
def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9_.+-]+@(gmail\.com|googlemail\.com|yahoo\.com|icloud\.com|apple\.com)$", email)

def draw_correction(draw, coords, note, w, h):
    """Draws a professional red circle and handwritten-style note."""
    # Convert Gemini 0-1000 scale to pixels
    ymin, xmin, ymax, xmax = coords
    left = xmin * w / 1000
    top = ymin * h / 1000
    right = xmax * w / 1000
    bottom = ymax * h / 1000
    
    # Draw Red Circle
    draw.ellipse([left, top, right, bottom], outline="red", width=6)
    
    # Draw Note Text
    try:
        # If running locally, you might need a path to a .ttf file
        font = ImageFont.load_default() 
    except:
        font = None
    draw.text((right + 10, top), note, fill="red", font=font)

# ==========================================
# 3. ACCESS CONTROL (LOGIN & BOARD)
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>AXOM TERMINAL ACCESS</h1>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        email = st.text_input("AUTHORIZED EMAIL (GOOGLE/YAHOO/APPLE)")
        name = st.text_input("FULL NAME")
        if st.button("AUTHENTICATE SYSTEM", use_container_width=True):
            if is_valid_email(email) and name:
                st.session_state.logged_in = True
                st.session_state.user_name = name.upper()
                st.rerun()
            else:
                st.error("ACCESS DENIED: PLEASE USE A VERIFIED EMAIL DOMAIN.")
    st.stop()

if st.session_state.board is None:
    st.markdown(f"<div class='welcome-note'>WELCOME TO AXOM {st.session_state.user_name}</div>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        st.session_state.board = st.selectbox("SELECT BOARD", ["CAMBRIDGE IGCSE/A-LEVEL", "EDEXCEL", "OXFORD AQA", "IB"])
        st.session_state.subject = st.selectbox("SELECT SUBJECT", ["ENGLISH", "MATHEMATICS", "PHYSICS", "BIOLOGY", "BUSINESS"])
        if st.button("INITIALIZE DASHBOARD"): st.rerun()
    st.stop()

# ==========================================
# 4. COMMAND CENTER (12-BUTTON GRID)
# ==========================================
st.markdown(f"""
    <div class='portal-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h2 style='margin:0; color: white;'>AXOM COMMAND: {st.session_state.menu_choice}</h2>
            <div style='text-align: right;'>
                <span style='color: #D4AF37; font-weight: bold;'>{st.session_state.user_name}</span><br>
                <span style='font-size: 0.8rem;'>{st.session_state.board} | {st.session_state.subject}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📄 PAPER CHECKER", use_container_width=True): st.session_state.menu_choice = "PAPER CHECKER"
    if st.button("📅 SCHEDULES", use_container_width=True): st.session_state.menu_choice = "SCHEDULES"
    if st.button("🏫 CLASSROOMS (AXON)", use_container_width=True): st.session_state.menu_choice = "CLASSROOMS"
    if st.button("🏆 LEADERBOARD", use_container_width=True): st.session_state.menu_choice = "LEADERBOARD"

with col2:
    if st.button("📜 HISTORY", use_container_width=True): st.session_state.menu_choice = "HISTORY"
    if st.button("📊 REPORTS", use_container_width=True): st.session_state.menu_choice = "REPORTS"
    if st.button("🤖 INTERACTIVE AI", use_container_width=True): st.session_state.menu_choice = "AI CHAT"
    if st.button("💳 SUBSCRIPTION", use_container_width=True): st.session_state.menu_choice = "SUBSCRIPTION"

with col3:
    if st.button("⚡ FLASHCARDS", use_container_width=True): st.session_state.menu_choice = "FLASHCARDS"
    if st.button("🗺️ MAP OF REPORT", use_container_width=True): st.session_state.menu_choice = "REPORT MAP"
    if st.button("🎙️ AI REVISION", use_container_width=True): st.session_state.menu_choice = "AI REVISION"
    if st.button("⚙️ SETTINGS", use_container_width=True): st.session_state.menu_choice = "SETTINGS"

st.divider()

# ==========================================
# 5. DYNAMIC MODULES
# ==========================================
view = st.session_state.menu_choice

if view == "PAPER CHECKER":
    st.markdown("<h3 style='color: #D4AF37;'>SENIOR EXAMINER: VISUAL MARKING</h3>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("UPLOAD SCRIPT (PDF/JPG/PNG)", type=['pdf', 'jpg', 'png', 'jpeg'])

    if uploaded_file:
        if st.button("START RED-PEN ANALYSIS"):
            with st.spinner("AI EXAMINER SCANNING PAGE..."):
                try:
                    # 1. Image Conversion
                    if uploaded_file.type == "application/pdf":
                        # Requires poppler-utils in packages.txt
                        images = convert_from_bytes(uploaded_file.getvalue())
                        img = images[0].convert("RGB")
                    else:
                        img = Image.open(uploaded_file).convert("RGB")
                    
                    w, h = img.size
                    draw = ImageDraw.Draw(img)

                    # 2. AI Visual Marking Logic
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    prompt = f"""
                    Identify 3 major technical errors in this {st.session_state.subject} script. 
                    For each error, provide:
                    1. Coordinates in [ymin, xmin, ymax, xmax] (0-1000 scale).
                    2. A short handwritten-style correction note.
                    Return as: [ymin, xmin, ymax, xmax] | Note
                    """
                    
                    response = model.generate_content([prompt, img])
                    
                    # 3. Apply Visual Corrections
                    lines = response.text.split('\n')
                    for line in lines:
                        if '|' in line:
                            match = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', line)
                            if match:
                                coords = [int(x) for x in match.groups()]
                                note = line.split('|')[1].strip()
                                draw_correction(draw, coords, note, w, h)

                    st.image(img, caption="AXOM SENIOR EXAMINER: MARKED SCRIPT", use_container_width=True)
                    st.success("Analysis Complete. View the Red-Pen marks above.")
                
                except Exception as e:
                    st.error(f"SYSTEM ERROR: {e}")
                    st.info("Check if packages.txt with 'poppler-utils' is in your GitHub.")

elif view == "CLASSROOMS":
    # Use your Daily.co Room URL here
    st.components.v1.iframe("https://axom.daily.co/Main-Classroom", height=700)

elif view == "SETTINGS":
    if st.button("CLEAR ALL DATA & SIGN OUT"):
        st.session_state.clear()
        st.rerun()

else:
    st.info(f"The {view} module is ready for configuration.")
