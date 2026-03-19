import streamlit as st
import os
import pymupdf  # PyMuPDF
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load API Key from .env or Streamlit Secrets
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

# Initialize Gemini Client (2026 SDK Style)
client = genai.Client(api_key=GEMINI_API_KEY)

# --- App Configuration ---
st.set_page_config(page_title="EduConnect AI", layout="wide")

def extract_text_from_pdf(uploaded_file):
    """Extracts text using the latest PyMuPDF methods."""
    doc = pymupdf.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def generate_lesson_plan(content):
    """Uses Gemini 3.1 Flash to generate a structured lesson plan."""
    prompt = f"""
    As an expert educator, analyze the following text and create a structured lesson plan.
    Include: 
    1. Learning Objectives
    2. Key Vocabulary
    3. 5 Discussion Questions
    4. A short summary for students.
    
    Content: {content[:5000]} 
    """
    response = client.models.generate_content(
        model="gemini-2.0-flash", # Latest stable production model
        contents=prompt
    )
    return response.text

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "AI Lesson Planner", "Virtual Classroom"])

# --- Dashboard ---
if page == "Dashboard":
    st.title("Welcome to EduConnect AI")
    st.write("Manage your teaching materials and connect with students in one place.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Upcoming Lessons", value="4")
    with col2:
        st.metric(label="Active Projects", value="AXOM / AXON")

# --- AI Lesson Planner ---
elif page == "AI Lesson Planner":
    st.title("AI-Powered Lesson Planner")
    uploaded_file = st.file_file_uploader("Upload a PDF textbook or article", type="pdf")

    if uploaded_file:
        with st.spinner("Analyzing document..."):
            raw_text = extract_text_from_pdf(uploaded_file)
            lesson_plan = generate_lesson_plan(raw_text)
            
            st.subheader("Generated Lesson Plan")
            st.markdown(lesson_plan)
            
            st.download_button("Download Plan", lesson_plan, file_name="lesson_plan.txt")

# --- Virtual Classroom (Jitsi Integration) ---
elif page == "Virtual Classroom":
    st.title("Virtual Classroom")
    room_name = st.text_input("Enter Room Name", value="Global_Classroom_2026")
    user_name = st.text_input("Your Name", value="Teacher")

    if st.button("Launch Classroom"):
        # Embedding Jitsi Meet via IFrame
        jitsi_url = f"https://meet.jit.si/{room_name}#config.startWithVideoMuted=true&userInfo.displayName='{user_name}'"
        
        st.components.v1.iframe(jitsi_url, height=600, scrolling=True)
        st.info("Tip: Share the room name with your students to have them join.")

# --- Footer ---
st.markdown("---")
st.caption("Powered by Gemini 3.1 & Streamlit 1.55")
