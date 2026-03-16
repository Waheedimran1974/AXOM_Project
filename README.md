# AXOM: Senior Examiner AI

AXOM is a high-performance academic assessment tool designed to provide rigorous, examiner-level feedback on English language papers. Built for 2026 academic standards, it utilizes the Gemini 2.0 Flash engine to visually mark PDFs with a red pen and provide detailed band-score reports.

## Core Features

* Senior Lecturer Persona: Feedback delivered with high academic rigor and critical analysis.
* Visual Red-Pen Marking: Automatically draws strike-throughs on PDF errors and adds explanatory comments.
* Multi-Rigor Assessment: Toggle between Standard and Harsh marking modes.
* Ad-Gate Processing: Integrated 30-second delay for monetization and processing transparency.
* Export Options: Students can download annotated PDFs and print official reports.
* Submission History: Track progress across multiple attempts within a single session.

## Technical Stack

* Language: Python
* Framework: Streamlit
* AI Engine: Google Gemini 2.0 Flash
* PDF Engine: PyMuPDF (fitz)
* Cloud Hosting: Streamlit Cloud / GitHub

## Installation and Local Setup

1. Clone the Repository:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/AXOM.git](https://github.com/YOUR_USERNAME/AXOM.git)
   cd AXOM
   pip install -r requirements.txt
   GEMINI_KEY = "your_api_key_here"
   streamlit run app.py
   © 2026 AXOM Global. All Rights Reserved.
