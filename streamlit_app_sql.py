from sqlmain import sql_app
import streamlit as st
import psycopg2
import pandas as pd
import tempfile
import json
from state.state_schema import AgentState
from agents.csv_to_postgres_agent import csv_to_postgres_agent
from agents.semantic_inference_agent import semantic_inference_agent

# ✅ Instantiate graph
app = sql_app()

# --- DB Utilities ---
def get_existing_tables():
    try:
        conn = psycopg2.connect(dbname="analyticbot", user="yavar", password="", host="localhost", port="5432")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)
        return sorted(row[0] for row in cursor.fetchall())
    except Exception as e:
        print(f"❌ Failed to fetch tables: {e}")
        return []

def get_table_preview(table_name):
    try:
        conn = psycopg2.connect(dbname="analyticbot", user="yavar", password="", host="localhost", port="5432")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        schema = cursor.fetchall()
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 5')
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        return schema, pd.DataFrame(rows, columns=colnames)
    except Exception as e:
        print(f"❌ Table preview failed: {e}")
        return [], pd.DataFrame()

# --- App Setup ---
st.set_page_config("Z Transact | SAP Data Analyst Agent", layout="wide")
st.title("📊 Z Transact: Data Analyst Agent")

if "state" not in st.session_state:
    st.session_state.state = AgentState()
state = st.session_state.state

# --- Upload File ---
uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])
if uploaded_file:
    file_type = "csv" if uploaded_file.name.endswith(".csv") else "xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
        tmp.write(uploaded_file.read())
        temp_file_path = tmp.name

    state.file_path = temp_file_path
    state.file_type = file_type
    state.original_name = uploaded_file.name
    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("📥 Convert to PostgreSQL Table"):
        result_state = csv_to_postgres_agent(state)
        if result_state.error:
            st.error(result_state.error)
        else:
            st.success(f"✅ File converted to table: `{result_state.table_name}`")
            st.session_state.state = result_state

# --- Sidebar Table Selection ---
st.sidebar.header("📚 Choose a Table")
available_tables = get_existing_tables()
selected_table = st.sidebar.selectbox("Available Tables", available_tables)

if selected_table:
    state.table_name = selected_table
    schema, sample_df = get_table_preview(selected_table)
    if schema:
        state.column_names = [col[0] for col in schema]
        state.original_names = [col[0] for col in schema]
        st.sidebar.subheader("📊 Table Schema")
        st.sidebar.dataframe(pd.DataFrame(schema, columns=["Column", "Type", "Nullable"]), height=200)

    if not sample_df.empty:
        state.internal_data = sample_df
        st.sidebar.subheader("🧾 Sample Data")
        st.sidebar.dataframe(sample_df, height=200)

    if st.sidebar.button("🧠 Infer Column Semantics"):
        state = semantic_inference_agent(state)
        if state.error:
            st.error(state.error)
        else:
            st.success("✅ Semantic schema generated.")
            st.sidebar.json(state.semantic_schema)

# --- NL to SQL Analysis ---
st.markdown("---")
question = st.text_area("💬 Ask a question about your data:", "Show items with zero value")

