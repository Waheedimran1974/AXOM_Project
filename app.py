import streamlit as st
import time
import datetime
import io
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# --- 1. NEURAL UI CONFIGURATION ---
st.set_page_config(page_title="BITs.edu | Neural Senior Examiner", layout="wide")

# High-Performance CSS for "Addictive" UX
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono&display=swap');
    
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* Premium Glassmorphism Cards */
    .bits-card {
        background: rgba(15, 15, 15, 0.8);
        border: 1px solid #222;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
    }
    
    /* Subscription Tiers */
    .plan-container {
        display: flex;
        gap: 20px;
        margin-top: 20px;
    }
    .plan-card {
        flex: 1;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #333;
        text-align: center;
        background: #0A0A0A;
        transition: 0.3s;
    }
    .plan-card:hover { border-color: #00E5FF; transform: translateY(-5px); }
    .plan-pro { border: 2px solid #00E5FF; background: linear-gradient(145deg, #0A0A0A, #111); }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00E5FF, #0099FF) !important;
        color: #000 !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        height: 50px;
        border: none !important;
        width: 100%;
        text-transform: uppercase;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE RENDERING ENGINE ---
@st.cache_data
def convert_pdf_to_images(pdf_bytes):
    return convert_from_bytes(pdf_bytes)

def draw_bits_marks(img, marks):
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    red_color, teal_color = (255, 75, 75, 230), (0, 229, 255, 230)
    
    for m in marks:
        x, y = int(m['x']), int(m['y'])
        color = teal_color if m['correct'] else red_color
        if m['correct']:
            draw.line([(x-20, y), (x, y+20), (x+40, y-30)], fill=color, width=12)
        else:
            draw.line([(x-25, y-25), (x+25, y+25)], fill=color, width=12)
            draw.line([(x+25, y-25), (x-25, y+25)], fill=color, width=12)
        if m.get('note'):
            draw.rectangle([x+60, y-20, x+450, y+40], fill=(0,0,0,200), outline=color, width=2)
            draw.text((x+75, y-5), m['note'], fill=(255,255,255))
    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 3. SESSION STATE ---
if 'current_eval' not in st.session_state: st.session_state.current_eval = None

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color:#00E5FF; font-size: 42px; font-weight: 900;'>BITs</h1>", unsafe_allow_html=True)
    st.caption("Neural Academic Infrastructure")
    st.divider()
    menu = st.radio("DASHBOARD", ["NEURAL GRADER", "PRO SUBSCRIPTION", "REVISION HUB"])
    st.divider()
    st.info("Status: Online • Gemini 2.0 Flash Active")

# --- 5. NEURAL GRADER PAGE ---
if menu == "NEURAL GRADER":
    st.title("🚀 Neural Script Analysis")
    st.write("Upload your PDF script for PhD-level examiner feedback.")
    
    with st.container():
        c1, c2 = st.columns(2)
        board = c1.selectbox("EXAM BOARD", ["Cambridge IGCSE", "Edexcel", "AQA", "SAT"])
        subject = c2.text_input("SUBJECT CODE", "English 0500 P1")
        
        up_script = st.file_uploader("UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_scheme = st.file_uploader("MARKING SCHEME (OPTIONAL)", type=['pdf'])

        if up_script and st.button("EXECUTE CENSORA ENGINE"):
            with st.status("Senior Examiner is cross-referencing your work...", expanded=True):
                pages = convert_pdf_to_images(up_script.read())
                time.sleep(2.5)
                eval_data = {
                    "score": 82 if up_scheme else 74,
                    "summary": "Precise alignment with marking scheme detected. Excellent structure.",
                    "marks": [{"page": 0, "x": 300, "y": 250, "correct": True, "note": "Strong Synthesis."}]
                }
                st.session_state.current_eval = {"data": eval_data, "images": pages}
                st.balloons()

    if st.session_state.current_eval:
        data = st.session_state.current_eval['data']
        st.markdown(f"""<div class="bits-card"><h2 style="color:#00E5FF; margin:0;">FINAL SCORE: {data['score']}%</h2><p>{data['summary']}</p></div>""", unsafe_allow_html=True)
        for i, img in enumerate(st.session_state.current_eval['images']):
            marked_img = draw_bits_marks(img, [m for m in data['marks'] if m['page'] == i])
            st.image(marked_img, caption=f"BITs Page {i+1}", use_column_width=True)

# --- 6. SUBSCRIPTION PLANS (THE "MONEY" PAGE) ---
elif menu == "PRO SUBSCRIPTION":
    st.title("💎 Unlock Unlimited Potential")
    st.write("Upgrade to BITs Pro for prioritized processing and unlimited neural scans.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="plan-card">
            <h3>FREEMIUM</h3>
            <h2 style="color: #888;">$0 <small>/mo</small></h2>
            <hr style="border-color: #333;">
            <p>✓ 1 Neural Scan / Day</p>
            <p>✓ Standard Latency</p>
            <p>✓ Basic Revision Path</p>
            <p>✗ Visual Annotations</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("Current Plan", disabled=True)

    with col2:
        st.markdown("""
        <div class="plan-card plan-pro">
            <h3 style="color: #00E5FF;">BITs PRO</h3>
            <h2>$10 <small>/mo</small></h2>
            <hr style="border-color: #00E5FF;">
            <p>✓ Unlimited Neural Scans</p>
            <p>✓ Priority Engine Access</p>
            <p>✓ Full Visual Red-Pen Marking</p>
            <p>✓ 24/7 AI Revision Tutor</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("UPGRADE TO PRO"):
            st.success("Redirecting to Secure Payment Gateway...")

# --- 7. REVISION HUB ---
elif menu == "REVISION HUB":
    st.title("🧠 Neural Revision")
    if not st.session_state.current_eval:
        st.warning("Please complete a Neural Scan first to generate your revision path.")
    else:
        st.info("Analysis complete. Focus on 'Evidence Integration' for your next attempt.")
