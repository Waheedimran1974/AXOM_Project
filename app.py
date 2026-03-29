import streamlit as st
from google import genai
import os
import json
import re
import urllib.parse
import io
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes
from fpdf import FPDF
from datetime import datetime

# --- 1. HUD & NEURAL INTERFACE STYLE ---
st.set_page_config(page_title="AXOM | EXAMINER PRO", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #001e3c 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    
    /* GREEN STICKY (CORRECT) */
    .sticky-green {
        background: #c8e6c9; color: #1b5e20; padding: 15px; border-radius: 4px;
        border-left: 10px solid #4caf50; margin-bottom: 15px;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.3); font-family: 'Comic Sans MS', cursive;
    }
    
    /* RED STICKY (INCORRECT) */
    .sticky-red {
        background: #ffcdd2; color: #b71c1c; padding: 15px; border-radius: 4px;
        border-left: 10px solid #f44336; margin-bottom: 15px;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.3); font-family: 'Comic Sans MS', cursive;
    }
    
    .red-alert-box { background: rgba(255, 23, 68, 0.1); border: 1px solid #ff1744; padding: 25px; border-radius: 12px; margin-bottom: 20px; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; font-weight: bold; border-radius: 8px; height: 45px; }
    .yt-button { display: block; width: 100%; text-align: center; background: #ff0000; color: white !important; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    # Examiner Colors: Green for Tick, Red for Cross
    color = (0, 200, 83, 255) if mark_type == 'tick' else (244, 67, 54, 255)
    sz = 45
    
    # Draw Handwritten Marks
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=14)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=14)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=14)
    
    # Neural ID Bubble (Examiner Ink Style)
    draw.ellipse([x+sz, y-sz, x+sz+75, y-sz+75], fill=color)
    # Using default font but simulating 'Handwritten' sizing
    draw.text((x+sz+25, y-sz+12), str(index), fill=(255,255,255,255))
    
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.jpg.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12)
        logo = logo.resize((base_width, int(logo.size[1] * (base_width/logo.size[0]))), Image.LANCZOS)
        img.paste(logo, (img.width-logo.width-50, img.height-logo.height-50), logo)
    return img

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "eval_data" not in st.session_state: st.session_state.eval_data = None
if "pages" not in st.session_state: st.session_state.pages = []

# --- 4. ACCESS SYSTEM ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="border:1px solid #00d4ff; padding:40px; border-radius:15px; background:rgba(0,20,46,0.8); text-align:center;">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        u_email = st.text_input("EMAIL")
        if st.button("UNLOCK"):
            if "@" in u_email: st.session_state.user_email, st.session_state.logged_in = u_email, True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with st.sidebar:
        st.title("AXOM V4.4 PRO")
        st.write(f"📡 **SIGNAL:** {st.session_state.user_email}")
        st.markdown("---")
        menu = st.radio("SELECT", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("TERMINATE"): st.session_state.logged_in = False; st.rerun()

    # --- SCANNER ---
    if menu == "NEURAL SCAN":
        st.title("🧠 EXAMINER SCAN")
        c1, c2 = st.columns(2)
        board, subj = c1.text_input("BOARD", "IGCSE"), c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT", type=['pdf'])

        if up_s and st.button("START MARKING"):
            with st.spinner("AI ANALYZING HANDWRITING..."):
                try:
                    raw_pages = convert_from_bytes(up_s.read())
                    prompt = f"Senior Examiner for {board} {subj}. Return ONLY JSON: {{'page_marks': [{{'page': 0, 'marks': [{{'type': 'tick'|'cross', 'x': 0-1000, 'y': 0-1000, 'note': '...', 'topic': '...' }}] }}], 'weaknesses': [{{'topic': '...', 'reason': '...', 'yt': '...' }}] }}"
                    response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + raw_pages)
                    st.session_state.eval_data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    st.session_state.pages, st.session_state.current_subj = raw_pages, subj
                except: st.error("NEURAL SCAN ERROR")

        if st.session_state.eval_data:
            pdf = FPDF()
            for idx, img in enumerate(st.session_state.pages):
                st.markdown(f"### PAGE {idx+1}")
                col_img, col_stickers = st.columns([3, 1])
                marks = next((p['marks'] for p in st.session_state.eval_data['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                
                with col_stickers:
                    st.subheader("📌 Examiner Notes")
                    for i, m in enumerate(marks):
                        style = "sticky-green" if m['type'] == 'tick' else "sticky-red"
                        with st.expander(f"NOTE #{i+1}: {m['topic']}", expanded=True):
                            st.markdown(f'<div class="{style}">{m["note"]}</div>', unsafe_allow_html=True)
                        marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                
                marked_img = apply_logo(marked_img)
                col_img.image(marked_img, use_column_width=True)
                
                t_p = f"t_{idx}.png"; marked_img.save(t_p); pdf.add_page(); pdf.image(t_p,0,0,210,297); os.remove(t_p)
            
            p_out = pdf.output(dest='S')
            st.download_button("📩 DOWNLOAD MARKED PDF", data=p_out.encode('latin1') if isinstance(p_out, str) else bytes(p_out), file_name="AXOM_FEEDBACK.pdf")

    # --- REVISION ---
    elif menu == "REVISION HUB":
        st.title("🚨 REVISION HUB")
        if st.session_state.eval_data:
            for item in st.session_state.eval_data['weaknesses']:
                q = urllib.parse.quote(f"{st.session_state.current_subj} {item['yt']}")
                st.markdown(f"""
                <div class="red-alert-box">
                    <h2 style="color:#ff1744;">⚠️ {item['topic'].upper()}</h2>
                    <p>{item['reason']}</p>
                    <a href="https://www.youtube.com/results?search_query={q}" target="_blank" class="yt-button">▶ OPEN LESSON</a>
                </div>
                """, unsafe_allow_html=True)
