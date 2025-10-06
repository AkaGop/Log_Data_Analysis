# -*- coding: utf-8 -*-
"""
Module: app.py
Author: Jules
"""

import streamlit as st
import pandas as pd
from parser import load_and_parse_log, KNOWLEDGE_BASE
from io import StringIO
import re

def generate_summary_text(df):
    """Generates a human-readable summary report from the DataFrame."""
    summary_lines = []

    # --- Executive Summary ---
    alarms_present = not df[df['AlarmID'].notna()].empty

    summary_lines.append("### 1. EXECUTIVE SUMMARY ###")
    if alarms_present:
        summary_lines.append("The equipment is in a **fault state**. Alarms were detected during the process.")
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
    dock_events = df[df['Event'] == 'MagazineDocked']
    if not dock_events.empty:
        for _, event in dock_events.iterrows():
            summary_lines.append(f"- **{event['Timestamp']}:** Magazine '{event['MagazineID']}' was docked by operator '{event['OperatorID']}'.")

    map_complete_events = df[df['Event'] == 'MappingCompleted']
    if not map_complete_events.empty:
        summary_lines.append("- Magazine slot mapping was successfully completed.")

    load_complete_events = df[df['Event'] == 'LoadToToolCompleted']
    if not load_complete_events.empty:
        summary_lines.append("- Panel loading to the tool was completed.")

    unload_complete_events = df[df['Event'] == 'UnloadFromToolCompleted']
    if not unload_complete_events.empty:
        summary_lines.append("- Panel unloading from the tool was completed.")
    summary_lines.append("\n")

    # --- Alarms and Anomalies ---
    summary_lines.append("### 4. ANOMALY ANALYSIS & MAINTENANCE INSIGHTS ###")
    if alarms_present:
        summary_lines.append("**Alarms Detected:**")
        for _, alarm in df[df['AlarmID'].notna()].iterrows():
            summary_lines.append(f"- **{alarm['Timestamp']}:** Alarm with ID `{int(alarm['AlarmID'])}` was triggered.")
    else:
        summary_lines.append("No significant anomalies or alarms were detected.")
    summary_lines.append("\n")

    # --- Action Plan ---
    summary_lines.append("### 5. ACTIONABLE MAINTENANCE RECOMMENDATIONS ###")
    if alarms_present:
        summary_lines.append("- **Priority 1: Investigate Alarms.** Create a service ticket to investigate the cause of the triggered alarms.")
    summary_lines.append("- **Priority 2: Monitor Performance.** Track the KPIs from this report to establish performance baselines.")

    return "\n".join(summary_lines)


def main():
    """Main execution block to handle user input and run analysis."""
    st.set_page_config(layout="wide")
    st.title("Hirata Loadport Log Analysis")

    uploaded_file = st.file_uploader("Upload a log file", type="txt")

    if uploaded_file is not None:
        log_content = uploaded_file.getvalue().decode("utf-8")
        
        df = load_and_parse_log(log_content, KNOWLEDGE_BASE)
        
        if df.empty:
            st.warning("Could not find any valid events to analyze in the log file.")
            return

        st.success("File uploaded and processed successfully!")

        # --- Generate Reports ---
        summary_text = generate_summary_text(df)

        # --- UI Sections ---
        
        # Section 1: Executive Summary
        st.header("Executive Summary")
        if "fault state" in summary_text:
            st.error("Equipment is in a fault state. Priority: High.")
        else:
            st.success("Process was successful. This represents a 'Golden Run.'")

        # Section 2: Key Performance Indicators (KPIs)
        st.header("Key Performance Indicators (KPIs)")
        try:
            # Cycle Time: From first dock to last unload
            start_time = df[df['CEID'] == 181]['Timestamp'].min()
            end_time = df[df['CEID'] == 132]['Timestamp'].max()

            # Mapping Time: From port state 'MIC' to 'MappingCompleted'
            map_start_time = df[df['PortState'] == 'MIC']['Timestamp'].min()
            map_end_time = df[df['CEID'] == 136]['Timestamp'].max()

            total_cycle_time = (end_time - start_time).total_seconds() if pd.notna(start_time) and pd.notna(end_time) else "N/A"
            mapping_time = (map_end_time - map_start_time).total_seconds() if pd.notna(map_start_time) and pd.notna(map_end_time) else "N/A"

            panel_count = df[df['Event'] == 'UnloadedFromMag']['Timestamp'].count()
            avg_time_per_panel = (total_cycle_time / panel_count) if isinstance(total_cycle_time, (int, float)) and panel_count > 0 else "N/A"

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Cycle Time", f"{total_cycle_time:.2f}s" if isinstance(total_cycle_time, (int, float)) else "N/A")
            col2.metric("Mapping Time", f"{mapping_time:.2f}s" if isinstance(mapping_time, (int, float)) else "N/A")
            col3.metric("Average Time Per Panel", f"{avg_time_per_panel:.2f}s" if isinstance(avg_time_per_panel, (int, float)) else "N/A")

        except Exception as e:
            st.warning(f"Could not calculate all KPIs. This might be due to missing events in the log. Error: {e}")

        # Section 3: Summary Report & Action Plan
        st.header("Summary Report & Action Plan")
        st.markdown(summary_text)

        # Section 4: Detailed Event Log
        st.header("Detailed Event Log")
        st.dataframe(df.astype(str))

        # Section 5: Download Buttons
        st.header("Download Reports")
        
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')

        st.download_button(
            label="Download Full Report (.csv)",
            data=csv_buffer.getvalue(),
            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_report.csv",
            mime="text/csv",
        )

        st.download_button(
            label="Download Summary (.txt)",
            data=summary_text,
            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_summary.txt",
            mime="text/plain",
        )

if __name__ == "__main__":
    main()