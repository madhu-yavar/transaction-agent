from pathlib import Path
import json
import gradio as gr
from main import run_pipeline_from_drive_path
import pandas as pd

def run_data_input(upload, cloud_link):
    try:
        if upload:
            file_path = upload.name
            file_type = Path(file_path).suffix.lower().replace(".", "")
            source = "local"
        elif cloud_link:
            file_path = cloud_link
            file_type = Path(cloud_link).suffix.lower().replace(".", "")
            source = "cloud"
        else:
            return "❌ Please upload a file or provide a cloud link."

        # ✅ Run LangGraph pipeline
        agent_state = run_pipeline_from_drive_path(file_path, file_type, source)

        # ✅ Verify model and extract safe fields
        if not hasattr(agent_state, "model_dump"):
            return "❌ Internal error: AgentState is not a valid model."

        output = agent_state.model_dump()

        # ✅ Handle internal_data (like DataFrame) preview
        if isinstance(agent_state.internal_data, pd.DataFrame):
            preview_df = agent_state.internal_data.head(10).to_dict(orient="records")
            output["data_preview"] = preview_df
        else:
            output["data_preview"] = "⚠️ No DataFrame or unrecognized data."

        return json.dumps(output, indent=2)

    except Exception as e:
        return f"❌ Error: {str(e)}"

# === Gradio UI ===
demo = gr.Interface(
    fn=run_data_input,
    inputs=[
        gr.File(label="📁 Upload Local File"),
        gr.Textbox(label="🔗 Or Paste Cloud Link")
    ],
    outputs=gr.Textbox(label="🧠 Agent Output", lines=20),
    title="📊 Data Input Agent (LangGraph)",
    description="Upload a PDF/CSV/Excel file or paste a cloud link. This LangGraph agent pipeline processes and displays structured output."
)

if __name__ == "__main__":
    demo.launch()
