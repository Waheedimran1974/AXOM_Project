import streamlit as st
from google import genai
import os
import json
import re
import urllib.parse
import io
import smtplib
import random
from email.message import EmailMessage
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from fpdf import FPDF
from datetime import datetime

# --- 1. HUD & INTERFACE STYLING ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); text-align: center; box-shadow: 0 0 30px rgba(0, 212, 255, 0.2); }
    
    /* STICKY NOTE DESIGN */
    .sticky-note {
        background-color: #ffffa5; color: #111; padding: 15px; border-radius: 2px;
        border-left: 8px solid #ffd700; margin-bottom: 12px;
        font-family: sans-serif; box-shadow: 3px 3px 10px rgba(0,0,0,0.5);
    }
    
    /* REVISION RED BOX */
    .red-alert-box {
        background: rgba(255, 50, 50, 0.1); border: 2px solid #ff3232;
        padding: 20px; border-radius: 10px; margin-bottom: 25px;
        box-shadow: 0 0 20px rgba(255, 50, 50, 0.2);
    }
    
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; font-weight: bold; height: 50px; }
    .page-header { border-bottom: 2px solid #00d4ff; margin: 30px 0 10px 0; padding-bottom: 5px; font-weight: bold; color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES ---
try: client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except: client = None
MODEL_ID = "gemini-2.5-flash"

def send_otp(recip, code):
    try:
        msg = EmailMessage()
        msg.set_content(f"YOUR AXOM SECURE ACCESS KEY: {code}\n\nDO NOT SHARE THIS CODE.")
        msg['Subject'] = 'AXOM NEURAL ACCESS PROTOCOL'
        msg['From'] = st.secrets["SMTP_EMAIL"]
        msg['To'] = recip
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(st.secrets["SMTP_EMAIL"], st.secrets["SMTP_PASS"])
            s.send_message(msg)
        return True
    except: return False

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0)); draw = ImageDraw.Draw(overlay)
    color = (0, 230, 118, 255) if mark_type == 'tick' else (255, 50, 50, 255)
    sz = 40
    if mark_type == 'tick':
        draw.line([(x-sz, y), (x-sz//3, y+sz), (x+sz, y-sz)], fill=color, width=12)
    else:
        draw.line([(x-sz, y-sz), (x+sz, y+sz)], fill=color, width=12)
        draw.line([(x+sz, y-sz), (x-sz, y+sz)], fill=color, width=12)
    draw.ellipse([x+sz, y-sz, x+sz+50, y-sz+50], fill=(0, 212, 255, 220))
    draw.text((x+sz+15, y-sz+10), str(index), fill=(0,0,0,255))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def apply_logo(img, logo_path="logo.jpg.png"):
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12)
        logo = logo.resize((base_width, int(logo.size[1] * (base_width/logo.size[0]))), Image.LANCZOS)
        img.paste(logo, (img.width-logo.width-50, img.height-logo.height-50), logo)
    return img

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "eval_data" not in st.session_state: st.session_state.eval_data = None

# --- 4. SECURE ACCESS SYSTEM ---
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="future-frame">', unsafe_allow_html=True)
        st.title("AXOM | ACCESS")
        if not st.session_state.otp_sent:
            u_email = st.text_input("ENTER EMAIL")
            if st.button("SEND ACCESS KEY"):
                if "@" in u_email:
                    code = str(random.randint(100000, 999999))
                    if send_otp(u_email, code):
                        st.session_state.generated_otp, st.session_state.user_email, st.session_state.otp_sent = code, u_email, True
                        st.rerun()
                else: st.error("INVALID EMAIL")
        else:
            otp_in = st.text_input("ENTER 6-DIGIT KEY", type="password")
            if st.button("AUTHENTICATE"):
                if otp_in == st.session_state.generated_otp:
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("ACCESS DENIED.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MAIN HUB ---
else:
    with st.sidebar:
        st.title("AXOM V4.0 PRO")
        if os.path.exists("logo.jpg.png"): st.image("logo.jpg.png")
        st.write(f"**ACTIVE:** {st.session_state.user_email}")
        menu = st.radio("INTERFACE", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("LOGOUT"): st.session_state.logged_in = False; st.session_state.otp_sent = False; st.rerun()

    if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL SCANNER")
        c1, c2 = st.columns(2)
        board, subj = c1.text_input("BOARD", "IGCSE"), c2.text_input("SUBJECT", "Physics")
        up_s, up_m = st.file_uploader("UPLOAD SCRIPT", type=['pdf']), st.file_uploader("MARK SCHEME (OPT)", type=['pdf'])

        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("AI CONNECTING STICKY NOTES TO REVISION PATHS..."):
                try:
                    script_pages = convert_from_bytes(up_s.read())
                    p_txt = f"Senior Examiner for {board} {subj}. Return ONLY JSON: {{'page_marks': [{{'page': 0, 'marks': [{{'type': 'tick'|'cross', 'x': 0-1000, 'y': 0-1000, 'note': '...', 'topic': '...' }}] }}], 'weaknesses': [{{'topic': '...', 'reason': '...', 'yt': '...' }}] }}"
                    response = client.models.generate_content(model=MODEL_ID, contents=[p_txt] + script_pages)
                    st.session_state.eval_data = json.loads(re.search(r'\{.*\}', response.text, re.DOTALL).group(0))
                    st.session_state.pages = script_pages
                    st.session_state.current_subj = subj
                except Exception as e: st.error(f"SCAN ERROR: {e}")

        if st.session_state.eval_data:
            output_pdf = FPDF()
            for idx, img in enumerate(st.session_state.pages):
                st.markdown(f"<div class='page-header'>PAGE {idx+1}</div>", unsafe_allow_html=True)
                col_img, col_sticky = st.columns([3, 1])
                marks = next((p['marks'] for p in st.session_state.eval_data['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                with col_sticky:
                    st.subheader("📌 Sticky Notes")
                    for i, m in enumerate(marks):
                        with st.expander(f"NOTE #{i+1}: {m['topic']}", expanded=False):
                            st.markdown(f'<div class="sticky-note">{m["note"]}</div>', unsafe_allow_html=True)
                        marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                marked_img = apply_logo(marked_img, "logo.jpg.png")
                col_img.image(marked_img, use_column_width=True)
                t_p = f"t_{idx}.png"; marked_img.save(t_p); output_pdf.add_page(); output_pdf.image(t_p,0,0,210,297); os.remove(t_p)
            
            pdf_out = output_pdf.output(dest='S')
            pdf_bytes = pdf_out.encode('latin1') if isinstance(pdf_out, str) else bytes(pdf_out)
            st.download_button("📩 DOWNLOAD AXOM REVIEW", data=pdf_bytes, file_name="AXOM_REVIEW.pdf")

    elif menu == "REVISION HUB":
        st.title("🚨 THE REVISION HUB")
        if st.session_state.eval_data:
            for item in st.session_state.eval_data['weaknesses']:
                q = urllib.parse.quote(f"{st.session_state.current_subj} {item['yt']}")
                st.markdown(f'<div class="red-alert-box"><h2>⚠️ WEAKNESS: {item["topic"].upper()}</h2><p>{item["reason"]}</p></div>', unsafe_allow_html=True)
                st.video(f"https://www.youtube.com/embed?listType=search&list={q}")
