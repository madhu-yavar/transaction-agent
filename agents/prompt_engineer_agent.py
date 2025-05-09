


# from state.state_schema import AgentState
# from utils.gemini_client import gemini_chat
# import textwrap

# def prompt_engineer_agent(state: AgentState) -> AgentState:
#     if not state.raw_text or not state.table_name or not state.column_names:
#         state.error = "❌ Missing required fields for prompt engineering (raw_text, table_name, or column_names)."
#         return state

#     try:
#         print("\n🤖 Agent: 🧠 Prompt Engineer")
#         print(f"🔹 Input: table_name={state.table_name}, question={state.raw_text}")

#         # ✅ Build semantic schema with examples (if available)
#         if hasattr(state, "semantic_schema") and state.semantic_schema:
#             semantic_info = "\n".join([
#                 f'- "{col["column"]}": {col["semantic"]}' 
#                 for col in state.semantic_schema
#             ])
#         else:
#             semantic_info = "\n".join([f'- "{col}"' for col in state.original_names or []])

#         # 🧠 Final Prompt
#         engineered_prompt = textwrap.dedent(f"""
#         You are a PostgreSQL expert with SAP ERP and domain knowledge.

#         Your task is to convert the following **natural language question** into a valid SQL query for PostgreSQL.

#         Table Name: "{state.table_name}"

#         Column Descriptions (inferred from data):
#         {semantic_info}

#         Rules:
#         1. Use the table name exactly as provided: "{state.table_name}"
#         2. Always use **quoted** column names (e.g., "PO", "GR/GI Sl")
#         3. NEVER use placeholder names like 'your_table_name' or 'column1'
#         4. NEVER return markdown, comments, or explanations—only executable SQL.
#         5. Avoid using window functions in WHERE clause directly—use subqueries or CTEs instead.

#         Important: 
        
#         Column names may contain spaces or punctuation. Use them exactly as listed.

#         🔐 DATE HANDLING RULE:
#         If comparing or subtracting text-based date columns:
#         - Add WHERE filters using regex:
#           "Doc. Date" ~ '^\\d{{2}}\\.\\d{{2}}\\.\\d{{4}}$' AND "Pstng Date" ~ '^\\d{{2}}\\.\\d{{2}}\\.\\d{{4}}$'
#         - Only then apply TO_DATE("Doc. Date", 'DD.MM.YYYY') etc.

#         🔍 ANALYZE SAMPLE VALUES WHEN POSSIBLE. For example:
#         - If a column contains 'GR goods receipt' or 'GR for order' in its values, it likely refers to Goods Receipt Note (GRN) status.
#         - If values like 'Partially Completed' appear, infer relevant business filters accordingly.

#         Now answer this question using SQL:
#         {state.raw_text}

#         SQL:
#         """)

#         state.engineered_prompt = engineered_prompt.strip()
#         return state

#     except Exception as e:
#         state.error = f"❌ Prompt Engineer Agent failed: {str(e)}"
#         return state

from state.state_schema import AgentState
from utils.gemini_client import gemini_chat
import textwrap

def prompt_engineer_agent(state: AgentState) -> AgentState:
    if not state.raw_text or not state.table_name or not state.column_names:
        state.error = "❌ Missing required fields for prompt engineering (raw_text, table_name, or column_names)."
        return state

    try:
        print("\n🤖 Agent: 🧠 Prompt Engineer")
        print(f"🔹 Input: table_name={state.table_name}, question={state.raw_text}")

        if hasattr(state, "semantic_schema") and state.semantic_schema:
            semantic_info = "\n".join([
                f'- "{col["column"]}": {col["semantic"]}' 
                for col in state.semantic_schema
            ])
        else:
            semantic_info = "\n".join([f'- "{col}"' for col in state.original_names or []])

        engineered_prompt = textwrap.dedent(f"""
        You are a PostgreSQL expert with SAP CRM knowledge.

        Convert the following user question into a valid SQL query.

        Table: "{state.table_name}"

        Column Info (with sample semantics):
        {semantic_info}

        ⚠️ Business Intelligence Guideline:
        If the query refers to *statuses like "GRN partially completed"*, and the column values do not explicitly contain this text,
        you must derive it. For example:
          - Use `" Quantity in"` and `"  Qty OPUn"` to infer partial receipt.
          - If `" Quantity in"` < `"  Qty OPUn"`, then it's "Partially Completed"
          - If equal, it's "Completed"
          - If 0 or null, it's "Not Completed"

        Rules:
        1. Use the exact table name: "{state.table_name}"
        2. Always use quoted column names (e.g., "Net Value", "Item", "Doc. Date")
        3. DO NOT use placeholders like 'your_table_name'
        4. DO NOT use window functions directly in WHERE clause.
        5. Return only the raw SQL — no explanations, no markdown.

        ‼️ Mandatory Date Validation:
        If comparing or subtracting dates stored as text, use:
        WHERE "Doc. Date" ~ '^\\d{{2}}\\.\\d{{2}}\\.\\d{{4}}$' AND "Pstng Date" ~ '^\\d{{2}}\\.\\d{{2}}\\.\\d{{4}}$'
        before applying TO_DATE()

        Question: {state.raw_text}

        SQL:
        """)

        state.engineered_prompt = engineered_prompt.strip()
        return state

    except Exception as e:
        state.error = f"❌ Prompt Engineer Agent failed: {str(e)}"
        return state

