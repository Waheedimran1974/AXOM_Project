import streamlit as st
import google.generativeai as genai
import re
import io
import base64
import time
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. AXOM CORE ENGINE CONFIG
# ==========================================
st.set_page_config(page_title="AXOM Global Terminal", layout="wide", initial_sidebar_state="collapsed")

# Professional Dark UI with Gold Accents
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #ffffff; }
    
    /* Login Card Styling */
    .login-container {
        display: flex; justify-content: center; align-items: center; height: 80vh;
    }
    .auth-card {
        background-color: #001F3F; padding: 50px; border-radius: 20px;
        border: 1px solid #D4AF37; box-shadow: 0px 10px 40px rgba(0,0,0,0.8);
        text-align: center; width: 450px;
    }
    .sso-button {
        display: flex; align-items: center; justify-content: center;
        background-color: white; color: #000; padding: 12px;
        border-radius: 5px; cursor: pointer; font-weight: bold;
        margin-top: 20px; border: 1px solid #ddd; transition: 0.3s;
    }
    .sso-button:hover { background-color: #f1f1f1; transform: translateY(-2px); }
    
    /* Dashboard Styling */
    .portal-header { 
        background-color: #001F3F; padding: 20px; border-bottom: 3px solid #D4AF37; 
        margin-bottom: 30px;
    }
    .zoom-container {
        width:100%; height:750px; overflow:scroll; border:2px solid #D4AF37; 
        background-color: #1a1a1a; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Session Management ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_data' not in st.session_state: st.session_state.user_data = {}
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "DASHBOARD"

# ==========================================
# 2. THE SECURE ACCESS GATE (SSO INTERFACE)
# ==========================================
if not st.session_state.authenticated:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # This is the actual UI users will see
    with st.container():
        st.markdown("""
            <div class="auth-card">
                <h1 style="color: #D4AF37; letter-spacing: 5px; margin-bottom: 0;">AXOM</h1>
                <p style="color: #888; font-size: 0.9rem; margin-bottom: 40px;">GLOBAL EXAMINATION TERMINAL</p>
                <hr style="border: 0.5px solid #1e293b; margin-bottom: 30px;">
        """, unsafe_allow_html=True)
        
        # Google Login Simulation (Integration point for OAuth)
        if st.button("🔴 SIGN IN WITH GOOGLE", use_container_width=True):
            # In a live app, this triggers the Google Popup
            st.session_state.authenticated = True
            st.session_state.user_data = {"name": "AUTHORIZED USER", "email": "verified@axom.com"}
            st.rerun()
            
        if st.button("🔵 SIGN IN WITH MICROSOFT", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.user_data = {"name": "AUTHORIZED USER", "email": "verified@axom.com"}
            st.rerun()

        st.markdown("""
                <p style="color: #555; font-size: 0.7rem; margin-top: 30px;">
                    By signing in, you agree to AXOM Security Protocols.<br>
                    v2.6 SECURE UPLINK
                </p>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 3. VISION & DRAWING ENGINE
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

    try:
        f_size = 45 if any(s in note for s in ['=', '+', '-', '/']) else 38
        axom_font = ImageFont.truetype("ibrahim_handwriting.ttf", f_size)
    except:
        axom_font = ImageFont.load_default()

    draw.text((right + 20, top), note, fill=pen_color, font=axom_font)

# ==========================================
# 4. COMMAND CENTER (POST-LOGIN)
# ==========================================
st.markdown(f"""
    <div class='portal-header'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <h2 style='margin:0; color: #D4AF37; letter-spacing: 2px;'>AXOM // TERMINAL</h2>
            <div style='text-align: right;'>
                <span style='color: white; font-weight: bold;'>{st.session_state.user_data.get('name')}</span><br>
                <span style='font-size: 0.7rem; color: #39FF14;'>● SYSTEM SECURE</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Navigation Grid
n1, n2, n3, n4 = st.columns(4)
with n1:
    if st.button("📄 PAPER CHECKER", use_container_width=True): st.session_state.menu_choice = "PAPER CHECKER"
with n2:
    if st.button("🤖 AI ASSISTANT", use_container_width=True): st.session_state.menu_choice = "AI CHAT"
with n3:
    if st.button("📊 ANALYTICS", use_container_width=True): st.session_state.menu_choice = "REPORTS"
with n4:
    if st.button("🚪 LOGOUT", use_container_width=True): 
        st.session_state.authenticated = False
        st.rerun()

st.divider()

# ==========================================
# 5. MODULE: PAPER CHECKER
# ==========================================
if st.session_state.menu_choice == "PAPER CHECKER":
    st.markdown("### VISION ENGINE: TRUE-INK ANALYSIS")
    
    file = st.file_uploader("DROP SCRIPT HERE", type=['pdf', 'jpg', 'png', 'jpeg'])
    
    if file:
        z_col, b_col = st.columns([1, 1])
        with z_col:
            res = st.select_slider("SCAN RESOLUTION", options=["SD", "HD", "4K"])
            px = {"SD": 900, "HD": 1400, "4K": 2400}[res]
        
        if st.button("EXECUTE SCAN", use_container_width=True):
            with st.spinner("AI VISION ANALYZING PIXELS..."):
                try:
                    # Convert to Image
                    if file.type == "application/pdf":
                        img = convert_from_bytes(file.getvalue())[0].convert("RGB")
                    else:
                        img = Image.open(file).convert("RGB")
                    
                    w, h = img.size
                    draw = ImageDraw.Draw(img)

                    # AI Logic
                    model = genai.GenerativeModel('gemini-2.0-flash')
                    resp = model.generate_content(["Mark this script. [ymin, xmin, ymax, xmax] | category | Note", img])
                    
                    for line in resp.text.split('\n'):
                        if '|' in line:
                            coords = [int(x) for x in re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', line).groups()]
                            parts = line.split('|')
                            draw_axom_marks(draw, coords, parts[2].strip(), w, h, parts[1].strip())

                    # Zoom Display
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.markdown(f'<div class="zoom-container"><img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" style="width:{px}px;"></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"SCAN FAILED: {e}")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #444; font-size: 0.8rem;'>AXOM GLOBAL SECURE ACCESS // ENCRYPTED SESSION</p>", unsafe_allow_html=True)
