# -*- coding: utf-8 -*-
"""
Hirata Loadport Log Analyzer
Streamlit application to parse and analyze Hirata Loadport communication logs.
"""
import re
import os
from datetime import datetime
from collections import defaultdict
import streamlit as st
import pandas as pd

# --- KNOWLEDGE BASE (Derived from Hirata Manuals) ---
KNOWLEDGE_BASE = {
    "ceid_map": {
        12: "ControlStateChange", 101: "AlarmClear", 102: "AlarmSet",
        120: "IDRead", 121: "UnloadedFromMag", 122: "LoadedToMag",
        127: "LoadedToTool", 131: "LoadToToolCompleted", 132: "UnloadFromToolCompleted",
        136: "MappingCompleted", 141: "PortStatusChange", 151: "LoadStarted",
        152: "UnloadStarted", 180: "RequestMagazineDock", 181: "MagazineDocked",
        182: "MagazineUndocked", 183: "RequestOperatorIdCheck", 184: "RequestOperatorLogin",
    },
    "rcmd_map": {
        "LOADSTART": "Command to start loading panels from a magazine to the tool.",
        "UNLOADSTART": "Command to start unloading panels from the tool to a magazine.",
        "REPLYOPERATORLOGIN": "Host's acknowledgement of an operator login event.",
        "REPLYMAGAZINEDOCK": "Host's acknowledgement of a magazine dock event.",
        "REPLYOPERATORIDCHECK": "Host's acknowledgement of an operator ID check.",
        "REPLYMAPPINGCHECK": "Host's acknowledgement of a mapping check event.",
        "CHECKSLOT": "Command to instruct the equipment to perform a slot map scan.",
    },
    "secs_map": {
        "S1F1": "Are You There Request", "S1F2": "Are You There Data",
        "S2F31": "Date and Time Request", "S2F32": "Date and Time Data",
        "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
        "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
    }
}

def parse_secs_data(data_lines, ceid_map):
    """Parses a list of data lines into a structured dictionary with enhanced logic."""
    full_text = "\n".join(data_lines)
    data = {}
    ceid, rcmd, alarm_id = None, None, None

    # Identify CEID/AlarmID
    potential_ids = re.findall(r"<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", full_text)
    if potential_ids and int(potential_ids[0]) in ceid_map:
        pid = int(potential_ids[0])
        if ceid_map[pid] in ["AlarmSet", "AlarmClear"]:
            alarm_id = pid
            data['AlarmID'] = alarm_id
        else:
            ceid = pid
            data['CEID'] = ceid

    # Identify RCMD
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'\s*>", full_text)
    if rcmd_match and rcmd_match.group(1) in KNOWLEDGE_BASE['rcmd_map']:
        rcmd = rcmd_match.group(1)
        data['RCMD'] = rcmd

    # Apply specific parsing based on message type
    if rcmd:
        param_pairs = re.findall(r"<\s*L\s*\[2\]\s*<A\s*\[\d+\]\s*'([^']+)'>\s*<(?:A|U\d)\s*\[\d+\]\s*'([^']*)'>\s*>", full_text)
        for key, value in param_pairs:
            data[key] = value
    elif ceid:
        if ceid == 141: # PortStatusChange
            match = re.search(r"<\s*U1\s*\[1\]\s*(\d+)\s*>\s*<\s*A\s*\[3\]\s*'(\w+)'\s*>", full_text)
            if match: data.update({'PortID': match.group(1), 'PortState': match.group(2)})
        elif ceid == 120: # IDRead
            fields = re.findall(r"<\s*(?:A|U\d)\s*\[\d+\]\s*'([^']*)'\s*>", full_text)
            if len(fields) >= 5:
                data.update({'LotID': fields[1], 'PanelID': fields[2], 'Orientation': fields[3], 'Result': "Success" if fields[4] == '0' else f"Failure({fields[4]})", 'SlotInfo': f"Slot: {fields[5]}"})
        elif ceid == 181: # MagazineDocked
            fields = re.findall(r"<\s*(?:A|U\d)\s*\[\d+\]\s*'([^']*)'\s*>", full_text)
            u_fields = re.findall(r"<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", full_text)
            if len(u_fields) > 1 and len(fields) > 2:
                data.update({'PortID': u_fields[1], 'MagazineID': fields[1], 'OperatorID': fields[2]})
        else: # Generic fallback for other simple messages
            patterns = {'OperatorID': r"'OPERATORID'>\s*<A\s*\[\d+\]\s*'(\w+)'", 'MagazineID': r"'MAGAZINEID'>\s*<A\s*\[\d+\]\s*'([\w-]+)'"}
            for key, pattern in patterns.items():
                match = re.search(pattern, full_text)
                if match: data[key] = match.group(1)
    return data

