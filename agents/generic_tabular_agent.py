import pandas as pd
from state.state_schema import AgentState
from pathlib import Path

def generic_tabular_agent(state: AgentState) -> AgentState:
    """
    Loads CSV or Excel files into a DataFrame and updates state.
    """
    try:
        path = state.file_path

        if state.file_type == "csv":
            df = pd.read_csv(path)

        elif state.file_type in {"xls", "xlsx", "excel"}:
            df = pd.read_excel(path)

        else:
            state.error = "⚠️ Unsupported format for tabular load."
            return state

        # Update state
        state.internal_data = df
        state.data_frame = df
        state.display_preview = df.head(10).to_markdown(index=False)

    except Exception as e:
        state.error = f"Generic Tabular Agent Error: {str(e)}"

    return state
