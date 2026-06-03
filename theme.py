from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


BG = "#FAF8F5"
SURFACE = "#FFFDF9"
INK = "#1C1B19"
MUTED = "#756F67"
BORDER = "#E8E0D7"
GRID = "#EEE7DE"
ACCENT = "#7C8B6F"
ACCENT_DARK = "#536044"
TERRACOTTA = "#B97A5E"
PALETTE = ["#7C8B6F", "#AEB89C", "#D7C8B5", "#B97A5E", "#8C8378", "#C7B7A3", "#5F6C54"]
FONT_BODY = "Inter, Geist, Work Sans, sans-serif"
FONT_DISPLAY = "Fraunces, DM Serif Display, Playfair Display, Georgia, serif"


def apply_theme() -> None:
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: {BG};
                --surface: {SURFACE};
                --ink: {INK};
                --muted: {MUTED};
                --border: {BORDER};
                --accent: {ACCENT};
            }}
            html, body, [data-testid="stAppViewContainer"] {{
                background: var(--bg);
                color: var(--ink);
                font-family: {FONT_BODY};
            }}
            [data-testid="stHeader"], [data-testid="stToolbar"], footer, #MainMenu {{
                visibility: hidden;
                height: 0;
            }}
            .block-container {{
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1240px;
            }}
            h1, h2, h3, .display-font {{
                font-family: {FONT_DISPLAY};
                color: var(--ink);
                letter-spacing: 0;
            }}
            .page-kicker {{
                color: var(--accent);
                text-transform: uppercase;
                letter-spacing: .08em;
                font-size: .78rem;
                font-weight: 700;
                margin-bottom: .3rem;
            }}
            .page-title {{
                font-family: {FONT_DISPLAY};
                font-size: clamp(2rem, 4vw, 3.35rem);
                line-height: 1.04;
                margin: 0 0 .45rem 0;
            }}
            .page-subtitle {{
                color: var(--muted);
                max-width: 760px;
                margin-bottom: 1.5rem;
            }}
            .section-title {{
                font-family: {FONT_DISPLAY};
                font-size: 1.45rem;
                margin: 1.8rem 0 .5rem 0;
            }}
            .kpi-card {{
                background: rgba(255, 253, 249, .72);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: .95rem 1rem;
                min-height: 118px;
                box-shadow: 0 12px 30px rgba(74, 61, 44, .045);
                overflow: hidden;
            }}
            .kpi-label {{
                color: var(--muted);
                font-size: .78rem;
                font-weight: 700;
                letter-spacing: .06em;
                text-transform: uppercase;
            }}
            .kpi-value {{
                font-family: {FONT_DISPLAY};
                font-size: clamp(1.45rem, 2.2vw, 1.9rem);
                color: var(--ink);
                margin-top: .35rem;
                line-height: 1.05;
                white-space: nowrap;
                max-width: 100%;
            }}
            .kpi-caption {{
                color: var(--muted);
                font-size: .82rem;
                margin-top: .5rem;
            }}
            [data-testid="stSidebar"] {{
                background: #F4EFE8;
                border-right: 1px solid var(--border);
            }}
            [data-testid="stMetric"] {{
                background: transparent;
            }}
            div[data-testid="stDataFrame"] {{
                border: 1px solid var(--border);
                border-radius: 8px;
                overflow: hidden;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def plotly_template() -> go.layout.Template:
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"family": FONT_BODY, "color": INK, "size": 13},
            colorway=PALETTE,
            hovermode="x unified",
            margin={"l": 20, "r": 20, "t": 42, "b": 40},
            xaxis={
                "showgrid": False,
                "zeroline": False,
                "linecolor": BORDER,
                "tickcolor": BORDER,
            },
            yaxis={
                "showgrid": True,
                "gridcolor": GRID,
                "zeroline": False,
                "linecolor": BORDER,
                "tickcolor": BORDER,
            },
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )
    )


def styled_figure(fig: go.Figure, height: int = 390) -> go.Figure:
    fig.update_layout(template=plotly_template(), height=height)
    return fig


def page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-kicker">{kicker}</div>
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_inr(value: float, compact: bool = False) -> str:
    if compact:
        if abs(value) >= 10_000_000:
            return f"₹{value / 10_000_000:.2f}Cr"
        if abs(value) >= 100_000:
            return f"₹{value / 100_000:.2f}L"
        if abs(value) >= 1_000:
            return f"₹{value / 1_000:.1f}K"
    rounded = int(round(value))
    sign = "-" if rounded < 0 else ""
    number = str(abs(rounded))
    if len(number) <= 3:
        return f"{sign}₹{number}"
    last_three = number[-3:]
    rest = number[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return f"{sign}₹{','.join(groups)},{last_three}"


def format_pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"
