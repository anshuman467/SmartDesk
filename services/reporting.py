from datetime import datetime
import hashlib
import pandas as pd

from database.db import fetch_records, fetch_uploaded_files
from services.analytics import (
    generate_suspect_summary,
    generate_threat_panel,
    contact_intelligence_table,
    tower_intelligence_panel,
    build_behavioral_timeline,
)

def generate_forensic_hit_report(target_number: str) -> list:
    records = fetch_records()
    if records.empty:
        return [("Error", "# Error: No records found in the database.")]
        
    # Filter records for the specific target
    target_records = records[
        (records["phone_number"].astype(str) == target_number) | 
        (records["other_party_number"].astype(str) == target_number)
    ].copy()
    
    if target_records.empty:
        return [("Error", f"# Error: No activity found for target {target_number}.")]
        
    summary = generate_suspect_summary(target_records)
    threats = generate_threat_panel(target_records)
    contacts = contact_intelligence_table(target_records)
    towers = tower_intelligence_panel(target_records)
    timeline = build_behavioral_timeline(target_records)

    # We return a list of (page_title, page_content) for better UI rendering
    pages = []
    
    # ── PAGE 1: EXECUTIVE SUMMARY ──
    p1_md = []
    p1_md.append(f"# FORENSIC HIT REPORT: TARGET {target_number}")
    p1_md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
    p1_md.append("---")
    
    imsi_list = target_records["imsi"].dropna().unique().tolist() if "imsi" in target_records.columns else []
    imsi_str = ", ".join(map(str, imsi_list)) if imsi_list else "Unknown"
    operator_str = target_records["mcc"].dropna().astype(str).mode()[0] if "mcc" in target_records.columns and not target_records["mcc"].dropna().empty else "Unknown"
    top_contact = contacts.iloc[0]["other_party_number"] if not contacts.empty else "N/A"
    
    p1_md.append(f"- **Target Number:** {target_number}")
    p1_md.append(f"- **Unique IMEIs Detected:** {summary['imei_count']}")
    p1_md.append(f"- **Known IMSIs:** {imsi_str}")
    p1_md.append(f"- **Primary Operator (MCC):** {operator_str}")
    p1_md.append(f"- **Overall Risk Score:** {summary['risk_score']}/100")
    p1_md.append(f"- **Top Contact:** {top_contact}")
    p1_md.append(f"- **Home Tower / Most Frequented:** {summary['top_tower']}")
    pages.append(("Executive Summary", "\n".join(p1_md)))
    
    # ── PAGE 2: COMMUNICATION ANALYSIS ──
    p2_md = ["## PAGE 2: COMMUNICATION ANALYSIS", "---"]
    p2_md.append(f"- **Total Connected Calls:** {summary['total_calls']}")
    p2_md.append(f"- **Unique Contacts Network:** {summary['unique_contacts']}")
    
    short_calls = (target_records["duration"] < 15).sum() if "duration" in target_records.columns else 0
    p2_md.append(f"- **Burst Behavior (<15s):** {short_calls} calls")
    
    if not contacts.empty:
        p2_md.append("\n### Top Contacts Matrix")
        p2_md.append("| Contact Number | Calls | Risk Level | Reciprocity |")
        p2_md.append("|---|---|---|---|")
        for _, row in contacts.head(10).iterrows():
            p2_md.append(f"| {row['other_party_number']} | {row['calls']} | {row.get('risk', 'N/A')} | {row.get('reciprocity', 'N/A')} |")
    pages.append(("Communication Analysis", "\n".join(p2_md)))

    # ── PAGE 3: TOWER & MOVEMENT ──
    p3_md = ["## PAGE 3: TOWER & MOVEMENT", "---"]
    p3_md.append(f"- **Total Active Days:** {summary['active_days']}")
    
    if not towers.empty:
        p3_md.append("\n### Key Scene Intersections")
        p3_md.append("| Tower ID | Total Hits | First Seen | Last Seen | Suspicion Flag |")
        p3_md.append("|---|---|---|---|---|")
        for _, row in towers.head(10).iterrows():
            f_seen = row['first_seen'].strftime('%Y-%m-%d %H:%M') if pd.notnull(row['first_seen']) else 'N/A'
            l_seen = row['last_seen'].strftime('%Y-%m-%d %H:%M') if pd.notnull(row['last_seen']) else 'N/A'
            p3_md.append(f"| {row['tower_id']} | {row['hits']} | {f_seen} | {l_seen} | {row.get('suspicion', 'Normal')} |")
    pages.append(("Tower & Movement", "\n".join(p3_md)))

    # ── PAGE 4: DEVICE INTELLIGENCE ──
    p4_md = ["## PAGE 4: DEVICE INTELLIGENCE", "---"]
    imei_list = target_records["imei"].dropna().unique().tolist() if "imei" in target_records.columns else []
    p4_md.append(f"- **Total Devices (IMEIs) Used:** {len(imei_list)}")
    if len(imei_list) > 1:
        p4_md.append("- **SIM Swap Alert:** **CRITICAL** (Target moved SIM across multiple devices).")
    else:
        p4_md.append("- **SIM Swap Alert:** Normal (Single device used).")
        
    burner_score = "HIGH" if short_calls > 20 or len(imei_list) > 1 else "LOW"
    p4_md.append(f"- **Burner Behavior Probability:** **{burner_score}**")
    
    if imei_list:
        p4_md.append("\n### Known Hardware Identifiers")
        for imei in imei_list:
            p4_md.append(f"- IMEI: {imei}")
    pages.append(("Device Intelligence", "\n".join(p4_md)))

    # ── PAGE 5: THREAT FLAGS ──
    p5_md = ["## PAGE 5: AUTOMATED THREAT FLAGS", "---"]
    if threats:
        for t in threats:
            p5_md.append(f"### 🚨 [{t['level'].upper()}] {t['title']}")
            p5_md.append(f"> {t['desc']}\n")
    else:
        p5_md.append("No automated threat flags triggered for this suspect.")
    
    # ── IPDR DIGITAL INTELLIGENCE (Optional if IPDR exists) ──
    ipdr_records = records[records["file_type"] == "ipdr"].copy()
    target_ipdr = ipdr_records[ipdr_records["phone_number"].astype(str) == target_number].copy()
    
    if not target_ipdr.empty:
        from services.analytics import generate_ipdr_summary, generate_ipdr_threats
        ipdr_summary = generate_ipdr_summary(target_ipdr)
        ipdr_threats = generate_ipdr_threats(target_ipdr)
        
        p5_md.append("\n---")
        p5_md.append("### DIGITAL BEHAVIOR (IPDR)")
        p5_md.append(f"- **Total Internet Sessions:** {ipdr_summary['total']}")
        p5_md.append(f"- **Unique Destination IPs:** {ipdr_summary['unique_ips']}")
        p5_md.append(f"- **VPN/Tunneling Usage:** {'DETECTED' if ipdr_summary['vpn_hits'] > 0 else 'None'}")
        p5_md.append(f"- **Messaging Traffic Intensity:** {ipdr_summary['msg_pct']}%")
        p5_md.append(f"- **Digital Suspicion Score:** {ipdr_summary['risk_score']}/100")
        
        p5_md.append("\n#### Detected Digital Threats")
        for dt in ipdr_threats:
            p5_md.append(f"- **[{dt['level']}]** {dt['title']}: {dt['desc']}")
    pages.append(("Threat Flags", "\n".join(p5_md)))

    # ── PAGE 6: COURT ANNEXURE ──
    p6_md = ["## PAGE 6: COURT ANNEXURE & CHAIN OF CUSTODY", "---"]
    files_df = fetch_uploaded_files()
    if files_df.empty:
        p6_md.append("No source files found in database.")
    else:
        p6_md.append("| Source File Name | File Type | Record Count | System Upload Timestamp | File Hash (SHA-256 Mock) |")
        p6_md.append("|---|---|---|---|---|")
        for _, row in files_df.iterrows():
            hash_str = f"{row['file_name']}_{row['uploaded_at']}"
            file_hash = hashlib.sha256(hash_str.encode('utf-8')).hexdigest()
            p6_md.append(f"| {row['file_name']} | {row['file_type']} | {row['record_count']} | {row['uploaded_at']} | `{file_hash[:16]}...` |")
            
    p6_md.append("\n\n*End of Report.*")
    pages.append(("Court Annexure", "\n".join(p6_md)))
    
    return pages

    return pages

