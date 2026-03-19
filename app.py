import streamlit as st
import google.generativeai as genai
import re
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. SYSTEM CONFIGURATION & THEME
# ==========================================
st.set_page_config(page_title="AXOM Global Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    .portal-header { 
        background-color: #001F3F; padding: 25px; border-left: 10px solid #D4AF37; 
        margin-bottom: 25px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .welcome-note { 
        font-size: 2.2rem; font-weight: bold; color: #D4AF37; text-align: center; 
        padding: 30px; text-transform: uppercase; letter-spacing: 2px;
    }
    .stButton>button { 
        border-radius: 0px; height: 60px; font-weight: bold; text-transform: uppercase; 
        transition: 0.4s; border: 1px solid #1e293b; background-color: #0f172a;
    }
    .stButton>button:hover { border: 1px solid #D4AF37; color: #D4AF37; background-color: #001F3F; }
    .zoom-container {
        width:100%; height:750px; overflow:scroll; border:3px solid #D4AF37; 
        background-color: #1a1a1a; padding: 15px; border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session State Management ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'board' not in st.session_state: st.session_state.board = None
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "DASHBOARD"

# ==========================================
# 2. THE MULTI-PEN & MATH DRAWING ENGINE
# ==========================================
def draw_axom_marks(draw, coords, note, w, h, category):
    """Handles Red (Error), Green (Correct), and Blue (Info) with Custom Font."""
    colors = {
        "error": "#FF3131",   # Bright Red
        "correct": "#39FF14", # Neon Green
        "info": "#1F51FF"     # Neon Blue
    }
    pen_color = colors.get(category.lower(), "#FF3131")
    
    # Scale Gemini coordinates (0-1000) to Image Pixels
    ymin, xmin, ymax, xmax = coords
    left, top, right, bottom = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000

    # 1. DRAW SHAPES (Vision Logic)
    if category.lower() == "correct":
        # Draw a Teacher's Tick
        draw.line([left, (top+bottom)/2, (left+right)/2, bottom, right, top-20], fill=pen_color, width=8)
    elif category.lower() == "error":
        # Draw a "Human" Circle
        draw.ellipse([left, top, right, bottom], outline=pen_color, width=5)
    else:
        # Draw an Underline for Info
        draw.line([left, bottom+10, right, bottom+10], fill=pen_color, width=4)

    # 2. APPLY CUSTOM HANDWRITING
    try:
        # Check if the note is Math-heavy to increase size
        is_math = any(sym in note for sym in ['=', '+', '-', '/', '^', '√', 'x', 'y'])
        font_size = 48 if is_math else 38
        axom_font = ImageFont.truetype("ibrahim_handwriting.ttf", font_size)
    except IOError:
        axom_font = ImageFont.load_default()

    # Position note: Errors get notes on right, Correct/Info get notes above
    text_pos = (right + 20, top) if category == "error" else (left, top - 60)
    draw.text(text_pos, note, fill=pen_color, font=axom_font)

# ==========================================
# 3. AUTHENTICATION & ONBOARDING
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>AXOM TERMINAL ACCESS</h1>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        email = st.text_input("AUTHORIZED EMAIL")
        name = st.text_input("FULL NAME")
        if st.button("AUTHENTICATE SYSTEM", use_container_width=True):
            if name and "@" in email:
                st.session_state.logged_in, st.session_state.user_name = True, name.upper()
                st.rerun()
    st.stop()

if st.session_state.board is None:
    st.markdown(f"<div class='welcome-note'>WELCOME TO AXOM {st.session_state.user_name}</div>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        st.session_state.board = st.selectbox("BOARD", ["CAMBRIDGE IGCSE/A-LEVEL", "EDEXCEL", "AQA", "IB"])
        st.session_state.subject = st.selectbox("SUBJECT", ["MATHEMATICS", "PHYSICS", "CHEMISTRY", "BIOLOGY", "ENGLISH"])
        if st.button("INITIALIZE COMMAND CENTER"): st.rerun()
    st.stop()

# ==========================================
# 4. MASTER NAVIGATION GRID
# ==========================================
st.markdown(f"""
    <div class='portal-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h2 style='margin:0; color: white;'>AXOM COMMAND: {st.session_state.menu_choice}</h2>
            <div style='text-align: right;'>
                <span style='color: #D4AF37; font-weight: bold;'>{st.session_state.user_name}</span><br>
                <span style='font-size: 0.8rem;'>{st.session_state.board} | {st.session_state.subject}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

nav1, nav2, nav3 = st.columns(3)
with nav1:
    if st.button("📄 PAPER CHECKER", use_container_width=True): st.session_state.menu_choice = "PAPER CHECKER"
    if nav1.button("🏫 CLASSROOMS", use_container_width=True): st.session_state.menu_choice = "CLASSROOMS"
with nav2:
    if st.button("📊 REPORTS & HISTORY", use_container_width=True): st.session_state.menu_choice = "REPORTS"
    if nav2.button("🤖 INTERACTIVE AI", use_container_width=True): st.session_state.menu_choice = "AI CHAT"
with nav3:
    if st.button("⚡ FLASHCARDS", use_container_width=True): st.session_state.menu_choice = "FLASHCARDS"
    if nav3.button("⚙️ SETTINGS", use_container_width=True): st.session_state.menu_choice = "SETTINGS"

st.divider()

# ==========================================
# 5. DYNAMIC MODULE: PAPER CHECKER
# ==========================================
view = st.session_state.menu_choice

if view == "PAPER CHECKER":
    st.markdown("<h3 style='color: #D4AF37;'>AXOM VISION: TRUE-INK ANALYZER</h3>", unsafe_allow_html=True)
    
    up_col, set_col = st.columns([2, 1])
    with up_col:
        uploaded_file = st.file_uploader("UPLOAD EXAM SCRIPT", type=['pdf', 'jpg', 'png', 'jpeg'])
    with set_col:
        zoom_val = st.select_slider("VIEW RESOLUTION", options=["Standard", "Detailed", "Ultra-HD"])
        width_px = {"Standard": 900, "Detailed": 1400, "Ultra-HD": 2200}[zoom_val]

    if uploaded_file:
        if st.button("INITIATE VISION SCAN", use_container_width=True):
            with st.spinner("AI EXAMINER CALIBRATING VISION..."):
                try:
                    # 1. Convert File to Image
                    if uploaded_file.type == "application/pdf":
                        images = convert_from_bytes(uploaded_file.getvalue())
                        img = images[0].convert("RGB")
                    else:
                        img = Image.open(uploaded_file).convert("RGB")
                    
                    w, h = img.size
                    draw = ImageDraw.Draw(img)

                    # 2. AI Vision Analysis (Multimodal - No OCR)
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    prompt = f"""
                    Identify 5 points in this {st.session_state.subject} paper.
                    Points can be: 'error' (mistake), 'correct' (good work), or 'info' (advice).
                    Look specifically at Math working, diagrams, and handwriting.
                    
                    Return strictly in this format for each point:
                    [ymin, xmin, ymax, xmax] | category | Note
                    """
                    
                    response = model.generate_content([prompt, img])
                    
                    # 3. Apply Visual Marks
                    for line in response.text.split('\n'):
                        if '|' in line:
                            parts = line.split('|')
                            coords_raw = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', parts[0])
                            if coords_raw:
                                coords = [int(x) for x in coords_raw.groups()]
                                cat, note = parts[1].strip(), parts[2].strip()
                                draw_axom_marks(draw, coords, note, w, h, cat)

                    # 4. Display in Zoomable Container
                    st.success("VISION ANALYSIS COMPLETE")
                    
                    # Encode image to display in custom HTML scroll box
                    buffered = io.BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    
                    st.markdown(f"""
                        <div class="zoom-container">
                            <img src="data:image/png;base64,{img_str}" style="width:{width_px}px;">
                        </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"SYSTEM HALTED: {e}")

elif view == "CLASSROOMS":
    st.components.v1.iframe("https://axom.daily.co/Main-Classroom", height=800)

elif view == "SETTINGS":
    if st.button("HARD RESET & LOGOUT"):
        st.session_state.clear()
        st.rerun()

else:
    st.info(f"The {view} module is currently being optimized for the 2026 session.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #444;'>AXOM GLOBAL TERMINAL v2.1 | 2026 SERIES</p>", unsafe_allow_html=True)
