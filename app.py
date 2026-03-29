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
st.set_page_config(page_title="AXOM | MASTER EXAMINER", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top, #001224 0%, #000000 100%); color: #00e5ff; font-family: 'Inter', sans-serif; }
    
    .sticky-green {
        background: #d4edda; color: #155724; padding: 12px; border-radius: 4px;
        border-left: 8px solid #28a745; margin-bottom: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.4); font-family: 'Comic Sans MS', cursive; font-weight: bold;
    }
    
    .sticky-red {
        background: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px;
        border-left: 10px solid #dc3545; margin-bottom: 15px;
        box-shadow: 3px 3px 12px rgba(0,0,0,0.5); font-family: 'Comic Sans MS', cursive;
    }
    
    .red-alert-box { 
        background: linear-gradient(145deg, rgba(220, 53, 69, 0.1), rgba(0,0,0,0)); 
        border: 1px solid #dc3545; padding: 25px; border-radius: 8px; margin-bottom: 25px; 
    }
    
    .stButton>button { 
        width: 100%; background: linear-gradient(90deg, #00e5ff, #007bff) !important; 
        color: #fff !important; font-weight: 900; border-radius: 4px; height: 50px;
    }
    
    .yt-launch-btn { 
        display: inline-block; width: 100%; text-align: center; background: #ff0000; 
        color: #ffffff !important; padding: 14px; border-radius: 6px; 
        text-decoration: none; font-weight: 900; font-size: 1.1rem;
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
    # Real Examiner Red/Green Spectrum
    color = (0, 160, 0, 255) if mark_type == 'tick' else (220, 20, 60, 255)
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
    """Corrected function definition and error handling"""
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        base_width = int(img.width * 0.12)
        h_ratio = (base_width / float(logo.size[0]))
        v_size = int((float(logo.size[1]) * float(h_ratio)))
        logo = logo.resize((base_width, v_size), Image.LANCZOS)
        img.paste(logo, (img.width - logo.width - 40, img.height - logo.height - 40), logo)
    return img

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "eval_data" not in st.session_state: st.
