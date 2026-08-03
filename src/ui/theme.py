"""
Shared UI theme and small render helpers.

One place for the ATS look-and-feel (a clean recruiter-tool palette:
white surface, slate-gray text, a single confident blue as the action
color, a dark navy sidebar for wayfinding) so every page stays
consistent. Injected once per session from app.py.
"""

import streamlit as st

# Palette — deliberately restrained: one blue does all the "action" work,
# everything else is neutral so candidate data, not chrome, carries the eye.
BLUE = "#2563eb"
BLUE_DARK = "#1d4ed8"
BLUE_SOFT = "#eff6ff"
INK = "#0f172a"
SLATE = "#475569"
MUTED = "#94a3b8"
LINE = "#e8edf3"
SURFACE = "#ffffff"
CANVAS = "#eef2fb"
GREEN = "#16a34a"
GREEN_SOFT = "#dcfce7"
GREEN_DARK = "#15803d"
AMBER = "#d97706"
AMBER_SOFT = "#fef3c7"
RED = "#dc2626"
RED_SOFT = "#fee2e2"
RED_DARK = "#b91c1c"

# Sidebar gets its own dark-navy sub-palette — distinct from the light
# main canvas so the nav reads as chrome, not content.
NAVY = "#0b1220"
NAVY_SOFT = "#111c33"
NAVY_LINE = "rgba(255,255,255,0.08)"
NAVY_HOVER = "rgba(255,255,255,0.06)"
SIDEBAR_TEXT = "#e2e8f0"
SIDEBAR_MUTED = "#8592ab"

# Gold / silver / bronze for the top-3 ranking badges.
GOLD = "#d4af37"
SILVER = "#9aa4b2"
BRONZE = "#b06a35"

CARD_SHADOW = "0 2px 8px rgba(15,23,42,0.06)"
CARD_SHADOW_HOVER = "0 4px 16px rgba(15,23,42,0.09)"

# Soft-tint background for a stat card's icon tile, keyed by the same
# color used for its value — so "blue value" always pairs with "blue tile".
_ICON_SOFT = {BLUE: BLUE_SOFT, GREEN: GREEN_SOFT, AMBER: AMBER_SOFT, RED: RED_SOFT}


