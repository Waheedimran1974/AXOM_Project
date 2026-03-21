import streamlit as st
from google import genai
import pandas as pd
import os
import smtplib
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from email.message import EmailMessage
import io
import json
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD STYLING (FUTURE INTERFACE) ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle, #00122e 0%, #00050d 100%);
        color: #00d4ff;
        font-family: 'Courier New', monospace;
    }
    .future-frame {
        border: 2px solid #00d4ff;
        border-radius: 10px;
        padding: 40px;
        background: rgba(0, 20, 46, 0.9);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
        text-align: center;
    }
    /* FUTURE BUTTON & INPUT STYLING */
    .stButton>button {
        width: 100%;
        background: transparent;
        color: #00d4ff;
        border: 1px solid #00d4ff;
        border-radius: 5px;
        transition: 0.3s;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: #00d4ff !important;
        color: #000 !important;
        box-shadow: 0 0 20px #00d4ff;
    }
    .stTextInput>div>div>input {
        background: rgba(0, 212, 255, 0.1) !important;
        color: #00d4ff !important;
        border: 1px solid #00d4ff !important;
        border-radius: 5px !important;
        height: 45px;
        font-size: 16px;
        text-align: center;
    }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ENGINES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash"
HISTORY_FILE = "axom_history.csv"

def get_igcse_grade(percentage):
    if percentage >= 80: return "A*"
    if percentage >= 70: return "A"
    if percentage >= 60: return "B"
    if percentage >= 50: return "C"
    return "D/E"

def save_to_history(email, board, subject, score, total):
    perc = (score / total * 100) if total > 0 else 0
    grade = get_igcse_grade(perc)
    new_data = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Email": email,
        "Board": board if board else "N/A",
        "Subject": subject if subject else "N/A",
        "Result": f"{score}/{total}",
        "Grade": grade
    }
    df_new = pd.DataFrame([new_data])
    file_exists = os.path.exists(HISTORY_FILE)
    df_new.to_csv(HISTORY_FILE, mode='a', header=not file_exists, index=False)

def send_neural_key(receiver_email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"AXOM NEURAL ACCESS KEY: {otp}\nINITIALIZING SECURE LINK...")
    msg['Subject'] = "AXOM | SECURE ACCESS KEY"
    msg['From'] = st.secrets["SENDER_EMAIL"]
    msg['To'] = receiver_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SENDER_EMAIL"], st.secrets["APP_PASSWORD"])
            server.send_message(msg)
        return otp
    except: return None

def mark_page_visual(image, marks_data):
    draw = ImageDraw.Draw(image)
    mark_font_size = 65 
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", mark_font_size)
    except: font = ImageFont.load_default()
    
    ink_color = (239, 68, 68) 
    page_ticks = 0
    annotations_list = []
    
    for mark in marks_data:
        x, y = mark.get('x', 50) + random.randint(-5, 5), mark.get('y', 50) + random.randint(-5, 5)
        icon = "✓" if mark['type'] == 'tick' else "✕"
        draw.text((x, y), icon, fill=ink_color, font=font)
        if mark['type'] == 'tick': page_ticks += 1
        if 'comment' in mark: annotations_list.append({'x': x, 'y': y, 'text': mark['comment']})
    return image, page_ticks, annotations_list

# --- 3. SESSION LOGIC ---
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "identify"
    st.session_state.logged_in = False

