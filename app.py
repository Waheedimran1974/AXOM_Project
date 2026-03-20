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

# --- 1. HUD STYLING ---
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
        color: #000;
        box-shadow: 0 0 15px #00d4ff;
    }
    .stTextInput>div>div>input {
        background: rgba(0, 0, 0, 0.5);
        color: #00d4ff;
        border: 1px solid #00d4ff;
    }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ENGINES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash"
HISTORY_FILE = "axom_history.csv"

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
    try:
        font = ImageFont.truetype("ibrahim_handwriting.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    ink_color = (239, 68, 68) 
    page_ticks = 0
    
    for mark in marks_data:
        x, y = mark.get('x', 50), mark.get('y', 50)
        if mark['type'] == 'tick':
            draw.text((x, y), "✓", fill=ink_color, font=font)
            page_ticks += 1
        else:
            draw.text((x, y), "✕", fill=ink_color, font=font)
        
        if 'comment' in mark:
            draw.text((x + 70, y), f"- {mark['comment']}", fill=ink_color, font=font)
            
    return image, page_ticks

def archive_data(email, score, feedback):
    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), email, score, feedback]], 
                             columns=["Date", "Email", "Score", "Feedback"])
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
    else:
        df = new_entry
    df.to_csv(HISTORY_FILE, index=False)

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
                with st.spinner("TRANSMITTING..."):
                    otp = send_neural_key(email_in)
                    if otp:
                        st.session_state.generated_otp = otp
                        st.session_state.temp_email = email_in
                        st.session_state.auth_step = "verify"
                        st.rerun()
                    else:
                        st.error("COMMS ERROR: CHECK CONFIGURATION")

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
                    st.error("ACCESS DENIED: INVALID KEY")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.sidebar.title("AXOM STATUS")
    st.sidebar.write(f"USER: {st.session_state.user_email}")
    if st.sidebar.button("TERMINATE SESSION"):
        st.session_state.logged_in = False
        st.session_state.auth_step = "identify"
        st.rerun()

    tab1, tab2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with tab1:
        st.header("DOCUMENT SCAN")
        uploaded_file = st.file_uploader("UPLOAD SCRIPT", type=['pdf'])
        
        if uploaded_file:
            if st.button("RUN FULL NEURAL ANALYSIS"):
                with st.spinner("EXAMINING ENTIRE DOCUMENT..."):
                    file_bytes = uploaded_file.read()
                    all_marked_pages = []
                    total_score = 0
                    total_questions = 0
                    full_feedback_log = []
                    
                    try:
                        pages = convert_from_bytes(file_bytes)
                        
                        for i, page_img in enumerate(pages):
                            prompt = f"""
                            You are a strict examiner for IGCSE Science. Mark page {i+1} of this script.
                            Focus on scientific diagrams and text.
                            Return ONLY a JSON list of dictionaries:
                            [{{'type': 'tick'|'cross', 'x': int, 'y': int, 'comment': str}}]
                            If the page is blank, return []. No other text.
                            """
                            
                            response = client.models.generate_content(
                                model=MODEL_ID,
                                contents=[prompt, page_img]
                            )
                            
                            try:
                                clean_json = response.text.strip('`').replace('json', '').strip()
                                marks_data = json.loads(clean_json)
                                marked_img, p_score = mark_page_visual(page_img, marks_data)
                                
                                total_score += p_score
                                total_questions += len(marks_data)
                                all_marked_pages.append(marked_img)
                                full_feedback_log.append(f"Page {i+1}: {response.text}")
                            except:
                                all_marked_pages.append(page_img)

                        # --- GENERATE BRANDED PDF ---
                        pdf = FPDF()
                        percentage = (total_score / total_questions * 100) if total_questions > 0 else 0
                        
                        # COVER PAGE
                        pdf.add_page()
                        pdf.set_fill_color(0, 18, 46)
                        pdf.rect(0, 0, 210, 297, 'F')
                        pdf.set_text_color(0, 212, 255)
                        pdf.set_font("Arial", 'B', 35)
                        pdf.cell(0, 100, "CHECKED BY AXOM", ln=True, align='C')
                        pdf.set_font("Arial", 'B', 24)
                        pdf.cell(0, 20, f"TOTAL MARKS: {total_score} / {total_questions}", ln=True, align='C')
                        pdf.cell(0, 20, f"PERCENTAGE: {percentage:.1f}%", ln=True, align='C')
                        
                        # APPEND PAGES
                        for img in all_marked_pages:
                            pdf.add_page()
                            temp_name = f"temp_{random.randint(1000,9999)}.png"
                            img.save(temp_name)
                            pdf.image(temp_name, x=0, y=0, w=210, h=297)
                            os.remove(temp_name)
                        
                        # Convert bytearray to bytes for Streamlit
                        final_pdf_bytes = bytes(pdf.output())

                        st.success(f"ANALYSIS COMPLETE: {total_score}/{total_questions}")
                        st.download_button(
                            label="📥 DOWNLOAD CHECKED BY AXOM PDF",
                            data=final_pdf_bytes,
                            file_name=f"{uploaded_file.name.replace('.pdf','')}_CHECKED_BY_AXOM.pdf",
                            mime="application/pdf"
                        )
                        
                        archive_data(st.session_state.user_email, f"{total_score}/{total_questions}", "\n".join(full_feedback_log))

                    except Exception as e:
                        st.error(f"SYSTEM ERROR: {str(e)}")

    with tab2:
        st.header("SESSION LOGS")
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_data = df[df['Email'] == st.session_state.user_email]
            if not user_data.empty:
                st.dataframe(user_data)
            else:
                st.info("NO ARCHIVED DATA FOUND")
        else:
            st.warning("ARCHIVE SYSTEM EMPTY")
