from pathlib import Path
from langgraph.graph import StateGraph, END
from state.state_schema import AgentState

# Import agents
from agents.data_input_agent import data_input_agent
from agents.ocr_decision_agent import ocr_decision_agent
from agents.ocr_extraction_agent import ocr_extraction_agent  # Uses corrected Code 1
from agents.language_agent import language_agent
from agents.pdf_table_extraction_agent import pdf_table_extraction_agent
from agents.dynamic_table_understanding_agent import dynamic_table_understanding_agent
from agents.table_splitting_agent import table_splitting_agent
from agents.dynamic_table_detection_agent import dynamic_table_detection_agent
from agents.generic_tabular_agent import generic_tabular_agent
from agents.image_table_extraction_agent import image_table_extraction_agent
from agents.display_agent import display_agent
from utils.gemini_client import gemini_vision_chat

# Build graph
graph = StateGraph(AgentState)

# Register core nodes
graph.add_node("DataInput", data_input_agent)
graph.add_node("OCRDecision", ocr_decision_agent)
graph.add_node("OCRExtraction", ocr_extraction_agent)  # Uses corrected Code 1
graph.add_node("LanguageAgent", language_agent)
graph.add_node("PDFTableExtraction", pdf_table_extraction_agent)
graph.add_node("DynamicTableUnderstanding", dynamic_table_understanding_agent)
graph.add_node("TableSplitting", table_splitting_agent)
graph.add_node("DynamicTableDetection", dynamic_table_detection_agent)
graph.add_node("GenericTabular", generic_tabular_agent)
graph.add_node("ImageTableExtraction", image_table_extraction_agent)
graph.add_node("DisplayAgent", display_agent)

# Set entry point
graph.set_entry_point("DataInput")

# Routing logic
def route_after_data_input(state: AgentState):
    ext = state.file_type.lower()
    if ext == "pdf":
        return "OCRDecision"
    elif ext in {"csv", "xls", "xlsx"}:
        return "GenericTabular"
    elif ext in {"jpg", "jpeg", "png"}:
        return "ImageTableExtraction"
    state.error = f"Unsupported file type: {ext}"
    return "DisplayAgent"

def route_after_ocr_decision(state: AgentState):
    if state.use_ocr is None:
        state.error = "OCR decision not set"
        return "DisplayAgent"
    return "OCRExtraction" if state.use_ocr else "LanguageAgent"

def route_after_text(state: AgentState):
    if state.error:
        return "DisplayAgent"
    if state.raw_text and len(state.raw_text) > 20:
        return "PDFTableExtraction"
    return "DynamicTableUnderstanding"

# Edges
graph.add_conditional_edges("DataInput", route_after_data_input)
graph.add_conditional_edges("OCRDecision", route_after_ocr_decision)
graph.add_conditional_edges("OCRExtraction", route_after_text)
graph.add_conditional_edges("LanguageAgent", route_after_text)
graph.add_edge("GenericTabular", "DynamicTableDetection")
graph.add_edge("ImageTableExtraction", "DynamicTableDetection")
graph.add_edge("PDFTableExtraction", "TableSplitting")
graph.add_edge("DynamicTableUnderstanding", "TableSplitting")
graph.add_edge("TableSplitting", "DynamicTableDetection")
graph.add_edge("DynamicTableDetection", "DisplayAgent")
graph.add_edge("DisplayAgent", END)

# Compile graph
app = graph.compile()

def run_pipeline_from_drive_path(file_path: str, file_type: str, source: str = "local") -> AgentState:
    print(f"🚀 Running pipeline for {file_path} ({file_type})")
    # Validate file existence
    if not Path(file_path).exists():
        return AgentState(
            source=source,
            file_path=file_path,
            file_type=file_type.lower(),
            original_name=Path(file_path).name,
            error=f"File not found: {file_path}"
        )
    # Initialize state
    initial_state = AgentState(
        source=source,
        file_path=file_path,
        file_type=file_type.lower(),
        original_name=Path(file_path).name
    )
    # Run pipeline
    try:
        result = app.invoke(initial_state)
        # Ensure result is AgentState (aligned with Code 3)
        return AgentState(**result) if isinstance(result, dict) else result
    except Exception as e:
        return AgentState(
            source=source,
            file_path=file_path,
            file_type=file_type.lower(),
            original_name=Path(file_path).name,
            error=f"Pipeline error: {str(e)}"
        )