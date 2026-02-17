"""
step5_processing.py — Job submission and live status polling via Google Drive.

No ngrok. No URLs. The app writes a job file to Drive; Colab picks it up.
Progress is read back from a status file Colab writes every few seconds.
"""

import streamlit as st
import time

from utils.drive_queue import submit_job, get_status, get_heartbeat, build_job_payload

# ── Pipeline stage definitions (must match Colab's status writes) ──────────
PIPELINE_STAGES = [
    ("🔄", "Audio Sync & Alignment"),
    ("🔍", "Lens Distortion Correction"),
    ("🪡", "Panorama Stitching"),
    ("🏃", "Player & Ball Detection"),
    ("🥅", "Goal Event Detection"),
    ("🏷️",  "Name Tag Rendering"),
    ("🎬", "Video Render & Overlays"),
]


# ── Colab status panel ──────────────────────────────────────────────────────

def _colab_status_panel(folder_id: str):
    """
    Shows whether the Colab watcher is alive, with a direct open button.
    Reads a heartbeat.json file the watcher writes every 30 seconds.
    """
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)

    # Notebook URL — from secrets if set, otherwise a text input
    notebook_url = ""
    try:
        notebook_url = st.secrets.get("colab_notebook_url", "")
    except Exception:
        pass
    if not notebook_url:
        notebook_url = st.session_state.get("colab_notebook_url", "")

    col_status, col_btn = st.columns([3, 1])

    with col_status:
        st.markdown("**Colab Watcher Status**")

        if not folder_id or len(folder_id) < 20:
            st.markdown(
                '<p style="font-size:0.8rem;color:#7a9070">'
                'Enter your Drive folder ID below to check watcher status.'
                '</p>',
                unsafe_allow_html=True,
            )
        else:
            heartbeat = get_heartbeat(folder_id)

            if heartbeat is None:
                # No heartbeat file at all — watcher never started
                st.markdown(
                    '<div style="display:flex;align-items:center;gap:10px;margin:6px 0">'
                    '<div style="width:10px;height:10px;border-radius:50%;background:#ff4545;flex-shrink:0"></div>'
                    '<span style="font-size:0.82rem;color:#ff4545"><strong>Not running</strong> — '
                    'open your Colab notebook and click Run All</span>'
                    '</div>',
                    unsafe_allow_html=True,
                )
            elif not heartbeat.get("alive", True):
                age = heartbeat.get("age_seconds", 0)
                mins = age // 60
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0">'
                    f'<div style="width:10px;height:10px;border-radius:50%;background:#ffb020;flex-shrink:0"></div>'
                    f'<span style="font-size:0.82rem;color:#ffb020"><strong>Stale</strong> — '
                    f'last seen {mins} min ago. Colab may have timed out. Reopen and run again.</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                gpu   = heartbeat.get("gpu", "GPU")
                jobs  = heartbeat.get("job_count", 0)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0">'
                    f'<div style="width:10px;height:10px;border-radius:50%;background:#c8f542;'
                    f'box-shadow:0 0 6px rgba(200,245,66,0.6);flex-shrink:0"></div>'
                    f'<span style="font-size:0.82rem;color:#c8f542"><strong>Ready</strong> — '
                    f'{gpu} · {jobs} job{"s" if jobs != 1 else ""} processed this session</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if notebook_url:
            st.link_button(
                "Open Colab →",
                notebook_url,
                use_container_width=True,
            )
        else:
            # Let them paste the notebook URL if not in secrets
            nb_url_input = st.text_input(
                "Colab notebook URL",
                value=st.session_state.get("colab_notebook_url", ""),
                placeholder="https://colab.research.google.com/drive/...",
                key="colab_notebook_url",
                label_visibility="collapsed",
            )
            if nb_url_input:
                st.link_button("Open Colab →", nb_url_input, use_container_width=True)
            else:
                st.markdown(
                    '<p style="font-size:0.7rem;color:#7a9070;line-height:1.4">'
                    'Paste your notebook URL above, or add '
                    '<code>colab_notebook_url</code> to Streamlit Secrets.</p>',
                    unsafe_allow_html=True,
                )

    st.markdown('</div>', unsafe_allow_html=True)


