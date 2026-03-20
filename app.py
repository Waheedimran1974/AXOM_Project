import streamlit as st
import google.generativeai as genai
import re
import io
import base64
import random
import smtplib
from email.mime.text import MIMEText
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes
import streamlit as st
import pandas as pd
import os

# ==========================================
# 1. SECURE CONFIGURATION
# ==========================================
try:
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
    genai.configure(api_key=GENAI_API_KEY)
except Exception:
    st.error("Secrets not configured in Streamlit Cloud.")
    st.stop()

# ==========================================
# 2. GLASSMORPHISM UI TEMPLATE
# ==========================================
st.set_page_config(page_title="AXOM | Neural", layout="wide", initial_sidebar_state="collapsed")

def apply_glass_theme():
    st.markdown("""
        <style>
        /* Modern Gradient Background */
        .stApp {
            background: radial-gradient(circle at top right, #f8fafc, #e2e8f0);
            color: #1e293b;
            font-family: 'Inter', sans-serif;
        }
        
        /* Glass Effect Card */
        .glass-card {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 24px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
            margin: 40px auto;
            max-width: 450px;
            text-align: center;
        }

        .brand {
            font-size: 3.5rem;
            font-weight: 900;
            background: linear-gradient(to right, #0f172a, #334155);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }

        /* Modernized Buttons */
        .stButton>button {
            background: #0f172a !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 500 !important;
            border: none !important;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton>button:hover {
            background: #334155 !important;
            transform: scale(1.02);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }

        /* Hide Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. BACKEND ENGINES
# ==========================================
def send_otp_mail(email, code):
    msg = MIMEText(f"Your AXOM Access Code: {code}")
    msg['Subject'] = 'AXOM Security'
    msg['From'] = f"AXOM <{SENDER_EMAIL}>"
    msg['To'] = email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except: return False

def apply_neural_overlay(draw, coords, note, w, h, cat):
    color = "#059669" if "correct" in cat.lower() else "#e11d48"
    ymin, xmin, ymax, xmax = coords
    l, t, r, b = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000
    
    if "correct" in cat.lower():
        draw.line([l, (t+b)/2, (l+r)/2, b, r, t-20], fill=color, width=7)
    else:
        draw.rectangle([l, t, r, b], outline=color, width=4)

    try: font = ImageFont.truetype("ibrahim_handwriting.ttf", 55)
    except: font = ImageFont.load_default()
    draw.text((r + 15, t), note, fill=color, font=font)

# ==========================================
# 4. APP LOGIC & ROUTING
# ==========================================
if 'view' not in st.session_state: st.session_state.view = "LOGIN"
if 'user_mail' not in st.session_state: st.session_state.user_mail = ""
if 'session_otp' not in st.session_state: st.session_state.session_otp = ""

apply_glass_theme()

# --- LOGIN SCREEN ---
if st.session_state.view != "DASHBOARD":
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h1 class="brand">AXOM</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color:#64748b; margin-bottom:2rem;">Intelligence for Educators</p>', unsafe_allow_html=True)

        if st.session_state.view == "LOGIN":
            u_email = st.text_input("Institutional Email", placeholder="name@school.com", label_visibility="collapsed")
            if st.button("Request Access"):
                if "@" in u_email:
                    otp_code = str(random.randint(100000, 999999))
                    st.session_state.session_otp = otp_code
                    st.session_state.user_mail = u_email
                    if send_otp_mail(u_email, otp_code):
                        st.session_state.view = "OTP_VERIFY"
                        st.rerun()
                else: st.error("Please enter a valid email.")

        elif st.session_state.view == "OTP_VERIFY":
            st.write(f"Verifying {st.session_state.user_mail}...")
            otp_in = st.text_input("Enter 6-Digit Code", max_chars=6, label_visibility="collapsed")
            if st.button("Authenticate"):
                if otp_in == st.session_state.session_otp:
                    st.session_state.view = "DASHBOARD"
                    st.rerun()
                else: st.error("Incorrect code.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- DASHBOARD SCREEN ---
st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; padding: 20px 5%;">
        <h2 style="margin:0; font-weight:900; letter-spacing:-1px;">AXOM.ai</h2>
        <div style="background:white; padding:8px 16px; border-radius:50px; border:1px solid #e2e8f0; font-size:0.8rem;">
            {st.session_state.user_mail}
        </div>
    </div>
""", unsafe_allow_html=True)

# Main Interaction Area
col_left, col_right = st.columns([1, 3])

with col_left:
    st.markdown("### Control Panel")
    file = st.file_uploader("Drop script here", type=['pdf', 'jpg', 'png'])
    quality = st.select_slider("Marking Detail", options=["Draft", "Standard", "HD"], value="Standard")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

with col_right:
    if file:
        if st.button("Run AI Examination", type="primary"):
            with st.spinner("Analyzing handwriting..."):
                if file.type == "application/pdf":
                    img = convert_from_bytes(file.getvalue())[0].convert("RGB")
                else:
                    img = Image.open(file).convert("RGB")
                
                w, h = img.size
                draw = ImageDraw.Draw(img)
                
                model = genai.GenerativeModel('gemini-2.0-flash')
                prompt = "Mark this exam paper. Format: [ymin, xmin, ymax, xmax] | category (correct/error) | note"
                
                try:
                    resp = model.generate_content([prompt, img])
                    for line in resp.text.split('\n'):
                        if '|' in line:
                            m = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', line)
                            if m:
                                apply_neural_overlay(draw, [int(x) for x in m.groups()], line.split('|')[2].strip(), w, h, line.split('|')[1].strip())
                    
                    st.image(img, use_container_width=True)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
    else:
        st.info("Please upload a student script to begin.")
        # --- THE PERMANENT MEMORY SYSTEM ---
HISTORY_FILE = "axom_history.csv"

def save_to_history(student_email, error, correction):
    # Create a new row of data
    new_data = pd.DataFrame([[student_email, error, correction]], 
                            columns=["Email", "Error", "Correction"])
    
    # If the file exists, add to it. If not, create it.
    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE)
        history_df = pd.concat([history_df, new_data], ignore_index=True)
    else:
        history_df = new_data
    
    # Save it back to the system
    history_df.to_csv(HISTORY_FILE, index=False)

# --- THE FLASHCARD INTERFACE ---
def show_flashcards(email):
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        user_history = df[df['Email'] == email]
        
        if not user_history.empty:
            st.subheader("🗂️ Ibrahim's Revision Cards")
            for index, row in user_history.tail(5).iterrows(): # Show last 5
                with st.container():
                    st.info(f"**Mistake:** {row['Error']}")
                    st.success(f"**Correction:** {row['Correction']}")
        else:
            st.write("No history found for this user yet.")
