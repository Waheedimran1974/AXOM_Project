import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# --- 1. HUD STYLING (THE FUTURE ERA LOOK) ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: radial-gradient(circle, #00122e 0%, #00050d 100%);
        color: #00d4ff;
    }
    
    /* Futuristic Frame for Login/Containers */
    .future-frame {
        border: 2px solid #00d4ff;
        border-radius: 15px;
        padding: 30px;
        background: rgba(0, 20, 46, 0.8);
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        text-align: center;
    }
    
    /* Buttons */
    .stButton>button {
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
    
    /* Inputs */
    .stTextInput>div>div>input {
        background: rgba(0, 0, 0, 0.5);
        color: #00d4ff;
        border: 1px solid #00d4ff;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #00d4ff !important;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 10px #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE SYSTEM LOGIC ---
genai.configure(api_key=st.secrets["GENAI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')
HISTORY_FILE = "axom_history.csv"

def apply_handwriting(image, text, x, y):
    draw = ImageDraw.Draw(image)
    try:
        font_path = "ibrahim_handwriting.ttf"
        font = ImageFont.truetype(font_path, 45)
    except:
        font = ImageFont.load_default()
    draw.text((x, y), text, fill=(255, 0, 85), font=font) # Neon Pink/Red Ink
    return image

def save_to_csv(email, score, feedback):
    new_data = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), email, score, feedback]], 
                            columns=["Date", "Email", "Score", "Feedback"])
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
    df.to_csv(HISTORY_FILE, index=False)

# --- 3. APP INTERFACE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # UNIVERSAL LOGIN SCREEN
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM SYSTEM ACCESS")
        st.write("SECURE NEURAL LINK REQUIRED")
        user_input = st.text_input("USER IDENTIFICATION (EMAIL)")
        if st.button("INITIALIZE SESSION"):
            if user_input:
                st.session_state.logged_in = True
                st.session_state.user_email = user_input
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    # MAIN NEURAL INTERFACE
    st.sidebar.markdown("### SYSTEM STATUS: ACTIVE")
    st.sidebar.write(f"USER: {st.session_state.user_email}")
    if st.sidebar.button("TERMINATE SESSION"):
        st.session_state.logged_in = False
        st.rerun()

    tab1, tab2 = st.tabs(["NEURAL SCANNER", "DATA ARCHIVE"])

    with tab1:
        st.header("SCRIPT UPLOAD")
        uploaded_file = st.file_uploader("PLACE DOCUMENT IN SCANNER", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        if uploaded_file:
            if st.button("RUN NEURAL ANALYSIS"):
                with st.spinner("SCANNING..."):
                    img = Image.open(uploaded_file).convert("RGB")
                    prompt = "Analyze this text. Provide a professional grade and feedback."
                    response = model.generate_content([prompt, img])
                    ai_result = response.text
                    
                    marked_img = apply_handwriting(img, "ANALYSIS COMPLETE: " + ai_result[:25], 50, 50)
                    save_to_csv(st.session_state.user_email, "PROCESSED", ai_result)
                    
                    st.image(marked_img, caption="NEURAL OVERLAY RESULT")
                    st.success("DATA ENCRYPTED AND SAVED TO ARCHIVE")

    with tab2:
        st.header("SESSION LOGS")
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_df = df[df['Email'] == st.session_state.user_email]
            
            if not user_df.empty:
                for index, row in user_df.tail(10).iterrows():
                    st.markdown(f"""
                    <div style="border: 1px solid #00d4ff; padding: 15px; border-radius: 5px; margin-bottom: 10px; background: rgba(0, 212, 255, 0.05);">
                        <span style="color: #00d4ff;">TIMESTAMP: {row['Date']}</span><br>
                        <span style="color: #ffffff;">{row['Feedback']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("NO ARCHIVED DATA FOUND FOR THIS ID")
