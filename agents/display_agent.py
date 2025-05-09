# agents/display_agent.py

from state.state_schema import AgentState
import pandas as pd

def display_agent(state: AgentState) -> AgentState:
    """
    Prepares a markdown preview of the loaded DataFrame (first 10 rows).
    Updates `state.display_preview` with a markdown string.
    """
    try:
        # --- Validate data_frame existence and non-emptiness ---
        if state.data_frame is None or not isinstance(state.data_frame, pd.DataFrame) or state.data_frame.empty:
            state.display_preview = "⚠️ No data available for preview."
            return state

        # --- Generate preview markdown ---
        preview_md = state.data_frame.head(10).to_markdown(index=False)
        state.display_preview = f"### 📄 Data Preview (First 10 Rows)\n\n{preview_md}"

        return state

    except Exception as e:
        state.display_preview = f"❌ Display Agent Error: {str(e)}"
        return state
