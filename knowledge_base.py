# -*- coding: utf-8 -*-
"""
Module: knowledge_base.py
Description: Contains static data mappings for the Hirata log parser.
Author: Jules
"""

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
        "S1F1": "Are You There Request",
        "S1F2": "Are You There Data",
        "S2F31": "Date and Time Request",
        "S2F32": "Date and Time Data",
        "S6F11": "Event Report Send",
        "S6F12": "Event Report Acknowledge",
        "S2F49": "Enhanced Remote Command",
        "S2F50": "Enhanced Remote Command Acknowledge",
    }
}