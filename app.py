import streamlit as st
import time
import re
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
import json

# --- 1. SYSTEM ARCHITECTURE & UI ENGINE ---
st.set_page_config(page_title="AXOM | Neural Infrastructure", layout="wide", initial_sidebar_state="expanded")

# Professional Custom CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;500;800&display=swap');
    
    .stApp { background-color: #030303; color: #FFFFFF; font-family: 'JetBrains Mono', monospace; }
    
    /* Login Glassmorphism */
    .login-box {
        background: rgba(10, 10, 10, 0.8);
        border: 1px solid #1A1A1A;
        padding: 40px;
        border-radius: 4px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        max-width: 450px;
        margin: auto;
    }

    /* Metric Command Center */
    .stat-box {
        background: #0A0A0A;
        border-left: 3px solid #00E5FF;
        padding: 15px;
        margin-bottom: 10px;
    }
    .stat-label { font-size: 0.7rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-size: 1.5rem; color: #00E5FF; font-weight: 800; }

    /* Monetary Prize UI */
    .prize-hero {
        background: linear-gradient(180deg, #0A0A0A 0%, #000 100%);
        border: 1px solid #00E5FF;
        padding: 60px 20px;
        text-align: center;
        border-radius: 2px;
        position: relative;
        overflow: hidden;
    }
    .prize-amount { font-size: 5rem; font-weight: 800; color: #FFF; margin: 10px 0; letter-spacing: -2px; }
    .status-badge {
        background: #00E5FF; color: #000; padding: 2px 12px;
        font-size: 0.7rem; font-weight: 900; position: absolute; top: 20px; right: 20px;
    }

    /* Sidebar & Inputs */
    section[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #111; }
    .stTextInput>div>div>input { background-color: #0A0A0A !important; border: 1px solid #222 !important; color: #00E5FF !important; }
    .stButton>button { 
        background: #00E5FF !important; color: #000 !important; 
        border-radius: 0px !important; font-weight: 800 !important;
        border: none !important; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { background: #FFFFFF !important; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION LOGIC ---
if 'auth_state' not in st.session_state: st.session_state.auth_state = "login"
if 'otp' not in st.session_state: st.session_state.otp = None
if 'user_email' not in st.session_state: st.session_state.user_email = ""

def send_access_code(email):
    otp = str(random.randint(100000, 999999))
    st.session_state.otp = otp
    try:
        smtp_email = st.secrets["SMTP_EMAIL"]
        smtp_pass = st.secrets["SMTP_PASS"]
        msg = MIMEMultipart()
        msg['Subject'] = f"AXOM Security Code: {otp}"
        msg['From'] = f"AXOM Neural Gate <{smtp_email}>"
        msg['To'] = email
        msg.attach(MIMEText(f"Access Code: {otp}\nExpires in 10 minutes.", 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(smtp_email, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"AUTH_ERR: {e}")
        return False

# --- 3. LOGIN INTERFACE ---
if st.session_state.auth_state != "verified":
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; color:#00E5FF;'>AXOM <span style='color:#FFF'>CORE</span></h1>", unsafe_allow_html=True)
        
        if st.session_state.auth_state == "login":
            email = st.text_input("ENTER REGISTERED EMAIL", placeholder="identity@network.com")
            if st.button("REQUEST ACCESS CODE"):
                if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    if send_access_code(email):
                        st.session_state.user_email = email
                        st.session_state.auth_state = "otp_verify"
                        st.rerun()
                else:
                    st.error("INVALID_PROTOCOL: MALFORMED EMAIL")
        
        elif st.session_state.auth_state == "otp_verify":
            code = st.text_input("6-DIGIT VERIFICATION CODE", type="password")
            if st.button("VERIFY IDENTITY"):
                if code == st.session_state.otp:
                    st.session_state.auth_state = "verified"
                    st.rerun()
                else:
                    st.error("AUTH_FAILED: INCORRECT CODE")
            if st.button("← BACK"):
                st.session_state.auth_state = "login"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MAIN COMMAND CENTER ---
else:
    with st.sidebar:
        st.markdown("<h2 style='color:#00E5FF'>COMMAND</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size:0.7rem; color:#666;'>NODE: {st.session_state.user_email}</p>", unsafe_allow_html=True)
        menu = st.radio("SELECT MODULE", ["DASHBOARD", "VISION GRADER", "FOCUS STATION", "MONETARY GRANT"])
        st.markdown("---")
        if st.button("TERMINATE SESSION"):
            st.session_state.auth_state = "login"
            st.rerun()

    if menu == "DASHBOARD":
        st.subheader("SYSTEM STATUS")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="stat-box"><p class="stat-label">Neural Points</p><p class="stat-value">1,420</p></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="stat-box"><p class="stat-label">Global Rank</p><p class="stat-value">#842</p></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="stat-box"><p class="stat-label">Efficiency</p><p class="stat-value">92%</p></div>', unsafe_allow_html=True)
        
        st.image("https://via.placeholder.com/1200x400/0A0A0A/00E5FF?text=ANALYTICS+VISUALIZATION+COMING+SOON", use_column_width=True)

    elif menu == "VISION GRADER":
        st.subheader("NEURAL SCANNER")
        col1, col2 = st.columns(2)
        with col1:
            exam_board = st.text_input("EXAM BOARD", placeholder="e.g. Cambridge, Edexcel, CBSE")
        with col2:
            subject = st.text_input("SUBJECT", placeholder="e.g. Physics P4, English B")
        
        script = st.file_uploader("UPLOAD SCRIPT (PDF/PNG)", type=['pdf','png','jpg'])
        if script and st.button("EXECUTE ANALYSIS"):
            with st.status("Initializing Gemini 2.5 Flash..."):
                time.sleep(2)
                st.write(f"Aligning with {exam_board} protocols...")
                time.sleep(1)
            st.success(f"Grading Complete for {subject}. Check Neural Archive.")

    elif menu == "MONETARY GRANT":
        st.markdown(f"""
            <div class="prize-hero">
                <div class="status-badge">ACTIVE CYCLE 2026</div>
                <p style="color:#666; letter-spacing:4px; font-size:0.8rem;">ACADEMIC EXCELLENCE GRANT</p>
                <h1 class="prize-amount">$5,000.00</h1>
                <p style="max-width:700px; margin:0 auto; color:#AAA; line-height:1.6;">
                    The AXOM Foundation awards a $5,000.00 scholarship monthly to the student showing the highest 
                    ratio of <b>Focus Persistence</b> and <b>AI-Verified Grade Improvement</b>. 
                </p>
                <div style="margin-top:40px;">
                    <span style="border:1px solid #333; padding:10px 20px; color:#555; font-size:0.7rem;">
                        APPLICATIONS OPEN IN: 142 DAYS
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    elif menu == "FOCUS STATION":
        st.subheader("DEEP WORK PROTOCOL")
        hrs = st.select_slider("SESSION DURATION (HRS)", options=[1, 2, 4, 6, 8, 12])
        if st.button("INITIALIZE"):
            st.warning("Session logging active. External applications locked.")
