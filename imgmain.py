# imgmain.py

from pathlib import Path
from langgraph.graph import StateGraph, END
from state.state_schema import AgentState
from agents.data_input_agent import data_input_agent
from agents.image_table_extraction_agent import image_table_extraction_agent
from agents.dynamic_table_detection_agent import dynamic_table_detection_agent
from agents.display_agent import display_agent

# Build graph
graph = StateGraph(AgentState)

graph.add_node("DataInput", data_input_agent)
graph.add_node("ImageTableExtraction", image_table_extraction_agent)
graph.add_node("DynamicTableDetection", dynamic_table_detection_agent)
graph.add_node("DisplayAgent", display_agent)

graph.set_entry_point("DataInput")

def route_after_input(state: AgentState):
    if state.file_type in {"jpg", "jpeg", "png"}:
        return "ImageTableExtraction"
    return "DisplayAgent"

graph.add_conditional_edges("DataInput", route_after_input)
graph.add_edge("ImageTableExtraction", "DynamicTableDetection")
graph.add_edge("DynamicTableDetection", "DisplayAgent")
graph.add_edge("DisplayAgent", END)

app = graph.compile()

def run_pipeline_from_drive_path(file_path: str, file_type: str, source: str = "local") -> AgentState:
    print(f"📸 Image pipeline running on {file_path} ({file_type})")
    initial_state = AgentState(
        source=source,
        file_path=file_path,
        file_type=file_type.lower(),
        original_name=Path(file_path).name
    )
    result = app.invoke(initial_state)
    return AgentState(**result) if isinstance(result, dict) else result
