# Updated dynamic_table_understanding_agent.py with page-by-page PDF processing

import pandas as pd
import re
import json
import pdfplumber
from state.state_schema import AgentState
from utils.gemini_client import gemini_chat


def dynamic_table_understanding_agent(state: AgentState) -> AgentState:
    """
    Processes PDF page by page using LLM to extract structured tables.
    Updates `internal_data`, `data_frame`, and preview.
    """
    try:
        if state.file_type != "pdf" or not state.file_path:
            state.error = "⚠️ Not a PDF file or missing path."
            return state

        all_tables = []

        with pdfplumber.open(state.file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text or len(text.strip()) < 10:
                    continue

                print(f"📄 Analyzing Page {i+1}...")
                prompt = build_gemini_table_prompt(text)
                response = gemini_chat(prompt)
                tables_info = try_parse_json(response)

                if not tables_info or "tables" not in tables_info:
                    continue

                for table in tables_info.get("tables", []):
                    header = table.get("header", [])
                    rows = table.get("rows", [])
                    if header and rows:
                        try:
                            df = pd.DataFrame(rows, columns=header)
                            all_tables.append(df)
                        except Exception as e:
                            print(f"⚠️ Skipping invalid table on Page {i+1}: {e}")
                            continue

        if all_tables:
            print("✅ Assigning combined tables to state.internal_data...")
            state.internal_data = all_tables  # <-- Use full list of DataFrames here
            state.data_frame = pd.concat(all_tables, ignore_index=True)
            state.display_preview = state.data_frame.head(10).to_markdown(index=False)
            state.error = None
        else:
            print("⚠️ No valid tables extracted into DataFrames.")
            state.error = "⚠️ No rows parsed into valid DataFrame."


    except Exception as e:
        state.error = f"Dynamic Table Understanding Agent Error: {str(e)}"

    print(f"🔍 Type of all_tables: {type(all_tables)} | Length: {len(all_tables)}")
    for idx, df in enumerate(all_tables):
        print(f"📄 Table {idx+1} shape: {df.shape}")


    return state


def build_gemini_table_prompt(page_text: str) -> str:
    return f"""
You are a table extraction assistant.

Task:
- Detect table-like structures in this page.
- Extract one or more tables with headers and rows.
- Output clean JSON format:

{{
  "tables": [
    {{
      "title": "optional",
      "header": ["Col1", "Col2"],
      "rows": [["A", "B"], ["C", "D"]]
    }}
  ]
}}

Text:
------------------
{page_text}
------------------
"""


def try_parse_json(response: str) -> dict:
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        try:
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            print(f"⚠️ JSON Parsing Fallback Failed: {e}")
            return {}
    return {}
