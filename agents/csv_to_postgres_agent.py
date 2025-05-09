# csv_to_postgres_agent.py
import pandas as pd
import psycopg2
from state.state_schema import AgentState
import os

def infer_table_name(file_path: str) -> str:
    base = os.path.basename(file_path)
    return os.path.splitext(base)[0].replace(" ", "_").replace("-", "_").lower()

def check_table_exists(conn, table_name: str) -> bool:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            );
        """, (table_name,))
        return cursor.fetchone()[0]

def create_table_from_dataframe(conn, df: pd.DataFrame, table_name: str):
    with conn.cursor() as cursor:
        columns = ", ".join([f'"{col}" TEXT' for col in df.columns])
        cursor.execute(f'CREATE TABLE "{table_name}" ({columns});')

        for _, row in df.iterrows():
            values = tuple(row.astype(str).fillna("").tolist())
            placeholders = ", ".join(["%s"] * len(values))
            cursor.execute(f'INSERT INTO "{table_name}" VALUES ({placeholders})', values)
    conn.commit()

def csv_to_postgres_agent(state: AgentState) -> AgentState:
    try:
        table_name = infer_table_name(state.file_path)
        state.table_name = table_name

        if state.file_type == "csv":
            df = pd.read_csv(state.file_path)
        elif state.file_type == "xlsx":
            df = pd.read_excel(state.file_path)
        else:
            state.error = "Unsupported file type"
            return state

        state.column_names = [col.strip() for col in df.columns]
        state.original_names = df.columns.tolist()

        conn = psycopg2.connect(
            dbname="analyticbot",
            user="yavar",
            password="",
            host="localhost",
            port="5432"
        )

        if not check_table_exists(conn, table_name):
            create_table_from_dataframe(conn, df, table_name)
            state.chat_response = f"✅ Table '{table_name}' created and populated."
        else:
            state.chat_response = f"ℹ️ Table '{table_name}' already exists. Skipping creation."

        conn.close()
        return state

    except Exception as e:
        state.error = f"❌ CSV to PostgreSQL conversion failed: {str(e)}"
        return state
