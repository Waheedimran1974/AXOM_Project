import streamlit as st
import google.generativeai as genai
import re
import io
import base64
import time
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. CORE CONFIG & META-DESIGN
# ==========================================
st.set_page_config(page_title="AXOM // GLOBAL", layout="wide", initial_sidebar_state="collapsed")

def inject_cyber_styles():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 100%); color: #f8fafc; }
        
        /* Remove the 'Hollow Block' / Border from Tabs */
        [data-testid="stExpander"], [data-testid="stVerticalBlock"] > div { border: none !important; }
        .stTabs [data-baseweb="tab-panel"] { border: none !important; padding-top: 20px !important; }
        
        /* Auth Card */
        .auth-container {
            max-width: 450px; margin: 60px auto; padding: 40px;
            background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(20px);
            border: 1px solid rgba(212, 175, 55, 0.2); border-radius: 8px;
            text-align: center; box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }
        
        .brand-logo { 
            font-size: 4rem; font-weight: 900; color: #D4AF37; 
            letter-spacing: 15px; text-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
            margin-bottom: 0px;
        }

        /* Glowing Cyber Buttons */
        .stButton>button {
            width: 100%; background: transparent !important; color: #D4AF37 !important;
            border: 1px solid #D4AF37 !important; transition: 0.4s;
            text-transform: uppercase; letter-spacing: 2px; font-weight: bold;
        }
        .stButton>button:hover {
            background: #D4AF37 !important; color: #020617 !important;
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.5);
        }

        /* Scrollable Paper Container */
        .zoom-container {
            width:100%; height:800px; overflow:scroll; 
            border: 1px solid rgba(212, 175, 55, 0.3); background: #000;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. THE HANDWRITING ENGINE
# ==========================================
def draw_neural_marks(draw, coords, note, w, h, cat):
    colors = {"error": "#ff3131", "correct": "#39ff14", "info": "#1f51ff"}
    pen_color = colors.get(cat.lower(), "#ff3131")
    
    ymin, xmin, ymax, xmax = coords
    l, t, r, b = xmin*w/1000, ymin*h/1000, xmax*w/1000, ymax*h/1000

    if cat.lower() == "correct":
        draw.line([l, (t+b)/2, (l+r)/2, b, r, t-20], fill=pen_color, width=10)
    else:
        draw.rectangle([l, t, r, b], outline=pen_color, width=6)

    # LOAD IBRAHIM HANDWRITING
    try:
        font = ImageFont.truetype("ibrahim_handwriting.ttf", 55)
    except:
        font = ImageFont.load_default()

    # Draw Text with slight shadow for 'Ink' feel
    draw.text((r + 12, t + 2), note, fill="#000", font=font)
    draw.text((r + 10, t), note, fill=pen_color, font=font)

# ==========================================
# 3. ROUTING & STATE
# ==========================================
if 'auth' not in st.session_state: st.session_state.auth = False
if 'page' not in st.session_state: st.session_state.page = "GATE"

inject_cyber_styles()

if not st.session_state.auth:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="brand-logo">AXOM</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-size: 0.8rem; margin-bottom: 30px;">// SECURE NEURAL LINK v3.1 //</p>', unsafe_allow_html=True)
        
        # Cleaner SSO Buttons
        if st.button("SIGN IN WITH GOOGLE"):
            st.session_state.auth = True
            st.rerun()
        st.write("<p style='font-size: 0.7rem; color: #444;'>OR</p>", unsafe_allow_html=True)
        if st.button("SIGN IN WITH MICROSOFT"):
            st.session_state.auth = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. COMMAND CENTER (POST-LOGIN)
# ==========================================
# Glass Header
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 20px; border-bottom: 1px solid rgba(212, 175, 55, 0.2);">
        <h2 style="color: #D4AF37; margin:0; letter-spacing: 5px;">AXOM // CMD</h2>
        <div style="color: #39ff14; font-size: 0.8rem;">● SECURE_SESSION_ACTIVE</div>
    </div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h3 style='color: #D4AF37;'>PROTOCOLS</h3>", unsafe_allow_html=True)
    if st.button("PAPER CHECKER"): st.session_state.page = "CHECKER"
    if st.button("AI MENTOR"): st.session_state.page = "AI"
    st.divider()
    if st.button("TERMINATE"):
        st.session_state.auth = False
        st.rerun()

if st.session_state.page == "CHECKER":
    st.markdown("<h3 style='color: #D4AF37;'>NEURAL MARKING ENGINE</h3>", unsafe_allow_html=True)
    
    file = st.file_uploader("UPLOAD SCRIPT", type=['pdf', 'jpg', 'png'])
    if file:
        res = st.select_slider("RENDER RESOLUTION", options=["SD", "HD", "4K"])
        px_w = {"SD": 900, "HD": 1500, "4K": 2500}[res]
        
        if st.button("EXECUTE MARKING"):
            with st.spinner("AI EXAMINER ANALYZING PIXELS..."):
                # File Processing
                if file.type == "application/pdf":
                    img = convert_from_bytes(file.getvalue())[0].convert("RGB")
                else:
                    img = Image.open(file).convert("RGB")
                
                w, h = img.size
                draw = ImageDraw.Draw(img)

                # AI Logic
                model = genai.GenerativeModel('gemini-2.0-flash')
                resp = model.generate_content(["Analyze and mark this exam paper. Format: [ymin, xmin, ymax, xmax] | category | note", img])
                
                # Marking
                for line in resp.text.split('\n'):
                    if '|' in line:
                        match = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', line)
                        if match:
                            coords = [int(x) for x in match.groups()]
                            draw_neural_marks(draw, coords, line.split('|')[2].strip(), w, h, line.split('|')[1].strip())

                # Display
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                st.markdown(f'<div class="zoom-container"><img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" style="width:{px_w}px;"></div>', unsafe_allow_html=True)
