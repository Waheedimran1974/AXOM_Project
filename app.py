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

# --- 1. HUD & ENHANCED UI STYLING ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    /* Global Styles */
    .stApp { 
        background: radial-gradient(circle at top, #001e3c 0%, #00050d 100%); 
        color: #00d4ff; 
        font-family: 'Inter', 'Segoe UI', monospace; 
    }
    
    /* Neon Frames */
    .future-frame { 
        border: 1px solid #00d4ff; 
        border-radius: 15px; 
        padding: 40px; 
        background: rgba(0, 20, 46, 0.8); 
        text-align: center; 
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.1); 
    }
    
    /* Interactive Sticky Notes */
    .sticky-note {
        background: #fff9c4; 
        color: #263238; 
        padding: 15px; 
        border-radius: 4px;
        border-left: 8px solid #fbc02d; 
        margin-bottom: 12px;
        font-size: 0.9rem;
        box-shadow: 4px 4px 12px rgba(0,0,0,0.4);
    }
    
    /* Revision Red Box - Improved Contrast */
    .red-alert-box {
        background: rgba(255, 23, 68, 0.08); 
        border: 1px solid #ff1744;
        padding: 25px; 
        border-radius: 12px; 
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(255, 23, 68, 0.15);
    }
    
    .stButton>button { 
        width: 100%; 
        background: linear-gradient(90deg, #00d4ff, #0088ff) !important; 
        color: #fff !important; 
        font-weight: 700; 
        height: 50px; 
        border: none;
        border-radius: 8px;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0, 212, 255, 0.4); }
    
    .page-header { 
        border-left: 4px solid #00d4ff; 
        margin: 40px 0 20px 0; 
        padding-left: 15px; 
        font-weight: 800; 
        color: #00d4ff; 
        font-size: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try:
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except:
    st.error("SYSTEM ERROR: GENAI_API_KEY NOT FOUND IN SECRETS.")
    client = None

MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 23, 68, 255)
    sz = 45
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=15)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=15)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=15)
    
    # ID Badge
    draw.ellipse([x+sz, y-sz, x+sz+60, y-sz+60], fill=(0, 212, 255, 230))
    draw.text((x+sz+18, y-sz+12), str(index), fill=(0,0,0,255), font_size=30)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.jpg.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12)
        logo = logo.resize((base_width, int(logo.size[1] * (base_width/logo.size[0]))), Image.LANCZOS)
        img.paste(logo, (img.width-logo.width-50, img.height-logo.height-50), logo)
    return img

# --- 3. SESSION INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "eval_data" not in st.session_state: st.session_state.eval_data = None
if "pages" not in st.session_state: st.session_state.pages = []

# --- 4. ACCESS SYSTEM (DIRECT BYPASS) ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | NEURAL PORTAL")
        u_email = st.text_input("AUTHORIZED EMAIL", placeholder="teacher@axom.ai")
        if st.button("INITIALIZE SYSTEM"):
            if "@" in u_email:
                st.session_state.user_email = u_email
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("PLEASE ENTER A VALID EMAIL")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. AXOM MAIN ENGINE ---
else:
    with st.sidebar:
        st.title("AXOM V4.1 PRO")
        if os.path.exists("logo.jpg.png"): st.image("logo.jpg.png")
        st.write(f"📡 **SIGNAL:** {st.session_state.user_email}")
        st.markdown("---")
        menu = st.radio("SELECT MODE", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("TERMINATE"):
            st.session_state.logged_in = False
            st.rerun()

    # --- MODE: NEURAL SCAN ---
    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL SCANNER")
        c1, c2 = st.columns(2)
        board = c1.text_input("EXAM BOARD", "IGCSE")
        subj = c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT (PDF)", type=['pdf'])
        up_m = st.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])

        if up_s and st.button("RUN NEURAL EVALUATION"):
            with st.spinner("SCANNING HANDWRITING & GENERATING NEURAL PATHS..."):
                try:
                    raw_pages = convert_from_bytes(up_s.read())
                    prompt = f"Senior Examiner for {board} {subj}. Return JSON ONLY: {{'page_marks': [{{'page': 0, 'marks': [{{'type': 'tick'|'cross', 'x': 0-1000, 'y': 0-1000, 'note': '...', 'topic': '...' }}] }}], 'weaknesses': [{{'topic': '...', 'reason': '...', 'yt': '...' }}] }}"
                    
                    response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + raw_pages)
                    cleaned_json = re.search(r'\{.*\}', response.text, re.DOTALL).group(0)
                    
                    st.session_state.eval_data = json.loads(cleaned_json)
                    st.session_state.pages = raw_pages
                    st.session_state.current_subj = subj
                except Exception as e:
                    st.error(f"NEURAL ERROR: {e}")

        if st.session_state.eval_data:
            output_pdf = FPDF()
            for idx, img in enumerate(st.session_state.pages):
                st.markdown(f"<div class='page-header'>ANALYSIS: PAGE {idx+1}</div>", unsafe_allow_html=True)
                col_img, col_sticky = st.columns([3, 1])
                
                # Fetch marks for current page
                marks = next((p['marks'] for p in st.session_state.eval_data['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                
                with col_sticky:
                    st.subheader("📌 Sticky Notes")
                    for i, m in enumerate(marks):
                        with st.expander(f"NOTE #{i+1}: {m['topic']}", expanded=True):
                            st.markdown(f'<div class="sticky-note">{m["note"]}</div>', unsafe_allow_html=True)
                        # Draw mark on image
                        marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                
                marked_img = apply_logo(marked_img, "logo.jpg.png")
                col_img.image(marked_img, use_column_width=True)
                
                # Save PDF Page
                t_path = f"t_{idx}.png"
                marked_img.save(t_path)
                output_pdf.add_page()
                output_pdf.image(t_path, 0, 0, 210, 297)
                os.remove(t_path)
            
            # PDF Download Logic
            pdf_data = output_pdf.output(dest='S')
            final_bytes = pdf_data.encode('latin1') if isinstance(pdf_data, str) else bytes(pdf_data)
            st.download_button("📩 DOWNLOAD AXOM REVIEW", data=final_bytes, file_name=f"AXOM_{subj}_Review.pdf")

    # --- MODE: REVISION HUB ---
    elif menu == "REVISION HUB":
        st.title("🚨 REVISION HUB")
        if not st.session_state.eval_data:
            st.info("NO SCAN DATA FOUND. PLEASE EXECUTE A NEURAL SCAN TO POPULATE THIS HUB.")
        else:
            for item in st.session_state.eval_data['weaknesses']:
                search_term = urllib.parse.quote(f"{st.session_state.current_subj} {item['yt']}")
                
                # REVISION RED BOX HUB
                st.markdown(f"""
                <div class="red-alert-box">
                    <h2 style="color: #ff1744; margin:0; font-size: 1.2rem;">⚠️ GAP IDENTIFIED: {item['topic'].upper()}</h2>
                    <p style="color: #eee; margin: 10px 0;">{item['reason']}</p>
                    <a href="https://www.youtube.com/results?search_query={search_term}" target="_blank" style="color:#00d4ff; font-weight:bold; text-decoration: none;">🔍 SEARCH EXTERNAL RESOURCES</a>
                </div>
                """, unsafe_allow_html=True)
                
                # Video Integration
                st.video(f"https://www.youtube.com/embed?listType=search&list={search_term}")
                st.markdown("---")
