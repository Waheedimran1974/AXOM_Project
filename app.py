import streamlit as st
from google import genai
import pandas as pd
import os
import io
import json
import re
import csv
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | NEURAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 30px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 20px rgba(0, 212, 255, 0.2); }
    .report-box { padding: 20px; border-left: 5px solid #00d4ff; background: rgba(0, 212, 255, 0.1); margin: 10px 0; border-radius: 0 10px 10px 0; color: #fff; }
    .stButton>button { width: 100%; background: #00d4ff; color: #000; border: none; border-radius: 5px; height: 50px; font-weight: bold; text-transform: uppercase; }
    .stButton>button:hover { background: #008fb3 !important; color: #fff !important; box-shadow: 0 0 15px #00d4ff; }
    .stTextInput>div>div>input { background: rgba(0, 212, 255, 0.1) !important; color: #00d4ff !important; border: 1px solid #00d4ff !important; text-align: center; }
    h1, h2, h3 { color: #00d4ff !important; text-shadow: 0 0 8px #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BACKEND UTILITIES ---
client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
MODEL_ID = "gemini-3-flash" 
HISTORY_FILE = "axom_history.csv"

def get_grade(perc):
    if perc >= 80: return "A*"
    if perc >= 70: return "A"
    if perc >= 60: return "B"
    if perc >= 50: return "C"
    return "D/E"

def robust_json_parser(text):
    try:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match: return json.loads(match.group(0))
        return []
    except: return []

def mark_visuals(image, marks_data):
    draw = ImageDraw.Draw(image)
    f_size = int(image.height * 0.035) 
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", f_size)
    except: font = ImageFont.load_default()
    ticks, notes = 0, []
    for m in marks_data:
        x, y = int((m.get('x', 50)/1000)*image.width), int((m.get('y', 50)/1000)*image.height)
        char = "✓" if m['type'] == 'tick' else "✕"
        draw.text((x, y), char, fill=(239, 68, 68), font=font)
        if m['type'] == 'tick': ticks += 1
        if 'comment' in m: notes.append(m['comment'])
    return image, ticks, notes

# --- 3. LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1
