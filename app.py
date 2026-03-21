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

# --- 1. HUD STYLING (AXOM NEURAL THEME) ---
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
    .stButton>button {
        width: 100%;
        background: transparent;
        color: #00d4ff;
        border: 1px solid #00d4ff;
        border-radius: 5px;
        transition: 0.3s;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .stButton>button:hover {
        background: #00d4ff;
        color: #000 !important;
        box-shadow: 0 0 15px #00d4ff;
    }
    .stTextInput>div>div>input {
        background: rgba(0, 0, 0, 0.5) !important;
        color: #00d4ff !important;
        border: 1px solid #00d4ff !important;
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
    """Saves session data to a local CSV file for persistent history."""
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
    except:
        return None

def mark_page_visual(image, marks_data):
    draw = ImageDraw.Draw(image)
    mark_font_size = 65 
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", mark_font_size)
    except:
        font = ImageFont.load_default()
    
    ink_color = (239, 68, 68) 
    page_ticks = 0
    annotations_list = []
    
    for mark in marks_data:
        x = mark.get('x', 50) + random.randint(-5, 5)
        y = mark.get('y', 50) + random.randint(-5, 5)
        icon = "✓" if mark['type'] == 'tick' else "✕"
        draw.text((x, y), icon, fill=ink_color, font=font)
        
        if mark['type'] == 'tick':
            page_ticks += 1
        if 'comment' in mark:
            annotations_list.append({'x': x, 'y': y, 'text': mark['comment']})
            
    return image, page_ticks, annotations_list

# --- 3. SESSION & AUTH LOGIC ---
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
                with st.spinner("TRANSMITTING..."):
                    otp = send_neural_key(email_in)
                    if otp:
                        st.session_state.generated_otp = otp
                        st.session_state.temp_email = email_in
                        st.session_state.auth_step = "verify"
                        st.rerun()
                    else:
                        st.error("COMMS ERROR: CHECK CONFIG")

        elif st.session_state.auth_step == "verify":
            st.title("VERIFY LINK")
            st.write(f"KEY SENT TO: {st.session_state.temp_email}")
            otp_in = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("INITIALIZE SESSION"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.session_state.user_email = st.session_state.temp_email
                    st.rerun()
                else:
                    st.error("ACCESS DENIED")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- SIDEBAR: EXAM METADATA ---
    st.sidebar.title("AXOM STATUS")
    st.sidebar.write(f"ACTIVE: {st.session_state.user_email}")
    st.sidebar.markdown("---")
    exam_board = st.sidebar.text_input("EXAM BOARD", placeholder="e.g. Cambridge / Edexcel")
    subject_info = st.sidebar.text_input("SUBJECT / CODE", placeholder="e.g. 0580 Mathematics")
    
    if st.sidebar.button("TERMINATE SESSION"):
        st.session_state.logged_in = False
        st.session_state.auth_step = "identify"
        st.rerun()

    tab1, tab2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with tab1:
        st.header("DOCUMENT SCAN")
        uploaded_file = st.file_uploader("UPLOAD SCRIPT (PDF)", type=['pdf'])
        
        if uploaded_file:
            if st.button("RUN FULL NEURAL ANALYSIS"):
                with st.spinner("SYNCHRONIZING WITH EXAM STANDARDS..."):
                    file_bytes = uploaded_file.read()
                    total_score = 0
                    total_elements = 0
                    
                    try:
                        pages = convert_from_bytes(file_bytes)
                        pdf = FPDF()
                        
                        # --- COVER PAGE ---
                        pdf.add_page()
                        pdf.set_fill_color(0, 18, 46)
                        pdf.rect(0, 0, 210, 297, 'F')
                        pdf.set_text_color(0, 212, 255)
                        pdf.set_font("Arial", 'B', 32)
                        pdf.cell(0, 60, "CHECKED BY AXOM", ln=True, align='C')
                        
                        pdf.set_font("Arial", 'B', 18)
                        pdf.cell(0, 12, f"BOARD: {exam_board.upper() if exam_board else 'UNSPECIFIED'}", ln=True, align='C')
                        pdf.cell(0, 12, f"SUBJECT: {subject_info.upper() if subject_info else 'GENERAL'}", ln=True, align='C')

                        # --- PAGE ANALYSIS ---
                        for i, page_img in enumerate(pages):
                            prompt = (f"Act as a strict {exam_board} examiner for {subject_info}. "
                                      f"Mark page {i+1} accurately. Return ONLY a JSON list: "
                                      "[{'type': 'tick'|'cross', 'x': int, 'y': int, 'comment': str}]")
                            
                            response = client.models.generate_content(model=MODEL_ID, contents=[prompt, page_img])
                            
                            try:
                                clean_json = response.text.strip('`').replace('json', '').strip()
                                marks_data = json.loads(clean_json)
                                marked_img, p_score, page_notes = mark_page_visual(page_img, marks_data)
                                
                                total_score += p_score
                                total_elements += len(marks_data)
                                
                                pdf.add_page()
                                temp_path = f"axom_p{i}.png"
                                marked_img.save(temp_path)
                                pdf.image(temp_path, x=0, y=0, w=210, h=297)
                                os.remove(temp_path)
                                
                                for note in page_notes:
                                    scaled_x = (note['x'] / marked_img.width) * 210
                                    scaled_y = (note['y'] / marked_img.height) * 297
                                    pdf.text_annotation(x=scaled_x, y=scaled_y, text=note['text'])
                            except:
                                pdf.add_page()

                        final_pdf = bytes(pdf.output())
                        
                        # Save session to the stable History CSV
                        save_to_history(st.session_state.user_email, exam_board, subject_info, total_score, total_elements)
                        
                        orig_filename = uploaded_file.name.rsplit('.', 1)[0]
                        final_filename = f"{orig_filename}_checked by AXOM.pdf"

                        st.success(f"ANALYSIS COMPLETE | SAVED TO ARCHIVE")
                        st.download_button(label="📥 DOWNLOAD CHECKED SCRIPT", data=final_pdf, file_name=final_filename, mime="application/pdf")

                    except Exception as e:
                        st.error(f"NEURAL ERROR: {str(e)}")

    with tab2:
        st.header("ARCHIVED SESSIONS")
        if os.path.exists(HISTORY_FILE):
            history_df = pd.read_csv(HISTORY_FILE)
            user_view = history_df[history_df['Email'] == st.session_state.user_email]
            
            if not user_view.empty:
                # Format the table for the AXOM theme
                st.dataframe(user_view.drop(columns=['Email']), use_container_width=True)
                if st.button("CLEAR MY HISTORY"):
                    history_df = history_df[history_df['Email'] != st.session_state.user_email]
                    history_df.to_csv(HISTORY_FILE, index=False)
                    st.rerun()
            else:
                st.info("No past sessions found for your profile.")
        else:
            st.warning("Database initialized. Complete your first scan to see history here.")
