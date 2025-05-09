# agents/dynamic_table_detection_agent.py
from state.state_schema import AgentState
import pandas as pd

def dynamic_table_detection_agent(state: AgentState) -> AgentState:
    try:
        print("🔎 dynamic_table_detection_agent: Checking for internal_data...")
        detected_tables = []

        if isinstance(state.internal_data, pd.DataFrame):
            print("✅ Found a DataFrame in internal_data.")
            detected_tables.append({
                "name": "Extracted Table",
                "table": state.internal_data,
                "candidate_headers": [0]  # Assume first row is best guess
            })

        elif isinstance(state.internal_data, list):
            print("✅ Found list of DataFrames.")
            for i, df in enumerate(state.internal_data):
                if isinstance(df, pd.DataFrame):
                    detected_tables.append({
                        "name": f"Extracted Table {i+1}",
                        "table": df,
                        "candidate_headers": [0]  # Update if you want better logic
                    })

        if detected_tables:
            state.detected_tables = detected_tables
            print(f"✅ Detected {len(detected_tables)} tables.")
        else:
            state.error = "⚠️ No tables detected from internal_data."
            print("❌ No tables detected.")

        if isinstance(state.internal_data, pd.DataFrame):
            print("✅ internal_data is a DataFrame.")
            
        elif isinstance(state.internal_data, list):
            print("✅ internal_data is a list.")
            for i, item in enumerate(state.internal_data):
                print(f" - Item {i} type: {type(item)} | shape: {getattr(item, 'shape', None)}")
        else:
            print(f"❌ internal_data is of type: {type(state.internal_data)}")


    except Exception as e:
        state.error = f"Dynamic Table Detection Error: {str(e)}"

    return state

