import streamlit as st
import smtplib
import random
import re
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. UI CONFIGURATION ---
st.set_page_config(page_title="AXOM | Secure Access", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { 
        background: #00E5FF !important; color: #000 !important; 
        font-weight: 600 !important; border-radius: 2px !important; width: 100%;
    }
    .auth-container { max-width: 400px; margin: 0 auto; padding-top: 100px; }
    .accent { color: #00E5FF; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 1
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = None
if 'user_email' not in st.session_state: st.session_state.user_email = ""

# --- 3. SECURE EMAIL ENGINE ---
def send_otp_email(receiver_email):
    # Pulling from st.secrets to keep credentials safe from hackers
    smtp_user = st.secrets["SMTP_EMAIL"]
    smtp_pass = st.secrets["SMTP_PASS"]
    
    otp = str(random.randint(100000, 999999))
    st.session_state.generated_otp = otp

    msg = MIMEMultipart()
    msg['From'] = f"AXOM Security <{smtp_user}>"
    msg['To'] = receiver_email
    msg['Subject'] = f"{otp} is your AXOM Access Password"

    body = f"Welcome to AXOM.\n\nYour temporary access password is: {otp}\n\nThis code will expire shortly."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail System Error: {e}")
        return False

# --- 4. LOGIN INTERFACE ---
def login_screen():
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>AXOM <span class='accent'>v1.0</span></h1>", unsafe_allow_html=True)
    
    if st.session_state.auth_step == 1:
        st.write("Enter your email to receive an access password.")
        email = st.text_input("Email Address", placeholder="student@example.com")
        if st.button("Send Access Password"):
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                with st.spinner("Sending secure code..."):
                    if send_otp_email(email):
                        st.session_state.user_email = email
                        st.session_state.auth_step = 2
                        st.rerun()
            else:
                st.error("Please enter a valid email address.")

    elif st.session_state.auth_step == 2:
        st.write(f"Access password sent to: **{st.session_state.user_email}**")
        user_otp = st.text_input("Enter 6-Digit Password", placeholder="000000")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify & Enter"):
                if user_otp == st.session_state.generated_otp:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Please check your email.")
        with col2:
            if st.button("Back"):
                st.session_state.auth_step = 1
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. APP ROUTING ---
if not st.session_state.authenticated:
    login_screen()
else:
    # --- PRO DASHBOARD STARTS HERE ---
    with st.sidebar:
        st.markdown(f"<p style='color:#00E5FF'>User: {st.session_state.user_email}</p>", unsafe_allow_html=True)
        menu = st.radio("Navigation", ["Dashboard", "Vision AI Grader", "Monetary Prize"])
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.auth_step = 1
            st.rerun()

    if menu == "Dashboard":
        st.title("Performance Dashboard")
        st.write("Welcome back to your high-intensity focus environment.")
        
    elif menu == "Monetary Prize":
        st.subheader("Annual Excellence Grant")
        st.markdown("""
            <div style="background:#111; border:1px solid #00E5FF; padding:40px; border-radius:4px; text-align:center;">
                <span style="background:#00E5FF; color:#000; padding:2px 10px; font-weight:bold; font-size:12px;">COMING SOON</span>
                <h1 style="font-size:60px;">$5,000.00</h1>
                <p>Awarded for verified focus and academic excellence.</p>
            </div>
        """, unsafe_allow_html=True)
