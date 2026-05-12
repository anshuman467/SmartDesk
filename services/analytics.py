import io
from typing import List

import pandas as pd


def filter_ipdr(
    df: pd.DataFrame,
    phone_number: str = "",
    destination_ip: str = "",
    destination_port: str = "",
    service_name: str = "",
) -> pd.DataFrame:
    filtered = df[df["file_type"] == "ipdr"].copy()

    if phone_number and "phone_number" in filtered.columns:
        filtered = filtered[filtered["phone_number"].astype(str).str.contains(phone_number, na=False)]
    if destination_ip and "destination_ip" in filtered.columns:
        filtered = filtered[filtered["destination_ip"].astype(str).str.contains(destination_ip, na=False)]
    if destination_port and "destination_port" in filtered.columns:
        filtered = filtered[filtered["destination_port"].astype(str).str.contains(destination_port, na=False)]
    if service_name and "service_name" in filtered.columns:
        filtered = filtered[filtered["service_name"].astype(str).str.contains(service_name, na=False)]

    return filtered.sort_values("date_time", ascending=False)


def top_counts(df: pd.DataFrame, column: str, limit: int = 10) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame(columns=[column, "count"])
    series = df[column].dropna()
    if series.empty:
        return pd.DataFrame(columns=[column, "count"])
    return series.value_counts().head(limit).rename_axis(column).reset_index(name="count")


def common_entity_table(df: pd.DataFrame, entity: str) -> pd.DataFrame:
    if entity not in df.columns:
        return pd.DataFrame(columns=[entity, "occurrences", "files"])

    repeated = (
        df.dropna(subset=[entity])
        .groupby(entity)
        .agg(
            occurrences=("id", "count"),
            files=("source_file", "nunique"),
        )
        .reset_index()
        .sort_values(["occurrences", "files"], ascending=False)
    )
    return repeated


def multi_number_imei(df: pd.DataFrame) -> pd.DataFrame:
    if not {"imei", "phone_number"}.issubset(df.columns):
        return pd.DataFrame(columns=["imei", "unique_numbers"])
    return (
        df.dropna(subset=["imei", "phone_number"])
        .groupby("imei")["phone_number"]
        .nunique()
        .reset_index(name="unique_numbers")
        .query("unique_numbers > 1")
        .sort_values("unique_numbers", ascending=False)
    )


def common_destination_ip(df: pd.DataFrame) -> pd.DataFrame:
    if not {"destination_ip", "phone_number"}.issubset(df.columns):
        return pd.DataFrame(columns=["destination_ip", "unique_numbers"])
    return (
        df[df["file_type"] == "ipdr"]
        .dropna(subset=["destination_ip", "phone_number"])
        .groupby("destination_ip")["phone_number"]
        .nunique()
        .reset_index(name="unique_numbers")
        .sort_values("unique_numbers", ascending=False)
    )


def common_numbers_across_files(df: pd.DataFrame, file_names: List[str]) -> pd.DataFrame:
    subsets = []
    for file_name in file_names:
        file_df = df[(df["file_type"] == "tower_dump") & (df["source_file"] == file_name)]
        numbers = set(file_df["phone_number"].dropna().astype(str))
        if numbers:
            subsets.append(numbers)

    if not subsets:
        return pd.DataFrame(columns=["phone_number"])

    common_numbers = sorted(set.intersection(*subsets)) if len(subsets) > 1 else sorted(subsets[0])
    return pd.DataFrame({"phone_number": common_numbers})


def filter_cdr(
    df: pd.DataFrame,
    phone_number: str = "",
    other_party_number: str = "",
    tower_id: List[str] = None,
    call_type: List[str] = None,
    date_range: tuple = None,
    time_range: tuple = None,
    min_duration: int = 0,
) -> pd.DataFrame:
    filtered = df[df["file_type"] == "cdr"].copy()
    
    if phone_number and "phone_number" in filtered.columns:
        filtered = filtered[filtered["phone_number"].astype(str).str.contains(phone_number, na=False)]
    if other_party_number and "other_party_number" in filtered.columns:
        filtered = filtered[filtered["other_party_number"].astype(str).str.contains(other_party_number, na=False)]
    if tower_id and "tower_id" in filtered.columns:
        filtered = filtered[filtered["tower_id"].isin(tower_id)]
    if call_type and "call_type" in filtered.columns:
        filtered = filtered[filtered["call_type"].isin(call_type)]
        
    if date_range and "date_time" in filtered.columns:
        start_date, end_date = date_range
        filtered = filtered[(filtered["date_time"].dt.date >= start_date) & (filtered["date_time"].dt.date <= end_date)]
        
    if time_range and "date_time" in filtered.columns:
        start_t, end_t = time_range
        filtered = filtered[filtered["date_time"].dt.time.between(start_t, end_t)]
        
    if min_duration > 0 and "duration" in filtered.columns:
        filtered = filtered[filtered["duration"] >= min_duration]
        
    return filtered.sort_values("date_time", ascending=False)


