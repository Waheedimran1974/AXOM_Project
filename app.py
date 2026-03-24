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
    .ad-banner { background: linear-gradient(45deg, #FFD700, #DAA520); color: #000; padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; margin-top: 20px; border: 2px solid #fff; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE DATABASE & SUBSCRIPTION SYSTEM ---
DB_FILE = "axom_users.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["email", "tier", "credits"])
        df.to_csv(DB_FILE, index=False)

def get_user_data(email):
    df = pd.read_csv(DB_FILE)
    if email in df['email'].values:
        user = df[df['email'] == email].iloc[0]
        return user['tier'], int(user['credits'])
    else:
        # New user gets Free Tier and 3 Credits
        new_row = pd.DataFrame({"email": [email], "tier": ["Free"], "credits": [3]})
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        return "Free", 3

def deduct_credit(email):
    df = pd.read_csv(DB_FILE)
    df.loc[df['email'] == email, 'credits'] -= 1
    df.to_csv(DB_FILE, index=False)

init_db()

# --- 3. BACKEND ENGINES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash" 

def apply_watermark(base_image, logo_path="logo.jpg"):
    """Fuses the AXOM Logo into the center of the student's paper"""
    try:
        watermark = Image.open(logo_path).convert("RGBA")
        # Resize logo to cover 60% of the page
        wm_width = int(base_image.width * 0.6)
        wpercent = (wm_width/float(watermark.size[0]))
        wm_height = int((float(watermark.size[1])*float(wpercent)))
        watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)

        # Drop opacity to 15%D (Ghost effect)
        alpha = watermark.split()[3]
        alpha = alpha.point(lambda p: p * 0.15)
        watermark.putalpha(alpha)

        # Center and paste
        position = ((base_image.width - wm_width) // 2, (base_image.height - wm_height) // 2)
        transparent = Image.new('RGBA', base_image.size, (0,0,0,0))
        transparent.paste(base_image, (0,0))
        transparent.paste(watermark, position, mask=watermark)
        return transparent.convert("RGB")
    except Exception as e:
        return base_image # If logo.jpg is missing, skip watermark

def add_axom_branding(pdf):
    """Applies Footer Branding and Cross-Sell Ads"""
    pdf.set_y(-25)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 5, "POWERED BY AXOM NEURAL INTERFACE", align='R', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, f"Date: {datetime.now().strftime('%d/%m/%Y')} | Verified via Gemini 2.5 Logic Engine", align='R', new_x="LMARGIN", new_y="NEXT")
    
    # The Cross-Sell Footer Ad
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_text_color(218, 165, 32) # Gold
    pdf.cell(0, 5, "► UPGRADE TO AXOM PRO OR VISIT NEXT STEP FUTURE (NSF) FOR 1-ON-1 TUTORING", align='R')
    pdf.set_text_color(0, 0, 0)

def generate_correction_graph(eq_str, fname="axom_plt.png"):
    try:
        plt.figure(figsize=(6, 4))
        x = np.linspace(-10, 10, 400)
        y = eval(eq_str.replace('^', '**').replace('y=', '').strip(), {"np": np, "x": x, "sin": np.sin, "cos": np.cos})
        plt.plot(x, y, color='#00d4ff', linewidth=2)
        plt.axhline(0, color='black', lw=1); plt.axvline(0, color='black', lw=1)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.savefig(fname, bbox_inches='tight'); plt.close('all')
        return True
    except: return False

def send_otp(recip, code):
    try:
        msg = EmailMessage()
        msg.set_content(f"AXOM SYSTEM ACCESS.\n\nKey: {code}")
        msg['Subject'] = 'AXOM SECURITY'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recip
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"]); s.send_message(msg)
        return True
    except: return False

# --- 4. SECURITY GATEWAY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        try: st.image("logo.jpg", width=150) # Tries to load your logo
        except: pass
        st.title("AXOM | ACCESS")
        if not st.session_state.otp_sent:
            u_email = st.text_input("ENTER REGISTERED EMAIL")
            if st.button("GET SECURITY KEY"):
                code = str(random.randint(100000, 999999))
                if send_otp(u_email, code):
                    st.session_state.generated_otp, st.session_state.target_email, st.session_state.otp_sent = code, u_email, True
                    st.rerun()
        else:
            u_otp = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("UNLOCK INTERFACE"):
                if u_otp == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. THE NEURAL INTERFACE ---
else:
    # Check Subscription Status
    user_tier, credits_left = get_user_data(st.session_state.target_email)

    with st.sidebar:
        try: st.image("logo.jpg", use_column_width=True)
        except: pass
        st.markdown(f"**USER:** `{st.session_state.target_email}`")
        st.markdown(f"**TIER:** `{user_tier}`")
        st.markdown(f"**CREDITS:** `{credits_left}` remaining")
        
        # THE AD SYSTEM
        st.markdown("""
        <div class="ad-banner">
            🚀 COMING SOON: AXON<br>
            <span style='font-size:12px; font-weight:normal;'>Next-Gen Video Learning System.</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        if st.button("TERMINATE SESSION"):
            st.session_state.logged_in = False; st.session_state.otp_sent = False; st.rerun()

    st.header("NEURAL SCANNER")
    
    if credits_left <= 0 and user_tier != "Admin":
        st.error("INSUFFICIENT CREDITS. Please upgrade your subscription to continue scanning.")
    else:
        col1, col2 = st.columns(2)
        with col1: board_name = st.text_input("EXAM BOARD", "")
        with col2: subject_name = st.text_input("SUBJECT/CODE", "")

        up_script = st.file_uploader("1. UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_ms = st.file_uploader("2. UPLOAD MARK SCHEME (PDF) - OPTIONAL", type=['pdf'])
        
        if up_script and st.button("EXECUTE FULL SCAN (-1 Credit)"):
            with st.spinner("INITIATING EDU AI..."):
                try:
                    script_imgs = convert_from_bytes(up_script.read())
                    ms_data = "Standard IGCSE criteria."
                    if up_ms:
                        ms_imgs = convert_from_bytes(up_ms.read())
                        ms_data = client.models.generate_content(model=MODEL_ID, contents=["Extract marks:", ms_imgs[0]]).text

                    pdf = FPDF()
                    all_comments = []
                    prompt = f"Board: {board_name} {subject_name}. MS: {ms_data}. For bad graphs write 'CORRECTION: y=f(x)'. Output JSON: [{{'type':'tick'|'cross','x':int,'y':int,'comment':str}}]"

                    for i, img in enumerate(script_imgs):
                        resp = client.models.generate_content(model=MODEL_ID, contents=[prompt, img])
                        match = re.search(r'\[.*\]', resp.text, re.DOTALL)
                        marks = json.loads(match.group(0)) if match else []
                        
                        draw = ImageDraw.Draw(img)
                        for m in marks:
                            px, py = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                            draw.text((px, py), "✓" if m['type']=='tick' else "✕", fill=(255,0,0))
                            all_comments.append(m['comment'])
                        
                        # 1. APPLY WATERMARK TO IMAGE BEFORE SAVING TO PDF
                        watermarked_img = apply_watermark(img)
                        
                        pdf.add_page()
                        tmp_path = f"ax_pg_{i}_{int(time.time())}.png"
                        watermarked_img.save(tmp_path)
                        pdf.image(tmp_path, x=0, y=0, w=210, h=297)
                        add_axom_branding(pdf) # 2. APPLY FOOTER ADS
                        os.remove(tmp_path)

                    pdf.add_page()
                    pdf.set_font("Helvetica", 'B', 16)
                    pdf.cell(200, 10, f"AXOM NEURAL FEEDBACK", new_x="LMARGIN", new_y="NEXT", align='C')
                    
                    y_cursor = 30
                    for c in all_comments:
                        if "CORRECTION:" in c and y_cursor < 240:
                            f_str = c.split("CORRECTION:")[1].strip()
                            if generate_correction_graph(f_str, "tmp_graph.png"):
                                pdf.set_font("Helvetica", '', 11); pdf.set_xy(10, y_cursor)
                                pdf.multi_cell(190, 8, f"Correction: {f_str}"); pdf.image("tmp_graph.png", x=10, y=y_cursor+10, w=90)
                                y_cursor += 85; os.remove("tmp_graph.png")
                    
                    add_axom_branding(pdf)

                    # 3. DEDUCT CREDIT UPON SUCCESS
                    deduct_credit(st.session_state.target_email)

                    st.success("SCAN COMPLETE: CREDITS DEDUCTED")
                    st.download_button("📥 DOWNLOAD MARKED SCRIPT", data=bytes(pdf.output()), file_name=f"AXOM_Review.pdf")

                except Exception as e: st.error(f"ENGINE CRASH: {e}")
