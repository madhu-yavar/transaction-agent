# from state.state_schema import AgentState
# from utils.gemini_client import gemini_chat

# def sql_explainer_agent(state: AgentState) -> AgentState:
#     if not state.display_preview or state.internal_data is None:
#         state.error = "❌ Cannot generate explanation: missing SQL or data."
#         return state

#     try:
#         df = state.internal_data
#         total_rows = len(df)

#         # ✅ Dynamically choose chunk size
#         if total_rows <= 30:
#             chunk_size = total_rows
#         elif total_rows <= 200:
#             chunk_size = 20
#         elif total_rows <= 1000:
#             chunk_size = 50
#         else:
#             chunk_size = 100

#         explanation_chunks = []

#         for i in range(0, total_rows, chunk_size):
#             chunk_df = df.iloc[i:i + chunk_size]
#             sample_data = chunk_df.to_dict(orient="records")

#             insight_prompt = f"""
# You are a business data analyst.

# You are given:
# 1. A SQL query
# 2. Its output (sample data from part {i//chunk_size + 1})
# 3. A user question

# Based on the **query results** and the **user's original intent**, provide a detailed **explanation and prescriptive insights**. Focus on patterns, anomalies, trends, totals, and what actions can be taken.

# SQL Query:
# {state.display_preview}

# User Question:
# {state.raw_text}

# Sample Output (Part {i//chunk_size + 1}):
# {sample_data}

# Instructions:
# - Start with a concise summary of the query's intent.
# - Analyze the data: identify any patterns, outliers, totals, or notable metrics.
# - Explain it clearly in business terms (e.g., PO delays, partially completed orders).
# - Offer 3–5 actionable, prescriptive insights (what the user should consider doing).
# - Maintain a professional tone. Do not include markdown or code formatting.
# """

#             print(f"📘 SQL Explainer Agent – Processing chunk {i//chunk_size + 1}")
#             explanation = gemini_chat(insight_prompt)
#             explanation_chunks.append(f"[Chunk {i//chunk_size + 1}]\n{explanation.strip()}")

#         state.explanation_report = "\n\n---\n\n".join(explanation_chunks)
#         return state

#     except Exception as e:
#         state.explanation_report = f"❌ Explanation failed: {str(e)}"
#         return state


from state.state_schema import AgentState
from utils.gemini_client import gemini_chat
import pandas as pd
import math
import json

def chunk_dataframe(df: pd.DataFrame, chunk_size: int):
    total = len(df)
    num_chunks = math.ceil(total / chunk_size)
    return [df.iloc[i * chunk_size:(i + 1) * chunk_size] for i in range(num_chunks)]

def determine_chunk_size(row_count: int) -> int:
    if row_count <= 50:
        return 10
    elif row_count <= 500:
        return 20
    elif row_count <= 2000:
        return 50
    else:
        return 100

def sql_explainer_agent(state: AgentState) -> AgentState:
    if not state.display_preview or state.internal_data is None:
        state.error = "❌ Cannot generate explanation: missing SQL or data."
        return state

    try:
        total_rows = len(state.internal_data)
        chunk_size = determine_chunk_size(total_rows)
        chunks = chunk_dataframe(state.internal_data, chunk_size=chunk_size)

        all_explanations = []

        for idx, chunk in enumerate(chunks):
            print(f"📘 SQL Explainer Agent – Processing chunk {idx + 1}/{len(chunks)}")

            sample_data = chunk.to_dict(orient="records")

            insight_prompt = f"""
You are a business data analyst.

You are given:
1. A SQL query
2. Its output (sample rows)
3. A user question

Analyze the **output** and the **original intent** to provide a clear explanation and **prescriptive business insights**.

SQL Query:
{state.display_preview}

User Question:
{state.raw_text}

Sample Output:
{json.dumps(sample_data, indent=2)}

Instructions:
- Summarize the intent of the query.
- Identify patterns, outliers, or any anomalies.
- Explain what the result reveals in business terms (e.g., bottlenecks, delays, mismatches).
- Recommend 3 to 5 specific business actions based on insights.
- Write in professional, clear language.
- Output plain text only. No markdown or code formatting.
            """

            explanation = gemini_chat(insight_prompt)
            all_explanations.append(f"🔹 Chunk {idx+1} Insights:\n{explanation.strip()}")

        # Join all chunked responses
        state.chat_response = "\n\n".join(all_explanations)
        return state

    except Exception as e:
        state.chat_response = f"❌ Explanation failed: {str(e)}"
        return state

