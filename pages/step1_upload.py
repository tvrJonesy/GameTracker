import streamlit as st

KIT_COLOURS = {
    "Red":        "#ef4444",
    "Blue":       "#3b82f6",
    "Amber":      "#f59e0b",
    "Green":      "#10b981",
    "White":      "#f5f5f0",
    "Black":      "#1e1e2e",
    "Purple":     "#a855f7",
    "Orange":     "#f97316",
    "Pink":       "#ec4899",
    "Teal":       "#14b8a6",
    "Navy":       "#1e3a5f",
    "Yellow":     "#eab308",
}

def render():
    st.markdown("""
    <div class="ml-step-heading">
      <span class="ml-step-num">STEP 01</span>
      <span class="ml-step-title">Upload Footage</span>
    </div>
    """, unsafe_allow_html=True)

    # ── File uploads ──────────────────────────────────────────────────────
    st.markdown('<div class="ml-card ml-card-accent">', unsafe_allow_html=True)
    st.markdown("**Upload both camera files**")
    st.markdown('<div class="ml-warn">📷 Camera A covers the <strong>left half</strong> of the pitch (camera faces right). Camera B covers the <strong>right half</strong> (camera faces left). Make sure you match the correct file to the correct slot.</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### 📷 Camera A — Left Half")
        cam_a = st.file_uploader(
            "Camera A",
            type=["mp4", "mov", "avi", "mkv"],
            key="cam_a",
            label_visibility="collapsed",
        )
        if cam_a:
            size_gb = cam_a.size / 1024**3
            st.markdown(f'<div class="ml-success">✓ {cam_a.name}<br>{size_gb:.2f} GB</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown("##### 📷 Camera B — Right Half")
        cam_b = st.file_uploader(
            "Camera B",
            type=["mp4", "mov", "avi", "mkv"],
            key="cam_b",
            label_visibility="collapsed",
        )
        if cam_b:
            size_gb = cam_b.size / 1024**3
            st.markdown(f'<div class="ml-success">✓ {cam_b.name}<br>{size_gb:.2f} GB</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Match details ─────────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**Match Details**")

    col1, col2, col3 = st.columns(3)
    with col1:
        home_name = st.text_input("Home Team", value=st.session_state.get("home_name", ""), placeholder="e.g. Rovers FC", key="home_name")
    with col2:
        away_name = st.text_input("Away Team", value=st.session_state.get("away_name", ""), placeholder="e.g. United", key="away_name")
    with col3:
        match_date = st.date_input("Match Date", key="match_date")

    st.markdown("---")
    st.markdown("**Kit Colours** — used for player name tag labels")

    col_home, col_away = st.columns(2)
    with col_home:
        st.markdown(f"🏠 **{home_name or 'Home Team'}**")
        home_colour_name = st.selectbox(
            "Home kit colour",
            options=list(KIT_COLOURS.keys()),
            index=0,
            key="home_colour_name",
            label_visibility="collapsed",
        )
        home_hex = KIT_COLOURS[home_colour_name]
        st.markdown(
            f'<div style="width:100%;height:28px;border-radius:6px;background:{home_hex};'
            f'border:1px solid rgba(255,255,255,0.15);margin-top:4px"></div>',
            unsafe_allow_html=True,
        )
        st.session_state["home_colour"] = home_hex

    with col_away:
        st.markdown(f"✈️ **{away_name or 'Away Team'}**")
        away_colour_name = st.selectbox(
            "Away kit colour",
            options=list(KIT_COLOURS.keys()),
            index=1,
            key="away_colour_name",
            label_visibility="collapsed",
        )
        away_hex = KIT_COLOURS[away_colour_name]
        st.markdown(
            f'<div style="width:100%;height:28px;border-radius:6px;background:{away_hex};'
            f'border:1px solid rgba(255,255,255,0.15);margin-top:4px"></div>',
            unsafe_allow_html=True,
        )
        st.session_state["away_colour"] = away_hex

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sync reminder ─────────────────────────────────────────────────────
    with st.expander("📋 Pre-upload checklist"):
        st.markdown("""
        Before uploading, confirm:
        - ✅ Both files are from the **same match**
        - ✅ You clapped loudly in front of both cameras at the start (audio sync marker)
        - ✅ Both cameras were set to the **same resolution and frame rate**
        - ✅ Electronic image stabilisation was **disabled** on both cameras
        - ✅ Camera A = left half, Camera B = right half
        """)

    # Save upload state
    st.session_state["cam_a_ready"] = cam_a is not None
    st.session_state["cam_b_ready"] = cam_b is not None

    if not (cam_a and cam_b):
        st.markdown('<div class="ml-warn">⚠️ Upload both camera files to continue.</div>', unsafe_allow_html=True)