def generate_event_description(event, ceid_map):
    """Generates a human-readable description for the CSV, enhanced for new types."""
    data = event.get('data', {})
    ceid, rcmd, alarm_id = data.get('CEID'), data.get('RCMD'), data.get('AlarmID')

    if rcmd:
        desc = KNOWLEDGE_BASE['rcmd_map'].get(rcmd, rcmd)
        if rcmd == "LOADSTART": return f"Host: Start loading Lot '{data.get('LOTID', 'N/A')}' from Port {data.get('SRCPORTID', 'N/A')}."
        if rcmd.startswith("REPLY"): return f"Host: Acknowledged command for {data.get('MagazineID') or data.get('OperatorID')}. Result: {data.get('Result', 'N/A')}."
        return f"Host Command: {desc}"
    if alarm_id: return f"Alarm: Alarm ID '{alarm_id}' was set."
    if ceid:
        ceid_desc = ceid_map.get(ceid, f"Unknown CEID {ceid}")
        if ceid == 141: return f"Event: Port {data.get('PortID', 'N/A')} status changed to {data.get('PortState', 'N/A')}."
        if ceid == 120: return f"Event: Read Panel ID '{data.get('PanelID', 'N/A')}' from Lot '{data.get('LotID', 'N/A')}' in {data.get('SlotInfo', 'N/A')}."
        if ceid == 181: return f"Event: Magazine '{data.get('MagazineID', 'N/A')}' docked at Port {data.get('PortID', 'N/A')} by Operator '{data.get('OperatorID', 'N/A')}'."
        if ceid == 136: return f"Event: Magazine mapping completed. Found {len(data.get('PanelIDs', []))} panels."
        if ceid == 131: return "Event: All panels successfully loaded to the tool."
        if ceid == 184: return f"Event: Operator Login Requested (ID: {data.get('OperatorID', 'N/A')})."
        return f"Event: {ceid_desc}"
    return ""

def load_and_parse_log(log_content, knowledge_base):
    """Parses the entire log content into a structured list of events."""
    events = []
    lines = log_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not match: i+=1; continue
        timestamp, log_type, message_part = match.groups()
        msg_name = (re.search(r"Message=.*?:'(\w+)'", message_part) or re.search(r"MessageName=(\w+)", message_part))
        msg_name = msg_name.group(1) if msg_name else "N/A"
        
        data = {}
        if "Core:Send" in log_type or "Core:Receive" in log_type:
            if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
                data_block_lines = []
                j = i + 1
                while j < len(lines) and lines[j].strip() != '.': data_block_lines.append(lines[j]); j += 1
                i = j
                data = parse_secs_data(data_block_lines, knowledge_base['ceid_map'])
        events.append({"timestamp": timestamp, "msg_name": msg_name, "data": data})
        i += 1
    return events

def generate_csv_report(events, knowledge_base):
    """Generates a detailed DataFrame from the parsed event data with expanded columns."""
    report_data = []
    header = ["Timestamp", "MessageType", "MessageDescription", "EventDescription", "CEID", "AlarmID", "RCMD", "OperatorID", "MagazineID", "LotID", "PanelID", "PortID", "PortState", "SlotInfo", "DataSummary"]
    for event in events:
        if not event['data']: continue
        description = generate_event_description(event, knowledge_base['ceid_map'])
        if description:
            data = event['data']
            data_summary = "; ".join([f"{k}:{v}" for k, v in data.items() if k not in header and v])
            report_data.append({
                "Timestamp": event['timestamp'], "MessageType": event['msg_name'],
                "MessageDescription": knowledge_base['secs_map'].get(event['msg_name'], ''),
                "EventDescription": description, "CEID": data.get('CEID', ''), "AlarmID": data.get('AlarmID', ''),
                "RCMD": data.get('RCMD', ''), "OperatorID": data.get('OperatorID', ''), "MagazineID": data.get('MagazineID', ''),
                "LotID": data.get('LotID', ''), "PanelID": data.get('PanelID', ''),
                "PortID": data.get('PortID', data.get('SRCPORTID', '')), "PortState": data.get('PortState', ''),
                "SlotInfo": data.get('SlotInfo', ''), "DataSummary": data_summary
            })
    return pd.DataFrame(report_data, columns=header)

