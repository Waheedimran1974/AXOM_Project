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

# --- Initialize Session States ---
if "history" not in st.session_state:
    st.session_state.history = []
if 'role' not in st.session_state:
    st.session_state.role = None

# ==========================================
# 2. THE HANDS: RED PEN PAINTER (Your Logic)
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
                        annot = page.add_line_annot(fitz.Point(inst.x0, line_mid), fitz.Point(inst.x1, line_mid))
                        annot.set_colors(stroke=(1, 0, 0)) 
                        annot.update()
                        page.add_text_annot(fitz.Point(inst.x1 + 5, inst.y0), action["comment"])
        return doc.write()
    except:
        return None

# ==========================================
# 3. IDENTITY & ROLE SELECTION (The New Part)
# ==========================================
st.set_page_config(page_title="AXOM Global", layout="wide")

if not st.session_state.role:
    st.markdown("<h1 style='text-align: center;'>🚀 Welcome to AXOM</h1>", unsafe_allow_html=True)
    st.subheader("Select Your Account Type to Begin")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎓 Student Portal"): st.session_state.role = "Student"
    with col2:
        if st.button("👨‍🏫 Teacher Portal"): st.session_state.role = "Teacher"
    with col3:
        if st.button("👪 Parent Portal"): st.session_state.role = "Parent"
    st.stop() # Stops the app here until a role is picked

# --- Sidebar for Logout & History ---
with st.sidebar:
    st.success(f"Mode: {st.session_state.role}")
    if st.button("Logout / Change Role"):
        st.session_state.role = None
        st.rerun()
    
    st.divider()
    st.header("Submission History")
    if not st.session_state.history:
        st.write("No papers marked yet.")
    else:
        for item in reversed(st.session_state.history):
            st.write(f"**{item['filename']}**")
            st.caption(f"{item['timestamp']}")

# ==========================================
# 4. MAIN INTERFACE (Your Marking Logic)
# ==========================================
if st.session_state.role == "Student":
    # Custom Branding Header
    st.markdown(
        """
        <div style='background-color: #001F3F; padding: 20px; border-radius: 10px; border-bottom: 5px solid #D4AF37;'>
            <h1 style='color: white; text-align: center; margin: 0;'>AXOM STUDENT PORTAL</h1>
            <p style='color: #D4AF37; text-align: center; font-weight: bold;'>SENIOR EXAMINER AI SYSTEM</p>
        </div>
        <br>
        """,
        unsafe_allow_html=True
    )

    if error_message:
        st.error(f"Engine Offline: {error_message}")
        st.stop()

    uploaded_file = st.file_uploader("Upload Exam Paper (PDF)", type=['pdf'])

    if uploaded_file:
        rigor = st.select_slider("Select Marking Rigor", options=["Standard", "Harsh"])
        
        with st.expander("View Full Terms of Service"):
            st.markdown("1. Nature of Service: Automated Feedback...") # Shortened for space
        
        tos_agreed = st.checkbox("I agree to the Halal-Ads & Data Privacy Terms")
        run_button = st.button("RUN AXOM ANALYSIS", disabled=not tos_agreed)
        
        if run_button:
            # --- PROGRESS BAR LOGIC (From your code) ---
            progress_bar = st.progress(0)
            status_updates = ["Initializing...", "Scanning...", "Generating Feedback..."]
            for i in range(15): # Shortened to 15s for faster testing
                progress_bar.progress((i + 1) / 15)
                time.sleep(0.5)
            
            # --- AI GENERATION LOGIC ---
            with st.spinner("Finalizing report..."):
                try:
                    pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                    prompt = (f"Mark this paper in {rigor} mode. Format: JSON_START "
                              "[{\"action\": \"strike_through\", \"text\": \"word\", \"comment\": \"explanation\"}] JSON_END")
                    
                    response = model.generate_content([prompt] + pdf_parts)
                    full_text = response.text
                    
                    # (Extraction logic from your code)
                    report_text = full_text.split("JSON_START")[0] if "JSON_START" in full_text else full_text
                    
                    st.session_state.history.append({
                        "filename": uploaded_file.name,
                        "timestamp": time.strftime("%H:%M:%S")
                    })

                    st.markdown("### Examiner Report")
                    st.write(report_text)
                    
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

elif st.session_state.role == "Teacher":
    st.title("👨‍🏫 Teacher Dashboard")
    st.write("Coming in the next Sprint: Handwriting Clone & Class Stats.")

elif st.session_state.role == "Parent":
    st.title("👪 Parent Dashboard")
    st.write("Coming in the next Sprint: Student Progress & Grade Predictor.")
