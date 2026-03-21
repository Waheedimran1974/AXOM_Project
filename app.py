import streamlit as st
from google import genai
import pandas as pd
import os
import io
import json
import re
import csv
import smtplib
import random
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 30px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 20px rgba(0, 212, 255, 0.2); }
    .report-box { padding: 20px; border-left: 5px solid #00d4ff; background: rgba(0, 212, 255, 0.1); margin: 10px 0; border-radius: 0 10px 10px 0; color: #fff; }
    .stButton>button { width: 100%; background: #00d4ff; color: #000; border: none; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; margin-top: 10px; }
    .stButton>button:hover { background: #008fb3 !important; color: #fff !important; box-shadow: 0 0 15px #00d4ff; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; font-size: 18px; letter-spacing: 2px;}
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND UTILITIES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash" 
HISTORY_FILE = "axom_history.csv"

def get_grade(perc):
    if perc >= 80: return "A*"
    if perc >= 70: return "A"
    if perc >= 60: return "B"
    if perc >= 50: return "C"
    return "D/E"

def robust_json_parser(text):
    try:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match: return json.loads(match.group(0))
        return []
    except: return []

def mark_visuals(image, marks_data):
    draw = ImageDraw.Draw(image)
    f_size = int(image.height * 0.035) 
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", f_size)
    except: font = ImageFont.load_default()
    ticks, notes = 0, []
    for m in marks_data:
        x, y = int((m.get('x', 50)/1000)*image.width), int((m.get('y', 50)/1000)*image.height)
        char = "✓" if m['type'] == 'tick' else "✕"
        draw.text((x, y), char, fill=(239, 68, 68), font=font)
        if m['type'] == 'tick': ticks += 1
        if 'comment' in m: notes.append(m['comment'])
    return image, ticks, notes

# --- 3. OTP EMAIL ENGINE ---
def send_otp_email(recipient, otp):
    try:
        msg = EmailMessage()
        msg.set_content(f"AXOM Neural Interface Initialization.\n\nYour 6-digit Access Key is: {otp}\n\nUse this key to unlock the evaluation dashboard.")
        msg['Subject'] = 'AXOM ACCESS KEY'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recipient

        # Using Gmail's SMTP server (adjust if using Yahoo/Outlook)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email. Check SMTP Secrets. Error: {e}")
        return False

# --- 4. SECURE OTP LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "get_email"
if "current_otp" not in st.session_state:
    st.session_state.current_otp = None
if "u_email" not in st.session_state:
    st.session_state.u_email = ""

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        
        # STEP 1: Enter Email
        if st.session_state.auth_step == "get_email":
            st.title("AXOM | REQUEST ACCESS")
            email_input = st.text_input("ENTER REGISTERED EMAIL ID")
            
            if st.button("TRANSMIT NEURAL KEY"):
                if email_input:
                    with st.spinner("TRANSMITTING KEY TO INBOX..."):
                        generated_code = str(random.randint(100000, 999999))
                        if send_otp_email(email_input, generated_code):
                            st.session_state.current_otp = generated_code
                            st.session_state.u_email = email_input
                            st.session_state.auth_step = "verify_otp"
                            st.rerun()
                else:
                    st.warning("Please enter an email address.")
                    
        # STEP 2: Enter OTP
        elif st.session_state.auth_step == "verify_otp":
            st.title("AXOM | VERIFY IDENTITY")
            st.info(f"An access key was sent to {st.session_state.u_email}")
            user_otp = st.text_input("ENTER 6-DIGIT KEY", type="password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("UNLOCK INTERFACE"):
                    if user_otp == st.session_state.current_otp:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("ACCESS DENIED: Invalid or expired key.")
            with col_b:
                if st.button("CANCEL / RESEND"):
                    st.session_state.auth_step = "get_email"
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MAIN INTERFACE ---
else:
    with st.sidebar:
        st.markdown(f"**ACTIVE USER:**\n`{st.session_state.u_email}`")
        if st.button("TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.session_state.auth_step = "get_email"
            st.session_state.current_otp = None
            st.rerun()

    t1, t2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with t1:
        st.header("NEURAL SCANNER")
        up_script = st.file_uploader("1. UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_ms = st.file_uploader("2. UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])
        
        c1, col_b = st.columns(2)
        with c1: board = st.text_input("EXAM BOARD", "Cambridge")
        with col_b: code = st.text_input("SUBJECT CODE", "IGCSE Exam")

        if up_script and st.button("RUN FULL NEURAL EVALUATION"):
            with st.spinner("AXOM ANALYZING SCRIPT..."):
                try:
                    script_imgs = convert_from_bytes(up_script.read())
                    pdf = FPDF()
                    all_ticks, total_items, all_comments = 0, 0, []
                    
                    for i, img in enumerate(script_imgs):
                        prompt = f"Strict {board} examiner mode for {code}. Output ONLY JSON: [{{'type':'tick'|'cross','x':int,'y':int,'comment':str}}]"
                        response = client.models.generate_content(model=MODEL_ID, contents=[prompt, img])
                        data = robust_json_parser(response.text)
                        
                        marked_img, p_ticks, p_notes = mark_visuals(img, data)
                        all_ticks += p_ticks
                        total_items += len(data)
                        all_comments.extend(p_notes)
                        
                        pdf.add_page()
                        tmp = f"temp_p{i}.png"
                        marked_img.save(tmp)
                        pdf.image(tmp, 0, 0, 210, 297)
                        os.remove(tmp)

                    perc = (all_ticks/total_items*100) if total_items > 0 else 0
                    grade = get_grade(perc)
                    st.session_state.last_comments = all_comments 
                    
                    new_row = pd.DataFrame([
                        {
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Email": st.session_state.u_email,
                            "Board": board,
                            "Subject": code,
                            "Result": f"{all_ticks}/{total_items}",
                            "Grade": grade
                        }
                    ])
                    new_row.to_csv(HISTORY_FILE, mode='a', header=not os.path.exists(HISTORY_FILE), index=False, quoting=csv.QUOTE_ALL)
                    
                    pdf_output = pdf.output(dest='S')
                    pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)

                    st.success(f"ANALYSIS COMPLETE: {grade} ({all_ticks}/{total_items})")
                    st.download_button("📥 DOWNLOAD CHECKED SCRIPT", data=pdf_bytes, file_name="AXOM_Checked.pdf")
                    
                    st.markdown("---")
                    if st.button("📊 GENERATE DIAGNOSTIC REPORT"):
                        with st.spinner("AI EVALUATING PERFORMANCE..."):
                            analysis_prompt = f"Based on these examiner comments: {all_comments}. Tell the student their 2 biggest strengths, 2 biggest weaknesses, and exactly what to revise for {code} exams."
                            report_resp = client.models.generate_content(model=MODEL_ID, contents=[analysis_prompt])
                            st.markdown(f'<div class="report-box"><h3>NEURAL DIAGNOSTIC</h3>{report_resp.text}</div>', unsafe_allow_html=True)

                except Exception as e: 
                    st.error(f"SYSTEM ERROR: {e}")

    with t2:
        st.header("DATA ARCHIVE")
        if os.path.exists(HISTORY_FILE):
            try:
                df = pd.read_csv(HISTORY_FILE, quoting=csv.QUOTE_ALL, on_bad_lines='warn')
                user_df = df[df['Email'] == st.session_state.u_email]
                st.dataframe(user_df.drop(columns=['Email']), use_container_width=True)
            except Exception:
                st.error("The history file is corrupted.")
                if st.button("PURGE CORRUPTED HISTORY"):
                    os.remove(HISTORY_FILE)
                    st.rerun()
        else: 
            st.info("No records found.")
