import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Setup with the 2026 Stable Model
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
    # UPDATED: Using the new stable 2.5 Flash engine
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"Setup Error: {e}")

st.set_page_config(page_title="AXOM Global", layout="wide")
st.title("🚀 AXOM: Senior Examiner AI (v2.5)")

# 2. Upload Logic
uploaded_file = st.file_uploader("Upload Exam PDF or Image", type=['pdf', 'png', 'jpg', 'jpeg'])

if uploaded_file:
    st.sidebar.success("Document detected by AXOM.")
    if st.button("RUN GLOBAL ANALYSIS"):
        with st.spinner("Accessing Gemini 2.5 Intelligence..."):
            try:
                # Prepare content
                if uploaded_file.type == "application/pdf":
                    content = [{"mime_type": "application/pdf", "data": uploaded_file.read()}]
                else:
                    img = Image.open(uploaded_file)
                    content = [img]
                
                # Professional Senior Examiner Prompt
                prompt = "You are a Senior IGCSE Examiner. Analyze this student paper. Give a total score and 3 tips for A*."
                
                # The AI Call
                response = model.generate_content([prompt] + content)
                st.markdown("### 📊 Examiner Report")
                st.write(response.text)
                st.success("Analysis Complete. Profit: $0.998")
                
            except Exception as e:
                st.error(f"AI Engine Report: {e}")
                st.info("Technical Tip: Ensure your API Key has 'Gemini 2.5' enabled in Google AI Studio.")
system_prompt = """
IDENTITY:
You are the AXOM Senior Examiner. Your voice is that of Waheed Imran. 
You are marking professional exam papers.

RULES:
1. ANCHORING: Stick 100% to the provided mark scheme.
2. CRITIQUE: Focus on "Negative Marking"—find what is missing.
3. VISUALS: Identify specific coordinates for "Red Pen" annotations.
4. TONE: Professional, concise, and academic. No AI fluff.

MARKING PROCESS:
- Step 1: Scan for keywords from the mark scheme.
- Step 2: Evaluate grammar/syntax against the specific Band descriptors.
- Step 3: Calculate the final mark based on the threshold.
- Step 4: Generate 'Red Pen' margin notes.
"""
{
  "action": "strike_through",
  "color": "red",
  "text": "swimmed",
  "comment": "Irregular verb error. Use 'swam'. Band 2 penalty applied."
}
