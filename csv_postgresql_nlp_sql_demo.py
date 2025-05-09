### Postgresql - NLP - SQL - Analytics bot
import streamlit as st
import psycopg2
import pandas as pd
import google.generativeai as genai
import textwrap
import re
from datetime import datetime

# Configure Gemini
genai.configure(api_key="AIzaSyAe8rheF4wv2ZHJB2YboUhyyVlM2y0vmlk")

def _make_unique_columns(columns):
    seen = {}
    unique = []
    for col in columns:
        base = col.strip()
        count = seen.get(base, 0)
        if count > 0:
            new_col = f"{base}_{count}"
        else:
            new_col = base
        unique.append(new_col)
        seen[base] = count + 1
    return unique

class GeminiDBAgent:
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = self._establish_connection()
        self.table_name = "Purchase_Report _1000_astral"
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.query_history = []
        self.max_retries = 3
        self.schema = self._sanitize_schema(self._get_table_schema())

    def _establish_connection(self):
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")
            return None

    def _test_connection(self):
        if self.conn is None or self.conn.closed:
            self.conn = self._establish_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except:
            return False

    def _get_table_schema(self):
        if not self._test_connection():
            return None
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (self.table_name.strip('"'),))
                schema = cursor.fetchall()

                cursor.execute(f'SELECT * FROM "{self.table_name}" LIMIT 3')
                sample_data = cursor.fetchall()

            return {
                'schema': schema,
                'sample_data': sample_data
            }
        except Exception as e:
            st.error(f"Schema fetch failed: {str(e)}")
            return None

    def _sanitize_schema(self, schema):
        if not schema:
            return None
        return {
            'schema': schema['schema'],
            'sample_data': schema['sample_data'],
            'column_names': [col[0].strip() for col in schema['schema']],
            'original_names': [col[0] for col in schema['schema']]
        }
    
    def generate_valid_sql(self, question):
        """Retry SQL generation and validation"""
        for attempt in range(self.max_retries):
            sql = self.generate_sql(question)
            if not sql:
                continue

            validation = self._validate_sql(question, sql)
            if "VALID:" in validation:
                return sql, validation

        return None, "Max validation attempts reached or all SQLs invalid"    

    def _validate_sql(self, question, sql):
        issues = []
        used_columns = re.findall(r'"(.+?)"', sql)
        for col in used_columns:
            if col not in self.schema['original_names']:
                clean_col = col.strip()
                if clean_col in self.schema['column_names']:
                    issues.append(f"Column '{col}' should be '{clean_col}'")

        prompt = textwrap.dedent(f"""
        Validate this SQL query for the question:

        QUESTION: {question}
        SCHEMA COLUMNS (CLEANED): {self.schema['column_names']}
        ORIGINAL COLUMN NAMES: {self.schema['original_names']}
        SQL: {sql}

        Check for:
        1. Exact column name matches (watch for spaces)
        2. Proper quoting of special characters
        3. Correct table name
        4. Valid SQL syntax

        Return validation as: VALID: <reason> or INVALID: <reason>
        """)

        try:
            llm_validation = self.model.generate_content(prompt).text
        except Exception as e:
            llm_validation = f"VALIDATION FAILED: {str(e)}"

        full_validation = "\n".join([
            "Programmatic Checks:",
            *issues,
            "\nLLM Validation:",
            llm_validation
        ])
        return full_validation
    
    def generate_sql(self, question):
        prompt = textwrap.dedent(f"""
        You are a PostgreSQL expert.

        Convert the following natural language question into a valid SQL query.

        Table: "{self.table_name}"
        Columns: {self.schema['column_names']}

        Rules:
        1. Use the exact table name: "{self.table_name}"
        2. Use quoted column names (e.g., "Net Value", "Item", "Doc. Date")
        3. DO NOT use placeholders like 'your_table_name'
        4. DO NOT use window functions (e.g., LAG, LEAD) directly in the WHERE clause.
        Instead, calculate them in a CTE or subquery and filter in the outer SELECT.
        5. Return only the raw SQL. No explanations. No markdown.

        Question: {question}

        SQL:
        """)
        try:
            response = self.model.generate_content(prompt)
            return self._clean_sql(response.text)
        except Exception as e:
            st.error(f"SQL generation failed: {str(e)}")
            return None
    
    
    

    def _clean_sql(self, sql):
        sql = sql.strip()
        sql = re.sub(r'^```sql\s*|\s*```$', '', sql, flags=re.DOTALL)
        sql = re.sub(r'^```\s*|\s*```$', '', sql, flags=re.DOTALL)
        return sql.strip().rstrip(';')

    def execute_query(self, sql_query):
        if not self._test_connection():
            return None, "No database connection"
        try:
            self.conn.rollback()
            sql_query = sql_query.strip().rstrip(';')
            with self.conn.cursor() as cursor:
                cursor.execute(sql_query)
                results = pd.DataFrame(cursor.fetchall(), 
                                       columns=[desc[0] for desc in cursor.description]) if cursor.description else pd.DataFrame()
                self.query_history.append({
                    'timestamp': datetime.now(),
                    'sql': sql_query,
                    'columns': list(results.columns) if not results.empty else []
                })
                return results, "Execution successful"
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if hasattr(e, 'pgerror'):
                error_msg += f"\nPG Error: {e.pgerror}"
            self.conn.rollback()
            return None, error_msg
        
       

