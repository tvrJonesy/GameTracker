"""
step1_upload.py — Select footage from Google Drive.

No file uploader. No size limit.
Users copy videos to GameTracker/raw/ on their own machine or via Drive web,
then the Colab watcher scans that folder and writes filelist.json.
This page reads filelist.json and presents two dropdowns.
"""

import streamlit as st
from utils.drive_queue import get_raw_files

KIT_COLOURS = {
    "Red":    "#ef4444", "Blue":   "#3b82f6", "Amber":  "#f59e0b",
    "Green":  "#10b981", "White":  "#f5f5f0", "Black":  "#1e1e2e",
    "Purple": "#a855f7", "Orange": "#f97316", "Pink":   "#ec4899",
    "Teal":   "#14b8a6", "Navy":   "#1e3a5f", "Yellow": "#eab308",
}

VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.mts', '.m2ts'}


def _fmt_size(size_mb: float) -> str:
    if size_mb >= 1024:
        return f"{size_mb / 1024:.1f} GB"
    return f"{size_mb:.0f} MB"


def _file_select_card(files: list, folder_id: str):
    """Render the two-column camera file dropdowns."""
    st.markdown('<div class="ml-card ml-card-accent">', unsafe_allow_html=True)
    st.markdown("**Select footage from Google Drive**")
    st.markdown(
        '<p style="font-size:0.78rem;color:#7a9070;line-height:1.6;margin-bottom:0.75rem">'
        "Copy your video files to <code>GameTracker/raw/</code> in Google Drive "
        "(drag-and-drop via drive.google.com, or move from your camera's SD card). "
        "Then click <strong>Refresh</strong> to scan for new files."
        "</p>",
        unsafe_allow_html=True,
    )

    # Camera-assignment reminder
    st.markdown(
        '<div class="ml-info" style="margin-bottom:0.75rem">'
        "📷 <strong>Camera A</strong> covers the <strong>left half</strong> of the pitch "
        "(lens facing right). "
        "📷 <strong>Camera B</strong> covers the <strong>right half</strong> "
        "(lens facing left)."
        "</div>",
        unsafe_allow_html=True,
    )

    # File names + sizes for the dropdowns
    options     = ["— select —"] + [
        f"{f['name']}  ({_fmt_size(f.get('size_mb', 0))})"
        for f in files
    ]
    # Map display label back to raw filename
    label_to_name = {
        f"{f['name']}  ({_fmt_size(f.get('size_mb', 0))})": f['name']
        for f in files
    }

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("##### 📷 Camera A — Left Half")
        sel_a = st.selectbox(
            "Camera A file",
            options=options,
            index=0 if not st.session_state.get("cam_a_filename") else
                  next((i+1 for i, f in enumerate(files)
                        if f['name'] == st.session_state.get("cam_a_filename")), 0),
            key="cam_a_select",
            label_visibility="collapsed",
        )
        if sel_a != "— select —":
            fname = label_to_name[sel_a]
            st.session_state["cam_a_filename"] = fname
            st.session_state["cam_a_ready"]    = True
            st.markdown(
                f'<div class="ml-success">✓ {fname}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.session_state["cam_a_ready"] = False

    with col_b:
        st.markdown("##### 📷 Camera B — Right Half")
        sel_b = st.selectbox(
            "Camera B file",
            options=options,
            index=0 if not st.session_state.get("cam_b_filename") else
                  next((i+1 for i, f in enumerate(files)
                        if f['name'] == st.session_state.get("cam_b_filename")), 0),
            key="cam_b_select",
            label_visibility="collapsed",
        )
        if sel_b != "— select —":
            fname = label_to_name[sel_b]
            st.session_state["cam_b_filename"] = fname
            st.session_state["cam_b_ready"]    = True
            st.markdown(
                f'<div class="ml-success">✓ {fname}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.session_state["cam_b_ready"] = False

    # Warn if same file selected for both cameras
    if (st.session_state.get("cam_a_ready") and st.session_state.get("cam_b_ready")
            and st.session_state.get("cam_a_filename") == st.session_state.get("cam_b_filename")):
        st.markdown(
            '<div class="ml-warn">⚠️ Both cameras are set to the same file — '
            'check you have the right files selected.</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)


def render():
    st.markdown("""
    <div class="ml-step-heading">
      <span class="ml-step-num">STEP 01</span>
      <span class="ml-step-title">Select Footage</span>
    </div>
    """, unsafe_allow_html=True)

    folder_id = st.session_state.get("gdrive_folder_id", "")

    # ── Drive folder ID (if not already set in secrets) ───────────────────
    if not folder_id:
        st.markdown('<div class="ml-card">', unsafe_allow_html=True)
        st.markdown("**Google Drive Folder ID**")
        st.markdown(
            '<p style="font-size:0.78rem;color:#7a9070;margin-bottom:0.5rem">'
            "Enter this once here or in Streamlit Secrets. "
            "It's the long ID from the URL when you open your GameTracker folder in Drive."
            "</p>",
            unsafe_allow_html=True,
        )
        st.text_input(
            "Drive folder ID",
            value="",
            placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
            key="gdrive_folder_id",
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)
        folder_id = st.session_state.get("gdrive_folder_id", "")

    # ── File list ─────────────────────────────────────────────────────────
    files = st.session_state.get("_raw_files_cache", None)

    col_refresh, col_status = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh file list", use_container_width=True,
                     disabled=not (folder_id and len(folder_id) >= 20)):
            with st.spinner("Scanning GameTracker/raw/…"):
                files = get_raw_files(folder_id)
                st.session_state["_raw_files_cache"] = files

    with col_status:
        if not folder_id or len(folder_id) < 20:
            st.markdown(
                '<p style="font-size:0.78rem;color:#7a9070;padding-top:0.6rem">'
                "Enter your Drive folder ID above first."
                "</p>",
                unsafe_allow_html=True,
            )
        elif files is None:
            st.markdown(
                '<p style="font-size:0.78rem;color:#7a9070;padding-top:0.6rem">'
                "Click Refresh to scan <code>GameTracker/raw/</code> for video files. "
                "Colab must be running for the scan to work."
                "</p>",
                unsafe_allow_html=True,
            )
        elif len(files) == 0:
            st.markdown(
                '<div class="ml-warn" style="margin-top:0.25rem">'
                "No video files found in <code>GameTracker/raw/</code>. "
                "Copy your footage there first, then click Refresh."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<p style="font-size:0.78rem;color:#c8f542;padding-top:0.6rem">'
                f"✓ {len(files)} file{'s' if len(files) != 1 else ''} found in Drive"
                f"</p>",
                unsafe_allow_html=True,
            )

    # ── Dropdowns (only shown once files are loaded) ──────────────────────
    if files:
        _file_select_card(files, folder_id)
    elif files is not None:
        # files == [] — show how-to
        st.markdown("""
        <div class="ml-card">
          <strong>How to add files to GameTracker/raw/</strong>
          <p style="font-size:0.82rem;color:#7a9070;margin:0.5rem 0 0.25rem">
            Choose the method that suits you:
          </p>
          <p style="font-size:0.82rem;margin:0.25rem 0">
            <strong>From a computer:</strong> Open
            <a href="https://drive.google.com" target="_blank"
               style="color:#c8f542">drive.google.com</a>,
            navigate to <code>GameTracker/raw/</code>, drag and drop your MP4 files.
          </p>
          <p style="font-size:0.82rem;margin:0.25rem 0">
            <strong>From Google Drive desktop app:</strong>
            Open the GameTracker/raw folder in Finder or Explorer and copy files in.
          </p>
          <p style="font-size:0.82rem;margin:0.25rem 0">
            <strong>From phone/tablet:</strong>
            Use the Google Drive app, tap + → Upload, select your video files.
          </p>
          <p style="font-size:0.82rem;color:#7a9070;margin-top:0.5rem">
            Once files appear in Drive, click <strong>Refresh</strong> above.
          </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Match details ─────────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**Match Details**")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.text_input("Home Team", placeholder="e.g. Rovers FC", key="home_name")
    with col2:
        st.text_input("Away Team", placeholder="e.g. United",    key="away_name")
    with col3:
        st.date_input("Match Date", key="match_date")

    st.markdown("---")
    st.markdown("**Kit Colours** — used for player name tag labels")

    home_name = st.session_state.get("home_name", "") or "Home Team"
    away_name = st.session_state.get("away_name", "") or "Away Team"

    col_home, col_away = st.columns(2)
    with col_home:
        st.markdown(f"🏠 **{home_name}**")
        home_colour_name = st.selectbox(
            "Home kit", options=list(KIT_COLOURS.keys()),
            index=0, key="home_colour_name", label_visibility="collapsed",
        )
        home_hex = KIT_COLOURS[home_colour_name]
        st.markdown(
            f'<div style="width:100%;height:28px;border-radius:6px;background:{home_hex};'
            f'border:1px solid rgba(255,255,255,0.15);margin-top:4px"></div>',
            unsafe_allow_html=True,
        )
        st.session_state["home_colour"] = home_hex

    with col_away:
        st.markdown(f"✈️ **{away_name}**")
        away_colour_name = st.selectbox(
            "Away kit", options=list(KIT_COLOURS.keys()),
            index=1, key="away_colour_name", label_visibility="collapsed",
        )
        away_hex = KIT_COLOURS[away_colour_name]
        st.markdown(
            f'<div style="width:100%;height:28px;border-radius:6px;background:{away_hex};'
            f'border:1px solid rgba(255,255,255,0.15);margin-top:4px"></div>',
            unsafe_allow_html=True,
        )
        st.session_state["away_colour"] = away_hex

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Pre-match checklist ───────────────────────────────────────────────
    with st.expander("📋 Pre-match checklist"):
        st.markdown("""
        - ✅ Both files are from the **same match**
        - ✅ You clapped loudly in front of both cameras at the start (audio sync marker)
        - ✅ Both cameras were set to the **same resolution and frame rate**
        - ✅ Electronic image stabilisation was **disabled** on both cameras
        - ✅ Camera A = left half of pitch · Camera B = right half
        - ✅ Files copied to **GameTracker/raw/** in Google Drive
        """)

    # ── Readiness gate ────────────────────────────────────────────────────
    if not (st.session_state.get("cam_a_ready") and st.session_state.get("cam_b_ready")):
        st.markdown(
            '<div class="ml-warn">⚠️ Select both camera files above to continue.</div>',
            unsafe_allow_html=True,
        )
