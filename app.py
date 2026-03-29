import streamlit as st
from google import genai
import os
import json
import re
import datetime
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import io

# --- 1. HUD & INTERFACE STYLING ---
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
    .plan-card:hover { transform: translateY(-10px); box-shadow: 0px 0px 30px rgba(0, 229, 255, 0.5); border-color: #ffffff; }
    .price-tag { font-size: 2.2rem; font-weight: 900; color: #ffffff; margin: 10px 0; }
    .stButton>button { width: 100%; background: linear-gradient(90deg, #00e5ff, #007bff) !important; color: #fff !important; font-weight: 900; border-radius: 4px; height: 50px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CLOUD & API INITIALIZATION ---
# Google Drive Setup
def get_drive_service():
    # Requires service_account info in st.secrets["google_drive"]
    info = json.loads(st.secrets["google_drive_json"])
    creds = service_account.Credentials.from_service_account_info(info)
    return build('drive', 'v3', credentials=creds)

def save_to_drive(file_bytes, filename, folder_id):
    service = get_drive_service()
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/pdf')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

# AI Client
try: 
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: 
    client = None

MODEL_ID = "gemini-2.5-flash"

# --- 3. SESSION INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "eval_history" not in st.session_state: st.session_state.eval_history = []
if "current_eval" not in st.session_state: st.session_state.current_eval = None
if "show_sub" not in st.session_state: st.session_state.show_sub = False

# --- 4. THE SUBSCRIPTION ENGINE (STRIPE INTEGRATED) ---
# Replace these with your actual Stripe Payment Links from your Stripe Dashboard
STRIPE_LINKS = {
    "WEEKLY": "https://buy.stripe.com/your_weekly_link",
    "MONTHLY": "https://buy.stripe.com/your_monthly_link",
    "YEARLY": "https://buy.stripe.com/your_yearly_link",
    "PAY_AS_YOU_GO": "https://buy.stripe.com/your_paygo_link"
}

def show_subscription_plans():
    st.title("SELECT ACCESS PLAN")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="plan-card"><h3>WEEKLY</h3><div class="price-tag">$4.99</div></div>', unsafe_allow_html=True)
        st.link_button("ACTIVATE WEEKLY", STRIPE_LINKS["WEEKLY"])

    with col2:
        st.markdown('<div class="plan-card"><h3>MONTHLY</h3><div class="price-tag">$14.99</div></div>', unsafe_allow_html=True)
        st.link_button("ACTIVATE MONTHLY", STRIPE_LINKS["MONTHLY"])

    with col3:
        st.markdown('<div class="plan-card"><h3>YEARLY</h3><div class="price-tag">$99.99</div></div>', unsafe_allow_html=True)
        st.link_button("ACTIVATE YEARLY", STRIPE_LINKS["YEARLY"])

    with col4:
        st.markdown('<div class="plan-card"><h3>PAY AS YOU GO</h3><div class="price-tag">$2.00</div></div>', unsafe_allow_html=True)
        st.link_button("BUY CREDITS", STRIPE_LINKS["PAY_AS_YOU_GO"])

# --- 5. MAIN APP FLOW ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.title("AXOM | VISION LOGIN")
        u_email = st.text_input("EMAIL")
        if st.button("INITIALIZE"):
            if "@" in u_email: 
                st.session_state.user_email = u_email
                st.session_state.logged_in = True
                st.rerun()
else:
    with st.sidebar:
        st.title("AXOM V6.8 PRO")
        if st.button("UPGRADE PLAN"): st.session_state.show_sub = True
        menu = st.radio("INTERFACE", ["NEURAL SCAN", "NEURAL ARCHIVE"])
        if st.button("EXIT"): 
            st.session_state.logged_in = False
            st.rerun()

    if st.session_state.show_sub:
        show_subscription_plans()
        if st.button("BACK"): 
            st.session_state.show_sub = False
            st.rerun()
    
    elif menu == "NEURAL SCAN":
        st.title("VISION AI SCANNER")
        up_s = st.file_uploader("UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        
        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("SAVING TO CLOUD & SCANNING..."):
                file_bytes = up_s.read()
                # 1. Save to Google Drive (Replace folder_id with your AXOM Archive folder ID)
                drive_id = save_to_drive(file_bytes, f"{st.session_state.user_email}_{datetime.datetime.now()}.pdf", "YOUR_DRIVE_FOLDER_ID")
                
                # 2. Process with AI
                raw_pages = convert_from_bytes(file_bytes)
                prompt = "Senior Examiner. Analyze script. Return JSON: {'page_marks':[], 'weaknesses':[]}"
                response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + raw_pages)
                
                st.success(f"File Archived to Drive (ID: {drive_id})")
                # Visual output logic follows...
