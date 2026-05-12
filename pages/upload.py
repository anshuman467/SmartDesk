from pathlib import Path

import pandas as pd
import streamlit as st

from database.db import fetch_uploaded_files, insert_records
from services.auth import require_login
from services.normalizer import load_and_normalize, normalize_with_mapping
from services.sample_data import write_sample_files
from services.ui import apply_theme, close_page_shell, page_intro, render_navbar


BASE_DIR = Path(__file__).resolve().parent.parent
require_login()
apply_theme(True)
render_navbar(True)


def recommended_fields(file_type: str) -> list[str]:
    common = ["phone_number", "imei", "imsi", "date_time"]
    if file_type == "ipdr":
        return common + ["source_ip", "destination_ip", "destination_port", "domain", "service_provider"]
    if file_type == "cdr":
        return common + ["other_party_number", "call_type", "duration", "tower_id", "tower_location"]
    if file_type == "tower_dump":
        return common + ["tower_id", "tower_location", "mcc", "mnc", "lac", "cellid", "tac", "radio"]
    return common


page_intro(
    "Upload and Normalize",
    "Import one or many telecom documents, inspect the normalized structure, and save them into the investigation database.",
    eyebrow="Data Intake",
)

# ── Primary Actions ──
with st.container():
    col1, col2 = st.columns([0.6, 0.4], vertical_alignment="center")
    with col1:
        upload_mode = st.selectbox("Global File Type Override", ["auto", "cdr", "ipdr", "tower_dump"], help="Use 'auto' to let the system detect format per-file.")
    with col2:
        if st.button("Create Sample Data", use_container_width=True):
            write_sample_files(BASE_DIR / "data" / "sample")
            st.success("Samples created in `data/sample`.")

uploaded_files = st.file_uploader(
    "Upload multiple CSV or Excel files",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # ── Master Process Button ──
    if st.button("Process and Save All Uploaded Documents", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_inserted = 0
        results = []
        
        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {uploaded_file.name}...")
            try:
                raw_df, normalized_df, mapping, file_type = load_and_normalize(uploaded_file, upload_mode)
                inserted = insert_records(uploaded_file.name, file_type, normalized_df)
                total_inserted += inserted
                results.append(f"✅ {uploaded_file.name}: {inserted} records ({file_type.upper()})")
            except Exception as e:
                results.append(f"❌ {uploaded_file.name}: Failed ({str(e)})")
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        st.success(f"Finished! Total of {total_inserted} records ingested into the investigation workspace.")
        with st.expander("Detailed Ingestion Log"):
            st.write("\n".join(results))
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    st.subheader("File Previews")
    
    for uploaded_file in uploaded_files:
        with st.expander(f"Review {uploaded_file.name}"):
            try:
                raw_df, normalized_df, mapping, file_type = load_and_normalize(uploaded_file, upload_mode)
                
                st.write(f"Detected: **{file_type.upper()}**")
                
                tab1, tab2, tab3 = st.tabs(["Normalized Data", "Raw Data", "Schema Mapping"])
                with tab1:
                    st.dataframe(normalized_df.head(10), use_container_width=True)
                with tab2:
                    st.dataframe(raw_df.head(10), use_container_width=True)
                with tab3:
                    mapping_df = pd.DataFrame([{"standard_field": k, "raw_column": v} for k, v in mapping.items()])
                    st.dataframe(mapping_df, use_container_width=True)
                    
                    st.caption("Optional: Adjust mapping manually below if detection was imperfect.")
                    selected_mapping: dict[str, str] = {}
                    options = ["<skip>"] + list(raw_df.columns)
                    m_cols = st.columns(3)
                    fields = recommended_fields(file_type)
                    for i, field in enumerate(fields):
                        default_col = mapping.get(field, "<skip>")
                        def_idx = options.index(default_col) if default_col in options else 0
                        with m_cols[i % 3]:
                            chosen = st.selectbox(f"{field}", options=options, index=def_idx, key=f"m_{uploaded_file.name}_{field}")
                            if chosen != "<skip>":
                                selected_mapping[field] = chosen
                    
                    if st.button("Save with Custom Mapping", key=f"save_custom_{uploaded_file.name}"):
                        manual_df = normalize_with_mapping(raw_df, file_type, selected_mapping)
                        inserted = insert_records(uploaded_file.name, file_type, manual_df)
                        st.success(f"Saved {inserted} records with manual mapping.")
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")

st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
st.subheader("Database Inventory")
files_df = fetch_uploaded_files()
if files_df.empty:
    st.info("The investigation database is currently empty. Upload files above to begin analysis.")
else:
    st.dataframe(files_df, use_container_width=True)

close_page_shell()
