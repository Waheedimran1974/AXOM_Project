import streamlit as st
import google.generativeai as genai
import re
import io
import base64
import time
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. CYBER-WORLD UI & CSS (THE GLOW)
# ==========================================
st.set_page_config(page_title="AXOM // CYBER-TERMINAL", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Base Terminal Background */
    .stApp {
        background: radial-gradient(circle, #0d1117 0%, #000000 100%);
        color: #e6edf3;
        font-family: 'Courier New', Courier, monospace;
    }

    /* Cyber Scanline Effect */
    .stApp::before {
        content: " ";
        display: block;
        position: absolute;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                    linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
        z-index: 2;
        background-size: 100% 2px, 3px 100%;
        pointer-events: none;
    }

    /* Glowing Cyber Button */
    .stButton>button {
        background: rgba(0, 0, 0, 0.6) !important;
        color: #00f3ff !important;
        border: 1px solid #00f3ff !important;
        border-radius: 0px !important;
        height: 60px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        transition: 0.3s all ease-in-out !important;
        box-shadow: 0 0 5px #00f3ff, inset 0 0 5px #00f3ff !important;
    }

    .stButton>button:hover {
        background: #00f3ff !important;
        color: #000 !important;
        box-shadow: 0 0 25px #00f3ff, 0 0 50px #00f3ff !important;
        transform: scale(1.02);
    }

    /* AXOM Gold Variant Button */
    div[data-testid="stVerticalBlock"] > div:nth-child(1) button {
        border-color: #D4AF37 !important;
        color: #D4AF37 !important;
        box-shadow: 0 0 5px #D4AF37, inset 0 0 5px #D4AF37 !important;
    }
    div[data-testid="stVerticalBlock"] > div:nth-child(1) button:hover {
        background: #D4AF37 !important;
        color: #000 !important;
        box-shadow: 0 0 25px #D4AF37, 0 0 50px #D4AF37 !important;
    }

    /* Login Box (Glassmorphism) */
    .auth-box {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        padding: 60px;
        border: 1px solid rgba(0, 243, 255, 0.3);
        border-radius: 2px;
        text-align: center;
        margin: auto;
        width: 500px;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.1);
    }

    /* Terminal Header */
    .cyber-header {
        border-bottom: 1px solid #00f3ff;
        padding-bottom: 10px;
        margin-bottom: 30px;
        text-shadow: 0 0 10px #00f3ff;
    }

    /* Image Container with Glow */
    .zoom-container {
        width:100%; height:800px; overflow:scroll; 
        border: 1px solid #00f3ff; 
        background-color: #000;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session Management ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'view' not in st.session_state: st.session_state.view = "DASHBOARD"

# ==========================================
# 2. LOGIN GATE (CYBER INTERFACE)
# ==========================================
if not st.session_state.auth:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown("""
            <div class="auth-box">
                <h1 style="color: #00f3ff; letter-spacing: 10px; margin-bottom: 0;">AXOM</h1>
                <p style="color: #555; font-size: 0.8rem; margin-bottom: 40px;">// SECURE NODE ACCESS //</p>
        """, unsafe_allow_html=True)
        
        if st.button("LOG IN WITH GOOGLE CLOUD"):
            st.session_state.auth = True
            st.session_state.user = "CYBER_USER_01"
            st.rerun()
            
        if st.button("LOG IN WITH MICROSOFT AZURE"):
            st.session_state.auth = True
            st.session_state.user = "CYBER_USER_01"
            st.rerun()

        st.markdown("""
                <p style="color: #00f3ff; font-size: 0.6rem; margin-top: 40px; opacity: 0.5;">
                    SYSTEM STATUS: ENCRYPTED<br>TERMINAL ID: 2026-AXOM-X
                </p>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# 3. COMMAND DASHBOARD
# ==========================================
st.markdown(f"""
    <div class="cyber-header">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <h2 style="margin:0; color: #00f3ff; letter-spacing: 5px;">TERMINAL_COMMAND</h2>
            <div style="text-align: right; color: #D4AF37; font-size: 0.9rem;">
                USER: {st.session_state.user} | STATUS: <span style="color: #39FF14;">ONLINE</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Glowing Navigation Grid
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("PAPER CHECKER"): st.session_state.view = "PAPER CHECKER"
with c2:
    if st.button("AI CHAT"): st.session_state.view = "AI CHAT"
with c3:
    if st.button("REPORTS"): st.session_state.view = "REPORTS"
with c4:
    if st.button("DISCONNECT"):
        st.session_state.auth = False
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 4. VISION MODULE (TRUE-INK)
# ==========================================
def draw_cyber_marks(draw, coords, note, w, h, cat):
    # Cyber Colors
    colors = {"error": "#ff003c", "correct": "#00f3ff", "info": "#D4AF37"}
    color = colors.get(cat.lower(), "#ff003c")
    
    ymin, xmin, ymax, xmax = coords
    l, t, r, b = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000

    if cat.lower() == "correct":
        draw.line([l, (t+b)/2, (l+r)/2, b, r, t-20], fill=color, width=10)
    else:
        draw.rectangle([l, t, r, b], outline=color, width=6)

    try:
        font = ImageFont.truetype("ibrahim_handwriting.ttf", 45)
    except:
        font = ImageFont.load_default()
        
    draw.text((r + 15, t), note, fill=color, font=font)

if st.session_state.view == "PAPER CHECKER":
    st.markdown("<h3 style='color: #00f3ff;'>[ SCANNING_PROTOCOL_INITIALIZED ]</h3>", unsafe_allow_html=True)
    
    file = st.file_uploader("UPLOAD DATA STREAM (PDF/JPG)", type=['pdf', 'jpg', 'png'])
    
    if file:
        col_z, col_b = st.columns([1, 1])
        with col_z:
            zoom = st.select_slider("RENDER RESOLUTION", options=["LOW-RES", "HD-STREAM", "NEURAL-LINK"])
            res_px = {"LOW-RES": 900, "HD-STREAM": 1500, "NEURAL-LINK": 2500}[zoom]
        
        if st.button("EXECUTE NEURAL MARKING"):
            with st.spinner("DECRYPTING SCRIPT..."):
                try:
                    if file.type == "application/pdf":
                        img = convert_from_bytes(file.getvalue())[0].convert("RGB")
                    else:
                        img = Image.open(file).convert("RGB")
                    
                    w, h = img.size
                    draw = ImageDraw.Draw(img)

                    model = genai.GenerativeModel('gemini-2.0-flash')
                    resp = model.generate_content(["Mark this script. [ymin, xmin, ymax, xmax] | category | Note", img])
                    
                    for line in resp.text.split('\n'):
                        if '|' in line:
                            coords = [int(x) for x in re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', line).groups()]
                            draw_cyber_marks(draw, coords, line.split('|')[2].strip(), w, h, line.split('|')[1].strip())

                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.markdown(f'<div class="zoom-container"><img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" style="width:{res_px}px;"></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"SYSTEM FAILURE: {e}")

st.markdown("<br><br><p style='text-align: center; color: #222;'>// AXOM_OS_V2.7 // NO_UNAUTHORIZED_ACCESS //</p>", unsafe_allow_html=True)
