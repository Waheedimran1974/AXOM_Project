import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import csv
import smtplib
import random
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
    .report-box { padding: 20px; border-left: 5px solid #00d4ff; background: rgba(0, 212, 255, 0.1); margin: 10px 0; border-radius: 0 10px 10px 0; color: #fff; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border: none !important; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; margin-top: 15px; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; font-size: 20px; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ENGINES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash" 
HISTORY_FILE = "axom_history.csv"

def generate_correction_graph(equation_str, filename="temp_plot.png"):
    """Creates a high-precision mathematical plot for the PDF report"""
    try:
        plt.figure(figsize=(6, 4))
        x = np.linspace(-10, 10, 400)
        safe_eq = equation_str.replace('^', '**').replace('y=', '').strip()
        y = eval(safe_eq, {"np": np, "x": x, "sin": np.sin, "cos": np.cos, "tan": np.tan, "sqrt": np.sqrt})
        
        plt.plot(x, y, color='#00d4ff', linewidth=2, label=f"y = {safe_eq}")
        plt.axhline(0, color='black', lw=1)
        plt.axvline(0, color='black', lw=1)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        plt.savefig(filename, bbox_inches='tight')
        plt.close('all') # Prevents memory leaks
        return True
    except Exception as e:
        print(f"Plot Error: {e}")
        return False

def send_otp_email(recipient, otp):
    """Sends the 6-digit access key via Secure SMTP"""
    try:
        msg = EmailMessage()
        msg.set_content(f"AXOM SYSTEM ACCESS GRANTED.\n\nYour temporary access key is: {otp}\n\nInitialize interface immediately.")
        msg['Subject'] = 'AXOM SECURITY KEY'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recipient
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            server.send_message(msg)
        return True
    except Exception as e: 
        print(f"SMTP Error: {e}")
        return False

# --- 3. SECURITY GATEWAY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "generated_otp" not in st.session_state: st.session_state.generated_otp = None
if "target_email" not in st.session_state: st.session_state.target_email = ""

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | SECURITY")
        if not st.session_state.otp_sent:
            u_email = st.text_input("ENTER REGISTERED EMAIL")
            if st.button("REQUEST ACCESS KEY"):
                if u_email:
                    with st.spinner("TRANSMITTING..."):
                        code = str(random.randint(100000, 999999))
                        if send_otp_email(u_email, code):
                            st.session_state.generated_otp = code
                            st.session_state.target_email = u_email
                            st.session_state.otp_sent = True
                            st.rerun()
                        else:
                            st.error("Email failed to send. Check SMTP secrets.")
                else:
                    st.warning("Please enter an email.")
        else:
            u_otp = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("UNLOCK NEURAL INTERFACE"):
                if u_otp == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
                else: 
                    st.error("INVALID KEY")
            if st.button("BACK"):
                st.session_state.otp_sent = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. THE NEURAL INTERFACE ---
else:
    with st.sidebar:
        st.write(f"SYSTEM ACTIVE: {st.session_state.target_email}")
        if st.button("TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.session_state.otp_sent = False
            st.rerun()

    t1, t2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with t1:
        st.header("NEURAL SCANNER | MULTI-MODAL")
        up_script = st.file_uploader("UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        
        if up_script and st.button("RUN FULL SCAN"):
            with st.spinner("ANALYZING GEOMETRY & TEXT..."):
                try:
                    script_imgs = convert_from_bytes(up_script.read())
                    pdf = FPDF()
                    all_comments = []
                    
                    # AI marking instructions
                    prompt = "Mark this exam. If a graph/angle is wrong, add 'CORRECTION: y=f(x)' to your comment (e.g., CORRECTION: y=x^2). Output JSON: [{'type':'tick'|'cross','x':int,'y':int,'comment':str}]"

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
                        tmp = f"p{i}.png"
                        img.save(tmp)
                        pdf.image(tmp, x=0, y=0, w=210, h=297)
                        os.remove(tmp)

                    # --- ADDING THE NOTES PAGE WITH DYNAMIC GRAPHS ---
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(200, 10, "AXOM GEOMETRY CORRECTIONS", new_x="LMARGIN", new_y="NEXT", align='C')
                    
                    y_pos = 30
                    for comm in all_comments:
                        if "CORRECTION:" in comm:
                            eq = comm.split("CORRECTION:")[1].strip()
                            if generate_correction_graph(eq, "temp_plot.png"):
                                pdf.set_font("Arial", '', 11)
                                pdf.set_xy(10, y_pos)
                                pdf.multi_cell(190, 10, f"Correct graph for: {eq}")
                                pdf.image("temp_plot.png", x=10, y=y_pos+10, w=100)
                                y_pos += 90
                                os.remove("temp_plot.png")

                    # Generate PDF bytes safely using fpdf2
                    pdf_bytes = bytes(pdf.output())

                    st.success("SCAN COMPLETE")
                    st.download_button("📥 DOWNLOAD MARKED SCRIPT", data=pdf_bytes, file_name="AXOM_Review.pdf", mime="application/pdf")

                except Exception as e: 
                    st.error(f"ENGINE CRASH: {e}")

    with t2:
        st.header("DATA ARCHIVE")
        st.info("Archive sync active. Scanning history will appear here.")
