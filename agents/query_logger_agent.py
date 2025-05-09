 # agents/query_logger_agent.py

# from state.state_schema import AgentState
# from datetime import datetime

# def query_logger_agent(state: AgentState) -> AgentState:
#     if state.query_history is None:
#         state.query_history = []

#     record = {
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "sql": state.display_preview or "N/A",
#         "columns": list(state.internal_data.columns) if hasattr(state.internal_data, "columns") else []
#     }

#     state.query_history.append(record)
#     return state

#     print(f"\n🤖 Agent: 📜 Query Logger 📜")
#     print(f"🔹 Input: table_name={state.table_name}, question={state.raw_text}")
#     print(f"🧪 Output keys: {list(state.dict().keys())}")


from state.state_schema import AgentState
from datetime import datetime

def query_logger_agent(state: AgentState) -> AgentState:
    if not state.display_preview:
        return state  # Skip if no SQL generated

    history_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question": state.raw_text,
        "sql": state.display_preview,
        "columns": list(state.internal_data.columns) if hasattr(state.internal_data, 'columns') else [],
        "row_count": len(state.internal_data) if hasattr(state.internal_data, '__len__') else 0
    }

    if not state.query_history:
        state.query_history = []

    state.query_history.append(history_entry)
    return state
    print(f"\n🤖 Agent: 📜 Query Logger 📜")
    print(f"🔹 Input: table_name={state.table_name}, question={state.raw_text}")
    print(f"🧪 Output keys: {list(state.dict().keys())}")
