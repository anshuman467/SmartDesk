import streamlit as st

from database.db import fetch_records
from services.auth import require_login
from services.analytics import common_entity_table, dataframe_to_csv_bytes, multi_number_imei
from services.ui import apply_theme, close_page_shell, page_intro, render_navbar

require_login()
apply_theme(True)
render_navbar(True)

page_intro(
    "Cross Link Analysis",
    "Correlate repeated numbers, IMEI, IMSI, destination IPs, and tower IDs across all uploaded records.",
    eyebrow="Entity Correlation",
)

records = fetch_records()
if records.empty:
    st.warning("No investigation records are available yet.")
    st.stop()

entity = st.selectbox(
    "Analyse repeated entity",
    ["phone_number", "imei", "imsi", "destination_ip", "tower_id"],
)
search_value = st.text_input(f"Search {entity}")

working = records.copy()
if search_value and entity in working.columns:
    working = working[working[entity].astype(str).str.contains(search_value, na=False)]

st.subheader("Matching Records")
st.dataframe(working, use_container_width=True)

st.subheader("Most Repeated Entities")
repeated = common_entity_table(records, entity)
st.dataframe(repeated, use_container_width=True)
st.download_button(
    "Download Entity Summary",
    data=dataframe_to_csv_bytes(repeated),
    file_name=f"{entity}_summary.csv",
    mime="text/csv",
)

st.subheader("Device Sharing Alerts")
imei_alerts = multi_number_imei(records)
if imei_alerts.empty:
    st.info("No IMEI is currently linked to multiple numbers.")
else:
    st.dataframe(imei_alerts, use_container_width=True)
close_page_shell()
