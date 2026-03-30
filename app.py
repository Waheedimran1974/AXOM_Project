import streamlit as st
import time
import datetime
import io
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# --- 1. NEURAL UI CONFIGURATION ---
st.set_page_config(page_title="BITs.edu | Neural Senior Examiner", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for the "Addictive" Premium Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* Premium Card Styling */
    .bits-card {
        background: linear-gradient(145deg, #0f0f0f, #151515);
        border: 1px solid #222;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #00E5FF;
        margin-bottom: 20px;
    }
    
    /* The "Censora" Red Pen Font Simulation */
    .examiner-note {
        font-family: 'JetBrains Mono', monospace;
        color: #FF4B4B;
        font-weight: bold;
    }

    /* Sidebar Branding */
    section[data-testid="stSidebar"] { background-color: #000 !important; border-right: 1px solid #222; }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #00E5FF, #0099FF) !important;
        color: #000 !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none !important;
        transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0px 0px 15px #00E5FF; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
@st.cache_data
def convert_pdf_to_images(pdf_bytes):
    return convert_from_bytes(pdf_bytes)

def draw_bits_marks(img, marks):
    """The BITs 'Red Pen' rendering engine."""
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    # Red-Pen Style Settings
    red_color = (255, 75, 75, 230)
    green_color = (0, 229, 255, 230) # Neon Teal for BITs style
    
    for m in marks:
        x, y = int(m['x']), int(m['y'])
        color = green_color if m['correct'] else red_color
        
        # Draw Symbol
        if m['correct']: # BITs Tick
            draw.line([(x-20, y), (x, y+20), (x+40, y-30)], fill=color, width=10)
        else: # BITs Cross
            draw.line([(x-25, y-25), (x+25, y+25)], fill=color, width=10)
            draw.line([(x+25, y-25), (x-25, y+25)], fill=color, width=10)
        
        # Examiner Side-Note
        if m.get('note'):
            draw.rectangle([x+60, y-20, x+450, y+40], fill=(0,0,0,180), outline=color, width=2)
            draw.text((x+75, y-5), m['note'], fill=(255,255,255))

    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 3. SESSION STATE & BUDGET SHIELD ---
if 'history' not in st.session_state: st.session_state.history = []
if 'usage_cost' not in st.session_state: st.session_state.usage_cost = 0.0
if 'current_eval' not in st.session_state: st.session_state.current_eval = None

# --- 4. NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color:#00E5FF; margin-bottom:0;'>BITs.edu</h1>", unsafe_allow_html=True)
    st.caption("Next Step Future | Neural Infrastructure")
    st.divider()
    
    menu = st.selectbox("DASHBOARD", ["VISION GRADER", "REVISION HUB", "SETTINGS & BILLING"])
    
    st.divider()
    st.write(f"**Session Cost:** `${st.session_state.usage_cost:.4f}`")
    st.progress(min(st.session_state.usage_cost / 0.50, 1.0), text="Daily Budget Used")

# --- 5. MAIN LOGIC ---
if menu == "VISION GRADER":
    st.title("🚀 Neural Script Scan")
    
    col1, col2, col3 = st.columns([1,1,1])
    board = col1.selectbox("EXAM BOARD", ["Cambridge IGCSE", "Edexcel", "AQA", "SAT"])
    rigor = col2.select_slider("MARKING RIGOR", options=["Supportive", "Standard", "Harsh Examiner"])
    subject = col3.text_input("SUBJECT CODE", "English 0500")

    up_s = st.file_uploader("UPLOAD SCRIPT (PDF)", type=['pdf'])

    if up_s:
        if st.button("EXECUTE CENSORA ENGINE"):
            if st.session_state.usage_cost >= 0.50:
                st.error("Budget Cap Reached! ($0.50). Upgrade to BITs Pro to continue.")
            else:
                with st.status("Censora AI is analyzing pages...", expanded=True):
                    # Convert PDF
                    pages = convert_pdf_to_images(up_s.read())
                    st.write(f"✓ Scanning {len(pages)} pages...")
                    
                    # Simulate Gemini 2.0 API Logic
                    time.sleep(2) 
                    st.session_state.usage_cost += 0.005 # Simulated API cost per call
                    
                    # Mock Result
                    eval_data = {
                        "score": 78,
                        "grade": "A",
                        "summary": "Strong analytical voice. However, Page 2 lacks direct textual evidence which dropped the band score from 9 to 7.",
                        "marks": [
                            {"page": 0, "x": 200, "y": 300, "correct": True, "note": "Excellent hook!"},
                            {"page": 1, "x": 150, "y": 500, "correct": False, "note": "Unsubstantiated claim."}
                        ],
                        "gaps": ["Evidence Integration", "Structural Transitions"]
                    }
                    
                    st.session_state.current_eval = {"data": eval_data, "images": pages}
                    st.balloons()

    if st.session_state.current_eval:
        data = st.session_state.current_eval['data']
        
        # Display Score Card
        st.markdown(f"""
            <div class="bits-card">
                <h2 style="color:#00E5FF; margin:0;">RESULT: {data['score']}% (Grade {data['grade']})</h2>
                <p style="margin-top:10px;">{data['summary']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Display Marked Pages
        for i, img in enumerate(st.session_state.current_eval['images']):
            p_marks = [m for m in data['marks'] if m['page'] == i]
            marked_img = draw_bits_marks(img, p_marks)
            st.image(marked_img, caption=f"Censora Marked Page {i+1}", use_column_width=True)

elif menu == "REVISION HUB":
    st.title("🧠 Neural Remediation")
    if not st.session_state.current_eval:
        st.warning("Please upload a script in Vision Grader first.")
    else:
        st.write("### Targeted Fixes for Your Last Attempt")
        for gap in st.session_state.current_eval['data']['gaps']:
            with st.expander(f"REMEDY: {gap}"):
                st.write("BITs AI suggests focusing on connective adverbs here. Practice Exercise 4.1 recommended.")
        
        if st.button("Generate Revision Plan"):
            st.write("Drafting a 3-day plan based on your weaknesses...")
            time.sleep(1)
            st.success("Plan Ready: Focus on 'Evidence Integration' tomorrow at 4 PM.")

elif menu == "SETTINGS & BILLING":
    st.title("⚙️ Infrastructure Settings")
    st.write("---")
    st.write("**Account Tier:** Freemium Beta")
    st.write("**Daily Limit:** $0.50")
    if st.button("UNLOCK BITS PRO ($10.00/mo)"):
        st.toast("Redirecting to Secure Payment Portal...")
