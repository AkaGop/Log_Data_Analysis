# -*- coding: utf-8 -*-
"""
Reporting Logic for Hirata Loadport Log Analyzer.
This module generates CSV and chronological, human-readable reports.
"""
import pandas as pd
from datetime import datetime
from src.knowledge_base import KNOWLEDGE_BASE

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
    prefix = "**ALARM:** " if state == "AlarmSet" else ""
    return f"{prefix}Alarm ID '{data.get('AlarmID')}' state changed to: {state}."

# --- Dispatch Table for Descriptions ---

EVENT_DESCRIPTORS = {
    141: _describe_port_status,
    120: _describe_id_read,
    181: _describe_magazine_docked,
    101: _describe_alarm,
    102: _describe_alarm,
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

def generate_executive_summary(events):
    """
    Generates a high-level summary based on the presence of alarms.
    """
    has_alarms = any(event['data'].get('AlarmState') == 'AlarmSet' for event in events)

    if has_alarms:
        summary = (
            "**Assessment: Equipment FAULT**\n"
            "**Priority: HIGH**\n\n"
            "One or more alarms were triggered during the operation. "
            "This indicates a potential issue that may require immediate attention. "
            "Review the detailed event log for specific alarm codes and timestamps."
        )
    else:
        summary = (
            "**Assessment: Golden Run**\n"
            "**Priority: Low**\n\n"
            "The process completed successfully without any critical alarms. "
            "This log represents a 'Golden Run' and can be used as a baseline for normal operations."
        )
    return summary

def calculate_kpis(events, detailed_df):
    """
    Calculates Key Performance Indicators (KPIs) from the event data.
    """
    kpis = {
        "Total Cycle Time": "N/A",
        "Mapping Time": "N/A",
        "Average Time Per Panel": "N/A",
        "Panel Count": "N/A"
    }

    df = detailed_df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y/%m/%d %H:%M:%S.%f')

    # --- Total Cycle Time (LOADSTART to LoadToToolCompleted) ---
    load_start_time = df[df['RCMD'] == 'LOADSTART']['Timestamp'].min()
    load_complete_time = df[df['CEID'] == 131]['Timestamp'].max() # CEID 131: LoadToToolCompleted

    if pd.notna(load_start_time) and pd.notna(load_complete_time):
        total_cycle_duration = load_complete_time - load_start_time
        kpis["Total Cycle Time"] = str(total_cycle_duration)

    # --- Mapping Time (MIC to MappingCompleted) ---
    mic_time = df[(df['CEID'] == 141) & (df['PortState'] == 'MIC')]['Timestamp'].min()
    map_complete_time = df[df['CEID'] == 136]['Timestamp'].max() # CEID 136: MappingCompleted

    if pd.notna(mic_time) and pd.notna(map_complete_time):
        mapping_duration = map_complete_time - mic_time
        kpis["Mapping Time"] = str(mapping_duration)

    # --- Average Time Per Panel ---
    panel_count_series = df[df['CEID'] == 136]['PanelCount'].dropna()
    if not panel_count_series.empty:
        panel_count = int(panel_count_series.iloc[0])
        kpis["Panel Count"] = panel_count
        if pd.notna(load_start_time) and pd.notna(load_complete_time) and panel_count > 0:
            avg_time = (load_complete_time - load_start_time) / panel_count
            kpis["Average Time Per Panel"] = str(avg_time)

    return kpis
