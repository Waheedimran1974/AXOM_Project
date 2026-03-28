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
from fpdf import FPDF

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")
st.markdown("""<style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border-radius: 5px; font-weight: bold; }
    .report-box { background: rgba(0, 212, 255, 0.1); border: 2px solid #00d4ff; padding: 25px; border-radius: 15px; margin-top: 20px; }
    .page-header { border-bottom: 1px solid #00d4ff; margin-bottom: 20px; padding-bottom: 10px; }
</style>""", unsafe_allow_html=True)

# --- 2. CORE SYSTEMS ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None

# UPGRADED TO GEMINI 2.5 FLASH
MODEL_ID = "gemini-2.5-flash" 

VIDEO_DATABASE = {
    "Physics": {"Electricity & Circuits": "https://www.youtube.com/watch?v=mc979OhitAg", "Forces & Motion": "https://www.youtube.com/watch?v=aFO4PBolwFg"},
    "Chemistry": {"Moles & Stoichiometry": "https://www.youtube.com/watch?v=SjQG3rKSZUQ"},
    "English": {"Essay Structure": "https://www.youtube.com/watch?v=GgwZz910f1k"}
}

def draw_mark(img, x, y, mark_type):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 50, 50, 255)
    sz = 35
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=10)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=10)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=10)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

# --- 3. STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "latest_mistakes" not in st.session_state: st.session_state.latest_mistakes = []
if "last_subject" not in st.session_state: st.session_state.last_subject = "Physics"

# --- 4. INTERFACE ---
if not st.session_state.logged_in:
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div style="text-align:center; padding:50px; border:2px solid #00d4ff; border-radius:10px;">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        em = st.text_input("EMAIL")
        if st.button("UNLOCK SYSTEM"): st.session_state.logged_in = True; st.session_state.target_email = em; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with st.sidebar:
        st.title("AXOM V1.5")
        menu = st.radio("PANEL", ["NEURAL SCAN", "REVISION HUB", "SETTINGS"])
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.rerun()

    if menu == "NEURAL SCAN":
        st.title("🧠 GEMINI 2.5 FULL SCRIPT ANALYSIS")
        c1, c2 = st.columns(2)
        b_n = c1.text_input("BOARD", "IGCSE")
        s_n = c2.selectbox("SUBJECT", ["Physics", "Chemistry", "English"])
        up_s = st.file_uploader("UPLOAD FULL PDF SCRIPT", type=['pdf'])

        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("GEMINI 2.5 IS ANALYZING ENTIRE PDF CONTEXT..."):
                try:
                    pages = convert_from_bytes(up_s.read())
                    topics = list(VIDEO_DATABASE.get(s_n, {}).keys())
                    
                    # SYSTEM PROMPT: Unified Intelligence
                    p_txt = f"""
                    Identify as a Senior Examiner. You are reviewing a full PDF containing {len(pages)} pages.
                    Treat all pages as ONE continuous file for {b_n} {s_n}.
                    Output ONLY valid JSON:
                    {{
                        "page_marks": [
                            {{ "page_index": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "Detailed feedback", "topic": "{topics}" }}] }}
                        ],
                        "summary": {{ "grade": "A-E", "strengths": ["string"], "weaknesses": ["string"], "plan": "string" }}
                    }}
                    """

                    # Send the Full Document in one Context Window
                    response = client.models.generate_content(model=MODEL_ID, contents=[p_txt] + pages)
                    res_json = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    
                    # PDF RE-GENERATION ENGINE
                    output_pdf = FPDF()
                    all_marked_images = []

                    st.subheader("📝 INTERACTIVE REVIEW")
                    page_marks_list = res_json.get("page_marks", [])

                    for idx, img in enumerate(pages):
                        # Filter marks for this specific page
                        current_marks = next((p['marks'] for p in page_marks_list if p['page_index'] == idx), [])
                        
                        marked_img = img.copy()
                        for m in current_marks:
                            px, py = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                            marked_img = draw_mark(marked_img, px, py, m['type'])
                        
                        # Display on UI
                        st.markdown(f"<div class='page-header'>PAGE {idx+1}</div>", unsafe_allow_html=True)
                        st.image(marked_img, use_column_width=True)
                        
                        with st.expander(f"View Feedback for Page {idx+1}"):
                            for i, m in enumerate(current_marks):
                                color = "green" if m['type'] == 'tick' else "red"
                                st.markdown(f":{color}[**Mark {i+1}:**] {m['note']}")

                        # Save for PDF download
                        temp_path = f"temp_page_{idx}.png"
                        marked_img.save(temp_path)
                        output_pdf.add_page()
                        output_pdf.image(temp_path, 0, 0, 210, 297)
                        os.remove(temp_path)

                    # FINAL REPORT CARD
                    report = res_json.get("summary", {})
                    st.markdown(f"""<div class="report-box">
                        <h2 style="color: #00d4ff; margin-top:0;">📊 AXOM PERFORMANCE REPORT</h2>
                        <h1 style="color: #FFD700;">FINAL GRADE: {report.get('grade')}</h1>
                        <p><b>STRENGTHS:</b> {', '.join(report.get('strengths'))}</p>
                        <p><b>WEAKNESSES:</b> {', '.join(report.get('weaknesses'))}</p>
                        <p><b>ACTION PLAN:</b> {report.get('plan')}</p>
                    </div>""", unsafe_allow_html=True)

                    st.session_state.latest_mistakes = report.get('weaknesses', [])
                    st.session_state.last_subject = s_n
                    
                    st.download_button("📩 DOWNLOAD MARKED PDF", data=bytes(output_pdf.output()), file_name=f"AXOM_EVALUATION.pdf")
                    st.success("TOTAL EVALUATION COMPLETE.")
                    
                except Exception as e: st.error(f"NEURAL ERROR: {e}")

    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION HUB")
        # Same Hub logic for video mapping...
