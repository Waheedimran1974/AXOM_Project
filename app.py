import streamlit as st
import google.generativeai as genai
import re
import io
import base64
import time
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes

# ==========================================
# 1. ARCHITECTURAL UI CONFIG (META-DESIGN)
# ==========================================
st.set_page_config(
    page_title="AXOM // GLOBAL GATEWAY", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

def inject_cyber_styles():
    st.markdown("""
        <style>
        /* The Obsidian Background */
        .stApp {
            background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
            color: #f8fafc;
        }

        /* Glassmorphism Auth Card */
        .auth-container {
            max-width: 480px;
            margin: 80px auto;
            padding: 50px;
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-radius: 4px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 20px rgba(212, 175, 55, 0.1);
            text-align: center;
        }

        /* The "AXOM" Brand Glow */
        .brand-logo {
            font-size: 3.5rem;
            font-weight: 900;
            color: #D4AF37;
            letter-spacing: 12px;
            text-shadow: 0 0 15px rgba(212, 175, 55, 0.5);
            margin-bottom: 0;
        }

        /* High-Performance Neon Buttons */
        .stButton>button {
            width: 100% !important;
            background: transparent !important;
            color: #D4AF37 !important;
            border: 1px solid #D4AF37 !important;
            padding: 15px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            transition: 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }

        .stButton>button:hover {
            background: #D4AF37 !important;
            color: #020617 !important;
            box-shadow: 0 0 30px rgba(212, 175, 55, 0.6) !important;
            transform: translateY(-2px);
        }

        /* Cyber-Text Inputs */
        input {
            background: rgba(0, 0, 0, 0.3) !important;
            border: 1px solid #1e293b !important;
            color: #f8fafc !important;
        }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SESSION & AUTH LOGIC (THE "ENGINE")
# ==========================================
def initialize_session():
    if 'access_granted' not in st.session_state:
        st.session_state.access_granted = False
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "GATE"
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = None

def gateway_interface():
    inject_cyber_styles()
    
    # We use columns to perfectly center the "Obsidian Card"
    _, col, _ = st.columns([1, 1.5, 1])
    
    with col:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.markdown('<h1 class="brand-logo">AXOM</h1>', unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-size: 0.8rem; margin-bottom: 40px;">// SECURE EXAM NEURAL LINK v3.0 //</p>', unsafe_allow_html=True)
        
        tab_sign_in, tab_sign_up = st.tabs(["SIGN IN", "CREATE ACCOUNT"])
        
        with tab_sign_in:
            st.write("<br>", unsafe_allow_html=True)
            email = st.text_input("UPLINK ID (Email)", key="login_email")
            pwd = st.text_input("ACCESS KEY", type="password", key="login_pwd")
            
            if st.button("INITIALIZE SESSION", key="btn_login"):
                if email and pwd: # You can add your specific validation here
                    with st.spinner("SYNCHRONIZING WITH CLOUD..."):
                        time.sleep(1.5)
                        st.session_state.access_granted = True
                        st.session_state.user_profile = {"email": email}
                        st.rerun()
                else:
                    st.error("CREDENTIALS REQUIRED")

        with tab_sign_up:
            st.write("<br>", unsafe_allow_html=True)
            new_name = st.text_input("FULL LEGAL NAME")
            new_email = st.text_input("PRIMARY EMAIL")
            new_pwd = st.text_input("CREATE PASSWORD", type="password")
            
            if st.button("REGISTER NEURAL ID", key="btn_signup"):
                st.success("ACCOUNT CREATED. PROCEED TO SIGN IN.")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. THE CORE COMMAND CENTER (POST-LOGIN)
# ==========================================
def core_dashboard():
    inject_cyber_styles()
    
    # Professional Header (Glassmorphic)
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 20px; border-bottom: 1px solid rgba(212, 175, 55, 0.3); background: rgba(15, 23, 42, 0.8);">
            <h2 style="color: #D4AF37; margin:0; letter-spacing: 5px;">AXOM // CMD</h2>
            <div style="text-align: right;">
                <span style="color: #39FF14; font-size: 0.7rem;">● UPLINK ACTIVE</span><br>
                <span style="font-size: 0.8rem;">{st.session_state.user_profile['email']}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar Navigation (Clean & Minimal)
    with st.sidebar:
        st.markdown("<h3 style='color: #D4AF37;'>NAVIGATION</h3>", unsafe_allow_html=True)
        if st.button("📄 PAPER CHECKER"): st.session_state.current_view = "CHECKER"
        if st.button("📊 ANALYTICS"): st.session_state.current_view = "REPORTS"
        if st.button("🤖 AI MENTOR"): st.session_state.current_view = "AI"
        st.divider()
        if st.button("LOGOUT"):
            st.session_state.access_granted = False
            st.rerun()

    # Routing
    if st.session_state.current_view == "CHECKER":
        run_paper_checker_module()
    else:
        st.info("Select a protocol from the sidebar.")

def run_paper_checker_module():
    st.markdown("<h2 style='color: #D4AF37;'>NEURAL PAPER CHECKER</h2>", unsafe_allow_html=True)
    # [Insert your Marking Vision code here - the draw_cyber_marks function]
    st.write("Awaiting script upload...")

# ==========================================
# EXECUTION BOOTLOADER
# ==========================================
initialize_session()

if not st.session_state.access_granted:
    gateway_interface()
else:
    core_dashboard()
