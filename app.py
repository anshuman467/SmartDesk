

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from database.db import clear_database, ensure_database, get_case_summary
from services.auth import current_user, init_session, login, signup
from services.reporting import generate_forensic_hit_report
from services.sample_data import ensure_sample_directory, seed_demo_records
from services.ui import apply_theme, close_page_shell, page_intro, render_navbar


st.set_page_config(
    page_title="Telecom Investigation Dashboard",
    page_icon="T",
    layout="wide",
    initial_sidebar_state="collapsed",
)


BASE_DIR = Path(__file__).resolve().parent
ensure_database()
ensure_sample_directory(BASE_DIR / "data" / "sample")
init_session()

if "auth_dialog_open" not in st.session_state:
    st.session_state.auth_dialog_open = False


@st.dialog("Access SmartDesk", width="large")
def auth_dialog() -> None:
    st.write("Enter your credentials to access the investigation workspace.")
    if "auth_view" not in st.session_state:
        st.session_state.auth_view = "login"

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Log In", use_container_width=True, type="primary" if st.session_state.auth_view == "login" else "secondary"):
            st.session_state.auth_view = "login"
            st.rerun()
    with col2:
        if st.button("Sign Up", use_container_width=True, type="primary" if st.session_state.auth_view == "signup" else "secondary"):
            st.session_state.auth_view = "signup"
            st.rerun()

    if st.session_state.auth_view == "login":
        if "signup_success" in st.session_state:
            st.success(st.session_state.signup_success)
            del st.session_state.signup_success

        with st.form("login_form_dialog"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
        if submitted:
            if login(email, password):
                st.session_state.auth_dialog_open = False
                st.success("Logged in successfully.")
                st.rerun()
            st.error("Invalid email or password. If you haven't created an account yet, please use the 'Sign Up' tab first!")

    else:
        with st.form("signup_form_dialog"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email", key="signup_email_dialog")
            password = st.text_input("Password", type="password", key="signup_password_dialog")
            submitted = st.form_submit_button("Create Account")
        if submitted:
            ok, message = signup(full_name, email, password)
            if ok:
                st.session_state.signup_success = message
                st.session_state.auth_view = "login"  # Automatically switch to Login view
                st.rerun()
            else:
                st.error(message)


def render_landing() -> None:
    # ── Hero ──────────────────────────────────────────────────────────────
    components.html(
        """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
          html, body {
            margin: 0; padding: 0;
            background: transparent;
            overflow: hidden;
            font-family: Inter, Segoe UI, sans-serif;
          }
          .hero-wrap {
            position: relative;
            height: 560px;
            border-radius: 34px;
            overflow: hidden;
            border: 1px solid rgba(59, 83, 128, 0.12);
            background:
              radial-gradient(circle at 20% 18%, rgba(47,183,201,0.10), transparent 24%),
              radial-gradient(circle at 82% 14%, rgba(123,79,216,0.08), transparent 22%),
              linear-gradient(180deg, rgba(255,255,255,0.82), rgba(255,255,255,0.60));
            box-shadow: 0 18px 55px rgba(36, 66, 122, 0.10);
          }
          canvas { position:absolute; inset:0; width:100%; height:100%; }
          .grid {
            position:absolute; inset:0;
            background-image:
              linear-gradient(rgba(48,68,104,0.05) 1px, transparent 1px),
              linear-gradient(90deg, rgba(48,68,104,0.05) 1px, transparent 1px);
            background-size:28px 28px;
            mask-image:linear-gradient(180deg,rgba(0,0,0,0.65),rgba(0,0,0,0.18));
            pointer-events:none;
          }
          .center-copy {
            position:absolute; inset:0;
            display:flex; flex-direction:column;
            align-items:center; justify-content:center;
            text-align:center; padding:0 36px;
            pointer-events:none;
          }
          .eyebrow {
            display:inline-flex; align-items:center;
            padding:8px 14px; border-radius:999px;
            border:1px solid rgba(59,83,128,0.12);
            background:rgba(255,255,255,0.76);
            color:#35507f; font-size:12px; font-weight:700;
            letter-spacing:0.08em; text-transform:uppercase;
          }
          h1 {
            margin:18px 0 12px 0;
            font-size:clamp(42px,7vw,78px);
            line-height:0.96; letter-spacing:-0.06em;
            color:#18243d; max-width:920px;
          }
          p { margin:0; max-width:720px; color:#68758c; font-size:18px; line-height:1.75; }
        </style>
        </head>
        <body>
          <div class="hero-wrap" id="hero">
            <canvas id="network-canvas"></canvas>
            <div class="grid"></div>
            <div class="center-copy">
              <div class="eyebrow">Telecom Forensic Investigation System</div>
              <h1>Advanced Intelligence.<br/>Cross-Link Analysis.</h1>
            </div>
          </div>
          <script>
            const hero=document.getElementById("hero");
            const canvas=document.getElementById("network-canvas");
            const ctx=canvas.getContext("2d");
            let nodes=[];
            const palette=["#2fb7c9","#5fa7ff","#7b4fd8"];
            let pointer={x:0,y:0,active:false};
            function resize(){
              const rect=hero.getBoundingClientRect();
              const ratio=window.devicePixelRatio||1;
              canvas.width=rect.width*ratio; canvas.height=rect.height*ratio;
              canvas.style.width=rect.width+"px"; canvas.style.height=rect.height+"px";
              ctx.setTransform(ratio,0,0,ratio,0,0);
              nodes.length=0;
              const count=Math.max(50,Math.floor(rect.width/25));
              for(let i=0;i<count;i++) nodes.push({x:Math.random()*rect.width,y:Math.random()*rect.height,vx:(Math.random()-.5)*.4,vy:(Math.random()-.5)*.4,size:Math.random()*2.5+1.5,color:palette[i%palette.length]});
            }
            function draw(){
              const rect=hero.getBoundingClientRect();
              ctx.clearRect(0,0,rect.width,rect.height);
              for(const n of nodes){n.x+=n.vx;n.y+=n.vy;if(n.x<0||n.x>rect.width)n.vx*=-1;if(n.y<0||n.y>rect.height)n.vy*=-1;}
              ctx.lineWidth=1;
              for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
                const dx=nodes[i].x-nodes[j].x,dy=nodes[i].y-nodes[j].y,dist=Math.sqrt(dx*dx+dy*dy);
                if(dist<120){ctx.globalAlpha=(120-dist)/120*.3;ctx.strokeStyle=nodes[i].color;ctx.beginPath();ctx.moveTo(nodes[i].x,nodes[i].y);ctx.lineTo(nodes[j].x,nodes[j].y);ctx.stroke();}
              }
              ctx.globalAlpha=.9;
              for(const n of nodes){ctx.fillStyle=n.color;ctx.beginPath();ctx.arc(n.x,n.y,n.size,0,Math.PI*2);ctx.fill();}
              if(pointer.active){
                const glow=ctx.createRadialGradient(pointer.x,pointer.y,0,pointer.x,pointer.y,200);
                glow.addColorStop(0,"rgba(47,183,201,0.15)");glow.addColorStop(.5,"rgba(123,79,216,0.05)");glow.addColorStop(1,"rgba(255,255,255,0)");
                ctx.globalAlpha=1;ctx.fillStyle=glow;ctx.beginPath();ctx.arc(pointer.x,pointer.y,200,0,Math.PI*2);ctx.fill();
                for(const n of nodes){const dx=pointer.x-n.x,dy=pointer.y-n.y,dist=Math.sqrt(dx*dx+dy*dy);
                  if(dist<150){ctx.globalAlpha=(150-dist)/150*.5;ctx.strokeStyle="#5fa7ff";ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(pointer.x,pointer.y);ctx.lineTo(n.x,n.y);ctx.stroke();ctx.setLineDash([]);}}
              }
              requestAnimationFrame(draw);
            }
            hero.addEventListener("mousemove",(e)=>{const r=hero.getBoundingClientRect();pointer.x=e.clientX-r.left;pointer.y=e.clientY-r.top;pointer.active=true;});
            hero.addEventListener("mouseleave",()=>{pointer.active=false;});
            window.addEventListener("resize",resize);
            resize(); draw();
          </script>
        </body>
        </html>
        """,
        height=560,
    )

    # ── Tagline slide ──────────────────────────────────────────────────────
    st.markdown("""
    <div style="
      text-align: center;
      padding: 10rem 2rem 5rem;
      max-width: 900px;
      margin: 0 auto;
    ">
      <h2 style="
        margin: 0 0 1.5rem;
        font-size: clamp(2.5rem, 5vw, 4.5rem);
        font-weight: 800;
        letter-spacing: -.05em;
        line-height: 1.1;
        color: var(--text);
      ">Turning Metadata into<br><span style="background:linear-gradient(135deg,#7c3aed,#06b6d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Meaningful Evidence.</span></h2>

      <p style="
        font-size: 1.4rem; 
        color: var(--muted); 
        font-weight: 500; 
        letter-spacing: -0.02em; 
        margin: 0 auto 3.5rem;
        max-width: 600px;
      ">
        Trace cross-links. Map routes. Catch suspects instantly.
      </p>
    </div>
    """, unsafe_allow_html=True)

    left, center, right = st.columns([1, 0.4, 1])
    with center:
        if st.button("Get Started →", key="hero_explore", use_container_width=True):
            st.session_state.auth_dialog_open = True
            st.rerun()

    # thin hairline divider before features
    st.markdown("""
    <div style="width:60px;height:2px;margin:3rem auto 0;
                background:linear-gradient(90deg,#7c3aed,#06b6d4);
                border-radius:2px;"></div>
    """, unsafe_allow_html=True)

    # ── Scroll divider ─────────────────────────────────────────────────────
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    # ── FEATURES section ──────────────────────────────────────────────────
    st.markdown('<div id="features"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:4rem;padding-top:6rem;">
      <h2 style="margin:0;font-size:clamp(2rem,4vw,3.5rem);font-weight:800;
                 letter-spacing:-.04em;color:var(--text);">
        Everything you need.
      </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="feature-grid" style="gap:0.8rem;">
        <div class="surface-card" style="padding:1rem 0.8rem;text-align:center;">
            <div style="font-size:1.4rem;margin-bottom:0.4rem;">📞</div>
            <h3 style="color:var(--text);font-size:0.95rem;margin:0;">CDR Processing</h3>
            <p style="color:var(--muted);margin-top:0.3rem;font-size:0.8rem;">Filter millions of call records instantly.</p>
        </div>
        <div class="surface-card" style="padding:1rem 0.8rem;text-align:center;">
            <div style="font-size:1.4rem;margin-bottom:0.4rem;">🌐</div>
            <h3 style="color:var(--text);font-size:0.95rem;margin:0;">IPDR Tracking</h3>
            <p style="color:var(--muted);margin-top:0.3rem;font-size:0.8rem;">Track suspect web traffic and IPs.</p>
        </div>
        <div class="surface-card" style="padding:1rem 0.8rem;text-align:center;">
            <div style="font-size:1.4rem;margin-bottom:0.4rem;">🔗</div>
            <h3 style="color:var(--text);font-size:0.95rem;margin:0;">Cross-Linkage</h3>
            <p style="color:var(--muted);margin-top:0.3rem;font-size:0.8rem;">Intersect data to find common suspects.</p>
        </div>
        <div class="surface-card" style="padding:1rem 0.8rem;text-align:center;">
            <div style="font-size:1.4rem;margin-bottom:0.4rem;">📡</div>
            <h3 style="color:var(--text);font-size:0.95rem;margin:0;">Tower Dumps</h3>
            <p style="color:var(--muted);margin-top:0.3rem;font-size:0.8rem;">Identify numbers across multiple scenes.</p>
        </div>
        <div class="surface-card" style="padding:1rem 0.8rem;text-align:center;">
            <div style="font-size:1.4rem;margin-bottom:0.4rem;">🗺️</div>
            <h3 style="color:var(--text);font-size:0.95rem;margin:0;">Live Mapping</h3>
            <p style="color:var(--muted);margin-top:0.3rem;font-size:0.8rem;">Visualize suspect escape routes.</p>
        </div>
        <div class="surface-card" style="padding:1rem 0.8rem;text-align:center;">
            <div style="font-size:1.4rem;margin-bottom:0.4rem;">📄</div>
            <h3 style="color:var(--text);font-size:0.95rem;margin:0;">Auto Reports</h3>
            <p style="color:var(--muted);margin-top:0.3rem;font-size:0.8rem;">Generate court-ready evidence.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:3.5rem'></div>", unsafe_allow_html=True)

    # ── ANALYSIS section ───────────────────────────────────────────────────
    st.markdown('<div id="analysis"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:4rem;padding-top:8rem;">
      <h2 style="margin:0;font-size:clamp(2rem,4vw,3.5rem);font-weight:800;
                 letter-spacing:-.04em;color:var(--text);">
        How we find the needle.
      </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;justify-content:center;gap:1rem;flex-wrap:wrap;text-align:center;">
        <div style="flex:1;min-width:180px;padding:1rem 0.8rem;background:transparent;">
            <div style="font-size:1.3rem;font-weight:800;color:var(--muted);opacity:0.3;margin-bottom:0.4rem;">01</div>
            <h3 style="font-size:0.95rem;color:var(--text);margin:0;">Normalize</h3>
            <p style="color:var(--muted);font-size:0.8rem;margin-top:0.3rem;">Standardize millions of raw rows instantly.</p>
        </div>
        <div style="flex:1;min-width:180px;padding:1rem 0.8rem;background:transparent;">
            <div style="font-size:1.3rem;font-weight:800;color:var(--muted);opacity:0.3;margin-bottom:0.4rem;">02</div>
            <h3 style="font-size:0.95rem;color:var(--text);margin:0;">Intersect</h3>
            <p style="color:var(--muted);font-size:0.8rem;margin-top:0.3rem;">Filter out 99.9% of innocent data.</p>
        </div>
        <div style="flex:1;min-width:180px;padding:1rem 0.8rem;background:transparent;">
            <div style="font-size:1.3rem;font-weight:800;color:var(--muted);opacity:0.3;margin-bottom:0.4rem;">03</div>
            <h3 style="font-size:0.95rem;color:var(--text);margin:0;">Match</h3>
            <p style="color:var(--muted);font-size:0.8rem;margin-top:0.3rem;">Reveal hidden connections and suspects.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:3.5rem'></div>", unsafe_allow_html=True)

    # ── MAP VIEW section ───────────────────────────────────────────────────
    st.markdown('<div id="map"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:4rem;padding-top:8rem;">
      <h2 style="margin:0;font-size:clamp(2rem,4vw,3.5rem);font-weight:800;
                 letter-spacing:-.04em;color:var(--text);">
        See the route.
      </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex;gap:1rem;flex-wrap:wrap;justify-content:center;align-items:center;">
        <div style="flex:1;min-width:200px;max-width:500px;text-align:center;padding:0.5rem;">
            <h3 style="font-size:1.2rem;margin:0;">Precision Mapping</h3>
            <p style="color:var(--muted);font-size:0.85rem;margin-top:0.6rem;">
            Convert raw Cell IDs into exact GPS coordinates. Plot the suspect's escape route directly on an interactive satellite map.
            </p>
        </div>
        <div style="flex:1;min-width:200px;text-align:center;padding:0.5rem;">
            <div style="background: rgba(10,14,28,0.45); border: 1px solid rgba(124,58,237,0.15); border-radius: 12px; padding: 1rem 0.8rem; backdrop-filter: blur(12px); box-shadow: 0 2px 10px rgba(0,0,0,0.15);">
                <div style="font-size:1.5rem;margin-bottom:0.8rem;">🛰️</div>
                <p style="color:rgba(255,255,255,0.5);font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;font-weight:600;">System Stack</p>
                <h4 style="color:#fff;font-size:0.95rem;margin:0;font-weight:700;letter-spacing:-0.01em;">OpenCelliD &bull; Leaflet &bull; Esri</h4>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:3.5rem'></div>", unsafe_allow_html=True)

    # ── REPORTS section ────────────────────────────────────────────────────
    st.markdown('<div id="reports"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;margin-bottom:3rem;padding-top:8rem;">
      <h2 style="margin:0;font-size:clamp(2rem,4vw,3.5rem);font-weight:800;
                 letter-spacing:-.04em;color:var(--text);">
        Court-Ready Evidence.
      </h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:2rem;">
        <div style="font-size:4rem;margin-bottom:1.5rem;">📑</div>
        <h3 style="font-size:1.8rem;margin:0 0 1rem 0;color:var(--text);">One-Click Generation</h3>
        <p style="color:var(--muted);font-size:1.2rem;max-width:600px;margin:0 auto;line-height:1.6;">
        Automatically compile cross-link discoveries and timelines into a structured report. Ready for FIR attachment.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:8rem'></div>", unsafe_allow_html=True)


def render_workspace() -> None:
    summary = get_case_summary()
    user = current_user()
    if user is None:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.warning("Your session is no longer valid. Please log in again.")
        return


    page_intro(
        "Investigation Workspace",
        "Use this home view as a command center for data intake, correlation, geospatial review, and report output.",
        eyebrow="Workspace Overview",
    )

    # ── Metric cards (pure HTML so content stays inside the box) ──
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.2rem;">
      <div style="background:rgba(255,255,255,0.75);border-radius:14px;padding:1.1rem 1.4rem;box-shadow:0 2px 10px rgba(0,0,0,0.07);border:1px solid rgba(0,0,0,0.06);">
        <div style="font-size:0.78rem;color:#64748b;font-weight:600;letter-spacing:.05em;margin-bottom:.35rem;">FILES</div>
        <div style="font-size:2rem;font-weight:700;color:#0f172a;line-height:1;">{summary["files"]}</div>
      </div>
      <div style="background:rgba(255,255,255,0.75);border-radius:14px;padding:1.1rem 1.4rem;box-shadow:0 2px 10px rgba(0,0,0,0.07);border:1px solid rgba(0,0,0,0.06);">
        <div style="font-size:0.78rem;color:#64748b;font-weight:600;letter-spacing:.05em;margin-bottom:.35rem;">RECORDS</div>
        <div style="font-size:2rem;font-weight:700;color:#0f172a;line-height:1;">{summary["records"]}</div>
      </div>
      <div style="background:rgba(255,255,255,0.75);border-radius:14px;padding:1.1rem 1.4rem;box-shadow:0 2px 10px rgba(0,0,0,0.07);border:1px solid rgba(0,0,0,0.06);">
        <div style="font-size:0.78rem;color:#64748b;font-weight:600;letter-spacing:.05em;margin-bottom:.35rem;">UNIQUE NUMBERS</div>
        <div style="font-size:2rem;font-weight:700;color:#0f172a;line-height:1;">{summary["unique_numbers"]}</div>
      </div>
      <div style="background:rgba(255,255,255,0.75);border-radius:14px;padding:1.1rem 1.4rem;box-shadow:0 2px 10px rgba(0,0,0,0.07);border:1px solid rgba(0,0,0,0.06);">
        <div style="font-size:0.78rem;color:#64748b;font-weight:600;letter-spacing:.05em;margin-bottom:.35rem;">UNIQUE TOWERS</div>
        <div style="font-size:2rem;font-weight:700;color:#0f172a;line-height:1;">{summary["unique_towers"]}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two column tool cards ──
    left, right = st.columns([1.15, 0.85], vertical_alignment="top")

    with left:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.75);border-radius:14px;padding:1.4rem 1.6rem;box-shadow:0 2px 10px rgba(0,0,0,0.07);border:1px solid rgba(0,0,0,0.06);">
          <div style="font-size:0.9rem;color:#475569;margin-bottom:1rem;">
            <strong>Active User:</strong> <code style="background:rgba(0,0,0,0.06);padding:.15rem .4rem;border-radius:6px;">{user['full_name']}</code>
          </div>
          <div style="display:flex;flex-direction:column;gap:0.65rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:.55rem .8rem;background:rgba(0,0,0,0.03);border-radius:10px;">
              <div>
                <div style="font-weight:600;font-size:0.9rem;color:#0f172a;">1. Intake and normalize</div>
                <div style="font-size:0.82rem;color:#64748b;margin-top:.2rem;">Open Upload and save the raw documents into the database.</div>
              </div>
              <span style="background:#3b82f6;color:#fff;font-size:0.72rem;font-weight:700;padding:.2rem .55rem;border-radius:999px;white-space:nowrap;margin-left:.8rem;">Start</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:.55rem .8rem;background:rgba(0,0,0,0.03);border-radius:10px;">
              <div>
                <div style="font-weight:600;font-size:0.9rem;color:#0f172a;">2. Correlate records</div>
                <div style="font-size:0.82rem;color:#64748b;margin-top:.2rem;">Use CDR, IPDR, and Cross Link pages to isolate suspicious entities.</div>
              </div>
              <span style="background:#8b5cf6;color:#fff;font-size:0.72rem;font-weight:700;padding:.2rem .55rem;border-radius:999px;white-space:nowrap;margin-left:.8rem;">Analyse</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:.55rem .8rem;background:rgba(0,0,0,0.03);border-radius:10px;">
              <div>
                <div style="font-weight:600;font-size:0.9rem;color:#0f172a;">3. Present findings</div>
                <div style="font-size:0.82rem;color:#64748b;margin-top:.2rem;">Use Tower Analysis, Map View, and Report Center for output.</div>
              </div>
              <span style="background:#64748b;color:#fff;font-size:0.72rem;font-weight:700;padding:.2rem .55rem;border-radius:999px;white-space:nowrap;margin-left:.8rem;">Present</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        # Use native bordered container — works correctly for Streamlit widgets
        with st.container(border=True):
            st.subheader("Quick Actions")
            if st.button("Seed Demo Data", key="seed_demo_home"):
                inserted = seed_demo_records(BASE_DIR / "data" / "sample")
                st.success(f"Inserted {inserted} demo records into the database.")
            if st.button("Clear Database", key="clear_db_home"):
                clear_database()
                st.warning("Database cleared.")
            if st.page_link("pages/report_center.py", label="Open Forensic Report Center", icon="📄"):
                pass
            st.caption("Use the navigation bar for detailed analytical modules.")

    close_page_shell()



def main() -> None:
    authenticated = bool(st.session_state.get("authenticated"))
    apply_theme(authenticated)
    render_navbar(authenticated)

    if not authenticated:
        render_landing()
        if st.session_state.auth_dialog_open:
            auth_dialog()

        # Scroll-to-section via JS after page renders
        section = st.session_state.get("landing_section", "")
        if section and section != "home":
            st.markdown(f"""
            <script>
              setTimeout(()=>{{
                const el=document.getElementById('{section}');
                if(el) el.scrollIntoView({{behavior:'smooth',block:'start'}});
              }}, 200);
            </script>
            """, unsafe_allow_html=True)
            st.session_state.landing_section = "home"
    else:
        render_workspace()


if __name__ == "__main__":
    main()
