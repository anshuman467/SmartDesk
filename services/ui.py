from textwrap import dedent

import streamlit as st

from services.auth import current_user, logout


def apply_theme(authenticated: bool) -> None:
    theme_mode = st.session_state.get("theme_mode", "light")
    dark_mode = theme_mode == "dark"
    background_css = """
        radial-gradient(circle at 10% 14%, rgba(47, 183, 201, 0.10), transparent 24%),
        radial-gradient(circle at 88% 12%, rgba(123, 79, 216, 0.08), transparent 26%),
        linear-gradient(180deg, #fbfcfe 0%, #f4f7fb 100%)
    """ if not dark_mode else """
        radial-gradient(circle at 12% 15%, rgba(47, 183, 201, 0.14), transparent 24%),
        radial-gradient(circle at 86% 10%, rgba(123, 79, 216, 0.15), transparent 24%),
        linear-gradient(180deg, #0f1728 0%, #121b2f 100%)
    """
    sidebar_css = "" if authenticated else """
    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    """

    st.markdown(
        dedent(
            f"""
            <style>
            :root {{
                --bg: {"#0f1728" if dark_mode else "#f5f7fb"};
                --bg-accent: {"#18243d" if dark_mode else "#edf3ff"};
                --panel: {"rgba(17,25,40,0.74)" if dark_mode else "rgba(255,255,255,0.76)"};
                --panel-strong: {"rgba(19,28,46,0.92)" if dark_mode else "rgba(255,255,255,0.92)"};
                --text: {"#eef4ff" if dark_mode else "#18243d"};
                --muted: {"#9cadc8" if dark_mode else "#6d7b92"};
                --line: {"rgba(198, 214, 255, 0.12)" if dark_mode else "rgba(59, 83, 128, 0.12)"};
                --accent-start: #2fb7c9;
                --accent-end: #7b4fd8;
                --accent-dark: {"#d8e6ff" if dark_mode else "#24427a"};
                --shadow: {"0 18px 55px rgba(0, 0, 0, 0.30)" if dark_mode else "0 18px 55px rgba(36, 66, 122, 0.10)"};
                --radius-lg: 28px;
                --radius-md: 20px;
                --radius-sm: 14px;
            }}

            html, body, [class*="css"]  {{
                font-family: "Inter", "Segoe UI", sans-serif !important;
            }}

            .stApp {{
                color: var(--text);
                background: {background_css};
            }}

            /* Hide Streamlit's Deploy button + three-dot toolbar */
            [data-testid="stToolbar"],
            [data-testid="stDecoration"],
            [data-testid="stStatusWidget"],
            #MainMenu {{
                display: none !important;
                visibility: hidden !important;
            }}

            [data-testid="stHeader"] {{
                background: transparent !important;
                height: 0 !important;
                min-height: 0 !important;
                padding: 0 !important;
            }}

            section.main > div {{
                padding-top: 5.6rem !important;
                max-width: 100% !important;
            }}

            .block-container {{
                max-width: 100% !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }}

            [data-testid="stSidebar"] {{
                width: 250px !important;
                min-width: 250px !important;
                background: {"linear-gradient(180deg, rgba(17,25,40,0.92), rgba(19,28,46,0.90))" if dark_mode else "linear-gradient(180deg, rgba(255,255,255,0.86), rgba(246,249,255,0.84))"};
                border-right: 1px solid var(--line);
                backdrop-filter: blur(18px);
            }}

            [data-testid="stSidebarNav"] {{
                padding-top: 1rem;
            }}

            [data-testid="stSidebarNav"] ul {{
                gap: 0.25rem;
            }}

            [data-testid="stSidebarNav"] li a {{
                border-radius: 14px;
                margin: 0.1rem 0.45rem;
                padding: 0.55rem 0.75rem;
                color: {"#d7e4ff" if dark_mode else "#35445e"};
            }}

            [data-testid="stSidebarNav"] li a:hover {{
                background: rgba(47, 183, 201, 0.10);
                color: var(--accent-dark);
            }}

            [data-testid="stSidebarNav"] li a[aria-current="page"] {{
                background: linear-gradient(90deg, rgba(47,183,201,0.14), rgba(123,79,216,0.14));
                color: var(--accent-dark);
                font-weight: 700;
            }}

            [data-testid="collapsedControl"] {{
                top: 5.6rem;
                left: 0.6rem;
                border-radius: 999px;
                background: {"rgba(19,28,46,0.92)" if dark_mode else "rgba(255,255,255,0.88)"};
                box-shadow: var(--shadow);
            }}

            {sidebar_css}

            .nav-shell {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                z-index: 1000;
                margin: 0;
            }}

            .nav-glass {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
                padding: 0.85rem 2rem;
                border-bottom: 1px solid {"rgba(255,255,255,0.08)" if dark_mode else "rgba(0,0,0,0.05)"};
                background: {"rgba(17,25,40,0.65)" if dark_mode else "rgba(255,255,255,0.70)"};
                backdrop-filter: blur(24px);
                -webkit-backdrop-filter: blur(24px);
            }}

            /* Responsive Navbar Logic */
            @media (max-width: 900px) {{
                .nav-shell [data-testid="column"]:nth-child(2),
                .nav-shell [data-testid="column"]:nth-child(3) {{
                    display: none !important;
                }}
                .nav-shell [data-testid="column"]:nth-child(4) {{
                    display: block !important;
                }}
            }}
            @media (min-width: 901px) {{
                .nav-shell [data-testid="column"]:nth-child(4) {{
                    display: none !important;
                }}
            }}

            .brand-wrapper {{
                position: relative;
                display: inline-block;
            }}

            .brand-glow {{
                position: absolute;
                top: 50%;
                left: 60%;
                transform: translate(-50%, -50%);
                width: 180px;
                height: 45px;
                background: linear-gradient(90deg, rgba(47, 183, 201, 0.4), rgba(123, 79, 216, 0.4));
                filter: blur(20px);
                border-radius: 100px;
                z-index: 0;
            }}

            .brand-inline {{
                display: flex;
                align-items: center;
                gap: 0.8rem;
                position: relative;
                z-index: 1;
            }}

            .brand-badge {{
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background: transparent;
                border: 2px solid var(--accent-end);
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--accent-start);
                font-weight: 900;
                font-size: 1.2rem;
            }}

            .brand-label {{
                font-size: 1.02rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                color: var(--text);
                margin: 0;
            }}

            .brand-sub {{
                margin: 0.1rem 0 0 0;
                color: {"#8ea2c9" if dark_mode else "#8c99b0"};
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
            }}

            .nav-links {{
                display: flex;
                gap: 1rem;
                align-items: center;
                color: var(--muted);
                font-size: 0.92rem;
            }}

            .nav-action-label {{
                margin: 0;
                text-align: center;
                color: var(--muted);
                font-size: 0.88rem;
                font-weight: 600;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            .page-shell {{
                padding-bottom: 1rem;
            }}

            .hero-panel, .tool-card, .metric-card {{
                border: 1px solid var(--line);
                background: linear-gradient(180deg, rgba(255,255,255,0.90), rgba(255,255,255,0.74));
                box-shadow: var(--shadow);
                backdrop-filter: blur(18px);
            }}

            .surface-card {{
                border: 1px solid var(--line);
                background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(255,255,255,0.76));
                border-radius: 28px;
                box-shadow: var(--shadow);
                padding: 1.4rem;
            }}

            .hero-panel {{
                border-radius: 32px;
                padding: 2.5rem;
            }}

            .tool-card {{
                border-radius: 24px;
                padding: 1.25rem;
            }}

            .metric-card {{
                border-radius: 22px;
                padding: 1rem 1.1rem;
            }}

            .mini-eyebrow {{
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                padding: 0.42rem 0.8rem;
                border-radius: 999px;
                background: rgba(255,255,255,0.84);
                border: 1px solid var(--line);
                color: var(--accent-dark);
                font-size: 0.82rem;
                font-weight: 700;
            }}

            .hero-title {{
                margin: 1.1rem 0 0.7rem 0;
                font-size: clamp(2.7rem, 5vw, 4.6rem);
                line-height: 0.96;
                letter-spacing: -0.06em;
                color: var(--text);
            }}

            .hero-muted {{
                max-width: 760px;
                color: var(--muted);
                line-height: 1.8;
                font-size: 1.02rem;
            }}

            .hero-kpis {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.85rem;
                margin-top: 1.4rem;
            }}

            .hero-kpi {{
                padding: 1rem;
                border-radius: 18px;
                background: rgba(255,255,255,0.72);
                border: 1px solid var(--line);
            }}

            .hero-kpi strong {{
                display: block;
                font-size: 1.2rem;
                color: var(--text);
            }}

            .hero-kpi span {{
                color: var(--muted);
                font-size: 0.86rem;
            }}

            .dual-btn {{
                display: inline-block;
                border-radius: 999px;
                padding: 0.9rem 1.45rem;
                background: linear-gradient(90deg, var(--accent-start), var(--accent-end));
                color: white;
                font-weight: 700;
                text-decoration: none;
                box-shadow: 0 18px 34px rgba(91, 96, 218, 0.18);
            }}

            .subtle-btn {{
                display: inline-block;
                border-radius: 999px;
                padding: 0.9rem 1.45rem;
                border: 1px solid var(--line);
                color: var(--accent-dark);
                background: rgba(255,255,255,0.82);
                text-decoration: none;
                font-weight: 700;
            }}

            .feature-grid {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 1rem;
            }}

            .insight-list {{
                display: grid;
                gap: 0.75rem;
                margin-top: 1rem;
            }}

            .insight-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
                padding: 0.9rem 1rem;
                border-radius: 18px;
                background: rgba(255,255,255,0.74);
                border: 1px solid var(--line);
            }}

            .insight-row strong {{
                color: var(--text);
            }}

            .status-pill {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0.32rem 0.7rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
            }}

            .status-blue {{
                background: rgba(47,183,201,0.14);
                color: #1d7284;
            }}

            .status-violet {{
                background: rgba(123,79,216,0.14);
                color: #6542b2;
            }}

            .status-slate {{
                background: rgba(59,83,128,0.10);
                color: #5a6882;
            }}

            .feature-block {{
                border: 1px solid var(--line);
                background: rgba(255,255,255,0.75);
                border-radius: 22px;
                padding: 1.2rem;
            }}

            .feature-block h4 {{
                margin: 0 0 0.45rem 0;
                color: var(--text);
                font-size: 1rem;
            }}

            .feature-block p {{
                margin: 0;
                color: var(--muted);
                line-height: 1.7;
                font-size: 0.94rem;
            }}

            .section-title {{
                margin: 0;
                color: var(--text);
                font-size: 1.4rem;
                letter-spacing: -0.03em;
            }}

            .section-copy {{
                margin: 0.45rem 0 0 0;
                color: var(--muted);
                line-height: 1.7;
            }}

            .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
                border-radius: 999px !important;
                border: 1px solid rgba(84, 110, 166, 0.10) !important;
                background: linear-gradient(90deg, var(--accent-start), var(--accent-end)) !important;
                color: white !important;
                font-weight: 700 !important;
                box-shadow: 0 16px 34px rgba(91, 96, 218, 0.14) !important;
                padding: 0.62rem 1rem !important;
                min-height: 48px !important;
                white-space: nowrap !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
            }}

            .stButton > button[kind="secondary"] {{
                background: {"rgba(19,28,46,0.92)" if dark_mode else "rgba(255,255,255,0.88)"} !important;
                color: var(--accent-dark) !important;
            }}

            .stSelectbox > div > div,
            .stTextInput > div > div > input,
            .stTextArea textarea,
            .stNumberInput input,
            .stDateInput input,
            .stFileUploader section {{
                border-radius: 16px !important;
            }}

            .stDataFrame, div[data-testid="stDataFrame"] {{
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid var(--line);
            }}

            [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .stMarkdown, p, label, span, div {{
                color: inherit;
            }}

            .stTabs [data-baseweb="tab-list"] {{
                gap: 0.5rem;
            }}

            .stTabs [data-baseweb="tab"] {{
                border-radius: 999px;
                background: rgba(255,255,255,0.72);
                border: 1px solid var(--line);
                padding: 0.4rem 1rem;
            }}

            /* Hide Streamlit Native Sidebar Completely to prevent duplicate navigation */
            [data-testid="stSidebar"], [data-testid="collapsedControl"] {{
                display: none !important;
            }}

            /* Make components.html navbar iframe truly full-width, flush to top */
            [data-testid="stCustomComponentV1"] {{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                margin: 0 !important;
                padding: 0 !important;
                z-index: 99999 !important;
                border: none !important;
            }}
            [data-testid="stCustomComponentV1"] iframe {{
                width: 100vw !important;
                display: block !important;
                pointer-events: auto !important;
            }}

            /* Tablet/Mobile (<1024px) */
            @media (max-width: 1023px) {{
                .feature-grid, .hero-kpis {{
                    grid-template-columns: 1fr;
                }}
                .nav-glass {{
                    padding: 0.6rem 1rem;
                }}
                .hero-title {{
                    font-size: 2.2rem;
                }}
            }}
            </style>
            """
        ),
        unsafe_allow_html=True,
    )


