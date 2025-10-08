# -*- coding: utf-8 -*-
"""
Centralized Knowledge Base for Hirata Loadport Log Analyzer.
This file contains mappings and definitions derived from Hirata manuals.
"""

KNOWLEDGE_BASE = {
    # Source: Page 92-94 of Specification Document
    "ceid_map": {
        7: "GemOpCommand",
        11: "GemEquipmentOFFLINE",
        12: "GemControlStateLOCAL",
        13: "GemControlStateREMOTE",
        16: "GemPPChangeEvent",
        30: "GemProcessStateChange",
        101: "AlarmClear",
        102: "AlarmSet",
        120: "IDRead",
        121: "UnloadedFromMag",
        122: "LoadedToMag",
        126: "UnloadedFromTool",
        127: "LoadedToTool",
        128: "PP-Selected",
        131: "LoadToToolCompleted",
        132: "UnloadFromToolCompleted",
        133: "MagToMagCompleted",
        134: "MagCheckedCompleted",
        136: "MappingCompleted",
        141: "PortStatusChange",
        142: "IDReaderStateChanged",
        143: "DriveStateChange",
        151: "LoadStarted",
        152: "UnloadStarted",
        153: "MagToMagStarted",
        154: "MagCheckStarted",
        156: "CheckSlotStarted",
        161: "PortCMDCanceled",
        180: "RequestMagazineDock",
        181: "MagazineDocked",
        182: "MagazineUndocked",
        183: "RequestOperatorIdCheck",
        184: "RequestOperatorLogin",
        185: "RequestMappingCheck",
        187: "ESDRead",
        188: "DEFRead",
        192: "BufferCapacityChanged",
        193: "BufferModeChanged",
        194: "LoadedToBufferShuttle1",
        195: "LoadedToBufferShuttle2",
        196: "UnloadedFromToolShuttle1",
        197: "UnloadedFromBufferShuttle2",
        198: "MappingCompletedShuttle1",
        199: "MappingCompletedShuttle2",
    },

    # Source: Page 121-128
    "rcmd_map": {
        "LOADSTART": "Command to start loading panels from a magazine to the tool.",
        "UNLOADSTART": "Command to start unloading panels from the tool to a magazine.",
        "CHECKMAG": "Command to check a magazine by pulling out, reading ID, and returning panels.",
        "TRANSFERMAGTOMAG": "Command to transfer panels from one magazine to another.",
        "STOP": "Command to stop the current process cycle.",
        "PAUSE": "Command to pause the current process cycle.",
        "RESUME": "Command to resume a paused process cycle.",
        "CHECKSLOT": "Command to instruct the equipment to perform a slot map scan.",
        "REPLYOPERATORLOGIN": "Host's acknowledgement of an operator login event.",
        "REPLYMAGAZINEDOCK": "Host's acknowledgement of a magazine dock event.",
        "REPLYOPERATORIDCHECK": "Host's acknowledgement of an operator ID check.",
        "REPLYMAPPINGCHECK": "Host's acknowledgement of a mapping check event.",
    },

    # Source: Page 53-54
    "secs_map": {
        "S1F1": "Are You There Request", "S1F2": "Are You There Data",
        "S1F3": "Selected Equipment Status Request", "S1F4": "Selected Equipment Status Data",
        "S2F31": "Date and Time Request", "S2F32": "Date and Time Data",
        "S2F49": "Enhanced Remote Command", "S2F50": "Enhanced Remote Command Acknowledge",
        "S5F1": "Alarm Report Send", "S5F2": "Alarm Report Acknowledge",
        "S6F11": "Event Report Send", "S6F12": "Event Report Acknowledge",
        "S9F1": "Unrecognized Device ID", "S9F3": "Unrecognized Stream Type",
        "S9F5": "Unrecognized Function Type", "S9F7": "Illegal Data",
    },

    # Source: Page 38
    "port_state_map": {
        "MIR": "Magazine In Ready (Ready to load magazine)",
        "MIC": "Magazine In Complete (Magazine is loaded and locked)",
        "MPC": "Mapping Complete (Panel presence check is done)",
        "MOR": "Magazine Out Ready (Ready to unload magazine)",
        "OOS": "Out of Service",
    },
    
    # Source: Page 110
    "id_read_result_map": {
        "0": "Success (OK)",
        "1": "Read Failure (NG)",
        "2": "Top/Bottom Mismatch",
        "3": "Bad Panel",
        "4": "Unknown Panel ID",
        "5": "Timeout",
        "8": "Duplicate Panel ID",
        "16": "PanelID/Slot Mismatch",
        "32": "Destination Slot Full",
        "128": "Resume Continue",
    },

    # ALID (Alarm ID) Map - Mappings extracted from log file analysis.
    # Descriptions are generic placeholders until spec is available.
    "alid_map": {
        2: "Alarm Value 2",
        18: "Alarm Value 18",
        101: "Alarm 101 (Set/Clear)",
        1001: "Load Port Interlock Error",
        1002: "Emergency Stop Activated",
        1003: "Panel Jammed in Shuttle",
        2001: "ID Reader Communication Failure",
    },

    # SVID (Status Variable ID) Map - Mappings extracted from log file analysis.
    # Descriptions are inferred from CEID map or are generic placeholders.
    "svid_map": {
        122: "LoadedToMag or UnloadedFromTool",
        123: "Mapping Data Information",
        124: "Unload Operation Info",
        125: "Panel Information",
        141: "PortStatusChange",
        150: "Magazine Dock Request Info",
        151: "Load Operation Info",
        152: "Unload Operation Info",
        180: "RequestMagazineDock",
        181: "MagazineDocked",
        182: "MagazineUndocked",
        183: "RequestOperatorIdCheck",
    }
}
