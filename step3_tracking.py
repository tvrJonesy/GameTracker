import streamlit as st


def render():
    st.markdown("""
    <div class="ml-step-heading">
      <span class="ml-step-num">STEP 03</span>
      <span class="ml-step-title">Tracking Settings</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Player tracking ───────────────────────────────────────────────────
    st.markdown('<div class="ml-card ml-card-accent">', unsafe_allow_html=True)
    st.markdown("**🏃 Player Tracking**")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Shirt number range**")
        num_min = st.number_input("From", min_value=1, max_value=99, value=20, key="shirt_min")
    with col2:
        st.markdown("&nbsp;")  # spacer
        num_max = st.number_input("To", min_value=1, max_value=99, value=35, key="shirt_max")

    if num_max <= num_min:
        st.markdown('<div class="ml-warn">⚠️ Max shirt number must be greater than min.</div>', unsafe_allow_html=True)
    else:
        count = num_max - num_min + 1
        st.markdown(f'<div class="ml-success">✓ Tracking {count} shirt numbers (#{num_min}–#{num_max}) — {count} players across both teams</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="ml-info">
      <strong>OCR note:</strong> Reading shirt numbers from cheap action cameras at this scale is
      the hardest part of the pipeline. Expect 70–85% accuracy. After processing you'll get a
      correction screen to fix any misread numbers before the final video is rendered.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Ball tracking ─────────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**⚽ Ball Tracking**")

    ball_colour = st.selectbox(
        "Ball colour hint",
        ["White (standard)", "Coloured / Hi-vis", "Black & white panels", "Let model decide"],
        key="ball_colour",
        help="Giving the tracker a colour hint improves initial detection speed, especially in the first few frames of each half.",
    )

    kalman_window = st.slider(
        "Ball lost tolerance (seconds)",
        min_value=0.5,
        max_value=3.0,
        value=float(st.session_state.get("kalman_window", 1.5)),
        step=0.5,
        format="%.1fs",
        key="kalman_window",
        help="How long the Kalman filter keeps predicting ball position after YOLO loses sight of it. Higher = smoother but may follow wrong object after long occlusion.",
    )

    st.markdown("""
    <div class="ml-info">
      <strong>Ball tracking method:</strong> YOLOv8 detects the ball per-frame. A Kalman filter predicts
      position between detections and across stitch boundary crossings. The virtual camera output uses
      the smoothed ball position with damped interpolation to avoid jerky pans.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Goal detection ────────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**🥅 Goal Detection**")

    col_conf, col_ht = st.columns(2)
    with col_conf:
        goal_conf = st.slider(
            "Confidence threshold",
            min_value=50,
            max_value=95,
            value=int(st.session_state.get("goal_conf", 75)),
            step=5,
            format="%d%%",
            key="goal_conf",
            help="Lower = catches more goals but risks false positives. Higher = more conservative.",
        )
        if goal_conf < 65:
            st.caption("⚠️ Low threshold — may trigger on near misses")
        elif goal_conf > 85:
            st.caption("ℹ️ High threshold — may miss goals from tight angles")

    with col_ht:
        halftime_mins = st.number_input(
            "Halftime break (mins)",
            min_value=5,
            max_value=20,
            value=int(st.session_state.get("halftime_mins", 10)),
            key="halftime_mins",
            help="Used to split the match into two halves for the score timeline.",
        )

    st.markdown("""
    <div class="ml-info">
      <strong>Goal detection logic:</strong> A goal is flagged when the tracked ball is inside the goal
      bounding box for 3+ consecutive frames AND attacking players are near the goal mouth. Each flagged
      event produces a 10-second review clip you confirm or reject before the score is updated.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
