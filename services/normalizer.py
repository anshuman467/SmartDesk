from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from core.schema import PORT_LOOKUP, STANDARD_FIELDS, TOWER_COORDINATES


def clean_column_name(name: str) -> str:
    return (
        str(name)
        .strip()
        .lower()
        .replace("-", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )


def detect_file_type(df: pd.DataFrame) -> str:
    cols = {clean_column_name(col) for col in df.columns}
    has_ip = any("ip" in col for col in cols)
    has_port = any("port" in col for col in cols)
    has_tower = any(token in col for col in cols for token in ["tower", "cell", "site"])
    has_call = any(token in col for col in cols for token in ["call", "duration", "callee"])

    if has_ip or has_port:
        return "ipdr"
    if has_tower and not has_call:
        return "tower_dump"
    if has_call:
        return "cdr"
    return "unknown"


def guess_standard_mapping(columns) -> Dict[str, str]:
    cleaned_to_raw = {clean_column_name(col): col for col in columns}
    mapping: Dict[str, str] = {}

    for standard_field, aliases in STANDARD_FIELDS.items():
        for cleaned_col, raw_col in cleaned_to_raw.items():
            if cleaned_col == standard_field or cleaned_col in aliases:
                mapping[standard_field] = raw_col
                break

    if "date_time" not in mapping and {"date", "time"}.issubset(mapping):
        mapping["date_time"] = "__combine_date_time__"

    return mapping


def read_uploaded_table(uploaded_file) -> pd.DataFrame:
    uploaded_file.seek(0)
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Only CSV and Excel files are supported.")


def _apply_tower_enrichment(normalized: pd.DataFrame) -> pd.DataFrame:
    # Ensure columns exist
    if "tower_latitude" not in normalized.columns:
        normalized["tower_latitude"] = pd.Series(index=normalized.index, dtype="float64")
    if "tower_longitude" not in normalized.columns:
        normalized["tower_longitude"] = pd.Series(index=normalized.index, dtype="float64")
    if "tower_location" not in normalized.columns:
        normalized["tower_location"] = pd.Series(index=normalized.index, dtype=object)

    if "tower_id" not in normalized.columns:
        return normalized

    normalized["tower_id"] = normalized["tower_id"].astype(str).str.strip().str.upper()

    for idx, row in normalized.iterrows():
        t_id = str(row["tower_id"])
        # If coordinates are missing and tower_id is known, enrich them
        if (pd.isna(row["tower_latitude"]) or pd.isna(row["tower_longitude"])) and t_id in TOWER_COORDINATES:
            default_loc, lat, lon = TOWER_COORDINATES[t_id]
            normalized.at[idx, "tower_latitude"] = lat
            normalized.at[idx, "tower_longitude"] = lon
            if pd.isna(row["tower_location"]) or not str(row["tower_location"]).strip():
                normalized.at[idx, "tower_location"] = default_loc

    return normalized


def normalize_dataframe(df: pd.DataFrame, file_type: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    df = df.copy()
    mapping = guess_standard_mapping(list(df.columns))
    return normalize_with_mapping(df, file_type, mapping), mapping


def normalize_with_mapping(df: pd.DataFrame, file_type: str, mapping: Dict[str, str]) -> pd.DataFrame:
    df = df.copy()
    normalized = pd.DataFrame(index=df.index)

    for standard_field, raw_column in mapping.items():
        if raw_column == "__combine_date_time__":
            normalized[standard_field] = (
                df[mapping["date"]].astype(str).str.strip() + " " + df[mapping["time"]].astype(str).str.strip()
            )
        elif raw_column in df.columns:
            normalized[standard_field] = df[raw_column]

    if "date_time" in normalized.columns:
        normalized["date_time"] = pd.to_datetime(normalized["date_time"], errors="coerce")

    for col in ["phone_number", "other_party_number", "imei", "imsi", "tower_id"]:
        if col in normalized.columns:
            normalized[col] = normalized[col].astype(str).str.strip()
            normalized[col] = normalized[col].replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})

    for col in ["source_port", "destination_port", "bytes_used", "duration", "mcc", "mnc", "lac", "cellid", "tac", "approx_radius_meters", "tower_latitude", "tower_longitude"]:
        if col in normalized.columns:
            normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

    for col in ["source_ip", "destination_ip", "domain", "service_provider", "tower_location", "protocol", "call_type", "radio"]:
        if col in normalized.columns:
            normalized[col] = normalized[col].astype(str).str.strip()
            normalized[col] = normalized[col].replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})

    normalized["file_type"] = file_type
    if "destination_port" in normalized.columns:
        normalized["service_name"] = normalized["destination_port"].map(PORT_LOOKUP)

    normalized = _apply_tower_enrichment(normalized)
    return normalized


def load_and_normalize(uploaded_file, manual_type: str) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, str], str]:
    raw_df = read_uploaded_table(uploaded_file)
    file_type = detect_file_type(raw_df) if manual_type == "auto" else manual_type
    normalized_df, mapping = normalize_dataframe(raw_df, file_type)
    return raw_df, normalized_df, mapping, file_type
