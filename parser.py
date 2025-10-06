# -*- coding: utf-8 -*-
"""
Module: parser.py
Author: Jules
"""

import re
import pandas as pd
from datetime import datetime

# --- KNOWLEDGE BASE (Derived from Hirata Manuals) ---
KNOWLEDGE_BASE = {
    "ceid_map": {
        12: "ControlStateChange",
        101: "AlarmClear",
        102: "AlarmSet",
        120: "IDRead",
        121: "UnloadedFromMag",
        122: "LoadedToMag",
        127: "LoadedToTool",
        131: "LoadToToolCompleted",
        132: "UnloadFromToolCompleted",
        136: "MappingCompleted",
        141: "PortStatusChange",
        151: "LoadStarted",
        152: "UnloadStarted",
        180: "RequestMagazineDock",
        181: "MagazineDocked",
        182: "MagazineUndocked",
        183: "RequestOperatorIdCheck",
        184: "RequestOperatorLogin",
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
        "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
        "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
    }
}

def parse_secs_data(data_lines, ceid_map):
    """Parses a list of data lines from a log entry into a structured dictionary."""
    full_text = "".join(data_lines)
    data = {}

    # --- S6F11 Event Report Parsing ---
    # Structure: <L[3] <U4 DATAID> <U4 CEID> <L[1] <L[2] <U4 RPTID> <L[n] ...data... >>>>
    s6f11_match = re.search(r"<\s*L\s*\[3\]\s*<U4\s*\[\d+\]\s*\d+>\s*<U4\s*\[\d+\]\s*(\d+)>", full_text, re.DOTALL)
    if s6f11_match:
        ceid = int(s6f11_match.group(1))
        if ceid in ceid_map:
            data['CEID'] = ceid

            # Specific data extraction based on CEID
            if ceid == 141: # PortStatusChange: <L[3] <A Clock> <U1 PortID> <A PortState>>
                match = re.search(r"<A\s*\[\d+\]\s*'(MIC|MPC|MOR|MIR)'>", full_text)
                if match: data['PortState'] = match.group(1)

            elif ceid == 120: # IDRead: <L[6] <A Clock> <A LotID> <A PanelID> <A Orientation> <U1 Result> <A Slot>>
                matches = re.findall(r"<A\s*\[\d+\]\s*'(.*?)'>", full_text)
                if len(matches) >= 4:
                    data['LotID'] = matches[1]
                    data['PanelID'] = matches[2]
                    data['Orientation'] = matches[3]
                    data['SlotInfo'] = f"Slot: {matches[4]}"

            elif ceid == 181: # MagazineDocked: <L[4] <A Clock> <U1 PortID> <A MagazineID> <A OperatorID>>
                matches = re.findall(r"<A\s*\[\d+\]\s*'(.*?)'>", full_text)
                if len(matches) >= 3:
                    data['MagazineID'] = matches[1]
                    data['OperatorID'] = matches[2]
                port_id_match = re.search(r"<U1\s*\[\d+\]\s*(\d+)>", full_text)
                if port_id_match: data['PortID'] = int(port_id_match.group(1))

            elif ceid == 102: # AlarmSet
                alarm_id_match = re.search(r"<U2\s*\[\d+\]\s*(\d+)>", full_text)
                if alarm_id_match: data['AlarmID'] = int(alarm_id_match.group(1))

    # --- S2F49 Host Command Parsing ---
    # Structure: <L[4] ... <A RCMD> <L[n] ...params... >>
    rcmd_match = re.search(r"<\s*A\s*\[\d+\]\s*'([A-Z_]{5,})'\s*>", full_text)
    if rcmd_match:
        rcmd = rcmd_match.group(1)
        if rcmd in KNOWLEDGE_BASE["rcmd_map"]:
            data['RCMD'] = rcmd

            # Extract Key-Value parameters
            param_text_match = re.search(r"(\<L\s*\[\d+\]\s*(?:\<L\s*\[2\].*?\>)+)", full_text, re.DOTALL)
            if param_text_match:
                param_text = param_text_match.group(1)
                params = re.findall(r"\<L\s*\[2\]\s*\<A\s*\[\d+\]\s*'(.*?)'\s*\>\s*\<(?:A|U\d)\s*\[\d+\]\s*'?([\w\.-]+)'?\s*\>\s*\>", param_text)
                for key, value in params:
                    data[key] = value

    return data


def generate_event_description(row, kb):
    """Generates a human-readable description for a row in the DataFrame."""
    if pd.notna(row.get('RCMD')):
        return kb['rcmd_map'].get(row['RCMD'], f"Unknown Command: {row['RCMD']}")
    if pd.notna(row.get('CEID')):
        ceid_int = int(row['CEID'])
        base_desc = kb['ceid_map'].get(ceid_int, f"Unknown Event")

        # Add context
        if ceid_int == 141: return f"{base_desc}: {row.get('PortState', 'N/A')}"
        if ceid_int == 120: return f"{base_desc}: Panel {row.get('PanelID', 'N/A')} in Slot {row.get('SlotInfo', 'N/A')}"
        if ceid_int == 181: return f"{base_desc}: Magazine {row.get('MagazineID', 'N/A')} by Operator {row.get('OperatorID', 'N/A')}"
        if ceid_int == 102: return f"{base_desc}: ALID {row.get('AlarmID', 'N/A')}"
        return base_desc
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
            i += 1
            continue

        timestamp, log_type, message_part = match.groups()

        direction = "Equipment to Host" if "Core:Send" in log_type else "Host to Equipment" if "Core:Receive" in log_type else "System"
        msg_name_match = re.search(r"MessageName=(\w+)|Message=.*?S\dF\d+:?'(\w+)'", message_part)
        msg_name = msg_name_match.group(1) or msg_name_match.group(2) if msg_name_match else None

        entry = {"Timestamp": timestamp, "Direction": direction, "Message": msg_name}

        data_block_lines = []
        if "Core:Send" in log_type or "Core:Receive" in log_type:
            if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
                j = i + 1
                while j < len(lines) and lines[j].strip() != '.':
                    data_block_lines.append(lines[j])
                    j += 1
                i = j

        if data_block_lines:
            parsed_details = parse_secs_data(data_block_lines, knowledge_base['ceid_map'])
            entry.update(parsed_details)

        # Add raw data for every entry that has a message body
        if data_block_lines:
            entry['RawData'] = " ".join("".join(data_block_lines).split())

        parsed_data.append(entry)
        i += 1

    if not parsed_data:
        return pd.DataFrame()

    df = pd.DataFrame(parsed_data)

    # --- Data Cleaning and Typing ---
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Simple Description'] = df['Message'].map(knowledge_base['secs_map'])
    df['Event'] = df.apply(lambda row: generate_event_description(row, knowledge_base), axis=1)

    # Coerce numeric types, converting errors to NaT/NaN
    for col in ['PortID', 'AlarmID', 'CEID']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Final column selection and ordering
    final_cols = [
        "Timestamp", "Direction", "Message", "Simple Description", "Event", "AlarmID",
        "PortID", "PortState", "MagazineID", "OperatorID", "LotID", "PanelID",
        "SlotInfo", "Orientation", "RawData"
    ]
    for col in final_cols:
        if col not in df.columns:
            df[col] = None

    return df[final_cols]