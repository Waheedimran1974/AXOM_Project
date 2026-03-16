import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
import json
import io

# ==========================================
# 1. CORE BRAIN: INITIALIZE AI
# ==========================================
@st.cache_resource
def load_axom_engine():
    try:
        if "GEMINI_KEY" not in st.secrets:
            return None, "Missing API Key in Streamlit Secrets."
        
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Stable 2.0 Flash engine
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model, None
    except Exception as e:
        return None, str(e)

model, error_message = load_axom_engine()

# ==========================================
# 2. THE HANDS: RED PEN PAINTER
# ==========================================
def apply_harsh_marking(uploaded_file, ai_json_instructions):
    try:
        input_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        
        for action in ai_json_instructions:
            for page in doc:
                text_instances = page.search_for(action["text"])
                for inst in text_instances:
                    if action["action"] == "strike_through":
                        line_mid = (inst.y0 + inst.y1) / 2
                        page.add_line_annot(fitz.Point(inst.x0, line_mid), fitz.Point(inst.x1, line_mid))
                        page.add_text_annot(fitz.Point(inst.x1 + 5, inst.y0), action["comment"])
        
        return doc.write()
    except:
        return None

# ==========================================
# 3. USER INTERFACE (UI)
# ==========================================
st.set_page_config(page_title="AXOM Global", layout="wide")
st.title("AXOM: Senior Examiner AI")

if error_message:
    st.error(f"Engine Offline: {error_message}")
    st.stop()

uploaded_file = st.file_uploader("Upload Exam Paper (PDF)", type=['pdf'])

if uploaded_file:
    rigor = st.select_slider("Select Marking Rigor", options=["Standard", "Harsh"])
    
    if st.button("RUN AXOM ANALYSIS"):
        # Integrated Ad-Gate and Timer
        timer_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        harsh_comments = [
            "Analyzing your syntax... it is concerning.",
            "Checking the mark scheme... you are making this easy for me.",
            "Looking for complex vocabulary... still looking...",
            "Evaluating your logic... have you read the prompt?",
            "Finalizing the grade... do not get your hopes up."
        ]

        # 30-Second Countdown
        for i in range(30):
            comment = harsh_comments[i // 6]
            timer_placeholder.markdown(f"#### {30 - i} seconds remaining... \n *{comment}*")
            progress_bar.progress((i + 1) / 30)
            time.sleep(1)
        
        timer_placeholder.empty()
        progress_bar.empty()

        with st.spinner("Finalizing report..."):
            try:
                # 1. AI Analysis
                pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                prompt = (
                    f"You are a Senior Lecturer. Mark this paper in {rigor} mode. "
                    "Provide a grade and specific academic feedback. "
                    "If errors are found, list them for a red-pen strike-through."
                )
                
                response = model.generate_content([prompt] + pdf_parts)
                
                # 2. Display Report
                st.markdown("### Examiner Report")
                st.write(response.text)
                
                # 3. Create Annotated PDF
                # Mock data remains for stability until JSON parsing is implemented
                mock_json = [{"action": "strike_through", "text": "swimmed", "comment": "Irregular verb error."}]
                marked_pdf = apply_harsh_marking(uploaded_file, mock_json)
                
                if marked_pdf:
                    st.download_button(
                        label="Download Annotated PDF", 
                        data=marked_pdf, 
                        file_name="AXOM_Marked.pdf",
                        mime="application/pdf"
                    )
                    
            except Exception as e:
                st.error(f"Analysis failed: {e}")
