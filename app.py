import streamlit as st
from google import genai
import os
import json
import re
import io
import time
import datetime
from PIL import Image, ImageDraw
from pdf2image import convert_from_bytes

# --- 1. HUD & INTERFACE STYLING ---
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
        background: #ff0055; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; position: absolute; top: -12px; right: 10px;
    }

    /* Ad & Focus Slots */
    .ad-slot-horizontal { width: 100%; padding: 20px; background: rgba(255,255,255,0.05); margin: 20px 0; border: 1px dashed #444; text-align: center; color: #777; }
    .focus-container { background: #000; border: 2px solid #00e5ff; padding: 50px; border-radius: 20px; text-align: center; box-shadow: 0px 0px 50px rgba(0, 229, 255, 0.1); }
    .big-clock { font-size: 5rem; font-weight: 900; color: #ffffff; font-family: 'Courier New'; margin: 20px 0; }
    
    /* Feedback Styling */
    .red-alert-box { background: linear-gradient(145deg, rgba(244, 67, 54, 0.1), rgba(0,0,0,0)); border: 1px solid #f44336; padding: 25px; border-radius: 8px; margin-bottom: 25px; }
    .chat-bubble { background: rgba(0, 229, 255, 0.1); border: 1px solid #00e5ff; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .user-bubble { background: rgba(255, 255, 255, 0.05); border: 1px solid #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 10px; text-align: right; }
    .stButton>button { width: 100%; background: linear-gradient(90deg, #00e5ff, #007bff) !important; color: #fff !important; font-weight: 900; border-radius: 4px; height: 50px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE UTILITIES & AI ---
try: 
    client = genai.Client(api_key=st.secrets.get("GENAI_API_KEY", ""))
except: 
    client = None

MODEL_ID = "gemini-2.5-flash"

def draw_mark(img, x, y, mark_type, index):
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    color = (46, 125, 5
