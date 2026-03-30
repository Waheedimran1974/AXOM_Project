# 🎓 BITS.edu: The Neural Senior Examiner
> **Advanced Academic Assessment Infrastructure**

[![Engine: Gemini 2.0 Flash](https://img.shields.io/badge/Engine-Gemini_2.0_Flash-blueviolet)](https://deepmind.google/technologies/gemini/)
[![Status: Private Beta](https://img.shields.io/badge/Status-Private_Beta-green)](https://bits.edu)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red)](https://bits.edu)

## 🏛️ Executive Summary
**BITS.edu** is a high-performance academic assessment tool engineered for 2026 international standards. Utilizing the **Gemini 2.0 Flash** multimodal engine, BITS.edu simulates a Senior Examiner's workflow—visually marking papers, identifying logical gaps, and providing high-fidelity band-score reports in real-time.

---

## 🚀 Core Functionalities

### 1. The "Censora" Marking Engine
* **Visual Red-Pen Annotations:** Automated PDF manipulation using `PyMuPDF` to render strike-throughs and examiner comments directly onto the document.
* **Multimodal Vision:** High-speed processing of 12-page PDFs to detect structure, handwriting, and complex formatting.
* **Marking Rigor Toggles:** User-selectable modes including *Standard* and *Harsh* (strict examiner-level) assessment.

### 2. Integrated Revision Intelligence
* **Contextual Tutoring:** A built-in chat interface that retains document context for deep-dive revision sessions.
* **Linguistic Precision:** Focused evaluation of vocabulary, logic, and argumentative strength over minor mechanical errors.

### 3. Enterprise-Grade Safeguards
* **Tier 1 Billing Protection:** Hard-coded usage caps and budget alerts to maintain operational efficiency.
* **Scalable Quota Management:** Built-in rate limiting to manage high-traffic launch cycles.

---

## 🛠️ Technical Architecture

* **Frontend:** Streamlit (Optimized for low-latency mobile and desktop performance).
* **Core Engine:** Google Gemini 2.0 Flash (API-integrated).
* **PDF Intelligence:** `fitz` (PyMuPDF) for coordinate-based annotation rendering.
* **Deployment:** Streamlit Cloud / GitHub Enterprise.

---

## 📦 Rapid Deployment Guide

### 1. Prerequisites
Python 3.10+ and a Google AI Studio / Google Cloud API Key.

### 2. Installation
```bash
git clone [https://github.com/BITS-EDU/BITS-Core.git](https://github.com/BITS-EDU/BITS-Core.git)
cd BITS-Core
pip install -r requirements.txt
