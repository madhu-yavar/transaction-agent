# # agents/sql_executor_agent.py

# import psycopg2
# import pandas as pd
# from state.state_schema import AgentState
# from datetime import datetime

# def sql_executor_agent(state: AgentState) -> AgentState:
#     if not state.display_preview:
#         state.error = "❌ No SQL query found in `display_preview`."
#         return state

#     try:
#         conn = psycopg2.connect(
#             dbname="analyticbot",
#             user="yavar",
#             password="",
#             host="localhost",
#             port="5432"
#         )
#         cursor = conn.cursor()

#         # Strip & clean SQL
#         sql = state.display_preview.strip().rstrip(";")

#         # Execute
#         cursor.execute(sql)
#         if cursor.description:
#             data = cursor.fetchall()
#             columns = [desc[0] for desc in cursor.description]
#             df = pd.DataFrame(data, columns=columns)
#             state.internal_data = df
#         else:
#             state.internal_data = pd.DataFrame()

#         cursor.close()
#         conn.close()
#         return state

#     except Exception as e:
#         state.error = f"❌ Execution error: {str(e)}"
#         return state


from state.state_schema import AgentState
import psycopg2
import pandas as pd

def sql_executor_agent(state: AgentState) -> AgentState:
    sql = state.display_preview
    if not sql or not any(sql.lower().lstrip().startswith(kw) for kw in ("select", "with")):
        state.error = "❌ SQL query is empty or invalid. Execution aborted."
        return state

    try:
        conn = psycopg2.connect(
            dbname="analyticbot",
            user="yavar",
            password="",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute(sql.strip().rstrip(";"))

        if cursor.description:
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(data, columns=columns)
            state.internal_data = df
        else:
            state.internal_data = pd.DataFrame()

        cursor.close()
        conn.close()
        return state

    except Exception as e:
        state.error = f"❌ Execution error: {str(e)}"
        return state


    print(f"\n🤖 Agent: 🛠️ SQL Executor 🛠️")
    print(f"🔹 Input: table_name={state.table_name}, question={state.raw_text}")
    print(f"🧪 Output keys: {list(state.dict().keys())}")



