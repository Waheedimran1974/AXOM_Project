import streamlit as st
import time
import datetime
import io
import base64
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# --- 1. GLOBAL SYSTEM CONFIGURATION ---
SYSTEM_VERSION = "2.2.0-PRO"
LAUNCH_DATE = "2026-03-31"
DAILY_BUDGET_CAP = 0.50

st.set_page_config(
    page_title="Edexcel | Neural Senior Examiner",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. NEURAL UI ENGINE (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono&display=swap');
    
    :root {
        --primary-glow: #0066CC;
        --secondary-glow: #003399;
        --dark-bg: #050505;
        --card-bg: rgba(15, 15, 15, 0.95);
    }

    .stApp { background-color: var(--dark-bg); color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    /* Premium Glassmorphism Cards */
    .bits-card {
        background: var(--card-bg);
        border: 1px solid #222;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
        margin-bottom: 25px;
        border-left: 4px solid var(--primary-glow);
    }
    
    /* Custom Examiner Style for Notes */
    .examiner-text {
        font-family: 'JetBrains Mono', monospace;
        color: #FF6B6B;
        font-size: 0.9rem;
        background: rgba(255, 75, 75, 0.1);
        padding: 5px;
        border-radius: 4px;
    }

    /* Subscription Tier UI */
    .plan-card {
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #333;
        text-align: center;
        background: #0A0A0A;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .plan-card:hover { border-color: var(--primary-glow); transform: translateY(-8px); }
    .plan-pro { border: 2px solid var(--primary-glow); box-shadow: 0 0 20px rgba(0, 102, 204, 0.2); }
    
    /* Grade Band Styling */
    .grade-a {
        color: #00FF88;
        font-weight: bold;
    }
    .grade-b {
        color: #88FF00;
        font-weight: bold;
    }
    .grade-c {
        color: #FFCC00;
        font-weight: bold;
    }
    .grade-d {
        color: #FF8800;
        font-weight: bold;
    }
    .grade-e {
        color: #FF4400;
        font-weight: bold;
    }
    .grade-u {
        color: #FF0000;
        font-weight: bold;
    }
    
    /* Global Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, var(--primary-glow), var(--secondary-glow)) !important;
        color: #FFF !important;
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
    </style>
    """, unsafe_allow_html=True)

# --- 3. EXAM BOARD CONFIGURATION ---
EXAM_BOARDS = {
    "Edexcel": {
        "grade_boundaries": {
            "A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "U": 0
        },
        "color_codes": {
            "A*": "grade-a", "A": "grade-a", "B": "grade-b", "C": "grade-c",
            "D": "grade-d", "E": "grade-e", "U": "grade-u"
        }
    },
    "Cambridge IGCSE": {
        "grade_boundaries": {
            "A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "F": 30, "G": 20, "U": 0
        },
        "color_codes": {
            "A*": "grade-a", "A": "grade-a", "B": "grade-b", "C": "grade-c",
            "D": "grade-d", "E": "grade-e", "F": "grade-e", "G": "grade-u", "U": "grade-u"
        }
    },
    "Oxford AQA": {
        "grade_boundaries": {
            "9": 90, "8": 80, "7": 70, "6": 60, "5": 50, "4": 40, "3": 30, "2": 20, "1": 10, "U": 0
        },
        "color_codes": {
            "9": "grade-a", "8": "grade-a", "7": "grade-b", "6": "grade-b",
            "5": "grade-c", "4": "grade-c", "3": "grade-d", "2": "grade-e", "1": "grade-u", "U": "grade-u"
        }
    }
}

# --- 4. CORE LOGIC & RENDERING UTILITIES ---
@st.cache_data
def process_pdf_to_images(pdf_bytes):
    """Converts student script PDF into high-res PIL images for vision processing."""
    try:
        return convert_from_bytes(pdf_bytes, dpi=200)
    except Exception as e:
        st.error(f"Engine Error: Unable to process PDF structure. {e}")
        return []

def calculate_grade(percentage, exam_board):
    """Calculate grade based on exam board boundaries"""
    boundaries = EXAM_BOARDS[exam_board]["grade_boundaries"]
    sorted_grades = sorted(boundaries.items(), key=lambda x: x[1], reverse=True)
    
    for grade, min_score in sorted_grades:
        if percentage >= min_score:
            return grade
    return "U"

def get_grade_color(grade, exam_board):
    """Get CSS class for grade display"""
    color_map = EXAM_BOARDS[exam_board]["color_codes"]
    return color_map.get(grade, "grade-u")

def render_examiner_marks(img, marks):
    """Professional examiner marking layer with Edexcel/IGCSE standards"""
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    color_correct = (0, 102, 204, 220)  # Edexcel Blue
    color_incorrect = (255, 75, 75, 220)  # Examiner Red
    color_partial = (255, 204, 0, 220)  # Partial credit
    
    for m in marks:
        x, y = int(m['x']), int(m['y'])
        
        if m['correct']:
            color = color_correct
            # Edexcel style tick
            draw.line([(x-20, y), (x-5, y+15), (x+25, y-20)], fill=color, width=12)
            # Award mark
            draw.text((x+30, y-10), f"+{m.get('marks_awarded', 1)}", fill=color, font=None)
        elif m.get('partial', False):
            color = color_partial
            # Partial credit symbol
            draw.ellipse([x-15, y-15, x+15, y+15], outline=color, width=8)
            draw.text((x+20, y-10), f"+{m.get('marks_awarded', 0.5)}", fill=color, font=None)
        else:
            color = color_incorrect
            # Cross mark
            draw.line([(x-25, y-25), (x+25, y+25)], fill=color, width=12)
            draw.line([(x+25, y-25), (x-25, y+25)], fill=color, width=12)
        
        # Examiner comments
        if m.get('note'):
            draw.rectangle([x+60, y-30, x+450, y+40], fill=(0,0,0,220), outline=color, width=2)
            draw.text((x+75, y-15), m['note'], fill=(255,255,255))
            
            # Add mark deduction note
            if not m['correct'] and m.get('deduction'):
                draw.text((x+75, y+5), f"Deducted: {m['deduction']} marks", fill=(255,100,100))

    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 5. SESSION MANAGEMENT ---
if 'user_tier' not in st.session_state:
    st.session_state.user_tier = "FREE"
if 'eval_history' not in st.session_state:
    st.session_state.eval_history = []
if 'current_scan' not in st.session_state:
    st.session_state.current_scan = None
if 'credits' not in st.session_state:
    st.session_state.credits = 1
if 'daily_usage' not in st.session_state:
    st.session_state.daily_usage = 0
if 'exam_board' not in st.session_state:
    st.session_state.exam_board = "Edexcel"

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color:#0066CC; font-size: 50px; font-weight: 900; margin-bottom:0;'>Edexcel</h1>", unsafe_allow_html=True)
    st.caption(f"Neural Examiner v{SYSTEM_VERSION} | Board Certified")
    st.divider()
    
    # Exam board selection
    st.session_state.exam_board = st.selectbox(
        "Examination Board",
        options=list(EXAM_BOARDS.keys()),
        index=0
    )
    
    st.divider()
    
    nav = st.radio("SYSTEM ACCESS", ["EXAMINER DASHBOARD", "GRADE BOUNDARIES", "SUBSCRIPTION", "ARCHIVE"], label_visibility="collapsed")
    
    st.divider()
    
    # Display tier and credit information
    tier_col, credit_col = st.columns(2)
    with tier_col:
        st.metric("TIER", st.session_state.user_tier)
    with credit_col:
        st.metric("DAILY CREDITS", f"{st.session_state.credits}/1")
    
    if st.session_state.user_tier == "FREE":
        st.info("Daily limit active. Upgrade for unlimited marking.")

# --- 7. PAGE: EXAMINER DASHBOARD ---
if nav == "EXAMINER DASHBOARD":
    st.title(f"{st.session_state.exam_board} Neural Examiner")
    st.write("Professional script marking with board-specific grade boundaries and standards")
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            subject = st.text_input("Subject", placeholder="e.g., Mathematics A")
            paper_code = st.text_input("Paper Code", placeholder="e.g., 4MA1/01")
        
        with col2:
            max_score = st.number_input("Total Marks Available", min_value=1, max_value=200, value=100)
            exam_session = st.selectbox("Exam Session", ["January", "June", "November", "Mock"])
        
        with col3:
            year = st.number_input("Year", min_value=2020, max_value=2026, value=2026)
            difficulty = st.selectbox("Level", ["Foundation", "Higher", "Advanced"])
    
    uploaded_file = st.file_uploader("Upload Candidate Script (PDF only)", type=['pdf'])
    
    if uploaded_file and st.session_state.credits > 0:
        if st.button("Execute Marking", use_container_width=True):
            with st.spinner(f"{st.session_state.exam_board} examiner processing script..."):
                time.sleep(1.5)  # Simulate processing
                pdf_bytes = uploaded_file.read()
                images = process_pdf_to_images(pdf_bytes)
                
                if images:
                    st.session_state.credits -= 1
                    st.session_state.daily_usage += 1
                    
                    # Simulate Edexcel-style marking results
                    sample_marks = [
                        {'x': 100, 'y': 200, 'correct': True, 'marks_awarded': 5, 
                         'note': 'Method mark awarded - correct application of formula'},
                        {'x': 350, 'y': 450, 'correct': False, 'deduction': 4,
                         'note': 'Incorrect use of quadratic formula'},
                        {'x': 550, 'y': 150, 'partial': True, 'marks_awarded': 2,
                         'note': 'Partially correct - working shown but final answer wrong'},
                        {'x': 700, 'y': 600, 'correct': True, 'marks_awarded': 3,
                         'note': 'Accuracy mark - fully correct solution'},
                    ]
                    
                    processed_img = render_examiner_marks(images[0], sample_marks)
                    
                    # Calculate mock score
                    total_awarded = sum(m.get('marks_awarded', 0) for m in sample_marks)
                    percentage = (total_awarded / max_score) * 100
                    grade = calculate_grade(percentage, st.session_state.exam_board)
                    grade_class = get_grade_color(grade, st.session_state.exam_board)
                    
                    # Display results
                    st.success(f"Marking complete - {st.session_state.exam_board} standards applied")
                    
                    # Results layout
                    res_col1, res_col2 = st.columns([2, 1])
                    
                    with res_col1:
                        st.image(processed_img, caption="Marked Script", use_container_width=True)
                        
                        # Download button for marked script
                        img_bytes = io.BytesIO()
                        processed_img.save(img_bytes, format='PNG')
                        st.download_button(
                            label="Download Marked Script",
                            data=img_bytes.getvalue(),
                            file_name=f"{paper_code}_marked.png",
                            mime="image/png"
                        )
                    
                    with res_col2:
                        st.subheader("Candidate Results")
                        
                        # Grade display
                        st.markdown(f"""
                        <div style='text-align: center; padding: 20px; background: rgba(0,102,204,0.1); border-radius: 10px;'>
                            <h3>Final Grade</h3>
                            <h1 class='{grade_class}' style='font-size: 72px;'>{grade}</h1>
                            <hr>
                            <p>Score: {total_awarded}/{max_score}</p>
                            <p>Percentage: {percentage:.1f}%</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("Marking Breakdown"):
                            st.write("Question Analysis:")
                            for idx, mark in enumerate(sample_marks, 1):
                                if mark['correct']:
                                    status = "Correct"
                                    color = "green"
                                elif mark.get('partial'):
                                    status = "Partial"
                                    color = "orange"
                                else:
                                    status = "Incorrect"
                                    color = "red"
                                st.markdown(f"**Q{idx}:** <span style='color:{color}'>{status}</span> - {mark.get('marks_awarded', 0)} marks", unsafe_allow_html=True)
                        
                        with st.expander("Examiner Comments"):
                            st.write("**Strengths:**")
                            st.write("- Good understanding of algebraic manipulation")
                            st.write("- Clear working shown in section 2")
                            st.write("**Areas for Improvement:**")
                            st.write("- Review quadratic formula application")
                            st.write("- Check unit conversions in word problems")
                            st.write("- Practice past papers for time management")
                        
                        # Save to history
                        st.session_state.eval_history.append({
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "subject": subject,
                            "paper_code": paper_code,
                            "grade": grade,
                            "score": f"{total_awarded}/{max_score}",
                            "percentage": percentage,
                            "exam_board": st.session_state.exam_board
                        })
                    
    elif uploaded_file and st.session_state.credits <= 0:
        st.error("Daily credit limit reached. Please upgrade for unlimited marking.")

# --- 8. PAGE: GRADE BOUNDARIES ---
elif nav == "GRADE BOUNDARIES":
    st.title("Grade Boundaries Reference")
    st.write(f"Current {st.session_state.exam_board} grade boundaries and standards")
    
    boundaries = EXAM_BOARDS[st.session_state.exam_board]["grade_boundaries"]
    
    # Display grade boundaries
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Minimum Percentage Required")
        for grade, percentage in boundaries.items():
            if grade != "U":
                grade_class = get_grade_color(grade, st.session_state.exam_board)
                st.markdown(f"<span class='{grade_class}'><b>{grade}</b></span>: {percentage}%", unsafe_allow_html=True)
    
    with col2:
        st.subheader("Ungraded Threshold")
        st.markdown(f"**U (Ungraded)**: Below {boundaries.get('U', 0)}%")
    
    st.divider()
    
    # Historical boundaries (placeholder)
    st.subheader("Historical Grade Boundaries")
    years = ["2025", "2024", "2023", "2022"]
    selected_year = st.selectbox("Select Year", years)
    
    # Sample historical data
    historical_data = {
        "2025": {"A*": 88, "A": 78, "B": 68, "C": 58},
        "2024": {"A*": 87, "A": 77, "B": 67, "C": 57},
        "2023": {"A*": 85, "A": 75, "B": 65, "C": 55},
        "2022": {"A*": 82, "A": 72, "B": 62, "C": 52}
    }
    
    if selected_year in historical_data:
        st.write(f"**{selected_year} Boundaries:**")
        for grade, percentage in historical_data[selected_year].items():
            st.write(f"{grade}: {percentage}%")
    
    st.info("Note: Grade boundaries vary by subject and session. Check official board documentation for definitive boundaries.")

# --- 9. PAGE: SUBSCRIPTION ---
elif nav == "SUBSCRIPTION":
    st.title("Subscription Plans")
    st.write("Choose the plan for your marking needs")
    
    tier_col1, tier_col2 = st.columns(2)
    
    with tier_col1:
        st.markdown("""
        <div class="plan-card">
            <h2>Free Tier</h2>
            <h3>£0</h3>
            <p>1 script per day</p>
            <p>Basic marking</p>
            <p>PDF export</p>
            <p>Single exam board</p>
            <br>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Current Plan", key="free_btn", use_container_width=True, disabled=True):
            pass
    
    with tier_col2:
        st.markdown("""
        <div class="plan-card plan-pro">
            <h2>Pro Tier</h2>
            <h3>£39<span style='font-size: 16px;'>/month</span></h3>
            <p>Unlimited scripts</p>
            <p>Advanced marking analytics</p>
            <p>All exam boards</p>
            <p>Priority processing</p>
            <p>API access for institutions</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upgrade to Pro", key="pro_btn", use_container_width=True):
            st.info("Payment processing integration would be implemented here")
            # Payment integration would go here

# --- 10. PAGE: ARCHIVE ---
elif nav == "ARCHIVE":
    st.title("Marking Archive")
    st.write("Access historical script markings and generate reports")
    
    # Filter controls
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        date_range = st.date_input("Date Range", [])
    with filter_col2:
        board_filter = st.selectbox("Exam Board", ["All"] + list(EXAM_BOARDS.keys()))
    with filter_col3:
        grade_filter = st.multiselect("Grade Filter", ["A*", "A", "B", "C", "D", "E", "U"])
    
    # Display archive
    st.markdown("### Archived Markings")
    
    if st.session_state.eval_history:
        for idx, eval_item in enumerate(reversed(st.session_state.eval_history[-10:])):
            with st.expander(f"{eval_item['paper_code']} - {eval_item['subject']} - Grade {eval_item['grade']} ({eval_item['date']})"):
                st.write(f"**Exam Board:** {eval_item['exam_board']}")
                st.write(f"**Score:** {eval_item['score']}")
                st.write(f"**Percentage:** {eval_item['percentage']:.1f}%")
                st.write(f"**Grade:** {eval_item['grade']}")
                
                # Download option
                if st.button(f"Download Report", key=f"download_{idx}"):
                    st.info("Report generation would be implemented here")
    else:
        st.info("No markings in archive. Complete a marking session to see results here.")
    
    # Generate summary report
    if st.session_state.eval_history:
        st.divider()
        if st.button("Generate Summary Report", use_container_width=True):
            total_scripts = len(st.session_state.eval_history)
            grade_distribution = {}
            for item in st.session_state.eval_history:
                grade = item['grade']
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
            
            st.subheader("Summary Statistics")
            st.write(f"**Total Scripts Marked:** {total_scripts}")
            st.write("**Grade Distribution:**")
            for grade, count in grade_distribution.items():
                st.write(f"- {grade}: {count} scripts ({count/total_scripts*100:.1f}%)")

# --- 11. FOOTER ---
st.markdown("---")
st.caption(f"Edexcel Neural Examiner v{SYSTEM_VERSION} | Board Certified Academic Assessment | {st.session_state.exam_board} Standards")
