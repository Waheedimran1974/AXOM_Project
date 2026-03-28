import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import smtplib
import urllib.parse # For safe URL generation
import random
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. STYLE ENGINE ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")
st.markdown("""<style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .report-box { background: rgba(0, 212, 255, 0.1); border: 2px solid #00d4ff; padding: 25px; border-radius: 15px; margin-top: 20px; }
    /* THE RED MISTAKE BOX */
    .mistake-box { 
        background: rgba(255, 50, 50, 0.15); 
        border: 2px solid #ff3232; 
        padding: 20px; 
        border-radius: 10px; 
        margin-bottom: 20px;
        box-shadow: 0 0 15px rgba(255, 50, 50, 0.3);
    }
    .yt-button {
        display: inline-block;
        padding: 10px 20px;
        background-color: #ff0000;
        color: white !important;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 10px;
    }
</style>""", unsafe_allow_html=True)

# --- 2. CORE SYSTEMS ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash" 

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
if "last_board" not in st.session_state: st.session_state.last_board = ""
if "last_subject" not in st.session_state: st.session_state.last_subject = ""

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
        st.title("AXOM V2.5")
        menu = st.radio("PANEL", ["NEURAL SCAN", "REVISION HUB", "SETTINGS"])
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.rerun()

    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL EVALUATION")
        c1, c2 = st.columns(2)
        user_board = c1.text_input("BOARD", placeholder="e.g. IGCSE", value=st.session_state.last_board)
        user_subject = c2.text_input("SUBJECT", placeholder="e.g. Physics", value=st.session_state.last_subject)
        
        col_up1, col_up2 = st.columns(2)
        up_script = col_up1.file_uploader("UPLOAD SCRIPT (PDF)", type=['pdf'])
        up_scheme = col_up2.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])

        if up_script and st.button("EXECUTE SCAN"):
            with st.spinner("AI ANALYZING ERRORS..."):
                try:
                    script_pages = convert_from_bytes(up_script.read())
                    ms_context = "Use global standard criteria."
                    if up_scheme:
                        ms_pages = convert_from_bytes(up_scheme.read())
                        ms_context = "Strictly follow the attached Mark Scheme images."

                    p_txt = f"""
                    Expert Examiner for {user_board} {user_subject}. {ms_context}
                    Output ONLY valid JSON:
                    {{
                        "page_marks": [{{ "page_index": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "Specific Topic Name" }}] }}],
                        "summary": {{ "grade": "A", "weaknesses": ["Specific Topic A", "Specific Topic B"] }}
                    }}
                    """

                    full_content = [p_txt] + script_pages
                    if up_scheme: full_content += ms_pages

                    response = client.models.generate_content(model=MODEL_ID, contents=full_content)
                    res_json = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    
                    # Store data for Revision Hub
                    st.session_state.latest_mistakes = res_json.get("summary", {}).get("weaknesses", [])
                    st.session_state.last_board = user_board
                    st.session_state.last_subject = user_subject

                    # Visual feedback (truncated for space, keep your page drawing logic here)
                    st.success(f"Analysis Complete! {len(st.session_state.latest_mistakes)} weaknesses identified.")
                    st.info("Go to the REVISION HUB to see your priority lessons.")
                    
                except Exception as e: st.error(f"NEURAL ERROR: {e}")

    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION HUB")
        
        if not st.session_state.latest_mistakes:
            st.write("No weaknesses detected yet. Complete a Neural Scan first.")
        else:
            st.markdown(f"### 🚨 PRIORITY REVISION: {st.session_state.last_subject.upper()}")
            st.write("AXOM has generated these custom study blocks based on your mistakes.")

            for mistake in st.session_state.latest_mistakes:
                # 1. Clean the mistake name for a URL
                query = f"{st.session_state.last_board} {st.session_state.last_subject} {mistake} revision".replace(" ", "+")
                yt_url = f"https://www.youtube.com/results?search_query={query}"

                # 2. Create the Red Box Interface
                st.markdown(f"""
                    <div class="mistake-box">
                        <h3 style="color: #ff3232; margin-top:0;">⚠️ TOPIC: {mistake.upper()}</h3>
                        <p style="color: #ffffff;">Our Neural Scan detected a lack of understanding in this specific area of the {st.session_state.last_subject} syllabus.</p>
                        <a href="{yt_url}" target="_blank" class="yt-button">📺 WATCH REVISION VIDEO</a>
                    </div>
                """, unsafe_allow_html=True)

    elif menu == "SETTINGS":
        st.title("⚙️ SETTINGS")
        st.write(f"Logged in: {st.session_state.get('target_email', 'User')}")
