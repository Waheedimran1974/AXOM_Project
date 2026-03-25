import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import smtplib
import random
import time
import textwrap
import matplotlib.pyplot as plt
import numpy as np
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | TOTAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 30px rgba(0, 212, 255, 0.3); text-align: center; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border: none !important; border-radius: 5px; height: 45px; font-weight: bold; text-transform: uppercase; }
    .ad-slot { background: #000; border: 1px dashed #ffd700; color: #ffd700; padding: 10px; text-align: center; font-size: 10px; margin-top: 10px; }
    .panel-card { background: rgba(0, 212, 255, 0.05); padding: 20px; border-radius: 10px; border: 1px solid rgba(0, 212, 255, 0.2); margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MULTI-PANEL DATABASE LOGIC ---
DB_FILE = "axom_users.csv"
HISTORY_FILE = "axom_history.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=["email", "tier", "credits", "joined"]).to_csv(DB_FILE, index=False)
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=["email", "date", "board", "subject", "score"]).to_csv(HISTORY_FILE, index=False)

def get_user_data(email):
    df = pd.read_csv(DB_FILE)
    if email in df['email'].values:
        user = df[df['email'] == email].iloc[0]
        return user['tier'], int(user['credits'])
    else:
        new_row = pd.DataFrame({"email": [email], "tier": ["Free"], "credits": [3], "joined": [datetime.now().strftime('%Y-%m-%d')]})
        pd.concat([df, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
        return "Free", 3

def deduct_credit(email):
    df = pd.read_csv(DB_FILE)
    df.loc[df['email'] == email, 'credits'] -= 1
    df.to_csv(DB_FILE, index=False)

def log_scan_history(email, board, subject):
    df_hist = pd.read_csv(HISTORY_FILE)
    new_log = pd.DataFrame({"email": [email], "date": [datetime.now().strftime('%Y-%m-%d %H:%M')], "board": [board], "subject": [subject], "score": ["Scanned"]})
    pd.concat([df_hist, new_log], ignore_index=True).to_csv(HISTORY_FILE, index=False)

init_db()

# --- 3. THE VISUAL ENGINE (WATERMARKS & STICKY NOTES) ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash"

def apply_watermark(base_image, logo_path="logo.jpg"):
    try:
        wm = Image.open(logo_path).convert("RGBA")
        wm_width = int(base_image.width * 0.5)
        w_percent = (wm_width / float(wm.size[0]))
        wm_height = int((float(wm.size[1]) * float(w_percent)))
        wm = wm.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
        
        alpha = wm.split()[3].point(lambda p: p * 0.15)
        wm.putalpha(alpha)
        
        overlay = Image.new('RGBA', base_image.size, (0,0,0,0))
        pos = ((base_image.width - wm_width) // 2, (base_image.height - wm_height) // 2)
        overlay.paste(wm, pos, mask=wm)
        return Image.alpha_composite(base_image.convert("RGBA"), overlay).convert("RGB")
    except:
        return base_image

def draw_sticky_note(img, x, y, mark_type, text):
    """Draws a professional sticky note with text wrapping directly on the image"""
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    # 1. Draw the Tick or Cross
    mark_color = (0, 200, 0, 255) if mark_type == 'tick' else (220, 0, 0, 255)
    symbol = "✓" if mark_type == 'tick' else "✕"
    
    # Using default font, scaled up by drawing lines if TTF is unavailable
    # Streamlit Cloud doesn't always have nice TTF fonts, so we use a robust method
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
        
    draw.text((x, y), symbol, fill=mark_color, font=font)
    
    # 2. Draw the Sticky Note if there is a comment
    if text and text.strip().lower() not in ["none", "correct", ""]:
        # Wrap text so it fits in a box
        wrapped_text = textwrap.wrap(text, width=25)
        
        line_height = 15 # Default spacing
        box_width = 200
        box_height = (len(wrapped_text) * line_height) + 20
        
        # Position note slightly to the right and below the mark
        box_x = x + 30
        box_y = y + 10
        
        # Keep box inside image boundaries
        if box_x + box_width > img.width: box_x = img.width - box_width - 10
        
        # Draw semi-transparent Yellow Background
        draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height], fill=(255, 242, 171, 230), outline=(200, 180, 50, 255), width=2)
        
        # Draw Black Text inside
        text_y = box_y + 10
        for line in wrapped_text:
            draw.text((box_x + 10, text_y), line, fill=(0, 0, 0, 255), font=font)
            text_y += line_height

    # Merge overlay with original image
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def add_floating_footer(pdf):
    pdf.set_auto_page_break(False)
    pdf.set_y(-25) 
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 10, "POWERED BY AXOM NEURAL INTERFACE", align='R', ln=True)
    pdf.set_y(-15)
    pdf.set_font("Helvetica", 'I', 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, f"LEGAL: AI Evaluation. Verified by AXOM Systems on {datetime.now().strftime('%d/%m/%Y')}.", align='R')
    pdf.set_auto_page_break(True, margin=30)

# --- 4. SECURITY GATEWAY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False

def send_otp(recip, code):
    try:
        msg = EmailMessage(); msg.set_content(f"AXOM ACCESS KEY: {code}"); msg['Subject'] = 'AXOM SECURITY'; msg['From'] = st.secrets["SMTP_EMAIL"]; msg['To'] = recip
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"]); s.send_message(msg)
        return True
    except: return False

# --- 5. THE INTERFACE ---
if not st.session_state.logged_in:
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        if os.path.exists("logo.jpg"): st.image("logo.jpg", width=180)
        st.title("AXOM | ACCESS")
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
                    st.session_state.logged_in = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    tier, creds = get_user_data(st.session_state.target_email)
    
    with st.sidebar:
        if os.path.exists("logo.jpg"): st.image("logo.jpg", use_column_width=True)
        st.write(f"**LEVEL:** {tier}\n\n**POWER:** {creds} Credits")
        menu = st.radio("SELECT PANEL", ["NEURAL SCAN", "REVISION HUB", "ANALYTICS", "SUBSCRIPTION", "SETTINGS"])
        st.divider()
        if tier == "Free": st.markdown('<div class="ad-slot">AD-SPACE: GOOGLE CARBON ADS</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.rerun()

    # --- THE CORE MARKER ---
    if menu == "NEURAL SCAN":
        st.title("🧠 AI NEURAL MARKER")
        if creds <= 0 and tier != "Admin":
            st.error("OUT OF CREDITS. Check Subscription Panel.")
        else:
            c1, c2 = st.columns(2)
            with c1: b_n = st.text_input("EXAM BOARD", "")
            with c2: s_n = st.text_input("SUBJECT", "")
            
            up_s = st.file_uploader("STUDENT SCRIPT (PDF)", type=['pdf'])
            up_m = st.file_uploader("MARK SCHEME (PDF)(OPTIONAL)", type=['pdf'])

            if up_s and st.button("EXECUTE SCAN"):
                if tier == "Free":
                    st.warning("WATCHING VIDEO AD... (3 seconds)")
                    time.sleep(3)
                
                with st.spinner("AI ANALYZING..."):
                    try:
                        s_imgs = convert_from_bytes(up_s.read())
                        m_txt = "Apply rigorous standards."
                        if up_m:
                            m_txt = client.models.generate_content(model=MODEL_ID, contents=["Extract key marking criteria:", convert_from_bytes(up_m.read())[0]]).text

                        pdf = FPDF()
                        
                        # High-Precision JSON Prompt
                        p_txt = f"""
                        Mark this {b_n} {s_n} script using these rules: {m_txt}.
                        Find exactly where the student wrote answers. 
                        OUTPUT ONLY A JSON LIST. NO TEXT.
                        Format strictly as: [{{"type":"tick"|"cross", "x":int (0-1000), "y":int (0-1000), "note":"Short correction or tip"}}]
                        Keep 'note' under 8 words. If correct, leave 'note' empty.
                        """

                        for i, img in enumerate(s_imgs):
                            # 503 Retry Logic
                            m_json = []
                            for _ in range(3):
                                try:
                                    r = client.models.generate_content(model=MODEL_ID, contents=[p_txt, img])
                                    m_json = json.loads(re.search(r'\[.*\]', r.text, re.DOTALL).group(0))
                                    break
                                except: time.sleep(2)
                            
                            # Apply Marks and Sticky Notes
                            marked_img = img.copy()
                            for m in m_json:
                                px, py = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                                marked_img = draw_sticky_note(marked_img, px, py, m['type'], m.get('note', ''))
                            
                            w_img = apply_watermark(marked_img)
                            
                            pdf.add_page()
                            t_p = f"t_{i}.png"; w_img.save(t_p)
                            pdf.image(t_p, x=0, y=0, w=210, h=297)
                            add_floating_footer(pdf)
                            os.remove(t_p)
                        
                        deduct_credit(st.session_state.target_email)
                        log_scan_history(st.session_state.target_email, b_n, s_n)
                        st.success("SCAN COMPLETE")
                        st.download_button("DOWNLOAD MARKED SCRIPT", data=bytes(pdf.output()), file_name="AXOM_Pro_Review.pdf")
                    except Exception as e: st.error(f"ENGINE ERROR: {e}")

    # --- OTHER PANELS (Placeholders from v8.0) ---
    elif menu == "REVISION HUB": st.title("REVISION HUB (In Development)")
    elif menu == "ANALYTICS": st.title("ANALYTICS (In Development)")
    elif menu == "SUBSCRIPTION": st.title("💎 AXOM PREMIUM (In Development)")
    elif menu == "SETTINGS": st.title("⚙️ SETTINGS (In Development)")
