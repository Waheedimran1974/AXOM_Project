import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import smtplib
import random
import time
from email.message import EmailMessage
from PIL import Image, ImageDraw
from datetime import datetime
from pdf2image import convert_from_bytes

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | TOTAL INTERFACE", layout="wide")
st.markdown("""<style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); text-align: center; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border: none !important; border-radius: 5px; height: 45px; font-weight: bold; }
    .video-card { border: 1px solid rgba(0, 212, 255, 0.3); background: rgba(0, 20, 46, 0.5); padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    .report-box { background: rgba(0, 212, 255, 0.1); border: 2px solid #00d4ff; padding: 25px; border-radius: 15px; margin-top: 20px; }
</style>""", unsafe_allow_html=True)

# --- 2. SYSTEM LOGIC ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.0-flash" # Use 2.0 Flash for massive context windows (entire PDFs)

VIDEO_DATABASE = {
    "Physics": {"Electricity & Circuits": "https://www.youtube.com/watch?v=mc979OhitAg", "Forces & Motion": "https://www.youtube.com/watch?v=aFO4PBolwFg"},
    "Chemistry": {"Moles & Stoichiometry": "https://www.youtube.com/watch?v=SjQG3rKSZUQ"},
    "English": {"Essay Structure": "https://www.youtube.com/watch?v=GgwZz910f1k"}
}

def draw_mark(img, x, y, mark_type):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 50, 50, 255)
    sz = 30
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=8)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=8)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=8)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

# --- 3. STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "latest_mistakes" not in st.session_state: st.session_state.latest_mistakes = []
if "last_subject" not in st.session_state: st.session_state.last_subject = "Physics"

# --- 4. INTERFACE ---
if not st.session_state.logged_in:
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        em = st.text_input("EMAIL")
        if st.button("UNLOCK HUB"): st.session_state.logged_in = True; st.session_state.target_email = em; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with st.sidebar:
        st.title("AXOM")
        menu = st.radio("PANEL", ["NEURAL SCAN", "REVISION HUB", "SETTINGS"])
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.rerun()

    if menu == "NEURAL SCAN":
        st.title("🧠 MULTI-PAGE NEURAL EVALUATION")
        c1, c2 = st.columns(2)
        b_n = c1.text_input("BOARD", "IGCSE")
        s_n = c2.selectbox("SUBJECT", ["Physics", "Chemistry", "English"])
        up_s = st.file_uploader("UPLOAD FULL STUDENT SCRIPT (PDF)", type=['pdf'])

        if up_s and st.button("EXECUTE FULL SCAN"):
            with st.spinner("AI ANALYZING ENTIRE DOCUMENT..."):
                try:
                    # 1. Convert ALL pages to images
                    pages = convert_from_bytes(up_s.read())
                    topics = list(VIDEO_DATABASE.get(s_n, {}).keys())
                    
                    # 2. Construct the Multi-Image Prompt
                    # We tell AI to index marks by "page_index"
                    p_txt = f"""
                    You are a Senior Examiner. I have uploaded {len(pages)} pages of a single {s_n} script.
                    Analyze ALL pages together and return ONE JSON object:
                    {{
                        "page_marks": [
                            {{ "page": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "one from {topics}" }}] }}
                        ],
                        "summary": {{ "grade": "A*", "strengths": [], "weaknesses": [], "action_plan": "" }}
                    }}
                    """

                    # 3. Send ALL images in one call
                    r = client.models.generate_content(model=MODEL_ID, contents=[p_txt] + pages)
                    res = json.loads(re.search(r'\{.*\}', r.text, re.DOTALL).group(0))
                    
                    # 4. Process Every Page
                    st.subheader("📝 MARKED SCRIPT REVIEW")
                    page_data = res.get("page_marks", [])
                    
                    for idx, pg_img in enumerate(pages):
                        # Find marks belonging to this specific page index
                        current_marks = next((p['marks'] for p in page_data if p['page'] == idx), [])
                        
                        marked_pg = pg_img.copy()
                        for m in current_marks:
                            px, py = int((m['x']/1000)*pg_img.width), int((m['y']/1000)*pg_img.height)
                            marked_pg = draw_mark(marked_pg, px, py, m['type'])
                        
                        st.image(marked_pg, caption=f"Page {idx+1}", use_column_width=True)
                        
                        # Show expandable notes for this page
                        with st.expander(f"View Feedback for Page {idx+1}"):
                            for i, m in enumerate(current_marks):
                                st.write(f"**Mark {i+1}:** {m['note']} ({m.get('topic')})")

                    # 5. Global Summary (Review Area)
                    report = res.get("summary", {})
                    st.markdown(f"""<div class="report-box">
                        <h2 style="color: #00d4ff;">📊 FINAL PERFORMANCE REVIEW</h2>
                        <h1 style="color: #FFD700;">ESTIMATED GRADE: {report.get('grade')}</h1>
                        <p><b>STRENGTHS:</b> {', '.join(report.get('strengths'))}</p>
                        <p><b>CRITICAL WEAKNESSES:</b> {', '.join(report.get('weaknesses'))}</p>
                        <p><b>EXAMINER ACTION PLAN:</b> {report.get('action_plan')}</p>
                    </div>""", unsafe_allow_html=True)

                    st.session_state.latest_mistakes = report.get('weaknesses', [])
                    st.session_state.last_subject = s_n
                    st.success("TOTAL EVALUATION COMPLETE.")
                    
                except Exception as e: st.error(f"SYSTEM OVERLOAD: {e}")

    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION")
        # Same Hub logic as before...
