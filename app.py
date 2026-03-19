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
# 1. SYSTEM CONFIGURATION & THEME
# ==========================================
st.set_page_config(page_title="AXOM Global Systems", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .welcome-note { 
        font-size: 2rem; font-weight: bold; color: #D4AF37; text-align: center; 
        padding: 40px; text-transform: uppercase; letter-spacing: 2px;
    }
    .portal-header { 
        background-color: #001F3F; padding: 20px; border-left: 10px solid #D4AF37; margin-bottom: 20px; 
    }
    .stButton>button { 
        border-radius: 0px; font-weight: bold; height: 60px; transition: 0.3s; 
        text-transform: uppercase; border: 1px solid #1e293b;
    }
    .stButton>button:hover { border: 1px solid #D4AF37; color: #D4AF37; background-color: #001F3F; }
    </style>
    """, unsafe_allow_html=True)

# --- Session State ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'board' not in st.session_state: st.session_state.board = None
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "DASHBOARD"

# ==========================================
# 2. CORE UTILITIES
# ==========================================
def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9_.+-]+@(gmail\.com|yahoo\.com|icloud\.com|apple\.com)$", email)

def scale_coords(coords, w, h):
    """Converts Gemini [ymin, xmin, ymax, xmax] (0-1000) to pixel coordinates."""
    return [
        int(coords[1] * w / 1000), # xmin
        int(coords[0] * h / 1000), # ymin
        int(coords[3] * w / 1000), # xmax
        int(coords[2] * h / 1000)  # ymax
    ]

# ==========================================
# 3. LOGIN & ONBOARDING
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>AXOM TERMINAL ACCESS</h1>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        email = st.text_input("AUTHORIZED EMAIL")
        name = st.text_input("FULL NAME")
        if st.button("AUTHENTICATE", use_container_width=True):
            if is_valid_email(email) and name:
                st.session_state.logged_in, st.session_state.user_name = True, name.upper()
                st.rerun()
    st.stop()

if st.session_state.board is None:
    st.markdown(f"<div class='welcome-note'>WELCOME TO AXOM {st.session_state.user_name}</div>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.session_state.board = st.selectbox("BOARD", ["CAMBRIDGE", "EDEXCEL", "AQA", "IB"])
        st.session_state.subject = st.selectbox("SUBJECT", ["ENGLISH", "MATH", "PHYSICS", "BIOLOGY"])
        if st.button("INITIALIZE"): st.rerun()
    st.stop()

# ==========================================
# 4. MAIN DASHBOARD GRID
# ==========================================
st.markdown(f"<div class='portal-header'><h2 style='margin:0; color: white;'>AXOM: {st.session_state.menu_choice}</h2></div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("PAST PAPER CHECKER", use_container_width=True): st.session_state.menu_choice = "PAPER CHECKER"
    if st.button("CLASSROOMS (AXON)", use_container_width=True): st.session_state.menu_choice = "CLASSROOMS"
with col2:
    if st.button("REPORTS", use_container_width=True): st.session_state.menu_choice = "REPORTS"
    if st.button("INTERACTIVE AI", use_container_width=True): st.session_state.menu_choice = "AI CHAT"
with col3:
    if st.button("AI REVISION (VOICE)", use_container_width=True): st.session_state.menu_choice = "AI REVISION"
    if st.button("SETTINGS", use_container_width=True): st.session_state.menu_choice = "SETTINGS"

st.divider()

# ==========================================
# 5. MODULE: PAPER CHECKER (THE RED PEN)
# ==========================================
current_view = st.session_state.menu_choice

if current_view == "PAPER CHECKER":
    st.markdown("<h2 style='color: #D4AF37;'>HUMAN-STYLE VISUAL MARKING</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("UPLOAD SCRIPT", type=['pdf', 'jpg', 'png'])

    if uploaded_file:
        if st.button("EXECUTE RED-PEN MARKING"):
            with st.spinner("EXAMINER IS CIRCLING ERRORS..."):
                # 1. Load Image
                if uploaded_file.type == "application/pdf":
                    images = convert_from_bytes(uploaded_file.getvalue())
                    img = images[0].convert("RGB")
                else:
                    img = Image.open(uploaded_file).convert("RGB")
                
                w, h = img.size
                draw = ImageDraw.Draw(img)

                # 2. AI Analysis with Bounding Boxes
                model = genai.GenerativeModel('gemini-2.0-flash')
                prompt = """Identify technical errors in this student script. 
                For each error, provide the coordinates in [ymin, xmin, ymax, xmax] format (0-1000) 
                and a short correction note. Return strictly as: [coords] | Note"""
                
                response = model.generate_content([prompt, img])
                
                # 3. Parse and Draw
                lines = response.text.split('\n')
                for line in lines:
                    if '|' in line:
                        try:
                            # Extracting [ymin, xmin, ymax, xmax]
                            coord_match = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', line)
                            if coord_match:
                                raw_coords = [int(x) for x in coord_match.groups()]
                                p_coords = scale_coords(raw_coords, w, h)
                                note = line.split('|')[1].strip()
                                
                                # Draw Red Circle
                                draw.ellipse(p_coords, outline="red", width=8)
                                # Draw Note next to circle
                                draw.text((p_coords[2]+10, p_coords[1]), note, fill="red")
                        except:
                            continue
                
                st.image(img, caption="AXOM SENIOR EXAMINER: MARKED SCRIPT", use_container_width=True)
                st.markdown(f"### EXAMINER SUMMARY\n{response.text}")

elif current_view == "CLASSROOMS":
    st.components.v1.iframe("https://axom.daily.co/Main-Classroom", height=700)

elif current_view == "SETTINGS":
    if st.button("RESET SYSTEM"):
        st.session_state.clear()
        st.rerun()

else:
    st.warning(f"{current_view} MODULE IS ONLINE. AWAITING DATA.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>COPYRIGHT 2026 AXOM GLOBAL</p>", unsafe_allow_html=True)
