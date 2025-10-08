# -*- coding: utf-8 -*-
"""
Log Parsing Logic for Hirata Loadport Log Analyzer.
This module contains functions to parse log content into structured data.
"""
import re
from src.knowledge_base import KNOWLEDGE_BASE

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

def load_and_parse_log(log_content, knowledge_base):
    """
    Parses the entire log content into a structured list of events,
    focusing only on message blocks that contain data.
    """
    events = []
    lines = log_content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Find the start of a message block
        match = re.match(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d+),\[([^\]]+)\],(.*)", line)
        if not match:
            i += 1
            continue

        timestamp, log_type, message_part = match.groups()

        # Check if this line indicates a data payload is coming
        if "Core:Send" in log_type or "Core:Receive" in log_type:
            msg_name_match = (re.search(r"Message=.*?:'(\w+)'", message_part) or re.search(r"MessageName=(\w+)", message_part))
            msg_name = msg_name_match.group(1) if msg_name_match else "N/A"

            # Look ahead for the data block
            if i + 1 < len(lines) and lines[i+1].strip().startswith('<'):
                data_block_lines = []
                j = i + 1
                # Collect all lines of the data block until the '.' terminator
                while j < len(lines) and not lines[j].strip() == '.':
                    data_block_lines.append(lines[j].strip())
                    j += 1

                # If we found a data block, parse it
                if data_block_lines:
                    data = parse_secs_data(data_block_lines, knowledge_base['ceid_map'])
                    # Only create an event if the parser found meaningful data
                    if data:
                        events.append({
                            "timestamp": timestamp,
                            "msg_name": msg_name,
                            "data": data
                        })
                # Advance the main loop counter past the processed data block
                i = j
            else:
                i += 1
        else:
            i += 1

    return events