if menu == "NEURAL SCAN":
        st.title("🧠 NEURAL MARKER & ANALYTICS")
        if creds <= 0 and tier != "Admin": 
            st.error("INSUFFICIENT CREDITS.")
        else:
            c1, c2 = st.columns(2)
            b_n = c1.text_input("BOARD", "IGCSE")
            s_n = c2.selectbox("SUBJECT", ["Physics", "Chemistry", "English"])
            up_s = st.file_uploader("STUDENT SCRIPT", type=['pdf'])

            if up_s:
                if st.button("EXECUTE NEURAL EVALUATION"):
                    if tier == "Free": st.warning("AD DELAY: 3s"); time.sleep(3)
                    with st.spinner("AI IS SCANNING PEN STROKES & ANALYZING SYLLABUS..."):
                        try:
                            s_imgs = convert_from_bytes(up_s.read())
                            cost = max(1, (len(s_imgs) + 4) // 5)
                            
                            available_topics = list(VIDEO_DATABASE.get(s_n, {}).keys())
                            
                            # THE PRO REPORT PROMPT
                            p_txt = f"""
                            Act as a Lead Senior Examiner for {b_n} {s_n}. 
                            Analyze this student's work and return ONLY a JSON object with this structure:
                            {{
                                "marks": [{{ "type": "tick"|"cross", "x": 0-1000, "y": 0-1000, "note": "Specific technical feedback", "topic": "Name from {available_topics}" }}],
                                "summary": {{
                                    "grade_estimate": "A",
                                    "strengths": ["list 2 key points"],
                                    "weaknesses": ["list 2 key topics to fix"],
                                    "action_plan": "One sentence instruction"
                                }}
                            }}
                            """
                            
                            # Process the first page for the interactive view
                            r = client.models.generate_content(model=MODEL_ID, contents=[p_txt, s_imgs[0]])
                            raw_json = json.loads(re.search(r'\{.*\}', r.text, re.DOTALL).group(0))
                            
                            marks = raw_json.get("marks", [])
                            report = raw_json.get("summary", {})

                            # 1. DRAW THE INTERACTIVE CANVAS
                            marked_display = s_imgs[0].copy()
                            for m in marks:
                                px, py = int((m['x']/1000)*marked_display.width), int((m['y']/1000)*marked_display.height)
                                marked_display = draw_sticky_note(marked_display, px, py, m['type'], "") # Symbol only on image
                            
                            st.image(marked_display, caption="Neural Overlay Active", use_column_width=True)

                            # 2. THE EXPANDABLE STICKY NOTES AREA
                            st.markdown("### 🔍 INTERACTIVE STICKY NOTES")
                            st.write("Click a note to expand the teacher's feedback for that mark.")
                            
                            for idx, m in enumerate(marks):
                                icon = "✅" if m['type'] == 'tick' else "❌"
                                with st.expander(f"{icon} Mark #{idx+1} - Technical Feedback"):
                                    st.info(f"**Topic:** {m.get('topic', 'General')}\n\n**Guidance:** {m['note']}")

                            # 3. THE EXECUTIVE SUMMARY REPORT
                            st.markdown("---")
                            st.markdown(f"""
                                <div style="background: rgba(0, 212, 255, 0.1); border: 2px solid #00d4ff; padding: 25px; border-radius: 15px;">
                                    <h2 style="color: #00d4ff; margin-top: 0;">📊 PERFORMANCE REVIEW: {s_n.upper()}</h2>
                                    <div style="display: flex; justify-content: space-between;">
                                        <div style="text-align: center; flex: 1; border-right: 1px solid rgba(0,212,255,0.3);">
                                            <p style="margin:0; font-size: 14px;">ESTIMATED GRADE</p>
                                            <h1 style="color: #FFD700; margin:0; font-size: 48px;">{report.get('grade_estimate', 'N/A')}</h1>
                                        </div>
                                        <div style="flex: 2; padding-left: 20px;">
                                            <p style="color: #00e676; margin-bottom: 5px;"><strong>STRENGTHS:</strong> {', '.join(report.get('strengths', []))}</p>
                                            <p style="color: #ff5252; margin-bottom: 5px;"><strong>WEAKNESSES:</strong> {', '.join(report.get('weaknesses', []))}</p>
                                            <p style="color: #ffd700;"><strong>ACTION PLAN:</strong> {report.get('action_plan')}</p>
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                            # 4. DATA UPDATES
                            st.session_state.latest_mistakes = report.get('weaknesses', [])
                            st.session_state.last_subject = s_n
                            deduct_credit(st.session_state.target_email, cost)
                            log_scan_history(st.session_state.target_email, b_n, s_n)

                            st.success("ANALYSIS COMPLETE. Head to REVISION HUB for your prescriptions.")
                            
                        except Exception as e:
                            st.error(f"NEURAL ERROR: {e}")
