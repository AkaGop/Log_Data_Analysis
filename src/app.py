# -*- coding: utf-8 -*-
"""
Created on Fri Oct  3 14:47:38 2025

@author: Gopal
"""

# -*- coding: utf-8 -*-
"""
Hirata Loadport Log Analyzer
Streamlit application to parse and analyze Hirata Loadport communication logs.
"""
import os
import streamlit as st
from src.knowledge_base import KNOWLEDGE_BASE
from src.parser import load_and_parse_log
from src.reporting import (
    generate_chronological_report,
    generate_csv_report,
    generate_executive_summary,
    calculate_kpis
)

@st.cache_data
def analyze_log_file(log_content, filename):
    """
    Cached function to perform all heavy analysis on the log file.
    This function's output is cached by Streamlit.
    """
    events = load_and_parse_log(log_content)
    if not events:
        return None, None, None, None
    
    # Generate reports
    chronological_report = generate_chronological_report(events)
    detailed_df = generate_csv_report(events)
    executive_summary = generate_executive_summary(events)
    kpis = calculate_kpis(events, detailed_df)

    return chronological_report, detailed_df, executive_summary, kpis

def main():
    """Main execution block for the Streamlit application."""
    st.set_page_config(layout="wide")
    st.title("Hirata Loadport Log Analyzer")
    st.markdown("Upload a log file for an automated analysis, including an executive summary, KPIs, and a detailed event breakdown.")

    uploaded_file = st.file_uploader("Upload a Hirata Loadport Log File", type=['txt', 'log'])

    if uploaded_file is not None:
        log_filename = uploaded_file.name
        
        try:
            log_content = uploaded_file.getvalue().decode('utf-8')
        except UnicodeDecodeError:
            st.error("File Read Error: The uploaded file is not a valid UTF-8 encoded text file. Please check the file format and re-upload.")
            return

        with st.spinner(f"Analyzing {log_filename}... (This may take a moment)"):
            try:
                chronological_report, detailed_df, summary, kpis = analyze_log_file(log_content, log_filename)
            except Exception as e:
                st.error(f"An unexpected error occurred during log analysis: {e}")
                st.warning("The log file may have an unexpected format. Please verify it's a valid Hirata Loadport log.")
                return

        if not chronological_report:
            st.error("Analysis complete, but no valid SECS/GEM events were found in the log file.")
            return

        st.success("Analysis Complete!")

        # --- Section 1: Executive Summary & KPIs ---
        st.subheader("Executive Summary")
        st.markdown(summary)

        st.subheader("Key Performance Indicators (KPIs)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Cycle Time", kpis.get("Total Cycle Time", "N/A"))
        col2.metric("Mapping Time", kpis.get("Mapping Time", "N/A"))
        col3.metric("Panels Processed", kpis.get("Panel Count", "N/A"))
        col4.metric("Avg. Time / Panel", kpis.get("Average Time Per Panel", "N/A"))

        # --- Section 2: Chronological Report ---
        st.subheader("Chronological Operation Report")
        st.text_area(
            "Sequence of Events",
            chronological_report,
            height=400
        )
        st.download_button(
            "Download Chronological Report (.txt)",
            chronological_report,
            f"{os.path.splitext(log_filename)[0]}_chronological_report.txt",
            "text/plain"
        )

        # --- Section 3: Detailed Data Table ---
        st.subheader("Detailed Event Data")
        st.dataframe(detailed_df)
        st.download_button(
            "Download Detailed Data (.csv)",
            detailed_df.to_csv(index=False).encode('utf-8'),
            f"{os.path.splitext(log_filename)[0]}_detailed_report.csv",
            "text/csv"
        )

if __name__ == "__main__":
    main()
