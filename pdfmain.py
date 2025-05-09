# pdfmain.py

from pathlib import Path
from langgraph.graph import StateGraph, END
from state.state_schema import AgentState

from agents.data_input_agent import data_input_agent
from agents.ocr_extraction_agent import ocr_extraction_agent
from agents.pdf_table_extraction_agent import pdf_table_extraction_agent
from agents.dynamic_table_detection_agent import dynamic_table_detection_agent
from agents.display_agent import display_agent
from agents.image_table_extraction_agent import image_table_extraction_agent

from pdf2image import convert_from_path
import tempfile
from PIL import Image
import os

graph = StateGraph(AgentState)

# Register nodes
graph.add_node("DataInput", data_input_agent)
graph.add_node("OCRExtraction", ocr_extraction_agent)
graph.add_node("PDFTableExtraction", pdf_table_extraction_agent)
graph.add_node("DynamicTableDetection", dynamic_table_detection_agent)
graph.add_node("DisplayAgent", display_agent)

# Custom fallback logic node
def ocr_with_fallback(state: AgentState) -> AgentState:
    print(f"📄 PDF pipeline running on {state.file_path} ({state.file_type})")

    # Step 1: Run OCR to extract raw text
    state = ocr_extraction_agent(state)

    if state.raw_text and len(state.raw_text.splitlines()) > 5:
        print("✅ Raw text found, continuing with PDFTableExtraction")
        return pdf_table_extraction_agent(state)
    else:
        print("📸 No valid raw text, falling back to image-based extraction")

        try:
            images = convert_from_path(state.file_path)
            all_tables = []

            for i, img in enumerate(images):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
                    img.save(tmp_img.name)
                    tmp_state = AgentState(
                        file_path=tmp_img.name,
                        file_type="png",
                        source=state.source,
                        original_name=f"{state.original_name}_page_{i+1}"
                    )
                    tmp_state = image_table_extraction_agent(tmp_state)

                    if tmp_state.detected_tables:
                        all_tables.extend(tmp_state.detected_tables)
                    os.unlink(tmp_img.name)

            if all_tables:
                state.detected_tables = all_tables
                state.internal_data = [t["table"] for t in all_tables]
                state.error = None
            else:
                state.error = "⚠️ No tables detected from images."
        except Exception as e:
            state.error = f"Image fallback failed: {str(e)}"

    return state

graph.add_node("OCRWithFallback", ocr_with_fallback)

# Entry point
graph.set_entry_point("DataInput")

# Routing
def route_after_input(state: AgentState):
    return "OCRWithFallback" if state.file_type == "pdf" else "DisplayAgent"

def route_after_fallback(state: AgentState):
    if state.detected_tables:
        return "DynamicTableDetection"
    else:
        return "DisplayAgent"

graph.add_conditional_edges("DataInput", route_after_input)
graph.add_conditional_edges("OCRWithFallback", route_after_fallback)
graph.add_edge("PDFTableExtraction", "DynamicTableDetection")
graph.add_edge("DynamicTableDetection", "DisplayAgent")
graph.add_edge("DisplayAgent", END)

# Compile graph
app = graph.compile()

def run_pipeline_from_drive_path(file_path: str, file_type: str, source: str = "local") -> AgentState:
    state = AgentState(
        source=source,
        file_path=file_path,
        file_type=file_type.lower(),
        original_name=Path(file_path).name
    )
    result = app.invoke(state)
    return AgentState(**result) if isinstance(result, dict) else result
