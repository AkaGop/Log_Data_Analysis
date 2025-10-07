# -*- coding: utf-8 -*-
"""
Hirata Loadport Log Analyzer
Streamlit application to parse and analyze Hirata Loadport communication logs.
"""
import os
import streamlit as st
from src.knowledge_base import KNOWLEDGE_BASE
from src.parser import load_and_parse_log
from src.reporting import generate_summary_report, generate_csv_report

def main():
    """Main execution block for the Streamlit application."""
    st.set_page_config(layout="wide")
    st.title("Hirata Loadport Log Analyzer")

    uploaded_file = st.file_uploader("Upload a Hirata Loadport Log File", type=['txt', 'log'])

    if uploaded_file is not None:
        log_content = uploaded_file.getvalue().decode('utf-8')
        log_filename = uploaded_file.name
        
        with st.spinner(f"Analyzing {log_filename}..."):
            events = load_and_parse_log(log_content, KNOWLEDGE_BASE)
            if not events:
                st.error("Could not find any valid events to analyze in the log file."); return
            summary_report_str = generate_summary_report(events, log_filename, KNOWLEDGE_BASE)
            detailed_df = generate_csv_report(events, KNOWLEDGE_BASE)

        st.success("Analysis Complete!")
        st.subheader("Analysis Summary Report")
        st.text_area("Summary", summary_report_str, height=300)
        st.download_button("Download Summary (.txt)", summary_report_str, f"{os.path.splitext(log_filename)[0]}_summary.txt", "text/plain")

        st.subheader("Detailed Event Data")
        st.dataframe(detailed_df)
        st.download_button("Download Detailed Data (.csv)", detailed_df.to_csv(index=False).encode('utf-8'), f"{os.path.splitext(log_filename)[0]}_report.csv", "text/csv")

if __name__ == "__main__":
    main()