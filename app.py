import streamlit as st
import time
import re
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. GLOBAL STYLING (THE AXOM CORE UI) ---
st.set_page_config(page_title="AXOM | Neural Infrastructure", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* Center Login Box */
    .auth-card {
        background: rgba(15, 15, 15, 0.95);
        border: 1px solid #1A1A1A;
        padding: 50px;
        border-radius: 8px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8);
        max-width: 500px;
        margin: auto;
        text-align: center;
    }

    /* Welcome Header */
    .welcome-text {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #FFFFFF, #00E5FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }

    /* Dashboard Metrics */
    .metric-container {
        display: flex;
        gap: 20px;
        margin: 25px 0;
    }
    .metric-card {
        flex: 1;
        background: #0A0A0A;
        border: 1px solid #111;
        padding: 20px;
        border-radius: 4px;
        border-left: 2px solid #00E5FF;
    }

    /* Inputs & Buttons */
    .stTextInput>div>div>input {
        background-color: #0A0A0A !important;
        border: 1px solid #222 !important;
        color: #00E5FF !important;
        height: 50px;
    }
    .stButton>button {
        background: #00E5FF !important;
        color: #000 !important;
        font-weight: 800 !important;
        border-radius: 2px !important;
        height: 50px;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE & SECURITY ---
if 'step' not in st.session_state: st.session_state.step = "email_gate"
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'otp_code' not in st.session_state: st.session_state.otp_code = None

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    st.session_state.otp_code = otp
    try:
        # Securely pulling from Streamlit Secrets
        msg = MIMEMultipart()
        msg['Subject'] = f"AXOM Access: {otp}"
        msg['From'] = f"AXOM System <{st.secrets['SMTP_EMAIL']}>"
        msg['To'] = email
        msg.attach(MIMEText(f"Your secure access code is: {otp}", 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            server.send_message(msg)
        return True
    except: return False

# --- 3. THE NAVIGATION FLOW ---

# STEP 1: EMAIL LOGIN
if st.session_state.step == "email_gate":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("<h1 style='color:#00E5FF; margin-bottom:0;'>AXOM</h1><p style='color:#666;'>NEURAL GATEWAY</p>", unsafe_allow_html=True)
        email = st.text_input("Enter Email", placeholder="user@domain.com")
        if st.button("Generate Access Code"):
            if "@" in email:
                with st.spinner("Encrypting..."):
                    if send_otp(email):
                        st.session_state.step = "otp_verify"
                        st.rerun()
            else: st.error("Invalid Email Format")
        st.markdown('</div>', unsafe_allow_html=True)

# STEP 2: OTP VERIFICATION
elif st.session_state.step == "otp_verify":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.write("Check your inbox for the 6-digit code.")
        code = st.text_input("Access Code", type="password")
        if st.button("Verify Identity"):
            if code == st.session_state.otp_code:
                st.session_state.step = "name_setup"
                st.rerun()
            else: st.error("Authentication Failed")
        st.markdown('</div>', unsafe_allow_html=True)

# STEP 3: NAME REGISTRATION
elif st.session_state.step == "name_setup":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("<h3>IDENTIFY YOURSELF</h3>", unsafe_allow_html=True)
        name = st.text_input("Full Name / Alias", placeholder="e.g. Abdullah H.")
        if st.button("Initialize Dashboard"):
            if len(name) > 1:
                st.session_state.user_name = name
                st.session_state.step = "dashboard"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# STEP 4: THE MAIN DASHBOARD
elif st.session_state.step == "dashboard":
    # Sidebar
    with st.sidebar:
        st.markdown(f"<h2 style='color:#00E5FF'>AXOM v1.0</h2>", unsafe_allow_html=True)
        menu = st.radio("System Menu", ["Overview", "Vision Grader", "Monetary Grant"])
        if st.button("Sign Out"):
            st.session_state.step = "email_gate"
            st.rerun()

    # Main Content
    st.markdown(f"<div class='welcome-text'>Welcome, {st.session_state.user_name}</div>", unsafe_allow_html=True)
    st.write("System Status: <span style='color:#00E5FF'>Operational</span>", unsafe_allow_html=True)

    if menu == "Overview":
        st.markdown("""
            <div class="metric-container">
                <div class="metric-card">
                    <p style="color:#666; font-size:12px; margin:0;">POINTS</p>
                    <p style="color:#00E5FF; font-size:24px; font-weight:bold; margin:0;">1,420</p>
                </div>
                <div class="metric-card">
                    <p style="color:#666; font-size:12px; margin:0;">ACCURACY</p>
                    <p style="color:#00E5FF; font-size:24px; font-weight:bold; margin:0;">88.4%</p>
                </div>
                <div class="metric-card">
                    <p style="color:#666; font-size:12px; margin:0;">RANK</p>
                    <p style="color:#00E5FF; font-size:24px; font-weight:bold; margin:0;">#42</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.subheader("Recent Activity")
        st.info("No neural scans performed in the last 24 hours.")

    elif menu == "Monetary Grant":
        st.markdown("""
            <div style="background:#0A0A0A; border:1px solid #00E5FF; padding:60px; text-align:center; border-radius:4px;">
                <p style="color:#00E5FF; font-weight:bold; letter-spacing:2px;">ANNUAL EXCELLENCE GRANT</p>
                <h1 style="font-size:80px; margin:10px 0;">$5,000.00</h1>
                <p style="color:#666;">COMING SOON: RECRUITMENT CYCLE 2026</p>
            </div>
        """, unsafe_allow_html=True)
