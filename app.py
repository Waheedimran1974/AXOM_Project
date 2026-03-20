import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 1. CONFIGURATION
genai.configure(api_key=st.secrets["GENAI_API_KEY"])
HISTORY_FILE = "axom_history.csv"

# 2. HANDWRITING ENGINE
def apply_custom_ink(draw, text, x, y, color):
    try:
        font_path = os.path.join(os.path.dirname(__file__), "ibrahim_handwriting.ttf")
        font = ImageFont.truetype(font_path, 40)
    except:
        font = ImageFont.load_default()
    
    # Draw text with a slight shadow for realism
    draw.text((x + 2, y + 2), text, fill="#00000020", font=font)
    draw.text((x, y), text, fill=color, font=font)

# 3. HISTORY LOGIC
def log_result(email, score, feedback):
    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), email, score, feedback]], 
                             columns=["Date", "Email", "Score", "Feedback"])
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
    else:
        df = new_entry
    df.to_csv(HISTORY_FILE, index=False)

# 4. USER INTERFACE
st.title("AXOM | Neural Examiner")

# Sidebar Login
with st.sidebar:
    st.header("Teacher Login")
    user_email = st.text_input("Enter Email", placeholder="name@example.com")
    is_logged_in = st.button("Access AXOM")

if is_logged_in:
    tab1, tab2 = st.tabs(["Mark Paper", "History & Flashcards"])

    with tab1:
        uploaded_file = st.file_uploader("Upload Student Script", type=['png', 'jpg', 'pdf'])
        if uploaded_file and st.button("Process with AI"):
            img = Image.open(uploaded_file).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            # Simulated AI Marking (Replace with your Gemini call)
            apply_custom_ink(draw, "Excellent work, Ibrahim!", 100, 100, "#dc2626")
            log_result(user_email, "8.5/10", "Strong grammar, watch spelling.")
            
            st.image(img, caption="Marked by AXOM")
            st.success("Result saved to history!")

    with tab2:
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            user_data = df[df['Email'] == user_email]
            
            st.subheader("Flashcard Revision")
            for _, row in user_data.tail(3).iterrows():
                st.info(f"**{row['Date']}** | Score: {row['Score']}\n\n{row['Feedback']}")
        else:
            st.write("No history yet.")
