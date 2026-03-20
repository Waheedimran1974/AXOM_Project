import streamlit as st
from google import genai
import pandas as pd
import os
import smtplib
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from email.message import EmailMessage
import io
import json
from pdf2image import convert_from_bytes

# --- 1. HUD STYLING ---
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
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-2.5-flash"
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

# Unified Handwriting & Marking Engine
def mark_script(image, marks_data):
    """
    Applies your font (ticks/crosses/comments) based on AI coordinate data.
    """
    draw = ImageDraw.Draw(image)
    try:
        # Load your specific writing font
        font = ImageFont.truetype("ibrahim_handwriting.ttf", 60)
    except:
        font = ImageFont.load_default()

    # Red Ink for Examiner
    ink_color = (239, 68, 68) # Standard examiner red

    # Marks data is expected to be a list of dicts: [{'type': 'tick', 'x': 100, 'y': 200, 'comment': 'Good point'}]
    for mark in marks_data:
        x, y = mark['x'], mark['y']
        
        # 1. Place the Icon
        if mark['type'] == 'tick':
            draw.text((x, y), "✓", fill=ink_color, font=font)
        elif mark['type'] == 'cross':
            draw.text((x, y), "✕", fill=ink_color, font=font)
        
        # 2. Add any associated comment right next to the icon
        if 'comment' in mark:
            # Shift comment slightly to the right of the icon
            draw.text((x + 70, y), f"- {mark['comment']}", fill=ink_color, font=font)
            
    return image

def archive_data(email, feedback):
    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), email, "MARKED", feedback]], 
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
            if st.button("RUN FULL NEURAL ANALYSIS"):
                with st.spinner("EXAMINING ENTIRE DOCUMENT..."):
                    file_bytes = uploaded_file.read()
                    all_feedback = []
                    
                    try:
                        # 1. Convert ALL pages to images
                        if uploaded_file.type == "application/pdf":
                            pages = convert_from_bytes(file_bytes)
                        else:
                            pages = [Image.open(io.BytesIO(file_bytes)).convert("RGB")]
                        
                        # 2. Loop through every page
                        for i, page_img in enumerate(pages):
                            st.subheader(f"Analyzing Page {i+1}...")
                            
                            # AI Analysis to generate COORDINATE-BASED markings
                            prompt = f"""
                            You are a strict examiner for IGCSE Biology/Physics. Mark page {i+1} of this script.
                            Focus on scientific diagrams and text.
                            Return your marking in a precise JSON list of dictionaries like this example format:
                            [{{'type': 'tick', 'x': 500, 'y': 300, 'comment': 'Correct label for Mitochondria'}}, {{'type': 'cross', 'x': 700, 'y': 450, 'comment': 'Units missing'}}]
                            Provide the (x,y) coordinates where the icon should be drawn on the original image (0,0 is top left). 
                            If the entire page is blank, return an empty list: [].
                            Return ONLY the JSON list, no introductory text.
                            """
                            
                            response = client.models.generate_content(
                                model=MODEL_ID,
                                contents=[prompt, page_img]
                            )
                            page_ai_data_str = response.text
                            all_feedback.append(f"Page {i+1} Data: {page_ai_data_str}")
                            
                            try:
                                # Clean and Parse JSON from Gemini
                                clean_json_str = page_ai_data_str.strip('`').replace('json', '').strip()
                                marks_data = json.loads(clean_json_str)
                                
                                # 3. Draw your font and icons onto this page
                                marked_page = mark_script(page_img, marks_data)
                                st.image(marked_page, caption=f"EXAMINER OVERLAY: PAGE {i+1}")
                                
                            except json.JSONDecodeError:
                                st.warning(f"Failed to parse AI data for page {i+1}. Skipping visual marks.")
                        
                        # 4. Final Archive
                        full_report = "\n".join(all_feedback)
                        archive_data(st.session_state.user_email, full_report)
                        st.success("FULL DOCUMENT ARCHIVED")
                        
                    except Exception as e:
                        st.error(f"SYSTEM ERROR: {str(e)}")

    with tab2:
        st.header("SESSION LOGS")
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_data = df[df['Email'] == st.session_state.user_email]
            
            if not user_data.empty:
                csv_report = user_data.to_csv(index=False).encode('utf-8')
                st.download_button("DOWNLOAD FULL REPORT", csv_report, "AXOM_Full_Log.csv", "text/csv")
                
                for _, row in user_data.tail(5).iterrows():
                    with st.expander(f"Session: {row['Date']}"):
                        st.write(row['Feedback'])
            else:
                st.info("NO ARCHIVED DATA FOUND")
        else:
            st.warning("ARCHIVE SYSTEM EMPTY")
