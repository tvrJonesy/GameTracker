import streamlit as st
from pages import step1_upload, step2_stitch, step3_tracking, step3b_squad, step4_output, step5_processing

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GameTracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background-color: #0b1a0e;
    color: #f0f4ee;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 900px; }

/* ── Wordmark header ── */
.ml-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0 1.25rem 0;
    border-bottom: 1px solid rgba(200,245,66,0.15);
    margin-bottom: 2rem;
}
.ml-wordmark {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 4px;
    color: #f0f4ee;
}
.ml-wordmark span { color: #c8f542; }
.ml-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    color: #c8f542;
    border: 1px solid rgba(200,245,66,0.35);
    padding: 4px 10px;
    border-radius: 4px;
    text-transform: uppercase;
}

/* ── Step progress bar ── */
.step-bar {
    display: flex;
    align-items: center;
    gap: 0;
    margin-bottom: 2.5rem;
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    flex: 1;
    position: relative;
}
.step-item:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 16px;
    left: 55%;
    width: 90%;
    height: 2px;
    background: rgba(200,245,66,0.15);
}
.step-item.done:not(:last-child)::after { background: rgba(200,245,66,0.5); }
.step-dot {
    width: 32px; height: 32px;
    border-radius: 50%;
    border: 2px solid rgba(200,245,66,0.2);
    background: #0b1a0e;
    display: flex; align-items: center; justify-content: center;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #7a9070;
    position: relative;
    z-index: 1;
}
.step-dot.active {
    border-color: #c8f542;
    background: rgba(200,245,66,0.12);
    color: #c8f542;
}
.step-dot.done {
    border-color: rgba(200,245,66,0.5);
    background: rgba(200,245,66,0.08);
    color: #c8f542;
}
.step-name {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #7a9070;
    text-align: center;
}
.step-name.active { color: #c8f542; }

/* ── Card ── */
.ml-card {
    background: #162d1a;
    border: 1px solid rgba(200,245,66,0.12);
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
}
.ml-card-accent {
    border-top: 2px solid #c8f542;
}

/* ── Section heading ── */
.ml-step-heading {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.25rem;
}
.ml-step-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 2px;
    color: #c8f542;
    background: rgba(200,245,66,0.1);
    border: 1px solid rgba(200,245,66,0.3);
    padding: 3px 8px;
    border-radius: 4px;
    text-transform: uppercase;
}
.ml-step-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 2px;
    color: #f0f4ee;
}

/* ── Info / warn boxes ── */
.ml-info {
    background: rgba(64,196,255,0.06);
    border: 1px solid rgba(64,196,255,0.2);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
    color: #9ecfe8;
    line-height: 1.6;
    margin: 0.75rem 0;
}
.ml-warn {
    background: rgba(255,176,32,0.07);
    border: 1px solid rgba(255,176,32,0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
    color: #f0b84a;
    line-height: 1.6;
    margin: 0.75rem 0;
}
.ml-success {
    background: rgba(200,245,66,0.07);
    border: 1px solid rgba(200,245,66,0.3);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
    color: #c8f542;
    line-height: 1.6;
    margin: 0.75rem 0;
}

/* ── Nav buttons ── */
.stButton > button {
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 3px !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}

/* Primary next button */
div[data-testid="column"]:last-child .stButton > button {
    background: #c8f542 !important;
    color: #0b1a0e !important;
    border: none !important;
    padding: 0.6rem 2rem !important;
}
div[data-testid="column"]:last-child .stButton > button:hover {
    box-shadow: 0 0 24px rgba(200,245,66,0.4) !important;
}

/* Back button */
div[data-testid="column"]:first-child .stButton > button {
    background: transparent !important;
    color: #7a9070 !important;
    border: 1px solid rgba(200,245,66,0.2) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background-color: #0b1a0e !important;
    border-color: rgba(200,245,66,0.2) !important;
    color: #f0f4ee !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #c8f542 !important;
    box-shadow: 0 0 0 1px #c8f542 !important;
}

/* ── File uploader ── */
.stFileUploader > div {
    background: rgba(200,245,66,0.03) !important;
    border: 2px dashed rgba(200,245,66,0.3) !important;
    border-radius: 8px !important;
}

/* ── Slider ── */
.stSlider > div > div > div > div {
    background: #c8f542 !important;
}

/* ── Colour picker ── */
.stColorPicker > div { border-color: rgba(200,245,66,0.2) !important; }

/* ── Divider ── */
hr { border-color: rgba(200,245,66,0.1) !important; }

/* ── Metric ── */
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2rem !important;
    color: #c8f542 !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    color: #7a9070 !important;
}

/* ── Progress ── */
.stProgress > div > div > div {
    background: #c8f542 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0f2312 !important;
    border-color: rgba(200,245,66,0.15) !important;
    color: #c8f542 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ──────────────────────────────────────────────────────
STEPS = [
    ("01", "Upload"),
    ("02", "Stitch"),
    ("03", "Tracking"),
    ("03b", "Squad"),
    ("04", "Output"),
    ("05", "Process"),
]

if "step" not in st.session_state:
    st.session_state.step = 0

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ml-header">
  <div class="ml-wordmark">Match<span>Lens</span></div>
  <div class="ml-tag">⚽ 9v9 · U11</div>
</div>
""", unsafe_allow_html=True)

# ── Progress bar ───────────────────────────────────────────────────────────
current = st.session_state.step
dots_html = ""
for i, (num, name) in enumerate(STEPS):
    dot_cls = "active" if i == current else ("done" if i < current else "")
    name_cls = "active" if i == current else ""
    label = "✓" if i < current else num
    dots_html += f"""
    <div class="step-item {'done' if i < current else ''}">
      <div class="step-dot {dot_cls}">{label}</div>
      <div class="step-name {name_cls}">{name}</div>
    </div>"""

st.markdown(f'<div class="step-bar">{dots_html}</div>', unsafe_allow_html=True)

# ── Route to current step ──────────────────────────────────────────────────
step_modules = [
    step1_upload,
    step2_stitch,
    step3_tracking,
    step3b_squad,
    step4_output,
    step5_processing,
]

step_modules[current].render()

# ── Navigation buttons ─────────────────────────────────────────────────────
st.markdown("---")
col_back, col_space, col_next = st.columns([1, 3, 1])

with col_back:
    if current > 0:
        if st.button("← BACK"):
            st.session_state.step -= 1
            st.rerun()

with col_next:
    if current < len(STEPS) - 1:
        label = "NEXT →" if current < len(STEPS) - 2 else "▶ PROCESS MATCH"
        if st.button(label):
            st.session_state.step += 1
            st.rerun()
