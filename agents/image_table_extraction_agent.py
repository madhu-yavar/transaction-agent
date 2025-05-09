# agents/image_table_extraction_agent.py

from state.state_schema import AgentState
from utils.gemini_client import gemini_vision_chat
import pandas as pd
from PIL import Image
import json
import re

def image_table_extraction_agent(state: AgentState) -> AgentState:
    """
    Extracts tables from an image using Gemini Vision.
    Updates state.detected_tables and internal_data.
    """
    try:
        print(f"📸 Running Gemini Vision Extraction on image: {state.file_path}")
        image = Image.open(state.file_path)

        vision_prompt = """
You are an expert in extracting tables from scanned images.
If the image has Checks, Mention that it is a check image and extract the values accordingly.
- Give appropriate title for the image according to the type of image.
Instructions:
- Extract all clear tabular structures from the image.
- Avoid any logos or text not part of a structured table.
- Output JSON only in the format:

```json
{
  "tables": [
    {
      "title": "optional title",
      "header": ["Column A", "Column B"],
      "rows": [
        ["value1", "value2"],
        ...
      ]
    }
  ]
}
```"""

        # Run Gemini Vision
        response = gemini_vision_chat(vision_prompt, image=image)
        print("📸 Gemini Vision responded. Attempting to parse...")

        tables_json = try_parse_json(response)

        # Build DataFrames
        detected_tables = []
        for i, table in enumerate(tables_json.get("tables", [])):
            header = table.get("header", [])
            rows = table.get("rows", [])
            if header and rows:
                df = pd.DataFrame(rows, columns=header)
                detected_tables.append({
                    "name": f"Image Table {i+1}",
                    "table": df,
                    "candidate_headers": [0]
                })

        if detected_tables:
            state.detected_tables = detected_tables
            state.internal_data = [t["table"] for t in detected_tables]
            state.display_preview = detected_tables[0]["table"].head(10).to_markdown(index=False)
            state.error = None
            print(f"✅ {len(detected_tables)} table(s) extracted from image.")
        else:
            print("⚠️ No tables found in image.")
            state.error = "⚠️ No tables found in image."

    except Exception as e:
        print(f"❌ Image Table Extraction Agent Error: {e}")
        state.error = f"Image Table Extraction Agent Error: {str(e)}"

    return state

def try_parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            return {}
    return {}
