import streamlit as st
import time
import json
import random
import datetime
import io
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes

# --- 1. SYSTEM CONFIGURATION & UI STYLING ---
st.set_page_config(page_title="AXOM | Neural Infrastructure", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* Login & Setup Cards */
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

    /* Subscription Cards */
    .plan-card {
        background: #0A0A0A; border: 1px solid #1A1A1A; padding: 30px; 
        border-radius: 4px; text-align: center; height: 100%; transition: 0.3s;
    }
    .plan-card:hover { border-color: #00E5FF; }
    .price { font-size: 2.2rem; font-weight: 900; color: #00E5FF; margin: 15px 0; }

    /* Revision Hub Alert */
    .gap-card {
        background: rgba(255, 75, 75, 0.05); border-left: 4px solid #FF4B4B;
        padding: 20px; margin-bottom: 15px; border-radius: 2px;
    }

    /* Inputs & Buttons */
    .stTextInput>div>div>input { background-color: #0A0A0A !important; border: 1px solid #222 !important; color: #00E5FF !important; height: 45px; }
    .stButton>button, .stDownloadButton>button {
        background: #00E5FF !important; color: #000 !important;
        font-weight: 800 !important; border-radius: 2px !important;
        height: 45px; border: none !important; width: 100%;
    }
    .stDownloadButton>button { background: #FFFFFF !important; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #000 !important; border-right: 1px solid #111; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE ENGINES (PDF & AUTH) ---
def generate_pdf_report(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 229, 255)
    pdf.cell(200, 20, "AXOM NEURAL PERFORMANCE REPORT", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(200, 10, f"TIMESTAMP: {data['timestamp']} | SUBJECT: {data['subject']}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 40)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 30, f"SCORE: {data['score']}%", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(200, 15, "IDENTIFIED REVISION GAPS:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.set_text_color(50, 50, 50)
    for gap in data['gaps']:
        pdf.multi_cell(0, 10, f"- {gap['topic']}: {gap['issue']}")
    return pdf.output(dest='S').encode('latin-1')

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    st.session_state.otp_code = otp
    try:
        msg = MIMEMultipart()
        msg['Subject'] = f"AXOM Secure Access: {otp}"
        msg['From'] = f"AXOM Gatekeeper <{st.secrets['SMTP_EMAIL']}>"
        msg['To'] = email
        msg.attach(MIMEText(f"Your login code is: {otp}", 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            server.send_message(msg)
        return True
    except: return False

def draw_marks(img, marks):
    draw_img = img.convert("RGBA")
    overlay = Image.new('RGBA', draw_img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    for m in marks:
        color = (46, 125, 50, 200) if m['correct'] else (198, 40, 40, 200)
        x, y, sz = int(m['x']), int(m['y']), 30
        if m['correct']:
            draw.line([(x-sz, y), (x, y+sz), (x+sz, y-sz)], fill=color, width=10)
        else:
            draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=10)
            draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=10)
    return Image.alpha_composite(draw_img, overlay).convert("RGB")

# --- 3. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = "email_gate"
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'history' not in st.session_state: st.session_state.history = []
if 'current_eval' not in st.session_state: st.session_state.current_eval = None

# --- 4. AUTHENTICATION FLOW ---
if st.session_state.step == "email_gate":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card"><h1>AXOM</h1><p>NEURAL GATEWAY</p>', unsafe_allow_html=True)
        email = st.text_input("Enter Email", placeholder="student@axom.ai")
        if st.button("Generate Access Code"):
            if "@" in email and send_otp(email):
                st.session_state.step = "otp_verify"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == "otp_verify":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card"><h3>VERIFY IDENTITY</h3>', unsafe_allow_html=True)
        code = st.text_input("6-Digit Code", type="password")
        if st.button("Enter Gateway"):
            if code == st.session_state.otp_code:
                st.session_state.step = "name_setup"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == "name_setup":
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="auth-card"><h3>IDENTITY SETUP</h3>', unsafe_allow_html=True)
        name = st.text_input("Enter Your Name")
        if st.button("Initialize Dashboard"):
            if len(name) > 1:
                st.session_state.user_name = name
                st.session_state.step = "active"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MAIN APPLICATION (ACTIVE STATE) ---
elif st.session_state.step == "active":
    with st.sidebar:
        st.markdown(f"<h2 style='color:#00E5FF'>AXOM CORE</h2><p style='color:#666;'>Welcome, {st.session_state.user_name}</p>", unsafe_allow_html=True)
        menu = st.radio("INTERFACE", ["VISION GRADER", "REVISION HUB", "NEURAL ARCHIVE", "SUBSCRIPTION", "MONETARY GRANT"])
        if st.button("Sign Out"):
            st.session_state.step = "email_gate"
            st.rerun()

    if menu == "VISION GRADER":
        st.subheader("NEURAL SCANNER")
        c1, c2 = st.columns(2)
        board = c1.text_input("EXAM BOARD", "Cambridge IGCSE")
        subject = c2.text_input("SUBJECT", "Physics P4")
        
        up_s = st.file_uploader("UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_m = st.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])

        if up_s and st.button("EXECUTE ANALYSIS"):
            with st.status("Analyzing Handwriting and Curriculum Logic..."):
                images = convert_from_bytes(up_s.read())
                time.sleep(2)
                eval_data = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "board": board, "subject": subject, "score": 82,
                    "marks": [{"page": 0, "x": 400, "y": 300, "correct": True}, {"page": 0, "x": 500, "y": 700, "correct": False}],
                    "gaps": [{"topic": "Kinematics", "issue": "Incorrect vector direction in Q2."}]
                }
                st.session_state.current_eval = {"data": eval_data, "images": images}
                st.session_state.history.append(st.session_state.current_eval)
            st.success("✅ Analysis Complete.")

        if st.session_state.current_eval:
            c_res, c_dl = st.columns([3, 1])
            c_res.write(f"### RESULT: {st.session_state.current_eval['data']['score']}%")
            c_dl.download_button("DOWNLOAD PDF", generate_pdf_report(st.session_state.current_eval['data']), file_name="Report.pdf")
            for i, img in enumerate(st.session_state.current_eval['images']):
                p_marks = [m for m in st.session_state.current_eval['data']['marks'] if m['page'] == i]
                st.image(draw_marks(img, p_marks), use_column_width=True)

    elif menu == "REVISION HUB":
        st.subheader("NEURAL REMEDIATION")
        if st.session_state.current_eval:
            for gap in st.session_state.current_eval['data']['gaps']:
                st.markdown(f'<div class="gap-card"><b>{gap["topic"]}</b><br><p>{gap["issue"]}</p></div>', unsafe_allow_html=True)
        else: st.info("Scan a paper to see revision gaps.")

    elif menu == "NEURAL ARCHIVE":
        st.subheader("HISTORICAL DATA")
        for item in reversed(st.session_state.history):
            with st.expander(f"{item['data']['timestamp']} | {item['data']['subject']} ({item['data']['score']}%)"):
                st.download_button("DOWNLOAD REPORT", generate_pdf_report(item['data']), file_name="Archive_Report.pdf", key=str(random.random()))

    elif menu == "SUBSCRIPTION":
        st.subheader("ACCESS PLANS")
        col1, col2, col3 = st.columns(3)
        plans = [("BASIC", "Free"), ("PRO", "$14.99"), ("ELITE", "$99.99")]
        for i, (n, p) in enumerate(plans):
            with [col1, col2, col3][i]:
                st.markdown(f'<div class="plan-card"><h3>{n}</h3><div class="price">{p}</div><p style="color:#666;">Full AI Analytics</p></div>', unsafe_allow_html=True)
                st.button(f"SELECT {n}", key=f"s_{i}")

    elif menu == "MONETARY GRANT":
        st.markdown('<div style="background:#0A0A0A; border:1px solid #00E5FF; padding:80px; text-align:center;"><p style="color:#00E5FF; font-weight:bold;">ANNUAL EXCELLENCE GRANT</p><h1 style="font-size:80px;">$5,000.00</h1><p style="color:#666;">COMING SOON: 2026</p></div>', unsafe_allow_html=True)
