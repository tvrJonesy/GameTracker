"""
GameTracker — Single-page football match video processor.
No wizard. No settings sliders. Just pick files, enter names, and process.
"""

import streamlit as st
from utils.drive_queue import (
    get_raw_files, get_heartbeat, submit_job,
    get_status, build_job_payload
)
import time
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="GameTracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS — pitch-green dark theme
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;500;700&display=swap');

:root {
    --pitch-dark: #0b1a0e;
    --pitch-mid: #1a2e1f;
    --accent: #c8f542;
    --text: #f0f4ee;
    --muted: #7a9070;
}

.stApp {
    background: linear-gradient(180deg, var(--pitch-dark) 0%, #0d1f11 100%);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Bebas Neue', sans-serif;
    color: var(--accent);
    letter-spacing: 0.05em;
}

.stButton button {
    background: var(--accent);
    color: var(--pitch-dark);
    border: none;
    font-weight: 700;
    font-size: 1rem;
    border-radius: 8px;
    padding: 0.6rem 1.5rem;
    transition: all 0.2s;
}
.stButton button:hover {
    background: #d4f95e;
    transform: translateY(-2px);
}
.stButton button:disabled {
    background: #3a4a3d;
    color: #5a6a5d;
}

.stTextInput input, .stSelectbox select, .stDateInput input {
    background: var(--pitch-mid);
    border: 1px solid rgba(200,245,66,0.2);
    color: var(--text);
    border-radius: 6px;
}

div[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}

.card {
    background: var(--pitch-mid);
    border: 1px solid rgba(200,245,66,0.15);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.status-ok {
    color: var(--accent);
    font-weight: 600;
}
.status-warn {
    color: #ffb020;
    font-weight: 600;
}
.status-error {
    color: #ff4545;
    font-weight: 600;
}

.info-box {
    background: rgba(200,245,66,0.08);
    border-left: 3px solid var(--accent);
    padding: 0.75rem 1rem;
    border-radius: 4px;
    margin: 0.5rem 0;
    font-size: 0.88rem;
    line-height: 1.6;
}

.name-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    margin-top: 0.75rem;
}

.name-cell {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
}

.name-num {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    color: var(--muted);
    min-width: 28px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

KIT_COLOURS = {
    "Red": "#ef4444", "Blue": "#3b82f6", "Green": "#10b981",
    "Amber": "#f59e0b", "White": "#f5f5f0", "Black": "#1e1e2e",
    "Purple": "#a855f7", "Orange": "#f97316", "Pink": "#ec4899",
    "Teal": "#14b8a6", "Navy": "#1e3a5f", "Yellow": "#eab308",
}

def fmt_size(size_mb):
    return f"{size_mb / 1024:.1f} GB" if size_mb >= 1024 else f"{size_mb:.0f} MB"

def init_session_state():
    defaults = {
        "home_name": "", "away_name": "",
        "home_colour": "#ef4444", "away_colour": "#3b82f6",
        "squad_home": {}, "squad_away": {},
        "cam_a_filename": None, "cam_b_filename": None,
        "cam_a_ready": False, "cam_b_ready": False,
        "_raw_files_cache": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

init_session_state()

st.markdown("# ⚽ GAMETRACKER")
st.markdown(
    '<p style="font-size:0.95rem;color:var(--muted);margin-top:-0.5rem">'
    'Dual-camera football match processor · Automatic stitching, player tracking, ball-following camera'
    '</p>',
    unsafe_allow_html=True
)

# ── Folder ID check ───────────────────────────────────────────────────────────
folder_id = ""
try:
    folder_id = st.secrets.get("gdrive_folder_id", "")
except Exception:
    pass

if not folder_id:
    folder_id = st.session_state.get("gdrive_folder_id", "")

if not folder_id or len(folder_id) < 20:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📁 Google Drive Setup")
    st.markdown(
        '<div class="info-box">'
        'Enter your GameTracker Google Drive folder ID. '
        'Find it in the browser URL when you open your GameTracker folder: '
        '<code>drive.google.com/drive/folders/<strong>THIS_PART</strong></code>'
        '</div>',
        unsafe_allow_html=True
    )
    st.text_input(
        "Folder ID",
        placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
        key="gdrive_folder_id",
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

st.session_state["gdrive_folder_id"] = folder_id

# ── Active job check ──────────────────────────────────────────────────────────
active_job_id = st.session_state.get("active_job_id")

if active_job_id:
    # Show processing view
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Processing")
    
    status = get_status(folder_id, active_job_id)
    
    if status is None:
        st.markdown('<p class="status-warn">⏳ Waiting for Colab to pick up job…</p>',
                    unsafe_allow_html=True)
    elif status.get("status") == "error":
        st.markdown(f'<p class="status-error">❌ Error: {status.get("error", "Unknown")}</p>',
                    unsafe_allow_html=True)
        if st.button("Try Again"):
            st.session_state.pop("active_job_id", None)
            st.rerun()
    elif status.get("status") == "done":
        st.balloons()
        st.markdown('<p class="status-ok">✓ Complete! Video saved to GameTracker/output/</p>',
                    unsafe_allow_html=True)
        if st.button("Process Another Match"):
            for k in ["active_job_id", "cam_a_ready", "cam_b_ready",
                      "cam_a_filename", "cam_b_filename", "squad_home", "squad_away"]:
                st.session_state.pop(k, None)
            st.rerun()
    else:
        stage_name = status.get("stage", "Processing")
        progress   = status.get("progress", 0)
        message    = status.get("message", "")
        
        st.markdown(f'<p class="status-ok">▶ {stage_name}</p>', unsafe_allow_html=True)
        if message:
            st.markdown(f'<p style="font-size:0.85rem;color:var(--muted)">{message}</p>',
                        unsafe_allow_html=True)
        st.progress(progress / 100)
        
        st.markdown('</div>', unsafe_allow_html=True)
        time.sleep(5)
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# SETUP VIEW
# ══════════════════════════════════════════════════════════════════════════════

# ── Colab status ──────────────────────────────────────────────────────────────
hb = get_heartbeat(folder_id)
colab_alive = hb is not None and hb.get("alive", False)

col_status, col_btn = st.columns([3, 1])
with col_status:
    if colab_alive:
        gpu = hb.get("gpu", "GPU")
        jobs = hb.get("job_count", 0)
        st.markdown(
            f'<p class="status-ok">● Colab Ready — {gpu} · {jobs} job(s) processed</p>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p class="status-warn">○ Colab Not Running — '
            'open your notebook and click Run All</p>',
            unsafe_allow_html=True
        )
with col_btn:
    colab_url = ""
    try:
        colab_url = st.secrets.get("colab_notebook_url", "")
    except Exception:
        pass
    if colab_url:
        st.link_button("Open Colab →", colab_url, use_container_width=True)

st.markdown("---")

# ── File picker ───────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 📷 Select Footage")

files = st.session_state.get("_raw_files_cache")

col_refresh, col_files_status = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        with st.spinner("Scanning Drive..."):
            files = get_raw_files(folder_id)
            st.session_state["_raw_files_cache"] = files
with col_files_status:
    if files is None:
        st.markdown(
            '<p style="color:var(--muted);padding-top:0.5rem">'
            'Click Refresh to scan GameTracker/raw/ for video files</p>',
            unsafe_allow_html=True
        )
    elif len(files) == 0:
        st.markdown(
            '<p class="status-warn" style="padding-top:0.5rem">'
            'No files found — copy videos to GameTracker/raw/ in Drive</p>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<p class="status-ok" style="padding-top:0.5rem">'
            f'✓ {len(files)} file(s) found</p>',
            unsafe_allow_html=True
        )

if files and len(files) > 0:
    options = ["— select —"] + [
        f"{f['name']}  ({fmt_size(f.get('size_mb', 0))})" for f in files
    ]
    label_to_name = {
        f"{f['name']}  ({fmt_size(f.get('size_mb', 0))})": f['name'] for f in files
    }
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown(
        "**Camera A** = left half of pitch (lens faces right) · "
        "**Camera B** = right half (lens faces left)"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**📷 Camera A — Left Half**")
        sel_a = st.selectbox(
            "Camera A",
            options=options,
            key="cam_a_select",
            label_visibility="collapsed",
        )
        if sel_a != "— select —":
            st.session_state["cam_a_filename"] = label_to_name[sel_a]
            st.session_state["cam_a_ready"] = True
        else:
            st.session_state["cam_a_ready"] = False
    
    with col_b:
        st.markdown("**📷 Camera B — Right Half**")
        sel_b = st.selectbox(
            "Camera B",
            options=options,
            key="cam_b_select",
            label_visibility="collapsed",
        )
        if sel_b != "— select —":
            st.session_state["cam_b_filename"] = label_to_name[sel_b]
            st.session_state["cam_b_ready"] = True
        else:
            st.session_state["cam_b_ready"] = False

st.markdown('</div>', unsafe_allow_html=True)

# ── Match details ─────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### ⚽ Match Details")

col1, col2 = st.columns(2)
with col1:
    home_name = st.text_input("Home Team", placeholder="e.g. Rovers FC", key="home_name")
with col2:
    away_name = st.text_input("Away Team", placeholder="e.g. United", key="away_name")

st.markdown("**Kit Colours** — used for name tag overlays")
col_hc, col_ac = st.columns(2)
with col_hc:
    st.markdown(f"🏠 {home_name or 'Home'}")
    home_colour_name = st.selectbox(
        "Home kit",
        options=list(KIT_COLOURS.keys()),
        index=0,
        key="home_colour_name",
        label_visibility="collapsed",
    )
    st.session_state["home_colour"] = KIT_COLOURS[home_colour_name]
with col_ac:
    st.markdown(f"✈️ {away_name or 'Away'}")
    away_colour_name = st.selectbox(
        "Away kit",
        options=list(KIT_COLOURS.keys()),
        index=1,
        key="away_colour_name",
        label_visibility="collapsed",
    )
    st.session_state["away_colour"] = KIT_COLOURS[away_colour_name]

st.markdown('</div>', unsafe_allow_html=True)

# ── Player names ──────────────────────────────────────────────────────────────
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 🏷️ Player Names")
st.markdown(
    '<div class="info-box">'
    'Enter first names for shirt numbers #20–35. Leave blank for any player '
    'not in today\'s squad. OCR reads the shirt number from the video and shows '
    'the name you enter here.'
    '</div>',
    unsafe_allow_html=True
)

# Ensure squad dicts exist
if "squad_home" not in st.session_state or not isinstance(st.session_state["squad_home"], dict):
    st.session_state["squad_home"] = {}
if "squad_away" not in st.session_state or not isinstance(st.session_state["squad_away"], dict):
    st.session_state["squad_away"] = {}

col_home, col_away = st.columns(2)

with col_home:
    st.markdown(f"**🏠 {home_name or 'Home Team'}**")
    st.markdown('<div class="name-grid">', unsafe_allow_html=True)
    for num in range(20, 36):
        col_num, col_input = st.columns([1, 3])
        with col_num:
            st.markdown(f'<span class="name-num">#{num}</span>', unsafe_allow_html=True)
        with col_input:
            val = st.text_input(
                f"home_{num}",
                value=st.session_state["squad_home"].get(num, ""),
                placeholder="Name",
                key=f"home_{num}",
                label_visibility="collapsed",
            )
            st.session_state["squad_home"][num] = val.strip().upper() if val else ""
    st.markdown('</div>', unsafe_allow_html=True)

with col_away:
    st.markdown(f"**✈️ {away_name or 'Away Team'}**")
    st.markdown('<div class="name-grid">', unsafe_allow_html=True)
    for num in range(20, 36):
        col_num, col_input = st.columns([1, 3])
        with col_num:
            st.markdown(f'<span class="name-num">#{num}</span>', unsafe_allow_html=True)
        with col_input:
            val = st.text_input(
                f"away_{num}",
                value=st.session_state["squad_away"].get(num, ""),
                placeholder="Name",
                key=f"away_{num}",
                label_visibility="collapsed",
            )
            st.session_state["squad_away"][num] = val.strip().upper() if val else ""
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Process button ────────────────────────────────────────────────────────────
ready_files = st.session_state.get("cam_a_ready") and st.session_state.get("cam_b_ready")
ready_colab = colab_alive

if not ready_files:
    st.warning("⚠️ Select both camera files above to continue")
elif not ready_colab:
    st.warning("⚠️ Colab is not running — open your notebook and click Run All")
else:
    if st.button("▶ PROCESS MATCH", use_container_width=True, type="primary"):
        with st.spinner("Submitting job to Colab..."):
            try:
                # Build job payload with sensible defaults
                job = {
                    "match": {
                        "home_name": st.session_state.get("home_name", "Home"),
                        "away_name": st.session_state.get("away_name", "Away"),
                        "match_date": datetime.now().strftime("%Y-%m-%d"),
                        "home_colour": st.session_state.get("home_colour", "#ef4444"),
                        "away_colour": st.session_state.get("away_colour", "#3b82f6"),
                    },
                    "stitch": {
                        "seam_auto": True,
                        "overlap_pct": 18,
                        "lens_correct": True,
                        "colour_match": True,
                        "stabilise": True,
                        "preview_stitch": False,
                        "camera_model": "Generic action camera (auto-calibrate)",
                    },
                    "tracking": {
                        "shirt_min": 1,
                        "shirt_max": 35,
                        "ball_colour": "White (standard)",
                        "kalman_window": 1.5,
                        "goal_conf": 75,
                        "halftime_mins": 10,
                    },
                    "squad": {
                        "home": {str(k): v for k, v in st.session_state["squad_home"].items() if v},
                        "away": {str(k): v for k, v in st.session_state["squad_away"].items() if v},
                    },
                    "output": {
                        "follow_ball": True,
                        "resolution": "1920×1080 (1080p)",
                        "fps": "60 fps",
                        "export_fmt": "MP4 (H.264)",
                        "overlays": {
                            "score": True,
                            "timer": True,
                            "names": True,
                            "numbers": True,
                            "ball_trail": True,
                            "speed": False,
                            "heatmap": False,
                            "goal_alert": True,
                        },
                    },
                    "files": {
                        "cam_a": st.session_state.get("cam_a_filename", ""),
                        "cam_b": st.session_state.get("cam_b_filename", ""),
                    },
                }
                
                job_id = submit_job(folder_id, job)
                st.session_state["active_job_id"] = job_id
                st.rerun()
            except Exception as e:
                st.error(f"Failed to submit job: {e}")
