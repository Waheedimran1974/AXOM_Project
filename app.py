import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
import smtplib
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from email.message import EmailMessage

# --- 1. HUD STYLING (FUTURE ERA) ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle, #00122e 0%, #00050d 100%);
        color: #00d4ff;
        font-family: 'Courier New', monospace;
    }
    .future-frame {
        border: 2px solid #00d4ff;
        border-radius: 10px;
        padding: 40px;
        background: rgba(0, 20, 46, 0.9);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
        text-align: center;
    }
    .stButton>button {
        width: 100%;
        background: transparent;
        color: #00d4ff;
        border: 1px solid #00d4ff;
        border-radius: 5px;
        transition: 0.3s;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .stButton>button:hover {
        background: #00d4ff;
        color: #000;
        box-shadow: 0 0 15px #00d4ff;
    }
    .stTextInput>div>div>input {
        background: rgba(0, 0, 0, 0.5);
        color: #00d4ff;
        border: 1px solid #00d4ff;
    }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 10px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND ENGINES ---
genai.configure(api_key=st.secrets["GENAI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')
HISTORY_FILE = "axom_history.csv"

def send_neural_key(receiver_email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"AXOM NEURAL ACCESS KEY: {otp}\nINITIALIZING SECURE LINK...")
    msg['Subject'] = "AXOM | SECURE ACCESS KEY"
    msg['From'] = st.secrets["SENDER_EMAIL"]
    msg['To'] = receiver_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SENDER_EMAIL"], st.secrets["APP_PASSWORD"])
            server.send_message(msg)
        return otp
    except:
        return None

def apply_handwriting(image, text, x, y):
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("ibrahim_handwriting.ttf", 45)
    except:
        font = ImageFont.load_default()
    draw.text((x, y), text, fill=(255, 0, 85), font=font) 
    return image

def archive_data(email, score, feedback):
    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), email, score, feedback]], 
                             columns=["Date", "Email", "Score", "Feedback"])
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
    else:
        df = new_entry
    df.to_csv(HISTORY_FILE, index=False)

# --- 3. SESSION LOGIC ---
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "identify"
    st.session_state.logged_in = False

# --- 4. INTERFACE ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        if st.session_state.auth_step == "identify":
            st.title("AXOM INTERFACE")
            email_in = st.text_input("INPUT EMAIL ID")
            if st.button("REQUEST NEURAL KEY"):
                with st.spinner("TRANSMITTING..."):
                    otp = send_neural_key(email_in)
                    if otp:
                        st.session_state.generated_otp = otp
                        st.session_state.temp_email = email_in
                        st.session_state.auth_step = "verify"
                        st.rerun()
                    else:
                        st.error("COMMS ERROR: CHECK CONFIGURATION")

        elif st.session_state.auth_step == "verify":
            st.title("VERIFY LINK")
            st.write(f"KEY SENT TO: {st.session_state.temp_email}")
            otp_in = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("INITIALIZE SESSION"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.session_state.user_email = st.session_state.temp_email
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: INVALID KEY")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.sidebar.title("AXOM STATUS")
    st.sidebar.write(f"USER: {st.session_state.user_email}")
    if st.sidebar.button("TERMINATE SESSION"):
        st.session_state.logged_in = False
        st.session_state.auth_step = "identify"
        st.rerun()

    tab1, tab2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with tab1:
        st.header("DOCUMENT SCAN")
        uploaded_file = st.file_uploader("UPLOAD SCRIPT", type=['png', 'jpg', 'jpeg', 'pdf'])
        if uploaded_file:
            if st.button("RUN NEURAL ANALYSIS"):
                with st.spinner("ANALYZING WITH GEMINI 2.0 FLASH..."):
                    img = Image.open(uploaded_file).convert("RGB")
                    response = model.generate_content(["Mark this English paper. Give score/10 and feedback.", img])
                    ai_feedback = response.text
                    marked_img = apply_handwriting(img, "NEURAL MARK: " + ai_feedback[:25], 50, 50)
                    archive_data(st.session_state.user_email, "PROCESSED", ai_feedback)
                    st.image(marked_img, caption="NEURAL OVERLAY RESULT")
                    st.success("SESSION DATA ARCHIVED")

    with tab2:
        st.header("SESSION LOGS")
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_data = df[df['Email'] == st.session_state.user_email]
            if not user_data.empty:
                for _, row in user_data.tail(10).iterrows():
                    st.markdown(f"""
                    <div style="border: 1px solid #00d4ff; padding: 15px; border-radius: 5px; margin-bottom: 10px; background: rgba(0, 212, 255, 0.05);">
                        <span style="color: #00d4ff; font-size: 0.8rem;">{row['Date']}</span><br>
                        <span style="color: #ffffff;">{row['Feedback']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("NO ARCHIVED DATA FOUND")
        else:
            st.warning("ARCHIVE SYSTEM EMPTY")
