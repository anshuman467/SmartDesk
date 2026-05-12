import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import math
from datetime import time

from database.db import fetch_records
from services.auth import require_login
from services.analytics import (
    dataframe_to_csv_bytes, 
    filter_cdr, 
    tower_intelligence_panel, 
    get_hour_heatmap_data,
    contact_intelligence_table,
    generate_suspect_summary,
    generate_threat_panel,
    build_behavioral_timeline
)
from services.ui import apply_theme, close_page_shell, page_intro, render_navbar

require_login()
apply_theme(True)
render_navbar(True)

# ── CUSTOM UI STYLES FOR THREAT PANEL ─────────────────────────────────────
st.markdown("""
<style>
.threat-card {
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border-left: 4px solid;
    background: rgba(10, 14, 28, 0.6);
}
.threat-Critical { border-color: #ef4444; }
.threat-Suspicious { border-color: #eab308; }
.threat-Multi-link { border-color: #a855f7; }
.threat-Neutral { border-color: #3b82f6; }

.threat-title {
    font-weight: 700;
    margin-bottom: 0.25rem;
    font-size: 1.05rem;
}
.threat-Critical .threat-title { color: #ef4444; }
.threat-Suspicious .threat-title { color: #fde047; }
.threat-Multi-link .threat-title { color: #d8b4fe; }
.threat-Neutral .threat-title { color: #93c5fd; }

.threat-desc {
    font-size: 0.9rem;
    color: var(--muted);
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

page_intro(
    "CDR Analysis",
    "Forensic behavioral profiling, movement tracking, and automated threat detection.",
    eyebrow="Intelligence Dashboard",
)

# ── DATA LOADING ──────────────────────────────────────────────────────────
records = fetch_records("file_type = ?", ("cdr",))
if records.empty:
    st.warning("No CDR records available. Please upload forensic data first.")
    st.stop()

# ── LEFT PANEL: INVESTIGATION FILTERS (SIDEBAR) ───────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Investigation Filters")
    phone_number = st.text_input("Target Number (Suspect)")
    other_party = st.text_input("Contact Number")
    
    tower_options = sorted(records["tower_id"].dropna().unique().tolist())
    tower_ids = st.multiselect("Filter by Towers", options=tower_options)
    
    type_options = sorted(records["call_type"].dropna().unique().tolist())
    call_types = st.multiselect("Call Types", options=type_options)
    
    date_range = st.date_input(
        "Date Range",
        value=(records["date_time"].min().date(), records["date_time"].max().date())
    )
    
    time_range = st.slider(
        "Time of Day",
        value=(time(0, 0), time(23, 59)),
        format="HH:mm"
    )
    min_dur = st.number_input("Minimum Duration (seconds)", min_value=0, value=0)

# Apply Filters
filtered = filter_cdr(
    records,
    phone_number=phone_number,
    other_party_number=other_party,
    tower_id=tower_ids if tower_ids else None,
    call_type=call_types if call_types else None,
    date_range=date_range if len(date_range) == 2 else None,
    time_range=time_range,
    min_duration=min_dur
)

# ── TOP RIBBON: SUSPECT SUMMARY ───────────────────────────────────────────
st.markdown("#### 🎯 Suspect Summary Ribbon")
summary = generate_suspect_summary(filtered)

ribbon_c1, ribbon_c2, ribbon_c3, ribbon_c4, ribbon_c5, ribbon_c6 = st.columns(6)
ribbon_c1.metric("Total Calls", summary["total_calls"])
ribbon_c2.metric("Unique Contacts", summary["unique_contacts"])
ribbon_c3.metric("Top Tower", summary["top_tower"])
ribbon_c4.metric("IMEI Count", summary["imei_count"])
ribbon_c5.metric("Active Days", summary["active_days"])
ribbon_c6.metric("Risk Score", f"{summary['risk_score']}/100", 
                 delta="High Risk" if summary['risk_score'] >= 70 else "Low Risk", 
                 delta_color="inverse" if summary['risk_score'] >= 70 else "normal")

st.markdown("---")

# ── MAIN SCREEN LAYOUT: CENTER (INTELLIGENCE) & RIGHT (THREAT PANEL) ──────
main_col, threat_col = st.columns([2.5, 1], gap="large")

with main_col:
    st.markdown("### 🧠 Primary Intelligence Zone")
    
    # 1. Behavioral Timeline
    st.markdown("##### Behavioral Timeline")
    timeline_df = build_behavioral_timeline(filtered)
    if not timeline_df.empty:
        fig_time = px.bar(
            timeline_df, x="date", y="total_events",
            labels={"date": "Date", "total_events": "Call Events"},
            color_discrete_sequence=["#3b82f6"]
        )
        fig_time.update_layout(margin=dict(l=0, r=0, b=0, t=10), height=250, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("No timeline data available.")
        
    # 2. Activity Heatmap
    st.markdown("##### 24-Hour Activity Heatmap")
    heatmap_data = get_hour_heatmap_data(filtered)
    if not heatmap_data.empty:
        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(x="Hour of Day", y="Day of Week", color="Hits"),
            color_continuous_scale="Viridis",
            aspect="auto"
        )
        fig_heat.update_layout(margin=dict(l=0, r=0, b=0, t=10), height=280)
        st.plotly_chart(fig_heat, use_container_width=True)
        
    # 3. Network Link Graph
    st.markdown("##### Target Network Graph")
    contact_intel = contact_intelligence_table(filtered)
    if not contact_intel.empty:
        top_contacts = contact_intel.head(15) # Optimized to top 15 for visual clarity
        target = phone_number if phone_number else "Primary Suspect"
        
        edge_x, edge_y = [], []
        node_x, node_y = [0], [0]
        node_text, node_size, node_color = [target], [35], ["#ef4444"] # Target is Red
        
        for i, row in enumerate(top_contacts.itertuples()):
            angle = (i / len(top_contacts)) * 2 * math.pi
            x, y = math.cos(angle), math.sin(angle)
            
            edge_x.extend([0, x, None])
            edge_y.extend([0, y, None])
            
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{row.other_party_number}<br>Calls: {row.calls}")
            node_size.append(15 + min(row.calls, 25))
            node_color.append("#3b82f6" if row.calls < 20 else "#a855f7") # Blue neutral, Purple high-link
            
        fig_graph = go.Figure()
        fig_graph.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#444'), hoverinfo='none', mode='lines'))
        fig_graph.add_trace(go.Scatter(
            x=node_x, y=node_y, mode='markers+text', text=node_text, textposition="top center", hoverinfo='text',
            marker=dict(size=node_size, color=node_color, line_width=2)
        ))
        
        fig_graph.update_layout(
            showlegend=False, margin=dict(l=0, r=0, b=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=350, plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_graph, use_container_width=True)

with threat_col:
    st.markdown("### 🚨 Threat Panel")
    threats = generate_threat_panel(filtered)
    
    for t in threats:
        # Determine CSS class based on level (Multi-link anomaly -> Multi-link)
        css_level = t['level'].split()[0] 
        st.markdown(f"""
        <div class="threat-card threat-{css_level}">
            <div class="threat-title">{t['title']}</div>
            <p class="threat-desc">{t['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("##### Common Scene Hits")
    tower_intel = tower_intelligence_panel(filtered)
    if not tower_intel.empty:
        st.dataframe(
            tower_intel[["tower_id", "hits", "suspicion"]].head(5),
            use_container_width=True,
            hide_index=True
        )

# ── BOTTOM: RAW RECORDS TABLE ──────────────────────────────────────────────
st.markdown("---")
with st.expander("📝 View Raw Records Database", expanded=False):
    st.dataframe(filtered, use_container_width=True)
    st.download_button(
        "📥 Export Forensic Evidence (CSV)",
        data=dataframe_to_csv_bytes(filtered),
        file_name="forensic_evidence_export.csv",
        mime="text/csv",
        use_container_width=True
    )

close_page_shell()
