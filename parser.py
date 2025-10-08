# -*- coding: utf-8 -*-
"""
Log Parsing Logic for Hirata Loadport Log Analyzer.
This module contains functions to parse log content into structured data.
"""
import re
from knowledge_base import KNOWLEDGE_BASE

# --- Individual Parser Functions ---

def _parse_port_status_change(full_text):
    """Parses CEID 141 (PortStatusChange)."""
    data = {}
    match = re.search(r"<\s*U1\s*\[1\]\s*(\d+)\s*>\s*<\s*A\s*\[3\]\s*'(\w+)'\s*>", full_text)
    if match:
        data['PortID'] = match.group(1)
        data['PortState'] = match.group(2)
    return data

def _parse_id_read(full_text):
    """Parses CEID 120 (IDRead)."""
    data = {}
    fields = re.findall(r"<\s*(?:A|U\d)\s*\[\d+\]\s*'([^']*)'\s*>", full_text)
    if len(fields) >= 5:
        result_code = fields[4]
        result_text = KNOWLEDGE_BASE['id_read_result_map'].get(result_code, f"Unknown Code({result_code})")
        data.update({
            'LotID': fields[1], 
            'PanelID': fields[2], 
            'Orientation': fields[3], 
            'ResultCode': result_code,
            'Result': result_text,
            'SlotInfo': f"Slot: {fields[5]}" if len(fields) > 5 else 'N/A'
        })
    return data

def _parse_magazine_docked(full_text):
    """Parses CEID 181 (MagazineDocked)."""
    data = {}
    fields = re.findall(r"<\s*(?:A|U\d)\s*\[\d+\]\s*'([^']*)'\s*>", full_text)
    u_fields = re.findall(r"<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", full_text)
    if len(u_fields) > 1 and len(fields) > 2:
        data.update({
            'PortID': u_fields[1], 
            'MagazineID': fields[1], 
            'OperatorID': fields[2]
        })
    return data

def _parse_generic(full_text):
    """Generic fallback parser for simple key-value pairs."""
    data = {}
    patterns = {
        'OperatorID': r"'OPERATORID'>\s*<A\s*\[\d+\]\s*'(\w+)'",
        'MagazineID': r"'MAGAZINEID'>\s*<A\s*\[\d+\]\s*'([\w-]+)'"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, full_text)
        if match:
            data[key] = match.group(1)
    return data

def _parse_svid_change(full_text):
    """Parses SVID changes from event reports."""
    data = {}
    # Structure: <L[2] <U4[1] SVID> <A[n] SVID_VALUE>>
    svid_matches = re.findall(r"<\s*L\s*\[2\]\s*<\s*U\d\s*\[\d+\]\s*(\d+)\s*>\s*<\s*A\s*\[\d+\]\s*'([^']*)'\s*>\s*>", full_text)
    if svid_matches:
        svid, value = svid_matches[0]
        svid = int(svid)
        data['SVID'] = svid
        data['SVID_Name'] = KNOWLEDGE_BASE['svid_map'].get(svid, f"Unknown SVID({svid})")
        data['SVID_Value'] = value
    return data

# --- Dispatch Table ---

CEID_PARSERS = {
    141: _parse_port_status_change,
    120: _parse_id_read,
    181: _parse_magazine_docked,
    16: _parse_svid_change, # GemPPChangeEvent often reports SVID changes
    # Add other CEID -> function mappings here as needed
}

# --- Main Parsing Logic ---

def parse_secs_data(data_lines):
    """
    Parses a list of data lines into a structured dictionary using a dispatch pattern.
    This version robustly finds the CEID instead of assuming it's the first ID.
    """
    full_text = "\n".join(data_lines)
    data = {}
    ceid = None
    rcmd = None
    ceid_map = KNOWLEDGE_BASE['ceid_map']
    alid_map = KNOWLEDGE_BASE['alid_map']

    # Find all potential integer IDs in the message
    potential_ids = re.findall(r"<\s*U\d\s*\[\d+\]\s*(\d+)\s*>", full_text)

    # Find the CEID by checking all potential IDs against the ceid_map
    for pid_str in potential_ids:
        pid = int(pid_str)
        if pid in ceid_map:
            ceid = pid
            break  # Found the first valid CEID, assume it's the primary one

    # If a CEID was found, process it
    if ceid:
        data['CEID'] = ceid
        event_name = ceid_map.get(ceid)

        # Handle Alarms specifically
        if event_name in ["AlarmSet", "AlarmClear"]:
            # In an alarm message, the ALID is usually the number following the CEID
            try:
                ceid_index = potential_ids.index(str(ceid))
                if ceid_index + 1 < len(potential_ids):
                    alarm_id = int(potential_ids[ceid_index + 1])
                    data['AlarmID'] = alarm_id
                    data['AlarmState'] = event_name
                    data['AlarmTEXT'] = alid_map.get(alarm_id, f"Unknown Alarm ID ({alarm_id})")
            except (ValueError, IndexError):
                pass  # Could not find ALID, but we still have the CEID

        # Use the dispatch table to find the correct parser for any event
        parser_func = CEID_PARSERS.get(ceid, _parse_generic)
        parsed_data = parser_func(full_text)
        data.update(parsed_data)

    # Identify RCMD for Host Commands (S2F49)
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'\s*>", full_text)
    if rcmd_match and rcmd_match.group(1) in KNOWLEDGE_BASE['rcmd_map']:
        rcmd = rcmd_match.group(1)
        data['RCMD'] = rcmd
        # This part should only run if it's an RCMD, not if we already found a CEID
        if not ceid:
            param_pairs = re.findall(r"<\s*L\s*\[2\]\s*<A\s*\[\d+\]\s*'([^']+)'>\s*<(?:A|U\d)\s*\[\d+\]\s*'([^']*)'>\s*>", full_text)
            for key, value in param_pairs:
                data[key] = value
        
    return data

def load_and_parse_log(log_content):
    """
    Parses the entire log content into a structured list of events.
    """
    events = []
    lines = log_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not match:
            i += 1
            continue

        timestamp, log_type, message_part = match.groups()
        direction = "Host->Equip" if "Core:Send" in log_type else "Equip->Host"

        if "Core:Send" in log_type or "Core:Receive" in log_type:
            msg_name_match = (re.search(r"Message=.*?:'(\w+)'", message_part) or 
                              re.search(r"MessageName=(\w+)", message_part))
            msg_name = msg_name_match.group(1) if msg_name_match else "N/A"

            if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
                data_block_lines = []
                j = i + 1
                while j < len(lines) and not lines[j].strip() == '.':
                    data_block_lines.append(lines[j].strip())
                    j += 1

                if data_block_lines:
                    data = parse_secs_data(data_block_lines)
                    if data:
                        events.append({
                            "timestamp": timestamp,
                            "direction": direction,
                            "msg_name": msg_name,
                            "data": data
                        })
                i = j
            else:
                i += 1
        else:
            i += 1
    return events
