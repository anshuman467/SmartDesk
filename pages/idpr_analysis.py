import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from database.db import fetch_records
from services.auth import require_login
from services.analytics import (
    filter_ipdr, 
    generate_ipdr_summary, 
    generate_ipdr_threats, 
    get_ipdr_sankey_data,
    dataframe_to_csv_bytes,
    classify_port_behavior
)
from services.ui import apply_theme, close_page_shell, page_intro, render_navbar

require_login()
apply_theme(True)
render_navbar(authenticated=True)

# ── DATA LOADING ──────────────────────────────────────────────────────────
records = fetch_records("file_type = ?", ("ipdr",))
if records.empty:
    page_intro("IPDR Analysis", "No records found. Please upload data first.", eyebrow="Cyber Forensics")
    st.warning("No IPDR data available.")
    st.stop()

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Cyber Filters")
    phone_filter = st.text_input("Target Number", placeholder="e.g. 9876543210")
    ip_filter = st.text_input("Destination IP", placeholder="e.g. 157.240.")
    port_filter = st.text_input("Destination Port")
    
    st.markdown("---")
    date_range = st.date_input("Date Range", [])
    risk_filter = st.multiselect("Risk Level", ["Low", "Medium", "High", "Critical"])

# ── DATA PROCESSING ───────────────────────────────────────────────────────
filtered = filter_ipdr(
    records,
    phone_number=phone_filter,
    destination_ip=ip_filter,
    destination_port=port_filter
)

summary = generate_ipdr_summary(filtered)
threats = generate_ipdr_threats(filtered)

# ── UI LAYOUT ─────────────────────────────────────────────────────────────
page_intro(
    "Digital Intelligence Dashboard",
    f"Analyzing {len(filtered)} internet sessions for target profiling and cyber threat detection.",
    eyebrow="IPDR Forensic Suite"
)

# 1. TOP SUMMARY RIBBON (pure HTML - stays inside boxes correctly)
metrics = [
    ("Total Sessions", summary["total"], "Blue"),
    ("Unique IPs", summary["unique_ips"], "Blue"),
    ("VPN Hits", summary["vpn_hits"], "Yellow" if summary["vpn_hits"] > 0 else "Blue"),
    ("Messaging %", f"{summary['msg_pct']}%", "Blue"),
    ("Digital Risk", f"{summary['risk_score']}/100", "Red" if summary["risk_score"] > 60 else "Yellow")
]
st.markdown("".join([f"""
    <div style="display:inline-block;width:calc(20% - 0.8rem);margin-right:1rem;
        background:rgba(255,255,255,0.75);border-radius:14px;padding:1rem 1.2rem;
        box-shadow:0 2px 10px rgba(0,0,0,0.07);border:1px solid rgba(0,0,0,0.06);
        border-left:4px solid {color.lower()};vertical-align:top;">
      <div style="font-size:0.78rem;color:#64748b;font-weight:600;letter-spacing:.04em;margin-bottom:.3rem;">{label}</div>
      <div style="font-size:1.6rem;font-weight:800;color:#0f172a;line-height:1;">{val}</div>
    </div>""" for label, val, color in metrics
]), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 2. MAIN INTELLIGENCE ZONE
left_col, right_col = st.columns([1.1, 0.9])

with left_col:
    with st.container(border=True):
        st.subheader("🌐 Application Flow Matrix")
        st.caption("Visualizing traffic flow from Suspect to Application Category and Infrastructure.")
        
        sankey_data = get_ipdr_sankey_data(filtered, phone_filter)
        if sankey_data["links"]:
            fig = go.Figure(data=[go.Sankey(
                node = dict(
                  pad = 15,
                  thickness = 20,
                  line = dict(color = "black", width = 0.5),
                  label = sankey_data["nodes"],
                  color = "#7c3aed"
                ),
                link = dict(
                  source = [l["source"] for l in sankey_data["links"]],
                  target = [l["target"] for l in sankey_data["links"]],
                  value = [l["value"] for l in sankey_data["links"]],
                  color = "rgba(124, 58, 237, 0.2)"
              ))])
            fig.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Insufficient data for Sankey flow.")

with right_col:
    with st.container(border=True):
        st.subheader("🚨 Digital Threat Panel")
        
        for t in threats:
            color = "#ef4444" if t["level"] == "Critical" else "#f59e0b" if t["level"] == "Suspicious" else "#3b82f6"
            st.markdown(f"""
                <div style="padding:1rem; border-radius:14px; background:rgba(0,0,0,0.03); border-left:4px solid {color}; margin-bottom:1rem;">
                    <div style="font-weight:700; color:{color}; font-size:0.9rem;">{t['level'].upper()}</div>
                    <div style="font-weight:600; margin-top:0.2rem; color:#0f172a;">{t['title']}</div>
                    <div style="font-size:0.85rem; color:#64748b; margin-top:0.3rem;">{t['desc']}</div>
                </div>
            """, unsafe_allow_html=True)

# 3. LOWER ANALYTICS
st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    with st.container(border=True):
        st.subheader("📊 Service Category Distribution")
        if not filtered.empty:
            filtered["port_cat"] = filtered["destination_port"].apply(lambda x: classify_port_behavior(x)["category"])
            cat_counts = filtered["port_cat"].value_counts()
            st.bar_chart(cat_counts)

with c2:
    with st.container(border=True):
        st.subheader("📅 Activity Intensity")
        if "date_time" in filtered.columns:
            hourly = filtered["date_time"].dt.hour.value_counts().sort_index()
            st.line_chart(hourly)

# 4. RAW RECORDS
with st.expander("📂 View Raw Forensic Records"):
    st.dataframe(filtered, use_container_width=True)
    st.download_button(
        "Download Export (.csv)",
        data=dataframe_to_csv_bytes(filtered),
        file_name="forensic_ipdr_export.csv",
        mime="text/csv"
    )

close_page_shell()


