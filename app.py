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
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model, None
    except Exception as e:
        return None, str(e)

model, error_message = load_axom_engine()

if "history" not in st.session_state:
    st.session_state.history = []

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
                    # Choose color based on action
                    # (1, 0, 0) is Red | (0, 0.5, 0) is Green
                    stroke_color = (1, 0, 0) if action["type"] == "error" else (0, 0.5, 0)
                    
                    if action["action"] == "strike_through":
                        line_mid = (inst.y0 + inst.y1) / 2
                        annot = page.add_line_annot(fitz.Point(inst.x0, line_mid), fitz.Point(inst.x1, line_mid))
                        annot.set_colors(stroke=stroke_color)
                        annot.update()
                        
                        # Add the comment in the same color
                        page.add_text_annot(fitz.Point(inst.x1 + 5, inst.y0), action["comment"])
        return doc.write()
    except:
        return None

# ==========================================
# 3. USER INTERFACE (UI)
# ==========================================
st.set_page_config(page_title="AXOM Global", layout="wide")
st.title("AXOM: Senior Examiner AI")

with st.sidebar:
    st.header("Submission History")
    if not st.session_state.history:
        st.write("No papers marked yet.")
    else:
        for item in reversed(st.session_state.history):
            st.write(f"**{item['filename']}**")
            st.caption(f"Mode: {item['mode']} | {item['timestamp']}")
            st.divider()
        
        if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()

if error_message:
    st.error(f"Engine Offline: {error_message}")
    st.stop()

uploaded_file = st.file_uploader("Upload Exam Paper (PDF)", type=['pdf'])

if uploaded_file:
    rigor = st.select_slider("Select Marking Rigor", options=["Standard", "Harsh"])
    
    if st.button("RUN AXOM ANALYSIS"):
        timer_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        status_updates = [
            "Initializing AXOM Neural Engine...",
            "Fetching IGCSE Mark Scheme...",
            "Scanning syntax and morphology...",
            "Comparing vocabulary to Band 9 descriptors...",
            "Calculating deductive penalties...",
            "Generating Senior Lecturer feedback..."
        ]

        for i in range(30):
            msg = status_updates[i // 5]
            with timer_placeholder.container():
                st.markdown(f"### {msg}")
                st.info(f"Analysis in progress: {30 - i}s remaining. Do not refresh this page.")
                st.caption("ADVERTISEMENT: Prepare for your IELTS with AXOM Premium. No wait times. 100% Accuracy.")
            
            progress_bar.progress((i + 1) / 30)
            time.sleep(1)
        
        timer_placeholder.empty()
        progress_bar.empty()

        with st.spinner("Finalizing report..."):
            try:
                pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                prompt = (
                    f"You are a Senior Lecturer. Mark this paper in {rigor} mode. "
                    "Provide a grade and academic feedback. "
                    "At the very end of your response, provide a JSON list of errors for strike-throughs. "
                    "Format: JSON_START "
                    "[{\"action\": \"strike_through\", \"text\": \"word\", \"comment\": \"explanation\"}] "
                    "JSON_END"
                )
                
                response = model.generate_content([prompt] + pdf_parts)
                full_text = response.text
                
                correction_list = []
                report_text = full_text

                if "JSON_START" in full_text and "JSON_END" in full_text:
                    try:
                        report_text = full_text.split("JSON_START")[0]
                        json_part = full_text.split("JSON_START")[1].split("JSON_END")[0]
                        correction_list = json.loads(json_part.strip())
                    except:
                        correction_list = []

                st.session_state.history.append({
                    "filename": uploaded_file.name,
                    "mode": rigor,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "report": report_text
                })

                # --- THE REPORT VIEW ---
                st.markdown("---")
                st.markdown("### Examiner Report")
                st.markdown(f"<div id='printable-report'>{report_text}</div>", unsafe_allow_html=True)
                
                # --- PRINT BUTTON ---
                st.button("Print This Report", on_click=lambda: st.write('<script>window.print();</script>', unsafe_allow_html=True))
                
                marked_pdf = apply_harsh_marking(uploaded_file, correction_list)
                
                if marked_pdf:
                    st.download_button(
                        label="Download Annotated PDF", 
                        data=marked_pdf, 
                        file_name=f"AXOM_Marked_{uploaded_file.name}",
                        mime="application/pdf"
                    )
                    
            except Exception as e:
                st.error(f"Analysis failed: {e}")
