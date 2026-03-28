import streamlit as st
from google import genai
import pandas as pd
import os
import json
import re
import smtplib
import random
import time
import textwrap
import matplotlib.pyplot as plt
import numpy as np
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pdf2image import convert_from_bytes
from fpdf import FPDF

# --- 1. HUD & STYLE ENGINE ---
st.set_page_config(page_title="AXOM | TOTAL INTERFACE", layout="wide")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle, #00122e 0%, #00050d 100%); color: #00d4ff; font-family: 'Courier New', monospace; }
    .future-frame { border: 2px solid #00d4ff; border-radius: 10px; padding: 40px; background: rgba(0, 20, 46, 0.9); box-shadow: 0 0 30px rgba(0, 212, 255, 0.3); text-align: center; }
    .stButton>button { width: 100%; background: #00d4ff !important; color: #000 !important; border: none !important; border-radius: 5px; height: 45px; font-weight: bold; text-transform: uppercase; }
    .ad-slot { background: #000; border: 1px dashed #ffd700; color: #ffd700; padding: 10px; text-align: center; font-size: 10px; margin-top: 10px; }
    .panel-card { background: rgba(0, 212, 255, 0.05); padding: 20px; border-radius: 10px; border: 1px solid rgba(0, 212, 255, 0.2); margin-bottom: 20px; }
    
    /* PRO PRICING CARDS CSS */
    .pricing-card { border-radius: 15px; padding: 20px; text-align: center; border: 2px solid #00d4ff; background: rgba(0, 20, 46, 0.8); margin-bottom: 15px;}
    .highlight { border: 3px solid #FF4B4B; box-shadow: 0px 4px 15px rgba(255, 75, 75, 0.3); transform: scale(1.02); }
    .vip-gold { background: linear-gradient(145deg, #FFD700, #FFA500); color: black !important; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MULTI-PANEL DATABASE LOGIC ---
DB_FILE = "axom_users.csv"
HISTORY_FILE = "axom_history.csv"

def init_db():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=["email", "tier", "credits", "joined"]).to_csv(DB_FILE, index=False)
    if not os.path.exists(HISTORY_FILE):
        pd.DataFrame(columns=["email", "date", "board", "subject", "score"]).to_csv(HISTORY_FILE, index=False)

def get_user_data(email):
    df = pd.read_csv(DB_FILE)
    if email in df['email'].values:
        user = df[df['email'] == email].iloc[0]
        return user['tier'], int(user['credits'])
    else:
        new_row = pd.DataFrame({"email": [email], "tier": ["Free"], "credits": [3], "joined": [datetime.now().strftime('%Y-%m-%d')]})
        pd.concat([df, new_row], ignore_index=True).to_csv(DB_FILE, index=False)
        return "Free", 3

def deduct_credit(email, amount=1):
    df = pd.read_csv(DB_FILE)
    df.loc[df['email'] == email, 'credits'] -= amount
    df.to_csv(DB_FILE, index=False)

def redeem_credits(email, code_input):
    """Automated Sales Engine: Validates code and upgrades user"""
    if code_input.startswith("AXOM-") and len(code_input) > 10:
        df = pd.read_csv(DB_FILE)
        # Determine tier and credits based on code pattern (Simple MVP logic)
        if "VIP" in code_input:
            df.loc[df['email'] == email, 'credits'] += 150
            df.loc[df['email'] == email, 'tier'] = "VIP"
        elif "CRUSH" in code_input:
            df.loc[df['email'] == email, 'credits'] += 60
            df.loc[df['email'] == email, 'tier'] = "Pro"
        else:
            df.loc[df['email'] == email, 'credits'] += 21
            if df.loc[df['email'] == email, 'tier'].values[0] == "Free":
                df.loc[df['email'] == email, 'tier'] = "Pro"
        df.to_csv(DB_FILE, index=False)
        return True
    return False

def log_scan_history(email, board, subject):
    df_hist = pd.read_csv(HISTORY_FILE)
    new_log = pd.DataFrame({"email": [email], "date": [datetime.now().strftime('%Y-%m-%d %H:%M')], "board": [board], "subject": [subject], "score": ["Scanned"]})
    pd.concat([df_hist, new_log], ignore_index=True).to_csv(HISTORY_FILE, index=False)

init_db()

# --- 3. THE VISUAL ENGINE (WATERMARKS & STICKY NOTES) ---
# Initialize Gemini
try:
    client = genai.Client(api_key=st.secrets["GENAI_API_KEY"])
except:
    client = None # Handles local testing without secrets
    
MODEL_ID = "gemini-2.5-flash"

def apply_watermark(base_image, logo_path="logo.jpg"):
    try:
        wm = Image.open(logo_path).convert("RGBA")
        wm_width = int(base_image.width * 0.5)
        w_percent = (wm_width / float(wm.size[0]))
        wm_height = int((float(wm.size[1]) * float(w_percent)))
        wm = wm.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
        
        alpha = wm.split()[3].point(lambda p: p * 0.15)
        wm.putalpha(alpha)
        
        overlay = Image.new('RGBA', base_image.size, (0,0,0,0))
        pos = ((base_image.width - wm_width) // 2, (base_image.height - wm_height) // 2)
        overlay.paste(wm, pos, mask=wm)
        return Image.alpha_composite(base_image.convert("RGBA"), overlay).convert("RGB")
    except:
        return base_image

def draw_sticky_note(img, x, y, mark_type, text):
    """Draws High-Visibility Ticks/Crosses and Premium Sticky Notes"""
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    
    # 1. SET COLORS & PARAMETERS
    tick_color = (0, 230, 118, 255)  # Neon Green
    cross_color = (255, 50, 50, 255) # Bright Red
    line_width = 6
    mark_size = 25

    # 2. DRAW THE MARK
    if mark_type == 'tick':
        draw.line([(x-mark_size, y), (x-mark_size//3, y+mark_size), (x+mark_size, y-mark_size)], fill=tick_color, width=line_width)
    else:
        draw.line([(x-mark_size, y-mark_size), (x+mark_size, y+mark_size)], fill=cross_color, width=line_width)
        draw.line([(x+mark_size, y-mark_size), (x-mark_size, y+mark_size)], fill=cross_color, width=line_width)

    # 3. DRAW THE STICKY NOTE
    if text and text.strip().lower() not in ["none", "correct", ""]:
        wrapped_text = textwrap.wrap(text, width=22)
        try: font = ImageFont.truetype("arial.ttf", 18)
        except: font = ImageFont.load_default()

        box_width = 220
        line_height = 22
        box_header_h = 8
        box_body_h = (len(wrapped_text) * line_height) + 20
        
        bx, by = x + 40, y - 20
        if bx + box_width > img.width: bx = x - box_width - 40

        # Shadow, Body, Header, Text
        draw.rectangle([bx+4, by+4, bx+box_width+4, by+box_body_h+4], fill=(0,0,0,80))
        draw.rectangle([bx, by, bx+box_width, by+box_body_h], fill=(255, 255, 150, 255), outline=(0,0,0,255), width=1)
        draw.rectangle([bx, by, bx+box_width, by+box_header_h], fill=(255, 210, 50, 255))
        
        ty = by + 15
        for line in wrapped_text:
            draw.text((bx + 12, ty), line, fill=(0, 0, 0, 255), font=font)
            ty += line_height

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def add_floating_footer(pdf):
    pdf.set_auto_page_break(False)
    pdf.set_y(-25) 
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 10, "POWERED BY AXOM NEURAL INTERFACE", align='R', ln=True)
    pdf.set_y(-15)
    pdf.set_font("Helvetica", 'I', 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, f"LEGAL: AI Evaluation. Verified by AXOM Systems on {datetime.now().strftime('%d/%m/%Y')
