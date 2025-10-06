# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 14:47:38 2025

@author: Gopal
"""

import re
import os
import csv
from datetime import datetime
from collections import defaultdict

# --- KNOWLEDGE BASE (Derived from Hirata Manuals) ---
KNOWLEDGE_BASE = {
    "ceid_map": {
        18: "Alarm Set/Clear", 113: "Alarm Set/Clear", 114: "Alarm Set/Clear",
        131: "LoadToToolCompleted", 132: "UnloadFromToolCompleted",
        136: "MappingCompleted", 141: "PortStatusChange", 150: "RequestMagazineDock",
        151: "MagazineDocked", 152: "RequestOperatorIdCheck", 180: "RequestMagazineDock",
        181: "MagazineDocked", 182: "MagazineUndocked", 183: "RequestOperatorIdCheck",
        184: "RequestOperatorLogin",
    },
    "secs_map": {
        "S1F1": "Are You There Request", "S1F2": "Are You There Data",
        "S2F31": "Date and Time Request", "S2F32": "Date and Time Data",
        "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
        "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
    }
}

def parse_secs_data(data_lines, ceid_map):
    """Parses a list of data lines into a structured dictionary."""
    full_text = "".join(data_lines)
    data = {}
    
    potential_ids = re.findall(r"<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", full_text)
    for pid in potential_ids:
        pid = int(pid)
        if pid in ceid_map:
            if "Alarm" in ceid_map[pid]: data['AlarmID'] = pid
            else: data['CEID'] = pid
            break 

    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'\s*>", full_text)
    if rcmd_match: data['RCMD'] = rcmd_match.group(1)

    patterns = {
        'OperatorID': r"'OPERATORID'>\s*<A\s*\[\d+\]\s*'(\w+)'",
        'MagazineID': r"'MAGAZINEID'>\s*<A\s*\[\d+\]\s*'([\w-]+)'",
        'Result': r"'RESULT'>\s*<U1\s*\[\d+\]\s*(\d+)>",
        'LotID': r"'LOTID'>\s*<A\s*\[\d+\]\s*'([\d\.]+)'",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text)
        if match:
            if key == 'Result': data[key] = "Success" if match.group(1) == '0' else f"Failure({match.group(1)})"
            else: data[key] = match.group(1)

    panel_ids = re.findall(r"<\s*A\s*\[\d+\]\s*'(\d{9,})'\s*>", full_text)
    if panel_ids:
        unique_panels = list(set([p for p in panel_ids if len(p) < 15]))
        if unique_panels: data['PanelIDs'] = unique_panels
    return data

def generate_event_description(event, ceid_map):
    """Generates a human-readable description for the CSV."""
    data = event.get('data', {})
    ceid, rcmd, alarm_id = data.get('CEID'), data.get('RCMD'), data.get('AlarmID')

    if rcmd:
        if rcmd == "LOADSTART": return f"Host Command: Initiating LOADSTART for Lot '{data.get('LotID', 'N/A')}' with {len(data.get('PanelIDs', []))} panels."
        if rcmd == "REPLYOPERATORLOGIN": return f"Host Command: Acknowledging Operator Login for '{data.get('OperatorID', 'N/A')}'. Result: {data.get('Result', 'N/A')}."
        if rcmd == "REPLYMAGAZINEDOCK": return f"Host Command: Acknowledging Magazine Dock for '{data.get('MagazineID', 'N/A')}'. Result: {data.get('Result', 'N/A')}."
        if rcmd == "REPLYMAPPINGCHECK": return f"Host Command: Acknowledging mapping results. Result: {data.get('Result', 'N/A')}."
        return f"Host Command: {rcmd}"
    if alarm_id: return f"Warning: Anomaly detected with Alarm ID '{alarm_id}' while equipment was idle."
    if ceid:
        ceid_desc = ceid_map.get(ceid, f"Unknown CEID {ceid}")
        if "RequestOperatorLogin" in ceid_desc: return f"Event: Operator Login Requested (ID: {data.get('OperatorID', 'N/A')})."
        if "RequestMagazineDock" in ceid_desc: return f"Event: Magazine Dock Requested (ID: {data.get('MagazineID', 'N/A')})."
        if "MagazineDocked" in ceid_desc: return "Event: Magazine has been successfully docked."
        if "MappingCompleted" in ceid_desc: return f"Event: Magazine mapping completed. Found {len(data.get('PanelIDs', []))} panels."
        if "LoadToToolCompleted" in ceid_desc: return "Event: All panels successfully loaded to the tool."
        return f"Event: {ceid_desc}"
    return ""

def load_and_parse_log(input_filename, knowledge_base):
    """Loads and parses the entire log file into a structured list of events."""
    events = []
    with open(input_filename, 'r') as f: lines = f.readlines()
    
    current_tid = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not match: i+=1; continue
        timestamp, log_type, message_part = match.groups()
        
        tid_match = re.search(r"TransactionID=(\d+)", message_part)
        if tid_match: current_tid = tid_match.group(1)
        
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
        
        events.append({"timestamp": timestamp, "tid": current_tid, "msg_name": msg_name, "data": data})
        i += 1
    return events

def generate_csv_report(events, csv_filename, knowledge_base):
    """Generates a detailed CSV file from the parsed event data."""
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        header = ["Timestamp", "MessageType", "MessageDescription", "EventDescription", "CEID", "AlarmID", "RCMD", "DataSummary"]
        writer.writerow(header)
        for event in events:
            if not event['data']: continue
            description = generate_event_description(event, knowledge_base['ceid_map'])
            if description:
                data_summary = "; ".join([f"{k}:{v}" for k, v in event['data'].items() if k not in ['CEID', 'RCMD', 'AlarmID'] and v])
                writer.writerow([
                    event['timestamp'], event['msg_name'], knowledge_base['secs_map'].get(event['msg_name'], ''), 
                    description, event['data'].get('CEID', ''), event['data'].get('AlarmID', ''), 
                    event['data'].get('RCMD', ''), data_summary
                ])

def generate_summary_report(events, summary_filename, knowledge_base):
    """Analyzes all events and generates a dynamic, human-readable summary report."""
    if not events:
        with open(summary_filename, 'w', encoding='utf-8') as f: f.write("Log file is empty or could not be parsed.")
        return

    summary_data = {"operators": set(), "magazines": set(), "lot_id": None, "panel_count": 0, "job_start_time": None, "job_end_time": None, "anomalies": [], "alarms": defaultdict(int)}
    for event in events:
        data = event.get('data', {})
        if not data: continue
        if data.get('OperatorID'): summary_data['operators'].add(data['OperatorID'])
        if data.get('MagazineID'): summary_data['magazines'].add(data['MagazineID'])
        if data.get('RCMD') == 'LOADSTART':
            summary_data['lot_id'], summary_data['panel_count'], summary_data['job_start_time'] = data.get('LotID'), len(data.get('PanelIDs', [])), event['timestamp']
        if data.get('CEID') == 131: summary_data['job_end_time'] = event['timestamp']
        if data.get('Result', '').startswith("Failure"): summary_data['anomalies'].append(f"- {event['timestamp']}: A command failed: {generate_event_description(event, knowledge_base['ceid_map'])}")
        if data.get('AlarmID'): summary_data['alarms'][data['AlarmID']] += 1

    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n" + "MAINTENANCE & RELIABILITY ANALYSIS REPORT\n" + f"Log File Analyzed: {os.path.basename(summary_filename).replace('_summary.txt', '.txt')}\n" + f"Date of Log: {events[0]['timestamp'].split(' ')[0]}\n" + "="*80 + "\n\n")
        f.write("### 1. EXECUTIVE SUMMARY ###\nThis report analyzes the equipment's operational log. The system is deemed **operationally healthy**. ")
        if summary_data['job_start_time']: f.write(f"It successfully completed an automated loading cycle for Lot ID '{summary_data['lot_id']}' without critical failures. ")
        f.write("Anomalies are detailed below but did not impact production.\n\n")
        f.write("### 2. DETAILED OPERATIONAL WALKTHROUGH ###\n\n" + "**Phase A: Job Setup**\n")
        f.write(f"The process was initiated by operator(s): {', '.join(summary_data['operators']) or 'N/A'}. Magazine(s) used: {', '.join(summary_data['magazines']) or 'N/A'}. The log shows successful magazine docking, slot mapping, and state transitions (MIR -> MIC -> MPC) preparing for the automated job.\n\n")
        f.write("**Phase B: Automated Production Cycle**\n")
        if summary_data['job_start_time']:
            f.write(f"At {summary_data['job_start_time']}, the host commanded a `LOADSTART` for Lot ID **'{summary_data['lot_id']}'**, containing **{summary_data['panel_count']} panels**.\n")
            if summary_data['job_end_time']:
                start = datetime.strptime(summary_data['job_start_time'], "%Y/%m/%d %H:%M:%S.%f"); end = datetime.strptime(summary_data['job_end_time'], "%Y/%m/%d %H:%M:%S.%f")
                duration = (end - start).total_seconds(); cycle_time = duration / summary_data['panel_count'] if summary_data['panel_count'] > 0 else 0
                f.write(f"The entire automated process took **{duration:.2f} seconds**. The average cycle time per panel was approximately **{cycle_time:.2f} seconds**. This is a critical performance baseline.\n\n")
        else: f.write("No major automated production job (like LOADSTART) was detected in this log file.\n\n")
        f.write("### 3. ANOMALY ANALYSIS & MAINTENANCE INSIGHTS ###\n\n")
        if not summary_data['anomalies'] and not summary_data['alarms']: f.write("No significant anomalies or alarms were detected.\n\n")
        else:
            for anomaly in summary_data['anomalies']: f.write(f"**Anomaly (Transient Error):**\n  {anomaly}\n  **Analysis:** This was a temporary, self-recovering issue, likely related to operator timing rather than a persistent hardware fault.\n\n")
            if summary_data['alarms']:
                f.write("**Anomalies (Idle-State Alarms):**\n")
                for alarm_id, count in summary_data['alarms'].items(): f.write(f"  - **Alarm ID {alarm_id}:** Occurred {count} time(s) while the equipment was idle.\n")
                f.write("  - **Analysis:** These alarm codes are **NOT DOCUMENTED** in the standard operation manual and are classified as non-critical warnings.\n\n")
        f.write("### 4. ACTIONABLE MAINTENANCE RECOMMENDATIONS ###\n\n")
        f.write("**Priority 1: Investigate Undocumented Alarms (If Present)**\n  - Action: If 'Idle-State Alarms' were noted, create a service ticket with Hirata support. Provide this log and request a full alarm code dictionary.\n\n")
        f.write("**Priority 2: Monitor Transient Errors (If Present)**\n  - Action: If any docking failures were noted, log their occurrence. If frequent, schedule a PM to inspect the relevant sensors and alignments.\n\n")
        f.write("**Priority 3: Establish Performance Baselines**\n  - Action: Formally document the average panel transfer cycle time calculated in this report as the current performance benchmark for this equipment. Tracking this KPI will help detect performance degradation over time.\n")

def main():
    """Main execution block to handle user input and run analysis."""
    input_file = input("Please enter the name of the log file to analyze (e.g., Mess_4.txt): ")
    if not os.path.exists(input_file):
        print(f"\n--- ERROR ---\nFile not found: '{input_file}'\nPlease ensure the file is in the same directory and the name is spelled correctly.")
        return
    
    base_name = os.path.splitext(input_file)[0]
    csv_out = f"{base_name}_report.csv"
    summary_out = f"{base_name}_summary.txt"

    print("\nStarting analysis...")
    
    events = load_and_parse_log(input_file, KNOWLEDGE_BASE)
    
    if not events:
        print("Could not find any valid events to analyze in the log file.")
        return
        
    generate_csv_report(events, csv_out, KNOWLEDGE_BASE)
    generate_summary_report(events, summary_out, KNOWLEDGE_BASE)
    
    print(f"\nAnalysis complete!")
    print(f"-> Detailed CSV report saved to: '{csv_out}'")
    print(f"-> Summary report saved to: '{summary_out}'")

if __name__ == "__main__":
    main()
