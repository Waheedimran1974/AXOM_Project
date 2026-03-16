import streamlit as st
import google.generativeai as genai
from PIL import Image
import streamlit as st
import fitz  # This is the PyMuPDF "Red Pen" tool
import time
import json
# (You will also import your Gemini API tool here)
def apply_harsh_marking(original_pdf, ai_json_instructions):
    doc = fitz.open(stream=original_pdf.read(), filetype="pdf")
    
    for action in ai_json_instructions:
        # Loop through every page to find the error
        for page in doc:
            text_instances = page.search_for(action["text"])
            for inst in text_instances:
                if action["action"] == "strike_through":
                    # Draw Red Line
                    line_mid = (inst.y0 + inst.y1) / 2
                    page.add_line_annot(fitz.Point(inst.x0, line_mid), fitz.Point(inst.x1, line_mid))
                    # Add Harsh Comment
                    page.add_text_annot(fitz.Point(inst.x1 + 5, inst.y0), action["comment"])
    
    return doc.write() # Returns the "Red Pen" version
    HARSH_PROMPT = """
You are Senior Lecturer Waheed Imran in HARSH MODE. 
Identify grammar/vocab errors and output ONLY valid JSON in this format:
[{"action": "strike_through", "text": "wrong_word", "comment": "Brutal feedback"}]
"""

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
def get_system_prompt(mode):
    base_persona = "You are Senior Lecturer Waheed Imran."
    
    if mode == "Harsh Mode":
        return base_persona + """ 
        MODE: HARSH. 
        POLICY: Zero-tolerance for low-level vocabulary. 
        CRITIQUE: Be brutal and direct. 
        MARKING: Deductive only. Start at 100% and hunt for reasons to fail the candidate.
        """
    else:
        return base_persona + "MODE: Standard. Provide balanced feedback."
        st.title("AXOM: Senior Examiner Marking")

uploaded_file = st.file_uploader("Upload your IGCSE/IELTS Paper", type="pdf")

if uploaded_file:
    if st.button("Mark My Paper (Harsh Mode)"):
        # MISSION: THE AD-GATE
        with st.spinner("Harsh Mode Engaged... Reviewing for mediocrity..."):
            
            # This simulates your 30-second Ad-Gate timer
            time.sleep(30) 
            
            # 1. Send PDF to Gemini with HARSH_PROMPT
            # 2. Get the JSON back (Example below)
            mock_json = [{"action": "strike_through", "text": "swimmed", "comment": "Band 2 Error. Use 'swam'."}]
            
            # 3. Use the Painter to mark the PDF
            marked_pdf = apply_harsh_marking(uploaded_file, mock_json)
            
            # 4. Give the student the result
            st.success("Paper Marked. It was... disappointing.")
            st.download_button("Download Marked Paper", data=marked_pdf, file_name="AXOM_Marked.pdf")
