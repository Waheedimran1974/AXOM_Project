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
    page_title="BITs.edu | Neural Senior Examiner",
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
    
    /* Custom Red-Pen Style for Notes */
    .red-pen-text {
        font-family: 'JetBrains Mono', monospace;
        color: #FF4B4B;
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
    
    /* Remove emoji from buttons and text */
    button span, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        letter-spacing: normal;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE LOGIC & RENDERING UTILITIES ---
@st.cache_data
def process_pdf_to_images(pdf_bytes):
    """Converts student script PDF into high-res PIL images for vision processing."""
    try:
        return convert_from_bytes(pdf_bytes, dpi=200)
    except Exception as e:
        st.error(f"Engine Error: Unable to process PDF structure. {e}")
        return []

def render_neural_marks(img, marks):
    """The 'Censora' Red Pen rendering layer."""
    canvas = img.convert("RGBA")
    overlay = Image.new('RGBA', canvas.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    color_pass = (0, 229, 255, 220)  # BITs Teal
    color_fail = (255, 75, 75, 220)  # Examiner Red
    
    for m in marks:
        x, y = int(m['x']), int(m['y'])
        color = color_pass if m['correct'] else color_fail
        
        # Professional Examiner Symbols
        if m['correct']:
            # Tick mark
            draw.line([(x-25, y), (x, y+25), (x+50, y-35)], fill=color, width=14)
        else:
            # Cross mark
            draw.line([(x-30, y-30), (x+30, y+30)], fill=color, width=14)
            draw.line([(x+30, y-30), (x-30, y+30)], fill=color, width=14)
        
        # Red-Pen Logic Box
        if m.get('note'):
            draw.rectangle([x+70, y-25, x+500, y+50], fill=(0,0,0,210), outline=color, width=2)
            draw.text((x+85, y-10), m['note'], fill=(255,255,255))

    return Image.alpha_composite(canvas, overlay).convert("RGB")

# --- 4. SESSION MANAGEMENT ---
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

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h1 style='color:#00E5FF; font-size: 50px; font-weight: 900; margin-bottom:0;'>BITs</h1>", unsafe_allow_html=True)
    st.caption(f"v{SYSTEM_VERSION} | Next Step Future Infrastructure")
    st.divider()
    
    nav = st.radio("SYSTEM ACCESS", ["NEURAL GRADER", "REVISION HUB", "SUBSCRIPTION", "ARCHIVE"], label_visibility="collapsed")
    
    st.divider()
    
    # Display tier and credit information
    tier_col, credit_col = st.columns(2)
    with tier_col:
        st.metric("TIER", st.session_state.user_tier)
    with credit_col:
        max_credits = 1 if st.session_state.user_tier == "FREE" else float('inf')
        st.metric("DAILY CREDITS", f"{st.session_state.credits}/1")
    
    if st.session_state.user_tier == "FREE":
        st.info("Daily limit active. Upgrade for unlimited scans.")

# --- 6. PAGE: NEURAL GRADER ---
if nav == "NEURAL GRADER":
    st.title("Neural Script Analysis")
    st.write("Scan student scripts against PhD-level examiner logic (Gemini 2.0 Optimized).")
    
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            exam_subject = st.text_input("Exam Subject", placeholder="e.g., Advanced Mathematics")
            max_score = st.number_input("Maximum Score", min_value=1, max_value=100, value=100)
        
        with col2:
            exam_level = st.selectbox("Difficulty Level", ["Undergraduate", "Master's", "PhD", "Professional"])
            time_limit = st.number_input("Time Limit (minutes)", min_value=1, max_value=300, value=60)
    
    uploaded_file = st.file_uploader("Upload Student Script (PDF only)", type=['pdf'])
    
    if uploaded_file and st.session_state.credits > 0:
        if st.button("Execute Neural Scan", use_container_width=True):
            with st.spinner("Neural engine processing script..."):
                time.sleep(1)  # Simulate processing
                pdf_bytes = uploaded_file.read()
                images = process_pdf_to_images(pdf_bytes)
                
                if images:
                    st.session_state.credits -= 1
                    st.session_state.daily_usage += 1
                    
                    # Simulate marking results
                    sample_marks = [
                        {'x': 100, 'y': 200, 'correct': True, 'note': 'Excellent methodology'},
                        {'x': 300, 'y': 400, 'correct': False, 'note': 'Missing key theorem'},
                        {'x': 500, 'y': 150, 'correct': True, 'note': 'Good use of references'}
                    ]
                    
                    processed_img = render_neural_marks(images[0], sample_marks)
                    
                    # Display results
                    st.success("Neural scan completed successfully")
                    
                    # Show results in columns
                    res_col1, res_col2 = st.columns([2, 1])
                    
                    with res_col1:
                        st.image(processed_img, caption="Annotated Script", use_container_width=True)
                    
                    with res_col2:
                        st.subheader("Evaluation Summary")
                        st.metric("Estimated Score", "72/100")
                        st.metric("Time Spent", "45 min")
                        st.metric("Quality Index", "B+")
                        
                        with st.expander("Detailed Feedback"):
                            st.write("Strengths:")
                            st.write("- Strong conceptual understanding")
                            st.write("- Good problem-solving approach")
                            st.write("Areas for Improvement:")
                            st.write("- Missing critical theorem in section 3")
                            st.write("- Need more rigorous proof structure")
                    
                    # Download button
                    img_bytes = io.BytesIO()
                    processed_img.save(img_bytes, format='PNG')
                    st.download_button(
                        label="Download Annotated Script",
                        data=img_bytes.getvalue(),
                        file_name="annotated_script.png",
                        mime="image/png"
                    )
                    
    elif uploaded_file and st.session_state.credits <= 0:
        st.error("Daily credit limit reached. Please upgrade to continue.")

# --- 7. PAGE: SUBSCRIPTION ---
elif nav == "SUBSCRIPTION":
    st.title("Subscription Plans")
    st.write("Choose the plan that fits your needs")
    
    tier_col1, tier_col2 = st.columns(2)
    
    with tier_col1:
        st.markdown("""
        <div class="plan-card">
            <h2>Free Tier</h2>
            <h3>$0</h3>
            <p>1 scan per day</p>
            <p>Basic analytics</p>
            <p>PDF export</p>
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
            <p>Unlimited scans</p>
            <p>Advanced analytics</p>
            <p>Priority processing</p>
            <p>API access</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upgrade to Pro", key="pro_btn", use_container_width=True):
            st.info("Payment processing would be integrated here")
            # Payment integration would go here

# --- 8. PAGE: REVISION HUB ---
elif nav == "REVISION HUB":
    st.title("Revision Hub")
    st.write("Review past evaluations and track progress")
    
    # Placeholder for revision history
    if st.session_state.eval_history:
        for idx, eval_item in enumerate(st.session_state.eval_history):
            with st.expander(f"Evaluation {idx + 1} - {eval_item.get('date', 'Unknown date')}"):
                st.write(f"Subject: {eval_item.get('subject', 'N/A')}")
                st.write(f"Score: {eval_item.get('score', 'N/A')}")
                st.write(f"Feedback: {eval_item.get('feedback', 'N/A')}")
    else:
        st.info("No evaluations in history. Complete a scan to see results here.")

# --- 9. PAGE: ARCHIVE ---
elif nav == "ARCHIVE":
    st.title("Evaluation Archive")
    st.write("Access historical data and generate reports")
    
    # Date filter
    date_range = st.date_input("Select Date Range", [])
    
    # Archive content placeholder
    st.markdown("### Archived Evaluations")
    
    archive_data = [
        {"date": "2026-03-30", "student": "JD001", "subject": "Mathematics", "score": "85/100"},
        {"date": "2026-03-29", "student": "MS045", "subject": "Physics", "score": "92/100"},
        {"date": "2026-03-28", "student": "AK023", "subject": "Computer Science", "score": "78/100"},
    ]
    
    for item in archive_data:
        with st.container():
            col_a, col_b, col_c, col_d = st.columns([2,2,2,1])
            with col_a:
                st.write(item["date"])
            with col_b:
                st.write(item["student"])
            with col_c:
                st.write(item["subject"])
            with col_d:
                st.write(item["score"])
            st.divider()
    
    # Export functionality
    if st.button("Generate Report", use_container_width=True):
        st.success("Report generation would be implemented here")

# --- 10. FOOTER ---
st.markdown("---")
st.caption(f"BITs Neural Senior Examiner v{SYSTEM_VERSION} | Enterprise Grade Academic Assessment")
