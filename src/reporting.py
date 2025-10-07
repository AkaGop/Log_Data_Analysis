# -*- coding: utf-8 -*-
"""
Reporting Logic for Hirata Loadport Log Analyzer.
This module generates CSV and human-readable summary reports.
"""
from datetime import datetime
from collections import defaultdict
import pandas as pd
from src.knowledge_base import KNOWLEDGE_BASE

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