# -*- coding: utf-8 -*-
"""
Module: parser.py
Description: Final, robust parser for Hirata log files using targeted data extraction.
Author: Jules
"""

import re
import pandas as pd
from datetime import datetime
from knowledge_base import KNOWLEDGE_BASE

def _get_ceid(text):
    """Extracts the CEID from an S6F11 message block."""
    match = re.search(r"<\s*L\s*\[3\]\s*<U4.*?<U4\s*\[\d+\]\s*(\d+)>", text, re.DOTALL)
    return int(match.group(1)) if match else None

def _get_port_state(text):
    """Extracts the PortState from a CEID 141 message block."""
    match = re.search(r"<A\s*\[\d+\]\s*'(MIC|MPC|MOR|MIR)'>", text)
    return match.group(1) if match else None

def _get_magazine_id(text):
    """Extracts the MagazineID from a CEID 181 message block."""
    matches = re.findall(r"<A\s*\[\d+\]\s*'(.*?)'>", text)
    return matches[1] if len(matches) > 2 else None

def _get_operator_id(text):
    """Extracts the OperatorID from a CEID 181 message block."""
    matches = re.findall(r"<A\s*\[\d+\]\s*'(.*?)'>", text)
    return matches[2] if len(matches) > 2 else None

def _get_alarm_id(text):
    """Extracts the AlarmID from a CEID 102 message block."""
    match = re.search(r"<\s*U2\s*\[\d+\]\s*(\d+)\s*>", text)
    return int(match.group(1)) if match else None

def _parse_data_block(text_block, msg_name):
    """Orchestrates the targeted extraction of data from a raw text block."""
    data = {}
    if msg_name == 'S6F11':
        ceid = _get_ceid(text_block)
        if ceid:
            data['CEID'] = ceid
            if ceid == 141: data['PortState'] = _get_port_state(text_block)
            elif ceid == 181:
                data['MagazineID'] = _get_magazine_id(text_block)
                data['OperatorID'] = _get_operator_id(text_block)
            elif ceid == 102: data['AlarmID'] = _get_alarm_id(text_block)
    return data

def _generate_event_description(row, kb):
    """Generates a human-readable description for a row in the DataFrame."""
    if pd.notna(row.get('RCMD')):
        return kb['rcmd_map'].get(row['RCMD'], f"Unknown Command: {row['RCMD']}")
    if pd.notna(row.get('CEID')):
        ceid_int = int(row['CEID'])
        base_desc = kb['ceid_map'].get(ceid_int, "Unknown Event")
        context = []
        if ceid_int == 141 and pd.notna(row.get('PortState')): context.append(f"State: {row['PortState']}")
        if ceid_int == 181 and pd.notna(row.get('MagazineID')): context.append(f"Magazine: {row['MagazineID']}")
        if ceid_int == 102 and pd.notna(row.get('AlarmID')): context.append(f"ALID: {int(row['AlarmID'])}")
        return f"{base_desc} ({', '.join(context)})" if context else base_desc
    return "Log Entry"

def load_and_parse_log(log_content, knowledge_base):
    """Loads and parses the entire log file into a structured DataFrame."""
    lines = log_content.splitlines()
    parsed_data = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not match:
            i += 1; continue

        timestamp, log_type, message_part = match.groups()
        direction = "Equipment to Host" if "Core:Send" in log_type else "Host to Equipment" if "Core:Receive" in log_type else "System"
        msg_name_match = re.search(r"MessageName=(\w+)|Message=.*?S\dF\d+:?'(\w+)'", message_part)
        msg_name = (msg_name_match.group(1) or msg_name_match.group(2)) if msg_name_match else None
        entry = {"Timestamp": timestamp, "Direction": direction, "Message": msg_name}

        data_block_lines = []
        if ("Core:Send" in log_type or "Core:Receive" in log_type) and i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
            j = i + 1
            while j < len(lines) and lines[j].strip() != '.':
                data_block_lines.append(lines[j]); j += 1
            i = j

        if data_block_lines:
            text_block = "".join(data_block_lines)
            parsed_details = _parse_data_block(text_block, msg_name)
            entry.update(parsed_details)
            entry['RawData'] = " ".join(text_block.split())

        parsed_data.append(entry)
        i += 1

    df = pd.DataFrame(parsed_data)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Simple Description'] = df['Message'].map(knowledge_base['secs_map'])
    df['Event'] = df.apply(lambda row: _generate_event_description(row, knowledge_base), axis=1)

    for col in ['PortID', 'AlarmID', 'CEID']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    final_cols = ["Timestamp", "Direction", "Message", "Simple Description", "Event", "AlarmID", "CEID", "PortID", "PortState", "MagazineID", "OperatorID", "LotID", "PanelID", "SlotInfo", "Orientation", "RawData"]
    for col in final_cols:
        if col not in df.columns: df[col] = None

    return df[final_cols]