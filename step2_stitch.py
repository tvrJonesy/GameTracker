import streamlit as st


def render():
    st.markdown("""
    <div class="ml-step-heading">
      <span class="ml-step-num">STEP 02</span>
      <span class="ml-step-title">Panorama Stitch Settings</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="ml-card ml-card-accent">', unsafe_allow_html=True)
    st.markdown("**Seam Detection Mode**")

    seam_mode = st.radio(
        "Seam detection",
        options=["🤖 Auto — detect overlap from pitch markings (recommended)", "✂️ Manual — set overlap % myself"],
        index=0,
        key="seam_mode",
        label_visibility="collapsed",
    )
    st.session_state["seam_auto"] = "Auto" in seam_mode

    st.markdown("---")
    st.markdown("**Estimated Overlap Width**")
    st.markdown('<p style="font-size:0.78rem;color:#7a9070;margin-bottom:0.5rem">% of each camera\'s frame that overlaps with the other at the centre of the pitch. 15–20% is typical for a tripod at halfway.</p>', unsafe_allow_html=True)

    overlap = st.slider(
        "Overlap %",
        min_value=5,
        max_value=40,
        value=st.session_state.get("overlap_pct", 18),
        step=1,
        format="%d%%",
        key="overlap_pct",
        label_visibility="collapsed",
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Options toggles ───────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**Processing Options**")

    col1, col2 = st.columns(2)
    with col1:
        lens_correct = st.checkbox(
            "🔍 Lens distortion correction",
            value=st.session_state.get("lens_correct", True),
            key="lens_correct",
            help="Removes fisheye barrel distortion from action cameras. Strongly recommended — without this the stitch seam will never align cleanly.",
        )
        colour_match = st.checkbox(
            "🎨 Colour match at seam",
            value=st.session_state.get("colour_match", True),
            key="colour_match",
            help="Balances exposure and white balance between the two cameras so the join is invisible even if lighting differs slightly.",
        )
    with col2:
        stabilise = st.checkbox(
            "📐 Horizon stabilisation",
            value=st.session_state.get("stabilise", True),
            key="stabilise",
            help="Corrects minor tilt differences between the two cameras so the stitched horizon is level.",
        )
        preview_stitch = st.checkbox(
            "👁️ Generate stitch preview frame",
            value=st.session_state.get("preview_stitch", True),
            key="preview_stitch",
            help="Outputs a single stitched still image after the first 30 seconds so you can confirm the seam looks correct before the full job runs.",
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Info box ──────────────────────────────────────────────────────────
    st.markdown("""
    <div class="ml-info">
      <strong>How stitching works:</strong> OpenCV extracts SIFT feature points from the overlap zone of both
      frames (pitch lines, grass texture, centre circle markings). It matches corresponding points between the
      two cameras, computes a homography matrix, and warps one frame to align with the other. Multi-band
      blending then hides the seam. The homography is computed once per half from a static frame — since
      your cameras are on a fixed tripod this is valid for the entire half and makes processing fast.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚙️ Advanced: camera model for lens profile"):
        st.markdown('<p style="font-size:0.78rem;color:#7a9070">If you know your camera model, select it for a more accurate lens correction. Otherwise "Generic action camera" works well for most cheap wide-angle cameras.</p>', unsafe_allow_html=True)
        camera_model = st.selectbox(
            "Camera model",
            ["Generic action camera (auto-calibrate)", "GoPro Hero (any)", "DJI Osmo Action", "Insta360 GO", "Akaso / Apeman / CAMPARK"],
            key="camera_model",
        )
