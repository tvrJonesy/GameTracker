import streamlit as st


def render():
    st.markdown("""
    <div class="ml-step-heading">
      <span class="ml-step-num">STEP 04</span>
      <span class="ml-step-title">Output Video Settings</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Output mode ───────────────────────────────────────────────────────
    st.markdown('<div class="ml-card ml-card-accent">', unsafe_allow_html=True)
    st.markdown("**Output Mode**")

    output_mode = st.radio(
        "Output mode",
        options=[
            "🎯 Ball-following camera — virtual camera pans and zooms to follow the ball",
            "🌍 Full panorama (fixed) — complete wide view, ideal for tactical review",
        ],
        index=0,
        key="output_mode",
        label_visibility="collapsed",
    )
    st.session_state["follow_ball"] = "Ball-following" in output_mode
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Overlays ──────────────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**Video Overlays**")
    st.markdown('<p style="font-size:0.78rem;color:#7a9070;margin-bottom:0.75rem">Choose which graphics are composited onto the output video.</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        ov_score      = st.checkbox("🏆 Score bug",            value=True,  key="ov_score")
        ov_timer      = st.checkbox("⏱️ Match timer",          value=True,  key="ov_timer")
        ov_names      = st.checkbox("🏷️ Player name tags",     value=True,  key="ov_names",
                                    help="First name floating above each player, coloured by team kit.")
        ov_numbers    = st.checkbox("🔢 Player number tags",   value=True,  key="ov_numbers",
                                    help="Shirt number shown alongside or instead of name tag.")
    with col2:
        ov_ball_trail = st.checkbox("🔴 Ball trail",           value=True,  key="ov_ball_trail",
                                    help="Fading trail showing the last 12 frames of ball movement.")
        ov_speed      = st.checkbox("💨 Player speed (km/h)",  value=False, key="ov_speed")
        ov_heatmap    = st.checkbox("🌡️ Heat map overlay",     value=False, key="ov_heatmap",
                                    help="Cumulative player position heatmap shown at halftime and full time.")
        ov_goal_alert = st.checkbox("🎉 Goal replay alert",    value=False, key="ov_goal_alert",
                                    help="Animated banner + slow-motion replay clip when a goal is confirmed.")

    if ov_names:
        st.markdown("""
        <div class="ml-info">
          <strong>Name tag style:</strong> First name only · Kit colour background · White text ·
          Anchored above player head · 6-frame smoothing to prevent jitter
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Technical settings ────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**Export Settings**")

    col_res, col_fps, col_fmt = st.columns(3)
    with col_res:
        resolution = st.selectbox(
            "Resolution",
            ["1920×1080 (1080p)", "2560×1440 (1440p)", "3840×2160 (4K) — slow"],
            index=0,
            key="resolution",
        )
    with col_fps:
        fps = st.selectbox(
            "Frame rate",
            ["30 fps", "60 fps"],
            index=1,
            key="fps",
        )
    with col_fmt:
        fmt = st.selectbox(
            "Format",
            ["MP4 (H.264)", "MP4 (H.265 / HEVC)", "WebM"],
            index=0,
            key="export_fmt",
        )

    # Estimated output size
    res_map = {"1920×1080 (1080p)": 1080, "2560×1440 (1440p)": 1440, "3840×2160 (4K) — slow": 2160}
    fps_map = {"30 fps": 30, "60 fps": 60}
    res_val = res_map.get(resolution, 1080)
    fps_val = fps_map.get(fps, 60)
    # rough bitrate estimate MB/min
    bitrate_mb_min = (res_val / 1080) ** 2 * (fps_val / 30) * 150
    est_size_gb = bitrate_mb_min * 50 / 1000  # 50 min match
    st.caption(f"Estimated output file size for a 50-min match: ~{est_size_gb:.1f} GB")

    if "4K" in resolution:
        st.markdown('<div class="ml-warn">⚠️ 4K output on Colab free tier will be very slow (~3–4 hours). 1080p is recommended.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Summary ───────────────────────────────────────────────────────────
    active_overlays = []
    if ov_score:      active_overlays.append("Score bug")
    if ov_timer:      active_overlays.append("Timer")
    if ov_names:      active_overlays.append("Name tags")
    if ov_numbers:    active_overlays.append("Number tags")
    if ov_ball_trail: active_overlays.append("Ball trail")
    if ov_speed:      active_overlays.append("Speed")
    if ov_heatmap:    active_overlays.append("Heatmap")
    if ov_goal_alert: active_overlays.append("Goal replay")

    if active_overlays:
        st.markdown(
            f'<div class="ml-success">✓ {len(active_overlays)} overlays enabled: '
            f'{", ".join(active_overlays)}</div>',
            unsafe_allow_html=True,
        )