def generate_html_report(pages: list, target_number: str) -> str:
    import markdown
    
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; color: #1e293b; line-height: 1.6; margin: 0; padding: 0; background: #f1f5f9; }
        .report-container { width: 210mm; margin: 40px auto; }
        .report-page { 
            background: white; 
            min-height: 297mm; 
            padding: 2cm; 
            margin-bottom: 20px; 
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); 
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
            page-break-after: always;
        }
        h1 { color: #0f172a; font-size: 28px; border-bottom: 4px solid #2563eb; padding-bottom: 12px; margin-top: 0; }
        h2 { color: #1e40af; font-size: 22px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px; }
        h3 { color: #334155; font-size: 18px; margin-top: 25px; }
        p, li { font-size: 14px; color: #334155; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; }
        th { background: #f8fafc; color: #475569; text-align: left; padding: 12px; border: 1px solid #e2e8f0; font-weight: 600; }
        td { padding: 10px; border: 1px solid #f1f5f9; }
        tr:nth-child(even) { background: #fcfdfe; }
        .watermark { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg); font-size: 80px; color: rgba(0,0,0,0.03); font-weight: bold; pointer-events: none; white-space: nowrap; }
        .footer { position: absolute; bottom: 40px; left: 2cm; right: 2cm; font-size: 11px; color: #94a3b8; text-align: center; border-top: 1px solid #f1f5f9; padding-top: 15px; }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
        .tag-critical { background: #fee2e2; color: #991b1b; }
        .tag-suspicious { background: #ffedd5; color: #9a3412; }
        blockquote { border-left: 4px solid #cbd5e1; padding-left: 15px; font-style: italic; color: #64748b; background: #f8fafc; margin: 10px 0; padding: 10px 15px; }
        @media print {
            body { background: white; }
            .report-container { margin: 0; width: 100%; }
            .report-page { box-shadow: none; margin: 0; }
        }
    </style>
    """
    
    html = [f"<!DOCTYPE html><html><head><title>Forensic Report - {target_number}</title>{css}</head><body><div class='report-container'>"]
    
    for title, md_content in pages:
        # Convert markdown to HTML
        body_html = markdown.markdown(md_content, extensions=['tables', 'nl2br'])
        
        # Post-process for our custom tags
        body_html = body_html.replace("[CRITICAL]", "<span class='tag tag-critical'>CRITICAL</span>")
        body_html = body_html.replace("[SUSPICIOUS]", "<span class='tag tag-suspicious'>SUSPICIOUS</span>")
        
        page_html = f"""
        <div class='report-page'>
            <div class='watermark'>CONFIDENTIAL</div>
            {body_html}
            <div class='footer'>
                SIGNALDESK FORENSIC INTELLIGENCE SYSTEM | TARGET: {target_number} | CONFIDENTIAL REPORT
            </div>
        </div>
        """
        html.append(page_html)
        
    html.append("</div></body></html>")
    return "".join(html)

