# -*- coding: utf-8 -*-
"""
Reporting Logic for Hirata Loadport Log Analyzer.
This module generates CSV and chronological, human-readable reports.
"""
import pandas as pd
from knowledge_base import KNOWLEDGE_BASE

# --- Individual Description Generators ---

def _describe_port_status(data):
    port_id = data.get('PortID', 'N/A')
    port_state_code = data.get('PortState', 'N/A')
    port_state_desc = KNOWLEDGE_BASE['port_state_map'].get(port_state_code, 'Unknown State')
    return f"Port {port_id} status changed to {port_state_code} ({port_state_desc})."

def _describe_id_read(data):
    result_text = data.get('Result', 'N/A')
    prefix = "" if data.get('ResultCode') == '0' else "**ERROR:** "
    return (f"{prefix}Read Panel ID '{data.get('PanelID', 'N/A')}' from Lot '{data.get('LotID', 'N/A')}' "
            f"in {data.get('SlotInfo', 'N/A')}. Result: {result_text}.")

def _describe_magazine_docked(data):
    return (f"Magazine '{data.get('MagazineID', 'N/A')}' docked at Port {data.get('PortID', 'N/A')} "
            f"by Operator '{data.get('OperatorID', 'N/A')}'.")
            
def _describe_alarm(data):
    state = data.get('AlarmState', 'N/A')
    alarm_text = data.get('AlarmTEXT', 'Unknown Alarm')
    prefix = "**ALARM:** " if state == "AlarmSet" else ""
    return f"{prefix}Alarm '{data.get('AlarmID')}' ({alarm_text}) changed to: {state}."

def _describe_svid_change(data):
    """Generates a description for an SVID change event."""
    svid_name = data.get('SVID_Name', 'Unknown SVID')
    svid_value = data.get('SVID_Value', 'N/A')
    return f"Status Update: {svid_name} is now '{svid_value}'."

# --- Dispatch Table for Descriptions ---

EVENT_DESCRIPTORS = {
    141: _describe_port_status,
    120: _describe_id_read,
    181: _describe_magazine_docked,
    101: _describe_alarm,
    102: _describe_alarm,
    16: _describe_svid_change,
    # Add other CEID -> description function mappings here
}

def generate_event_description(event):
    """Generates a single human-readable description line for an event."""
    data = event.get('data', {})
    ceid = data.get('CEID')
    rcmd = data.get('RCMD')

    # Handle Host Commands
    if rcmd:
        desc = KNOWLEDGE_BASE['rcmd_map'].get(rcmd, rcmd)
        lot_id = data.get('LOTID') or data.get('LotID')
        port_id = data.get('SRCPORTID')
        if lot_id and port_id:
            return f"Host Command: Sent `{rcmd}` for Lot '{lot_id}' on Port {port_id}."
        else:
            return f"Host Command: Sent `{rcmd}`. ({desc})"
    
    # Handle Equipment Events using the dispatch table
    if ceid in EVENT_DESCRIPTORS:
        return EVENT_DESCRIPTORS[ceid](data)
    
    # Generic fallback for unhandled events
    if ceid:
        ceid_desc = KNOWLEDGE_BASE['ceid_map'].get(ceid, f"Unknown CEID {ceid}")
        return f"Event: {ceid_desc} occurred. Data: {data}"
        
    return "Unknown log entry."


def generate_summary_report(events):
    """Analyzes events to generate a high-level summary with KPIs."""
    if not events:
        return "No data available to generate a summary."

    # --- KPI Calculations ---
    start_time = pd.to_datetime(events[0]['timestamp'])
    end_time = pd.to_datetime(events[-1]['timestamp'])
    total_cycle_time = end_time - start_time

    panels_processed = sum(1 for event in events if event.get('data', {}).get('CEID') in [131, 132])
    alarms_set = sum(1 for event in events if event.get('data', {}).get('AlarmState') == 'AlarmSet')

    # --- Executive Summary ---
    if alarms_set > 0:
        executive_summary = "Fault State Detected"
        summary_color = "color: red;"
    else:
        executive_summary = "Golden Run"
        summary_color = "color: green;"

    # --- Report Generation ---
    report_lines = [
        "### Analysis Summary Report",
        "---",
        f"**Executive Summary:** <span style='{summary_color}'>{executive_summary}</span>",
        "#### Key Performance Indicators (KPIs):",
        f"- **Total Cycle Time:** {total_cycle_time}",
        f"- **Total Panels Processed:** {panels_processed}",
        f"- **Total Alarms:** {alarms_set}",
    ]

    return "\n".join(report_lines)

def generate_chronological_report(events):
    """Analyzes all events and generates a dynamic, chronological report."""
    if not events:
        return "Log file is empty or no valid SECS/GEM events were found."

    report_lines = [
        "HIRATA LOADPORT OPERATION REPORT - CHRONOLOGICAL WALKTHROUGH\n" + "="*80,
        "This report details the sequence of operations as recorded in the log file.\n"
    ]

    for event in events:
        description = generate_event_description(event)
        report_lines.append(f"[{event['timestamp']}] {description}")

    return "\n".join(report_lines)


def generate_csv_report(events):
    """Generates a detailed DataFrame from the parsed event data."""
    report_data = []
    # Dynamic header generation based on all possible keys
    header = sorted(list(set(key for event in events for key in event['data'])))
    base_header = ["Timestamp", "Direction", "MessageType", "EventDescription"]
    full_header = base_header + [h for h in header if h not in base_header]

    for event in events:
        description = generate_event_description(event)
        data = event['data']
        
        row = {
            "Timestamp": event['timestamp'],
            "Direction": event['direction'],
            "MessageType": event['msg_name'],
            "EventDescription": description,
        }
        row.update(data)
        report_data.append(row)
        
    return pd.DataFrame(report_data, columns=full_header)
