from state.state_schema import AgentState
from utils.gemini_client import gemini_chat
import textwrap
import re

def clean_sql(sql: str) -> str:
    sql = sql.strip()
    sql = re.sub(r'^```sql\s*|\s*```$', '', sql, flags=re.DOTALL)
    sql = re.sub(r'^```\s*|\s*```$', '', sql, flags=re.DOTALL)
    return sql.strip().rstrip(';')

def nl_to_sql_agent(state: AgentState) -> AgentState:
    if not state.raw_text:
        state.error = "❌ No user query found in `raw_text`."
        return state

    if not state.table_name:
        state.error = "❌ No table name found in `table_name`."
        return state

    # ✅ Use engineered prompt if available
    if getattr(state, "engineered_prompt", None):
        prompt = state.engineered_prompt
    else:
        columns = state.original_names or []
        column_display = "\n".join([f'- "{col}"' for col in columns])
        prompt = textwrap.dedent(f"""
        You are a PostgreSQL expert.

        Convert the following natural language question into a valid SQL query.

        Table: "{state.table_name}"

        Column Names (quoted exactly as used in the database):
        {column_display}

        Rules:
        1. Use the exact table name: "{state.table_name}"
        2. Always use quoted column names (e.g., "Net Value", "Item", "Doc. Date")
        3. DO NOT use placeholders like 'your_table_name'
        4. DO NOT use window functions (e.g., LAG, LEAD) directly in the WHERE clause.
           Instead, calculate them in a CTE or subquery and filter in the outer SELECT.
        5. Return only the raw SQL. No explanations. No markdown formatting.
        

        Important: Column names may have leading/trailing spaces. Use them exactly as listed.

        Question: {state.raw_text}

        SQL:
        """)

    try:
        raw_sql = gemini_chat(prompt)
        cleaned_sql = clean_sql(raw_sql)

        if not cleaned_sql or not any(cleaned_sql.lower().startswith(kw) for kw in ("select", "with")):
            state.error = f"❌ Invalid SQL:\n{raw_sql}"
            return state

        state.display_preview = cleaned_sql
        return state
    except Exception as e:
        state.error = f"❌ SQL generation failed: {str(e)}"
        return state


