import streamlit as st
import google.generativeai as genai
import re
import io
import base64
import time
import random
import smtplib
from email.mime.text import MIMEText
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. SECURE CONFIGURATION (PULLS FROM SECRETS)
# ==========================================
try:
    SENDER_EMAIL = st.secrets["SENDER_EMAIL"]
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
    GENAI_API_KEY = st.secrets["GENAI_API_KEY"]
    
    genai.configure(api_key=GENAI_API_KEY)
except Exception as e:
    st.error("⚠️ SYSTEM CONFIGURATION MISSING: Please add SENDER_EMAIL, APP_PASSWORD, and GENAI_API_KEY to your Streamlit Secrets.")
    st.stop()

# ==========================================
# 2. UI DESIGN (ENTERPRISE MINIMALIST)
# ==========================================
st.set_page_config(page_title="AXOM | Neural Terminal", layout="wide", initial_sidebar_state="collapsed")

def inject_enterprise_styles():
    st.markdown("""
        <style>
        .stApp { background-color: #fafafa; color: #111827; font-family: 'Inter', sans-serif; }
        
        /* Auth Card */
        .auth-card {
            max-width: 400px; margin: 80px auto; padding: 40px;
            background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05); text-align: center;
        }
        .brand-text { font-size: 2.8rem; font-weight: 800; color: #111827; letter-spacing: -1px; margin-bottom: 5px; }
        
        /* Buttons */
        .stButton>button {
            width: 100%; background-color: #111827 !important; color: #ffffff !important;
            border: none !important; border-radius: 8px !important; padding: 14px !important;
            font-weight: 600 !important; transition: 0.2s;
        }
        .stButton>button:hover { background-color: #374151 !important; transform: translateY(-1px); }
        
        /* Inputs */
        input { border-radius: 8px !important; border: 1px solid #d1d5db !important; padding: 12px !important; }
        
        /* Dashboard */
        .header-bar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 40px; background: #ffffff; border-bottom: 1px solid #e5e7eb; margin-bottom: 30px;
        }
        .zoom-container {
            width:100%; height:850px; overflow:scroll; border: 1px solid #e5e7eb; 
            background: #f3f4f6; border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. UTILITY FUNCTIONS
# ==========================================
def send_otp(target_email, code):
    msg = MIMEText(f"Your AXOM secure login code is: {code}\n\nDo not share this code.")
    msg['Subject'] = 'AXOM Security Code'
    msg['From'] = f"AXOM Admin <{SENDER_EMAIL}>"
    msg['To'] = target_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except: return False

def draw_neural_marks(draw, coords, note, w, h, cat):
    # Professional marking colors
    color = "#16a34a" if "correct" in cat.lower() else "#dc2626"
    ymin, xmin, ymax, xmax = coords
    l, t, r, b = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000

    # Draw Logic
    if "correct" in cat.lower():
        draw.line([l, (t+b)/2, (l+r)/2, b, r, t-20], fill=color, width=8)
    else:
        draw.rectangle([l, t, r, b], outline=color, width=5)

    # Handwriting Placement
    try:
        font = ImageFont.truetype("ibrahim_handwriting.ttf", 55)
    except:
        font = ImageFont.load_default()
    
    # Text shadow for 'ink' look
    draw.text((r + 17, t + 2), note, fill="#00000033", font=font)
    draw.text((r + 15, t), note, fill=color, font=font)

# ==========================================
# 4. AUTHENTICATION FLOW
# ==========================================
if 'status' not in st.session_state: st.session_state.status = "OUT"
if 'user' not in st.session_state: st.session_state.user = ""
if 'otp' not in st.session_state: st.session_state.otp = ""

inject_enterprise_styles()

if st.session_state.status != "IN":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="brand-text">AXOM</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#6b7280; margin-bottom:30px;">ENTERPRISE GRADING TERMINAL</p>', unsafe_allow_html=True)

        if st.session_state.status == "OUT":
            email_in = st.text_input("Work Email", placeholder="teacher@school.edu")
            if st.button("Continue"):
                if "@" in email_in and "." in email_in:
                    code =
