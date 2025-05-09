from state.state_schema import AgentState
from pdf2image import convert_from_path
from PIL import Image
from agents.image_table_extraction_agent import image_table_extraction_agent
import pdfplumber
import pandas as pd
import tempfile

def pdf_table_extraction_agent(state: AgentState) -> AgentState:
    """
    Extracts tables from a PDF using pdfplumber.
    Falls back to Gemini Vision if nothing meaningful is extracted.
    """
    try:
        print(f"🔍 Starting PDF Table Extraction (pdf_table_extraction_agent): {state.file_path}")
        tables = []
        raw_text_parts = []

        with pdfplumber.open(state.file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        raw_text_parts.append(text)

                    table = page.extract_table()
                    if table:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        if df.shape[0] >= 2 and df.shape[1] >= 2:
                            tables.append(df)
                        else:
                            print(f"⚠️ Skipping small table on page {i+1}: shape {df.shape}")
                except Exception as e:
                    print(f"⚠️ Error processing page {i+1}: {e}")
                    continue

        if tables:
            state.internal_data = tables
            state.detected_tables = [
                {"name": f"PDF Table {i+1}", "table": tbl, "candidate_headers": [0]}
                for i, tbl in enumerate(tables)
            ]
            state.raw_text = "\n".join(raw_text_parts)
            state.error = None
            print("✅ Tables extracted from PDF text.")
            return state

        # 🔁 Fallback: Convert pages to images and process with Gemini Vision
        print("📸 No valid tables found — fallback to image-based extraction.")
        images = convert_from_path(state.file_path)
        fallback_tables = []

        for idx, img in enumerate(images):
            print(f"🖼️ Converting page {idx+1} to image for Gemini Vision")
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                img.save(tmp_img.name)
                temp_state = AgentState(
                    file_path=tmp_img.name,
                    file_type="png",
                    source=state.source
                )
                temp_state = image_table_extraction_agent(temp_state)
                if temp_state.detected_tables:
                    fallback_tables.extend(temp_state.detected_tables)

        if fallback_tables:
            state.detected_tables = fallback_tables
            state.internal_data = [t["table"] for t in fallback_tables]
            state.raw_text = None
            state.error = None
            print(f"✅ Extracted {len(fallback_tables)} table(s) via image fallback.")
        else:
            state.internal_data = None
            state.detected_tables = []
            state.error = "⚠️ No valid tables extracted from PDF or image fallback."

        return state

    except Exception as e:
        state.error = f"PDF Table Extraction Agent Error: {str(e)}"
        return state
