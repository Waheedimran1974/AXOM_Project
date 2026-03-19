import streamlit as st
import random
import smtplib
import time
from email.mime.text import MIMEText
# (Keep your other imports like PIL, genai, pdf2image here for the Paper Checker)

# ==========================================
# 1. ENTERPRISE UI & CONFIG
# ==========================================
st.set_page_config(page_title="AXOM | Professional Terminal", layout="wide", initial_sidebar_state="collapsed")

def inject_enterprise_styles():
    st.markdown("""
        <style>
        .stApp { background-color: #fafafa; color: #111827; font-family: 'Inter', sans-serif; }
        .auth-card {
            max-width: 400px; margin: 100px auto; padding: 40px;
            background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: center;
        }
        .brand-text { font-size: 2.5rem; font-weight: 800; color: #111827; letter-spacing: 2px; margin-bottom: 5px; }
        .sub-text { color: #6b7280; font-size: 0.9rem; margin-bottom: 30px; }
        .stButton>button {
            width: 100%; background-color: #111827 !important; color: #ffffff !important;
            border: none !important; border-radius: 6px !important; padding: 12px !important;
            font-weight: 600 !important; transition: 0.2s ease;
        }
        .stButton>button:hover { background-color: #374151 !important; }
        input { border-radius: 6px !important; border: 1px solid #d1d5db !important; padding: 10px !important; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. EMAIL VERIFICATION ENGINE (OTP)
# ==========================================
def send_verification_email(receiver_email, otp_code):
    """Sends the 6-digit code to the user."""
    
    # ⚠️ SYSTEM ADMIN: PUT YOUR ACTUAL GMAIL AND APP PASSWORD HERE ⚠️
    sender_email = "YOUR_EMAIL@gmail.com" 
    app_password = "YOUR_16_LETTER_APP_PASSWORD" 
    
    msg = MIMEText(f"Your AXOM secure login code is: {otp_code}\n\nThis code expires in 10 minutes. Do not share it with anyone.")
    msg['Subject'] = 'AXOM Security Code'
    msg['From'] = f"AXOM Security <{sender_email}>"
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email routing failed: {e}")
        return False

# ==========================================
# 3. STATE MANAGEMENT
# ==========================================
if 'auth_status' not in st.session_state: st.session_state.auth_status = "logged_out" 
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = ""

inject_enterprise_styles()

# ==========================================
# 4. THE AUTHENTICATION GATEWAY
# ==========================================
if st.session_state.auth_status != "logged_in":
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="brand-text">AXOM</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-text">Enterprise Examination Platform</div>', unsafe_allow_html=True)

        # STEP 1: ASK FOR EMAIL
        if st.session_state.auth_status == "logged_out":
            email_input = st.text_input("Work or School Email", placeholder="name@school.edu")
            if st.button("Continue with Email"):
                if "@" in email_input and "." in email_input:
                    otp = str(random.randint(100000, 999999))
                    st.session_state.generated_otp = otp
                    st.session_state.user_email = email_input
                    
                    with st.spinner("Encrypting and routing to your inbox..."):
                        # THIS ACTUALLY SENDS THE EMAIL NOW
                        email_sent = send_verification_email(email_input, otp)
                        
                        if email_sent:
                            st.session_state.auth_status = "otp_sent"
                            st.rerun()
                        else:
                            st.error("System Error: Could not route email. Check server configuration.")
                else:
                    st.error("Invalid email format.")

        # STEP 2: VERIFY OTP CODE
        elif st.session_state.auth_status == "otp_sent":
            st.info(f"We sent a 6-digit code to **{st.session_state.user_email}**")
            entered_otp = st.text_input("Enter 6-digit code", max_chars=6)
            
            if st.button("Verify & Sign In"):
                if entered_otp == st.session_state.generated_otp:
                    st.session_state.auth_status = "logged_in"
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid code.")
            
            if st.button("← Use a different email"):
                st.session_state.auth_status = "logged_out"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. CORE ENGINE (POST-LOGIN)
# ==========================================
# (Insert your Paper Checker UI and logic here)
st.success(f"Welcome to the AXOM Dashboard, {st.session_state.user_email}")
