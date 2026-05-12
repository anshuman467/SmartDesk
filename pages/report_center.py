import streamlit as st
import pandas as pd

from database.db import fetch_uploaded_files, get_case_summary, fetch_records
from services.auth import require_login
from services.reporting import generate_forensic_hit_report, generate_html_report
from services.ui import apply_theme, close_page_shell, page_intro, render_navbar

require_login()
apply_theme(True)
render_navbar(True)

page_intro(
    "Report Center",
    "Generate a professional, multi-page Forensic Hit Report detailing suspect communication, movement, device intelligence, and chain of custody.",
    eyebrow="Intelligence Reporting",
)

summary = get_case_summary()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Files Uploaded", summary["files"])
col2.metric("Total Records", summary["records"])
col3.metric("Unique Numbers", summary["unique_numbers"])
col4.metric("Unique Towers", summary["unique_towers"])

st.markdown("---")
st.subheader("🎯 Target Selection for Report")

# Fetch and filter for 'Suspicious' targets only (numbers with significant activity)
records = fetch_records()
if not records.empty:
    # We count records per phone number and only keep those with > 5 hits
    # This filters out the 'noise' from tower dumps and one-off calls
    counts = records["phone_number"].value_counts()
    suspicious_numbers = counts[counts > 5].index.astype(str).tolist()
    all_numbers = sorted(suspicious_numbers)
else:
    all_numbers = []

if not all_numbers:
    if records.empty:
        st.warning("No records found in the database. Please upload data first.")
    else:
        st.info("No 'High-Activity' suspects found yet. Showing all numbers as a fallback.")
        all_numbers = sorted(list(set(records["phone_number"].dropna().astype(str).unique())))
    
if not all_numbers:
    st.stop()

selected_target = st.selectbox("Select Primary Suspect / Target Number", options=all_numbers)

st.markdown("---")

report_pages = generate_forensic_hit_report(selected_target)

# Create the full text for download by joining pages with page-break tags
report_full_text = ""
for title, content in report_pages:
    report_full_text += f"{content}\n\n<div style='page-break-after: always;'></div>\n\n"

col_preview, col_export = st.columns([3, 1])

with col_preview:
    st.subheader("📄 Report Preview")
    # Use tabs for a cleaner "Investigator Grade" experience
    tab_titles = [p[0] for p in report_pages]
    tabs = st.tabs(tab_titles)
    
    for i, tab in enumerate(tabs):
        with tab:
            with st.container(height=500, border=True):
                st.markdown(report_pages[i][1], unsafe_allow_html=True)

with col_export:
    st.subheader("💾 Export Options")
    st.info("Choose your preferred format for the forensic hit report.")
    
    # 1. Markdown Export
    st.download_button(
        "📥 Download as Markdown (.md)",
        data=report_full_text.encode("utf-8"),
        file_name=f"forensic_report_{selected_target}.md",
        mime="text/markdown",
        use_container_width=True
    )
    
    # 2. HTML Export (Professional Design)
    html_report = generate_html_report(report_pages, selected_target)
    st.download_button(
        "🌐 Download as HTML (.html)",
        data=html_report.encode("utf-8"),
        file_name=f"forensic_report_{selected_target}.html",
        mime="text/html",
        type="primary",
        use_container_width=True
    )
    
close_page_shell()
