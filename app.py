import streamlit as st
import google.generativeai as genai
import re
import io
import base64
import time
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. SECURITY & SYSTEM CONFIG
# ==========================================
# CHANGE THIS KEY TO YOUR SECRET PASSWORD
MASTER_ACCESS_KEY = "AXOM-2026-PRO" 

st.set_page_config(page_title="AXOM Global Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .auth-card {
        background-color: #001F3F; padding: 40px; border-radius: 15px;
        border: 2px solid #D4AF37; box-shadow: 0px 0px 30px rgba(212, 175, 55, 0.2);
        text-align: center; margin-top: 50px;
    }
    .portal-header { 
        background-color: #001F3F; padding: 25px; border-left: 10px solid #D4AF37; 
        margin-bottom: 25px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .stButton>button { 
        border-radius: 5px; height: 55px; font-weight: bold; text-transform: uppercase; 
        transition: 0.4s; border: 1px solid #D4AF37; background-color: #0f172a; color: #D4AF37;
    }
    .stButton>button:hover { background-color: #D4AF37; color: #001F3F; }
    .zoom-container {
        width:100%; height:750px; overflow:scroll; border:3px solid #D4AF37; 
        background-color: #1a1a1a; padding: 15px; border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Enhanced Session State ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "DASHBOARD"

# ==========================================
# 2. THE IRON GATE (LOGIN SYSTEM)
# ==========================================
if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
            <div class="auth-card">
                <h1 style="color: #D4AF37; margin-bottom: 5px;">AXOM GLOBAL</h1>
                <p style="color: #888; margin-bottom: 30px;">SECURE TERMINAL v2.5</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.write("### ENTER SYSTEM CREDENTIALS")
            input_name = st.text_input("FULL NAME", placeholder="e.g. IBRAHIM W. IMRAN")
            input_email = st.text_input("AUTHORIZED EMAIL", placeholder="student@gmail.com")
            input_key = st.text_input("SYSTEM ACCESS KEY", type="password", placeholder="••••••••")
            
            if st.button("INITIALIZE SECURE UPLINK", use_container_width=True):
                if input_key == MASTER_ACCESS_KEY:
                    if "@" in input_email and len(input_name) > 2:
                        st.session_state.authenticated = True
                        st.session_state.user_name = input_name.upper()
                        st.session_state.user_email = input_email
                        st.success("AUTHENTICATION SUCCESSFUL. LOADING ENGINES...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("INVALID IDENTITY FORMAT.")
                else:
                    st.error("ACCESS DENIED: INCORRECT SYSTEM KEY.")
    st.stop()

# ==========================================
# 3. CORE LOGIC (DRAWING & VISION)
# ==========================================
def draw_axom_marks(draw, coords, note, w, h, category):
    colors = {"error": "#FF3131", "correct": "#39FF14", "info": "#1F51FF"}
    pen_color = colors.get(category.lower(), "#FF3131")
    ymin, xmin, ymax, xmax = coords
    left, top, right, bottom = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000

    if category.lower() == "correct":
        draw.line([left, (top+bottom)/2, (left+right)/2, bottom, right, top-20], fill=pen_color, width=8)
    elif category.lower() == "error":
        draw.ellipse([left, top, right, bottom], outline=pen_color, width=6)
    else:
        draw.line([left, bottom+10, right, bottom+10], fill=pen_color, width=5)

    try:
        is_math = any(sym in note for sym in ['=', '+', '-', '/', '^', '√', 'x', 'y'])
        f_size = 50 if is_math else 40
        axom_font = ImageFont.truetype("ibrahim_handwriting.ttf", f_size)
    except:
        axom_font = ImageFont.load_default()

    text_pos = (right + 20, top) if category == "error" else (left, top - 65)
    draw.text(text_pos, note, fill=pen_color, font=axom_font)

# ==========================================
# 4. COMMAND CENTER INTERFACE
# ==========================================
st.markdown(f"""
    <div class='portal-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h2 style='margin:0; color: white;'>AXOM COMMAND: {st.session_state.menu_choice}</h2>
            <div style='text-align: right;'>
                <span style='color: #D4AF37; font-weight: bold;'>{st.session_state.user_name}</span><br>
                <span style='font-size: 0.8rem; color: #888;'>SECURE SESSION ACTIVE</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("📄 PAPER CHECKER", use_container_width=True): st.session_state.menu_choice = "PAPER CHECKER"
with nav2:
    if st.button("🤖 AI CHAT", use_container_width=True): st.session_state.menu_choice = "AI CHAT"
with nav3:
    if st.button("⚙️ SETTINGS / LOGOUT", use_container_width=True): st.session_state.menu_choice = "SETTINGS"

st.divider()

# ==========================================
# 5. MODULES
# ==========================================
if st.session_state.menu_choice == "PAPER CHECKER":
    st.markdown("<h3 style='color: #D4AF37;'>VISION ANALYZER</h3>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        uploaded_file = st.file_uploader("UPLOAD SCRIPT", type=['pdf', 'jpg', 'png', 'jpeg'])
    with col_b:
        zoom_val = st.select_slider("VIEW RESOLUTION", options=["Standard", "Detailed", "Ultra-HD"])
        width_px = {"Standard": 900, "Detailed": 1400, "Ultra-HD": 2200}[zoom_val]

    if uploaded_file:
        if st.button("RUN VISION SCAN", use_container_width=True):
            with st.spinner("AI EXAMINER ANALYZING..."):
                try:
                    if uploaded_file.type == "application/pdf":
                        images = convert_from_bytes(uploaded_file.getvalue())
                        img = images[0].convert("RGB")
                    else:
                        img = Image.open(uploaded_file).convert("RGB")
                    
                    w, h = img.size
                    draw = ImageDraw.Draw(img)

                    model = genai.GenerativeModel('gemini-2.0-flash')
                    prompt = "Identify 5 points: 'error', 'correct', or 'info'. Format: [ymin, xmin, ymax, xmax] | category | Note"
                    
                    response = model.generate_content([prompt, img])
                    
                    for line in response.text.split('\n'):
                        if '|' in line:
                            parts = line.split('|')
                            coords_raw = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', parts[0])
                            if coords_raw:
                                coords = [int(x) for x in coords_raw.groups()]
                                draw_axom_marks(draw, coords, parts[1].strip(), parts[2].strip(), w, h, parts[1].strip())

                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    st.markdown(f'<div class="zoom-container"><img src="data:image/png;base64,{img_str}" style="width:{width_px}px;"></div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"SYSTEM ERROR: {e}")

elif st.session_state.menu_choice == "SETTINGS":
    st.write(f"USER: {st.session_state.user_name}")
    st.write(f"EMAIL: {st.session_state.user_email}")
    if st.button("TERMINATE SESSION & LOGOUT"):
        st.session_state.clear()
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: #444;'>AXOM GLOBAL SECURE TERMINAL v2.5</p>", unsafe_allow_html=True)