# ── Settings summary ────────────────────────────────────────────────────────

def _settings_summary():
    home        = st.session_state.get("home_name", "—") or "—"
    away        = st.session_state.get("away_name", "—") or "—"
    home_colour = st.session_state.get("home_colour", "#ef4444")
    away_colour = st.session_state.get("away_colour", "#3b82f6")
    home_squad  = st.session_state.get("squad_home", {})
    away_squad  = st.session_state.get("squad_away", {})
    home_names  = sum(1 for v in home_squad.values() if v)
    away_names  = sum(1 for v in away_squad.values() if v)

    overlays = [
        label for key, label in [
            ("ov_score", "Score"), ("ov_timer", "Timer"),
            ("ov_names", "Name tags"), ("ov_numbers", "Numbers"),
            ("ov_ball_trail", "Ball trail"), ("ov_speed", "Speed"),
            ("ov_heatmap", "Heatmap"), ("ov_goal_alert", "Goal replay"),
        ] if st.session_state.get(key, False)
    ]

    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**Job Summary**")

    rows = [
        ("Match",         f"{home} vs {away}"),
        ("Date",          str(st.session_state.get("match_date", "—"))),
        ("Squad names",   f"{home_names} home + {away_names} away names entered"),
        ("Shirt numbers", f"#{st.session_state.get('shirt_min', 20)}–#{st.session_state.get('shirt_max', 35)}"),
        ("Seam mode",     "Auto" if st.session_state.get("seam_auto", True)
                          else f"Manual ({st.session_state.get('overlap_pct', 18)}% overlap)"),
        ("Output mode",   "Ball-following" if st.session_state.get("follow_ball", True)
                          else "Full panorama"),
        ("Resolution",    st.session_state.get("resolution", "1920x1080")),
        ("Overlays",      ", ".join(overlays) if overlays else "None"),
    ]

    for label, value in rows:
        col_l, col_v = st.columns([2, 5])
        with col_l:
            st.markdown(
                f'<p style="font-family:DM Mono,monospace;font-size:0.7rem;'
                f'color:#7a9070;letter-spacing:1px;text-transform:uppercase;'
                f'margin:3px 0">{label}</p>',
                unsafe_allow_html=True,
            )
        with col_v:
            if label == "Match":
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0">'
                    f'<div style="width:12px;height:12px;border-radius:50%;background:{home_colour}"></div>'
                    f'<span style="font-size:0.82rem">{home}</span>'
                    f'<span style="font-size:0.75rem;color:#7a9070">vs</span>'
                    f'<div style="width:12px;height:12px;border-radius:50%;background:{away_colour}"></div>'
                    f'<span style="font-size:0.82rem">{away}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<p style="font-size:0.82rem;margin:3px 0">{value}</p>',
                    unsafe_allow_html=True,
                )
    st.markdown('</div>', unsafe_allow_html=True)


# ── Drive folder ID input ───────────────────────────────────────────────────

