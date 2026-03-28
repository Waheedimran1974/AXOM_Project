import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import urllib.parse
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & THEME ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")
st.markdown("""<style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .mistake-box { 
        background: rgba(255, 50, 50, 0.1); 
        border-left: 5px solid #ff3232; 
        padding: 20px; 
        border-radius: 5px; 
        margin-bottom: 25px;
    }
    .video-container {
        border: 2px solid #00d4ff;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 15px;
        background: #000;
    }
</style>""", unsafe_allow_html=True)

# --- 2. CORE ENGINE ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash"

# --- 3. LOGIC ---
if "latest_eval" not in st.session_state: st.session_state.latest_eval = []
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # (Login Logic Here - Simplified for brevity)
    st.title("AXOM | ACCESS")
    if st.button("UNLOCK"): st.session_state.logged_in = True; st.rerun()
else:
    menu = st.sidebar.radio("PANEL", ["NEURAL SCAN", "REVISION HUB"])

    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL EVALUATION")
        board = st.text_input("BOARD", "IGCSE")
        subj = st.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT", type=['pdf'])
        up_m = st.file_uploader("UPLOAD MARK SCHEME (OPT)", type=['pdf'])

        if up_s and st.button("EXECUTE SCAN"):
            with st.spinner("AI ANALYZING & LOCATING RESOURCES..."):
                script_pages = convert_from_bytes(up_s.read())
                
                # We ask Gemini to find specific YouTube IDs for the topics it marks wrong
                p_txt = f"""
                Examiner for {board} {subj}. 
                Analyze the script. For every 'cross' (mistake), identify the topic.
                Then, suggest a high-quality YouTube search term that would lead to a specific lesson.
                Output ONLY JSON:
                {{
                    "marks": [{{ "page": 0, "type": "cross", "x": 500, "y": 500, "topic": "Name" }}],
                    "weaknesses": [
                        {{ 
                            "topic": "Specific Topic", 
                            "reason": "Why they failed",
                            "yt_search": "Cognito IGCSE Physics Electricity Lesson" 
                        }}
                    ]
                }}
                """
                response = client.models.generate_content(model=MODEL_ID, contents=[p_txt] + script_pages)
                res = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                
                st.session_state.latest_eval = res.get("weaknesses", [])
                st.session_state.current_subj = subj
                st.success("SCAN COMPLETE. Proceed to REVISION HUB.")

    elif menu == "REVISION HUB":
        st.title("📚 ADAPTIVE REVISION HUB")
        
        if not st.session_state.latest_eval:
            st.info("No weaknesses logged. Run a Neural Scan to begin.")
        else:
            for item in st.session_state.latest_eval:
                topic = item['topic']
                search_term = item['yt_search']
                
                # Construct the direct URL
                encoded_query = urllib.parse.quote(search_term)
                direct_url = f"https://www.youtube.com/results?search_query={encoded_query}"
                
                st.markdown(f"""
                <div class="mistake-box">
                    <h2 style="color: #ff3232; margin:0;">⚠️ WEAKNESS: {topic.upper()}</h2>
                    <p style="color: #ccc; margin-top:5px;">{item['reason']}</p>
                    <p><b>Direct Resource:</b> <a href="{direct_url}" style="color: #00d4ff;">{direct_url}</a></p>
                </div>
                """, unsafe_allow_html=True)

                # SHOW THE UI OF THE VIDEO (The Embed)
                # Since we can't get a "Specific ID" without the YouTube API, 
                # we use a "Search Embed" or show the student how to fix it:
                st.write("### 📺 PRIORITY LESSON PREVIEW")
                
                # Note: For security/API reasons, Streamlit st.video() requires a specific link.
                # In a real production environment, you would use the YouTube Data API here.
                # For now, we provide the interactive search UI:
                st.video(f"https://www.youtube.com/embed?listType=search&list={encoded_query}")
                
                st.markdown("---")
