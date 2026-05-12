import pydeck as pdk
import streamlit as st

from database.db import fetch_records
from services.auth import require_login
from services.analytics import common_numbers_across_files, dataframe_to_csv_bytes, route_timeline
from services.mappls import get_mappls_token, render_mappls_route_map
from services.opencellid import enrich_route_with_opencellid, get_api_key
from services.ui import apply_theme, close_page_shell, page_intro, render_navbar

require_login()
apply_theme(True)
render_navbar(True)

page_intro(
    "Tower Dump & Map View",
    "Find common numbers across locations and reconstruct suspect movement from tower dump overlaps visually.",
    eyebrow="Location Overlap & Routing",
)

records = fetch_records("file_type = ?", ("tower_dump",))
if records.empty:
    st.warning("No tower dump data is available.")
    st.stop()

tab_data, tab_map = st.tabs(["📊 Data Analysis", "🗺️ Geospatial Map View"])

with tab_data:
    st.markdown("### Common Entity Identification")
    file_names = sorted(records["source_file"].dropna().unique().tolist())
    selected_files = st.multiselect(
        "Select tower dump files",
        options=file_names,
        default=file_names[: min(3, len(file_names))],
    )

    common_numbers = common_numbers_across_files(records, selected_files)

    col1, col2 = st.columns(2)
    col1.metric("Selected Files", len(selected_files))
    col2.metric("Common Numbers", len(common_numbers))

    st.subheader("Common Numbers Across Selected Dumps")
    st.dataframe(common_numbers, use_container_width=True)
    st.download_button(
        "Download Common Numbers",
        data=dataframe_to_csv_bytes(common_numbers),
        file_name="common_numbers.csv",
        mime="text/csv",
    )

    if not common_numbers.empty:
        suspect = st.selectbox("Inspect route for number", common_numbers["phone_number"].tolist())
        st.subheader("Movement Timeline")
        st.dataframe(route_timeline(records, suspect), use_container_width=True)


with tab_map:
    st.markdown("### Geospatial Routing")
    numbers = sorted(records["phone_number"].dropna().astype(str).unique().tolist())
    number_summary = (
        records[records["phone_number"].notna()]
        .groupby("phone_number")
        .agg(
            total_events=("id", "count"),
            mapped_points=("tower_latitude", lambda s: int(s.notna().sum())),
        )
        .reset_index()
        .sort_values(["mapped_points", "total_events"], ascending=False)
    )

    default_number = numbers[0] if numbers else ""
    if not number_summary.empty:
        default_number = str(number_summary.iloc[0]["phone_number"])

    selected_number = st.selectbox(
        "Select suspect number for routing",
        numbers,
        index=numbers.index(default_number) if default_number in numbers else 0,
    )

    m_col1, m_col2 = st.columns([1.2, 1])
    with m_col1:
        radius_override = st.slider("Default approximate area radius (meters)", min_value=100, max_value=3000, value=600, step=100)
    with m_col2:
        use_opencellid = st.toggle("Use OpenCelliD lookup for missing coordinates", value=True)

    mappls_token = get_mappls_token()
    use_mappls = st.toggle("Use Mappls map renderer", value=True, disabled=not bool(mappls_token))
    if not mappls_token:
        st.info("Mappls renderer is unavailable because `MAPPLS_ACCESS_TOKEN` is not configured. PyDeck will be used.")

    api_key = get_api_key()
    if use_opencellid and not api_key:
        st.info("OpenCelliD lookup is enabled, but no API key is configured. Using locally known coordinates.")

    route_df = route_timeline(records, selected_number)
    if use_opencellid and api_key:
        route_df = enrich_route_with_opencellid(route_df, api_key)

    status_col1, status_col2, status_col3 = st.columns(3)
    status_col1.metric("Mappls Token", "Configured" if mappls_token else "Missing")
    status_col2.metric("OpenCelliD Key", "Configured" if api_key else "Missing")
    status_col3.metric("Selected Events", len(route_df))

    route_df = route_df.dropna(subset=["tower_latitude", "tower_longitude"])

    if not number_summary.empty:
        with st.expander("Available numbers and mapped point counts", expanded=False):
            st.dataframe(number_summary, use_container_width=True)

    if route_df.empty:
        st.info("No mapped tower coordinates are available for the selected number.")
    else:
        if "approx_radius_meters" not in route_df.columns:
            route_df["approx_radius_meters"] = radius_override
        route_df["approx_radius_meters"] = route_df["approx_radius_meters"].fillna(radius_override)
        route_df["incident_note"] = route_df["approx_radius_meters"].astype(int).astype(str) + " m approximate scene radius"

        st.subheader("Tower Route Table")
        st.dataframe(route_df, use_container_width=True)

        if use_mappls and mappls_token:
            st.subheader("Mappls Incident Area View")
            render_mappls_route_map(route_df, mappls_token)
            st.caption("Mappls renders the base map. OpenCelliD provides approximate cell coordinates.")
        else:
            area_layer = pdk.Layer(
                "ScatterplotLayer",
                data=route_df,
                get_position="[tower_longitude, tower_latitude]",
                get_color="[78, 165, 217, 55]",
                get_radius="approx_radius_meters",
                stroked=True,
                filled=True,
                line_width_min_pixels=1,
                line_width_max_pixels=2,
                get_line_color="[39, 70, 144, 110]",
                pickable=True,
            )

            tower_layer = pdk.Layer(
                "ScatterplotLayer",
                data=route_df,
                get_position="[tower_longitude, tower_latitude]",
                get_color="[39, 70, 144, 185]",
                get_radius=110,
                pickable=True,
            )

            line_data = route_df[["tower_longitude", "tower_latitude"]].values.tolist()
            path_layer = pdk.Layer(
                "PathLayer",
                data=[{"path": line_data}],
                get_path="path",
                get_color="[0, 120, 255]",
                width_scale=20,
                width_min_pixels=3,
            )

            view_state = pdk.ViewState(
                latitude=float(route_df["tower_latitude"].mean()),
                longitude=float(route_df["tower_longitude"].mean()),
                zoom=10,
                pitch=0,
            )

            st.pydeck_chart(
                pdk.Deck(
                    map_provider="carto",
                    map_style="dark",
                    layers=[area_layer, tower_layer, path_layer],
                    initial_view_state=view_state,
                    tooltip={"text": "{tower_id}\n{tower_location}\n{date_time}\n{incident_note}"},
                )
            )

            st.caption("OpenCelliD coordinates are approximate estimates. Radius overlay is an approximate incident area.")

close_page_shell()
