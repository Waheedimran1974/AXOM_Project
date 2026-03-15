import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Setup the Secret and Model
try:
    # Use the specific key name from your Streamlit Secrets
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
    # Using the most stable direct model name
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Configuration Error: {e}")

st.set_page_config(page_title="AXOM Global", layout="wide")
st.title("🚀 AXOM: Senior Examiner AI")

# 2. File Upload Logic
uploaded_file = st.file_uploader("Upload Exam PDF or Image", type=['pdf', 'png', 'jpg', 'jpeg'])

if uploaded_file:
    st.success("File received by AXOM Engine.")
    if st.button("RUN SENIOR EXAMINER ANALYSIS"):
        with st.spinner("Analyzing against Cambridge standards..."):
            try:
                # Prepare content based on file type
                if uploaded_file.type == "application/pdf":
                    content = [{"mime_type": "application/pdf", "data": uploaded_file.read()}]
                else:
                    img = Image.open(uploaded_file)
                    content = [img]
                
                # The Professional Grading Prompt
                prompt = "You are a Senior IGCSE Examiner. Provide a score and 3 A* tips."
                
                # The AI Call
                response = model.generate_content([prompt] + content)
                st.markdown("### 📊 Examiner Report")
                st.write(response.text)
                st.success("Profit Logged: $0.998")
                
            except Exception as e:
                # This catches if it's still a 404 or a key issue
                st.error(f"AI Engine Report: {e}")