# --- 4. INTERFACE ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        if st.session_state.auth_step == "identify":
            st.title("AXOM INTERFACE")
            email_in = st.text_input("INPUT EMAIL ID")
            if st.button("REQUEST NEURAL KEY"):
                otp = send_neural_key(email_in)
                if otp:
                    st.session_state.generated_otp, st.session_state.temp_email, st.session_state.auth_step = otp, email_in, "verify"
                    st.rerun()
        elif st.session_state.auth_step == "verify":
            st.title("VERIFY LINK")
            otp_in = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("INITIALIZE SESSION"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.logged_in, st.session_state.user_email = True, st.session_state.temp_email
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    st.sidebar.title("AXOM STATUS")
    st.sidebar.write(f"ACTIVE: {st.session_state.user_email}")
    if st.sidebar.button("TERMINATE SESSION"):
        st.session_state.logged_in = False
        st.rerun()

    tab1, tab2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with tab1:
        st.header("DOCUMENT SCAN")
        uploaded_file = st.file_uploader("1. UPLOAD SCRIPT (PDF)", type=['pdf'])
        
        # --- NEW INTEGRATED FUTURE INPUTS ---
        col_a, col_b = st.columns(2)
        with col_a:
            board_input = st.text_input("2. EXAM BOARD", placeholder="e.g. Cambridge")
        with col_b:
            subject_input = st.text_input("3. SUBJECT CODE", placeholder="e.g. 0580/22")

        if uploaded_file:
            if st.button("RUN FULL NEURAL ANALYSIS"):
                with st.spinner("SYNCHRONIZING WITH EXAM STANDARDS..."):
                    file_bytes = uploaded_file.read()
                    total_score, total_elements = 0, 0
                    try:
                        pages = convert_from_bytes(file_bytes)
                        pdf = FPDF()
                        
                        # COVER PAGE
                        pdf.add_page()
                        pdf.set_fill_color(0, 18, 46); pdf.rect(0, 0, 210, 297, 'F')
                        pdf.set_text_color(0, 212, 255); pdf.set_font("Arial", 'B', 32)
                        pdf.cell(0, 60, "CHECKED BY AXOM", ln=True, align='C')
                        pdf.set_font("Arial", 'B', 18)
                        pdf.cell(0, 12, f"BOARD: {board_input.upper() if board_input else 'N/A'}", ln=True, align='C')
                        pdf.cell(0, 12, f"SUBJECT: {subject_input.upper() if subject_input else 'N/A'}", ln=True, align='C')

                        for i, page_img in enumerate(pages):
                            prompt = f"Mark page {i+1} as a strict {board_input} examiner for {subject_input}. Return ONLY JSON: [{{'type': 'tick'|'cross', 'x': int, 'y': int, 'comment': str}}]"
                            response = client.models.generate_content(model=MODEL_ID, contents=[prompt, page_img])
                            try:
                                clean_json = response.text.strip('`').replace('json', '').strip()
                                marks_data = json.loads(clean_json)
                                marked_img, p_score, page_notes = mark_page_visual(page_img, marks_data)
                                total_score += p_score; total_elements += len(marks_data)
                                pdf.add_page()
                                temp_p = f"axom_{i}.png"; marked_img.save(temp_p)
                                pdf.image(temp_p, x=0, y=0, w=210, h=297); os.remove(temp_p)
                                for n in page_notes:
                                    pdf.text_annotation(x=(n['x']/marked_img.width)*210, y=(n['y']/marked_img.height)*297, text=n['text'])
                            except: pdf.add_page()

                        final_pdf = bytes(pdf.output())
                        save_to_history(st.session_state.user_email, board_input, subject_input, total_score, total_elements)
                        f_name = f"{uploaded_file.name.rsplit('.', 1)[0]}_checked by AXOM.pdf"
                        st.success("ANALYSIS COMPLETE")
                        st.download_button("📥 DOWNLOAD CHECKED SCRIPT", data=final_pdf, file_name=f_name)
                    except Exception as e: st.error(f"NEURAL ERROR: {e}")

    with tab2:
        st.header("ARCHIVED SESSIONS")
        if os.path.exists(HISTORY_FILE):
            hist = pd.read_csv(HISTORY_FILE)
            user_hist = hist[hist['Email'] == st.session_state.user_email]
            if not user_hist.empty:
                st.dataframe(user_hist.drop(columns=['Email']), use_container_width=True)
                if st.button("CLEAR HISTORY"):
                    hist[hist['Email'] != st.session_state.user_email].to_csv(HISTORY_FILE, index=False)
                    st.rerun()
            else: st.info("No past sessions found.")
