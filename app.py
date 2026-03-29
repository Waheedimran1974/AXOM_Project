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

# --- 1. HUD & HIGH-TECH STYLING ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { 
        background: radial-gradient(circle at top, #001e3c 0%, #00050d 100%); 
        color: #00d4ff; 
        font-family: 'Inter', sans-serif; 
    }
    .future-frame { 
        border: 1px solid #00d4ff; border-radius: 15px; padding: 40px; 
        background: rgba(0, 20, 46, 0.8); text-align: center; 
    }
    
    /* STICKY NOTE STYLING */
    .sticky-note {
        background: #fff9c4; color: #1a1a1a; padding: 15px; border-radius: 4px;
        border-left: 10px solid #fbc02d; margin-bottom: 15px;
        box-shadow: 4px 4px 15px rgba(0,0,0,0.5); font-size: 0.95rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .red-alert-box {
        background: rgba(255, 23, 68, 0.1); border: 1px solid #ff1744;
        padding: 25px; border-radius: 12px; margin-bottom: 20px;
    }
    
    .stButton>button { 
        width: 100%; background: linear-gradient(90deg, #00d4ff, #0088ff) !important; 
        color: #fff !important; font-weight: 700; border: none; border-radius: 8px;
        height: 45px; transition: 0.3s ease;
    }
    
    .yt-button {
        display: block; width: 100%; text-align: center; background: #ff0000;
        color: white !important; padding: 12px; border-radius: 8px;
        text-decoration: none; font-weight: bold; margin-top: 10px;
    }
    
    .page-header { 
        border-bottom: 2px solid #00d4ff; margin: 40px 0 15px 0; 
        padding-bottom: 5px; color: #00d4ff; font-weight: 800; font-size: 1.4rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try:
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except:
    client = None

MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 23, 68, 255)
    sz = 45
    
    # Draw logic for Tick or Cross
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=15)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=15)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=15)
    
    # Draw numerical ID bubble next to mark
    draw.ellipse([x+sz, y-sz, x+sz+70, y-sz+70], fill=(0, 212, 255, 240))
    draw.text((x+sz+22, y-sz+15), str(index), fill=(0,0,0,255), font_size=35)
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
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | NEURAL PORTAL")
        u_email = st.text_input("AUTHORIZED EMAIL", placeholder="name@domain.com")
        if st.button("INITIALIZE SYSTEM"):
            if "@" in u_email:
                st.session_state.user_email, st.session_state.logged_in = u_email, True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with st.sidebar:
        st.title("AXOM V4.3 PRO")
        # Sidebar Logo Removed per Request
        st.write(f"📡 **USER:** {st.session_state.user_email}")
        st.markdown("---")
        menu = st.radio("INTERFACE", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("TERMINATE"):
            st.session_state.logged_in = False
            st.rerun()

    # --- MODE: NEURAL SCAN ---
    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL SCANNER")
        c1, c2 = st.columns(2)
        board, subj = c1.text_input("BOARD", "IGCSE"), c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT (PDF)", type=['pdf'])

        if up_s and st.button("EXECUTE ANALYSIS"):
            with st.spinner("AI SCANNING HANDWRITING & MAPPING COORDINATES..."):
                try:
                    raw_pages = convert_from_bytes(up_s.read())
                    prompt = f"Senior Examiner for {board} {subj}. Return ONLY JSON: {{'page_marks': [{{'page': 0, 'marks': [{{'type': 'tick'|'cross', 'x': 0-1000, 'y': 0-1000, 'note': '...', 'topic': '...' }}] }}], 'weaknesses': [{{'topic': '...', 'reason': '...', 'yt': '...' }}] }}"
                    response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + raw_pages)
                    st.session_state.eval_data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    st.session_state.pages, st.session_state.current_subj = raw_pages, subj
                except Exception as e: st.error(f"NEURAL SCAN FAILED: {e}")

        if st.session_state.eval_data:
            output_pdf = FPDF()
            for idx, img in enumerate(st.session_state.pages):
                st.markdown(f"<div class='page-header'>NEURAL FEEDBACK: PAGE {idx+1}</div>", unsafe_allow_html=True)
                col_img, col_sticky = st.columns([3, 1])
                
                # Filter marks for current page
                page_marks = next((p['marks'] for p in st.session_state.eval_data['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                
                with col_sticky:
                    st.subheader("📌 Sticky Notes")
                    if not page_marks:
                        st.write("No marks on this page.")
                    for i, m in enumerate(page_marks):
                        # FIX: Use expander to act as open/close sticky note
                        with st.expander(f"NOTE #{i+1}: {m['topic']}", expanded=True):
                            st.markdown(f'<div class="sticky-note">{m["note"]}</div>', unsafe_allow_html=True)
                        
                        # Apply mark to image using coordinates (scaled to img size)
                        marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                
                # Apply watermark logo to the script image
                marked_img = apply_logo(marked_img, "logo.jpg.png")
                col_img.image(marked_img, use_column_width=True)
                
                # PDF Generation Logic
                temp_filename = f"axom_p{idx}.png"
                marked_img.save(temp_filename)
                output_pdf.add_page()
                output_pdf.image(temp_filename, 0, 0, 210, 297) # A4 size in mm
                os.remove(temp_filename)
            
            # PDF Download Button
            pdf_bytes = output_pdf.output(dest='S')
            final_data = pdf_bytes.encode('latin1') if isinstance(pdf_bytes, str) else bytes(pdf_bytes)
            st.download_button("📩 DOWNLOAD MARKED REVIEW", data=final_data, file_name=f"AXOM_{subj}_Feedback.pdf")

    # --- MODE: REVISION HUB ---
    elif menu == "REVISION HUB":
        st.title("🚨 REVISION HUB")
        if not st.session_state.eval_data:
            st.info("NO ANALYSIS DATA FOUND. RUN A NEURAL SCAN FIRST.")
        else:
            for item in st.session_state.eval_data['weaknesses']:
                search_query = urllib.parse.quote(f"{st.session_state.current_subj} {item['yt']}")
                yt_link = f"https://www.youtube.com/results?search_query={search_query}"
                
                st.markdown(f"""
                <div class="red-alert-box">
                    <h2 style="color: #ff1744; margin:0; font-size: 1.25rem;">⚠️ GAP: {item['topic'].upper()}</h2>
                    <p style="color: #eee; margin: 10px 0;">{item['reason']}</p>
                    <a href="{yt_link}" target="_blank" class="yt-button">▶ OPEN NEURAL LESSON</a>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")
