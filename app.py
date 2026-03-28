import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import urllib.parse
import smtplib
import random
from email.message import EmailMessage
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from fpdf import FPDF
from datetime import datetime

# --- 1. HUD & INTERFACE STYLING ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); text-align: center; box-shadow: 0 0 30px rgba(0, 212, 255, 0.2); }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; font-weight: bold; border-radius: 5px; height: 45px; }
    
    /* REVISION HUB STYLING */
    .mistake-box { 
        background: rgba(255, 50, 50, 0.1); 
        border-left: 5px solid #ff3232; 
        padding: 20px; 
        border-radius: 5px; 
        margin-bottom: 25px;
    }
    .report-card { 
        background: rgba(0, 212, 255, 0.05); 
        border: 1px solid #00d4ff; 
        padding: 20px; 
        border-radius: 10px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try:
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except Exception:
    st.error("CRITICAL: API KEY MISSING IN SECRETS.")
    client = None

MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type):
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 50, 50, 255)
    sz = 35
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=10)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=10)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=10)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

# --- 3. SECURITY & SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "latest_eval" not in st.session_state: st.session_state.latest_eval = []

def send_otp(recip, code):
    try:
        msg = EmailMessage()
        msg.set_content(f"YOUR AXOM ACCESS KEY: {code}")
        msg['Subject'] = 'AXOM SECURITY PROTOCOL'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recip
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            s.send_message(msg)
        return True
    except: return False

# --- 4. LOGIN ENGINE ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        if not st.session_state.otp_sent:
            email = st.text_input("ENTER REGISTERED EMAIL")
            if st.button("GENERATE KEY"):
                code = str(random.randint(100000, 999999))
                if send_otp(email, code):
                    st.session_state.generated_otp = code
                    st.session_state.user_email = email
                    st.session_state.otp_sent = True
                    st.rerun()
        else:
            otp_in = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("AUTHENTICATE"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("INVALID KEY.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MAIN APPLICATION ---
else:
    with st.sidebar:
        st.title("AXOM V3.5")
        st.write(f"USER: {st.session_state.user_email}")
        menu = st.radio("NAVIGATION", ["NEURAL SCAN", "REVISION HUB", "SETTINGS"])
        if st.button("TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.rerun()

    # --- PANEL: NEURAL SCAN ---
    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL EVALUATION ENGINE")
        
        c1, c2 = st.columns(2)
        board = c1.text_input("EXAMINATION BOARD", "IGCSE")
        subj = c2.text_input("SUBJECT", "Physics")
        
        col_up1, col_up2 = st.columns(2)
        up_script = col_up1.file_uploader("UPLOAD SCRIPT (PDF)", type=['pdf'])
        up_scheme = col_up2.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])

        if up_script and st.button("EXECUTE FULL ANALYSIS"):
            with st.spinner("GEMINI 2.5 ANALYZING MULTI-PAGE CONTEXT..."):
                try:
                    script_pages = convert_from_bytes(up_script.read())
                    ms_context = "Use standard marking criteria."
                    if up_scheme:
                        ms_pages = convert_from_bytes(up_scheme.read())
                        ms_context = "STRICTLY follow the attached Mark Scheme images."
                    
                    p_txt = f"""
                    Identify as Senior Examiner for {board} {subj}. {ms_context}
                    Analyze the full script. Return ONLY JSON:
                    {{
                        "page_marks": [{{ "page": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "Name" }}] }}],
                        "summary": {{ "grade": "A*", "strengths": [], "weaknesses": [{{ "topic": "Name", "reason": "Why", "yt": "Search terms" }}] }}
                    }}
                    """

                    full_content = [p_txt] + script_pages
                    if up_scheme: full_content += ms_pages

                    response = client.models.generate_content(model=MODEL_ID, contents=full_content)
                    res = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    
                    # Store eval for Revision Hub
                    st.session_state.latest_eval = res.get("summary", {}).get("weaknesses", [])
                    st.session_state.current_subj = subj

                    # PDF Output Preparation
                    output_pdf = FPDF()
                    page_marks_data = res.get("page_marks", [])

                    for idx, img in enumerate(script_pages):
                        current_marks = next((p['marks'] for p in page_marks_data if p['page'] == idx), [])
                        marked_img = img.copy()
                        for m in current_marks:
                            px, py = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                            marked_img = draw_mark(marked_img, px, py, m['type'])
                        
                        st.image(marked_img, caption=f"Page {idx+1}", use_column_width=True)
                        
                        temp_path = f"temp_{idx}.png"
                        marked_img.save(temp_path); output_pdf.add_page(); output_pdf.image(temp_path, 0, 0, 210, 297); os.remove(temp_path)

                    st.markdown(f"### FINAL GRADE: {res['summary']['grade']}")
                    st.download_button("📩 DOWNLOAD MARKED SCRIPT", data=bytes(output_pdf.output()), file_name="AXOM_REVIEW.pdf")
                    st.success("SCAN COMPLETE. GO TO REVISION HUB.")

                except Exception as e: st.error(f"NEURAL ERROR: {e}")

    # --- PANEL: REVISION HUB ---
    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION HUB")
        
        if not st.session_state.latest_eval:
            st.info("Run a Neural Scan to identify weaknesses.")
        else:
            for item in st.session_state.latest_eval:
                topic = item['topic']
                search_query = item['yt']
                encoded_query = urllib.parse.quote(search_query)
                yt_link = f"https://www.youtube.com/results?search_query={encoded_query}"

                st.markdown(f"""
                <div class="mistake-box">
                    <h2 style="color: #ff3232; margin:0;">⚠️ TOPIC: {topic.upper()}</h2>
                    <p style="color: #ccc;">{item['reason']}</p>
                    <p><b>Link:</b> <a href="{yt_link}" target="_blank" style="color: #00d4ff;">Open in YouTube</a></p>
                </div>
                """, unsafe_allow_html=True)

                # EMBED VIDEO PREVIEW
                st.video(f"https://www.youtube.com/embed?listType=search&list={encoded_query}")
                st.markdown("---")
