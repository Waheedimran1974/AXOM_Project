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
    .portal-header { background-color: #001F3F; padding: 25px; border-left: 10px solid #D4AF37; margin-bottom: 25px; }
    .welcome-note { font-size: 2.2rem; font-weight: bold; color: #D4AF37; text-align: center; padding: 30px; text-transform: uppercase; }
    .stButton>button { border-radius: 0px; height: 65px; font-weight: bold; text-transform: uppercase; transition: 0.4s; border: 1px solid #1e293b; }
    .stButton>button:hover { border: 1px solid #D4AF37; color: #D4AF37; background-color: #001F3F; }
    </style>
    """, unsafe_allow_html=True)

# --- Session State ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'board' not in st.session_state: st.session_state.board = None
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "DASHBOARD"

# ==========================================
# 2. UTILITY & DRAWING FUNCTIONS
# ==========================================
def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9_.+-]+@(gmail\.com|yahoo\.com|icloud\.com|apple\.com)$", email)

def draw_axom_marks(draw, coords, note, w, h, category):
    """Draws multi-color marks and loads custom handwriting."""
    colors = {
        "error": "#FF0000",   # Red
        "correct": "#00FF00", # Green
        "info": "#1E90FF"     # Blue
    }
    pen_color = colors.get(category.lower(), "#FF0000")
    
    # Scale Gemini coordinates (0-1000) to actual image pixels
    ymin, xmin, ymax, xmax = coords
    left, top, right, bottom = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000

    # Draw the Shape
    if category.lower() == "correct":
        # Draw a checkmark
        draw.line([left, bottom, (left+right)/2, bottom+20, right, top], fill=pen_color, width=5)
    else:
        # Draw a circle
        draw.ellipse([left, top, right, bottom], outline=pen_color, width=4)

    # --- THE HANDWRITING ENGINE ---
    try:
        # The system looks for your custom file here. 
        # Size 36 is usually good for handwriting fonts on A4 paper.
        axom_font = ImageFont.truetype("ibrahim_handwriting.ttf", 36)
    except IOError:
        # If the file isn't uploaded yet, it won't crash. It uses a basic font.
        axom_font = ImageFont.load_default()

    # Write the note
    draw.text((right + 15, top), note, fill=pen_color, font=axom_font)

# ==========================================
# 3. ACCESS GATE
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>AXOM TERMINAL ACCESS</h1>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        email = st.text_input("AUTHORIZED EMAIL")
        name = st.text_input("FULL NAME")
        if st.button("AUTHENTICATE SYSTEM", use_container_width=True):
            if is_valid_email(email) and name:
                st.session_state.logged_in = True
                st.session_state.user_name = name.upper()
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID EMAIL DOMAIN.")
    st.stop()

if st.session_state.board is None:
    st.markdown(f"<div class='welcome-note'>WELCOME TO AXOM {st.session_state.user_name}</div>", unsafe_allow_html=True)
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        st.session_state.board = st.selectbox("SELECT BOARD", ["CAMBRIDGE IGCSE/A-LEVEL", "EDEXCEL", "OXFORD AQA", "IB"])
        st.session_state.subject = st.selectbox("SELECT SUBJECT", ["ENGLISH", "MATHEMATICS", "PHYSICS", "BIOLOGY", "CHEMISTRY"])
        if st.button("INITIALIZE DASHBOARD"): st.rerun()
    st.stop()

# ==========================================
# 4. COMMAND CENTER
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

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📄 PAPER CHECKER", use_container_width=True): st.session_state.menu_choice = "PAPER CHECKER"
    if st.button("🏫 CLASSROOMS (AXON)", use_container_width=True): st.session_state.menu_choice = "CLASSROOMS"
with col2:
    if st.button("📊 REPORTS & HISTORY", use_container_width=True): st.session_state.menu_choice = "REPORTS"
    if st.button("🤖 INTERACTIVE AI", use_container_width=True): st.session_state.menu_choice = "AI CHAT"
with col3:
    if st.button("⚡ FLASHCARDS", use_container_width=True): st.session_state.menu_choice = "FLASHCARDS"
    if st.button("⚙️ SETTINGS", use_container_width=True): st.session_state.menu_choice = "SETTINGS"

st.divider()

# ==========================================
# 5. DYNAMIC MODULES
# ==========================================
view = st.session_state.menu_choice

if view == "PAPER CHECKER":
    st.markdown("<h3 style='color: #D4AF37;'>AXOM TRUE-INK VISION MARKING</h3>", unsafe_allow_html=True)
    
    col_upload, col_controls = st.columns([2, 1])
    with col_upload:
        uploaded_file = st.file_uploader("UPLOAD SCRIPT", type=['pdf', 'jpg', 'png'])
    with col_controls:
        st.info("Display Settings")
        zoom_level = st.select_slider("VIEW RESOLUTION", options=["Standard", "Detailed", "Ultra-HD"])
        img_width = {"Standard": 800, "Detailed": 1200, "Ultra-HD": 2000}[zoom_level]

    if uploaded_file:
        if st.button("RUN VISION SCAN & MARK", use_container_width=True):
            with st.spinner("AI EXAMINER APPLYING TRUE-INK PROTOCOL..."):
                try:
                    # 1. Process Image
                    if uploaded_file.type == "application/pdf":
                        images = convert_from_bytes(uploaded_file.getvalue())
                        img = images[0].convert("RGB")
                    else:
                        img = Image.open(uploaded_file).convert("RGB")
                    
                    w, h = img.size
                    draw = ImageDraw.Draw(img)

                    # 2. Advanced Vision Prompt
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    prompt = f"""
                    Analyze this {st.session_state.subject} script. Look at the layout, diagrams, and working out.
                    Identify exactly 4 distinct points to mark. 
                    Assign one of these categories to each point: 'error', 'correct', or 'info'.
                    
                    For each point, provide:
                    1. Coordinates in [ymin, xmin, ymax, xmax] (0-1000 scale).
                    2. Category ('error', 'correct', 'info').
                    3. A short, natural teacher note (max 6 words).
                    
                    Strict output format:
                    [ymin, xmin, ymax, xmax] | category | Note
                    """
                    
                    response = model.generate_content([prompt, img])
                    
                    # 3. Apply Multi-Color & Custom Font Marks
                    for line in response.text.split('\n'):
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 3:
                                coord_match = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', parts[0])
                                if coord_match:
                                    coords = [int(x) for x in coord_match.groups()]
                                    category = parts[1].strip()
                                    note = parts[2].strip()
                                    draw_axom_marks(draw, coords, note, w, h, category)

                    # 4. Display the Zoomable Result
                    st.success("MARKING COMPLETE")
                    st.markdown(f"""
                        <div style="width:100%; height:700px; overflow:scroll; border:2px solid #D4AF37; background-color: #1a1a1a; padding: 10px;">
                            <img src="data:image/png;base64,{base64.b64encode(io.BytesIO().tap(lambda b: img.save(b, format='PNG')).getvalue()).decode()}" 
                                 style="width:{img_width}px;">
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("VIEW RAW EXAMINER DATA"):
                        st.write(response.text)

                except Exception as e:
                    st.error(f"SYSTEM ERROR: {e}")
                    st.info("Check if packages.txt with 'poppler-utils' is in your GitHub.")

elif view == "CLASSROOMS":
    st.components.v1.iframe("https://axom.daily.co/Main-Classroom", height=700)

elif view == "SETTINGS":
    st.write(f"Logged in as: {st.session_state.user_email}")
    if st.button("CLEAR ALL DATA & SIGN OUT"):
        st.session_state.clear()
        st.rerun()

else:
    st.info(f"The {view} module is pending configuration.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #555;'>COPYRIGHT 2026 AXOM GLOBAL</p>", unsafe_allow_html=True)
