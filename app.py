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

# --- 2. DATABASE & SYSTEM LOGIC ---
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

def log_scan_history(email, board, subject):
    df_hist = pd.read_csv(HISTORY_FILE)
    new_log = pd.DataFrame({"email": [email], "date": [datetime.now().strftime('%Y-%m-%d %H:%M')], "board": [board], "subject": [subject], "score": ["Scanned"]})
    pd.concat([df_hist, new_log], ignore_index=True).to_csv(HISTORY_FILE, index=False)

init_db()

# --- 3. KNOWLEDGE BASE ---
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

# --- 4. VISUAL ENGINE ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash"

def draw_sticky_note(img, x, y, mark_type, text=""):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    tick_color = (0, 230, 118, 255); cross_color = (255, 50, 50, 255); line_width = 7; mark_size = 30
    if mark_type == 'tick':
        draw.line([(x-mark_size, y), (x-mark_size//3, y+mark_size), (x+mark_size, y-mark_size)], fill=tick_color, width=line_width)
    else:
        draw.line([(x-mark_size, y-mark_size), (x+mark_size, y+mark_size)], fill=cross_color, width=line_width)
        draw.line([(x+mark_size, y-mark_size), (x-mark_size, y+mark_size)], fill=cross_color, width=line_width)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

# --- 5. STATE & SECURITY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "latest_mistakes" not in st.session_state: st.session_state.latest_mistakes = []
if "last_subject" not in st.session_state: st.session_state.last_subject = "Physics"

def send_otp(recip, code):
    try:
        msg = EmailMessage(); msg.set_content(f"AXOM ACCESS KEY: {code}"); msg['Subject'] = 'AXOM SECURITY'; msg['From'] = st.secrets["SMTP_EMAIL"]; msg['To'] = recip
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s: s.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"]); s.send_message(msg)
        return True
    except: return False

# --- 6. CORE INTERFACE ---
if not st.session_state.logged_in:
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
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
                if otp == st.session_state.generated_otp: st.session_state.logged_in = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    tier, creds = get_user_data(st.session_state.target_email)
    
    with st.sidebar:
        st.title("AXOM")
        st.write(f"**POWER:** {creds} Credits")
        menu = st.radio("PANEL", ["NEURAL SCAN", "REVISION HUB", "SUBSCRIPTION", "SETTINGS"])
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.rerun()

    # --- PANEL 1: NEURAL SCAN ---
    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL MARKER & ANALYTICS")
        c1, c2 = st.columns(2)
        b_n = c1.text_input("BOARD", "IGCSE")
        s_n = c2.selectbox("SUBJECT", ["Physics", "Chemistry", "English"])
        up_s = st.file_uploader("STUDENT SCRIPT", type=['pdf'])

        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("AI SCANNING PEN STROKES..."):
                try:
                    s_imgs = convert_from_bytes(up_s.read())
                    cost = max(1, (len(s_imgs) + 4) // 5)
                    available_topics = list(VIDEO_DATABASE.get(s_n, {}).keys())
                    
                    p_txt = f"""Return ONLY JSON: {{
                        "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "one from {available_topics}" }}],
                        "summary": {{ "grade_estimate": "A", "strengths": [], "weaknesses": [], "action_plan": "" }}
                    }} Mark {b_n} {s_n}."""

                    r = client.models.generate_content(model=MODEL_ID, contents=[p_txt, s_imgs[0]])
                    raw_json = json.loads(re.search(r'\{.*\}', r.text, re.DOTALL).group(0))
                    
                    marks = raw_json.get("marks", [])
                    report = raw_json.get("summary", {})

                    # Display Marked Image
                    marked_display = s_imgs[0].copy()
                    for m in marks:
                        px, py = int((m['x']/1000)*marked_display.width), int((m['y']/1000)*marked_display.height)
                        marked_display = draw_sticky_note(marked_display, px, py, m['type'])
                    st.image(marked_display, use_column_width=True)

                    # Interactive Sticky Notes
                    st.markdown("### 🔍 CLICK TO EXPAND FEEDBACK")
                    for idx, m in enumerate(marks):
                        icon = "✅" if m['type'] == 'tick' else "❌"
                        with st.expander(f"{icon} Mark #{idx+1} Feedback"):
                            st.info(f"**Topic:** {m.get('topic')}\n\n**Note:** {m['note']}")

                    # Executive Summary Report Area
                    st.markdown(f"""
                        <div style="background: rgba(0, 212, 255, 0.1); border: 2px solid #00d4ff; padding: 20px; border-radius: 10px;">
                            <h2 style="color: #00d4ff;">📊 PERFORMANCE REVIEW</h2>
                            <h1 style="color: #FFD700;">GRADE: {report.get('grade_estimate')}</h1>
                            <p><b>STRENGTHS:</b> {', '.join(report.get('strengths'))}</p>
                            <p><b>WEAKNESSES:</b> {', '.join(report.get('weaknesses'))}</p>
                            <p><b>ACTION:</b> {report.get('action_plan')}</p>
                        </div>
                    """, unsafe_allow_html=True)

                    st.session_state.latest_mistakes = report.get('weaknesses', [])
                    st.session_state.last_subject = s_n
                    deduct_credit(st.session_state.target_email, cost)
                except Exception as e: st.error(f"SCAN ERROR: {e}")

    # --- PANEL 2: REVISION HUB ---
    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION")
        subj = st.selectbox("Filter", ["Physics", "Chemistry", "English"], 
                            index=["Physics", "Chemistry", "English"].index(st.session_state.last_subject))
        
        if subj == st.session_state.last_subject and st.session_state.latest_mistakes:
            st.error("🚨 PRIORITY TOPICS DETECTED")
            for m in st.session_state.latest_mistakes:
                if m in VIDEO_DATABASE[subj]:
                    st.markdown(f'<div class="video-card priority-card"><h4>{m}</h4>', unsafe_allow_html=True)
                    st.video(VIDEO_DATABASE[subj][m])
                    st.markdown('</div>', unsafe_allow_html=True)

        for topic, url in VIDEO_DATABASE[subj].items():
            if topic not in st.session_state.latest_mistakes:
                st.markdown(f'<div class="video-card"><h4>{topic}</h4>', unsafe_allow_html=True)
                st.video(url)
                st.markdown('</div>', unsafe_allow_html=True)

    # --- PANEL 3: SUBSCRIPTION ---
    elif menu == "SUBSCRIPTION":
        st.title("💎 UPGRADES")
        st.write("Starter: 37 SAR | Pro: 94 SAR | VIP: 187 SAR")

    # --- PANEL 4: SETTINGS ---
    elif menu == "SETTINGS":
        st.title("⚙️ SETTINGS")
        st.write(f"Logged in as: {st.session_state.target_email}")
