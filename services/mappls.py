import json
import os
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def get_mappls_token() -> str:
    secret_key = ""
    try:
        secret_key = st.secrets.get("MAPPLS_ACCESS_TOKEN", "")
    except Exception:
        secret_key = ""
    return secret_key or os.getenv("MAPPLS_ACCESS_TOKEN", "")


def render_mappls_route_map(route_df: pd.DataFrame, access_token: str, height: int = 760) -> None:
    if route_df.empty:
        st.info("No mapped route points available.")
        return

    safe_df = route_df.copy()
    safe_df["tower_location"] = safe_df.get("tower_location", "").fillna("Approximate tower/cell area")
    safe_df["incident_note"] = safe_df.get("incident_note", "").fillna("Approximate area")

    route_points: list[dict[str, Any]] = []
    for _, row in safe_df.iterrows():
        route_points.append(
            {
                "lat": float(row["tower_latitude"]),
                "lng": float(row["tower_longitude"]),
                "tower_id": str(row.get("tower_id", "")),
                "tower_location": str(row.get("tower_location", "")),
                "date_time": str(row.get("date_time", "")),
                "radius": int(float(row.get("approx_radius_meters", 500))),
                "incident_note": str(row.get("incident_note", "")),
            }
        )

    center_lat = float(safe_df["tower_latitude"].mean())
    center_lng = float(safe_df["tower_longitude"].mean())
    points_json = json.dumps(route_points)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
      <style>
        html, body, #map {{
          margin: 0;
          padding: 0;
          width: 100%;
          height: {height}px;
          border-radius: 20px;
          overflow: hidden;
        }}
        .map-note {{
          position: absolute;
          left: 14px;
          bottom: 14px;
          z-index: 999;
          background: rgba(255,255,255,0.94);
          padding: 10px 12px;
          border-radius: 14px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.10);
          font-family: Arial, sans-serif;
          font-size: 12px;
          color: #23324d;
          max-width: 260px;
          line-height: 1.45;
        }}
      </style>
    </head>
    <body>
      <div id="map"></div>
      <div class="map-note">
        OpenCelliD coordinates are approximate cell/cell-coverage estimates. Circles indicate the probable incident area, not a guaranteed exact tower structure.
      </div>
      <script>
        const routePoints = {points_json};
        const map = L.map('map').setView([{center_lat}, {center_lng}], 12);
        L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
            attribution: '&copy; Google Maps'
        }}).addTo(map);

        const latlngs = [];
        routePoints.forEach(function(point) {{
            L.circle([point.lat, point.lng], {{
                color: '#274690',
                fillColor: '#4ea5d9',
                fillOpacity: 0.20,
                radius: point.radius,
                weight: 2
            }}).addTo(map);
            L.circle([point.lat, point.lng], {{
                color: '#1d3557',
                fillColor: '#274690',
                fillOpacity: 0.85,
                radius: 40,
                weight: 2
            }}).addTo(map).bindPopup("<b>" + point.tower_id + "</b><br>" + point.tower_location);
            latlngs.push([point.lat, point.lng]);
        }});

        if (latlngs.length > 1) {{
            const polyline = L.polyline(latlngs, {{color: '#1d3557', weight: 4}}).addTo(map);
            map.fitBounds(polyline.getBounds(), {{padding: [80, 80]}});
        }}
      </script>
    </body>
    </html>
    """

    components.html(html, height=height, scrolling=False)