if st.button("🚀 Run Analysis"):
    if not state.table_name:
        st.error("❌ Please select or upload a table first.")
    else:
        state.raw_text = question
        final_state = app.invoke(state)
        state = final_state if isinstance(final_state, AgentState) else AgentState(**final_state)

        if state.error:
            st.error(state.error)
        else:
            st.subheader("🧾 Final SQL")
            st.code(state.display_preview or "No SQL generated", language="sql")

            st.subheader("📊 Query Result")
            if isinstance(state.internal_data, pd.DataFrame) and not state.internal_data.empty:
                st.dataframe(state.internal_data)
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.download_button("📥 Download CSV", state.internal_data.to_csv(index=False), "result.csv")
                with col2:
                    st.download_button("📥 Download JSON", state.internal_data.to_json(orient="records"), "result.json")
            else:
                st.info("No data returned.")

            # --- Validation Display ---
            st.markdown("### ✅ Validation")
            if hasattr(state, "validation_report") and state.validation_report:
                st.markdown(
                    f"<div style='padding: 0.5rem; background-color: black; border-radius: 5px; border-left: 4px solid #28a745;'>"
                    f"<pre style='white-space: pre-wrap; word-break: break-word;'>{state.validation_report}</pre></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info("No validation available.")

            # --- Explanation Display ---
            st.markdown("### 🧠 Explanation")
            if hasattr(state, "explanation_report") and state.explanation_report:
                st.markdown(
                    f"<div style='padding: 0.5rem; background-color: black; border-radius: 5px; border-left: 4px solid #ffc107;'>"
                    f"<pre style='white-space: pre-wrap; word-break: break-word;'>{state.explanation_report}</pre></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info("No explanation available.")

# --- History Tab ---
st.markdown("---")
with st.expander("📖 Past Queries"):
    history = getattr(state, "query_history", [])
    if history:
        for i, q in enumerate(reversed(history), 1):
            st.markdown(f"**{i}. [{q['timestamp']}]** — `{q['sql'][:80]}...`")
            if q.get("columns"):
                st.caption(f"Returned Columns: {', '.join(q['columns'])}")
    else:
        st.info("No previous queries logged.")




# from sqlmain import sql_app  # Correct import
# import streamlit as st
# import psycopg2
# import pandas as pd
# import tempfile
# import os
# import json
# from state.state_schema import AgentState
# from agents.csv_to_postgres_agent import csv_to_postgres_agent
# from agents.semantic_inference_agent import semantic_inference_agent
# # ✅ Use built-in Streamlit expander
# from streamlit import expander


# # ✅ Instantiate compiled graph
# app = sql_app()  # FIX: call to get graph object

# # --- DB Utilities ---
# def get_existing_tables():
#     try:
#         conn = psycopg2.connect(dbname="analyticbot", user="yavar", password="", host="localhost", port="5432")
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT table_name FROM information_schema.tables
#             WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
#         """)
#         tables = [row[0] for row in cursor.fetchall()]
#         cursor.close()
#         conn.close()
#         return sorted(tables)
#     except Exception as e:
#         print(f"❌ Failed to fetch tables: {e}")
#         return []

# def get_table_preview(table_name):
#     try:
#         conn = psycopg2.connect(dbname="analyticbot", user="yavar", password="", host="localhost", port="5432")
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT column_name, data_type, is_nullable 
#             FROM information_schema.columns WHERE table_name = %s
#             ORDER BY ordinal_position
#         """, (table_name,))
#         schema = cursor.fetchall()

#         cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 5')
#         rows = cursor.fetchall()
#         colnames = [desc[0] for desc in cursor.description]

#         cursor.close()
#         conn.close()
#         return schema, pd.DataFrame(rows, columns=colnames)
#     except Exception as e:
#         print(f"❌ Table preview failed: {e}")
#         return [], pd.DataFrame()

# # --- App Setup ---
# st.set_page_config("Z Transact | SAP Data Analyst Agent", layout="wide")
# st.title("📊 Z Transact: Data Analyst Agent ")

# if "state" not in st.session_state:
#     st.session_state.state = AgentState()

# state = st.session_state.state

# # --- Upload File ---
# uploaded_file = st.file_uploader("Upload CSV or Excel File", type=["csv", "xlsx"])

# if uploaded_file:
#     file_type = "csv" if uploaded_file.name.endswith(".csv") else "xlsx"
#     with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as tmp:
#         tmp.write(uploaded_file.read())
#         temp_file_path = tmp.name

#     state.file_path = temp_file_path
#     state.file_type = file_type
#     state.original_name = uploaded_file.name

#     st.success(f"Uploaded: {uploaded_file.name}")

#     if st.button("📥 Convert to PostgreSQL Table"):
#         print("🚀 Running csv_to_postgres_agent")
#         result_state = csv_to_postgres_agent(state)
#         if result_state.error:
#             st.error(result_state.error)
#         else:
#             st.success(f"✅ File converted to table: `{result_state.table_name}`")
#             st.session_state.state = result_state

# # --- Sidebar Table Selection ---
# st.sidebar.header("📚 Choose a Table")
# available_tables = get_existing_tables()
# selected_table = st.sidebar.selectbox("Available Tables", available_tables)

# if selected_table:
#     state.table_name = selected_table
#     schema, sample_df = get_table_preview(selected_table)

#     if schema:
#         state.column_names = [col[0] for col in schema]
#         state.original_names = [col[0] for col in schema]

#         st.sidebar.subheader("📊 Table Schema")
#         schema_df = pd.DataFrame(schema, columns=["Column", "Type", "Nullable"])
#         st.sidebar.dataframe(schema_df, height=200)

#     if not sample_df.empty:
#         state.internal_data = sample_df
#         st.sidebar.subheader("🧾 Sample Data")
#         st.sidebar.dataframe(sample_df, height=200)

#     if st.sidebar.button("🧠 Infer Column Semantics"):
#         print("🧠 Running semantic_inference_agent")
#         state = semantic_inference_agent(state)
#         if state.error:
#             st.error(state.error)
#         else:
#             st.success("✅ Semantic schema generated.")
#             st.sidebar.json(state.semantic_schema)


# # --- NL to SQL Analysis ---
# st.markdown("---")
# question = st.text_area("💬 Ask a question about your data:", "Show items with zero value")

# if st.button("🚀 Run Analysis"):
#     if not state.table_name:
#         st.error("❌ Please select or upload a table first.")
#     else:
#         state.raw_text = question
#         print("🧠 Invoking SQL agent workflow...")
#         final_state = app.invoke(state)
#         state = final_state if isinstance(final_state, AgentState) else AgentState(**final_state)

#         if state.error:
#             st.error(state.error)
#         else:
#             st.subheader("🧾 Final SQL")
#             st.code(state.display_preview or "No SQL generated", language="sql")

#             st.subheader("📊 Query Result")
#             if isinstance(state.internal_data, pd.DataFrame) and not state.internal_data.empty:
#                 st.dataframe(state.internal_data)

#                 col1, col2 = st.columns([1, 1])
#                 with col1:
#                     st.download_button("📥 Download CSV", state.internal_data.to_csv(index=False), "result.csv")
#                 with col2:
#                     st.download_button("📥 Download JSON", state.internal_data.to_json(orient="records"), "result.json")
#             else:
#                 st.info("No data returned.")

#             from streamlit_expander import st_expander  # optional if using expanders

#             # --- Validation Display ---
#             st.markdown("### ✅ Validation")
#             if state.validation_report:
#                 st.markdown(
#                     f"<div style='padding: 0.5rem; background-color: #f1f3f5; border-radius: 5px; border-left: 4px solid #28a745;'>"
#                     f"<pre style='white-space: pre-wrap; word-break: break-word;'>{state.validation_report}</pre></div>",
#                     unsafe_allow_html=True,
#                 )
#             else:
#                 st.info("No validation available.")

#             # --- Explanation Display ---
#             st.markdown("### 🧠 Explanation")
#             if state.explanation_report:
#                 st.markdown(
#                     f"<div style='padding: 0.5rem; background-color: #fff3cd; border-radius: 5px; border-left: 4px solid #ffc107;'>"
#                     f"<pre style='white-space: pre-wrap; word-break: break-word;'>{state.explanation_report}</pre></div>",
#                     unsafe_allow_html=True,
#                 )
#             else:
#                 st.info("No explanation available.")

            
#             # st.subheader("✅ Validation")
#             # st.markdown(f"```text\n{state.validation_report or 'No validation available.'}\n```")

#             # st.subheader("🧠 Explanation")
#             # st.markdown(f"```text\n{state.explanation_report or 'No explanation available.'}\n```")


#             # # 🔍 Split out validation and explanation
#             # st.subheader("✅ Validation")
#             # validation_text = (state.chat_response or "").split("**Explanation:**")[0].strip()
#             # st.markdown(f"```text\n{validation_text or 'No validation available.'}\n```")

#             # st.subheader("🧠 Explanation")
#             # explanation_text = ""
#             # if state.chat_response and "**Explanation:**" in state.chat_response:
#             #     explanation_text = state.chat_response.split("**Explanation:**")[-1].strip()
#             # st.markdown(f"```text\n{explanation_text or 'No explanation available.'}\n```")

# # --- History Tab ---
# st.markdown("---")
# with st.expander("📖 Past Queries"):
#     history = getattr(state, "query_history", [])
#     if history:
#         for i, q in enumerate(reversed(history), 1):
#             st.markdown(f"**{i}. [{q['timestamp']}]** — `{q['sql'][:80]}...`")
#             if q.get("columns"):
#                 st.caption(f"Returned Columns: {', '.join(q['columns'])}")
#     else:
#         st.info("No previous queries logged.")


