import streamlit as st
from google import genai
import os
import json
import re
import io
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & EXAMINER INTERFACE STYLING ---
st.set_page_config(page_title="AXOM | MASTER EXAMINER", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #001224 0%, #000000 100%); color: #00e5ff; font-family: 'Inter', monospace; }
    
    /* GREEN STICKY (CORRECT - SILENT & GOLDEN) */
    .sticky-green {
        background: #d4edda; color: #155724; padding: 10px 15px; border-radius: 2px;
        border-left: 6px solid #28a745; margin-bottom: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.4); 
        font-family: 'Comic Sans MS', 'Chalkboard SE', cursive; font-weight: bold; font-size: 1.1rem;
    }
    
    /* RED STICKY (INCORRECT - EXPLANATORY) */
    .sticky-red {
        background: #f8d7da; color: #721c24; padding: 15px; border-radius: 2px;
        border-left: 6px solid #dc3545; margin-bottom: 15px;
        box-shadow: 3px 3px 12px rgba(0,0,0,0.5); 
        font-family: 'Comic Sans MS', 'Chalkboard SE', cursive; font-size: 1rem; line-height: 1.4;
    }
    
    .red-alert-box { 
        background: linear-gradient(145deg, rgba(220, 53, 69, 0.1), rgba(0,0,0,0)); 
        border: 1px solid #dc3545; padding: 25px; border-radius: 8px; margin-bottom: 25px; 
    }
    
    .stButton>button { 
        width: 100%; background: linear-gradient(90deg, #00e5ff, #007bff) !important; 
        color: #fff !important; font-weight: 900; border-radius: 4px; height: 50px; letter-spacing: 1px;
    }
    
    /* DIRECT VIDEO LAUNCH BUTTON */
    .yt-launch-btn { 
        display: inline-block; width: 100%; text-align: center; background: #ff0000; 
        color: #ffffff !important; padding: 14px; border-radius: 6px; 
        text-decoration: none; font-weight: 900; font-size: 1.1rem; letter-spacing: 1px;
        transition: all 0.2s ease-in-out;
    }
    .yt-launch-btn:hover { background: #cc0000; transform: translateY(-2px); box-shadow: 0 4px 15px rgba(255,0,0,0.4); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    # Real Examiner Ink Colors
    color = (0, 160, 0, 255) if mark_type == 'tick' else (220, 20, 60, 255)
    sz = 40
    
    # Hand-drawn aesthetic
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz+10), (x+sz+10, y-sz-10)], fill=color, width=12)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
        
    draw.ellipse([x+sz+5, y-sz-5, x+sz+65, y-sz+55], fill=color)
    draw.text((x+sz+22, y-sz+8), str(index), fill=(255,255,255,255))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.jpg.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12)
        logo = logo.resize((base_width, int(logo.size[1] * (base_width/logo.size[0]))), Image.LANCZOS)
        img.paste(logo, (img.width-logo.width-40, img.height-logo.height-40), logo)
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
        st.markdown('<div style="border:1px solid #00e5ff; padding:50px; border-radius:8px; background:rgba(0,10,20,0.9); text-align:center; box-shadow: 0 0 30px rgba(0, 229, 255, 0.1);">', unsafe_allow_html=True)
        st.title("AXOM | SECURE UPLINK")
        u_email = st.text_input("ENTER CREDENTIALS (EMAIL)")
        if st.button("INITIALIZE SESSION"):
            if "@" in u_email: st.session_state.user_email, st.session_state.logged_in = u_email, True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    with st.sidebar:
        st.title("AXOM V4.6 PRO")
        st.markdown(f"<span style='color:#00e5ff;'>● ACTIVE: {st.session_state.user_email}</span>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("COMMAND CENTER", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("DISCONNECT"): st.session_state.logged_in = False; st.rerun()

    # --- SCANNER ---
    if menu == "NEURAL SCAN":
        st.title("🧠 MASTER EXAMINER PROTOCOL")
        c1, c2 = st.columns(2)
        board, subj = c1.text_input("BOARD", "IGCSE"), c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT", type=['pdf'])

        if up_s and st.button("EXECUTE GRADING ALGORITHM"):
            with st.spinner("AI EXAMINING LOGIC & VOCABULARY..."):
                try:
                    raw_pages = convert_from_bytes(up_s.read())
                    
                    # PROMPT ENGINEERING: Direct URL injection & strict marking criteria
                    prompt = f"""
                    You are a strict Senior Examiner for {board} {subj}. 
                    Evaluate the following script based on the 2022 syllabus criteria.
                    Focus entirely on logic, scientific vocabulary, and conceptual understanding.
                    IGNORE mechanical errors such as capitalization and paragraphing structure.

                    Return ONLY a valid JSON object in this exact structure:
                    {{
                        "page_marks": [{{ "page": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "feedback", "topic": "..." }}] }}],
                        "weaknesses": [{{ "topic": "...", "reason": "...", "direct_vid_url": "https://youtu.be/..." }}]
                    }}

                    CRITICAL RULES:
                    1. If type is 'tick', the 'note' MUST be exactly the word 'Correct'. Nothing else.
                    2. If type is 'cross', the 'note' MUST be a clear explanation of why the logic or vocabulary failed.
                    3. For 'direct_vid_url', you MUST generate a direct, valid YouTube link (e.g., https://youtu.be/xxx) that explains the core weakness. DO NOT return a search query.
                    """
                    
                    response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + raw_pages)
                    st.session_state.eval_data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    st.session_state.pages, st.session_state.current_subj = raw_pages, subj
                except Exception as e: st.error(f"SYSTEM OVERLOAD / SCAN ERROR: {e}")

        if st.session_state.eval_data:
            pdf = FPDF()
            for idx, img in enumerate(st
