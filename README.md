# Telecom Investigation Dashboard

This project is a final-year investigation dashboard for:

- `CDR / IPDR analysis`
- `Tower dump analysis`

## Features

- upload CSV or Excel telecom records
- auto-detect `cdr`, `ipdr`, and `tower_dump`
- normalize different column names into one standard schema
- store cleaned records in SQLite
- analyse destination IPs, ports, services, and repeated entities
- detect common numbers across multiple tower dumps
- show suspect movement on a map using demo tower coordinates
- generate built-in sample data for testing and presentation

## Run

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Main Pages

- `app.py`: overview dashboard and demo-data controls
- `pages/upload.py`: upload, normalize, and save records
- `pages/cdr_analysis.py`: CDR filtering, top towers, repeated contact pairs
- `pages/idpr_analysis.py`: IPDR filtering, top destination IPs and ports
- `pages/cross_link.py`: repeated IMEI, IMSI, number, destination IP, tower ID
- `pages/tower_analysis.py`: common numbers across selected tower dump files
- `pages/map_view.py`: suspect route map

## Suggested Demo Flow

1. Seed the demo data from the home page.
2. Show `IPDR Analysis` and explain common destination IPs.
3. Show `Cross Link Analysis` and explain repeated IMEI or IMSI.
4. Show `Tower Analysis` and find common numbers across locations.
5. Show `Map View` and present the suspect movement timeline.
