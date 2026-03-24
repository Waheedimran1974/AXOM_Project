import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import csv
import smtplib
import random
import time
import matplotlib.pyplot as plt
import numpy as np
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
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border: none !important; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; margin-top: 15px; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ENGINES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.0-flash" 

def generate_correction_graph(equation_str, filename="temp_plot.png"):
    try:
        plt.figure(figsize=(6, 4))
        x = np.linspace(-10, 10, 400)
        safe_eq = equation_str.replace('^', '**').replace('y=', '').strip()
        y = eval(safe_eq, {"np": np, "x": x, "sin": np.sin, "cos": np.cos, "tan": np.tan, "sqrt": np.sqrt})
        plt.plot(x, y, color='#00d4ff', linewidth=2, label=f"y = {safe_eq}")
        plt.axhline(0, color='black', lw=1); plt.axvline(0, color='black', lw=1)
        plt.grid(True, linestyle='--', alpha=0.5); plt.legend()
        plt.savefig(filename, bbox_inches='tight')
        plt.close('all')
        return True
    except: return False

def send_otp_email(recipient, otp):
    try:
        msg = EmailMessage()
        msg.set_content(f"AXOM SYSTEM ACCESS GRANTED.\n\nYour temporary access key is: {otp}")
        msg['Subject'] = 'AXOM SECURITY KEY'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recipient
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            server.send_message(msg)
        return True
    except: return False

# --- 3. LOGIN SECURITY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | SECURITY")
        if not st.session_state.otp_sent:
            u_email = st.text_input("ENTER EMAIL")
            if st.button("REQUEST ACCESS KEY"):
                code = str(random.randint(100000, 999999))
                if send_otp_email(u_email, code):
                    st.session_state.generated_otp, st.session_state.target_email, st.session_state.otp_sent = code, u_email, True
                    st.rerun()
        else:
            u_otp = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("UNLOCK"):
                if u_otp == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. THE INTERFACE ---
else:
    with st.sidebar:
        st.write(f"SYSTEM ACTIVE: {st.session_state.target_email}")
        if st.button("TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.session_state.otp_sent = False
            st.rerun()

    st.header("NEURAL SCANNER | MULTI-MODAL")
    
    col_a, col_b = st.columns(2)
    with col_a: board_name = st.text_input("EXAM BOARD", "Cambridge")
    with col_b: subject_name = st.text_input("SUBJECT & CODE", "IGCSE Biology")

    up_script = st.file_uploader("1. UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
    up_markscheme = st.file_uploader("2. UPLOAD MARK SCHEME (PDF) - OPTIONAL", type=['pdf'])
    
    if up_script and st.button("RUN FULL NEURAL EVALUATION"):
        with st.spinner("AXOM ANALYZING SCRIPT..."):
            try:
                script_imgs = convert_from_bytes(up_script.read())
                
                # OPTIONAL MARK SCHEME LOGIC
                ms_text = "Use standard IGCSE/A-Level academic marking criteria."
                if up_markscheme:
                    ms_imgs = convert_from_bytes(up_markscheme.read())
                    ms_resp = client.models.generate_content(model=MODEL_ID, contents=["Summarize key points for marking from this mark scheme:", ms_imgs[0]])
                    ms_text = ms_resp.text

                pdf = FPDF()
                all_comments = []
                
                prompt = f"""
                Senior Examiner Mode: {board_name} {subject_name}. 
                Mark Scheme Data: {ms_text}
                If a graph/angle is wrong, add 'CORRECTION: y=f(x)' to your comment.
                Output ONLY JSON: [{{'type':'tick'|'cross','x':int,'y':int,'comment':str}}]
                """

                for i, img in enumerate(script_imgs):
                    resp = client.models.generate_content(model=MODEL_ID, contents=[prompt, img])
                    match = re.search(r'\[.*\]', resp.text, re.DOTALL)
                    data = json.loads(match.group(0)) if match else []
                    
                    draw = ImageDraw.Draw(img)
                    for m in data:
                        x, y = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                        draw.text((x, y), "✓" if m['type']=='tick' else "✕", fill=(255,0,0))
                        all_comments.append(m['comment'])
                    
                    pdf.add_page()
                    # CRASH FIX: Unique filename and verify save
                    tmp_name = f"page_cache_{i}_{random.randint(1,999)}.png"
                    img.save(tmp_name)
                    if os.path.exists(tmp_name):
                        pdf.image(tmp_name, x=0, y=0, w=210, h=297)
                        os.remove(tmp_name) # Clean up immediately

                # ADDING CORRECTIONS PAGE
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(200, 10, f"{board_name} {subject_name} - CORRECTIONS", new_x="LMARGIN", new_y="NEXT", align='C')
                
                y_pos = 30
                for comm in all_comments:
                    if "CORRECTION:" in comm and y_pos < 250:
                        eq = comm.split("CORRECTION:")[1].strip()
                        if generate_correction_graph(eq, "temp_plt.png"):
                            pdf.set_font("Helvetica", '', 11); pdf.set_xy(10, y_pos)
                            pdf.multi_cell(190, 10, f"Correct graph for: {eq}")
                            pdf.image("temp_plt.png", x=10, y=y_pos+10, w=100)
                            y_pos += 90; os.remove("temp_plt.png")

                st.success("SCAN COMPLETE")
                st.download_button("📥 DOWNLOAD MARKED SCRIPT", data=bytes(pdf.output()), file_name=f"AXOM_Review.pdf")

            except Exception as e: st.error(f"ENGINE ERROR: {e}")
