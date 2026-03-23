import streamlit as st
from google import genai
import pandas as pd
import os
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
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 30px rgba(0, 212, 255, 0.3); text-align: center; }
    .report-box { padding: 20px; border-left: 5px solid #00d4ff; background: rgba(0, 212, 255, 0.1); margin: 10px 0; border-radius: 0 10px 10px 0; color: #fff; }
    .stButton>button { width: 100%; background: #00d4ff; color: #000; border: none; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; margin-top: 15px; }
    .stButton>button:hover { background: #008fb3 !important; color: #fff !important; box-shadow: 0 0 15px #00d4ff; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; font-size: 20px; letter-spacing: 2px; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    div[data-testid="stRadio"] > div { background: rgba(0, 212, 255, 0.1); padding: 10px; border-radius: 5px; border: 1px solid #00d4ff;}
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
        msg.set_content(f"AXOM NEURAL INTERFACE ACCESS\n\nYour 6-digit access code is: {otp}\n\nUse this to unlock the evaluation dashboard.")
        msg['Subject'] = 'AXOM ACCESS KEY'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recipient

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email Dispatch Failed. Please check Streamlit Secrets. Error: {e}")
        return False

# --- 4. LOGIN GATEWAY ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "target_email" not in st.session_state:
    st.session_state.target_email = ""

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        
        if not st.session_state.otp_sent:
            u_email = st.text_input("ENTER EMAIL ID")
            if st.button("TRANSMIT ACCESS KEY"):
                if u_email:
                    with st.spinner("TRANSMITTING TO NETWORK..."):
                        code = str(random.randint(100000, 999999))
                        if send_otp_email(u_email, code):
                            st.session_state.generated_otp = code
                            st.session_state.target_email = u_email
                            st.session_state.otp_sent = True
                            st.rerun()
                else:
                    st.warning("EMAIL REQUIRED")
        else:
            st.info(f"Key transmitted to {st.session_state.target_email}")
            u_otp = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("VERIFY & UNLOCK"):
                if u_otp == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("INVALID KEY")
            if st.button("BACK / RESEND"):
                st.session_state.otp_sent = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. NEURAL DASHBOARD ---
else:
    with st.sidebar:
        st.markdown(f"**ACTIVE USER:**\n`{st.session_state.target_email}`")
        if st.button("TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.session_state.otp_sent = False
            st.rerun()

    t1, t2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with t1:
        st.header("NEURAL SCANNER")
        up_script = st.file_uploader("1. UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_ms = st.file_uploader("2. UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])
        
        c1, c2 = st.columns(2)
        with c1: board = st.text_input("EXAM BOARD", "Cambridge")
        with c2: code = st.text_input("SUBJECT CODE", "IGCSE Math/Physics")

        # --- THE NEW GEOMETRY TOGGLE ---
        scan_mode = st.radio("SELECT AI PROCESSING MODE:", 
                             ["Standard Text & Equation Scan", "Advanced Graph & Geometry Analysis"], 
                             horizontal=True)

        if up_script and st.button("INITIALIZE EVALUATION"):
            with st.spinner("AXOM ANALYZING SCRIPT..."):
                try:
                    script_imgs = convert_from_bytes(up_script.read())
                    pdf = FPDF()
                    all_ticks, total_items, all_comments = 0, 0, []
                    
                    # Determine which prompt to use based on the toggle
                    if scan_mode == "Standard Text & Equation Scan":
                        base_prompt = f"Strict {board} examiner mode for {code}. Output ONLY JSON: [{{'type':'tick'|'cross','x':int,'y':int,'comment':str}}]"
                    else:
                        base_prompt = f"Strict {board} examiner mode for {code}. GEOMETRY & GRAPH MODE: Critically analyze all plotted graphs, axes, line slopes, curve shapes, and drawn angles. If a graph or angle is incorrect, mark it with a cross and explicitly state the EXACT correct coordinates, formula, or angle in your comment. Output ONLY JSON: [{{'type':'tick'|'cross','x':int,'y':int,'comment':str}}]"

                    for i, img in enumerate(script_imgs):
                        response = client.models.generate_content(model=MODEL_ID, contents=[base_prompt, img])
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
                    
                    new_row = pd.DataFrame([{
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Email": st.session_state.target_email,
                        "Board": board, "Subject": code,
                        "Result": f"{all_ticks}/{total_items}", "Grade": grade
                    }])
                    new_row.to_csv(HISTORY_FILE, mode='a', header=not os.path.exists(HISTORY_FILE), index=False, quoting=csv.QUOTE_ALL)
                    
                    st.success(f"ANALYSIS COMPLETE: {grade} ({all_ticks}/{total_items})")
                    
                    pdf_output = pdf.output(dest='S')
                    pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)
                    st.download_button("📥 DOWNLOAD MARKED PDF", data=pdf_bytes, file_name="AXOM_Checked.pdf")
                    
                    # --- REPORT SECTION ---
                    st.markdown("---")
                    if st.button("📊 GENERATE DIAGNOSTIC REPORT"):
                        with st.spinner("AI COMPILING GEOMETRY DATA..."):
                            report_prompt = f"Based on these examiner comments: {all_comments}. Tell the student their 2 biggest strengths, 2 biggest weaknesses. If there were any graph or geometry errors, dedicate a section called 'GRAPH CORRECTIONS' explaining exactly how the curves or angles should have been drawn for {code}."
                            report_resp = client.models.generate_content(model=MODEL_ID, contents=[report_prompt])
                            st.markdown(f'<div class="report-box"><h3>NEURAL DIAGNOSTIC</h3>{report_resp.text}</div>', unsafe_allow_html=True)

                except Exception as e: 
                    st.error(f"SYSTEM ERROR: {e}")

    with t2:
        st.header("DATA ARCHIVE")
        if os.path.exists(HISTORY_FILE):
            try:
                df = pd.read_csv(HISTORY_FILE, quoting=csv.QUOTE_ALL, on_bad_lines='warn')
                user_df = df[df['Email'] == st.session_state.target_email]
                st.dataframe(user_df.drop(columns=['Email']), use_container_width=True)
            except Exception:
                st.error("Archive file corrupted.")
                if st.button("PURGE HISTORY AND FIX"):
                    os.remove(HISTORY_FILE)
                    st.rerun()
        else: 
            st.info("No records found yet.")
