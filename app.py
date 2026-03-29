import streamlit as st
import time
import json
import random
import datetime
import io
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# --- 1. SYSTEM UI ENGINE ---
st.set_page_config(page_title="AXOM | Neural Infrastructure", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    .summary-card {
        background: #0A0A0A; border: 1px solid #1A1A1A; padding: 25px;
        border-radius: 4px; border-top: 4px solid #00E5FF; margin: 20px 0;
    }
    
    /* Sidebar & Inputs */
    section[data-testid="stSidebar"] { background-color: #000 !important; border-right: 1px solid #111; }
    .stTextInput>div>div>input { background-color: #0A0A0A !important; border: 1px solid #222 !important; color: #00E5FF !important; }
    
    /* Buttons */
    .stButton>button, .stDownloadButton>button {
        background: #00E5FF !important; color: #000 !important;
        font-weight: 800 !important; border-radius: 2px !important;
        height: 45px; border: none !important; width: 100%;
    }
    .stDownloadButton>button { background: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MULTI-PAGE MARKING ENGINE ---
def draw_professional_marks(img, marks):
    """Applies examiner annotations to a single page image."""
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    try: font = ImageFont.truetype("arial.ttf", 26)
    except: font = ImageFont.load_default()

    for m in marks:
        x, y = int(m['x']), int(m['y'])
        color = (46, 125, 50, 255) if m['correct'] else (198, 40, 40, 255)
        
        # Tick or Cross
        sz = 35
        if m['correct']:
            draw.line([(x-sz, y), (x, y+sz), (x+sz, y-sz)], fill=color, width=12)
        else:
            draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
            draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
        
        # Side-Note Box
        note_text = m.get('note', '')
        if note_text:
            draw.rectangle([x + 60, y - 25, x + 500, y + 50], fill=(15, 15, 15, 230), outline=color, width=2)
            draw.text((x + 75, y - 10), note_text, fill=(255, 255, 255, 255), font=font)

    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 3. SESSION STATE ---
if 'history' not in st.session_state: st.session_state.history = []
if 'current_eval' not in st.session_state: st.session_state.current_eval = None

# --- 4. MAIN INTERFACE ---
with st.sidebar:
    st.markdown("<h2 style='color:#00E5FF'>AXOM CORE</h2>", unsafe_allow_html=True)
    menu = st.radio("INTERFACE", ["VISION GRADER", "REVISION HUB", "NEURAL ARCHIVE"])

if menu == "VISION GRADER":
    st.subheader("FULL-SCRIPT NEURAL SCAN")
    c1, c2 = st.columns(2)
    board = c1.text_input("EXAM BOARD", "Cambridge IGCSE")
    subject = c2.text_input("SUBJECT", "English Literature P2")
    
    up_s = st.file_uploader("UPLOAD FULL STUDENT SCRIPT (PDF)", type=['pdf'])
    up_m = st.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])

    if up_s and st.button("EXECUTE FULL SCRIPT ANALYSIS"):
        with st.status("Senior Examiner AI is processing all pages..."):
            # 1. Convert ALL PDF pages to images
            all_pages = convert_from_bytes(up_s.read())
            num_pages = len(all_pages)
            st.write(f"Detected {num_pages} pages. Analyzing sequence...")
            time.sleep(2)
            
            # 2. MOCK AI DATA (Simulated result for the entire PDF)
            # In production, Gemini would return a list of marks for EACH page index.
            eval_data = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "board": board, "subject": subject, "score": 84,
                "marks": [
                    {"page": 0, "x": 300, "y": 200, "correct": True, "note": "Strong thesis statement."},
                    {"page": 1, "x": 400, "y": 450, "correct": False, "note": "Analysis lacks textual evidence."},
                    {"page": 2, "x": 250, "y": 300, "correct": True, "note": "Sophisticated vocabulary choice."}
                ],
                "summary": f"Complete {num_pages}-page review finalized. The student shows excellent structural coherence. However, Page 2 indicates a drop in critical analysis depth.",
                "gaps": [{"topic": "Evidence Integration", "issue": "Missing citations on Page 2."}]
            }
            st.session_state.current_eval = {"data": eval_data, "images": all_pages}
            st.session_state.history.append(st.session_state.current_eval)

    if st.session_state.current_eval:
        st.write(f"### FINAL MARK: {st.session_state.current_eval['data']['score']}%")
        
        # Render Every Page in the PDF
        for i, img in enumerate(st.session_state.current_eval['images']):
            # Filter marks for this specific page
            p_marks = [m for m in st.session_state.current_eval['data']['marks'] if m['page'] == i]
            marked_img = draw_professional_marks(img, p_marks)
            
            st.image(marked_img, caption=f"SCRIPT PAGE {i+1} OF {len(st.session_state.current_eval['images'])}", use_column_width=True)
            st.divider()

        # Final Summary at the very end
        st.markdown(f"""
            <div class="summary-card">
                <h4 style="color:#00E5FF; margin-top:0;">OVERALL EXAMINER FEEDBACK</h4>
                <p style="color:#DDD;">{st.session_state.current_eval['data']['summary']}</p>
            </div>
        """, unsafe_allow_html=True)

elif menu == "REVISION HUB":
    st.subheader("NEURAL REMEDIATION")
    if st.session_state.current_eval:
        for gap in st.session_state.current_eval['data']['gaps']:
            st.info(f"**TOPIC:** {gap['topic']}\n\n**ISSUE:** {gap['issue']}")
