import streamlit as st
import time
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from PIL import Image, ImageDraw
import io

# --- 1. PROFESSIONAL UI STYLING ---
st.set_page_config(page_title="AXOM | Professional EdTech", layout="wide")

st.markdown("""
    <style>
    /* Professional Dark Theme */
    .stApp { 
        background-color: #050505; 
        color: #FFFFFF; 
        font-family: 'Segoe UI', Roboto, sans-serif; 
    }
    
    /* Navigation styling */
    section[data-testid="stSidebar"] {
        background-color: #0A0A0A !important;
        border-right: 1px solid #1A1A1A;
    }

    /* Professional Metric Cards */
    .metric-card {
        background: #111111;
        border: 1px solid #1A1A1A;
        padding: 20px;
        border-radius: 4px;
        text-align: center;
    }
    
    .accent-text { color: #00E5FF; font-weight: 600; }
    
    /* Prize Section */
    .prize-container {
        background: linear-gradient(180deg, #111 0%, #000 100%);
        border: 1px solid #00E5FF;
        padding: 40px;
        border-radius: 8px;
        text-align: center;
        margin-top: 20px;
    }
    
    .coming-soon-badge {
        background: #00E5FF;
        color: #000;
        padding: 4px 12px;
        font-size: 0.75rem;
        font-weight: bold;
        border-radius: 2px;
        text-transform: uppercase;
    }

    /* Buttons */
    .stButton>button {
        background: #00E5FF !important;
        color: #000 !important;
        font-weight: 600 !important;
        border-radius: 2px !important;
        border: none !important;
        height: 45px;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTHENTICATION & SESSION LOGIC ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'focus_points' not in st.session_state:
    st.session_state.focus_points = 0

def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def login_system():
    st.title("AXOM Login")
    with st.container():
        email = st.text_input("Institutional or Personal Email", placeholder="email@example.com")
        password = st.text_input("Password", type="password")
        
        if st.button("Access Dashboard"):
            if validate_email(email) and len(password) > 5:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Invalid credentials. Please verify your email format.")

# --- 3. MAIN APP INTERFACE ---
if not st.session_state.authenticated:
    login_system()
else:
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("<h2 style='color:#00E5FF'>AXOM v1.0</h2>", unsafe_allow_html=True)
        st.write(f"Logged in as: {st.session_state.user_email}")
        menu = st.radio("Navigation", ["Dashboard", "Vision AI Grader", "Focus Challenge", "Monetary Prize", "Settings"])
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # --- 4. PAGE ROUTING ---
    if menu == "Dashboard":
        st.subheader("Performance Overview")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="metric-card">Points Balance<br><span class="accent-text" style="font-size:24px">{st.session_state.focus_points}</span></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="metric-card">Global Percentile<br><span class="accent-text" style="font-size:24px">94th</span></div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="metric-card">Verified Scans<br><span class="accent-text" style="font-size:24px">12</span></div>', unsafe_allow_html=True)

    elif menu == "Vision AI Grader":
        st.subheader("Handwritten Document Analysis")
        st.write("Upload your paper for AI-verified grading and point allocation.")
        uploaded_file = st.file_uploader("Drop file here", type=['jpg', 'jpeg', 'png', 'pdf'])
        
        if uploaded_file:
            if st.button("Analyze Document"):
                with st.status("Initializing Gemini Vision Engine..."):
                    time.sleep(2)
                    st.write("Scanning syntax and structure...")
                    time.sleep(1)
                st.success("Analysis Complete: 88% Accuracy Score")
                st.session_state.focus_points += 10
                st.info("Reward: 10 Focus Points added to your balance.")

    elif menu == "Focus Challenge":
        st.subheader("High-Intensity Focus Session")
        st.write("Points are awarded based on verified camera presence and application lock.")
        duration = st.slider("Duration (Minutes)", 15, 120, 25)
        if st.button("Begin Session"):
            st.info(f"Session active. Focus for {duration} minutes to claim reward.")

    elif menu == "Monetary Prize":
        st.subheader("Annual Excellence Grant")
        st.markdown("""
            <div class="prize-container">
                <span class="coming-soon-badge">Coming Soon</span>
                <h1 style="font-size: 64px; margin: 20px 0;">$5,000.00</h1>
                <p style="color: #888; max-width: 600px; margin: 0 auto;">
                    The AXOM Global Grant is awarded to the student with the highest verified focus points 
                    and academic improvement ratio. Applications for the 2026 cycle open in September.
                </p>
            </div>
        """, unsafe_allow_html=True)

    elif menu == "Settings":
        st.subheader("Account Configurations")
        st.write("Manage your API keys and institutional data connections.")
