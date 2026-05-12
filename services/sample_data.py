from pathlib import Path
import random
from datetime import datetime, timedelta

import pandas as pd

from database.db import fetch_uploaded_files, insert_records
from services.normalizer import normalize_dataframe

def ensure_sample_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

# THE PRESENTATION SCENARIO
SUSPECT_1 = {"phone": "9810000001", "ip": "10.0.0.101", "imei": "359881000000001", "imsi": "404450000000001"}
SUSPECT_2 = {"phone": "9810000002", "ip": "10.0.0.102", "imei": "359881000000002", "imsi": "404450000000002"}
SUSPICIOUS_SERVER_IP = "185.199.108.153"

def _random_phone() -> str:
    return f"981{random.randint(1000000, 9999999)}"

def _random_imei() -> str:
    return f"359881{random.randint(100000000, 999999999)}"

def _random_imsi() -> str:
    return f"404450{random.randint(100000000, 999999999)}"

def _build_ipdr_sample() -> pd.DataFrame:
    records = []
    base_time = datetime(2026, 4, 20, 8, 0, 0)
    
    # 1. Background noise records
    for _ in range(40):
        records.append([
            _random_phone(),
            f"10.0.0.{random.randint(10, 250)}",
            f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            random.choice([80, 443, 8080]),
            "TCP",
            random.choice(["google.com", "whatsapp.com", "instagram.com", "youtube.com"]),
            "RandomISP",
            (base_time + timedelta(minutes=random.randint(1, 300))).strftime("%Y-%m-%d %H:%M:%S"),
            random.randint(1000, 50000),
            _random_imei(),
            _random_imsi(),
        ])

    # 2. Suspects connecting to the malicious server
    for susp in [SUSPECT_1, SUSPECT_2]:
        for i in range(5):
            records.append([
                susp["phone"], susp["ip"], SUSPICIOUS_SERVER_IP, 443, "TCP", "secure-chat-server.net", "PrivateISP",
                (base_time + timedelta(minutes=i*45)).strftime("%Y-%m-%d %H:%M:%S"),
                random.randint(5000, 15000), susp["imei"], susp["imsi"]
            ])

    return pd.DataFrame(records, columns=["Phone", "Source IP", "Destination IP", "Dest Port", "Protocol", "Domain", "Provider", "Date_Time", "Bytes", "IMEI", "IMSI"])


def _build_cdr_sample() -> pd.DataFrame:
    records = []
    base_time = datetime(2026, 4, 20, 8, 0, 0)

    # 1. Background noise
    for _ in range(30):
        records.append([
            _random_phone(), _random_phone(), random.choice(["VOICE", "SMS"]), random.randint(0, 300),
            _random_imei(), _random_imsi(), f"TWR00{random.randint(1,6)}", "Random Location",
            (base_time + timedelta(minutes=random.randint(1, 300))).strftime("%Y-%m-%d %H:%M:%S")
        ])

    # 2. Suspects calling each other
    for i in range(8):
        records.append([
            SUSPECT_1["phone"], SUSPECT_2["phone"], "VOICE", random.randint(30, 180),
            SUSPECT_1["imei"], SUSPECT_1["imsi"], "TWR001", "Connaught Place",
            (base_time + timedelta(minutes=i*30)).strftime("%Y-%m-%d %H:%M:%S")
        ])

    return pd.DataFrame(records, columns=["MSISDN", "Called_Number", "Call_Type", "Duration", "IMEI", "IMSI", "Tower_ID", "Location", "Date_Time"])


def _build_tower_samples() -> dict:
    towers = [
        ("tower_dump_a_10AM.csv", "TWR001", datetime(2026, 4, 20, 10, 0, 0), 10001, 101),
        ("tower_dump_b_11AM.csv", "TWR002", datetime(2026, 4, 20, 11, 0, 0), 10002, 102),
        ("tower_dump_c_12PM.csv", "TWR004", datetime(2026, 4, 20, 12, 0, 0), 10004, 104)
    ]
    
    samples = {}
    for file_name, tower_id, event_time, lac, cellid in towers:
        records = []
        # Add 50 random noise numbers to this tower at this time
        for _ in range(50):
            records.append([
                _random_phone(), _random_imei(), _random_imsi(), tower_id,
                (event_time + timedelta(minutes=random.randint(-15, 15))).strftime("%Y-%m-%d %H:%M:%S"),
                404, 10, lac, cellid
            ])
            
        # Insert our Suspects! They were at all 3 crime scenes!
        for susp in [SUSPECT_1, SUSPECT_2]:
            records.append([
                susp["phone"], susp["imei"], susp["imsi"], tower_id,
                (event_time + timedelta(minutes=random.randint(-2, 2))).strftime("%Y-%m-%d %H:%M:%S"),
                404, 10, lac, cellid
            ])
            
        samples[file_name] = pd.DataFrame(records, columns=["Phone", "IMEI", "IMSI", "Tower_ID", "Date_Time", "MCC", "MNC", "LAC", "CellID"])

    return samples


def write_sample_files(sample_dir: Path) -> None:
    ensure_sample_directory(sample_dir)
    _build_ipdr_sample().to_csv(sample_dir / "sample_ipdr.csv", index=False)
    _build_cdr_sample().to_csv(sample_dir / "sample_cdr.csv", index=False)
    for file_name, frame in _build_tower_samples().items():
        frame.to_csv(sample_dir / file_name, index=False)


def seed_demo_records(sample_dir: Path) -> int:
    ensure_sample_directory(sample_dir)
    write_sample_files(sample_dir)

    existing = fetch_uploaded_files()["file_name"].tolist()
    inserted = 0

    demo_frames = {
        "sample_ipdr.csv": ("ipdr", _build_ipdr_sample()),
        "sample_cdr.csv": ("cdr", _build_cdr_sample()),
    }
    for file_name, frame in _build_tower_samples().items():
        demo_frames[file_name] = ("tower_dump", frame)

    for file_name, (file_type, raw_frame) in demo_frames.items():
        if file_name in existing:
            continue
        normalized, _ = normalize_dataframe(raw_frame, file_type)
        inserted += insert_records(file_name, file_type, normalized)

    return inserted
