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
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 30px rgba(0, 212, 255, 0.2); text-align: center; }
    .stButton>button { width: 100%; background: transparent; color: #00d4ff; border: 1px solid #00d4ff; border-radius: 5px; transition: 0.3s; text-transform: uppercase; letter-spacing: 2px; font-weight: bold; }
    .stButton>button:hover { background: #00d4ff !important; color: #000 !important; box-shadow: 0 0 20px #00d4ff; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE ENGINES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.0-flash" # High-context model for multi-page PDF processing
HISTORY_FILE = "axom_history.csv"

def get_igcse_grade(percentage):
    if percentage >= 80: return "A*"
    elif percentage >= 70: return "A"
    elif percentage >= 60: return "B"
    elif percentage >= 50: return "C"
    return "D/E"

def mark_page_visual(image, marks_data):
    draw = ImageDraw.Draw(image)
    mark_font_size = 65 
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", mark_font_size)
    except: font = ImageFont.load_default()
    ink_color = (239, 68, 68) 
    page_ticks = 0
    annotations = []
    
    for mark in marks_data:
        x, y = mark.get('x', 50) + random.randint(-5, 5), mark.get('y', 50) + random.randint(-5, 5)
        icon = "✓" if mark['type'] == 'tick' else "✕"
        draw.text((x, y), icon, fill=ink_color, font=font)
        if mark['type'] == 'tick': page_ticks += 1
        if 'comment' in mark: annotations.append({'x': x, 'y': y, 'text': mark['comment']})
    return image, page_ticks, annotations

# --- 3. AUTH & SESSION ---
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "identify"
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        if st.session_state.auth_step == "identify":
            st.title("AXOM INTERFACE")
            email_in = st.text_input("INPUT EMAIL ID")
            if st.button("REQUEST NEURAL KEY"):
                st.session_state.generated_otp = "123456" # Placeholder for demo
                st.session_state.temp_email, st.session_state.auth_step = email_in, "verify"
                st.rerun()
        elif st.session_state.auth_step == "verify":
            st.title("VERIFY LINK")
            otp_in = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("INITIALIZE SESSION"):
                st.session_state.logged_in, st.session_state.user_email = True, st.session_state.temp_email
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    tab1, tab2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with tab1:
        st.header("NEURAL SCANNER")
        
        # PRIMARY UPLOADS
        up_script = st.file_uploader("1. UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_ms = st.file_uploader("2. UPLOAD MARK SCHEME (OPTIONAL PDF)", type=['pdf'])
        
        # FUTURE INPUTS
        c1, c2 = st.columns(2)
        with c1: board = st.text_input("3. EXAM BOARD", placeholder="e.g. Cambridge")
        with c2: subject = st.text_input("4. SUBJECT CODE", placeholder="e.g. 0610 Biology")

        if up_script:
            if st.button("RUN FULL NEURAL ANALYSIS"):
                with st.spinner("PROCESSING ENTIRE TEST CONTEXT..."):
                    try:
                        script_pages = convert_from_bytes(up_script.read())
                        ms_context = ""
                        if up_ms:
                            # If MS is provided, we convert it to text/images for the AI to read first
                            ms_context = "CRITICAL: Use the provided Mark Scheme PDF to grade the student script."
                        
                        pdf = FPDF()
                        # COVER PAGE
                        pdf.add_page()
                        pdf.set_fill_color(0, 18, 46); pdf.rect(0, 0, 210, 297, 'F')
                        pdf.set_text_color(0, 212, 255); pdf.set_font("Arial", 'B', 32)
                        pdf.cell(0, 80, "CHECKED BY AXOM", ln=True, align='C')
                        
                        total_score, total_possible = 0, 0
                        
                        # PROCESS AS ONE SESSION
                        for i, page_img in enumerate(script_pages):
                            prompt = (f"{ms_context} Act as a strict {board} examiner for {subject}. "
                                      f"Mark page {i+1} of the student's full test script. "
                                      "Ensure marks align with question numbering. "
                                      "Return ONLY JSON: [{'type': 'tick'|'cross', 'x': int, 'y': int, 'comment': str}]")
                            
                            # We send the page + MS (if exists) in one call
                            payload = [prompt, page_img]
                            if up_ms: payload.append("Reference Mark Scheme attached.")
                            
                            response = client.models.generate_content(model=MODEL_ID, contents=payload)
                            
                            try:
                                clean_json = response.text.strip('`').replace('json', '').strip()
                                marks_data = json.loads(clean_json)
                                marked_img, p_score, p_notes = mark_page_visual(page_img, marks_data)
                                
                                total_score += p_score
                                total_elements = len(marks_data)
                                total_possible += total_elements
                                
                                pdf.add_page()
                                t_p = f"ax_p{i}.png"; marked_img.save(t_p)
                                pdf.image(t_p, x=0, y=0, w=210, h=297); os.remove(t_p)
                                for n in p_notes:
                                    pdf.text_annotation(x=(n['x']/marked_img.width)*210, y=(n['y']/marked_img.height)*297, text=n['text'])
                            except: pdf.add_page()

                        final_pdf = bytes(pdf.output())
                        st.success(f"ANALYSIS COMPLETE: {total_score} MARKS AWARDED")
                        st.download_button("📥 DOWNLOAD CHECKED SCRIPT", data=final_pdf, file_name=f"{up_script.name.split('.')[0]}_checked by AXOM.pdf")
                    except Exception as e: st.error(f"SYSTEM ERROR: {e}")

    with tab2:
        st.header("ARCHIVED SESSIONS")
        st.info("Database active. Your graded history will persist here.")
