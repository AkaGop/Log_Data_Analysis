from parser import load_and_parse_log, KNOWLEDGE_BASE
import pandas as pd

def run_test():
    """Executes the parsing logic and prints DataFrame info to test for errors."""
    try:
        # Load the log file content
        with open("AOP101ULD.txt", "r") as f:
            log_content = f.read()

        # Parse the log
        print("--- PARSING LOG ---")
        df = load_and_parse_log(log_content, KNOWLEDGE_BASE)

        if df.empty:
            print("WARNING: Parsing resulted in an empty DataFrame.")
            return

        print("SUCCESS: Log parsed. DataFrame created.")
        print("\nDataFrame Info:")
        df.info()

        print("\n--- Events Found ---")
        print(df['Event'].value_counts())

        print("\n--- Sample Data ---")
        print(df.dropna(subset=['PortState', 'MagazineID', 'LotID', 'PanelID'], how='all').head())

        print("\n--- TEST COMPLETE ---")

    except Exception as e:
        print(f"\n---!!! AN ERROR OCCURRED !!!---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()