def _folder_id_input():
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown("**Google Drive Folder ID**")
    st.markdown(
        '<p style="font-size:0.78rem;color:#7a9070;margin-bottom:0.5rem;line-height:1.6">'
        "Set <strong>once</strong>, never changes. Open your <code>GameTracker</code> folder "
        "in Google Drive and copy the ID from the URL: "
        "<code>drive.google.com/drive/folders/<strong>THIS_PART</strong></code>"
        "</p>",
        unsafe_allow_html=True,
    )

    folder_id_from_secret = ""
    try:
        folder_id_from_secret = st.secrets.get("gdrive_folder_id", "")
    except Exception:
        pass

    if folder_id_from_secret:
        st.markdown(
            '<div class="ml-success">Folder ID loaded from Streamlit secrets.</div>',
            unsafe_allow_html=True,
        )
        st.session_state["gdrive_folder_id"] = folder_id_from_secret
    else:
        st.text_input(
            "Drive folder ID",
            value=st.session_state.get("gdrive_folder_id", ""),
            placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs",
            key="gdrive_folder_id",
            label_visibility="collapsed",
        )
        st.markdown("""
        <div class="ml-info">
          Add <code>gdrive_folder_id = "YOUR_ID"</code> to Streamlit Secrets
          (app Settings → Secrets) so this is pre-filled on every visit.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    return st.session_state.get("gdrive_folder_id", "")


# ── Pipeline progress UI ────────────────────────────────────────────────────

def _render_stages(current: int, done_up_to: int):
    for i, (icon, title) in enumerate(PIPELINE_STAGES):
        if i <= done_up_to:
            dot  = "border:2px solid rgba(200,245,66,0.5);background:rgba(200,245,66,0.08)"
            sym, colour = "✅", "#c8f542"
        elif i == current:
            dot  = "border:2px solid #ffb020;background:rgba(255,176,32,0.08)"
            sym, colour = icon, "#f0f4ee"
        else:
            dot  = "border:2px solid rgba(200,245,66,0.15);background:#0b1a0e"
            sym, colour = icon, "#7a9070"

        st.markdown(
            f'<div style="display:grid;grid-template-columns:36px 1fr;gap:12px;'
            f'align-items:center;padding:8px 0;'
            f'border-bottom:1px solid rgba(200,245,66,0.07)">'
            f'<div style="width:36px;height:36px;border-radius:50%;{dot};'
            f'display:flex;align-items:center;justify-content:center;font-size:1rem">{sym}</div>'
            f'<div style="font-size:0.82rem;color:{colour}">{title}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _progress_ui(job_id: str, folder_id: str):
    st.markdown('<div class="ml-card ml-card-accent">', unsafe_allow_html=True)
    st.markdown("**Processing Pipeline**")

    status = get_status(folder_id, job_id)

    if status is None:
        st.markdown(
            '<div class="ml-warn">Waiting for Colab to pick up the job '
            '(checks every 30 s)…</div>',
            unsafe_allow_html=True,
        )
        _render_stages(current=0, done_up_to=-1)
        st.markdown('</div>', unsafe_allow_html=True)
        time.sleep(5)
        st.rerun()

    elif status.get("status") == "error":
        st.markdown(
            f'<div class="ml-warn">Processing error: '
            f'{status.get("error", "Unknown error")}</div>',
            unsafe_allow_html=True,
        )
        _render_stages(current=-1, done_up_to=-1)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Try again"):
            st.session_state.pop("active_job_id", None)
            st.rerun()

    elif status.get("status") == "done":
        _render_stages(
            current=len(PIPELINE_STAGES),
            done_up_to=len(PIPELINE_STAGES) - 1,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.balloons()
        st.markdown(
            '<div class="ml-success" style="font-size:0.9rem;padding:1rem;margin-top:0.5rem">'
            '🎉 <strong>Complete!</strong> Your video is in Google Drive → '
            '<code>GameTracker/output/</code>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Process another match"):
            for k in ["active_job_id", "cam_a_ready", "cam_b_ready",
                      "cam_a_filename", "cam_b_filename"]:
                st.session_state.pop(k, None)
            st.session_state.step = 0
            st.rerun()

    else:
        stage_idx = status.get("stage_index", 0)
        progress  = status.get("progress", 0)
        message   = status.get("message", "")
        _render_stages(current=stage_idx, done_up_to=stage_idx - 1)
        if message:
            st.markdown(
                f'<p style="font-size:0.75rem;color:#ffb020;margin:6px 0 0 52px">{message}</p>',
                unsafe_allow_html=True,
            )
        st.progress(progress / 100)
        st.markdown('</div>', unsafe_allow_html=True)
        time.sleep(5)
        st.rerun()


# ── Main render ─────────────────────────────────────────────────────────────

def render():
    st.markdown("""
    <div class="ml-step-heading">
      <span class="ml-step-num">STEP 05</span>
      <span class="ml-step-title">Review &amp; Process</span>
    </div>
    """, unsafe_allow_html=True)

    folder_id     = st.session_state.get("gdrive_folder_id", "")
    active_job_id = st.session_state.get("active_job_id")

    # Colab status always shown at top
    _colab_status_panel(folder_id)

    # Already running — skip straight to progress
    if active_job_id:
        _folder_id_input()
        _progress_ui(active_job_id, folder_id)
        return

    # Pre-submission
    _settings_summary()
    folder_id = _folder_id_input()

    with st.expander("How does this work?"):
        st.markdown("""
        **No URLs. No tokens. Nothing to paste every session.**

        1. Click **Process Match** — videos upload to `GameTracker/raw/` and a
           `job_<id>.json` settings file is written to `GameTracker/jobs/` in your Drive.
        2. Your **Colab notebook** (open, watcher cell running) checks that folder
           every 30 seconds, picks up the job, and starts processing.
        3. Colab writes a `status_<id>.json` back to Drive every few seconds.
        4. This page reads it and updates the progress display automatically.
        5. Finished files land in `GameTracker/output/`.

        **Your match-day checklist (after one-time setup):**
        - Open Colab → Run All → leave the tab open
        - Open GameTracker → upload → click Process
        - Return in ~50 minutes to download your video
        """)

    st.markdown("""
    <div class="ml-info">
      <strong>Processing time:</strong> ~40–60 minutes on a free Colab T4 GPU.
      You can close this browser tab and reopen it later —
      the job keeps running and progress will catch up when you return.
    </div>
    """, unsafe_allow_html=True)

    ready_files  = (st.session_state.get("cam_a_ready")
                    and st.session_state.get("cam_b_ready"))
    ready_folder = bool(folder_id and len(folder_id) >= 20)

    # Check Colab heartbeat
    colab_alive = False
    if ready_folder:
        hb = get_heartbeat(folder_id)
        colab_alive = hb is not None and hb.get("alive", True)

    if not ready_files:
        st.markdown(
            '<div class="ml-warn">⚠️ Go back to Step 1 and upload both camera files.</div>',
            unsafe_allow_html=True,
        )
    if not ready_folder:
        st.markdown(
            '<div class="ml-warn">⚠️ Enter your Google Drive folder ID above.</div>',
            unsafe_allow_html=True,
        )
    if ready_folder and not colab_alive:
        st.markdown(
            '<div class="ml-warn">⚠️ Colab watcher is not running. '
            'Open your notebook and click Run All, then wait a few seconds for the '
            'status indicator above to turn green.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn, col_note = st.columns([2, 5])

    with col_btn:
        if st.button(
            "PROCESS MATCH",
            disabled=not (ready_files and ready_folder and colab_alive),
            use_container_width=True,
            type="primary",
        ):
            with st.spinner("Uploading to Google Drive…"):
                try:
                    payload = build_job_payload(st.session_state)
                    job_id  = submit_job(folder_id, payload)
                    st.session_state["active_job_id"] = job_id
                    st.rerun()
                except Exception as e:
                    st.markdown(
                        f'<div class="ml-warn">Failed to submit job: {e}<br>'
                        f'Check your service account has Editor access to the Drive folder.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    with col_note:
        st.markdown(
            '<p style="font-size:0.75rem;color:#7a9070;line-height:1.6;padding-top:0.5rem">'
            "Uploads both videos to Drive and drops a settings file for Colab to pick up."
            "</p>",
            unsafe_allow_html=True,
        )