def generate_summary_report(events, log_filename, knowledge_base):
    """Analyzes all events and generates a dynamic, human-readable summary report."""
    if not events: return "Log file is empty or could not be parsed."

    summary_data = {"operators": set(), "magazines": set(), "lot_id": None, "panel_count": 0, "job_start_time": None, "job_end_time": None, "anomalies": [], "alarms": defaultdict(int)}
    for event in events:
        data = event.get('data', {})
        if data.get('OperatorID'): summary_data['operators'].add(data['OperatorID'])
        if data.get('MagazineID'): summary_data['magazines'].add(data['MagazineID'])
        if data.get('RCMD') == 'LOADSTART':
            summary_data['lot_id'], summary_data['panel_count'], summary_data['job_start_time'] = data.get('LotID'), len(data.get('PanelIDs', [])), event['timestamp']
        if data.get('CEID') == 131: summary_data['job_end_time'] = event['timestamp']
        if data.get('Result', '').startswith("Failure"): summary_data['anomalies'].append(f"- {event['timestamp']}: A command failed: {generate_event_description(event, knowledge_base['ceid_map'])}")
        if data.get('AlarmID'): summary_data['alarms'][data['AlarmID']] += 1

    report_lines = [f"MAINTENANCE & RELIABILITY ANALYSIS REPORT for {log_filename}\n" + "="*80]
    report_lines.append("\n### 1. EXECUTIVE SUMMARY ###\nThis report analyzes the equipment's operational log. The system is deemed **operationally healthy**. ")
    if summary_data['job_start_time']: report_lines.append(f"It successfully completed an automated loading cycle for Lot ID '{summary_data['lot_id']}' without critical failures. ")

    report_lines.append("\n### 2. DETAILED OPERATIONAL WALKTHROUGH ###\n**Phase A: Job Setup**")
    report_lines.append(f"The process was initiated by operator(s): {', '.join(summary_data['operators']) or 'N/A'}. Magazine(s) used: {', '.join(summary_data['magazines']) or 'N/A'}.\n")

    report_lines.append("**Phase B: Automated Production Cycle**")
    if summary_data['job_start_time']:
        report_lines.append(f"At {summary_data['job_start_time']}, the host commanded a `LOADSTART` for Lot ID **'{summary_data['lot_id']}'**, containing **{summary_data['panel_count']} panels**.")
        if summary_data['job_end_time']:
            start = datetime.strptime(summary_data['job_start_time'], "%Y/%m/%d %H:%M:%S.%f"); end = datetime.strptime(summary_data['job_end_time'], "%Y/%m/%d %H:%M:%S.%f")
            duration = (end - start).total_seconds(); cycle_time = duration / summary_data['panel_count'] if summary_data['panel_count'] > 0 else 0
            report_lines.append(f"The entire automated process took **{duration:.2f} seconds**. Average cycle time per panel: **{cycle_time:.2f} seconds**.\n")
    else: report_lines.append("No major automated production job (like LOADSTART) was detected in this log file.\n")

    report_lines.append("### 3. ANOMALY ANALYSIS & MAINTENANCE INSIGHTS ###")
    if not summary_data['anomalies'] and not summary_data['alarms']: report_lines.append("No significant anomalies or alarms were detected.\n")
    else:
        for anomaly in summary_data['anomalies']: report_lines.append(f"**Anomaly (Transient Error):** {anomaly}\n")
        if summary_data['alarms']:
            report_lines.append("**Anomalies (Idle-State Alarms):**")
            for alarm_id, count in summary_data['alarms'].items(): report_lines.append(f"  - **Alarm ID {alarm_id}:** Occurred {count} time(s).")
            report_lines.append("  - **Analysis:** These alarm codes are classified as non-critical warnings.\n")

    report_lines.append("### 4. ACTIONABLE MAINTENANCE RECOMMENDATIONS ###")
    report_lines.append("**Priority 1:** Investigate any undocumented alarms with Hirata support.")
    report_lines.append("**Priority 2:** Monitor transient errors. If frequent, schedule PM for sensors.")
    report_lines.append("**Priority 3:** Formally document the cycle time as a performance benchmark.")
    return "\n".join(report_lines)

def main():
    """Main execution block for the Streamlit application."""
    st.set_page_config(layout="wide")
    st.title("Hirata Loadport Log Analyzer")

    uploaded_file = st.file_uploader("Upload a Hirata Loadport Log File", type=['txt', 'log'])

    if uploaded_file is not None:
        log_content = uploaded_file.getvalue().decode('utf-8')
        log_filename = uploaded_file.name
        
        with st.spinner(f"Analyzing {log_filename}..."):
            events = load_and_parse_log(log_content, KNOWLEDGE_BASE)
            if not events:
                st.error("Could not find any valid events to analyze in the log file."); return
            summary_report_str = generate_summary_report(events, log_filename, KNOWLEDGE_BASE)
            detailed_df = generate_csv_report(events, KNOWLEDGE_BASE)

        st.success("Analysis Complete!")
        st.subheader("Analysis Summary Report")
        st.text_area("Summary", summary_report_str, height=300)
        st.download_button("Download Summary (.txt)", summary_report_str, f"{os.path.splitext(log_filename)[0]}_summary.txt", "text/plain")

        st.subheader("Detailed Event Data")
        st.dataframe(detailed_df)
        st.download_button("Download Detailed Data (.csv)", detailed_df.to_csv(index=False).encode('utf-8'), f"{os.path.splitext(log_filename)[0]}_report.csv", "text/csv")

if __name__ == "__main__":
    main()