def render_navbar(authenticated: bool = False) -> None:
    """Fixed navbar injected directly into the page DOM via st.markdown. No JS needed."""

    # ── Inline SVG logo (magnifying glass + bar chart, matches uploaded logo) ──
    logo_html = '''<svg width="38" height="38" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#6366f1"/>
          <stop offset="100%" style="stop-color:#06b6d4"/>
        </linearGradient>
        <linearGradient id="bar" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color:#38bdf8"/>
          <stop offset="100%" style="stop-color:#0ea5e9"/>
        </linearGradient>
      </defs>
      <rect width="100" height="100" rx="20" fill="url(#bg)"/>
      <!-- Speed lines -->
      <rect x="8" y="36" width="20" height="5" rx="2.5" fill="#7dd3fc" opacity="0.9"/>
      <rect x="5" y="48" width="24" height="5" rx="2.5" fill="#93c5fd" opacity="0.8"/>
      <rect x="8" y="60" width="18" height="5" rx="2.5" fill="#7dd3fc" opacity="0.7"/>
      <!-- Magnifying glass circle -->
      <circle cx="63" cy="48" r="24" fill="none" stroke="white" stroke-width="7"/>
      <!-- Bar chart inside glass -->
      <rect x="47" y="52" width="7" height="12" rx="2" fill="url(#bar)"/>
      <rect x="57" y="44" width="7" height="20" rx="2" fill="url(#bar)"/>
      <rect x="67" y="38" width="7" height="26" rx="2" fill="white" opacity="0.95"/>
      <!-- Magnifying glass handle -->
      <line x1="81" y1="66" x2="92" y2="78" stroke="white" stroke-width="7" stroke-linecap="round"/>
    </svg>'''

    # ── Handle nav actions FIRST (before any rendering) ──
    nav_action = st.query_params.get("nav")
    if nav_action:
        if "nav" in st.query_params:
            del st.query_params["nav"]
        if nav_action == "login":
            st.session_state.auth_dialog_open = True
            st.rerun()
        elif nav_action == "logout":
            from services.auth import logout
            logout()
            st.rerun()

    # ── Build the auth token for links ──
    user = st.session_state.get("current_user")
    u_param = f"?u={user['email']}" if user and isinstance(user, dict) else ""

    # ── Build nav links ──
    if authenticated:
        links_html = f"""
            <a class="sd-nl" href="/{u_param}" target="_self">Home</a>
            <a class="sd-nl" href="/upload{u_param}" target="_self">Upload</a>
            <a class="sd-nl" href="/cdr_analysis{u_param}" target="_self">CDR</a>
            <a class="sd-nl" href="/idpr_analysis{u_param}" target="_self">IPDR</a>
            <a class="sd-nl" href="/tower_analysis{u_param}" target="_self">Tower Dump</a>
            <a class="sd-nl" href="/report_center{u_param}" target="_self">Reports</a>
        """
        cta_html = '<a class="sd-cta" href="/?nav=logout" target="_self">Log Out</a>'
    else:
        links_html = ""
        cta_html = '<a class="sd-cta" href="/?nav=login" target="_self">Log In / Sign Up</a>'

    # ── Same light glassmorphism style for BOTH states ──
    nav_bg = "rgba(255,255,255,.72)"
    nav_border = "rgba(59,83,128,.10)"
    brand_color = "#0f172a"
    link_color = "#475569"
    link_hover = "#0f172a"
    link_hover_bg = "rgba(0,0,0,.04)"

    navbar_html = f"""
    <style>
    .sd-navbar {{
        position: fixed !important;
        top: 0;
        left: 0;
        width: 100vw;
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.7rem 2rem;
        gap: 1rem;
        background: {nav_bg};
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid {nav_border};
        font-family: Inter, 'Segoe UI', sans-serif;
        box-sizing: border-box;
    }}
    .sd-navbar a, .sd-navbar a:visited, .sd-navbar a:active, .sd-navbar a:focus {{
        text-decoration: none !important;
    }}
    .sd-brand {{
        display: flex;
        align-items: center;
        gap: 0.55rem;
        cursor: pointer;
        text-decoration: none !important;
        flex-shrink: 0;
    }}
    .sd-badge {{
        width: 32px;
        height: 32px;
        border-radius: 9px;
        flex-shrink: 0;
        background: linear-gradient(135deg, #7c3aed, #06b6d4);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 800;
        font-size: 1rem;
    }}
    .sd-bname {{
        color: {brand_color};
        font-size: 0.95rem;
        font-weight: 700;
        line-height: 1.1;
    }}
    .sd-bsub {{
        color: #64748b;
        font-size: 0.5rem;
        letter-spacing: 0.12em;
        font-weight: 500;
    }}
    .sd-links {{
        display: flex;
        align-items: center;
        gap: 0.15rem;
        flex: 1;
        justify-content: center;
    }}
    .sd-nl {{
        color: {link_color} !important;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.4rem 0.85rem;
        border-radius: 8px;
        cursor: pointer;
        white-space: nowrap;
        text-decoration: none !important;
        border: 1px solid transparent;
        transition: color 0.18s, background 0.18s;
    }}
    .sd-nl:hover {{
        color: {link_hover} !important;
        background: {link_hover_bg};
    }}
    .sd-cta {{
        background: linear-gradient(135deg, #7c3aed, #06b6d4);
        color: #fff !important;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.45rem 1.1rem;
        border-radius: 999px;
        cursor: pointer;
        white-space: nowrap;
        text-decoration: none !important;
        transition: opacity 0.18s, transform 0.15s;
        display: inline-block;
        flex-shrink: 0;
    }}
    .sd-cta:hover {{
        opacity: 0.85;
        transform: translateY(-1px);
    }}

    /* Card styles for metrics and tools */
    .metric-card, .tool-card {{
        background: rgba(255,255,255,0.65) !important;
        border-radius: 12px !important;
        padding: 1rem 1.2rem !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 1rem !important;
        display: block !important;
    }}
    .metric-card .stMetric, .tool-card .stMetric {{
        margin: 0;
    }}
    .insight-list {{
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }}
    .insight-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0.6rem;
        background: rgba(0,0,0,0.04);
        border-radius: 8px;
    }}
    .status-pill {{
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.45rem;
        border-radius: 999px;
    }}
    .status-blue {{ background: #3b82f6; color: #fff; }}
    .status-violet {{ background: #8b5cf6; color: #fff; }}
    .status-slate {{ background: #64748b; color: #fff; }}

    /* Card styles for metrics and tools */
    .metric-card, .tool-card {{
        background: rgba(255,255,255,0.65);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }}
    .metric-card .stMetric, .tool-card .stMetric {{
        margin: 0;
    }}
    .insight-list {{
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }}
    .insight-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0.6rem;
        background: rgba(0,0,0,0.04);
        border-radius: 8px;
    }}
    .status-pill {{
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.2rem 0.45rem;
        border-radius: 999px;
    }}
    .status-blue {{ background: #3b82f6; color: #fff; }}
    .status-violet {{ background: #8b5cf6; color: #fff; }}
    .status-slate {{ background: #64748b; color: #fff; }}

    /* Push page content below the fixed navbar */
    section.main > div {{
        padding-top: 4.5rem !important;
    }}
    [data-testid="stHeader"] {{
        display: none !important;
    }}
    [data-testid="stSidebar"], [data-testid="collapsedControl"] {{
        display: none !important;
    }}
    /* Force Streamlit wrappers containing navbar to be fixed */
    div[data-testid="stMarkdownContainer"]:has(.sd-navbar),
    div[data-testid="stElementContainer"]:has(.sd-navbar),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.sd-navbar) {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        z-index: 999999 !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    </style>

    <div class="sd-navbar">
        <a class="sd-brand" href="/{u_param}" target="_self">
            {logo_html}
            <div>
                <div class="sd-bname">SmartDesk</div>
                <div class="sd-bsub">TELECOM INVESTIGATION SIMPLIFIED</div>
            </div>
        </a>
        <div class="sd-links">{links_html}</div>
        {cta_html}
    </div>
    """
    
    st.markdown(navbar_html, unsafe_allow_html=True)


def page_intro(title: str, description: str, eyebrow: str | None = None) -> None:
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    if eyebrow:
        st.markdown(f'<div class="mini-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="section-title" style="font-size:2rem; margin-top:0.9rem;">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="section-copy">{description}</p>', unsafe_allow_html=True)


def close_page_shell() -> None:
    st.markdown("</div>", unsafe_allow_html=True)