def tower_intelligence_panel(df: pd.DataFrame) -> pd.DataFrame:
    if "tower_id" not in df.columns:
        return pd.DataFrame()
        
    def get_night_pct(group):
        hours = group.dt.hour
        night_calls = ((hours >= 22) | (hours <= 5)).sum()
        return round((night_calls / len(group)) * 100, 1) if not group.empty else 0

    panel = (
        df.groupby("tower_id")
        .agg(
            hits=("id", "count"),
            first_seen=("date_time", "min"),
            last_seen=("date_time", "max"),
            night_pct=("date_time", get_night_pct),
            avg_radius=("approx_radius_meters", "mean"),
        )
        .reset_index()
    )
    
    # Simple suspicion heuristic: High night usage or sudden appearance
    panel["suspicion"] = "Normal"
    panel.loc[panel["night_pct"] > 60, "suspicion"] = "Elevated (Night)"
    panel.loc[panel["hits"] > panel["hits"].mean() * 2, "suspicion"] = "High (Frequency)"
    
    return panel.sort_values("hits", ascending=False)


def communication_behavior_matrix(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
        
    avg_dur = df["duration"].mean() if "duration" in df.columns and not df["duration"].dropna().empty else 0
    
    stats = {
        "total_calls": len(df),
        "in_out_ratio": 0,
        "avg_duration": round(avg_dur, 1),
        "short_calls": (df["duration"] < 15).sum() if "duration" in df.columns else 0,
        "night_calls": ((df["date_time"].dt.hour >= 22) | (df["date_time"].dt.hour <= 5)).sum(),
        "missed_calls": (df["call_type"].str.contains("missed", case=False, na=False)).sum() if "call_type" in df.columns else 0,
    }
    
    if "call_type" in df.columns:
        inc = df["call_type"].str.contains("incoming", case=False, na=False).sum()
        out = df["call_type"].str.contains("outgoing", case=False, na=False).sum()
        stats["in_out_ratio"] = round(inc / out, 2) if out > 0 else inc
        
    return stats


def contact_intelligence_table(df: pd.DataFrame) -> pd.DataFrame:
    if not {"phone_number", "other_party_number"}.issubset(df.columns):
        return pd.DataFrame()
        
    def get_reciprocity(group):
        inc = group["call_type"].str.contains("incoming", case=False, na=False).sum()
        out = group["call_type"].str.contains("outgoing", case=False, na=False).sum()
        return f"{inc}↑ / {out}↓"

    intel = (
        df.groupby("other_party_number")
        .agg(
            calls=("id", "count"),
            total_duration=("duration", "sum"),
            first_seen=("date_time", "min"),
            last_seen=("date_time", "max"),
            towers_shared=("tower_id", "nunique"),
        )
        .reset_index()
    )
    
    # Add reciprocity separately to avoid grouping issues with call_type logic
    recip_map = df.groupby("other_party_number").apply(get_reciprocity).to_dict()
    intel["reciprocity"] = intel["other_party_number"].map(recip_map)
    
    intel["risk"] = "Low"
    intel.loc[intel["calls"] > 20, "risk"] = "Medium"
    intel.loc[(intel["calls"] > 50) & (intel["total_duration"] < 300), "risk"] = "High (Burst)"
    
    return intel.sort_values("calls", ascending=False)


def get_hour_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["hour"] = df["date_time"].dt.hour
    df["day"] = df["date_time"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap = df.groupby(["day", "hour"]).size().unstack(fill_value=0).reindex(order)
    return heatmap

def route_timeline(df: pd.DataFrame, phone_number: str) -> pd.DataFrame:
    needed = [
        "date_time",
        "tower_id",
        "tower_location",
        "tower_latitude",
        "tower_longitude",
        "mcc",
        "mnc",
        "lac",
        "cellid",
        "tac",
        "radio",
        "approx_radius_meters",
        "source_file",
    ]
    available = [col for col in needed if col in df.columns]
    route_df = (
        df[(df["file_type"] == "tower_dump") & (df["phone_number"].astype(str) == str(phone_number))]
        .sort_values("date_time")
        [available]
    )
    return route_df


def generate_suspect_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"total_calls": 0, "unique_contacts": 0, "top_tower": "N/A", "imei_count": 0, "active_days": 0, "risk_score": 0}
    
    unique_contacts = df["other_party_number"].nunique() if "other_party_number" in df.columns else 0
    top_tower = df["tower_id"].value_counts().idxmax() if "tower_id" in df.columns and not df["tower_id"].dropna().empty else "N/A"
    imei_count = df["imei"].nunique() if "imei" in df.columns else 0
    active_days = df["date_time"].dt.date.nunique() if "date_time" in df.columns else 0
    
    # Calculate Risk Score (0-100)
    risk_score = 10
    if imei_count > 1: risk_score += 30
    if "duration" in df.columns:
        short_calls = (df["duration"] < 15).sum()
        if short_calls > 10: risk_score += 20
    if "date_time" in df.columns:
        night_calls = ((df["date_time"].dt.hour >= 23) | (df["date_time"].dt.hour <= 4)).sum()
        if night_calls > 5: risk_score += 20
    if unique_contacts > 50: risk_score += 10
    risk_score = min(risk_score, 100)
    
    return {
        "total_calls": len(df),
        "unique_contacts": unique_contacts,
        "top_tower": top_tower,
        "imei_count": imei_count,
        "active_days": active_days,
        "risk_score": risk_score
    }


def generate_threat_panel(df: pd.DataFrame) -> list:
    threats = []
    if df.empty:
        return threats
        
    # 1. Device Anomalies
    if "imei" in df.columns:
        imei_count = df["imei"].nunique()
        if imei_count > 1:
            threats.append({
                "level": "Critical",
                "title": "Device Anomaly",
                "desc": f"Suspect used {imei_count} different IMEI numbers (Burner behavior)."
            })
            
    # 2. Night Bursts
    if "date_time" in df.columns:
        night_calls = ((df["date_time"].dt.hour >= 23) | (df["date_time"].dt.hour <= 4)).sum()
        if night_calls > 10:
            threats.append({
                "level": "Suspicious",
                "title": "Night Operations",
                "desc": f"{night_calls} activities detected between 11PM and 4AM."
            })
            
    # 3. Short Calls (Burner behavior)
    if "duration" in df.columns:
        short_calls = (df["duration"] < 15).sum()
        if short_calls > 20:
            threats.append({
                "level": "Suspicious",
                "title": "Short Burst Communication",
                "desc": f"{short_calls} calls lasted less than 15 seconds."
            })
            
    # 4. Multi-link anomaly (Cross-scene or high frequency)
    if "other_party_number" in df.columns:
        top_contact_freq = df["other_party_number"].value_counts().max()
        if top_contact_freq > 50:
            threats.append({
                "level": "Multi-link anomaly",
                "title": "High-Frequency Target",
                "desc": f"Single contact interacted {top_contact_freq} times."
            })
            
    if not threats:
        threats.append({
            "level": "Neutral",
            "title": "Normal Activity",
            "desc": "No significant behavioral red flags detected."
        })
        
    return threats


def build_behavioral_timeline(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "date_time" not in df.columns:
        return pd.DataFrame()
        
    timeline = df.copy()
    timeline["date"] = timeline["date_time"].dt.date
    daily_stats = timeline.groupby("date").agg(
        total_events=("id", "count"),
        total_duration=("duration", "sum") if "duration" in timeline.columns else ("id", "count")
    ).reset_index()
    return daily_stats


# ── IPDR DIGITAL INTELLIGENCE LAYER ───────────────────────────────────────

def classify_ip_service(ip: str) -> dict:
    """Mock heuristic IP intelligence engine."""
    if not ip or not isinstance(ip, str):
        return {"org": "Unknown", "service": "Unknown", "category": "General", "risk": "Low"}
        
    # Heuristic mapping for common investigation targets
    heuristics = [
        ("157.240.", "Meta / WhatsApp", "Social Media", "Low"),
        ("31.13.", "Meta / Facebook", "Social Media", "Low"),
        ("149.154.", "Telegram Messenger", "Messaging", "Medium"),
        ("91.108.", "Telegram Messenger", "Messaging", "Medium"),
        ("104.16.", "Cloudflare / CDN", "Web Services", "Low"),
        ("104.18.", "Cloudflare / CDN", "Web Services", "Low"),
        ("185.129.", "VPN / Proxy Infra", "VPN", "High"),
        ("204.8.", "Tor Exit Node", "Dark Web", "Critical"),
        ("52.223.", "Amazon / AWS", "Cloud Hosting", "Low"),
        ("142.250.", "Google / YouTube", "Social/Search", "Low"),
    ]
    
    for prefix, org, cat, risk in heuristics:
        if ip.startswith(prefix):
            return {"org": org, "service": org, "category": cat, "risk": risk}
            
    return {"org": "Public Network", "service": "Generic Web", "category": "General", "risk": "Low"}


def classify_port_behavior(port: any) -> dict:
    """Categorizes network ports into behavioral groups."""
    try:
        p = int(port)
    except:
        return {"app": "Unknown", "category": "Unknown", "risk": "Low"}
        
    port_map = {
        443: {"app": "HTTPS / Encrypted", "category": "Secure Web", "risk": "Low"},
        80: {"app": "HTTP / Cleartext", "category": "Web", "risk": "Medium"},
        1194: {"app": "OpenVPN", "category": "VPN", "risk": "High"},
        5060: {"app": "SIP / VoIP", "category": "Communication", "risk": "Low"},
        9050: {"app": "Tor Proxy", "category": "Dark Web", "risk": "Critical"},
        1723: {"app": "PPTP VPN", "category": "VPN", "risk": "High"},
        5222: {"app": "XMPP / Jabber", "category": "Messaging", "risk": "Medium"},
        3389: {"app": "RDP", "category": "Remote Desktop", "risk": "Medium"},
    }
    
    return port_map.get(p, {"app": f"Port {p}", "category": "Custom App", "risk": "Low"})


def generate_ipdr_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"total": 0, "unique_ips": 0, "vpn_hits": 0, "msg_pct": 0, "risk_score": 0}
        
    df = df.copy()
    # Enrich data for analysis
    df["port_info"] = df["destination_port"].apply(classify_port_behavior)
    df["port_cat"] = df["port_info"].apply(lambda x: x["category"])
    
    total = len(df)
    unique_ips = df["destination_ip"].nunique() if "destination_ip" in df.columns else 0
    vpn_hits = df[df["port_cat"] == "VPN"].shape[0]
    
    msg_hits = df[df["port_cat"].isin(["Messaging", "Communication"])].shape[0]
    msg_pct = round((msg_hits / total) * 100, 1) if total > 0 else 0
    
    # Simple risk scoring logic
    risk_score = 15
    if vpn_hits > 0: risk_score += 35
    if df[df["port_cat"] == "Dark Web"].shape[0] > 0: risk_score += 45
    if total > 5000: risk_score += 5
    
    return {
        "total": total,
        "unique_ips": unique_ips,
        "vpn_hits": vpn_hits,
        "msg_pct": msg_pct,
        "risk_score": min(risk_score, 100)
    }


def generate_ipdr_threats(df: pd.DataFrame) -> list:
    threats = []
    if df.empty: return threats
    
    df = df.copy()
    df["port_info"] = df["destination_port"].apply(classify_port_behavior)
    df["port_cat"] = df["port_info"].apply(lambda x: x["category"])
    
    # 1. VPN Detection
    vpn_df = df[df["port_cat"] == "VPN"]
    if not vpn_df.empty:
        threats.append({
            "level": "Critical",
            "title": "VPN Tunnel Detected",
            "desc": f"Suspect established {len(vpn_df)} encrypted tunnels, potentially masking activity."
        })
        
    # 2. Midnight Internet Activity
    if "date_time" in df.columns:
        night_hits = ((df["date_time"].dt.hour >= 0) & (df["date_time"].dt.hour <= 4)).sum()
        if night_hits > 100:
            threats.append({
                "level": "Suspicious",
                "title": "Dark-Hour Browsing",
                "desc": f"Intense activity ({night_hits} sessions) detected during midnight hours."
            })
            
    # 3. Messaging Anomalies
    msg_hits = df[df["port_cat"] == "Messaging"].shape[0]
    if msg_hits > 500:
        threats.append({
            "level": "Suspicious",
            "title": "Messaging Spike",
            "desc": "Abnormal volume of encrypted messaging signaling detected."
        })
        
    if not threats:
        threats.append({"level": "Neutral", "title": "Normal Traffic", "desc": "No digital behavioral anomalies found."})
        
    return threats


def get_ipdr_sankey_data(df: pd.DataFrame, target: str) -> dict:
    if df.empty: return {"nodes": [], "links": []}
    
    # Simplified: Top 1 paths Target -> App Category -> Org
    df = df.copy()
    df["port_info"] = df["destination_port"].apply(classify_port_behavior)
    df["cat"] = df["port_info"].apply(lambda x: x["category"])
    df["ip_info"] = df["destination_ip"].apply(classify_ip_service)
    df["org"] = df["ip_info"].apply(lambda x: x["org"])
    
    # Paths: Target -> Category, Category -> Org
    p1 = df.groupby(["cat"]).size().reset_index(name="value")
    p2 = df.groupby(["cat", "org"]).size().reset_index(name="value")
    
    target_node = target if target else "Suspect"
    nodes = [target_node] + list(df["cat"].unique()) + list(df["org"].unique())
    node_map = {name: i for i, name in enumerate(nodes)}
    
    links = []
    # Link 1: Target -> Category
    for _, row in p1.iterrows():
        links.append({"source": node_map[target_node], "target": node_map[row["cat"]], "value": int(row["value"])})
    # Link 2: Category -> Org
    for _, row in p2.iterrows():
        links.append({"source": node_map[row["cat"]], "target": node_map[row["org"]], "value": int(row["value"])})
        
    return {"nodes": nodes, "links": links}


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    import io
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")
