import streamlit as st

SHIRT_NUMBERS = list(range(20, 36))  # #20 to #35

HOME_DEMO = ["JAMES", "OLIVER", "HARRY", "NOAH", "GEORGE",
             "CHARLIE", "JACK", "ARCHIE", "FREDDIE", "TOMMY",
             "LOUIE", "MAX", "REUBEN", "LEON", "OSCAR", "THEO"]

AWAY_DEMO = ["ALFIE", "EDWARD", "HENRY", "SAMUEL", "WILLIAM",
             "JOSEPH", "DANIEL", "LUCAS", "ETHAN", "MASON",
             "LOGAN", "LIAM", "RYAN", "DYLAN", "FINN", "JAKE"]


def _init_squad():
    if "squad_home" not in st.session_state:
        st.session_state["squad_home"] = {n: "" for n in SHIRT_NUMBERS}
    if "squad_away" not in st.session_state:
        st.session_state["squad_away"] = {n: "" for n in SHIRT_NUMBERS}


def _squad_column(team: str, label: str, colour: str, demo_names: list):
    """Render one team's squad entry column."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.75rem">'
        f'<div style="width:14px;height:14px;border-radius:50%;background:{colour};flex-shrink:0"></div>'
        f'<span style="font-family:\'DM Mono\',monospace;font-size:0.7rem;letter-spacing:2px;'
        f'text-transform:uppercase;color:#f0f4ee">{label}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    key = f"squad_{team}"
    squad = st.session_state[key]

    for num in SHIRT_NUMBERS:
        col_num, col_name = st.columns([1, 3])
        with col_num:
            st.markdown(
                f'<div style="background:#0b1a0e;border:1px solid rgba(200,245,66,0.15);'
                f'border-radius:6px;text-align:center;padding:7px 4px;'
                f'font-family:\'Bebas Neue\',sans-serif;font-size:1.1rem;'
                f'letter-spacing:1px;color:#c8f542">#{num}</div>',
                unsafe_allow_html=True,
            )
        with col_name:
            val = st.text_input(
                f"{team}_{num}",
                value=squad.get(num, ""),
                placeholder="First name",
                max_chars=12,
                key=f"squad_input_{team}_{num}",
                label_visibility="collapsed",
            )
            st.session_state[key][num] = val.upper() if val else ""

    # Action buttons
    col_clear, col_demo = st.columns(2)
    with col_clear:
        if st.button("Clear all", key=f"clear_{team}", use_container_width=True):
            st.session_state[key] = {n: "" for n in SHIRT_NUMBERS}
            st.rerun()
    with col_demo:
        if st.button("Load example", key=f"demo_{team}", use_container_width=True):
            st.session_state[key] = {
                SHIRT_NUMBERS[i]: demo_names[i]
                for i in range(min(len(SHIRT_NUMBERS), len(demo_names)))
            }
            st.rerun()


def _render_preview(home_colour: str, away_colour: str):
    """Render the live name tag preview as HTML."""
    home_squad = st.session_state.get("squad_home", {})
    away_squad = st.session_state.get("squad_away", {})

    # Pick up to 3 home + 2 away with names for preview
    home_samples = [(n, v) for n, v in home_squad.items() if v][:3]
    away_samples = [(n, v) for n, v in away_squad.items() if v][:2]

    if not home_samples and not away_samples:
        st.markdown(
            '<div style="background:#0f2312;border-radius:6px;padding:24px;'
            'text-align:center;font-family:DM Mono,monospace;font-size:0.7rem;'
            'color:#7a9070;letter-spacing:1px">Enter names above to see a preview</div>',
            unsafe_allow_html=True,
        )
        return

    def player_html(num, name, colour):
        display = name[:8] if len(name) > 8 else name
        return (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:0">'
            f'<div style="font-family:Bebas Neue,sans-serif;font-size:11px;letter-spacing:1.5px;'
            f'padding:2px 8px 1px;border-radius:3px;background:{colour};color:white;'
            f'white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,0.5)">{display}</div>'
            f'<div style="width:1px;height:7px;background:rgba(255,255,255,0.25)"></div>'
            f'<div style="width:30px;height:30px;border-radius:50%;background:{colour};'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-family:Bebas Neue,sans-serif;font-size:13px;color:white;'
            f'box-shadow:0 2px 8px rgba(0,0,0,0.5)">#{num}</div>'
            f'</div>'
        )

    players_html = "".join(
        player_html(n, v, home_colour) for n, v in home_samples
    ) + "".join(
        player_html(n, v, away_colour) for n, v in away_samples
    )

    st.markdown(
        f'<div style="background:#0f2312;border-radius:6px;padding:24px;'
        f'display:flex;align-items:flex-end;gap:40px;justify-content:center;'
        f'min-height:110px;position:relative;overflow:hidden">'
        f'<div style="position:absolute;inset:0;background:repeating-linear-gradient('
        f'90deg,transparent 0px,transparent 60px,'
        f'rgba(255,255,255,0.02) 60px,rgba(255,255,255,0.02) 120px)"></div>'
        f'<div style="display:flex;gap:36px;align-items:flex-end;position:relative;z-index:1">'
        f'{players_html}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def render():
    _init_squad()

    st.markdown("""
    <div class="ml-step-heading">
      <span class="ml-step-num">STEP 03b</span>
      <span class="ml-step-title">Player Name Tags</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<p style="color:#7a9070;font-size:0.85rem;line-height:1.7;margin-bottom:1.25rem">'
        "Enter first names for each shirt number. Labels appear as floating tags above each "
        "player in the output video, coloured by team. Leave blank for any player not in "
        "today's squad — that slot will show the number only."
        "</p>",
        unsafe_allow_html=True,
    )

    home_colour = st.session_state.get("home_colour", "#ef4444")
    away_colour = st.session_state.get("away_colour", "#3b82f6")
    home_name   = st.session_state.get("home_name", "Home Team") or "Home Team"
    away_name   = st.session_state.get("away_name", "Away Team") or "Away Team"

    # ── Squad entry columns ───────────────────────────────────────────────
    st.markdown('<div class="ml-card ml-card-accent">', unsafe_allow_html=True)
    col_home, col_divider, col_away = st.columns([5, 0.3, 5])

    with col_home:
        _squad_column("home", f"🏠 {home_name}", home_colour, HOME_DEMO)

    with col_divider:
        st.markdown(
            '<div style="border-left:1px solid rgba(200,245,66,0.1);'
            'height:100%;min-height:400px;margin:0 auto;width:1px"></div>',
            unsafe_allow_html=True,
        )

    with col_away:
        _squad_column("away", f"✈️ {away_name}", away_colour, AWAY_DEMO)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Live preview ──────────────────────────────────────────────────────
    st.markdown('<div class="ml-card">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:DM Mono,monospace;font-size:0.65rem;'
        'color:#7a9070;letter-spacing:1.5px;text-transform:uppercase;'
        'margin-bottom:0.75rem">▶ Live Tag Preview</div>',
        unsafe_allow_html=True,
    )
    _render_preview(home_colour, away_colour)

    st.markdown("""
    <div class="ml-info" style="margin-top:0.75rem">
      <strong>How it works:</strong> YOLO links each player bounding box to their shirt number
      via OCR. The first name for that number is rendered as a pill label anchored above the
      player's head, smoothed with a 6-frame moving average to prevent jitter.
      Home labels use the home kit colour; away labels use the away kit colour.
      Off-screen players are never labelled, keeping the ball-following view clean.
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Summary count
    home_filled = sum(1 for v in st.session_state.get("squad_home", {}).values() if v)
    away_filled = sum(1 for v in st.session_state.get("squad_away", {}).values() if v)
    total = home_filled + away_filled
    if total:
        st.markdown(
            f'<div class="ml-success">✓ {home_filled} home + {away_filled} away names entered ({total} total)</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="ml-warn">ℹ️ No names entered yet — players will be labelled by number only. You can still continue.</div>',
            unsafe_allow_html=True,
        )
