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

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | TOTAL NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); text-align: center; box-shadow: 0 0 30px rgba(0, 212, 255, 0.2); }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; font-weight: bold; border-radius: 5px; height: 50px; text-transform: uppercase; letter-spacing: 2px; }
    .mistake-box { background: rgba(255, 50, 50, 0.1); border-left: 5px solid #ff3232; padding: 20px; border-radius: 5px; margin-bottom: 25px; box-shadow: 0 0 15px rgba(255, 50, 50, 0.2); }
    .page-header { border-bottom: 1px solid #00d4ff; margin: 30px 0 10px 0; padding-bottom: 5px; font-weight: bold; color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE SYSTEMS ---
try:
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except:
    st.error("CRITICAL: API KEY ERROR.")
    client = None

MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type):
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 50, 50, 255)
    sz = 40
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=12)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        # Resize logo to roughly 10% of page width
        base_width = int(img.width * 0.12)
        w_percent = (base_width / float(logo.size[0]))
        h_size = int((float(logo.size[1]) * float(w_percent)))
        logo = logo.resize((base_width, h_size), Image.LANCZOS)
        
        # Position: Bottom Right (with 50px padding)
        pos = (img.width - logo.width - 50, img.height - logo.height - 50)
        img.paste(logo, pos, logo)
    return img

# --- 3. SESSION & SECURITY ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "latest_eval" not in st.session_state: st.session_state.latest_eval = []

# --- 4. ACCESS CONTROL ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        if not st.session_state.otp_sent:
            email = st.text_input("RECIPIENT EMAIL")
            if st.button("REQUEST AUTH KEY"):
                # Simplified for your logic - proceed to login
                st.session_state.user_email = email
                st.session_state.logged_in = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with st.sidebar:
        st.title("AXOM V3.5 PRO")
        if os.path.exists("logo.png"): st.image("logo.png", use_column_width=True)
        st.write(f"**ACTIVE:** {st.session_state.user_email}")
        menu = st.radio("SYSTEM PANEL", ["NEURAL SCAN", "REVISION HUB", "SETTINGS"])
        if st.button("TERMINATE"):
            st.session_state.logged_in = False
            st.rerun()

    # --- PANEL: NEURAL SCAN ---
    if menu == "NEURAL SCAN":
        st.title("🧠 ADVANCED NEURAL SCANNER")
        
        c1, c2 = st.columns(2)
        board = c1.text_input("EXAM BOARD", placeholder="e.g. IGCSE / A-LEVEL")
        subj = c2.text_input("SUBJECT", placeholder="e.g. Physics / English")
        
        col_up1, col_up2 = st.columns(2)
        up_script = col_up1.file_uploader("STUDENT SCRIPT (PDF)", type=['pdf'])
        up_scheme = col_up2.file_uploader("MARK SCHEME (OPTIONAL)", type=['pdf'])

        if up_script and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("AI IS SCANNING PEN STROKES & APPLYING SYLLABUS..."):
                try:
                    script_pages = convert_from_bytes(up_script.read())
                    ms_context = "Use global marking standards."
                    if up_scheme:
                        ms_pages = convert_from_bytes(up_scheme.read())
                        ms_context = "STRICTLY follow the uploaded Mark Scheme instructions."
                    
                    p_txt = f"""
                    You are a Senior Lead Examiner for {board} {subj}. {ms_context}
                    Analyze the full student script. Output ONLY valid JSON:
                    {{
                        "page_marks": [{{ "page": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "topic" }}] }}],
                        "summary": {{ "grade": "A", "weaknesses": [{{ "topic": "Name", "reason": "Why", "yt": "Search terms" }}] }}
                    }}
                    """

                    full_content = [p_txt] + script_pages
                    if up_scheme: full_content += ms_pages

                    response = client.models.generate_content(model=MODEL_ID, contents=full_content)
                    res = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    
                    st.session_state.latest_eval = res.get("summary", {}).get("weaknesses", [])
                    st.session_state.current_subj = subj

                    # --- PRO PDF GENERATOR ---
                    output_pdf = FPDF()
                    page_marks_data = res.get("page_marks", [])

                    st.subheader("📝 MARKED SCRIPT PREVIEW")
                    for idx, img in enumerate(script_pages):
                        current_marks = next((p['marks'] for p in page_marks_data if p['page'] == idx), [])
                        
                        # 1. Draw Marks
                        marked_img = img.copy()
                        for m in current_marks:
                            px, py = int((m['x']/1000)*img.width), int((m['y']/1000)*img.height)
                            marked_img = draw_mark(marked_img, px, py, m['type'])
                        
                        # 2. APPLY AXOM LOGO (Bottom Right)
                        marked_img = apply_logo(marked_img, "logo.png")
                        
                        # 3. Display
                        st.markdown(f"<div class='page-header'>NEURAL SCAN: PAGE {idx+1}</div>", unsafe_allow_html=True)
                        st.image(marked_img, use_column_width=True)
                        
                        # 4. Save to PDF
                        temp_path = f"axom_pg_{idx}.png"
                        marked_img.save(temp_path)
                        output_pdf.add_page()
                        output_pdf.image(temp_path, 0, 0, 210, 297)
                        os.remove(temp_path)

                    st.markdown(f"## FINAL PERFORMANCE GRADE: {res['summary']['grade']}")
                    
                    # --- THE PRO DOWNLOADER ---
                    pdf_data = output_pdf.output(dest='S').encode('latin1')
                    st.download_button(
                        label="📩 DOWNLOAD OFFICIAL AXOM REVIEW",
                        data=pdf_data,
                        file_name=f"AXOM_{subj}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("EVALUATION COMPLETE. WEAKNESSES LOGGED TO HUB.")

                except Exception as e: st.error(f"NEURAL ERROR: {e}")

    # --- PANEL: REVISION HUB ---
    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION HUB")
        
        if not st.session_state.latest_eval:
            st.info("Complete a Neural Scan to populate your revision path.")
        else:
            for item in st.session_state.latest_eval:
                topic = item['topic']
                search_query = item['yt']
                encoded_query = urllib.parse.quote(f"{st.session_state.current_subj} {search_query}")
                yt_link = f"https://www.youtube.com/results?search_query={encoded_query}"

                st.markdown(f"""
                <div class="mistake-box">
                    <h2 style="color: #ff3232; margin:0;">⚠️ TARGETED REVISION: {topic.upper()}</h2>
                    <p style="color: #ccc; margin-top:5px;">{item['reason']}</p>
                    <p><b>AXOM Direct Link:</b> <a href="{yt_link}" target="_blank" style="color: #00d4ff;">OPEN LESSON</a></p>
                </div>
                """, unsafe_allow_html=True)

                # EMBED VIDEO PREVIEW
                st.video(f"https://www.youtube.com/embed?listType=search&list={encoded_query}")
                st.markdown("---")
