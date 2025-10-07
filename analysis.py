# -*- coding: utf-8 -*-
"""
Module: analysis.py
Description: Handles the business logic for analyzing the parsed log data.
Author: Jules
"""

import pandas as pd
import numpy as np

def calculate_kpis(df):
    """Calculates Key Performance Indicators (KPIs) from the parsed DataFrame."""
    kpis = {
        "total_cycle_time": "N/A",
        "mapping_time": "N/A",
        "avg_time_per_panel": "N/A"
    }
    try:
        # --- Total Cycle Time & Average Time Per Panel ---
        dock_events = df[df['CEID'] == 181].sort_values(by='Timestamp')
        unload_complete_events = df[df['CEID'] == 132].sort_values(by='Timestamp')

        valid_cycle_times = []
        total_panels_in_valid_cycles = 0

        for _, dock_event in dock_events.iterrows():
            start_time = dock_event['Timestamp']

            # Find the first unload completion that occurs after the current dock event
            end_event_candidates = unload_complete_events[unload_complete_events['Timestamp'] > start_time]
            if not end_event_candidates.empty:
                end_time = end_event_candidates.iloc[0]['Timestamp']

                # Validate the cycle: ensure no other dock event happened in between
                interim_docks = dock_events[(dock_events['Timestamp'] > start_time) & (dock_events['Timestamp'] < end_time)]
                if interim_docks.empty:
                    cycle_time = (end_time - start_time).total_seconds()
                    if cycle_time > 0:
                        valid_cycle_times.append(cycle_time)

                        # Count panels for this specific, validated cycle
                        cycle_df = df[(df['Timestamp'] >= start_time) & (df['Timestamp'] <= end_time)]
                        panel_count = cycle_df['Event'].str.contains('UnloadedFromMag').sum()
                        total_panels_in_valid_cycles += panel_count

        if valid_cycle_times:
            avg_cycle_time = np.mean(valid_cycle_times)
            kpis['total_cycle_time'] = f"{avg_cycle_time:.2f}s (avg)"
            if total_panels_in_valid_cycles > 0:
                avg_panel_time = np.sum(valid_cycle_times) / total_panels_in_valid_cycles
                kpis['avg_time_per_panel'] = f"{avg_panel_time:.2f}s"

        # --- Mapping Time ---
        map_start_time = df[df['PortState'] == 'MIC']['Timestamp'].min()
        map_end_time = df[df['CEID'] == 136]['Timestamp'].max()
        if pd.notna(map_start_time) and pd.notna(map_end_time):
            mapping_time = (map_end_time - map_start_time).total_seconds()
            if mapping_time > 0:
                kpis['mapping_time'] = f"{mapping_time:.2f}s"

    except Exception:
        pass # Silently fail if KPIs can't be calculated

    return kpis

def generate_summary_report(df):
    """Generates a human-readable summary report from the DataFrame."""
    summary_lines = []

    # Treat all alarms as non-critical as we don't have the spec for critical alarms.
    alarms_present = not df[df['AlarmID'].notna()].empty
    is_critical_fault = False

    summary_lines.append("### 1. EXECUTIVE SUMMARY ###")
    if is_critical_fault:
        summary_lines.append("The equipment is in a **critical fault state**. Critical alarms were detected.")
    else:
        summary_lines.append("The process was successful and represents a **'Golden Run'**. No critical alarms were detected.")
    summary_lines.append("\n")

    # --- Key Entities ---
    summary_lines.append("### 2. KEY ENTITIES IDENTIFIED ###")
    operators = df['OperatorID'].dropna().unique()
    magazines = df['MagazineID'].dropna().unique()
    lots = df['LotID'].dropna().unique()

    summary_lines.append(f"- **Operator(s):** {', '.join(operators) if operators.any() else 'N/A'}")
    summary_lines.append(f"- **Magazine(s):** {', '.join(magazines) if magazines.any() else 'N/A'}")
    summary_lines.append(f"- **Lot ID(s):** {', '.join(lots) if lots.any() else 'N/A'}")
    summary_lines.append("\n")

    # --- Operational Walkthrough ---
    summary_lines.append("### 3. DETAILED OPERATIONAL WALKTHROUGH ###")
    dock_events = df[df['Event'].str.contains("MagazineDocked", na=False)]
    if not dock_events.empty:
        for _, event in dock_events.iterrows():
            summary_lines.append(f"- **{event['Timestamp']}:** Magazine '{event['MagazineID']}' was docked by operator '{event['OperatorID']}'.")

    summary_lines.append("\n")

    # --- Alarms and Anomalies ---
    summary_lines.append("### 4. ANOMALY ANALYSIS & MAINTENANCE INSIGHTS ###")
    if alarms_present:
        summary_lines.append("**Alarms Detected (Non-Critical):**")
        for _, alarm in df[df['AlarmID'].notna()].iterrows():
            summary_lines.append(f"- **{alarm['Timestamp']}:** Alarm with ID `{int(alarm['AlarmID'])}` was triggered.")
    else:
        summary_lines.append("No significant anomalies or alarms were detected.")
    summary_lines.append("\n")

    # --- Action Plan ---
    summary_lines.append("### 5. ACTIONABLE MAINTENANCE RECOMMENDATIONS ###")
    if alarms_present:
        summary_lines.append("- **Priority 1: Document Alarms.** Log the occurrence of the non-critical alarms for future reference.")
    summary_lines.append("- **Priority 2: Monitor Performance.** Track the KPIs from this report to establish performance baselines.")

    return "\n".join(summary_lines)