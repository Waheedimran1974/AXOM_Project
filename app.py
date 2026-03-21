import streamlit as st
from google import genai
import pandas as pd
import os
import smtplib
import random
import io
import json
import re
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from email.message import EmailMessage
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 30px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 20px rgba(0, 212, 255, 0.2); }
    .stButton>button { width: 100%; background: transparent; color: #00d4ff; border: 1px solid #00d4ff; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; }
    .stButton>button:hover { background: #00d4ff !important; color: #000 !important; box-shadow: 0 0 15px #00d4ff; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND UTILITIES ---
# Ensure you have "GENAI_API_KEY", "SENDER_EMAIL", and "APP_PASSWORD" in your Secrets!
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.0-flash"
HISTORY_FILE = "axom_history.csv"

def get_grade(perc):
    if perc >= 80: return "A*"
    if perc >= 70: return "A"
    if perc >= 60: return "B"
    if perc >= 50: return "C"
    return "D/E"

def send_otp(email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"AXOM ACCESS KEY: {otp}")
    msg['Subject'] = "AXOM | NEURAL KEY"
    msg['From'] = st.secrets["SENDER_EMAIL"]
    msg['To'] = email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SENDER_EMAIL"], st.secrets["APP_PASSWORD"])
            server.send_message(msg)
        return otp
    except Exception as e:
        st.error(f"Mail Error: {e}")
        return None

def robust_json_parser(text):
    """Extracts JSON from AI text even if it includes markdown or chatter."""
    try:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return []
    except:
        return []

def mark_visuals(image, marks_data):
    """Draws marks and prepares sticky note coordinates."""
    draw = ImageDraw.Draw(image)
    # Scalable font size based on image height
    f_size = int(image.height * 0.04) 
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", f_size)
    except:
        font = ImageFont.load_default()
    
    ticks = 0
    notes = []
    for m in marks_data:
        # AI provides 0-1000 coordinates for consistency
        x = int((m.get('x', 50) / 1000) * image.width)
        y = int((m.get('y', 50) / 1000) * image.height)
        
        char = "✓" if m['type'] == 'tick' else "✕"
        draw.text((x, y), char, fill=(239, 68, 68), font=font)
        
        if m['type'] == 'tick': ticks += 1
        if 'comment' in m:
            notes.append({'x': x, 'y': y, 'txt': m['comment']})
    return image, ticks, notes

# --- 3. SESSION AUTH ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.step = "login"

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        if st.session_state.step == "login":
            st.title("AXOM ACCESS")
            u_email = st.text_input("EMAIL")
            if st.button("GET KEY"):
                key = send_otp(u_email)
                if key:
                    st.session_state.otp, st.session_state.u_email, st.session_state.step = key, u_email, "verify"
                    st.rerun()
        else:
            st.title("VERIFY KEY")
            u_otp = st.text_input("6-DIGIT KEY", type="password")
            if st.button("UNLOCK"):
                if u_otp == st.session_state.otp:
                    st.session_state.logged_in = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MAIN INTERFACE ---
else:
    t1, t2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with t1:
        st.header("NEURAL SCANNER")
        up_script = st.file_uploader("UPLOAD SCRIPT", type=['pdf'])
        up_ms = st.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])
        
        c1, c2 = st.columns(2)
        with c1: board = st.text_input("EXAM BOARD", "Cambridge")
        with c2: code = st.text_input("SUBJECT CODE", "IGCSE Science")

        if up_script and st.button("INITIALIZE ANALYSIS"):
            with st.spinner("AXOM IS THINKING..."):
                try:
                    script_imgs = convert_from_bytes(up_script.read())
                    ms_text = ""
                    if up_ms:
                        # Simple MS integration: In a full build, you'd extract text from MS PDF
                        ms_text = "Use the provided Mark Scheme logic."

                    pdf = FPDF()
                    # Cover
                    pdf.add_page()
                    pdf.set_fill_color(0, 18, 46); pdf.rect(0,0,210,297,'F')
                    pdf.set_text_color(0, 212, 255); pdf.set_font("Arial",'B',30)
                    pdf.cell(0, 100, "AXOM EVALUATION", ln=True, align='C')
                    
                    all_ticks, all_possible = 0, 0
                    
                    for i, img in enumerate(script_imgs):
                        prompt = (f"Strict {board} examiner mode. Subject: {code}. {ms_text} "
                                  f"Mark page {i+1}. Give Ticks for correct, Crosses for wrong. "
                                  "Coordinates (x,y) must be 0-1000. "
                                  "Output ONLY JSON: [{'type':'tick'|'cross','x':int,'y':int,'comment':str}]")
                        
                        response = client.models.generate_content(model=MODEL_ID, contents=[prompt, img])
                        data = robust_json_parser(response.text)
                        
                        marked_img, p_ticks, p_notes = mark_visuals(img, data)
                        all_ticks += p_ticks
                        all_possible += len(data)
                        
                        # Add Page to PDF
                        pdf.add_page()
                        tmp = f"p{i}.png"; marked_img.save(tmp)
                        pdf.image(tmp, 0, 0, 210, 297); os.remove(tmp)
                        
                        # Add Sticky Notes (Annotations)
                        for n in p_notes:
                            pdf.text_annotation(x=(n['x']/marked_img.width)*210, y=(n['y']/marked_img.height)*297, text=n['txt'])

                    # Finalize PDF & History
                    final_pdf = bytes(pdf.output())
                    perc = (all_ticks/all_possible*100) if all_possible > 0 else 0
                    grade = get_grade(perc)
                    
                    # Save to History
                    row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), "Email": st.session_state.u_email, "Board": board, "Subject": code, "Result": f"{all_ticks}/{all_possible}", "Grade": grade}])
                    row.to_csv(HISTORY_FILE, mode='a', header=not os.path.exists(HISTORY_FILE), index=False)
                    
                    st.success(f"ANALYSIS COMPLETE: {grade}")
                    st.download_button(f"📥 DOWNLOAD {up_script.name.replace('.pdf','')}_checked by AXOM.pdf", data=final_pdf, file_name=f"{up_script.name.replace('.pdf','')}_checked by AXOM.pdf")
                except Exception as e:
                    st.error(f"CRITICAL ERROR: {e}")

    with t2:
        st.header("DATA ARCHIVE")
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_df = df[df['Email'] == st.session_state.u_email]
            st.table(user_df.drop(columns=['Email']))
        else:
            st.info("Archive empty. Complete a scan to begin.")
