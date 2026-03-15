import streamlit as st

st.set_page_config(page_title="AXOM - Global Financial Monitor", layout="wide")

st.title(" AXOM: Senior Examiner AI")
st.write("Ibrahim, the engine is officially live on the Cloud!")

st.sidebar.success("Subscription Status: $20 Premium")

subject = st.sidebar.selectbox("Select Subject", ["IGCSE English 0510", "Physics", "Chemistry", "Mathematics"])
st.write(f"Currently monitoring: **{subject}**")

st.info("Ready for PDF upload. Profit Tracking: $0.998 per page.")
