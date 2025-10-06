Project Brief: Streamlit Application for Hirata Loadport Log Analysis

Objective & Target Audience
The goal is to create a web-based Streamlit application that automates the analysis of Hirata Front End Loadport communication logs (.txt files). This tool will serve as a primary diagnostic and monitoring utility for:

Maintenance Managers: To get a high-level summary of equipment health, identify alarms, and understand operational timelines.

Process & Equipment Engineers: To perform deep-dive analysis of process flows, verify correct SECS/GEM communication sequences, and establish performance baselines.

Field Service Engineers: To quickly diagnose issues on-site without manually parsing complex log files.

The application must transform a raw, verbose log file into an intuitive, multi-layered dashboard that presents both a high-level summary and granular, searchable data.

User Workflow
The user experience should be simple and direct:

Launch: The user navigates to the Streamlit app URL.

Upload: The user is greeted with a clear title and a file uploader widget. They will upload a single log file (e.g., Mess_3.txt, Mess_4.txt).

Automatic Processing: Upon upload, the application immediately and automatically parses the entire log file in the background.

View Analysis: The results are instantly displayed on the page in a structured, multi-section format (details below).

Download Reports: The user has the option to download two separate files:

A detailed CSV file containing all parsed data, with each piece of information in its own column.

A formatted Text file (.txt) containing the high-level summary, KPIs, and action plan.

Core Functional Requirements
3.1. Log File Parsing Engine

This is the heart of the application. The Python backend must be able to read the uploaded .txt file and extract the following information for every significant SECS/GEM message, organizing it into a structured format (like a pandas DataFrame):

Timestamp: The full timestamp of the message (YYYY/MM/DD HH:MM:SS.ffffff).

Direction: "Equipment to Host" or "Host to Equipment".

Message: The SECS message name (e.g., S1F13, S6F11).

Transaction ID: The unique ID for the message pair.

Event: A human-readable name for the event (e.g., PortStatusChange, AlarmSet, Command: LOADSTART).

Clock: Any timestamp found within the message body.

Port ID: The port number involved in the operation (e.g., 1, 2).

Port State: The reported state of the port (e.g., MIC, MPC, MOR, MIR).

Magazine ID: The ID of the magazine being handled (e.g., M70256).

Operator ID: The ID of the operator who logged in (e.g., 59146).

Lot ID: The Lot ID for the panels being processed.

Panel ID: The specific ID of an individual panel.

Slot Info: For mapping events, a summary (e.g., "Panels: 24 of 24"). For panel moves, the specific slot number.

Source Port ID & Dest Port ID: For transfer commands.

Orientation: The panel orientation (e.g., 'Front').

Alarm ID: The numeric code of any triggered alarm.

Raw Data: A "catch-all" column for the text content of any message body that doesn't fit the specific parsing rules, ensuring no data is ever lost.

3.2. Streamlit User Interface & Display

The results should be displayed in a clean, multi-section dashboard:

Section 1: Executive Summary: A text section at the top that provides an automated, high-level assessment.

If alarms are present: It should state that the equipment is in a fault state and highlight the priority as "High."

If no alarms are present: It should state that the process was successful and represents a "Golden Run."

Section 2: Key Performance Indicators (KPIs): A clear dashboard section displaying calculated metrics. This requires the script to find start/end events and calculate the duration.

Total Cycle Time: (e.g., from LOADSTART command to LoadToToolCompleted).

Mapping Time: (e.g., from MIC port state to MappingCompleted event).

Average Time Per Panel: (Total cycle time divided by the number of panels processed).

Section 3: Summary Report & Action Plan: Display the full, formatted text of the maintenance report. This should be the same content that gets saved to the downloadable .txt file.

Section 4: Detailed Event Log: Display the complete, parsed data in an interactive table (use st.dataframe). The user must be able to sort and filter this table to investigate specific events.

Section 5: Download Buttons: Prominent buttons to download:

Download Full Report (.csv)

Download Summary (.txt)

Reference Guide for Parsing Logic: The Hirata Specification Document (PDF)
The developer must use the "Standard Online Specification Document" as the primary reference to build the parsing logic. This document is the source of truth for understanding the log file.

Key Information to Extract from the PDF:

Message Definitions (Streams & Functions): The script must map SxFx codes to their meanings.

Example: S1F13 is an "Establish Communication Request" (Page 67). S6F11 is an "Event Report Send" (Page 82). S2F49 is an "Enhanced Remote Command" (Page 77).

Data Dictionaries (CEID, RPTID, SVID, etc.): This is the most critical part. The parsing engine must use the tables in the PDF to translate codes into meaningful data.

Example: On Page 92, the PDF defines CEID 102 as AlarmSet and CEID 141 as PortStatusChange. The script must contain a mapping of these codes.

Data Structures: The PDF explains the structure of the data within the message bodies.

Example: The structure for an AlarmSet event report implies that the data will contain an ALID (Alarm ID). The script must be written to look for this specific data type (U2) after identifying a CEID 102 event.

Example: For S2F49 (Host Command), the PDF on Pages 122-127 details the possible command names (RCMD) and their parameters (CPNAME and CEPVAL). The script must parse these key-value pairs (e.g., 'LOTID', 'SRCPORTID').

Handling External References: The PDF occasionally refers to external documents.

Example: On Page 114, the detailed list of Alarm IDs (ALID) is noted to be in a "separate volume." The script should be designed so that new Alarm IDs and their text descriptions can be easily added to a dictionary or configuration file in the future.

Technical Stack
Language: Python

Framework: Streamlit

Libraries: pandas (for data handling and creating the DataFrame), and standard Python libraries (re, csv, datetime). No external libraries that require complex installation (like python-docx) should be used.

This detailed prompt provides a complete blueprint for the application. It defines the goal, the user, the workflow, the specific data to be extracted, the source of truth for the logic, and the final presentation.

"FOR REFERENCE I HAVE ADDED ONE LOG FILE AOP101ULD.txt"

IF YOU NEED CLARIFICATION PLEASE AKS# Log_Data_Analysis
