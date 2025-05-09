import pandas as pd
from state.state_schema import AgentState

def dynamic_table_reconstruction_agent(state: AgentState) -> AgentState:
    """
    Reconstructs a table using a user-specified header row from detected_tables.
    """
    try:
        if not state.detected_tables or len(state.detected_tables) == 0:
            state.error = "⚠️ No detected tables to reconstruct."
            return state

        if state.selected_table_index is None or not isinstance(state.selected_table_index, int):
            state.error = "⚠️ No table selected for reconstruction."
            return state

        if state.selected_header_row is None or not isinstance(state.selected_header_row, int):
            state.error = "⚠️ No header row selected."
            return state

        # ✅ Safety check
        if state.selected_table_index >= len(state.detected_tables):
            state.error = "⚠️ Selected table index out of range."
            return state

        selected_entry = state.detected_tables[state.selected_table_index]
        df = selected_entry.get("table")

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            state.error = "⚠️ Selected table is empty or invalid."
            return state

        if state.selected_header_row >= len(df):
            state.error = "⚠️ Selected header row index exceeds table length."
            return state

        # ✅ Reconstruct
        new_header = df.iloc[state.selected_header_row].astype(str)
        reconstructed_df = df.iloc[state.selected_header_row + 1:].copy()
        reconstructed_df.columns = new_header
        reconstructed_df.reset_index(drop=True, inplace=True)

        # ✅ Save to state
        state.data_frame = reconstructed_df
        state.display_preview = reconstructed_df.head(10).to_markdown(index=False)
        state.error = None

    except Exception as e:
        state.error = f"Dynamic Table Reconstruction Error: {str(e)}"

    return state
