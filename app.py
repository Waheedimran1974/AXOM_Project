import streamlit as st
from PIL import Image

# Secure Configuration

st.set_page_config(page_title="AXOM Global", layout="wide", page_icon="🚀")

# Sidebar - Business & Subject Controls
with st.sidebar:
    st.title("Settings")
    subject = st.selectbox("Target Subject", ["English", "Physics", "Chemistry", "Mathematics"])
    mode = st.radio("Grading Mode", ["Strict (Cambridge)", "Feedback Only", "Quick Score"])
    st.divider()
    st.write("📈 **Profit Rate:** $0.998 / page")
    st.write("🌍 **Status:** Global Cloud Live")

st.title("AXOM: Senior Examiner AI")

# Main Interface
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📄 Upload Student Work")
    uploaded_file = st.file_uploader("Upload Image/PDF of Exam", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Student Submission", use_container_width=True)

with col2:
    st.markdown("### 📊 AI Analysis Results")
    if uploaded_file and st.button("RUN SENIOR EXAMINER AI"):
        with st.spinner(f"Applying {subject} Marking Schemes..."):
            try:
                # The "Ruthless" Prompt Logic
                prompt = f"""
                You are a Senior Cambridge Examiner for {subject}. 
                Analyze this student paper. 
                1. Provide a total score based on standard marking schemes.
                2. List specific mistakes.
                3. Give 3 'Examiner Tips' for the student to reach an A*.
                Format the output clearly with headers.
                """
                
                response = model.generate_content([prompt, image])
                st.markdown(response.text)
                st.success("Analysis Complete. Profit Logged.")
                
            except Exception as e:
                st.error(f"Engine Error: {e}")
    else:
        st.info("Awaiting file upload to begin monitoring.")
streamlit
google-generativeai
python-dotenv
Pillow
