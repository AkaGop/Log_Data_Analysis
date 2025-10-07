# -*- coding: utf-8 -*-
"""
Module: app.py
Description: The main Streamlit application for Hirata log analysis.
Author: Jules
"""

import streamlit as st
import pandas as pd
import os
from io import StringIO
from parser import load_and_parse_log, KNOWLEDGE_BASE
from analysis import calculate_kpis, generate_summary_report

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
        kpis = calculate_kpis(df)
        summary_text = generate_summary_report(df)

        # --- UI Sections ---

        # Section 1: Executive Summary
        st.header("Executive Summary")
        if "fault state" in summary_text:
            st.error("Equipment is in a fault state. Priority: High.")
        else:
            st.success("Process was successful. This represents a 'Golden Run.'")

        # Section 2: Key Performance Indicators (KPIs)
        st.header("Key Performance Indicators (KPIs)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cycle Time", kpis['total_cycle_time'])
        col2.metric("Mapping Time", kpis['mapping_time'])
        col3.metric("Average Time Per Panel", kpis['avg_time_per_panel'])

        if kpis['total_cycle_time'] == 'N/A':
            st.info("Note: Total Cycle Time and Average Time Per Panel could not be calculated. A complete 'MagazineDocked' to 'UnloadFromToolCompleted' cycle was not found in this log.")

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