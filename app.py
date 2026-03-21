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

def send_neural_key(receiver_email):
    """Generates and sends a 6-digit OTP via SMTP."""
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
    """Draws large human-like ticks and crosses on the page image."""
    draw = ImageDraw.Draw(image)
    
    # Large, clear font size for Ibrahim to see easily
    mark_font_size = 65 
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", mark_font_size)
    except:
        font = ImageFont.load_default()
    
    ink_color = (239, 68, 68) # Professional Examiner Red
    page_ticks = 0
    annotations_list = []
    
    for mark in marks_data:
        # Slight jitter to look human
        x = mark.get('x', 50) + random.randint(-5, 5)
        y = mark.get('y', 50) + random.randint(-5, 5)
        
        icon = "✓" if mark['type'] == 'tick' else "✕"
        draw.text((x, y), icon, fill=ink_color, font=font)
        
        if mark['type'] == 'tick':
            page_ticks += 1
        
        # Collect data for Sticky Notes (Annotations)
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
                        st.error("COMMS ERROR: CHECK SECRETS")

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
    # --- SIDEBAR: EXAM METADATA ---
    st.sidebar.title("AXOM STATUS")
    st.sidebar.write(f"ACTIVE: {st.session_state.user_email}")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("EXAM CONFIGURATION")
    exam_board = st.sidebar.text_input("EXAM BOARD", placeholder="e.g. Cambridge / IGCSE")
    subject_info = st.sidebar.text_input("SUBJECT / CODE", placeholder="e.g. 0620 Chemistry")
    st.sidebar.markdown("---")
    
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
                        
                        # --- CUSTOM COVER PAGE ---
                        pdf.add_page()
                        pdf.set_fill_color(0, 18, 46) # Dark Blue
                        pdf.rect(0, 0, 210, 297, 'F')
                        pdf.set_text_color(0, 212, 255) # Cyan
                        
                        pdf.set_font("Arial", 'B', 32)
                        pdf.cell(0, 60, "CHECKED BY AXOM", ln=True, align='C')
                        
                        pdf.set_font("Arial", 'B', 18)
                        if exam_board:
                            pdf.cell(0, 12, f"EXAM BOARD: {exam_board.upper()}", ln=True, align='C')
                        if subject_info:
                            pdf.cell(0, 12, f"SUBJECT: {subject_info.upper()}", ln=True, align='C')
                            
                        pdf.ln(30)
                        pdf.set_font("Arial", 'I', 12)
                        pdf.cell(0, 10, f"PROCESSED ON: {datetime.now().strftime('%d %B %Y | %H:%M')}", ln=True, align='C')

                        # --- PAGE-BY-PAGE ANALYSIS ---
                        for i, page_img in enumerate(pages):
                            # AI Prompt tailored with specific subject info
                            prompt = (f"Act as a strict {exam_board} examiner for {subject_info}. "
                                      f"Mark page {i+1} accurately. Correct errors with helpful notes. "
                                      "Return ONLY a JSON list: [{'type': 'tick'|'cross', 'x': int, 'y': int, 'comment': str}]")
                            
                            response = client.models.generate_content(model=MODEL_ID, contents=[prompt, page_img])
                            
                            try:
                                clean_json = response.text.strip('`').replace('json', '').strip()
                                marks_data = json.loads(clean_json)
                                marked_img, p_score, page_notes = mark_page_visual(page_img, marks_data)
                                
                                total_score += p_score
                                total_elements += len(marks_data)
                                
                                # Add the marked page to the PDF
                                pdf.add_page()
                                temp_path = f"axom_p{i}.png"
                                marked_img.save(temp_path)
                                pdf.image(temp_path, x=0, y=0, w=210, h=297)
                                os.remove(temp_path)
                                
                                # Inject Sticky Note Annotations
                                for note in page_notes:
                                    # Scale Pillow pixels to A4 mm coordinates
                                    scaled_x = (note['x'] / marked_img.width) * 210
                                    scaled_y = (note['y'] / marked_img.height) * 297
                                    pdf.text_annotation(x=scaled_x, y=scaled_y, text=note['text'])
                            except Exception as e:
                                # Fallback for unparseable AI response
                                pdf.add_page()
                                t_path = f"fail_{i}.png"
                                page_img.save(t_path)
                                pdf.image(t_path, x=0, y=0, w=210, h=297)
                                os.remove(t_path)

                        # --- FINAL EXPORT ---
                        final_pdf = bytes(pdf.output())
                        
                        # Filename: [original]_checked by AXOM.pdf
                        orig_filename = uploaded_file.name.rsplit('.', 1)[0]
                        final_filename = f"{orig_filename}_checked by AXOM.pdf"

                        st.success(f"NEURAL ANALYSIS COMPLETE | SCORE: {total_score}/{total_elements}")
                        st.download_button(
                            label="📥 DOWNLOAD ENHANCED SCRIPT", 
                            data=final_pdf, 
                            file_name=final_filename, 
                            mime="application/pdf"
                        )

                    except Exception as e:
                        st.error(f"NEURAL INTERRUPT: {str(e)}")

    with tab2:
        st.header("ARCHIVED SESSIONS")
        st.info("DATA PERSISTENCE ENGINE INITIALIZING... HISTORY WILL APPEAR HERE IN NEXT VERSION.")
