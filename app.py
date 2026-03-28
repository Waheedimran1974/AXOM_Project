import streamlit as st
from google import genai
import os
import json
import re
import urllib.parse
import io
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from fpdf import FPDF
from datetime import datetime

# --- 1. HUD & NEURAL INTERFACE STYLE ---
st.set_page_config(page_title="AXOM | NEURAL BRIDGE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    
    /* NEURAL STICKY NOTE */
    .sticky-note {
        background-color: #ffffa5; color: #111; padding: 15px; border-radius: 2px;
        border-left: 8px solid #ffd700; margin-bottom: 12px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 3px 3px 10px rgba(0,0,0,0.5); transform: rotate(-0.5deg);
    }
    
    /* REVISION RED BOX */
    .red-alert-box {
        background: rgba(255, 50, 50, 0.1); border: 2px solid #ff3232;
        padding: 20px; border-radius: 10px; margin-bottom: 25px;
        box-shadow: 0 0 20px rgba(255, 50, 50, 0.2);
    }
    
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 50, 50, 255)
    sz = 40
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=12)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
    # Numerical ID Tag
    draw.ellipse([x+sz, y-sz, x+sz+50, y-sz+50], fill=(0, 212, 255, 220))
    draw.text((x+sz+15, y-sz+10), str(index), fill=(0,0,0,255))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12)
        logo = logo.resize((base_width, int(logo.size[1] * (base_width/logo.size[0]))), Image.LANCZOS)
        img.paste(logo, (img.width-logo.width-50, img.height-logo.height-50), logo)
    return img

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = "Guest"
if "eval_data" not in st.session_state: st.session_state.eval_data = None

# --- 4. LOGIN ENGINE ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align:center; padding:50px; border:2px solid #00d4ff; border-radius:10px;">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        e_in = st.text_input("EMAIL")
        if st.button("AUTHENTICATE"):
            if "@" in e_in: st.session_state.user_email = e_in; st.session_state.logged_in = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with st.sidebar:
        st.title("AXOM V3.8 PRO")
        if os.path.exists("logo.png"): st.image("logo.png")
        st.write(f"**ACTIVE:** {st.session_state.user_email}")
        menu = st.radio("INTERFACE", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.rerun()

    # --- PANEL: NEURAL SCAN ---
    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL SCANNER")
        c1, c2 = st.columns(2)
        board = c1.text_input("BOARD", "IGCSE")
        subj = c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT", type=['pdf'])
        up_m = st.file_uploader("MARK SCHEME (OPT)", type=['pdf'])

        if up_s and st.button("START EVALUATION"):
            with st.spinner("AI CONNECTING MARKS TO REVISION PATHS..."):
                try:
                    script_pages = convert_from_bytes(up_s.read())
                    p_txt = f"""
                    Senior Examiner for {board} {subj}.
                    Return ONLY JSON:
                    {{
                        "page_marks": [{{ "page": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "Specific Topic" }}] }}],
                        "weaknesses": [{{ "topic": "Topic", "reason": "Why", "yt": "YouTube search" }}]
                    }}
                    """
                    response = client.models.generate_content(model=MODEL_ID, contents=[p_txt] + script_pages)
                    st.session_state.eval_data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    st.session_state.pages = script_pages
                    st.session_state.current_subj = subj
                except Exception as e: st.error(f"SCAN ERROR: {e}")

        if st.session_state.eval_data:
            output_pdf = FPDF()
            for idx, img in enumerate(st.session_state.pages):
                st.markdown(f"<div class='page-header'>NEURAL FEEDBACK: PAGE {idx+1}</div>", unsafe_allow_html=True)
                col_img, col_sticky = st.columns([3, 1])
                
                marks = next((p['marks'] for p in st.session_state.eval_data['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                
                with col_sticky:
                    st.subheader("📌 Sticky Notes")
                    for i, m in enumerate(marks):
                        with st.expander(f"NOTE #{i+1}: {m['topic']}", expanded=False):
                            st.markdown(f'<div class="sticky-note">{m["note"]}</div>', unsafe_allow_html=True)
                        marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                
                marked_img = apply_logo(marked_img)
                col_img.image(marked_img, use_column_width=True)
                
                # PDF Generation
                t_p = f"t_{idx}.png"; marked_img.save(t_p); output_pdf.add_page(); output_pdf.image(t_p,0,0,210,297); os.remove(t_p)

            pdf_out = output_pdf.output(dest='S')
            pdf_bytes = pdf_out.encode('latin1') if isinstance(pdf_out, str) else bytes(pdf_out)
            st.download_button("📩 DOWNLOAD AXOM REVIEW", data=pdf_bytes, file_name="AXOM_REVIEW.pdf")

    # --- PANEL: REVISION HUB (THE RED BOXES) ---
    elif menu == "REVISION HUB":
        st.title("🚨 THE REVISION HUB")
        if not st.session_state.eval_data:
            st.info("No weaknesses logged. Run a Neural Scan first.")
        else:
            for item in st.session_state.eval_data['weaknesses']:
                q = urllib.parse.quote(f"{st.session_state.current_subj} {item['yt']}")
                
                # THE RED ALERT BOX
                st.markdown(f"""
                <div class="red-alert-box">
                    <h2 style="color: #ff3232; margin:0;">⚠️ WEAKNESS DETECTED: {item['topic'].upper()}</h2>
                    <p style="color: #ccc;">{item['reason']}</p>
                    <a href="https://www.youtube.com/results?search_query={q}" target="_blank" style="color:#00d4ff;">OPEN DIRECT LESSON</a>
                </div>
                """, unsafe_allow_html=True)
                
                # THE VIDEO UI
                st.video(f"https://www.youtube.com/embed?listType=search&list={q}")
                st.markdown("---")
