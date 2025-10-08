# Hirata Loadport Log Analyzer

A Streamlit web application for parsing, analyzing, and visualizing Hirata Loadport SECS/GEM communication logs. This tool transforms raw, verbose log files into an intuitive, multi-layered dashboard for rapid diagnostics and process analysis.


*(**Developer Note:** Please run the app, upload `AOP101ULD.txt`, and take a screenshot of the complete output page. Upload it to a site like [imgur.com](https://imgur.com) and replace the URL above.)*

---

## Key Features

-   **Automated Chronological Analysis:** Instantly generates a human-readable, step-by-step narrative of the entire operational sequence from a raw log file.
-   **Executive Summary:** Provides an immediate, high-level assessment of the operation, flagging it as a "Golden Run" or a "Fault State" based on alarm data.
-   **KPI Dashboard:** Automatically calculates and displays critical performance metrics like Total Cycle Time, Mapping Time, and Average Time Per Panel.
-   **Error Highlighting:** Intelligently identifies and flags anomalies, such as ID read failures and critical alarms, directly within the chronological report.
-   **Interactive Data Table:** Presents the full, granular data in a sortable and filterable table for deep-dive investigations.
-   **Dual Report Downloads:** Allows users to download both a comprehensive CSV file for further analysis and a formatted `.txt` summary for maintenance reports.
-   **Performance Optimized:** Leverages Streamlit's caching to ensure the analysis is performed only once per file, providing an instantaneous user experience.

## Target Audience

This tool is designed to serve as a primary diagnostic and monitoring utility for:

-   **Maintenance Managers:** To get a high-level summary of equipment health and operational timelines.
-   **Process & Equipment Engineers:** To perform deep-dive analysis of process flows and establish performance baselines.
-   **Field Service Engineers:** To quickly diagnose issues on-site without manually parsing complex log files.

---

## Installation

To run this application locally, ensure you have Python 3.8+ installed.

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd hirata-log-analyzer
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(**Developer Note:** Create a `requirements.txt` file by running `pip freeze > requirements.txt` in your activated virtual environment.)*

## Usage

1.  **Run the Streamlit application from your terminal:**
    ```bash
    streamlit run app.py
    ```

2.  **Open your web browser** and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

3.  **Upload a log file** (e.g., `AOP101ULD.txt`) using the file uploader.

4.  The application will automatically process the file and display the complete analysis dashboard.

---

## Project Structure

```
hirata-log-analyzer/
│
├── .gitignore
├── app.py                  # Main Streamlit application file (UI and workflow)
├── requirements.txt        # Python dependencies
├── README.md               # This file
│
└── src/
    ├── __init__.py
    ├── knowledge_base.py   # Centralized dictionary for all SECS/GEM definitions (CEIDs, RCMDs, etc.)
    ├── parser.py           # Core log parsing engine and data extraction logic
    └── reporting.py        # Generates the chronological report, KPIs, and CSV output
```

## Technical Deep Dive

The application's architecture is designed for accuracy, performance, and extensibility.

#### 1. The Knowledge Base (`knowledge_base.py`)

This module acts as the "brain" of the application. It is a centralized dictionary translated directly from the official **Hirata Specification Document**. It maps cryptic codes (e.g., CEID `141`) to human-readable information (e.g., `PortStatusChange`), ensuring that the analysis is accurate and easy to update as specifications change.

#### 2. The Modular Parser (`parser.py`)

Instead of a monolithic `if/elif/else` block, the parser uses a **dictionary dispatch pattern**. It maps specific `CEIDs` to dedicated parsing functions. This design makes the code cleaner and significantly easier to extend—adding support for a new event only requires a new, small function and a single entry in the dispatch dictionary.

#### 3. Stateful Reporting Engine (`reporting.py`)

The reporting module goes beyond simple data presentation. It uses the parsed events and the knowledge base to construct a chronological **narrative**. It understands the operational flow (e.g., `MagazineDocked` -> `MappingCompleted` -> `LOADSTART`) and can therefore calculate meaningful KPIs and highlight deviations from the expected sequence.

#### 4. Performance (`app.py`)

The entire analysis pipeline (parsing and reporting) is wrapped in a single function decorated with Streamlit's `@st.cache_data`. This ensures that for a given uploaded file, the intensive processing runs only once. All subsequent UI interactions are served from the cache, resulting in a fast and responsive user experience.

---

## Future Enhancements (Roadmap)

-   [ ] **Full SVID/ALID Mapping:** Integrate the complete lists of Status Variables and Alarms from the specification to provide even richer context.
-   [ ] **Formal State Model Tracking:** Implement a state machine to explicitly track and display the GEM `ControlState` and `ProcessingState` throughout the log.
-   [ ] **Advanced UI Filtering:** Add UI elements (multiselect, date range) to filter the detailed event log directly in the app.
-   [ ] **Visualizations:** Add charts to plot KPIs over time or visualize alarm frequency.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
