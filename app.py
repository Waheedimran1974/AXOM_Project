import streamlit as st

# Securely grab the key you saved in 'Secrets'
genai.configure(api_key=st.secrets["GEMINI_KEY"])

st.set_page_config(page_title="AXOM Global", layout="wide", page_icon="🚀")

# Header Section
st.title("🚀 AXOM: Senior Examiner AI")
st.subheader("Global Financial Monitoring & Grading")

# Sidebar for Business Controls
with st.sidebar:
    st.header("Control Panel")
    subject = st.selectbox("Target Subject", ["IGCSE English 0510", "Physics", "Chemistry", "Mathematics"])
    mode = st.radio("Grading Mode", ["Strict (Cambridge)", "Feedback Only", "Quick Score"])
    st.divider()
    st.write("📈 **Current Profit Rate:** $0.998 / page")

# Main Interface
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Upload Student Paper")
    uploaded_file = st.file_uploader("Drop PDF or Image here", type=['pdf', 'png', 'jpg'])
    
with col2:
    st.markdown("### 📊 Live Monitoring")
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' received.")
        if st.button("RUN SENIOR EXAMINER AI"):
            st.info(f"Analyzing {subject} standards... please wait.")
            # AI Logic will process here in the next step
    else:
        st.warning("Awaiting input for analysis.")
