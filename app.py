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
    .plan-pro { border: 2px solid var(--primary-glow); box-shadow: 0 0 20px rgba(0, 229, 255, 0.2); }
    
    /* Grade Band Styling */
    .grade-a-star { color: #00FF88; font-weight: bold; }
    .grade-a { color: #44FF44; font-weight: bold; }
    .grade-b { color: #88FF00; font-weight: bold; }
    .grade-c { color: #FFCC00; font-weight: bold; }
    .grade-d { color: #FF8800; font-weight: bold; }
    .grade-e { color: #FF4400; font-weight: bold; }
    .grade-f { color: #FF2200; font-weight: bold; }
    .grade-g { color: #FF0000; font-weight: bold; }
    .grade-u { color: #CC0000; font-weight: bold; }
    .grade-9 { color: #00FF88; font-weight: bold; }
    .grade-8 { color: #44FF44; font-weight: bold; }
    .grade-7 { color: #88FF00; font-weight: bold; }
    .grade-6 { color: #CCFF00; font-weight: bold; }
    .grade-5 { color: #FFCC00; font-weight: bold; }
    .grade-4 { color: #FFAA00; font-weight: bold; }
    .grade-3 { color: #FF8800; font-weight: bold; }
    .grade-2 { color: #FF6600; font-weight: bold; }
    .grade-1 { color: #FF4400; font-weight: bold; }
    
    /* Global Button Styling */
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
    </style>
    """, unsafe_allow_html=True)

# --- 3. COMPREHENSIVE EXAM BOARD CONFIGURATION ---
EXAM_BOARDS = {
    # UK Boards
    "Edexcel (Pearson)": {
        "region": "United Kingdom",
        "type": "GCSE/A-Level",
        "grade_boundaries": {
            "A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "U": 0
        },
        "grade_scale": "A*-U"
    },
    "Cambridge IGCSE": {
        "region": "United Kingdom",
        "type": "IGCSE",
        "grade_boundaries": {
            "A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "F": 30, "G": 20, "U": 0
        },
        "grade_scale": "A*-G"
    },
    "Oxford AQA": {
        "region": "United Kingdom",
        "type": "GCSE/A-Level",
        "grade_boundaries": {
            "9": 90, "8": 80, "7": 70, "6": 60, "5": 50, "4": 40, "3": 30, "2": 20, "1": 10, "U": 0
        },
        "grade_scale": "9-1"
    },
    "WJEC Eduqas": {
        "region": "United Kingdom",
        "type": "GCSE/A-Level",
        "grade_boundaries": {
            "A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "U": 0
        },
        "grade_scale": "A*-U"
    },
    "CCEA": {
        "region": "United Kingdom",
        "type": "GCSE/A-Level",
        "grade_boundaries": {
            "A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "U": 0
        },
        "grade_scale": "A*-U"
    },
    
    # International Boards
    "International Baccalaureate (IB)": {
        "region": "International",
        "type": "IB Diploma",
        "grade_boundaries": {
            "7": 85, "6": 75, "5": 65, "4": 55, "3": 45, "2": 35, "1": 25, "U": 0
        },
        "grade_scale": "1-7"
    },
    "College Board (AP)": {
        "region": "United States",
        "type": "Advanced Placement",
        "grade_boundaries": {
            "5": 80, "4": 70, "3": 60, "2": 50, "1": 0
        },
        "grade_scale": "1-5"
    },
    "Cambridge International (CIE)": {
        "region": "International",
        "type": "IGCSE/A-Level",
        "grade_boundaries": {
            "A*": 90, "A": 80, "B": 70, "C": 60, "D": 50, "E": 40, "U": 0
        },
        "grade_scale": "A*-U"
    },
    
    # US Boards
    "SAT": {
        "region": "United States",
        "type": "College Admission",
        "grade_boundaries": {
            "800": 95, "700": 85, "600": 70, "500": 55, "400": 40, "300": 25
        },
        "grade_scale": "200-800"
    },
    "ACT": {
        "region": "United States",
        "type": "College Admission",
        "grade_boundaries": {
            "36": 95, "32": 85, "28": 75, "24": 65, "20": 55, "16": 40
        },
        "grade_scale": "1-36"
    },
    
    # Australian Boards
    "VCAA (VCE)": {
        "region": "Australia",
        "type": "VCE",
        "grade_boundaries": {
            "A+": 90, "A": 80, "B+": 70, "B": 60, "C+": 50, "C": 40, "D": 30, "E": 20, "UG": 0
        },
        "grade_scale": "A+-UG"
    },
    "NESA (HSC)": {
        "region": "Australia",
        "type": "HSC",
        "grade_boundaries": {
            "Band 6": 90, "Band 5": 80, "Band 4": 70, "Band 3": 60, "Band 2": 50, "Band 1": 0
        },
        "grade_scale": "Band 1-6"
    },
    
    # Canadian Boards
    "Ontario (OSSD)": {
        "region": "Canada",
        "type": "OSSD",
        "grade_boundaries": {
            "A+ (90-100)": 90, "A (85-89)": 85, "A- (80-84)": 80, "B+ (77-79)": 77, 
            "B (73-76)": 73, "B- (70-72)": 70, "C+ (67-69)": 67, "C (63-66)": 63,
            "C- (60-62)": 60, "D+ (57-59)": 57, "D (53-56)": 53, "D- (50-52)": 50, "F": 0
        },
        "grade_scale": "A+-F"
    },
    "British Columbia": {
        "region": "Canada",
        "type": "BC Curriculum",
        "grade_boundaries": {
            "A (86-100)": 86, "B (73-85)": 73, "C+ (67-72)": 67, "C (60-66)": 60, "C- (50-59)": 50, "F": 0
        },
        "grade_scale": "A-F"
    },
    
    # Indian Boards
    "CBSE": {
        "region": "India",
        "type": "Central Board",
        "grade_boundaries": {
            "A1 (91-100)": 91, "A2 (81-90)": 81, "B1 (71-80)": 71, "B2 (61-70)": 61,
            "C1 (51-60)": 51, "C2 (41-50)": 41, "D (33-40)": 33, "E1 (21-32)": 21, "E2 (0-20)": 0
        },
        "grade_scale": "A1-E2"
    },
    "CISCE (ICSE/ISC)": {
        "region": "India",
        "type": "ICSE/ISC",
        "grade_boundaries": {
            "90-100": 90, "80-89": 80, "70-79": 70, "60-69": 60, "50-59": 50, "40-49": 40, "33-39": 33, "0-32": 0
        },
        "grade_scale": "Percentage"
    },
    
    # Chinese Boards
    "Gaokao (National)": {
        "region": "China",
        "type": "National Exam",
        "grade_boundaries": {
            "Top Tier": 90, "Upper Tier": 80, "Middle Tier": 70, "Lower Tier": 60, "Basic": 50
        },
        "grade_scale": "Tier System"
    },
    
    # European Boards
    "Abitur (Germany)": {
        "region": "Germany",
        "type": "University Entrance",
        "grade_boundaries": {
            "1.0 (Sehr gut)": 95, "1.5": 85, "2.0 (Gut)": 75, "2.5": 65, "3.0 (Befriedigend)": 55,
            "3.5": 45, "4.0 (Ausreichend)": 40, "5.0 (Mangelhaft)": 0
        },
        "grade_scale": "1.0-5.0"
    },
    "Baccalaureate (France)": {
        "region": "France",
        "type": "Baccalaureate",
        "grade_boundaries": {
            "Très bien (16-20)": 80, "Bien (14-15.9)": 70, "Assez bien (12-13.9)": 60,
            "Passable (10-11.9)": 50, "Échec (0-9.9)": 0
        },
        "grade_scale": "0-20"
    },
    "Matriculation (Finland)": {
        "region": "Finland",
        "type": "Matriculation",
        "grade_boundaries": {
            "Laudatur (7)": 90, "Eximia cum laude approbatur (6)": 80, "Magna cum laude approbatur (5)": 70,
            "Cum laude approbatur (4)": 60, "Lubenter approbatur (3)": 50, "Approbatur (2)": 40, "Improbatur (1)": 0
        },
        "grade_scale": "1-7"
    },
    
    # Middle Eastern Boards
    "Tawjihi (Jordan/Palestine)": {
        "region": "Middle East",
        "type": "General Secondary",
        "grade_boundaries": {
            "Excellent (90-100)": 90, "Very Good (80-89)": 80, "Good (70-79)": 70, "Acceptable (60-69)": 60, "Weak (0-59)": 0
        },
        "grade_scale": "Percentage"
    },
    "Qudrat (Saudi Arabia)": {
        "region": "Saudi Arabia",
        "type": "General Aptitude",
        "grade_boundaries": {
            "90-100": 90, "80-89": 80, "70-79": 70, "60-69": 60, "Below 60": 0
        },
        "grade_scale": "Percentage"
    },
    
    # African Boards
    "WAEC (West Africa)": {
        "region": "West Africa",
        "type": "WASSCE",
        "grade_boundaries": {
            "A1 (75-100)": 75, "B2 (70-74)": 70, "B3 (65-69)": 65, "C4 (60-64)": 60,
            "C5 (55-59)": 55, "C6 (50-54)": 50, "D7 (45-49)": 45, "E8 (40-44)": 40, "F9 (0-39)": 0
        },
        "grade_scale": "A1-F9"
    },
    "NECO (Nigeria)": {
        "region": "Nigeria",
        "type": "National Exam",
        "grade_boundaries": {
            "A1 (75-100)": 75, "B2 (70-74)": 70, "B3 (65-69)": 65, "C4 (60-64)": 60,
            "C5 (55-59)": 55, "C6 (50-54)": 50, "D (40-49)": 40, "E (30-39)": 30, "F (0-29)": 0
        },
        "grade_scale": "A1-F9"
    },
    
    # Southeast Asian Boards
    "SPM (Malaysia)": {
        "region": "Malaysia",
        "type": "SPM",
        "grade_boundaries": {
            "A+ (90-100)": 90, "A (80-89)": 80, "A- (70-79)": 70, "B+ (65-69)": 65, "B (60-64)": 60,
            "C+ (55-59)": 55, "C (50-54)": 50, "D (45-49)": 45, "E (40-44)": 40, "G (0-39)": 0
        },
        "grade_scale": "A+-G"
    },
    "Ujian Nasional (Indonesia)": {
        "region": "Indonesia",
        "type": "National Exam",
        "grade_boundaries": {
            "A (85-100)": 85, "B (70-84)": 70, "C (60-69)": 60, "D (50-59)": 50, "E (0-49)": 0
        },
        "grade_scale": "A-E"
    },
    
    # South Asian Boards
    "SSC/HSC (Bangladesh)": {
        "region": "Bangladesh",
        "type": "SSC/HSC",
        "grade_boundaries": {
            "A+ (80-100)": 80, "A (70-79)": 70, "A- (60-69)": 60, "B (50-59)": 50,
            "C (40-49)": 40, "D (33-39)": 33, "F (0-32)": 0
        },
        "grade_scale": "A+-F"
    },
    
    # Latin American Boards
    "ENEM (Brazil)": {
        "region": "Brazil",
        "type": "National Exam",
        "grade_boundaries": {
            "Excelente (800-1000)": 80, "Bom (600-799)": 60, "Regular (400-599)": 40, "Baixo (0-399)": 0
        },
        "grade_scale": "0-1000"
    },
    
    # New Zealand Boards
    "NZQA (NCEA)": {
        "region": "New Zealand",
        "type": "NCEA",
        "grade_boundaries": {
            "Excellence (E)": 80, "Merit (M)": 65, "Achieved (A)": 50, "Not Achieved (N)": 0
        },
        "grade_scale": "E, M, A, N"
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
    return list(boundaries.keys())[-1]  # Return lowest grade

def get_grade_color_class(grade):
    """Get CSS class for grade display based on grade format"""
    grade_str = str(grade).lower()
    
    if 'a*' in grade_str or '9' in grade_str or '7' in grade_str or 'excellent' in grade_str:
        return "grade-a-star"
    elif 'a' in grade_str and '*' not in grade_str and 'a1' not in grade_str:
        return "grade-a"
    elif 'b' in grade_str or '8' in grade_str or '6' in grade_str or 'merit' in grade_str:
        return "grade-b"
    elif 'c' in grade_str or '5' in grade_str or 'achieved' in grade_str:
        return "grade-c"
    elif 'd' in grade_str or '4' in grade_str:
        return "grade-d"
    elif 'e' in grade_str or '3' in grade_str or 'e8' in grade_str:
        return "grade-e"
    elif 'f' in grade_str or '2' in grade_str:
        return "grade-f"
    elif 'g' in grade_str or '1' in grade_str:
        return "grade-g"
    else:
        return "grade-u"

def render_examiner_marks(img, marks):
    """Professional examiner marking layer with universal standards"""
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    color_correct = (0, 229, 255, 220)  # BiTs Cyan
    color_incorrect = (255, 75, 75, 220)  # Examiner Red
    color_partial = (255, 204, 0, 220)  # Partial credit
    
    for m in marks:
        x, y = int(m['x']), int(m['y'])
        
        if m['correct']:
            color = color_correct
            # Professional tick mark
            draw.line([(x-20, y), (x-5, y+15), (x+25, y-20)], fill=color, width=12)
            # Award mark
            draw.text((x+30, y-10), f"+{m.get('marks_awarded', 1)}", fill=color)
        elif m.get('partial', False):
            color = color_partial
            # Partial credit symbol (circle with slash)
            draw.ellipse([x-15, y-15, x+15, y+15], outline=color, width=8)
            draw.text((x+20, y-10), f"+{m.get('marks_awarded', 0.5)}", fill=color)
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
    st.session_state.exam_board = "Edexcel (Pearson)"
if 'region_filter' not in st.session_state:
    st.session_state.region_filter = "All Regions"

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color:#00E5FF; font-size: 50px; font-weight: 900; margin-bottom:0;'>BiTs.edu</h1>", unsafe_allow_html=True)
    st.caption(f"Neural Senior Examiner v{SYSTEM_VERSION} | Global Standards")
    st.divider()
    
    # Region filter for exam boards
    regions = ["All Regions"] + sorted(list(set(board["region"] for board in EXAM_BOARDS.values())))
    st.session_state.region_filter = st.selectbox("Filter by Region", regions)
    
    # Filter exam boards by region
    filtered_boards = EXAM_BOARDS
    if st.session_state.region_filter != "All Regions":
        filtered_boards = {k: v for k, v in EXAM_BOARDS.items() if v["region"] == st.session_state.region_filter}
    
    # Exam board selection
    st.session_state.exam_board = st.selectbox(
        "Examination Board",
        options=list(filtered_boards.keys()),
        index=0 if filtered_boards else 0
    )
    
    # Display board info
    if st.session_state.exam_board in EXAM_BOARDS:
        board_info = EXAM_BOARDS[st.session_state.exam_board]
        st.caption(f"Region: {board_info['region']} | Type: {board_info['type']}")
        st.caption(f"Grade Scale: {board_info['grade_scale']}")
    
    st.divider()
    
    nav = st.radio("SYSTEM ACCESS", ["EXAMINER DASHBOARD", "BOARD DIRECTORY", "GRADE BOUNDARIES", "SUBSCRIPTION", "ARCHIVE"], label_visibility="collapsed")
    
    st.divider()
    
    # Display tier and credit information
    tier_col, credit_col = st.columns(2)
    with tier_col:
        st.metric("TIER", st.session_state.user_tier)
    with credit_col:
        st.metric("DAILY CREDITS", f"{st.session_state.credits}/1")
    
    if st.session_state.user_tier == "FREE":
        st.info("Daily limit active. Upgrade for unlimited marking across all boards.")

# --- 7. PAGE: EXAMINER DASHBOARD ---
if nav == "EXAMINER DASHBOARD":
    board_name = st.session_state.exam_board
    board_info = EXAM_BOARDS[board_name]
    
    st.title(f"BiTs Neural Examiner")
    st.write(f"**{board_name}** | {board_info['region']} | {board_info['type']} Standards")
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        
        with col1:
            subject = st.text_input("Subject", placeholder="e.g., Mathematics, Physics, English")
            paper_code = st.text_input("Paper/Exam Code", placeholder="e.g., 4MA1/01, 9709/12")
        
        with col2:
            max_score = st.number_input("Total Marks Available", min_value=1, max_value=500, value=100)
            exam_session = st.selectbox("Exam Session", ["January", "March", "June", "August", "October", "November", "Mock"])
        
        with col3:
            year = st.number_input("Year", min_value=2020, max_value=2026, value=2026)
            level = st.selectbox("Level", ["Foundation", "Higher", "Advanced", "Core", "Extended"])
    
    uploaded_file = st.file_uploader("Upload Candidate Script (PDF only)", type=['pdf'])
    
    if uploaded_file and st.session_state.credits > 0:
        if st.button("Execute Neural Marking", use_container_width=True):
            with st.spinner(f"BiTs Neural Examiner processing {board_name} script..."):
                time.sleep(1.5)  # Simulate processing
                pdf_bytes = uploaded_file.read()
                images = process_pdf_to_images(pdf_bytes)
                
                if images:
                    st.session_state.credits -= 1
                    st.session_state.daily_usage += 1
                    
                    # Simulate marking results based on board
                    sample_marks = [
                        {'x': 100, 'y': 200, 'correct': True, 'marks_awarded': 5, 
                         'note': f'{board_name} standard: Method mark awarded'},
                        {'x': 350, 'y': 450, 'correct': False, 'deduction': 4,
                         'note': 'Conceptual error per board marking scheme'},
                        {'x': 550, 'y': 150, 'partial': True, 'marks_awarded': 2,
                         'note': 'Partial credit - working shown'},
                        {'x': 700, 'y': 600, 'correct': True, 'marks_awarded': 3,
                         'note': 'Accuracy mark - fully correct'},
                    ]
                    
                    processed_img = render_examiner_marks(images[0], sample_marks)
                    
                    # Calculate mock score
                    total_awarded = sum(m.get('marks_awarded', 0) for m in sample_marks)
                    percentage = (total_awarded / max_score) * 100
                    grade = calculate_grade(percentage, board_name)
                    grade_class = get_grade_color_class(grade)
                    
                    # Display results
                    st.success(f"Marking complete - {board_name} standards applied")
                    
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
                        <div style='text-align: center; padding: 20px; background: rgba(0,229,255,0.1); border-radius: 10px;'>
                            <h3>Final Grade</h3>
                            <h1 class='{grade_class}' style='font-size: 72px;'>{grade}</h1>
                            <hr>
                            <p>Score: {total_awarded}/{max_score}</p>
                            <p>Percentage: {percentage:.1f}%</p>
                            <p>Board: {board_name}</p>
                            <p>Scale: {board_info['grade_scale']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("Marking Breakdown"):
                            st.write("Question Analysis:")
                            for idx, mark in enumerate(sample_marks, 1):
                                if mark['correct']:
                                    status = "Correct"
                                    color = "green"
                                elif mark.get('partial'):
                                    status = "Partial Credit"
                                    color = "orange"
                                else:
                                    status = "Incorrect"
                                    color = "red"
                                st.markdown(f"**Q{idx}:** <span style='color:{color}'>{status}</span> - {mark.get('marks_awarded', 0)} marks", unsafe_allow_html=True)
                        
                        with st.expander("Examiner Comments"):
                            st.write("**Strengths:**")
                            st.write("- Strong conceptual understanding demonstrated")
                            st.write("- Clear working shown in multiple sections")
                            st.write("**Areas for Improvement:**")
                            st.write("- Review key concepts in incorrect responses")
                            st.write("- Practice time management strategies")
                            st.write("- Focus on exam technique per board standards")
                        
                        # Save to history
                        st.session_state.eval_history.append({
                            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "subject": subject,
                            "paper_code": paper_code,
                            "grade": grade,
                            "score": f"{total_awarded}/{max_score}",
                            "percentage": percentage,
                            "exam_board": board_name,
                            "region": board_info['region']
                        })
                    
    elif uploaded_file and st.session_state.credits <= 0:
        st.error("Daily credit limit reached. Please upgrade for unlimited marking across all boards.")

# --- 8. PAGE: BOARD DIRECTORY ---
elif nav == "BOARD DIRECTORY":
    st.title("Global Examination Board Directory")
    st.write("Browse all supported examination boards and their grading standards")
    
    # Search and filter
    search_term = st.text_input("Search Boards", placeholder="Enter board name, region, or type...")
    
    # Filter boards
    filtered_boards = EXAM_BOARDS
    if search_term:
        filtered_boards = {k: v for k, v in EXAM_BOARDS.items() 
                          if search_term.lower() in k.lower() 
                          or search_term.lower() in v['region'].lower()
                          or search_term.lower() in v['type'].lower()}
    
    # Group by region
    regions = {}
    for board_name, board_info in filtered_boards.items():
        region = board_info['region']
        if region not in regions:
            regions[region] = []
        regions[region].append((board_name, board_info))
    
    # Display boards by region
    for region, boards in sorted(regions.items()):
        with st.expander(f"{region} ({len(boards)} boards)"):
            for board_name, board_info in sorted(boards):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{board_name}**")
                with col2:
                    st.write(board_info['type'])
                with col3:
                    st.write(board_info['grade_scale'])
                st.caption(f"Grade boundaries: {', '.join(list(board_info['grade_boundaries'].keys())[:5])}...")
                st.divider()

# --- 9. PAGE: GRADE BOUNDARIES ---
elif nav == "GRADE BOUNDARIES":
    board_name = st.session_state.exam_board
    board_info = EXAM_BOARDS[board_name]
    
    st.title("Grade Boundaries Reference")
    st.write(f"**{board_name}** | {board_info['region']} | {board_info['type']}")
    
    boundaries = board_info["grade_boundaries"]
    
    # Display grade boundaries
    st.subheader("Minimum Percentage Required")
    
    # Create columns for better display
    cols = st.columns(3)
    for idx, (grade, percentage) in enumerate(boundaries.items()):
        with cols[idx % 3]:
            grade_class = get_grade_color_class(grade)
            st.markdown(f"<span class='{grade_class}'><b>{grade}</b></span>: {percentage}%", unsafe_allow_html=True)
    
    st.divider()
    
    # Grade conversion tool
    st.subheader("Grade Conversion Tool")
    st.write("Convert percentage to grade based on board standards")
    
    percentage_input = st.slider("Enter Percentage Score", 0, 100, 75)
    converted_grade = calculate_grade(percentage_input, board_name)
    grade_class = get_grade_color_class(converted_grade)
    
    st.markdown(f"""
    <div style='text-align: center; padding: 30px; background: rgba(0,229,255,0.1); border-radius: 10px; margin: 20px 0;'>
        <h3>Conversion Result</h3>
        <h1 class='{grade_class}' style='font-size: 64px;'>{converted_grade}</h1>
        <p>{percentage_input}% under {board_name} standards</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info(f"Note: Grade boundaries vary by subject and session. Consult official {board_name} documentation for definitive boundaries.")

# --- 10. PAGE: SUBSCRIPTION ---
elif nav == "SUBSCRIPTION":
    st.title("Subscription Plans")
    st.write("Access all global examination boards with unlimited marking")
    
    tier_col1, tier_col2 = st.columns(2)
    
    with tier_col1:
        st.markdown("""
        <div class="plan-card">
            <h2>Free Tier</h2>
            <h3>$0</h3>
            <p>1 script per day</p>
            <p>Basic marking</p>
            <p>PDF export</p>
            <p>Single exam board</p>
            <p>Limited regions</p>
            <br>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Current Plan", key="free_btn", use_container_width=True, disabled=True):
            pass
    
    with tier_col2:
        st.markdown("""
        <div class="plan-card plan-pro">
            <h2>Pro Tier</h2>
            <h3>$49<span style='font-size: 16px;'>/month</span></h3>
            <p>Unlimited scripts</p>
            <p>Advanced marking analytics</p>
            <p><b>All 30+ examination boards</b></p>
            <p>All regions worldwide</p>
            <p>Priority processing</p>
            <p>API access for institutions</p>
            <p>Bulk upload capability</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upgrade to Pro", key="pro_btn", use_container_width=True):
            st.info("Payment processing integration would be implemented here")
            st.write("**Supported Regions:** UK, USA, Canada, Australia, India, China, Europe, Middle East, Africa, Southeast Asia")

# --- 11. PAGE: ARCHIVE ---
elif nav == "ARCHIVE":
    st.title("Marking Archive")
    st.write("Access historical script markings across all boards")
    
    # Filter controls
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        date_range = st.date_input("Date Range", [])
    with filter_col2:
        board_filter = st.selectbox("Exam Board", ["All"] + list(EXAM_BOARDS.keys()))
    with filter_col3:
        region_filter = st.selectbox("Region", ["All"] + sorted(list(set(board["region"] for board in EXAM_BOARDS.values()))))
    
    # Display archive
    st.markdown("### Archived Markings")
    
    if st.session_state.eval_history:
        filtered_history = st.session_state.eval_history
        if board_filter != "All":
            filtered_history = [h for h in filtered_history if h['exam_board'] == board_filter]
        if region_filter != "All":
            filtered_history = [h for h in filtered_history if h.get('region') == region_filter]
        
        for idx, eval_item in enumerate(reversed(filtered_history[-20:])):
            with st.expander(f"{eval_item['paper_code']} - {eval_item['subject']} - Grade {eval_item['grade']} ({eval_item['date']})"):
                st.write(f"**Exam Board:** {eval_item['exam_board']}")
                st.write(f"**Region:** {eval_item.get('region', 'N/A')}")
                st.write(f"**Score:** {eval_item['score']}")
                st.write(f"**Percentage:** {eval_item['percentage']:.1f}%")
                st.write(f"**Grade:** {eval_item['grade']}")
                
                # Download option
                if st.button(f"Generate Report", key=f"download_{idx}"):
                    st.info("Comprehensive report generation would be implemented here")
    else:
        st.info("No markings in archive. Complete a marking session to see results here.")
    
    # Generate summary report
    if st.session_state.eval_history:
        st.divider()
        if st.button("Generate Global Summary Report", use_container_width=True):
            total_scripts = len(st.session_state.eval_history)
            grade_distribution = {}
            board_distribution = {}
            
            for item in st.session_state.eval_history:
                grade = item['grade']
                board = item['exam_board']
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
                board_distribution[board] = board_distribution.get(board, 0) + 1
            
            st.subheader("Global Summary Statistics")
            st.write(f"**Total Scripts Marked:** {total_scripts}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Grade Distribution:**")
                for grade, count in sorted(grade_distribution.items())[:10]:
                    st.write(f"- {grade}: {count} scripts ({count/total_scripts*100:.1f}%)")
            
            with col2:
                st.write("**Board Distribution:**")
                for board, count in sorted(board_distribution.items(), key=lambda x: x[1], reverse=True)[:5]:
                    st.write(f"- {board}: {count} scripts ({count/total_scripts*100:.1f}%)")

# --- 12. FOOTER ---
st.markdown("---")
st.caption(f"BiTs.edu Neural Senior Examiner v{SYSTEM_VERSION} | Supporting 30+ Global Examination Boards | {len(EXAM_BOARDS)} Boards Worldwide")
