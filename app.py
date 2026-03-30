import streamlit as st
import time
import datetime
import io
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# --- 1. NEURAL UI CONFIGURATION ---
st.set_page_config(page_title="BITs.edu | Neural Senior Examiner", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    .bits-card {
        background: linear-gradient(145deg, #0f0f0f, #151515);
        border: 1px solid #222;
        padding: 25px;
        border-radius: 8px;
        border-left: 5px solid #00E5FF;
        margin-bottom: 25px;
    }
    section[data-testid="stSidebar"] { background-color: #000 !important; border-right: 1px solid #222; }
    .stButton>button {
        background: linear-gradient(90deg, #00E5FF, #0099FF) !important;
        color: #000 !important;
        font-weight: 800 !important;
        border: none !important;
        width: 100%;
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
    
    red_color = (255, 75, 75, 230)
    teal_color = (0, 229, 255, 230)
    
    for m in marks:
        x, y = int(m['x']), int(m['y'])
        color = teal_color if m['correct'] else red_color
        
        if m['correct']: # BITs Tick
            draw.line([(x-20, y), (x, y+20), (x+40, y-30)], fill=color, width=10)
        else: # BITs Cross
            draw.line([(x-25, y-25), (x+25, y+25)], fill=color, width=10)
            draw.line([(x+25, y-25), (x-25, y+25)], fill=color, width=10)
        
        if m.get('note'):
            draw.rectangle([x+60, y-20, x+450, y+40], fill=(0,0,0,180), outline=color, width=2)
            draw.text((x+75, y-5), m['note'], fill=(255,255,255))

    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 3. SESSION STATE ---
if 'usage_cost' not in st.session_state: st.session_state.usage_cost = 0.0
if 'current_eval' not in st.session_state: st.session_state.current_eval = None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#00E5FF;'>BITs.edu</h1>", unsafe_allow_html=True)
    st.caption("Next Step Future | Infrastructure")
    st.divider()
    menu = st.selectbox("INTERFACE", ["VISION GRADER", "REVISION HUB", "BILLING"])
    st.divider()
    st.write(f"**Session Cost:** `${st.session_state.usage_cost:.4f}`")
    st.progress(min(st.session_state.usage_cost / 0.50, 1.0))

# --- 5. VISION GRADER ---
if menu == "VISION GRADER":
    st.subheader("FULL-SCRIPT NEURAL SCAN")
    
    c1, c2 = st.columns(2)
    board = c1.selectbox("EXAM BOARD", ["Cambridge IGCSE", "Edexcel", "AQA", "SAT"])
    subject = c2.text_input("SUBJECT", "English 0500 P1")

    # FILE UPLOADERS
    up_script = st.file_uploader("UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
    up_scheme = st.file_uploader("UPLOAD MARKING SCHEME (OPTIONAL PDF)", type=['pdf'])

    if up_script and st.button("EXECUTE CENSORA ANALYSIS"):
        if st.session_state.usage_cost >= 0.50:
            st.error("Daily Budget Limit Reached ($0.50). Upgrade to BITs Pro.")
        else:
            with st.status("Senior Examiner is cross-referencing your work...", expanded=True):
                # 1. Convert Script
                pages = convert_pdf_to_images(up_script.read())
                
                # 2. Logic Check: Marking Scheme
                has_scheme = "ENABLED" if up_scheme else "GENERAL KNOWLEDGE"
                st.write(f"✓ Context Source: {has_scheme}")
                
                # 3. Simulate Gemini API Response
                time.sleep(2.5)
                st.session_state.usage_cost += 0.007
                
                # Mock Result based on Scheme Presence
                eval_data = {
                    "score": 82 if up_scheme else 75,
                    "summary": "Marking scheme utilized for precise band-score alignment." if up_scheme else "General assessment applied based on IGCSE standards.",
                    "marks": [
                        {"page": 0, "x": 300, "y": 250, "correct": True, "note": "Clear alignment with MS."},
                        {"page": 0, "x": 400, "y": 600, "correct": False, "note": "Point omitted from MS."}
                    ]
                }
                st.session_state.current_eval = {"data": eval_data, "images": pages}
                st.balloons()

    if st.session_state.current_eval:
        data = st.session_state.current_eval['data']
        st.markdown(f"""<div class="bits-card"><h2 style="color:#00E5FF;">FINAL MARK: {data['score']}%</h2><p>{data['summary']}</p></div>""", unsafe_allow_html=True)
        
        for i, img in enumerate(st.session_state.current_eval['images']):
            p_marks = [m for m in data['marks'] if m['page'] == i]
            marked_img = draw_bits_marks(img, p_marks)
            st.image(marked_img, caption=f"BITs Marked Page {i+1}", use_column_width=True)

# --- 6. REMAINING PAGES ---
elif menu == "REVISION HUB":
    st.title("🧠 Neural Remediation")
    st.info("Revision pathways will appear here after your first neural scan.")

elif menu == "BILLING":
    st.title("💸 Infrastructure Billing")
    st.write(f"Current Daily Usage: **${st.session_state.usage_cost:.4f} / $0.50**")
    st.button("Upgrade to Pro (Unlimited Credits)")
