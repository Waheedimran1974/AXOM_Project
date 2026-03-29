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
    
    /* Examiner Summary Styling */
    .summary-card {
        background: #0A0A0A; border: 1px solid #1A1A1A; padding: 25px;
        border-radius: 4px; border-top: 4px solid #00E5FF; margin-top: 20px;
    }
    .auth-card { background: rgba(15, 15, 15, 0.95); border: 1px solid #1A1A1A; padding: 50px; border-radius: 8px; text-align: center; max-width: 500px; margin: auto; }
    .stButton>button, .stDownloadButton>button { background: #00E5FF !important; color: #000 !important; font-weight: 800 !important; border-radius: 2px !important; height: 45px; border: none !important; width: 100%; }
    .stDownloadButton>button { background: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ADVANCED MARKING ENGINE (Ticks, Crosses & Notes) ---
def draw_professional_marks(img, marks):
    """Draws ticks/crosses and examiner side-notes directly on the script."""
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    # Attempt to load a clean font, fallback to default
    try: font = ImageFont.truetype("arial.ttf", 24)
    except: font = ImageFont.load_default()

    for m in marks:
        x, y = int(m['x']), int(m['y'])
        is_correct = m['correct']
        color = (46, 125, 50, 255) if is_correct else (198, 40, 40, 255)
        
        # 1. Draw Tick or Cross
        sz = 30
        if is_correct:
            draw.line([(x-sz, y), (x, y+sz), (x+sz, y-sz)], fill=color, width=12)
        else:
            draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
            draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
        
        # 2. Draw Examiner Side-Note Box
        note_text = m.get('note', '')
        if note_text:
            # Note background box
            box_coords = [x + 50, y - 20, x + 450, y + 40]
            draw.rectangle(box_coords, fill=(20, 20, 20, 220), outline=color, width=2)
            draw.text((x + 65, y - 10), note_text, fill=(255, 255, 255, 255), font=font)

    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 3. THE MAIN APP LOGIC ---
if 'step' not in st.session_state: st.session_state.step = "active" # Bypassing login for code preview
if 'history' not in st.session_state: st.session_state.history = []
if 'current_eval' not in st.session_state: st.session_state.current_eval = None

if st.session_state.step == "active":
    with st.sidebar:
        st.markdown("<h2 style='color:#00E5FF'>AXOM CORE</h2>", unsafe_allow_html=True)
        menu = st.radio("INTERFACE", ["VISION GRADER", "REVISION HUB", "NEURAL ARCHIVE"])

    if menu == "VISION GRADER":
        st.subheader("NEURAL SCANNER")
        c1, c2 = st.columns(2)
        board = c1.text_input("EXAM BOARD", "Cambridge IGCSE")
        subject = c2.text_input("SUBJECT", "Physics P4")
        
        up_s = st.file_uploader("UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_m = st.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])

        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.status("Senior Examiner AI is reviewing logic..."):
                images = convert_from_bytes(up_s.read())
                time.sleep(2)
                
                # MOCK AI DATA: In production, this comes from Gemini 2.5 Flash
                eval_data = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "board": board, "subject": subject, "score": 78,
                    "marks": [
                        {"page": 0, "x": 300, "y": 250, "correct": True, "note": "Excellent use of SI units."},
                        {"page": 0, "x": 350, "y": 600, "correct": False, "note": "Logic error: Formula inversion."},
                        {"page": 0, "x": 400, "y": 850, "correct": True, "note": "Correct derivation."}
                    ],
                    "summary": "The student demonstrates a strong grasp of theoretical concepts but struggles with complex algebraic manipulation. Focus on rearranging equations before substituting values.",
                    "gaps": [{"topic": "Algebraic Physics", "issue": "Rearrangement errors in 3-mark questions."}]
                }
                st.session_state.current_eval = {"data": eval_data, "images": images}
                st.session_state.history.append(st.session_state.current_eval)

        if st.session_state.current_eval:
            # 1. Header & PDF Download
            c_res, c_dl = st.columns([3, 1])
            c_res.write(f"### FINAL MARK: {st.session_state.current_eval['data']['score']}%")
            
            # 2. Render Marked Pages
            for i, img in enumerate(st.session_state.current_eval['images']):
                p_marks = [m for m in st.session_state.current_eval['data']['marks'] if m['page'] == i]
                marked_img = draw_professional_marks(img, p_marks)
                st.image(marked_img, caption=f"MARKED PAGE {i+1}", use_column_width=True)
            
            # 3. EXAMINER SUMMARY (The "Pro" Review)
            st.markdown(f"""
                <div class="summary-card">
                    <h4 style="color:#00E5FF; margin-top:0;">EXAMINER'S FINAL REVIEW</h4>
                    <p style="color:#DDD; line-height:1.6;">{st.session_state.current_eval['data']['summary']}</p>
                    <hr style="border:0.5px solid #222;">
                    <p style="font-size:0.8rem; color:#666;">Verified by AXOM Neural Infrastructure v7.0</p>
                </div>
            """, unsafe_allow_html=True)

    elif menu == "REVISION HUB":
        st.subheader("NEURAL REMEDIATION")
        if st.session_state.current_eval:
            for gap in st.session_state.current_eval['data']['gaps']:
                st.info(f"**TOPIC:** {gap['topic']}\n\n**ISSUE:** {gap['issue']}")
        else: st.warning("No data available. Run a scan.")