def inject_theme():
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {CANVAS}; }}
        .block-container {{ padding-top: 2.25rem; padding-bottom: 3rem; }}

        /* Type scale: 34px page titles, 20px section titles, 15px body.
           Scoped under .stApp (not bare h1/h2/h3/h4) to outrank Streamlit's
           own generated per-heading CSS rule (class-scoped h1 font-size),
           which otherwise silently wins on specificity and makes these
           font-size overrides a no-op. */
        .stApp h1 {{ color: {INK}; font-weight: 800; font-size: 34px; letter-spacing: -0.01em; }}
        .stApp h2, .stApp h3, .stApp h4 {{ color: {INK}; font-weight: 700; font-size: 20px; letter-spacing: -0.01em; }}
        /* These surfaces are hardcoded light above, so text has to be pinned
           dark to match. Without this, a viewer whose Streamlit resolves to
           the dark theme gets near-white text on them — labels, captions,
           tables and error tracebacks all render invisible, which reads as
           "the button did nothing". .streamlit/config.toml pins base=light
           for the same reason; this is the belt-and-braces half. */
        .stApp, .stApp p, .stApp li, .stApp label, .stApp span,
        div[data-testid="stMarkdownContainer"] {{ color: {INK}; font-size: 15px; }}
        .stApp small, .stCaption, div[data-testid="stCaptionContainer"],
        div[data-testid="stCaptionContainer"] * {{ color: {SLATE}; }}
        /* Alerts and exception blocks: light tinted panels need dark text. */
        div[data-testid="stAlert"], div[data-testid="stAlert"] *,
        div[data-testid="stException"], div[data-testid="stException"] * {{ color: {INK}; }}

        /* ---------- Sidebar: dark navy chrome ---------- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {NAVY} 0%, {NAVY_SOFT} 100%);
            border-right: 1px solid {NAVY_LINE};
        }}
        section[data-testid="stSidebar"] * {{ color: {SIDEBAR_TEXT}; }}
        section[data-testid="stSidebar"] small,
        section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] * {{
            color: {SIDEBAR_MUTED} !important;
        }}
        section[data-testid="stSidebar"] hr {{ border-color: {NAVY_LINE}; }}

        .ats-brand {{
            display: flex; align-items: center; gap: 0.65rem;
            padding: 0.15rem 0 1rem 0;
        }}
        .ats-brand-badge {{
            display: flex; align-items: center; justify-content: center;
            width: 2.35rem; height: 2.35rem; border-radius: 10px;
            background: linear-gradient(135deg, {BLUE} 0%, {BLUE_DARK} 100%);
            font-size: 1.2rem; flex-shrink: 0;
            box-shadow: 0 4px 10px -2px rgba(37,99,235,0.55);
        }}
        .ats-brand-name {{ font-size: 1.15rem; font-weight: 700; color: #ffffff; line-height: 1.15; }}
        .ats-brand-tag {{ font-size: 0.72rem; color: {SIDEBAR_MUTED}; letter-spacing: 0.02em; }}

        /* Nav radio -> icon list */
        section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap: 0.2rem; }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            border-radius: 10px;
            padding: 0.5rem 0.6rem;
            margin: 0;
            transition: background 0.15s ease;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: {NAVY_HOVER};
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
            display: none;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label > div:last-child p {{
            font-size: 0.94rem;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: {BLUE};
            box-shadow: 0 4px 12px -4px rgba(37,99,235,0.6);
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) * {{
            color: #ffffff !important;
            font-weight: 600;
        }}

        /* ---------- Cards ---------- */
        .ats-card {{
            background: {SURFACE};
            border: 1px solid {LINE};
            border-radius: 16px;
            padding: 22px 24px;
            box-shadow: {CARD_SHADOW};
            transition: box-shadow 0.15s ease, transform 0.15s ease;
        }}

        /* ---------- Stat cards (icon tile / label / big value / descriptor) ---------- */
        .ats-stat-card {{ display: flex; flex-direction: column; gap: 4px; }}
        .ats-stat-card:hover {{ box-shadow: {CARD_SHADOW_HOVER}; transform: translateY(-1px); }}
        .ats-stat-icon {{
            width: 38px; height: 38px; border-radius: 11px;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px; margin-bottom: 6px;
        }}
        .ats-stat-label {{ font-size: 12px; font-weight: 700; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.06em; }}
        .ats-stat-value {{ font-size: 34px; font-weight: 800; line-height: 1.15; }}
        .ats-stat-desc {{ font-size: 13px; color: {SLATE}; }}

        /* ---------- Match breakdown card (overall + 3-column stat row) ---------- */
        .ats-breakdown-overall-label {{ font-size: 12px; font-weight: 700; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.06em; }}
        .ats-breakdown-overall-value {{ font-size: 34px; font-weight: 800; line-height: 1.15; margin: 2px 0 16px 0; }}
        .ats-breakdown-row {{ display: flex; }}
        .ats-breakdown-stat {{ flex: 1; text-align: center; padding: 0 8px; }}
        .ats-breakdown-stat:first-child {{ padding-left: 0; }}
        .ats-breakdown-stat:last-child {{ padding-right: 0; }}
        .ats-breakdown-stat + .ats-breakdown-stat {{ border-left: 1px solid {LINE}; }}
        .ats-breakdown-stat-label {{ font-size: 12px; font-weight: 700; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
        .ats-breakdown-stat-value {{ font-size: 20px; font-weight: 800; color: {INK}; }}

        /* ---------- Ranked candidate list rows ---------- */
        .ats-rank-row {{
            display: flex; align-items: center; gap: 12px;
            padding: 10px 0; border-bottom: 1px solid {LINE};
        }}
        .ats-rank-row:last-child {{ border-bottom: none; }}
        .ats-rank-badge {{
            width: 26px; height: 26px; border-radius: 50%; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 12px; font-weight: 800; color: #ffffff;
        }}
        .ats-rank-info {{ flex: 1; min-width: 0; }}
        .ats-rank-name {{
            font-size: 14px; font-weight: 600; color: {INK}; margin-bottom: 5px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }}
        .ats-rank-bar-track {{ height: 6px; border-radius: 999px; background: {LINE}; overflow: hidden; }}
        .ats-rank-bar-fill {{ height: 100%; border-radius: 999px; }}
        .ats-rank-score {{ font-size: 14px; font-weight: 700; flex-shrink: 0; width: 48px; text-align: right; }}

        /* ---------- Donut chart (pure CSS conic-gradient — no plotting lib needed) ---------- */
        .ats-donut-wrap {{ display: flex; justify-content: center; padding: 4px 0 12px 0; }}
        .ats-donut {{
            border-radius: 50%; position: relative;
            display: flex; align-items: center; justify-content: center;
        }}
        .ats-donut-hole {{
            width: var(--hole); height: var(--hole); border-radius: 50%;
            background: {SURFACE};
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }}
        .ats-donut-value {{ font-size: 22px; font-weight: 800; color: {INK}; line-height: 1; }}
        .ats-donut-sublabel {{ font-size: 12px; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }}

        .ats-legend-row {{ display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 13px; color: {SLATE}; }}
        .ats-legend-dot {{ width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }}
        .ats-legend-label {{ flex: 1; }}
        .ats-legend-count {{ font-weight: 700; color: {INK}; }}

        /* ---------- Summary chip (top-right of a page header) ---------- */
        .ats-chip-wrap {{ display: flex; justify-content: flex-end; align-items: center; height: 100%; }}
        .ats-summary-chip {{
            display: inline-flex; align-items: center; gap: 6px;
            background: {BLUE_SOFT}; color: {BLUE_DARK};
            font-size: 13px; font-weight: 600;
            padding: 7px 16px; border-radius: 999px; white-space: nowrap;
        }}

        /* ---------- Job Description page only: soft requirement tags ---------- */
        /* Deliberately separate from .ats-pill (used elsewhere as full pills)
           so this stays scoped to the JD page's required/preferred skills. */
        .ats-tag-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0.15rem 0 0.35rem 0; }}
        .ats-tag {{
            display: inline-block; padding: 4px 12px; border-radius: 8px;
            background: {BLUE_SOFT}; color: {BLUE_DARK};
            border: none; font-size: 13px; font-weight: 600; line-height: 1.25;
            white-space: nowrap;
        }}

        /* ---------- Job Description page only: requirement summary card ---------- */
        .ats-req-card {{
            background: {SURFACE}; border: 1px solid {LINE}; border-radius: 14px;
            box-shadow: {CARD_SHADOW}; padding: 20px;
            display: flex; gap: 24px;
        }}
        .ats-req-item {{ flex: 1; }}
        .ats-req-label {{ font-size: 13px; font-weight: 700; color: {MUTED}; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
        .ats-req-value {{ font-size: 22px; font-weight: 800; color: {INK}; }}

        /* ---------- Resume Upload page only: success banner ---------- */
        .ats-success-banner {{
            background: #f0fdf4; color: {GREEN_DARK}; border: 1px solid {GREEN_SOFT};
            border-radius: 10px; padding: 12px 16px; font-size: 15px; font-weight: 500;
        }}

        /* ---------- Resume Upload page only: parsing results table ---------- */
        /* st.table is the only table on this page (Candidate Ranking uses
           st.dataframe, which is canvas-rendered and not CSS-stylable), so
           scoping to stTable's testid stays effectively page-local. */
        div[data-testid="stTable"] table {{ width: 100%; }}
        div[data-testid="stTable"] table td {{
            font-size: 14px; color: {INK};
        }}

        /* ---------- Skill pills ---------- */
        /* Laid out as a flex row so the gap between pills is even and there
           is no trailing margin at the end of a wrapped line. */
        .ats-pill-row {{
            display: flex; flex-wrap: wrap; gap: 6px;
            margin: 0.15rem 0 0.35rem 0;
        }}
        .ats-pill {{
            display: inline-block; padding: 5px 14px; border-radius: 999px;
            border: none; font-size: 13px; font-weight: 600; line-height: 1.25;
            white-space: nowrap;
        }}
        /* Scoped under .stApp and doubled up on the pill class so these beat
           the global `.stApp span {{ color: INK }}` rule above — a plain
           `.pill-match` (0,1,0) loses to it (0,1,1) and every pill would
           render with ink-colored text regardless of kind. */
        .stApp .ats-pill.pill-match {{ background: {GREEN_SOFT}; color: {GREEN_DARK}; }}
        .stApp .ats-pill.pill-miss  {{ background: {RED_SOFT}; color: {RED_DARK}; }}
        .stApp .ats-pill.pill-extra {{ background: {BLUE_SOFT}; color: {BLUE_DARK}; }}
        .ats-reason-ok {{ color: {GREEN}; }}
        .ats-reason-no {{ color: {RED}; }}

        /* The label lives in a nested <p>/<span>, so the color has to be set
           there too or Streamlit's primaryColor wins and the text matches
           the button's own background. */
        .stButton>button, .stButton>button p, .stButton>button span,
        .stButton>button:hover, .stButton>button:hover p, .stButton>button:hover span,
        .stButton>button:focus, .stButton>button:focus p, .stButton>button:focus span {{
            color: #ffffff;
        }}
        .stButton>button {{
            background: {BLUE}; border: none; border-radius: 10px;
            font-weight: 600; padding: 0.5rem 1.1rem;
            transition: background 0.15s ease, box-shadow 0.15s ease;
        }}
        .stButton>button:hover, .stButton>button:focus {{
            background: {BLUE_DARK};
            box-shadow: 0 4px 12px -4px rgba(37,99,235,0.5);
        }}
        div[data-testid="stMetricValue"] {{ color: {INK}; }}

        /* Native containers (st.container(border=True)) get the same card
           treatment for consistent spacing/shadow across the app. */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {SURFACE} !important;
            border: 1px solid {LINE} !important;
            border-radius: 16px !important;
            box-shadow: {CARD_SHADOW};
            margin-bottom: 16px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] {{
            padding: 22px 24px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_title(text):
    """The big page heading (Dashboard, Job Description, ...). Renders as
    an inline-styled <div>, not st.title() / a bare <h1> — Streamlit
    applies its own per-heading CSS class to real h1/h2/... elements, so
    even an inline-styled <h1> can end up fighting that rule in some
    render paths. A <div> has no Streamlit heading styling to fight at
    all. Every page should call this instead of st.title() so titles
    stay identical."""
    st.markdown(
        f"<div style='font-size:34px; font-weight:800; color:{INK}; margin-top:20px; margin-bottom:12px; line-height:1.2;'>{text}</div>",
        unsafe_allow_html=True,
    )


def score_color(score):
    """Green/blue/amber/red banding shared by metric numbers, badges and
    progress bars so a given score always reads the same everywhere."""
    if score >= 85:
        return GREEN
    if score >= 70:
        return BLUE
    if score >= 50:
        return AMBER
    return RED


def overall_match_color(score):
    """Green/amber/red banding for a single headline match % (Candidate
    Details' Overall score) — coarser than score_color()'s 4-band scale,
    which is used where finer distinction (e.g. the ranking donut) matters."""
    if score >= 70:
        return GREEN
    if score >= 50:
        return AMBER
    return RED


def match_breakdown_card(overall, stats):
    """Candidate Details' match breakdown: a big colored 'Overall' number
    plus an even row of sub-scores (e.g. Skills/Semantic/Experience) with
    thin dividers between them. stats: list of (label, value) tuples."""
    overall_color = overall_match_color(overall)
    stat_html = "".join(
        f'<div class="ats-breakdown-stat"><div class="ats-breakdown-stat-label">{label}</div>'
        f'<div class="ats-breakdown-stat-value">{value}%</div></div>'
        for label, value in stats
    )
    st.markdown(
        f"""<div class="ats-card">
            <div class="ats-breakdown-overall-label">Overall</div>
            <div class="ats-breakdown-overall-value" style="color:{overall_color};">{overall}%</div>
            <div class="ats-breakdown-row">{stat_html}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def metric_card(label, value, color=INK, icon=None, descriptor=None):
    """A stat card: colored icon tile, uppercase label, big colored value,
    and an optional descriptor line underneath."""
    icon_html = ""
    if icon:
        tile_bg = _ICON_SOFT.get(color, LINE)
        icon_html = f'<div class="ats-stat-icon" style="background:{tile_bg}; color:{color};">{icon}</div>'
    desc_html = f'<div class="ats-stat-desc">{descriptor}</div>' if descriptor else ""
    st.markdown(
        f"""<div class="ats-card ats-stat-card">
            {icon_html}
            <div class="ats-stat-label">{label}</div>
            <div class="ats-stat-value" style="color:{color};">{value}</div>
            {desc_html}
        </div>""",
        unsafe_allow_html=True,
    )


def rank_row(rank, name, score, badge_color):
    """One row in a 'Top Candidates' list: rank badge, name, score bar, score."""
    bar_color = score_color(score)
    st.markdown(
        f"""<div class="ats-rank-row">
            <div class="ats-rank-badge" style="background:{badge_color};">{rank}</div>
            <div class="ats-rank-info">
                <div class="ats-rank-name">{name}</div>
                <div class="ats-rank-bar-track"><div class="ats-rank-bar-fill" style="width:{min(score, 100)}%; background:{bar_color};"></div></div>
            </div>
            <div class="ats-rank-score" style="color:{bar_color};">{score:.0f}%</div>
        </div>""",
        unsafe_allow_html=True,
    )


def donut_chart(segments, center_value=None, center_label=None, size=170, thickness=30):
    """A donut chart built from a CSS conic-gradient — no plotting library
    required. segments: list of (label, count, color) tuples."""
    total = sum(count for _, count, _ in segments)
    stops = []
    cum = 0
    for _, count, color in segments:
        if count <= 0:
            continue
        start = cum / total * 360 if total else 0
        cum += count
        end = cum / total * 360 if total else 0
        stops.append(f"{color} {start:.2f}deg {end:.2f}deg")
    gradient = ", ".join(stops) if stops else f"{LINE} 0deg 360deg"

    center_html = ""
    if center_value is not None:
        sub_html = f'<div class="ats-donut-sublabel">{center_label}</div>' if center_label else ""
        center_html = f'<div class="ats-donut-value">{center_value}</div>{sub_html}'

    hole = size - thickness * 2
    st.markdown(
        f"""<div class="ats-donut-wrap">
            <div class="ats-donut" style="width:{size}px; height:{size}px; background:conic-gradient({gradient}); --hole:{hole}px;">
                <div class="ats-donut-hole">{center_html}</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def legend_row(label, count, color):
    st.markdown(
        f"""<div class="ats-legend-row">
            <span class="ats-legend-dot" style="background:{color};"></span>
            <span class="ats-legend-label">{label}</span>
            <span class="ats-legend-count">{count}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def summary_chip(text):
    st.markdown(
        f'<div class="ats-chip-wrap"><div class="ats-summary-chip">{text}</div></div>',
        unsafe_allow_html=True,
    )


def skill_tags(skills):
    """Job Description page only: soft, non-pill requirement tags (light
    blue, semi-rounded 8px corners) — visually distinct from skill_pills()
    so required/preferred skills don't read as clickable buttons."""
    if not skills:
        st.markdown(f'<span style="color:{MUTED};">None</span>', unsafe_allow_html=True)
        return
    tags = "".join(f'<span class="ats-tag">{s}</span>' for s in skills)
    st.markdown(f'<div class="ats-tag-row">{tags}</div>', unsafe_allow_html=True)


def requirement_summary_card(items):
    """Job Description page only: Experience/Education/Certifications as an
    even row inside one white card. items: list of (label, value) tuples."""
    cells = "".join(
        f'<div class="ats-req-item"><div class="ats-req-label">{label}</div>'
        f'<div class="ats-req-value">{value}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="ats-req-card">{cells}</div>', unsafe_allow_html=True)


def skill_pills(skills, kind="match"):
    """Render a row of skill pills.

    kind: match (green) | miss (red) | extra (blue). Every skill list in
    the app (except the JD page's own skill_tags()) goes through here so
    the pill styling stays identical across pages.
    """
    css = {"match": "pill-match", "miss": "pill-miss", "extra": "pill-extra"}[kind]
    if not skills:
        st.markdown(f'<span style="color:{MUTED};">None</span>', unsafe_allow_html=True)
        return
    pills = "".join(f'<span class="ats-pill {css}">{s}</span>' for s in skills)
    st.markdown(f'<div class="ats-pill-row">{pills}</div>', unsafe_allow_html=True)


def score_badge(score):
    return f'<span style="font-weight:700;color:{score_color(score)};">{score}%</span>'
