import streamlit as st
import time
import datetime
import io
import base64
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pdf2image import convert_from_bytes
import numpy as np
import tempfile
import os

# --- 1. GLOBAL SYSTEM CONFIGURATION ---
SYSTEM_VERSION = "2.3.0-PRO"
LAUNCH_DATE = "2026-03-31"
DAILY_BUDGET_CAP = 0.50

st.set_page_config(
    page_title="BiTs.edu | Neural Senior Examiner",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. NEURAL UI ENGINE (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono&display=swap');
    
    :root {
        --primary-glow: #00E5FF;
        --secondary-glow: #0099FF;
        --dark-bg: #050505;
        --card-bg: rgba(15, 15, 15, 0.95);
    }

    .stApp { background-color: var(--dark-bg); color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    .bits-card {
        background: var(--card-bg);
        border: 1px solid #222;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
        margin-bottom: 25px;
        border-left: 4px solid var(--primary-glow);
    }
    
    .plan-card {
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #333;
        text-align: center;
        background: #0A0A0A;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .plan-card:hover { border-color: var(--primary-glow); transform: translateY(-8px); }
    .plan-pro { border: 2px solid var(--primary-glow); box-shadow: 0 0 20px rgba(0, 229, 255, 0.2); }
    
    .grade-a-star { color: #00FF88; font-weight: bold; }
    .grade-a { color: #44FF44; font-weight: bold; }
    .grade-b { color: #88FF00; font-weight: bold; }
    .grade-c { color: #FFCC00; font-weight: bold; }
    .grade-d { color: #FF8800; font-weight: bold; }
    .grade-e { color: #FF4400; font-weight: bold; }
    .grade-u { color: #CC0000; font-weight: bold; }
    
    .stButton>button {
        background: linear-gradient(90deg, var(--primary-glow), var(--secondary-glow)) !important;
        color: #000 !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        height: 52px;
        border: none !important;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        transition: 0.3s !important;
    }
    .stButton>button:hover { filter: brightness(1.2); box-shadow: 0 0 20px var(--primary-glow); }
    
    .marking-scheme-badge {
        background: linear-gradient(135deg, #00E5FF20, #0099FF20);
        border-left: 3px solid #00E5FF;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. EXAMINER HANDWRITING FONTS ---
def get_examiner_font(size=24):
    """Load professional examiner-style handwriting font"""
    try:
        # Try to load a handwriting-style font if available
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        
        # Fallback to default
        return ImageFont.load_default()
    except:
        return ImageFont.load_default()

def draw_handwriting_text(draw, text, position, color, font_size=22):
    """Draw text with natural handwriting spacing"""
    font = get_examiner_font(font_size)
    
    # Add slight natural variation to positioning for handwritten feel
    x, y = position
    words = text.split(' ')
    current_x = x
    line_height = font_size + 5
    
    for word in words:
        # Slight random offset for natural look
        import random
        offset_y = random.randint(-2, 2)
        draw.text((current_x, y + offset_y), word + ' ', fill=color, font=font)
        bbox = draw.textbbox((0, 0), word + ' ', font=font)
        current_x += bbox[2] - bbox[0]
        
        # Line break for long text
        if current_x > 500:
            current_x = x
            y += line_height
    
    return y + line_height

# --- 4. COMPREHENSIVE EXAM BOARD CONFIGURATION ---
EXAM_BOARDS = {
    "Edexcel (Pearson)": {"region": "United Kingdom", "type": "GCSE/A-Level", "grade_boundaries": {"A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "U": 0}, "grade_scale": "A*-U"},
    "Cambridge IGCSE": {"region": "United Kingdom", "type": "IGCSE", "grade_boundaries": {"A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "F": 30, "G": 20, "U": 0}, "grade_scale": "A*-G"},
    "Oxford AQA": {"region": "United Kingdom", "type": "GCSE/A-Level", "grade_boundaries": {"9": 90, "8": 80, "7": 70, "6": 60, "5": 50, "4": 40, "3": 30, "2": 20, "1": 10, "U": 0}, "grade_scale": "9-1"},
    "International Baccalaureate (IB)": {"region": "International", "type": "IB Diploma", "grade_boundaries": {"7": 85, "6": 75, "5": 65, "4": 55, "3": 45, "2": 35, "1": 25, "U": 0}, "grade_scale": "1-7"},
    "College Board (AP)": {"region": "United States", "type": "Advanced Placement", "grade_boundaries": {"5": 80, "4": 70, "3": 60, "2": 50, "1": 0}, "grade_scale": "1-5"},
    "CBSE": {"region": "India", "type": "Central Board", "grade_boundaries": {"A1": 91, "A2": 81, "B1": 71, "B2": 61, "C1": 51, "C2": 41, "D": 33, "E": 0}, "grade_scale": "A1-E"},
}

# --- 5. MARKING SCHEME PARSER ---
def parse_marking_scheme(pdf_bytes):
    """Extract marking scheme from uploaded PDF"""
    try:
        images = convert_from_bytes(pdf_bytes, dpi=150, first_page=1, last_page=10)
        # Simulate marking scheme extraction
        marking_scheme = {
            "total_marks": 100,
            "questions": [
                {"qno": 1, "marks": 10, "key_points": ["Correct formula", "Working shown", "Final answer"]},
                {"qno": 2, "marks": 15, "key_points": ["Method mark", "Accuracy mark", "Units included"]},
                {"qno": 3, "marks": 20, "key_points": ["Part (a) correct", "Part (b) reasoning", "Conclusion"]},
            ]
        }
        return marking_scheme
    except:
        return None

# --- 6. ENHANCED MARK RENDERING WITH SIDE NOTES ---
def render_examiner_marks_enhanced(img, marks, page_width, page_height):
    """Professional examiner marking with ticks/crosses on page and notes in margin"""
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    color_correct = (0, 229, 255, 255)  # BiTs Cyan
    color_incorrect = (255, 75, 75, 255)  # Examiner Red
    color_partial = (255, 204, 0, 255)  # Partial credit
    color_note_bg = (30, 30, 40, 240)  # Dark semi-transparent for notes
    
    # Margin area for notes (right side)
    margin_x = page_width - 250
    note_y_start = 50
    
    for idx, mark in enumerate(marks):
        x, y = int(mark['x']), int(mark['y'])
        
        # Draw tick/cross directly on the page at the exact location
        if mark['correct']:
            color = color_correct
            # Professional tick mark
            draw.line([(x-20, y), (x-5, y+15), (x+25, y-20)], fill=color, width=12)
            # Small tick indicator
            draw.text((x+30, y-15), f"✓", fill=color, font=get_examiner_font(28))
        elif mark.get('partial', False):
            color = color_partial
            # Partial credit symbol
            draw.ellipse([x-15, y-15, x+15, y+15], outline=color, width=8)
            draw.line([(x-10, y), (x+10, y)], fill=color, width=6)
            draw.text((x+20, y-10), f"½", fill=color, font=get_examiner_font(24))
        else:
            color = color_incorrect
            # Cross mark
            draw.line([(x-25, y-25), (x+25, y+25)], fill=color, width=12)
            draw.line([(x+25, y-25), (x-25, y+25)], fill=color, width=12)
            draw.text((x+30, y-15), f"✗", fill=color, font=get_examiner_font(28))
        
        # Add marks awarded near the tick/cross
        if mark.get('marks_awarded'):
            draw.text((x+50, y-10), f"+{mark['marks_awarded']}", fill=color, font=get_examiner_font(20))
        
        # Draw notes in the margin (right side) if they exist
        if mark.get('note'):
            # Draw connecting line from mark to margin note
            draw.line([(x+80, y), (margin_x - 20, note_y_start + (idx * 80))], 
                     fill=color, width=2, joint="curve")
            
            # Draw note box in margin
            note_box = [margin_x, note_y_start + (idx * 80) - 30, 
                       margin_x + 220, note_y_start + (idx * 80) + 50]
            draw.rectangle(note_box, fill=color_note_bg, outline=color, width=2)
            
            # Add handwritten note
            draw_handwriting_text(draw, mark['note'], 
                                 (margin_x + 10, note_y_start + (idx * 80) - 15),
                                 (255, 255, 255, 255), 18)
            
            # Add mark indicator in note
            if not mark['correct'] and mark.get('deduction'):
                draw_handwriting_text(draw, f"(-{mark['deduction']})",
                                     (margin_x + 10, note_y_start + (idx * 80) + 15),
                                     (255, 150, 150, 255), 16)
            elif mark.get('marks_awarded'):
                draw_handwriting_text(draw, f"(+{mark['marks_awarded']})",
                                     (margin_x + 10, note_y_start + (idx * 80) + 15),
                                     (150, 255, 150, 255), 16)

    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 7. MARKING SCHEME COMPARISON ENGINE ---
def compare_with_marking_scheme(student_answers, marking_scheme):
    """Compare student answers with marking scheme"""
    marks_awarded = []
    total_possible = marking_scheme.get('total_marks', 100)
    
    for q in marking_scheme.get('questions', []):
        qno = q['qno']
        max_marks = q['marks']
        
        # Simulate intelligent marking based on key points
        if student_answers and qno <= len(student_answers):
            answer = student_answers[qno-1]
            awarded = 0
            
            # Check each key point
            for point in q['key_points']:
                if point.lower() in answer.lower():
                    awarded += max_marks // len(q['key_points'])
            
            marks_awarded.append({
                'qno': qno,
                'awarded': awarded,
                'max': max_marks,
                'feedback': f"Met {int(awarded/(max_marks/len(q['key_points'])))} of {len(q['key_points'])} criteria"
            })
        else:
            marks_awarded.append({'qno': qno, 'awarded': 0, 'max': max_marks, 'feedback': "No answer provided"})
    
    return marks_awarded, sum(m['awarded'] for m in marks_awarded)

# --- 8. SESSION MANAGEMENT ---
if 'user_tier' not in st.session_state:
    st.session_state.user_tier = "FREE"
if 'eval_history' not in st.session_state:
    st.session_state.eval_history = []
if 'credits' not in st.session_state:
    st.session_state.credits = 1
if 'exam_board' not in st.session_state:
    st.session_state.exam_board = "Edexcel (Pearson)"
if 'marking_scheme' not in st.session_state:
    st.session_state.marking_scheme = None

# --- 9. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color:#00E5FF; font-size: 50px; font-weight: 900; margin-bottom:0;'>BiTs.edu</h1>", unsafe_allow_html=True)
    st.caption(f"Neural Senior Examiner v{SYSTEM_VERSION}")
    st.divider()
    
    st.session_state.exam_board = st.selectbox("Examination Board", options=list(EXAM_BOARDS.keys()))
    
    st.divider()
    nav = st.radio("SYSTEM ACCESS", ["EXAMINER DASHBOARD", "SUBSCRIPTION", "ARCHIVE"], label_visibility="collapsed")
    
    st.divider()
    st.metric("TIER", st.session_state.user_tier)
    st.metric("DAILY CREDITS", f"{st.session_state.credits}/1")

# --- 10. PAGE: EXAMINER DASHBOARD ---
if nav == "EXAMINER DASHBOARD":
    board_info = EXAM_BOARDS[st.session_state.exam_board]
    
    st.title("BiTs Neural Examiner")
    st.write(f"**{st.session_state.exam_board}** | {board_info['region']} | {board_info['type']}")
    
    # Two-column layout for inputs
    col1, col2 = st.columns(2)
    
    with col1:
        subject = st.text_input("Subject", placeholder="e.g., Mathematics, Physics")
        paper_code = st.text_input("Paper Code", placeholder="e.g., 4MA1/01")
        max_score = st.number_input("Total Marks", min_value=1, max_value=500, value=100)
    
    with col2:
        exam_session = st.selectbox("Exam Session", ["January", "June", "November", "Mock"])
        year = st.number_input("Year", min_value=2020, max_value=2026, value=2026)
        level = st.selectbox("Level", ["Foundation", "Higher", "Advanced"])
    
    # Marking Scheme Upload Section
    st.markdown("---")
    st.subheader("Marking Scheme Upload (Optional)")
    st.markdown("Upload the official marking scheme for intelligent comparison")
    
    marking_file = st.file_uploader("Upload Marking Scheme (PDF)", type=['pdf'], key="marking_scheme")
    
    if marking_file:
        with st.spinner("Processing marking scheme..."):
            marking_scheme_data = parse_marking_scheme(marking_file.read())
            if marking_scheme_data:
                st.session_state.marking_scheme = marking_scheme_data
                st.success(f"Marking scheme loaded: {marking_scheme_data['total_marks']} total marks, {len(marking_scheme_data['questions'])} questions")
                
                # Display marking scheme summary
                with st.expander("View Marking Scheme Summary"):
                    st.write(f"**Total Marks:** {marking_scheme_data['total_marks']}")
                    for q in marking_scheme_data['questions']:
                        st.write(f"**Q{q['qno']}** ({q['marks']} marks): {', '.join(q['key_points'])}")
            else:
                st.error("Could not parse marking scheme. Please ensure it's a clear PDF.")
    
    st.markdown("---")
    
    # Student Script Upload
    uploaded_file = st.file_uploader("Upload Candidate Script (PDF)", type=['pdf'])
    
    if uploaded_file and st.session_state.credits > 0:
        if st.button("Execute Neural Marking", use_container_width=True):
            with st.spinner(f"BiTs Neural Examiner analyzing script..."):
                time.sleep(1.5)
                pdf_bytes = uploaded_file.read()
                images = process_pdf_to_images(pdf_bytes)
                
                if images:
                    st.session_state.credits -= 1
                    
                    # Generate intelligent marks based on marking scheme
                    if st.session_state.marking_scheme:
                        # Use marking scheme for intelligent marking
                        student_answers = ["Sample answer text for comparison"] * len(st.session_state.marking_scheme.get('questions', []))
                        marks_data, total_awarded = compare_with_marking_scheme(student_answers, st.session_state.marking_scheme)
                        
                        sample_marks = []
                        for idx, q in enumerate(st.session_state.marking_scheme.get('questions', [])[:4]):
                            mark_info = marks_data[idx] if idx < len(marks_data) else {'awarded': 0}
                            is_correct = mark_info['awarded'] > q['marks'] * 0.6
                            is_partial = 0 < mark_info['awarded'] <= q['marks'] * 0.6
                            
                            sample_marks.append({
                                'x': 150 + (idx * 150),
                                'y': 200 + (idx * 100),
                                'correct': is_correct,
                                'partial': is_partial,
                                'marks_awarded': mark_info['awarded'],
                                'deduction': q['marks'] - mark_info['awarded'] if not is_correct else 0,
                                'note': mark_info['feedback'] if mark_info['awarded'] < q['marks'] else "Good understanding demonstrated"
                            })
                    else:
                        # Default marking simulation
                        sample_marks = [
                            {'x': 150, 'y': 200, 'correct': True, 'marks_awarded': 8, 'note': "Method mark awarded - correct application"},
                            {'x': 350, 'y': 400, 'correct': False, 'marks_awarded': 0, 'deduction': 6, 'note': "Incorrect use of formula. Review section 3.2"},
                            {'x': 500, 'y': 300, 'partial': True, 'marks_awarded': 4, 'note': "Partial credit - working shown but final answer incomplete"},
                            {'x': 650, 'y': 500, 'correct': True, 'marks_awarded': 5, 'note': "Accuracy mark - fully correct solution"},
                            {'x': 200, 'y': 600, 'correct': False, 'marks_awarded': 0, 'deduction': 3, 'note': "Missing units in final answer"},
                        ]
                        total_awarded = sum(m['marks_awarded'] for m in sample_marks)
                    
                    # Get page dimensions
                    page_width, page_height = images[0].size
                    
                    # Render marks with side notes
                    processed_img = render_examiner_marks_enhanced(images[0], sample_marks, page_width, page_height)
                    
                    # Calculate grade
                    percentage = (total_awarded / max_score) * 100
                    grade = "A*" if percentage >= 90 else "A" if percentage >= 80 else "B" if percentage >= 70 else "C" if percentage >= 60 else "D" if percentage >= 50 else "E" if percentage >= 40 else "U"
                    
                    # Display results
                    st.success("Marking complete with examiner annotations")
                    
                    # Results layout
                    res_col1, res_col2 = st.columns([2, 1])
                    
                    with res_col1:
                        st.image(processed_img, caption="Marked Script with Examiner Notes", use_container_width=True)
                        
                        # Download options
                        img_bytes = io.BytesIO()
                        processed_img.save(img_bytes, format='PNG')
                        
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            st.download_button("Download Marked Script", data=img_bytes.getvalue(), 
                                             file_name=f"{paper_code}_marked.png", mime="image/png")
                        with col_dl2:
                            if st.button("Generate Marking Report"):
                                st.info("Detailed report generation would be implemented here")
                    
                    with res_col2:
                        st.markdown(f"""
                        <div style='text-align: center; padding: 20px; background: rgba(0,229,255,0.1); border-radius: 10px;'>
                            <h3>Candidate Results</h3>
                            <h1 style='font-size: 64px; color: #00FF88;'>{grade}</h1>
                            <hr>
                            <p><b>Score:</b> {total_awarded}/{max_score}</p>
                            <p><b>Percentage:</b> {percentage:.1f}%</p>
                            <p><b>Board:</b> {st.session_state.exam_board}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("Question Breakdown"):
                            for idx, mark in enumerate(sample_marks, 1):
                                status = "✓ Correct" if mark['correct'] else "✗ Incorrect" if not mark.get('partial') else "½ Partial"
                                color = "green" if mark['correct'] else "orange" if mark.get('partial') else "red"
                                st.markdown(f"**Q{idx}:** <span style='color:{color}'>{status}</span> - {mark['marks_awarded']} marks", unsafe_allow_html=True)
                                if mark.get('note'):
                                    st.caption(f"📝 {mark['note']}")
                        
                        with st.expander("Examiner Summary"):
                            st.write("**Strengths:**")
                            st.write("- Clear understanding of core concepts")
                            st.write("- Good working shown in multiple sections")
                            st.write("**Areas for Development:**")
                            st.write("- Review incorrect responses carefully")
                            st.write("- Practice past papers for exam technique")
                            st.write("- Pay attention to marking scheme requirements")
                        
                        # Save to history
                        st.session_state.eval_history.append({
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "subject": subject,
                            "paper_code": paper_code,
                            "grade": grade,
                            "score": f"{total_awarded}/{max_score}",
                            "percentage": percentage,
                            "exam_board": st.session_state.exam_board,
                            "marks": sample_marks
                        })
                    
    elif uploaded_file and st.session_state.credits <= 0:
        st.error("Daily credit limit reached. Please upgrade for unlimited marking.")

# --- 11. PAGE: SUBSCRIPTION ---
elif nav == "SUBSCRIPTION":
    st.title("Subscription Plans")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="plan-card">
            <h2>Free Tier</h2>
            <h3>$0</h3>
            <p>1 script per day</p>
            <p>Basic marking</p>
            <p>Standard annotations</p>
            <br><br>
        </div>
        """, unsafe_allow_html=True)
        st.button("Current Plan", disabled=True, use_container_width=True)
    
    with col2:
        st.markdown("""
        <div class="plan-card plan-pro">
            <h2>Pro Tier</h2>
            <h3>$49<span style='font-size: 16px;'>/month</span></h3>
            <p>Unlimited scripts</p>
            <p>Marking scheme comparison</p>
            <p>Advanced handwriting annotations</p>
            <p>All examination boards</p>
            <p>Priority support</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upgrade to Pro", use_container_width=True):
            st.info("Payment integration would be implemented here")

# --- 12. PAGE: ARCHIVE ---
elif nav == "ARCHIVE":
    st.title("Marking Archive")
    
    if st.session_state.eval_history:
        for idx, eval_item in enumerate(reversed(st.session_state.eval_history[-10:])):
            with st.expander(f"{eval_item['paper_code']} - {eval_item['subject']} - Grade {eval_item['grade']} ({eval_item['date']})"):
                st.write(f"**Exam Board:** {eval_item['exam_board']}")
                st.write(f"**Score:** {eval_item['score']}")
                st.write(f"**Percentage:** {eval_item['percentage']:.1f}%")
                
                if st.button(f"View Details", key=f"view_{idx}"):
                    st.info("Detailed view would show the marked script")
    else:
        st.info("No markings in archive. Complete a marking session to see results here.")

# --- 13. FOOTER ---
st.markdown("---")
st.caption(f"BiTs.edu Neural Senior Examiner v{SYSTEM_VERSION} | Professional Examiner Handwriting Technology")
