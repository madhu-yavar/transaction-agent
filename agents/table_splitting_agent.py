# agents/table_splitting_agent.py

from state.state_schema import AgentState
from utils.gemini_client import gemini_chat
import pandas as pd
import re

def table_splitting_agent(state: AgentState) -> AgentState:
    """
    Splits merged tables in raw text using LLM and updates state.detected_tables.
    """
    try:
        if not state.raw_text:
            state.error = "⚠️ No raw text to split."
            return state

        prompt = f"""
You are a smart document processing assistant.

Task:
- Analyze the provided text and identify different tables.
- Split when:
  1. Column counts change significantly
  2. Header rows repeat
  3. 2 or more consecutive empty rows appear

Format the output as:

```markdown
Table 1: [optional description]
| Column A | Column B |
|----------|----------|
| Data     | Data     |
---TABLE BREAK---

Table 2...
```

Document Text:
---------------------
{state.raw_text}
---------------------
"""

        response = gemini_chat(prompt)

        # Extract all markdown tables based on TABLE BREAK
        tables_raw = re.split(r'---TABLE BREAK---', response)

        split_tables = []
        for table_text in tables_raw:
            lines = [line.strip() for line in table_text.splitlines() if line.strip()]
            header_line = next((line for line in lines if line.startswith("|")), None)
            data_lines = [line for line in lines if line.startswith("|")]

            if header_line and data_lines:
                try:
                    headers = [col.strip() for col in header_line.strip("|").split("|")]
                    rows = []
                    for line in data_lines[1:]:
                        row = [cell.strip() for cell in line.strip("|").split("|")]
                        if len(row) == len(headers):
                            rows.append(row)

                    df = pd.DataFrame(rows, columns=headers)
                    split_tables.append({
                        "name": "Split Table",
                        "table": df,
                        "candidate_headers": [0]
                    })
                except Exception as e:
                    print(f"⚠️ Skipping table due to error: {e}")
                    continue

        if split_tables:
            state.detected_tables = split_tables
            state.error = None
        else:
            state.error = "⚠️ No tables split successfully."

        return state

    except Exception as e:
        state.error = f"Table splitting failed: {str(e)}"
        return state