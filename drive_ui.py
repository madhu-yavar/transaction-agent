# drive_ui.py
import gradio as gr
from cloud.drive_auth import authenticate_drive, list_drive_files, download_drive_file
from main import run_pipeline_from_drive_path

drive_service = None
drive_files = []

def connect_to_drive():
    global drive_service, drive_files
    drive_service = authenticate_drive()
    drive_files = list_drive_files(drive_service)
    file_names = [f"{f['name']} ({f['mimeType']})" for f in drive_files]
    return gr.update(choices=file_names, interactive=True), "✅ Connected to Google Drive!"

def handle_drive_file(index):
    global drive_files, drive_service
    if index is None or not drive_files:
        return "❌ No file selected."

    selected = drive_files[index]
    file_path = download_drive_file(drive_service, selected["id"], selected["name"])

    # Determine file_type
    mime = selected["mimeType"]
    if mime == "application/pdf":
        file_type = "pdf"
    elif mime == "text/csv":
        file_type = "csv"
    elif "sheet" in mime:
        file_type = "xlsx"
    else:
        file_type = "unknown"

    # Run pipeline
    final_state = run_pipeline_from_drive_path(file_path, file_type, source="cloud")

    return f"""✅ File processed successfully:

📄 File Name: {final_state.original_name}
📁 Type: {final_state.file_type}
🌐 Source: {final_state.source}
📋 Preview:\n\n{final_state.display_preview if final_state.display_preview else "No preview generated."}
"""

with gr.Blocks(title="📂 Google Drive Picker") as demo:
    gr.Markdown("## ☁️ Google Drive File Picker")

    connect_button = gr.Button("🔐 Connect to Google Drive")
    status = gr.Textbox(label="Status", interactive=False)

    file_selector = gr.Dropdown(choices=[], label="📄 Select File", interactive=False)
    process_button = gr.Button("🚀 Download & Process")
    output_box = gr.Textbox(label="Agent Output", lines=15, interactive=False)

    connect_button.click(fn=connect_to_drive, inputs=[], outputs=[file_selector, status])
    process_button.click(fn=handle_drive_file, inputs=file_selector, outputs=output_box)

if __name__ == "__main__":
    demo.launch()
