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
    .stButton>button { width: 100%; background: #00d4ff; color: #000; border: none; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; margin-top: 15px; }
    .stButton>button:hover { background: #008fb3 !important; color: #fff !important; box-shadow: 0 0 15px #00d4ff; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; font-size: 20px; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.0-flash" 
HISTORY_FILE = "axom_history.csv"

def generate_correction_graph(equation_str, filename="correction.png"):
    """Generates a mathematical plot based on AI suggestion"""
    try:
        plt.figure(figsize=(5, 4))
        x = np.linspace(-10, 10, 400)
        # Simple safety parser for common exam functions
        safe_eq = equation_str.replace('^', '**').replace('y=', '')
        y = eval(safe_eq, {"np": np, "x": x, "__builtins__": {}})
        plt.plot(x, y, color='#00d4ff', linewidth=2)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.title(f"CORRECTION: {equation_str}", color='black')
        plt.savefig(filename)
        plt.close()
        return True
    except:
        return False

# --- 3. OTP & LOGIN (RETAINED FROM V6.3) ---
def send_otp_email(recipient, otp):
    try:
        msg = EmailMessage()
        msg.set_content(f"AXOM ACCESS CODE: {otp}")
        msg['Subject'] = 'AXOM NEURAL KEY'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recipient
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            server.send_message(msg)
        return True
    except: return False

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        if not st.session_state.otp_sent:
            u_email = st.text_input("EMAIL ID")
            if st.button("SEND CODE"):
                code = str(random.randint(100000, 999999))
                if send_otp_email(u_email, code):
                    st.session_state.generated_otp, st.session_state.target_email, st.session_state.otp_sent = code, u_email, True
                    st.rerun()
        else:
            u_otp = st.text_input("6-DIGIT CODE", type="password")
            if st.button("UNLOCK"):
                if u_otp == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MAIN APP ENGINE ---
else:
    with st.sidebar:
        st.write(f"USER: {st.session_state.target_email}")
        if st.button("LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()

    up_script = st.file_uploader("UPLOAD EXAM SCRIPT (PDF)", type=['pdf'])
    
    if up_script and st.button("INITIALIZE NEURAL EVALUATION"):
        with st.spinner("ANALYZING GRAPHS & GEOMETRY..."):
            try:
                script_imgs = convert_from_bytes(up_script.read())
                pdf = FPDF()
                all_comments = []
                
                # Instruction to AI to provide Plotting Data
                prompt = """Mark this script. If you find a wrong graph or geometry drawing, 
                include 'PLOT: y=f(x)' in your JSON comment where f(x) is the correct math function.
                Output ONLY JSON: [{'type':'tick'|'cross','x':int,'y':int,'comment':str}]"""

                for i, img in enumerate(script_imgs):
                    resp = client.models.generate_content(model=MODEL_ID, contents=[prompt, img])
                    match = re.search(r'\[.*\]', resp.text, re.DOTALL)
                    data = json.loads(match.group(0)) if match else []
                    
                    # Draw marks on image
                    draw = ImageDraw.Draw(img)
                    for m in data:
                        x, y = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                        draw.text((x, y), "✓" if m['type']=='tick' else "✕", fill=(255,0,0))
                        all_comments.append(m['comment'])
                    
                    pdf.add_page()
                    tmp = f"p{i}.png"; img.save(tmp); pdf.image(tmp, 0, 0, 210, 297); os.remove(tmp)

                # --- DYNAMIC GRAPH INJECTION ---
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(200, 10, "AXOM GEOMETRY CORRECTIONS", ln=True, align='C')
                
                y_offset = 30
                for comm in all_comments:
                    if "PLOT:" in comm:
                        eq = comm.split("PLOT:")[1].strip()
                        if generate_correction_graph(eq, "temp_graph.png"):
                            pdf.set_font("Arial", '', 12)
                            pdf.cell(200, 10, f"Corrected Visual for: {eq}", ln=True)
                            pdf.image("temp_graph.png", x=10, y=y_offset, w=100)
                            y_offset += 85
                            os.remove("temp_graph.png")

                st.success("EVALUATION COMPLETE WITH DYNAMIC PLOTS")
                st.download_button("DOWNLOAD FINAL PDF", data=bytes(pdf.output(dest='S')), file_name="AXOM_Full_Review.pdf")

            except Exception as e: st.error(f"ENGINE ERROR: {e}")
