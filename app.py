import streamlit as st
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF
import time
import json
import io

# ==========================================
# 1. THE BRAIN: HARSH MODE & SYSTEM PROMPTS
# ==========================================
def get_system_prompt(mode):
    """Defines the 'Senior Lecturer' persona and the marking rules."""
    base_persona = "You are Senior Lecturer Waheed Imran. You are a professional English examiner with 30 years of experience. "
    
    if mode == "Harsh Mode":
        return base_persona + """
        MODE: HARSH (Brutal).
        POLICY: Zero-tolerance for basic vocabulary (fun, good, nice), simple grammar, or spelling errors.
        CRITIQUE: Be direct, academic, and unforgiving. 
        MARKING: Start at 100% and deduct marks for every error found. 
        INSTRUCTION: You must provide a structured report followed by a JSON list of specific corrections.
        JSON FORMAT: 
        [{"action": "strike_through", "text": "exact_word_from_text", "comment": "Brutal penalty explanation"}]
        """
    return base_persona + "MODE: Standard. Provide balanced, constructive feedback and a fair grade."

# ==========================================
# 2. THE HANDS: RED PEN PDF PAINTER
# ==========================================
def apply_harsh_marking(uploaded_file, ai_json_instructions):
    """Physically draws red lines and comments on the student's PDF."""
    try:
        input_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        
        for action in ai_json_instructions:
            for page in doc:
                # Find the specific word to strike through
                text_instances = page.search_for(action["text"])
                for inst in text_instances:
                    if action["action"] == "strike_through":
                        # Draw the Red Line
                        line_mid = (inst.y0 + inst.y1) / 2
                        page.add_line_annot(fitz.Point(inst.x0, line_mid), fitz.Point(inst.x1, line_mid))
                        # Add the Harsh Comment next to the error
                        page.add_text_annot(fitz.Point(inst.x1 + 5, inst.y0), action["comment"])
        
        return doc.write()
    except Exception as e:
        st.error(f"Red Pen Error: {e}")
        return None
# ==========================================
# 3. SETUP & SECURITY (STABLE 2026)
# ==========================================
try:
    API_KEY = st.secrets["AIzaSyDiz22b_eQXkB4fQQ8rl4_AZ1gmPc7TXiw"]
    genai.configure(api_key=API_KEY)
    
    # Using the Stable 2026 Workhorse: Gemini 2.0 Flash
    # This model is optimized for PDF 'Vision' and Harsh Mode JSON
    model = genai.GenerativeModel('gemini-2.0-flash') 
    
except Exception as e:
    st.error("Setup Error: Check your Streamlit Secrets for 'GEMINI_KEY'")
# ==========================================
# 4. THE USER INTERFACE (UI)
# ==========================================

# Sidebar: Branding and Mode Selection
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=AXOM", width=100) # Replace with your logo later
    st.title("Control Center")
    mode = st.radio("Select Marking Level:", ["Standard Mode", "Harsh Mode"], index=1)
    st.info(f"Status: {mode} Engaged")
    st.divider()
    st.caption("CEO: Waheed Imran")

# Main Screen: Upload Section
uploaded_file = st.file_uploader("Upload Student Paper (PDF format)", type=['pdf'])

if uploaded_file:
    st.success("Paper Received. Ready for Analysis.")
    
    if st.button(f"EXECUTE {mode.upper()} ANALYSIS"):
        
        # --- THE AD-GATE TIMER (Your Monetization Strategy) ---
        with st.spinner(f"Reviewing for mediocrity... Please wait."):
            progress_bar = st.progress(0)
            for percent in range(100):
                time.sleep(0.3) # 30 Second Total Wait
                progress_bar.progress(percent + 1)
            
            try:
                # 1. Process with Gemini 3 Flash
                pdf_data = uploaded_file.getvalue()
                content = [{"mime_type": "application/pdf", "data": pdf_data}]
                
                full_prompt = get_system_prompt(mode)
                response = model.generate_content([full_prompt] + content)
                
                # 2. Logic for Red Pen (Simulated JSON for prototype stability)
                # In your next phase, we will extract this JSON directly from response.text
                mock_json = [
                    {"action": "strike_through", "text": "swimmed", "comment": "Irrational verb usage. Band 2 Penalty."},
                    {"action": "strike_through", "text": "very fun", "comment": "Paucity of vocabulary. Use 'exhilarating'."}
                ]
                
                marked_pdf_bytes = apply_harsh_marking(uploaded_file, mock_json)
                
                # 3. Display Results
                st.markdown("---")
                st.markdown("## 📊 Official Examiner Report")
                st.write(response.text)
                
                if marked_pdf_bytes:
                    st.download_button(
                        label="📥 Download Annotated PDF (Red Pen Marks)",
                        data=marked_pdf_bytes,
                        file_name="AXOM_Harsh_Report.pdf",
                        mime="application/pdf"
                    )
                
                st.success("Profit generated. Branding applied.")
                
            except Exception as e:
                st.error(f"System Failure: {e}")
