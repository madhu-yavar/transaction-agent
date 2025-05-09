from state.state_schema import AgentState
from utils.gemini_client import gemini_chat
import json
import re

def semantic_inference_agent(state: AgentState) -> AgentState:
    if not state.column_names or state.internal_data is None:
        state.error = "❌ Semantic inference failed: Missing column names or sample data."
        return state

    try:
        sample_data = state.internal_data.sample(n=min(10, len(state.internal_data))).to_dict(orient="records")

        prompt = f"""
You are a smart semantic annotator.

Your task is to analyze the provided table structure to determine the **business meaning** of each column using:
- The column name
- The sample values

Column Headers:
{json.dumps(state.column_names, indent=2)}

Sample Rows:
{json.dumps(sample_data, indent=2)}

Output a valid JSON array like:
[
  {{
    "column": "<actual column name>",
    "semantic": "<semantic description with 2-3 sample values inside>"
  }},
  ...
]

Rules:
- Use both the column name and the sample values to determine meaning.
- For each column, include 2-3 representative values inside the semantic explanation.
- If a column has values like 'GR goods receipt' or 'GR for order', interpret it as a GRN status.
- Ignore empty or meaningless columns (e.g. all NaNs or Unnamed).
- Output must be a **pure JSON array** — no markdown, no explanations, no comments.

Examples should look like:
{{
  "column": "Pstng Date",
  "semantic": "Posting Date. Sample values: 31.01.2025, 21.01.2025"
}}
"""

        print("\n🤖 Agent: 🧠 Semantic Inference")
        print(f"🔹 Input: table_name={state.table_name}, question={state.raw_text}")

        response = gemini_chat(prompt)
        response_clean = re.sub(r"^```json|```$", "", response.strip()).strip()
        parsed = json.loads(response_clean)

        if isinstance(parsed, list):
            state.semantic_schema = parsed
        else:
            state.error = "❌ Gemini returned unexpected format for semantic schema."

        return state

    except Exception as e:
        state.error = f"❌ Semantic inference failed: {str(e)}"
        return state





# # agents/semantic_inference_agent.py

# from state.state_schema import AgentState
# from utils.gemini_client import gemini_chat
# import json
# import re

# def semantic_inference_agent(state: AgentState) -> AgentState:
#     if not state.column_names or state.internal_data is None:
#         state.error = "❌ Semantic inference failed: Missing column names or sample data."
#         return state

#     # Use 8–10 shuffled rows to introduce value variety
#     sample_rows = state.internal_data.sample(min(10, len(state.internal_data))).to_dict(orient="records")

#     prompt = f"""
# You are a data schema analyst with ERP and SAP domain knowledge.

# The user uploaded a table with the following column names and sample data. You must infer what each column represents in business terms based on both the column name and the actual values shown.

# ---

# 📌 Column Names:
# {json.dumps(state.column_names)}

# 📌 Sample Rows (values vary):
# {json.dumps(sample_rows, indent=2)}

# ---

# 🎯 Your Task:
# Analyze the column names AND the actual data values. Assign each column a semantic description explaining what it likely represents in business/SAP context.

# ✅ Guidelines:
# - Use value patterns. For example:
#   - If values include "GR goods receipt", "GR for order", it's a **GRN Status** field.
#   - If the format is like "31.01.2025", it's likely a **Date** field.
#   - If values are large numbers with commas or decimals, it's likely **Amount**, **Net Price**, or **Extended Price**.
#   - If values are consistently missing or all identical, label as **"Possibly Unused"**.
# - Do NOT guess only from column names. Use both name and values.

# ---

# 📤 Output Format:
# Return only valid JSON array (no markdown, no commentary), like:
# [
#   {{ "column": "<exact column name>", "semantic": "<business meaning>" }},
#   ...
# ]
# """

#     try:
#         print("\n🤖 Agent: 🧠 Semantic Inference")
#         print(f"🔹 Input: table_name={state.table_name}, question={state.raw_text}")
#         response = gemini_chat(prompt)

#         # Clean ```json or other wrappers
#         response_clean = re.sub(r"^```json|```$", "", response.strip()).strip()
#         parsed = json.loads(response_clean)

#         if isinstance(parsed, list):
#             state.semantic_schema = parsed
#             return state
#         else:
#             state.error = "❌ Gemini returned unexpected format for semantic schema."
#             return state
#     except Exception as e:
#         state.error = f"❌ Semantic inference failed: {str(e)}"
#         return state