def main():
    st.set_page_config(page_title="Z Transact - SAP Purchase Analytics", layout="wide")
    st.title(" Z Transact | Purchase Data Analytics Agent (SAP)")

    # Initialize connection and agent
    if 'agent' not in st.session_state:
        db_config = {
            "dbname": "analyticbot",
            "user": "yavar",
            "password": "",
            "host": "localhost",
            "port": "5432",
            "connect_timeout": 5
        }
        st.session_state.agent = GeminiDBAgent(db_config)

    with st.sidebar:
        st.markdown("## 🔌 Database Status")
        if st.session_state.agent.conn and st.session_state.agent._test_connection():
            st.success("✅ Connected")
        else:
            st.error("❌ Connection failed")

        if st.button("🔄 Reconnect"):
            st.session_state.agent.conn = st.session_state.agent._establish_connection()
            st.rerun()

        if st.session_state.agent.schema:
            with st.expander("📊 Show Table Schema"):
                schema_df = pd.DataFrame(
                    st.session_state.agent.schema['schema'], 
                    columns=["Column", "Type", "Nullable"]
                )
                st.dataframe(schema_df, height=300)

            with st.expander("🧾 Show Sample Data"):
                unique_columns = _make_unique_columns(st.session_state.agent.schema['column_names'])
                sample_df = pd.DataFrame(
                    st.session_state.agent.schema['sample_data'], 
                    columns=unique_columns
                )
                st.dataframe(sample_df)


    # Tabs for interaction
    tab1, tab2 = st.tabs(["🔎 Query Analytics", "📜 Query History"])

    with tab1:
        question = st.text_area("💬 Ask about purchase data:", "Show items with zero value")

        if st.button("🚀 Analyze"):
            if not st.session_state.agent._test_connection():
                st.error("❌ Database connection required")
                return

            with st.spinner(" Generating SQL..."):
                sql, validation = st.session_state.agent.generate_valid_sql(question)

            if not sql:
                st.error("⚠️ SQL generation failed or was invalid.")
                st.code(validation)
                return

            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("🧾 Final SQL")
                st.code(sql, language="sql")

                with st.spinner("🛠️ Executing SQL..."):
                    start_time = datetime.now()
                    results, status = st.session_state.agent.execute_query(sql)
                    exec_time = (datetime.now() - start_time).total_seconds()

                st.markdown(f"⏱️ Query executed in **{exec_time:.2f} seconds**")
                if results is not None and not results.empty:
                    st.success(f"✅ {len(results)} rows returned.")
                    st.dataframe(results)
                elif results is not None:
                    st.warning("⚠️ Query executed but returned no data.")
                else:
                    st.error(f"❌ Execution failed:\n{status}")

            with col2:
                st.subheader("✅ Validation Feedback")
                st.markdown(f"```text\n{validation.strip()}\n```")

                st.subheader("📘 Explanation")
                try:
                    explanation = st.session_state.agent.model.generate_content(
                        f"Explain this SQL in simple terms. Do not write -Okay, let's break down this SQL query in simple terms: Make it very professional:\n\n{sql}"
                    )
                    st.write(explanation.text.strip())
                except Exception as e:
                    st.error(f"❌ Explanation failed: {str(e)}")

    with tab2:
        st.subheader("📖 Query History")
        history = st.session_state.agent.query_history
        if history:
            for idx, q in enumerate(reversed(history)):
                with st.expander(f"Query {len(history)-idx} - {q['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                    st.code(q['sql'], language="sql")
                    if q['columns']:
                        st.caption(f"Returned Columns: {', '.join(q['columns'])}")
                    else:
                        st.caption("No columns returned.")
        else:
            st.info("No queries executed yet.")


if __name__ == "__main__":
    main()