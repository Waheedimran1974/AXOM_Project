import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import smtplib
import random
import time
import matplotlib.pyplot as plt
import numpy as np
from email.message import EmailMessage
from PIL import Image, ImageDraw
from datetime import datetime
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. CORE STYLE & UI ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 30px rgba(0, 212, 255, 0.3); text-align: center; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border: none !important; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; margin-top: 15px; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    .history-card { background: rgba(0, 212, 255, 0.05); padding: 10px; border-left: 3px solid #00d4ff; margin-bottom: 8px; font-size: 12px; }
    .sidebar-logo { display: block; margin-left: auto; margin-right: auto; width: 80%; padding-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE & HISTORY ENGINES ---
DB_FILE = "axom_users.csv"
HISTORY_FILE = "axom_history.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=["email", "tier", "credits"]).to_csv(DB_FILE, index=False)
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=["email", "date", "board", "subject"]).to_csv(HISTORY_FILE, index=False)

def get_user_data(email):
    df = pd.read_csv(DB_FILE)
    if email in df['email'].values:
        user = df[df['email'] == email].iloc[0]
        return user['tier'], int(user['credits'])
    else:
        new_row = pd.DataFrame({"email": [email], "tier": ["Free"], "credits": [3]})
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        return "Free", 3

def deduct_credit(email):
    df = pd.read_csv(DB_FILE)
    df.loc[df['email'] == email, 'credits'] -= 1
    df.to_csv(DB_FILE, index=False)

def log_scan_history(email, board, subject):
    df_hist = pd.read_csv(HISTORY_FILE)
    new_log = pd.DataFrame({"email": [email], "date": [datetime.now().strftime('%Y-%m-%d %H:%M')], "board": [board], "subject": [subject]})
    pd.concat([df_hist, new_log], ignore_index=True).to_csv(HISTORY_FILE, index=False)

init_db()

# --- 3. VISION & PDF PROCESSING ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash"

def apply_watermark(base_image, logo_path="logo.jpg"):
    """Fuses logo.jpg as a 15% opacity ghost watermark"""
    try:
        wm = Image.open(logo_path).convert("RGBA")
        wm_width = int(base_image.width * 0.5)
        w_percent = (wm_width / float(wm.size[0]))
        wm_height = int((float(wm.size[1]) * float(w_percent)))
        wm = wm.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
        
        # Ghost effect logic
        alpha = wm.split()[3].point(lambda p: p * 0.15)
        wm.putalpha(alpha)
        
        overlay = Image.new('RGBA', base_image.size, (0,0,0,0))
        pos = ((base_image.width - wm_width) // 2, (base_image.height - wm_height) // 2)
        overlay.paste(wm, pos, mask=wm)
        return Image.alpha_composite(base_image.convert("RGBA"), overlay).convert("RGB")
    except:
        return base_image

def add_floating_footer(pdf):
    """Pins AXOM Brand and Legal to current page without overflow"""
    pdf.set_auto_page_break(False)
    pdf.set_y(-25) 
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 10, "POWERED BY AXOM NEURAL INTERFACE", align='R', ln=True)
    
    pdf.set_y(-15)
    pdf.set_font("Helvetica", 'I', 7)
    pdf.set_text_color(150, 150, 150)
    legal = f"LEGAL: AI Evaluation. Verified by AXOM Systems on {datetime.now().strftime('%d/%m/%Y')}. Proprietary."
    pdf.cell(0, 10, legal, align='R')
    pdf.set_auto_page_break(True, margin=30)

def generate_graph(eq, fname="axom_p.png"):
    try:
        plt.figure(figsize=(5, 3))
        x = np.linspace(-10, 10, 400)
        y = eval(eq.replace('^', '**').replace('y=', '').strip(), {"np": np, "x": x, "sin": np.sin, "cos": np.cos})
        plt.plot(x, y, color='#00d4ff', lw=2)
        plt.grid(True, alpha=0.3); plt.savefig(fname, bbox_inches='tight'); plt.close('all')
        return True
    except: return False

# --- 4. SECURITY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

def send_otp(recip, code):
    try:
        msg = EmailMessage()
        msg.set_content(f"AXOM ACCESS KEY: {code}"); msg['Subject'] = 'AXOM SECURITY'; msg['From'] = st.secrets["SMTP_EMAIL"]; msg['To'] = recip
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"]); s.send_message(msg)
        return True
    except: return False

# --- 5. INTERFACE LOGIC ---
if not st.session_state.logged_in:
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        if os.path.exists("logo.jpg"): st.image("logo.jpg", width=180)
        st.title("AXOM | NEURAL")
        if not st.session_state.otp_sent:
            em = st.text_input("EMAIL")
            if st.button("GET KEY"):
                c = str(random.randint(100000, 999999))
                if send_otp(em, c):
                    st.session_state.generated_otp, st.session_state.target_email, st.session_state.otp_sent = c, em, True
                    st.rerun()
        else:
            otp = st.text_input("6-DIGIT KEY", type="password")
            if st.button("UNLOCK"):
                if otp == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    tier, creds = get_user_data(st.session_state.target_email)
    with st.sidebar:
        if os.path.exists("logo.jpg"): st.image("logo.jpg", use_column_width=True)
        st.markdown(f"**USER:** `{st.session_state.target_email}`\n**CREDITS:** `{creds}`")
        st.divider()
        st.markdown("### hISTORY")
        h_df = pd.read_csv(HISTORY_FILE)
        u_h = h_df[h_df['email'] == st.session_state.target_email].tail(5).iloc[::-1]
        for _, r in u_h.iterrows():
            st.markdown(f"<div class='history-card'><strong>{r['subject']}</strong><br>{r['date']}</div>", unsafe_allow_html=True)
        if st.button("LOGOUT"):
            st.session_state.logged_in = False; st.session_state.otp_sent = False; st.rerun()

    st.header("NEURAL SCANNER")
    if creds <= 0 and tier != "Admin":
        st.error("OUT OF CREDITS.")
    else:
        b_n = st.text_input("EXAM BOARD", "")
        s_n = st.text_input("SUBJECT", "")
        up_s = st.file_uploader("STUDENT SCRIPT (PDF)", type=['pdf'])
        up_m = st.file_uploader("MARK SCHEME (PDF)", type=['pdf'])

        if up_s and st.button("START SCAN"):
            with st.spinner("AI ANALYZING..."):
                try:
                    s_imgs = convert_from_bytes(up_s.read())
                    m_txt = "Apply general IGCSE standards."
                    if up_m:
                        m_txt = client.models.generate_content(model=MODEL_ID, contents=["Extract marks:", convert_from_bytes(up_m.read())[0]]).text

                    pdf = FPDF()
                    all_c = []
                    p_txt = f"Mark this {b_n} {s_n} script using {m_txt}. If a graph is wrong, include 'CORRECTION: y=f(x)'. OUTPUT ONLY JSON: [{{'type':'tick'|'cross','x':int,'y':int,'comment':str}}]"

                    for i, img in enumerate(s_imgs):
                        # 503 Retry Logic
                        for _ in range(3):
                            try:
                                r = client.models.generate_content(model=MODEL_ID, contents=[p_txt, img])
                                m_json = json.loads(re.search(r'\[.*\]', r.text, re.DOTALL).group(0))
                                break
                            except: time.sleep(2)
                        
                        draw = ImageDraw.Draw(img)
                        for m in m_json:
                            px, py = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                            draw.text((px, py), "✓" if m['type']=='tick' else "✕", fill=(255,0,0) if m['type']=='cross' else (0,255,0), font_size=40)
                            all_c.append(f"Pg {i+1}: {m['comment']}")
                        
                        w_img = apply_watermark(img)
                        pdf.add_page()
                        t_p = f"t_{i}.png"; w_img.save(t_p)
                        pdf.image(t_p, x=0, y=0, w=210, h=297)
                        add_floating_footer(pdf) # Fixes the additional page issue
                        os.remove(t_p)

                    # Corrections Page
                    pdf.add_page(); pdf.set_font("Helvetica", 'B', 16); pdf.cell(0, 10, "FEEDBACK", ln=True, align='C')
                    y_c = 30
                    for c in all_c:
                        if "CORRECTION:" in c and y_c < 240:
                            f = c.split("CORRECTION:")[1].strip()
                            if generate_graph(f, "g.png"):
                                pdf.set_xy(10, y_c); pdf.set_font("Helvetica", size=10); pdf.multi_cell(0, 5, c)
                                pdf.image("g.png", x=10, y=y_c+10, w=80); y_c += 70; os.remove("g.png")
                    
                    add_floating_footer(pdf)
                    deduct_credit(st.session_state.target_email)
                    log_scan_history(st.session_state.target_email, b_n, s_n)
                    st.download_button("📥 DOWNLOAD", data=bytes(pdf.output()), file_name="AXOM_Marked.pdf")
                except Exception as e: st.error(f"ENGINE ERROR: {e}")
