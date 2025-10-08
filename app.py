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
from knowledge_base import KNOWLEDGE_BASE
from parser import load_and_parse_log
from reporting import generate_chronological_report, generate_csv_report

@st.cache_data
def analyze_log_file(log_content, filename):
    """
    Cached function to perform all heavy analysis on the log file.
    This function's output is cached by Streamlit.
    """
    events = load_and_parse_log(log_content)
    if not events:
        return None, None
    
    chronological_report = generate_chronological_report(events)
    detailed_df = generate_csv_report(events)
    return chronological_report, detailed_df

def main():
    """Main execution block for the Streamlit application."""
    st.set_page_config(layout="wide")
    st.title("Hirata Loadport Log Analyzer")
    st.markdown("Upload a log file to see a detailed, chronological breakdown of all equipment operations.")

    uploaded_file = st.file_uploader("Upload a Hirata Loadport Log File", type=['txt', 'log'])

    if uploaded_file is not None:
        log_filename = uploaded_file.name
        
        try:
            log_content = uploaded_file.getvalue().decode('utf-8')
        except UnicodeDecodeError:
            st.error("File Read Error: The uploaded file is not a valid UTF-8 encoded text file. Please check the file format and re-upload.")
            return

        with st.spinner(f"Analyzing {log_filename}... (First analysis may take a moment)"):
            try:
                chronological_report, detailed_df = analyze_log_file(log_content, log_filename)
            except Exception as e:
                st.error(f"An unexpected error occurred during log analysis: {e}")
                st.warning("The log file may have an unexpected format. Please verify the file is a valid Hirata Loadport log.")
                return

        if not chronological_report:
            st.error("Analysis complete, but no valid SECS/GEM events were found in the log file.")
            return

        st.success("Analysis Complete!")
        st.subheader("Chronological Operation Report")
        st.text_area(
            "Sequence of Events",
            chronological_report,
            height=500
        )
        st.download_button(
            "Download Report (.txt)",
            chronological_report,
            f"{os.path.splitext(log_filename)[0]}_chronological_report.txt",
            "text/plain"
        )

        st.subheader("Detailed Event Data (CSV)")
        st.dataframe(detailed_df)
        st.download_button(
            "Download Detailed Data (.csv)",
            detailed_df.to_csv(index=False).encode('utf-8'),
            f"{os.path.splitext(log_filename)[0]}_detailed_report.csv",
            "text/csv"
        )

if __name__ == "__main__":
    main()
