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

# --- 1. HUD & INTERACTIVE CSS ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    
    /* STICKY NOTE STYLING */
    .sticky-note {
        background-color: #ffff88;
        color: #333;
        padding: 15px;
        border-radius: 5px;
        border-left: 10px solid #ffd700;
        margin-bottom: 10px;
        font-family: 'Comic Sans MS', cursive, sans-serif;
        box-shadow: 5px 5px 10px rgba(0,0,0,0.3);
        transform: rotate(-1deg);
        transition: transform 0.2s;
    }
    .sticky-note:hover { transform: rotate(0deg) scale(1.02); }
    
    .page-header { border-bottom: 2px solid #00d4ff; margin: 30px 0 10px 0; padding-bottom: 5px; font-weight: bold; color: #00d4ff; letter-spacing: 2px; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; font-weight: bold; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try:
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except Exception:
    st.error("CRITICAL: API KEY MISSING.")
    client = None

MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 50, 50, 255)
    sz = 40
    
    # Draw the symbol
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=12)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
    
    # Draw a "Neural ID Tag" next to the mark so user knows which sticky note matches
    draw.ellipse([x+sz, y-sz, x+sz+40, y-sz+40], fill=(0, 212, 255, 200))
    draw.text((x+sz+12, y-sz+8), str(index), fill=(0,0,0,255))
    
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12); w_percent = (base_width / float(logo.size[0]))
        h_size = int((float(logo.size[1]) * float(w_percent)))
        logo = logo.resize((base_width, h_size), Image.LANCZOS)
        pos = (img.width - logo.width - 50, img.height - logo.height - 50)
        img.paste(logo, pos, logo)
    return img

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = "Guest"
if "latest_eval" not in st.session_state: st.session_state.latest_eval = []
if "full_res" not in st.session_state: st.session_state.full_res = None

# --- 4. LOGIN ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="text-align:center; padding:50px; border:2px solid #00d4ff; border-radius:10px;">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        e_in = st.text_input("EMAIL")
        if st.button("UNLOCK"):
            if "@" in e_in: st.session_state.user_email = e_in; st.session_state.logged_in = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MAIN HUB ---
else:
    with st.sidebar:
        st.title("AXOM V3.7 PRO")
        if os.path.exists("logo.png"): st.image("logo.png")
        st.write(f"**ACTIVE:** {st.session_state.user_email}")
        menu = st.radio("PANEL", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("TERMINATE"): st.session_state.logged_in = False; st.rerun()

    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL SCAN & STICKY NOTES")
        c1, c2 = st.columns(2)
        board = c1.text_input("BOARD", "IGCSE")
        subj = c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT (PDF)", type=['pdf'])
        up_m = st.file_uploader("UPLOAD MARK SCHEME", type=['pdf'])

        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("AI GENERATING STICKY NOTES..."):
                try:
                    script_pages = convert_from_bytes(up_s.read())
                    p_txt = f"""
                    Senior Examiner for {board} {subj}.
                    Mark the script. For every feedback item, create a 'note'.
                    Return ONLY JSON:
                    {{
                        "page_marks": [{{ "page": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "topic" }}] }}],
                        "summary": {{ "grade": "A", "weaknesses": [{{ "topic": "Name", "reason": "Why", "yt": "Search terms" }}] }}
                    }}
                    """
                    response = client.models.generate_content(model=MODEL_ID, contents=[p_txt] + script_pages)
                    st.session_state.full_res = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    st.session_state.script_pages = script_pages
                    st.session_state.latest_eval = st.session_state.full_res.get("summary", {}).get("weaknesses", [])
                except Exception as e: st.error(f"NEURAL ERROR: {e}")

        # DISPLAY LOGIC WITH STICKY NOTES
        if st.session_state.full_res:
            output_pdf = FPDF()
            for idx, img in enumerate(st.session_state.script_pages):
                st.markdown(f"<div class='page-header'>PAGE {idx+1}</div>", unsafe_allow_html=True)
                
                # Split UI into Image and Sticky Note Sidebar
                col_img, col_notes = st.columns([3, 1])
                
                current_marks = next((p['marks'] for p in st.session_state.full_res['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                
                with col_notes:
                    st.subheader("📌 Sticky Notes")
                    for i, m in enumerate(current_marks):
                        # The Sticky Note - Uses Expander to Open/Close
                        with st.expander(f"NOTE #{i+1}: {m['topic']}", expanded=False):
                            st.markdown(f"""<div class="sticky-note">{m['note']}</div>""", unsafe_allow_html=True)
                        
                        # Apply mark with ID number to the image
                        marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                
                marked_img = apply_logo(marked_img, "logo.png")
                col_img.image(marked_img, use_column_width=True)
                
                # PDF Save
                temp_path = f"axom_{idx}.png"
                marked_img.save(temp_path); output_pdf.add_page(); output_pdf.image(temp_path, 0, 0, 210, 297); os.remove(temp_path)

            st.download_button("📩 DOWNLOAD MARKED PDF", data=bytes(output_pdf.output(dest='S')), file_name="AXOM_REVIEW.pdf")

    elif menu == "REVISION HUB":
        # (Revision Hub Logic remains same as previous pro version)
        st.title("📚 ADAPTIVE REVISION HUB")
        for item in st.session_state.latest_eval:
             st.video(f"https://www.youtube.com/embed?listType=search&list={item['yt']}")
