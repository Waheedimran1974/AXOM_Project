import streamlit as st
from google import genai
import os
import json
import re
import io
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from PIL import Image, ImageDraw
import datetime

# --- 1. EMAIL SYSTEM CONFIG ---
def send_email_report(receiver_email, score, feedback, student_name="Student"):
    """Sends the AI Analysis report to the student's email."""
    sender_email = st.secrets.get("EMAIL_USER", "your_email@gmail.com")
    sender_password = st.secrets.get("EMAIL_PASS", "your_app_password")
    
    msg = MIMEMultipart()
    msg['From'] = f"AXOM AI Grader <{sender_email}>"
    msg['To'] = receiver_email
    msg['Subject'] = f"📊 Your AXOM Results: {score}%"

    body = f"""
    Assalamu Alaikum {student_name},
    
    Congratulations on completing your session!
    
    Your AI Vision Score: {score}%
    
    Feedback Summary:
    {feedback[:500]}... (Log in to AXOM for full details)
    
    Keep focusing, the $5,000 prize is waiting!
    - The AXOM Team
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Error: {e}")
        return False

# --- 2. HUD & INTERFACE STYLING ---
st.set_page_config(page_title="AXOM | VISION & REVENUE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #000d1a 0%, #000000 100%); color: #00e5ff; font-family: 'Inter', sans-serif; }
    .plan-card {
        background: linear-gradient(145deg, #001a33, #000000);
        border: 2px solid #00e5ff; padding: 25px; border-radius: 15px;
        text-align: center; transition: 0.3s; box-shadow: 0px 0px 15px rgba(0, 229, 255, 0.2);
        position: relative; height: 100%;
    }
    .big-clock { font-size: 5rem; font-weight: 900; color: #ffffff; font-family: 'Courier New'; margin: 20px 0; }
    .price-tag { font-size: 2.2rem; font-weight: 900; color: #ffffff; }
    .stButton>button { width: 100%; background: linear-gradient(90deg, #00e5ff, #007bff) !important; color: #fff !important; font-weight: 900; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE INITIALIZATION ---
if 'focus_points' not in st.session_state: st.session_state.focus_points = 0
if 'is_running' not in st.session_state: st.session_state.is_running = False

# --- 4. CORE AI ENGINE ---
try:
    client = genai.Client(api_key=st.secrets.get("GENAI_API_KEY", "YOUR_KEY"))
except:
    client = None

def run_vision_analysis(image_file):
    """Simulated Gemini Call for Paper Grading"""
    # Real implementation would use client.models.generate_content
    time.sleep(2) # Simulate processing
    return {"score": 85, "feedback": "Great structure, improve punctuation.", "points": 7}

# --- 5. MAIN NAVIGATION ---
menu = st.sidebar.selectbox("AXOM MENU", ["Dashboard", "AI Grader", "Focus Time", "Subscription"])

if menu == "Dashboard":
    st.title("🚀 Student HQ")
    cols = st.columns(3)
    cols[0].metric("Focus Points 💎", st.session_state.focus_points)
    cols[1].metric("Global Rank", "#1,204")
    cols[2].metric("Prize Pool", "$5,000")

elif menu == "AI Grader":
    st.title("📝 Vision AI Grader")
    st.info("Watch a 30s ad to unlock your grading...")
    
    file = st.file_uploader("Upload Exam Paper (Image/PDF)", type=['png', 'jpg', 'jpeg'])
    email_input = st.text_input("Enter Email to receive results")

    if file and st.button("Start AI Grading"):
        with st.spinner("AI is analyzing your handwriting..."):
            result = run_vision_analysis(file)
            st.session_state.focus_points += result['points']
            st.success(f"Graded: {result['score']}%! You earned {result['points']} points.")
            st.write(result['feedback'])
            
            if email_input:
                if send_email_report(email_input, result['score'], result['feedback']):
                    st.toast("✅ Results sent to your email!")

elif menu == "Focus Time":
    st.title("⏱️ Focus Time Challenge")
    st.markdown('<div class="focus-container">', unsafe_allow_html=True)
    
    placeholder = st.empty()
    if st.button("Start 15min Session"):
        st.session_state.is_running = True
        for i in range(900, 0, -1):
            mins, secs = divmod(i, 60)
            placeholder.markdown(f'<div class="big-clock">{mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
            time.sleep(1)
            # Every 15 mins (at end)
            if i == 1:
                st.session_state.focus_points += 5
                st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Subscription":
    st.title("💎 Upgrade to PRO")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="plan-card"><div class="price-tag">$0</div><p>Ad-Supported</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="plan-card"><div class="price-tag">$14.99</div><p>Unlimited AI & No Ads</p></div>', unsafe_allow_html=True)
