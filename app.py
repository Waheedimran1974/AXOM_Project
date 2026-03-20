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
# 1. ENTERPRISE CONFIG & SYSTEM PREFS
# ==========================================
# ⚠️ ADMIN: CONFIG YOUR EMAIL ROUTING HERE ⚠️
SENDER_EMAIL = "dearhussain12@gmail.com" 
APP_PASSWORD = "drjlaihoavuaktnm" 
GENAI_API_KEY = "YOUR_GEMINI_API_KEY"

genai.configure(api_key=GENAI_API_KEY)

st.set_page_config(page_title="AXOM | Neural Terminal", layout="wide", initial_sidebar_state="collapsed")

def inject_styles():
    st.markdown("""
        <style>
        .stApp { background-color: #fafafa; color: #111827; font-family: 'Inter', sans-serif; }
        
        /* Auth Card Styling */
        .auth-card {
            max-width: 400px; margin: 80px auto; padding: 40px;
            background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); text-align: center;
        }
        .brand-text { font-size: 2.8rem; font-weight: 800; color: #111827; letter-spacing: -1px; margin-bottom: 5px; }
        
        /* Interactive Buttons */
        .stButton>button {
            width: 100%; background-color: #111827 !important; color: #ffffff !important;
            border: none !important; border-radius: 8px !important; padding: 14px !important;
            font-weight: 600 !important; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .stButton>button:hover { background-color: #374151 !important; transform: translateY(-1px); }
        
        /* Clean Inputs */
        input { border-radius: 8px !important; border: 1px solid #d1d5db !important; padding: 12px !important; }
        
        /* Header & Dashboard */
        .header-bar {
            display: flex; justify-content: space-between; align-items: center;
            padding: 15px 40px; background: #ffffff; border-bottom: 1px solid #e5e7eb;
            margin-bottom: 30px;
        }
        .zoom-container {
            width:100%; height:850px; overflow:scroll; border: 1px solid #e5e7eb; 
            background: #f3f4f6; border-radius: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CORE UTILITIES (EMAIL & DRAWING)
# ==========================================
def send_otp(target_email, code):
    msg = MIMEText(f"Your AXOM security code is: {code}\n\nValid for 10 minutes.")
    msg['Subject'] = 'AXOM Security Access'
    msg['From'] = f"AXOM Admin <{SENDER_EMAIL}>"
    msg['To'] = target_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except: return False

def draw_marks(draw, coords, note, w, h, cat):
    # Professional Palette
    colors = {"error": "#dc2626", "correct": "#16a34a", "info": "#2563eb"}
    color = colors.get(cat.lower(), "#dc2626")
    
    ymin, xmin, ymax, xmax = coords
    l, t, r, b = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000

    if cat.lower() == "correct":
        draw.line([l, (t+b)/2, (l+r)/2, b, r, t-20], fill=color, width=8)
    else:
        draw.rectangle([l, t, r, b], outline=color, width=5)

    try:
        font = ImageFont.truetype("ibrahim_handwriting.ttf", 55)
    except:
        font = ImageFont.load_default()

    # Apply Ink Shadow
    draw.text((r + 17, t + 2), note, fill="#00000033", font=font)
    draw.text((r + 15, t), note, fill=color, font=font)

# ==========================================
# 3. AUTHENTICATION STATE MACHINE
# ==========================================
if 'status' not in st.session_state: st.session_state.status = "OUT" # OUT, SENT, IN
if 'user' not in st.session_state: st.session_state.user = ""
if 'otp' not in st.session_state: st.session_state.otp = ""

inject_styles()

if st.session_state.status != "IN":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="brand-text">AXOM</div>', unsafe_allow_html=True)
        st.markdown('<p style="color:#6b7280; margin-bottom:30px;">Professional Neural Grading</p>', unsafe_allow_html=True)

        if st.session_state.status == "OUT":
            email_in = st.text_input("Email Address", placeholder="teacher@school.com")
            if st.button("Continue"):
                if "@" in email_in:
                    code = str(random.randint(100000, 999999))
                    st.session_state.otp = code
                    st.session_state.user = email_in
                    with st.spinner("Routing security code..."):
                        if send_otp(email_in, code):
                            st.session_state.status = "SENT"
                            st.rerun()
                        else: st.error("Email server offline. Check credentials.")
                else: st.error("Invalid email format.")

        elif st.session_state.status == "SENT":
            st.info(f"Code sent to {st.session_state.user}")
            code_in = st.text_input("6-Digit Code", max_chars=6)
            if st.button("Verify Identity"):
                if code_in == st.session_state.otp:
                    st.session_state.status = "IN"
                    st.rerun()
                else: st.error("Invalid code.")
            if st.button("← Back", key="back"):
                st.session_state.status = "OUT"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. DASHBOARD & VISION ENGINE
# ==========================================
st.markdown(f"""
    <div class="header-bar">
        <h3 style="margin:0; font-weight:800;">AXOM</h3>
        <div style="text-align:right; font-size:0.8rem; color:#6b7280;">
            SESSION: {st.session_state.user} <br> <span style="color:#16a34a;">● SECURE</span>
        </div>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### PROTOCOLS")
    mode = st.radio("Select Action", ["Paper Checker", "AI Analytics", "Settings"])
    st.divider()
    if st.button("Log Out"):
        st.session_state.clear()
        st.rerun()

if mode == "Paper Checker":
    st.markdown("## Evaluation Gateway")
    file = st.file_uploader("Upload Script (PDF/JPG)", type=['pdf', 'jpg', 'png'])
    
    if file:
        col1, col2 = st.columns([2,1])
        with col2:
            zoom = st.select_slider("View Quality", options=["Standard", "Detailed", "Ultra-HD"])
            px_val = {"Standard": 1000, "Detailed": 1600, "Ultra-HD": 2400}[zoom]
        
        if st.button("Begin Neural Analysis", type="primary"):
            with st.spinner("AI Examiner Processing..."):
                # Image Conversion
                if file.type == "application/pdf":
                    img = convert_from_bytes(file.getvalue())[0].convert("RGB")
                else:
                    img = Image.open(file).convert("RGB")
                
                w, h = img.size
                draw = ImageDraw.Draw(img)

                # AI Inference
                model = genai.GenerativeModel('gemini-2.0-flash')
                prompt = "Mark this paper. Format: [ymin, xmin, ymax, xmax] | category (correct/error) | note"
                resp = model.generate_content([prompt, img])
                
                # Render Marks
                for line in resp.text.split('\n'):
                    if '|' in line:
                        m = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', line)
                        if m:
                            coords = [int(x) for x in m.groups()]
                            draw_marks(draw, coords, line.split('|')[2].strip(), w, h, line.split('|')[1].strip())

                # Display Results
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode()
                st.markdown(f'<div class="zoom-container"><img src="data:image/png;base64,{img_b64}" style="width:{px_val}px;"></div>', unsafe_allow_html=True)
