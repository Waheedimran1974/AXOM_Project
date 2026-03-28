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
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border: none !important; border-radius: 5px; height: 45px; font-weight: bold; text-transform: uppercase; margin-top: 10px; }
    .ad-slot { background: #000; border: 1px dashed #ffd700; color: #ffd700; padding: 10px; text-align: center; font-size: 10px; margin-top: 10px; }
    
    /* PRO PRICING CARDS */
    .pricing-card { border-radius: 15px; padding: 20px; text-align: center; border: 2px solid #00d4ff; background: rgba(0, 20, 46, 0.8); margin-bottom: 15px;}
    .highlight { border: 3px solid #FF4B4B; box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.3); transform: scale(1.02); }
    .vip-gold { background: linear-gradient(145deg, #FFD700, #FFA500); color: black !important; font-weight: bold; border: none; }
    
    /* HUB CARDS */
    .video-card { border: 1px solid rgba(0, 212, 255, 0.3); background: rgba(0, 20, 46, 0.5); padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    .priority-card { border: 2px solid #FF4B4B; background: rgba(46, 0, 0, 0.5); box-shadow: 0 0 15px rgba(255, 75, 75, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MULTI-PANEL DATABASE LOGIC ---
DB_FILE = "axom_users.csv"
HISTORY_FILE = "axom_history.csv"

def init_db():
    if not os.path.exists(DB_FILE): pd.DataFrame(columns=["email", "tier", "credits", "joined"]).to_csv(DB_FILE, index=False)
    if not os.path.exists(HISTORY_FILE): pd.DataFrame(columns=["email", "date", "board", "subject", "score"]).to_csv(HISTORY_FILE, index=False)

def get_user_data(email):
    df = pd.read_csv(DB_FILE)
    if email in df['email'].values:
        user = df[df['email'] == email].iloc[0]
        return user['tier'], int(user['credits'])
    else:
        new_row = pd.DataFrame({"email": [email], "tier": ["Free"], "credits": [3], "joined": [datetime.now().strftime('%Y-%m-%d')]})
        pd.concat([df, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
        return "Free", 3

def deduct_credit(email, amount=1):
    df = pd.read_csv(DB_FILE)
    df.loc[df['email'] == email, 'credits'] -= amount
    df.to_csv(DB_FILE, index=False)

def redeem_credits(email, code_input):
    if code_input.startswith("AXOM-") and len(code_input) > 10:
        df = pd.read_csv(DB_FILE)
        if "VIP" in code_input:
            df.loc[df['email'] == email, 'credits'] += 150; df.loc[df['email'] == email, 'tier'] = "VIP"
        elif "CRUSH" in code_input:
            df.loc[df['email'] == email, 'credits'] += 60; df.loc[df['email'] == email, 'tier'] = "Pro"
        else:
            df.loc[df['email'] == email, 'credits'] += 21
            if df.loc[df['email'] == email, 'tier'].values[0] == "Free": df.loc[df['email'] == email, 'tier'] = "Pro"
        df.to_csv(DB_FILE, index=False); return True
    return False

def log_scan_history(email, board, subject):
    df_hist = pd.read_csv(HISTORY_FILE)
    new_log = pd.DataFrame({"email": [email], "date": [datetime.now().strftime('%Y-%m-%d %H:%M')], "board": [board], "subject": [subject], "score": ["Scanned"]})
    pd.concat([df_hist, new_log], ignore_index=True).to_csv(HISTORY_FILE, index=False)

init_db()

# --- 3. REVISION HUB KNOWLEDGE BASE ---
VIDEO_DATABASE = {
    "Physics": {
        "Electricity & Circuits": "https://www.youtube.com/watch?v=mc979OhitAg",
        "Forces & Motion": "https://www.youtube.com/watch?v=aFO4PBolwFg",
        "Thermal Physics": "https://www.youtube.com/watch?v=kR2eXw2E8i0"
    },
    "Chemistry": {
        "Moles & Stoichiometry": "https://www.youtube.com/watch?v=SjQG3rKSZUQ",
        "Organic Chemistry": "https://www.youtube.com/watch?v=UloIw7dhnls"
    },
    "English": {
        "Essay Structure": "https://www.youtube.com/watch?v=GgwZz910f1k",
        "Advanced Punctuation": "https://www.youtube.com/watch?v=wX-y0M-Y80w"
    }
}

# --- 4. THE VISUAL ENGINE ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash"

def apply_watermark(base_image, logo_path="logo.jpg"):
    try:
        wm = Image.open(logo_path).convert("RGBA")
        wm_width = int(base_image.width * 0.4); w_percent = (wm_width / float(wm.size[0]))
        wm_height = int((float(wm.size[1]) * float(w_percent)))
        wm = wm.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
        alpha = wm.split()[3].point(lambda p: p * 0.12); wm.putalpha(alpha)
        overlay = Image.new('RGBA', base_image.size, (0,0,0,0))
        pos = ((base_image.width - wm_width) // 2, (base_image.height - wm_height) // 2)
        overlay.paste(wm, pos, mask=wm)
        return Image.alpha_composite(base_image.convert("RGBA"), overlay).convert("RGB")
    except: return base_image

def draw_sticky_note(img, x, y, mark_type, text):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    tick_color = (0, 230, 118, 255); cross_color = (255, 50, 50, 255); line_width = 7; mark_size = 30
    if mark_type == 'tick':
        draw.line([(x-mark_size, y), (x-mark_size//3, y+mark_size), (x+mark_size, y-mark_size)], fill=tick_color, width=line_width)
    else:
        draw.line([(x-mark_size, y-mark_size), (x+mark_size, y+mark_size)], fill=cross_color, width=line_width)
        draw.line([(x+mark_size, y-mark_size), (x-mark_size, y+mark_size)], fill=cross_color, width=line_width)

    if text and text.strip().lower() not in ["none", "correct", ""]:
        wrapped_text = textwrap.wrap(text, width=22)
        try: font = ImageFont.truetype("arial.ttf", 20)
        except: font = ImageFont.load_default()
        bx, by = x + 45, y - 25; box_width = 240; line_height = 24
        if bx + box_width > img.width: bx = x - box_width - 45
        box_body_h = (len(wrapped_text) * line_height) + 25
        draw.rectangle([bx+5, by+5, bx+box_width+5, by+box_body_h+5], fill=(0,0,0,90))
        draw.rectangle([bx, by, bx+box_width, by+box_body_h], fill=(255, 255, 160, 255), outline=(0,0,0,255), width=2)
        draw.rectangle([bx, by, bx+box_width, by+10], fill=(255, 200, 0, 255))
        ty = by + 18
        for line in wrapped_text:
            draw.text((bx + 15, ty), line, fill=(0, 0, 0, 255), font=font); ty += line_height
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def add_floating_footer(pdf):
    pdf.set_auto_page_break(False); pdf.set_y(-25); pdf.set_font("Helvetica", 'B', 10); pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 10, "POWERED BY AXOM NEURAL INTERFACE", align='R', ln=True)
    pdf.set_y(-15); pdf.set_font("Helvetica", 'I', 7); pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, f"LEGAL: AI Evaluation. Verified by AXOM Systems on {datetime.now().strftime('%d/%m/%Y')}.", align='R')
    pdf.set_auto_page_break(True, margin=30)

# --- 5. STATE MANAGEMENT & SECURITY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "latest_mistakes" not in st.session_state: st.session_state.latest_mistakes = [] # Memory for the Hub
if "last_subject" not in st.session_state: st.session_state.last_subject = "Physics"

def send_otp(recip, code):
    try:
        msg = EmailMessage(); msg.set_content(f"AXOM ACCESS KEY: {code}"); msg['Subject'] = 'AXOM SECURITY'; msg['From'] = st.secrets["SMTP_EMAIL"]; msg['To'] = recip
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s: s.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"]); s.send_message(msg)
        return True
    except: return False

# --- 6. INTERFACE ---
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
                try: success = send_otp(em, c)
                except: success = True; st.warning(f"DEV MODE: OTP {c}")
                if success:
                    st.session_state.generated_otp, st.session_state.target_email, st.session_state.otp_sent = c, em, True
                    st.rerun()
        else:
            otp = st.text_input("6-DIGIT KEY", type="password")
            if st.button("UNLOCK"):
                if otp == st.session_state.generated_otp: st.session_state.logged_in = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    tier, creds = get_user_data(st.session_state.target_email)
    if tier == "VIP": st.markdown("<style>.stApp { border: 5px solid #FFD700; background: black; }</style>", unsafe_allow_html=True)
    
    with st.sidebar:
        if os.path.exists("logo.jpg"): st.image("logo.jpg", use_column_width=True)
        st.write(f"**LEVEL:** {'🏆 VIP' if tier == 'VIP' else tier}\n\n**POWER:** {creds} Credits")
        menu = st.radio("PANEL", ["NEURAL SCAN", "REVISION HUB", "SUBSCRIPTION", "SETTINGS"])
        if tier == "Free": st.markdown('<div class="ad-slot">ADS: UNIVERSITY ADMISSIONS 2026</div>', unsafe_allow_html=True)
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.session_state.otp_sent = False; st.rerun()

    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL MARKER")
        if creds <= 0 and tier != "Admin": st.error("INSUFFICIENT CREDITS.")
        else:
            c1, c2 = st.columns(2)
            b_n = c1.text_input("BOARD", "IGCSE")
            s_n = c2.selectbox("SUBJECT", ["Physics", "Chemistry", "English"])
            up_s = st.file_uploader("STUDENT SCRIPT", type=['pdf'])

            if up_s and st.button("EXECUTE SCAN"):
                if tier == "Free": st.warning("AD DELAY: 3s"); time.sleep(3)
                with st.spinner("ANALYZING SYLLABUS ALIGNMENT..."):
                    try:
                        s_imgs = convert_from_bytes(up_s.read())
                        cost = max(1, (len(s_imgs) + 4) // 5)
                        if creds < cost and tier != "Admin": st.error(f"Need {cost} credits."); st.stop()

                        # Provide the exact topics to the AI so it matches our Hub database
                        available_topics = list(VIDEO_DATABASE.get(s_n, {}).keys())
                        topic_hint = f" If the answer is a cross, specify the exact 'topic' from this list: {available_topics}." if available_topics else ""
                        
                        p_txt = f"Mark {b_n} {s_n}. Output JSON only: [{{'type':'tick'|'cross', 'x':0-1000, 'y':0-1000, 'note':'msg', 'topic':'topic_name'}}].{topic_hint}"
                        
                        pdf = FPDF()
                        found_mistakes = [] # Temporary list to catch mistakes

                        for i, img in enumerate(s_imgs):
                            r = client.models.generate_content(model=MODEL_ID, contents=[p_txt, img])
                            m_json = json.loads(re.search(r'\[.*\]', r.text, re.DOTALL).group(0))
                            
                            marked_img = img.copy()
                            for m in m_json:
                                px, py = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                                marked_img = draw_sticky_note(marked_img, px, py, m['type'], m.get('note', ''))
                                
                                # If it's a cross, save the topic to our memory
                                if m['type'] == 'cross' and m.get('topic') in available_topics:
                                    found_mistakes.append(m['topic'])
                            
                            w_img = apply_watermark(marked_img)
                            pdf.add_page(); t_p = f"t_{i}.png"; w_img.save(t_p); pdf.image(t_p, x=0, y=0, w=210, h=297)
                            add_floating_footer(pdf); os.remove(t_p)
                        
                        # Save data to state for the Revision Hub to read
                        st.session_state.latest_mistakes = list(set(found_mistakes)) # remove duplicates
                        st.session_state.last_subject = s_n
                        
                        deduct_credit(st.session_state.target_email, cost); log_scan_history(st.session_state.target_email, b_n, s_n)
                        st.success("SCAN COMPLETE.")
                        st.download_button("GET EVALUATED PDF", data=bytes(pdf.output()), file_name=f"AXOM_{s_n}_Review.pdf")
                        
                        if st.session_state.latest_mistakes:
                            st.info("🚨 Weaknesses detected! Head to the REVISION HUB to see your priority study plan.")
                    except Exception as e: st.error(f"ERROR: {e}")

    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION HUB")
        st.write("Targeted knowledge mapping based on your Neural Scan results.")
        
        # Auto-select the subject from the last scan
        subject_idx = ["Physics", "Chemistry", "English"].index(st.session_state.last_subject) if st.session_state.last_subject in ["Physics", "Chemistry", "English"] else 0
        subject_filter = st.selectbox("Select Subject", ["Physics", "Chemistry", "English"], index=subject_idx)
        
        # THE MISTAKE TO MEDICINE ENGINE
        if subject_filter == st.session_state.last_subject and st.session_state.latest_mistakes:
            st.markdown("### 🚨 PRIORITY PRESCRIPTIONS (Based on Last Scan)")
            for topic in st.session_state.latest_mistakes:
                if topic in VIDEO_DATABASE[subject_filter]:
                    st.markdown(f'<div class="video-card priority-card">', unsafe_allow_html=True)
                    st.subheader(f"⚠️ High Priority: {topic}")
                    st.write("AXOM detected critical errors in this topic on your recent paper.")
                    st.video(VIDEO_DATABASE[subject_filter][topic])
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")
        
        st.markdown("### Standard Syllabus Library")
        for topic, url in VIDEO_DATABASE[subject_filter].items():
            # Don't show it twice if it's already in the priority section
            if subject_filter == st.session_state.last_subject and topic in st.session_state.latest_mistakes:
                continue
                
            st.markdown(f'<div class="video-card">', unsafe_allow_html=True)
            st.subheader(f"Module: {topic}")
            st.video(url)
            with st.expander("Challenge Module: Active Recall MCQ"):
                st.write(f"**Question:** What is the fundamental principle underpinning {topic.lower()}?")
                st.radio("Select Answer:", ["Option A", "Option B", "Option C"], key=f"q_{topic}")
                st.button("Submit", key=f"btn_{topic}")
            st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "SUBSCRIPTION":
        st.title("💎 PREMIUM UPGRADES")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="pricing-card"><h3>STARTER</h3><h2>37 SAR</h2><p>21 Credits</p></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="pricing-card highlight"><h3>CRUSHER</h3><h2>94 SAR</h2><p>60 Credits</p></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="pricing-card vip-gold"><h3>VIP</h3><h2>187 SAR</h2><p>150 Credits</p></div>', unsafe_allow_html=True)
        
        code = st.text_input("REDEEM CODE")
        if st.button("ACTIVATE"):
            if redeem_credits(st.session_state.target_email, code):
                st.success("CREDITS ADDED!"); time.sleep(1); st.rerun()
            else: st.error("INVALID CODE")

    elif menu == "SETTINGS": 
        st.title("⚙️ SETTINGS")
        st.write("Account management and system diagnostics.")
