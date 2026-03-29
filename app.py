import streamlit as st
from google import genai
import os
import json
import re
import io
import datetime
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & HIGH-CONVERSION UI STYLING ---
st.set_page_config(page_title="AXOM | VISION & REVENUE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #000d1a 0%, #000000 100%); color: #00e5ff; font-family: 'Inter', sans-serif; }
    
    /* Subscription Cards */
    .plan-card {
        background: linear-gradient(145deg, #001a33, #000000);
        border: 2px solid #00e5ff; padding: 25px; border-radius: 15px;
        text-align: center; transition: 0.3s; box-shadow: 0px 0px 15px rgba(0, 229, 255, 0.2);
        position: relative; height: 100%;
    }
    .plan-card:hover { transform: translateY(-10px); box-shadow: 0px 0px 30px rgba(0, 229, 255, 0.5); border-color: #ffffff; }
    .price-tag { font-size: 2.2rem; font-weight: 900; color: #ffffff; margin: 10px 0; }
    .deal-badge {
        background: #ff0055; color: white; padding: 5px 12px;
        border-radius: 20px; font-size: 0.8rem; font-weight: bold;
        position: absolute; top: -12px; right: 10px;
    }

    /* Feedback Styling */
    .sticky-green { background: #e8f5e9; color: #2e7d32; padding: 12px; border-radius: 4px; border-left: 8px solid #4caf50; margin-bottom: 12px; font-weight: bold; }
    .sticky-red { background: #ffebee; color: #c62828; padding: 15px; border-radius: 4px; border-left: 10px solid #f44336; margin-bottom: 15px; }
    .red-alert-box { background: linear-gradient(145deg, rgba(244, 67, 54, 0.1), rgba(0,0,0,0)); border: 1px solid #f44336; padding: 25px; border-radius: 8px; margin-bottom: 25px; }
    
    /* Chat Bubbles */
    .chat-bubble { background: rgba(0, 229, 255, 0.1); border: 1px solid #00e5ff; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .user-bubble { background: rgba(255, 255, 255, 0.05); border: 1px solid #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 10px; text-align: right; }
    
    .stButton>button { width: 100%; background: linear-gradient(90deg, #00e5ff, #007bff) !important; color: #fff !important; font-weight: 900; border-radius: 4px; height: 50px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try: 
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: 
    client = None

MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    color = (46, 125, 50, 255) if mark_type == 'tick' else (198, 40, 40, 255)
    sz = 40
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz+10), (x+sz+10, y-sz-10)], fill=color, width=12)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
    draw.ellipse([x+sz+5, y-sz-5, x+sz+75, y-sz+65], fill=color)
    draw.text((x+sz+25, y-sz+12), str(index), fill=(255,255,255,255))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.jpg.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12)
        logo = logo.resize((base_width, int(logo.size[1] * (base_width/logo.size[0]))), Image.LANCZOS)
        img.paste(logo, (img.width - logo.width - 40, img.height - logo.height - 40), logo)
    return img

# --- 3. SESSION INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "eval_history" not in st.session_state: st.session_state.eval_history = []
if "current_eval" not in st.session_state: st.session_state.current_eval = None
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "show_sub" not in st.session_state: st.session_state.show_sub = False

# --- 4. THE SUBSCRIPTION ENGINE (STREAMLINED) ---
def show_subscription_plans():
    st.title("SELECT YOUR ACCESS TIER:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="plan-card">
            <h3>BASIC SCAN</h3>
            <div class="price-tag">$9.99<span style="font-size:1rem;">/mo</span></div>
            <div style="text-align:left; color:#00e5ff; font-size:0.9rem; margin:20px 0;">
                ● 10 PDF Scans / Month<br>
                ● 2022 Syllabus Logic<br>
                ● Standard PDF Reports<br>
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("ACTIVATE BASIC"): st.success("Redirecting to Secure Payment...")

    with col2:
        st.markdown("""
        <div class="plan-card" style="border-color:#ff0055;">
            <div class="deal-badge">POPULAR</div>
            <h3 style="color:#ff0055;">PRO EXAMINER</h3>
            <div class="price-tag">$24.99<span style="font-size:1rem;">/mo</span></div>
            <div style="text-align:left; color:#00e5ff; font-size:0.9rem; margin:20px 0;">
                ● <b>UNLIMITED</b> Neural Scans<br>
                ● <b>VISION AI</b> Graph Analysis<br>
                ● <b>AI CHAT TUTOR</b> Access<br>
                ● Custom Mark Scheme Uploads
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("ACTIVATE PRO"): st.success("Activating Pro Neural Link...")
    
    st.markdown("---")
    st.subheader("💎 EXCLUSIVE DEALS")
    c1, c2 = st.columns(2)
    c1.info("**Annual Legacy:** Pay for 10 months, get **2 MONTHS FREE**. Best for long-term IGCSE prep.")
    c2.warning("**Family Bundle:** Connect two accounts for a **15% discount** on the second sub.")

# --- 5. APP EXECUTION FLOW ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div style="border:1px solid #00e5ff; padding:50px; border-radius:8px; background:rgba(0,10,20,0.9); text-align:center;">', unsafe_allow_html=True)
        st.title("AXOM | VISION LOGIN")
        u_email = st.text_input("ACCESS EMAIL")
        if st.button("INITIALIZE"):
            if "@" in u_email: 
                st.session_state.user_email = u_email
                st.session_state.logged_in = True
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
else:
    with st.sidebar:
        st.title("AXOM V6.6 PRO")
        st.markdown(f"<span style='color:#00e5ff;'>● {st.session_state.user_email}</span>", unsafe_allow_html=True)
        if st.button("UPGRADE PLAN"): st.session_state.show_sub = True
        st.markdown("---")
        menu = st.radio("INTERFACE", ["NEURAL SCAN", "REVISION HUB", "NEURAL ARCHIVE"])
        if st.button("EXIT"): 
            st.session_state.logged_in = False
            st.rerun()

    if st.session_state.show_sub:
        show_subscription_plans()
        if st.button("← BACK TO DASHBOARD"): 
            st.session_state.show_sub = False
            st.rerun()
    
    elif menu == "NEURAL SCAN":
        st.title("VISION AI SCANNER")
        c1, c2 = st.columns(2)
        board, subj = c1.text_input("BOARD", "IGCSE"), c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD STUDENT SCRIPT (PDF)", type=['pdf'])
        up_m = st.file_uploader("UPLOAD MARK SCHEME (OPTIONAL)", type=['pdf'])

        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("AI SCANNING..."):
                try:
                    raw_pages = convert_from_bytes(up_s.read())
                    payload = ["Student Script:"] + raw_pages
                    ms_instr = "Use 2022 Syllabus."
                    if up_m:
                        payload += ["Mark Scheme Authority:"] + convert_from_bytes(up_m.read())
                        ms_instr = "Use provided Mark Scheme as absolute authority."
                    
                    prompt = f"Senior Examiner for {board} {subj}. {ms_instr} Analyze drawings. Ignore capitalization/paragraphs. Return JSON: {{'page_marks':[], 'weaknesses':[]}}"
                    response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + payload)
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        new_entry = {
                            "id": datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
                            "date": datetime.datetime.now().strftime("%d %b, %H:%M"),
                            "subj": subj, "data": data, "pages": raw_pages
                        }
                        st.session_state.eval_history.append(new_entry)
                        st.session_state.current_eval = new_entry
                    else: st.error("Neural data parse failed.")
                except Exception as e: st.error(f"Scan Error: {e}")

        if st.session_state.current_eval:
            for idx, img in enumerate(st.session_state.current_eval['pages']):
                st.markdown(f"### PAGE {idx+1}")
                marks = next((p['marks'] for p in st.session_state.current_eval['data']['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                for i, m in enumerate(marks):
                    marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                st.image(apply_logo(marked_img), use_column_width=True)

    elif menu == "REVISION HUB":
        st.title("🚨 REVISION & NEURAL TUTOR")
        if st.session_state.current_eval:
            t1, t2 = st.tabs(["GAPS & VIDEOS", "CHAT WITH TUTOR"])
            with t1:
                for item in st.session_state.current_eval['data'].get('weaknesses', []):
                    st.markdown(f'<div class="red-alert-box"><b>{item["topic"].upper()}</b><br>{item["reason"]}</div>', unsafe_allow_html=True)
                    st.link_button("▶ WATCH VIDEO LESSON", item["direct_vid_url"])
            with t2:
                for chat in st.session_state.chat_history:
                    st.markdown(f'<div class="{"user-bubble" if chat["role"]=="user" else "chat-bubble"}">{chat["content"]}</div>', unsafe_allow_html=True)
                user_q = st.chat_input("Ask about your marks...")
                if user_q:
                    st.session_state.chat_history.append({"role": "user", "content": user_q})
                    ctx = f"Context: Student failed {st.session_state.current_eval['data']['weaknesses']}. Help them."
                    resp = client.models.generate_content(model=MODEL_ID, contents=[ctx, user_q])
                    st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
                    st.rerun()
        else: st.info("Run a scan or select from Archive.")

    elif menu == "NEURAL ARCHIVE":
        st.title("📂 NEURAL ARCHIVE")
        for i, item in enumerate(st.session_state.eval_history):
            with st.container():
                st.markdown(f'<div style="border:1px solid #00e5ff; padding:15px; border-radius:10px; margin-bottom:10px;"><b>{item["subj"]}</b> | {item["date"]}</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if c1.button("LOAD", key=f"ld_{i}"): 
                    st.session_state.current_eval = item
                    st.success(f"Loaded {item['subj']}")
                if c2.button("DELETE", key=f"del_{i}"): 
                    st.session_state.eval_history.pop(i)
                    st.rerun()
