import streamlit as st
import smtplib
import random
import google.generativeai as genai
from email.message import EmailMessage

# --- HUD STYLING (THE FUTURE ERA LOOK) ---
st.markdown("""
    <style>
    .stApp { background: #00050d; color: #00d4ff; }
    .future-frame {
        border: 2px solid #00d4ff;
        border-radius: 10px;
        padding: 40px;
        background: rgba(0, 20, 46, 0.9);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
    }
    .stButton>button { width: 100%; border: 1px solid #00d4ff; background: transparent; color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- OTP ENGINE ---
def send_neural_key(receiver_email):
    otp = str(random.randint(100000, 999999))
    msg = EmailMessage()
    msg.set_content(f"Your AXOM Neural Access Key is: {otp}")
    msg['Subject'] = "AXOM | SECURE ACCESS KEY"
    msg['From'] = st.secrets["SENDER_EMAIL"]
    msg['To'] = receiver_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(st.secrets["SENDER_EMAIL"], st.secrets["APP_PASSWORD"])
        server.send_message(msg)
        server.quit()
        return otp
    except Exception as e:
        st.error("COMMS FAILURE: UNABLE TO SEND KEY")
        return None

# --- LOGIN INTERFACE ---
if "auth_step" not in st.session_state:
    st.session_state.auth_step = "identify"
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        
        # STEP 1: Identification
        if st.session_state.auth_step == "identify":
            st.title("AXOM INTERFACE")
            email = st.text_input("INPUT USER ID (EMAIL)")
            if st.button("REQUEST NEURAL KEY"):
                with st.spinner("TRANSMITTING..."):
                    key = send_neural_key(email)
                    if key:
                        st.session_state.generated_key = key
                        st.session_state.temp_email = email
                        st.session_state.auth_step = "verify"
                        st.rerun()

        # STEP 2: Verification
        elif st.session_state.auth_step == "verify":
            st.title("VERIFY IDENTITY")
            st.write(f"KEY SENT TO: {st.session_state.temp_email}")
            user_key = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("INITIALIZE LINK"):
                if user_key == st.session_state.generated_key:
                    st.session_state.logged_in = True
                    st.session_state.user_email = st.session_state.temp_email
                    st.success("LINK ESTABLISHED")
                    st.rerun()
                else:
                    st.error("INVALID KEY: ACCESS DENIED")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- REST OF YOUR APP (Marking/History) ---
    st.title("AXOM | MAIN TERMINAL")
    st.write(f"LINK ACTIVE: {st.session_state.user_email}")
    if st.sidebar.button("TERMINATE SESSION"):
        st.session_state.logged_in = False
        st.session_state.auth_step = "identify"
        st.rerun()
