import streamlit as st
from google import genai
import os
import json
import re
import io
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & INTERFACE STYLING ---
st.set_page_config(page_title="AXOM | VISION AI", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #000d1a 0%, #000000 100%); color: #00e5ff; font-family: 'Inter', sans-serif; }
    
    .sticky-green {
        background: #e8f5e9; color: #2e7d32; padding: 12px; border-radius: 4px;
        border-left: 8px solid #4caf50; margin-bottom: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.3); font-family: 'Comic Sans MS', cursive; font-weight: bold;
    }
    
    .sticky-red {
        background: #ffebee; color: #c62828; padding: 15px; border-radius: 4px;
        border-left: 10px solid #f44336; margin-bottom: 15px;
        box-shadow: 3px 3px 12px rgba(0,0,0,0.4); font-family: 'Comic Sans MS', cursive;
    }
    
    .red-alert-box { 
        background: linear-gradient(145deg, rgba(244, 67, 54, 0.1), rgba(0,0,0,0)); 
        border: 1px solid #f44336; padding: 25px; border-radius: 8px; margin-bottom: 25px; 
    }
    
    .stButton>button { 
        width: 100%; background: linear-gradient(90deg, #00e5ff, #007bff) !important; 
        color: #fff !important; font-weight: 900; border-radius: 4px; height: 50px; border: none;
    }
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
        h_ratio = (base_width / float(logo.size[0]))
        v_size = int((float(logo.size[1]) * float(h_ratio)))
        logo = logo.resize((base_width, v_size), Image.LANCZOS)
        img.paste(logo, (img.width - logo.width - 40, img.height - logo.height - 40), logo)
    return img

# --- 3. LOGIN & SESSION SYSTEM ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "eval_data" not in st.session_state: st.session_state.eval_data = None
if "pages" not in st.session_state: st.session_state.pages = []

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
        st.title("AXOM V6.0 PRO")
        st.markdown(f"<span style='color:#00e5ff;'>● {st.session_state.user_email}</span>", unsafe_allow_html=True)
        st.markdown("---")
        menu = st.radio("INTERFACE", ["NEURAL SCAN", "REVISION HUB"])
        if st.button("EXIT"): 
            st.session_state.logged_in = False
            st.rerun()

    # --- VISION SCANNER ---
    if menu == "NEURAL SCAN":
        st.title("🧠 VISION AI SCANNER")
        c1, c2 = st.columns(2)
        board, subj = c1.text_input("BOARD", "IGCSE"), c2.text_input("SUBJECT", "Physics")
        up_s = st.file_uploader("UPLOAD SCRIPT", type=['pdf'])

        if up_s and st.button("EXECUTE NEURAL EVALUATION"):
            with st.spinner("VISION AI ANALYZING GRAPHS & HANDWRITING..."):
                try:
                    raw_pages = convert_from_bytes(up_s.read())
                    prompt = f"""
                    You are a Senior Examiner for {board} {subj} (2022 Syllabus).
                    ACTIVATE VISION SYSTEMS: 
                    1. Analyze all handwriting, GRAPHS, DRAWINGS, and DIAGRAMS.
                    2. Evaluate logical reasoning and technical accuracy of sketches.
                    3. IGNORE mechanical errors (capitalization/paragraphs).
                    
                    Return ONLY JSON:
                    {{
                        "page_marks": [{{ "page": 0, "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "...", "topic": "..." }}] }}],
                        "weaknesses": [{{ "topic": "...", "reason": "...", "direct_vid_url": "https://youtu.be/..." }}]
                    }}
                    RULE: 'page' must be 0-indexed to match the page it was found on.
                    """
                    response = client.models.generate_content(model=MODEL_ID, contents=[prompt] + raw_pages)
                    match = re.search(r'\{.*\}', response.text, re.DOTALL)
                    if match:
                        st.session_state.eval_data = json.loads(match.group(0))
                        st.session_state.pages = raw_pages
                    else:
                        st.error("Vision data parse failed.")
                except Exception as e:
                    st.error(f"Scan Error: {e}")

        if st.session_state.eval_data:
            pdf = FPDF()
            for idx, img in enumerate(st.session_state.pages):
                st.markdown(f"### PAGE {idx+1}")
                col_img, col_stickers = st.columns([3, 1])
                
                # PAGE ANCHORING LOGIC
                marks = next((p['marks'] for p in st.session_state.eval_data['page_marks'] if p['page'] == idx), [])
                marked_img = img.copy()
                
                with col_stickers:
                    st.subheader("📌 Examiner Notes")
                    for i, m in enumerate(marks):
                        is_correct = m['type'] == 'tick'
                        style = "sticky-green" if is_correct else "sticky-red"
                        with st.expander(f"NOTE #{i+1}: {m['topic']}", expanded=not is_correct):
                            st.markdown(f'<div class="{style}">{m["note"]}</div>', unsafe_allow_html=True)
                        marked_img = draw_mark(marked_img, int((m['x']/1000)*img.width), int((m['y']/1000)*img.height), m['type'], i+1)
                
                marked_img = apply_logo(marked_img)
                col_img.image(marked_img, use_column_width=True)
                
                t_p = f"t_{idx}.png"
                marked_img.save(t_p)
                pdf.add_page()
                pdf.image(t_p, 0, 0, 210, 297)
                os.remove(t_p)
            
            p_out = pdf.output(dest='S')
            st.download_button("📩 EXTRACT FEEDBACK PDF", data=p_out.encode('latin1') if isinstance(p_out, str) else bytes(p_out), file_name="AXOM_EVAL.pdf")

    elif menu == "REVISION HUB":
        st.title("🚨 REVISION PATHWAYS")
        if st.session_state.eval_data:
            for item in st.session_state.eval_data.get('weaknesses', []):
                st.markdown(f"""
                <div class="red-alert-box">
                    <h2 style="color:#f44336; margin:0;">⚠️ TOPIC: {item['topic'].upper()}</h2>
                    <p style="color:#ccc; margin:10px 0;">{item['reason']}</p>
                    <a href="{item['direct_vid_url']}" target="_blank" style="background:#ff0000; color:#fff; padding:10px; display:block; text-align:center
