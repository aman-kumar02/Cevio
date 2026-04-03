import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from pypdf import PdfReader
from PIL import Image
import re

icon = Image.open("assets/cevio_logo.png")
st.set_page_config(page_title="Cevio", page_icon=icon, layout="wide", initial_sidebar_state="collapsed")

# --- Initialize Session State ---
state_defaults = {
    "analysis_ready": False,
    "score": 0,
    "gaps": "",
    "fixes": "",
    "email_draft": "",
    "message_draft": ""
}
for key, value in state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Master CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    [data-testid="stAppViewContainer"] { background: radial-gradient(circle at center, #1e1b4b 0%, #09090b 100%); color: #f8fafc; }
    [data-testid="stHeader"] { background: transparent !important; }
    *, *:focus, *:focus-visible, *:focus-within, *:active { outline: none !important; outline-color: transparent !important; -webkit-tap-highlight-color: transparent !important; }

    [data-testid="stFileUploader"] {
        background: rgba(30, 27, 75, 0.4) !important; backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 16px !important; padding: 0.8rem 1rem !important; 
        box-shadow: inset 0 0 20px rgba(255,255,255,0.02), 0 8px 32px rgba(0,0,0,0.3) !important; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important; 
    }
    [data-testid="stFileUploader"]:hover { border-color: #22d3ee !important; box-shadow: 0 0 25px rgba(34, 211, 238, 0.2) !important; }
    [data-testid="stFileUploader"] section, [data-testid="stFileUploader"] div, [data-testid="stFileUploadDropzone"] { background-color: transparent !important; background: transparent !important; border: none !important; box-shadow: none !important; }
    [data-testid="stFileUploadDropzone"] { padding: 0 !important; display: flex !important; align-items: center !important; min-height: 40px !important; }
    [data-testid="stFileUploadDropzone"] > div > div::before, [data-testid="stFileUploadDropzone"] > div > div > span { display: none !important; }
    [data-testid="stFileUploadDropzone"] small { color: #94a3b8 !important; font-weight: 600 !important; margin-left: 15px !important; }
    [data-testid="stFileUploader"] button {
        background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(34, 211, 238, 0.4) !important; border-radius: 8px !important; color: #22d3ee !important; 
        font-weight: 600 !important; padding: 0.5rem 1.5rem !important; margin: 0 !important; transition: all 0.3s ease !important;
    }
    [data-testid="stFileUploader"] button:hover { background: rgba(34, 211, 238, 0.1) !important; border-color: #22d3ee !important; }

    [data-testid="stTextArea"] > div, [data-testid="stTextArea"] div[data-baseweb="base-input"], [data-testid="stTextArea"] div[data-baseweb="base-input"] > div { background-color: transparent !important; background: transparent !important; border: none !important; box-shadow: none !important; }
    [data-testid="stTextArea"] textarea {
        background: rgba(30, 27, 75, 0.4) !important; backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important; 
        border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 16px !important; padding: 1.2rem 1.5rem !important; color: white !important;
        font-size: 1rem !important; height: 65px !important; min-height: 65px !important; overflow: hidden !important; 
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important; box-shadow: inset 0 0 20px rgba(255,255,255,0.02), 0 8px 32px rgba(0,0,0,0.3) !important; 
    }
    [data-testid="stTextArea"] textarea:hover, [data-testid="stTextArea"] textarea:focus { height: 250px !important; border-color: #22d3ee !important; box-shadow: 0 0 25px rgba(34, 211, 238, 0.2) !important; overflow-y: auto !important; }

    [data-testid="stToggle"] label p { font-weight: 600 !important; color: #cbd5e1 !important; letter-spacing: 0.5px; }
    .brand-container { display: flex; align-items: center; justify-content: flex-start; gap: 16px; margin-bottom: 2rem; padding-left: 0.5rem; }
    .brand-text { font-size: 3.5rem; font-weight: 800; letter-spacing: -1.5px; background: linear-gradient(135deg, #a78bfa, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 10px 30px rgba(167, 139, 250, 0.2); }
    .sleek-header { font-size: 0.9rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; color: #cbd5e1; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 10px; }
    [data-testid="stButton"] button {
        background: linear-gradient(135deg, #a78bfa, #22d3ee) !important; color: #0f172a !important; border: none !important; border-radius: 50px !important; 
        padding: 1.5rem 0 !important; font-size: 1.1rem !important; font-weight: 800 !important; letter-spacing: 1.5px !important; text-transform: uppercase; 
        box-shadow: 0 10px 30px rgba(34, 211, 238, 0.4) !important; transition: all 0.3s ease !important; width: 100%; margin-top: 1rem;
    }
    [data-testid="stButton"] button:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 15px 40px rgba(34, 211, 238, 0.6) !important; }
    [data-testid="stButton"] button:disabled { background: rgba(255, 255, 255, 0.05) !important; color: #475569 !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; box-shadow: none !important; transform: none !important; cursor: not-allowed !important; }

    .fullscreen-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px); z-index: 999999; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 2rem; }
    .glow-spinner { width: 70px; height: 70px; border-radius: 50%; border: 4px solid rgba(255,255,255,0.05); border-top-color: #22d3ee; border-bottom-color: #a78bfa; animation: spin 1s infinite; filter: drop-shadow(0 0 20px rgba(34, 211, 238, 0.8)); }
    @keyframes spin { 100% { transform: rotate(360deg); } }
    .loading-text { font-size: 1.2rem; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; background: linear-gradient(90deg, #a78bfa, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; filter: drop-shadow(0 0 10px rgba(34,211,238,0.5)); } 50% { opacity: 0.5; filter: none; } }

    .stMarkdown ul { list-style: none !important; padding-left: 0 !important; }
    .stMarkdown ul li { position: relative; padding: 18px 24px 18px 50px !important; background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; margin-bottom: 16px !important; color: #cbd5e1 !important; font-size: 1.05rem; line-height: 1.7; transition: all 0.3s ease; }
    .stMarkdown ul li:hover { transform: translateX(8px); background: rgba(34, 211, 238, 0.05); border-color: rgba(34, 211, 238, 0.3); box-shadow: 0 8px 20px rgba(0,0,0,0.2); }
    .stMarkdown ul li::before { content: "✦"; position: absolute; left: 20px; top: 18px; color: #22d3ee; font-size: 1.2rem; filter: drop-shadow(0 0 8px rgba(34, 211, 238, 0.8)); }
    .stMarkdown ul li strong { color: #a78bfa; font-weight: 700; letter-spacing: 0.5px; }

    .stTabs [data-baseweb="tab-list"] { background: rgba(255, 255, 255, 0.03); border-radius: 16px; padding: 8px; gap: 8px; border-bottom: none !important; }
    div[data-baseweb="tab-highlight"] { display: none !important; }
    .stTabs [data-baseweb="tab"] { flex: 1; justify-content: center; color: #64748b !important; font-weight: 600 !important; padding: 12px 0 !important; border-radius: 10px !important; border: none !important; background: transparent; transition: all 0.3s ease; }
    .stTabs [aria-selected="true"] { color: #ffffff !important; background: linear-gradient(135deg, rgba(167, 139, 250, 0.4), rgba(34, 211, 238, 0.4)) !important; border: 1px solid rgba(255,255,255,0.1) !important; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    </style>
""", unsafe_allow_html=True)

# --- API Setup ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
except:
    st.error("⚠️ API Key missing. Please configure your Streamlit Secrets.")
    st.stop()

# --- Header ---
st.markdown("""
    <div class="brand-container">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#grad1)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 12px rgba(167, 139, 250, 0.6));">
            <defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#a78bfa;stop-opacity:1" /><stop offset="100%" style="stop-color:#22d3ee;stop-opacity:1" /></linearGradient></defs>
            <circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>
        </svg>
        <div class="brand-text">CEVIO</div>
    </div>
""", unsafe_allow_html=True)

col_left, space, col_right = st.columns([1, 0.1, 1])

with col_left:
    typewriter_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;600;800&display=swap');
            body { margin: 0; display: flex; flex-direction: column; justify-content: center; height: 100%; background: transparent; font-family: 'Plus Jakarta Sans', sans-serif; padding: 2rem 2rem 2rem 0; }
            .title-small { color: #94a3b8; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; margin-bottom: 1rem; }
            .typewriter-container { font-size: 3.2rem; font-weight: 800; line-height: 1.2; height: 180px; }
            .type-text { background: linear-gradient(135deg, #f8fafc, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .highlight { background: linear-gradient(135deg, #a78bfa, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .cursor { display: inline-block; width: 5px; height: 3.5rem; background: #22d3ee; margin-left: 8px; animation: blink 0.8s infinite; vertical-align: bottom; }
            @keyframes blink { 50% { opacity: 0; } }
            .subtitle { color: #64748b; font-size: 1.1rem; line-height: 1.6; margin-top: 1rem; font-weight: 300; }
        </style>
    </head>
    <body>
        <div class="title-small">Why Tailor Your Resume?</div>
        <div class="typewriter-container"><span id="text" class="type-text"></span><span class="cursor"></span></div>
        <div class="subtitle">AI-driven analysis to align your skills directly with the recruiter's requirements. Processed securely in-memory. No Data is Stored. </div>
        <script>
            const phrases = ["Beat the <span class='highlight'>ATS Algorithms</span> instantly.", "Unlock <span class='highlight'>3x more</span> interview calls.", "Highlight exactly what <span class='highlight'>recruiters</span> want.", "Tailor your resume in <span class='highlight'>seconds</span>."];
            let i = 0, j = 0, isDeleting = false; const textEl = document.getElementById('text');
            function type() {
                const currentPhrase = phrases[i]; let currentText = currentPhrase.substring(0, j);
                textEl.innerHTML = currentText; let speed = isDeleting ? 30 : 60;
                if (!isDeleting && j === currentPhrase.length) { speed = 2500; isDeleting = true; }
                else if (isDeleting && j === 0) { isDeleting = false; i = (i + 1) % phrases.length; speed = 500; }
                j += isDeleting ? -1 : 1;
                if (currentPhrase.charAt(j) === '<' && !isDeleting) { j = currentPhrase.indexOf('>', j) + 1; }
                else if (currentPhrase.charAt(j-1) === '>' && isDeleting) { j = currentPhrase.lastIndexOf('<', j) - 1; }
                setTimeout(type, speed);
            }
            setTimeout(type, 1000);
        </script>
    </body>
    </html>
    """
    components.html(typewriter_html, height=400)

with col_right:
    st.markdown("<div class='sleek-header'>🎯 Target Job Description</div>", unsafe_allow_html=True)
    jd_text = st.text_area("", placeholder="Paste the target job description here...", label_visibility="collapsed")

    st.markdown("<br><div class='sleek-header'>📄 Upload Resume (PDF)</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    inputs_ready = bool(uploaded_file and jd_text)
    submit = st.button("Initialize Deep Scan", disabled=not inputs_ready, use_container_width=True)

loading_placeholder = st.empty()

# Temporary variables for triggering actions post-process
should_scroll = False
should_trigger_balloons = False

# --- Processing Logic ---
if submit and inputs_ready:
    loading_placeholder.markdown("""
        <div class="fullscreen-overlay">
            <div class="glow-spinner"></div>
            <div class="loading-text">Executing Deep Scan & Semantic Matching...</div>
        </div>
    """, unsafe_allow_html=True)

    try:
        reader = PdfReader(uploaded_file)
        resume_text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])

        prompt = (
                "Act as an Expert Technical Recruiter. Analyze this Resume against the Job Description (JD).\n"
                "You must be highly detailed. Provide deeply relevant insights.\n\n"
                "SCORING: Start at 100%. Deduct points heavily for missing core tech stack, missing years of experience, or missing hard requirements.\n\n"
                "OUTPUT STRICTLY IN THIS EXACT FORMAT.\n"
                "CRITICAL INSTRUCTION: DO NOT print literal placeholders like '[Specific Missing Skill 1]'. You MUST replace the bold text with an actual 2-4 word descriptive title.\n\n"
                "SCORE: [Insert Number 0-100]\n"
                "GAPS:\n"
                "* **[Name of Missing Skill]:** [Highly detailed explanation of why it is relevant based on the JD]\n"
                "* **[Name of Missing Skill]:** [Highly detailed explanation...]\n"
                "FIXES:\n"
                "* **[Short Name of Fix]:** [Write exactly how the candidate should re-word a specific bullet point]\n"
                "* **[Short Name of Fix]:** [Write exactly how to re-word...]\n"
                "EMAIL:\n"
                "Subject: [Write a compelling subject line]\n"
                "Dear [Name],\n"
                "[Write a FULLY COMPLETE, professional 3-sentence email asking for a referral. End with a professional sign-off.]\n"
                "MESSAGE:\n"
                "[Write a FULLY COMPLETE 2-sentence LinkedIn direct message asking for a referral.]\n\n"
                "JD:\n" + jd_text + "\n\n"
                                    "Resume:\n" + resume_text
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=2048, temperature=0.4)
        )
        raw_text = response.text

        score_match = re.search(r"SCORE:\s*(\d+)", raw_text)
        st.session_state.score = int(score_match.group(1)) if score_match else 0


        def get_section(start_tag, end_tag, text):
            try:
                extracted = text.split(start_tag)[1].split(end_tag)[0].strip()
                clean_lines = [line for line in extracted.split('\n') if line.strip() != '**' and line.strip() != '*']
                return '\n'.join(clean_lines).strip()
            except:
                return "Analysis detailed breakdown not available."


        st.session_state.gaps = get_section("GAPS:", "FIXES:", raw_text)
        st.session_state.fixes = get_section("FIXES:", "EMAIL:", raw_text)
        st.session_state.email_draft = get_section("EMAIL:", "MESSAGE:", raw_text)

        try:
            message_draft = raw_text.split("MESSAGE:")[1].strip()
            st.session_state.message_draft = "\n".join(
                [line for line in message_draft.split('\n') if line.strip() != '**'])
        except:
            st.session_state.message_draft = "Message draft not available."

        st.session_state.analysis_ready = True
        should_scroll = True
        should_trigger_balloons = True

        loading_placeholder.empty()

    except Exception as e:
        loading_placeholder.empty()
        st.error(f"An error occurred during processing: {e}")

# --- Display Results ---
st.markdown('<div id="results-anchor" style="padding-top: 20px;"></div>', unsafe_allow_html=True)

if st.session_state.analysis_ready:
    st.markdown(
        '<div style="width: 100%; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent); margin: 20px 0 40px 0;"></div>',
        unsafe_allow_html=True)
    res_left, space_mid, res_right = st.columns([2.5, 0.2, 1.2])

    with res_left:
        tab1, tab2, tab3 = st.tabs(["🚩 Detected Gaps", "💡 Strategic Fixes", "📩 Outreach Drafts"])
        with tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(st.session_state.gaps)
        with tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(st.session_state.fixes)
        with tab3:
            st.markdown("<br>", unsafe_allow_html=True)
            use_email = st.toggle("Switch to Email Outline format", value=False)

            selected_draft = st.session_state.email_draft if use_email else st.session_state.message_draft
            active_title = "✉️ Email Outline" if use_email else "💬 LinkedIn Direct Message"

            st.markdown(
                f"<div style='color: #22d3ee; font-weight: 700; letter-spacing: 1px; margin-bottom: 10px; margin-top: 10px; font-size: 0.95rem; text-transform: uppercase;'>{active_title}</div>",
                unsafe_allow_html=True)
            safe_draft = selected_draft.replace('\n', '<br>')
            st.markdown(
                f'<div style="background: rgba(255,255,255,0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.08); padding: 30px; border-radius: 20px; line-height: 1.8; color: #cbd5e1;">{safe_draft}</div>',
                unsafe_allow_html=True)

    with res_right:
        animation_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@800&display=swap');
                body {{ margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background: transparent; font-family: 'Plus Jakarta Sans', sans-serif; }}
                .score-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(255,255,255,0.03); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 24px; padding: 3rem 2rem; box-shadow: 0 10px 40px rgba(0,0,0,0.2); width: 100%; box-sizing: border-box; }}
                .circular-progress {{ width: 180px; height: 180px; border-radius: 50%; background: conic-gradient(#22d3ee 0deg, rgba(255,255,255,0.05) 0deg); display: flex; justify-content: center; align-items: center; position: relative; box-shadow: 0 0 30px rgba(34, 211, 238, 0.2); }}
                .circular-progress::before {{ content: ""; position: absolute; width: 150px; height: 150px; background: #0f111a; border-radius: 50%; box-shadow: inset 0 4px 10px rgba(0,0,0,0.5); }}
                .inner-text {{ position: relative; font-size: 3.5rem; font-weight: 800; color: white; background: linear-gradient(135deg, #ffffff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                .score-title {{ color: #cbd5e1; margin-top: 2.5rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; font-size: 1.1rem; text-align: center; margin-bottom: 0; }}
            </style>
        </head>
        <body>
            <div class="score-container">
                <div class="circular-progress" id="anim-circle"><div class="inner-text"><span id="anim-number">0</span>%</div></div>
                <h3 class="score-title">ATS Alignment</h3>
            </div>
            <script>
                const targetScore = parseInt("{st.session_state.score}") || 0;
                let currentScore = 0; const duration = 1500; const intervalTime = 15;
                const numEl = document.getElementById('anim-number'); const circEl = document.getElementById('anim-circle');
                if (targetScore > 0) {{
                    const increment = targetScore / (duration / intervalTime);
                    const timer = setInterval(() => {{
                        currentScore += increment;
                        if (currentScore >= targetScore) {{ currentScore = targetScore; clearInterval(timer); }}
                        numEl.innerText = Math.round(currentScore);
                        circEl.style.background = "conic-gradient(#22d3ee " + (currentScore * 3.6) + "deg, rgba(255,255,255,0.05) 0deg)";
                    }}, intervalTime);
                }}
            </script>
        </body>
        </html>
        """
        components.html(animation_html, height=350)

# --- Interactions & Animations ---
if should_scroll:
    scroll_html = "<script>const target = window.parent.document.getElementById('results-anchor'); if (target) { target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }</script>"
    components.html(scroll_html, height=0, width=0)

if should_trigger_balloons and st.session_state.score >= 50:
    st.balloons()

# --- Footer ---
st.markdown(
    '<div style="margin-top: 100px; padding-bottom: 20px; text-align: right; font-size: 0.8rem; color: #64748b; font-weight: 600; letter-spacing: 0.5px;">Designed by Aman</div>',
    unsafe_allow_html=True)