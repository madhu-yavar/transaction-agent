import gradio as gr
import pandas as pd
import fitz  # PyMuPDF
import tempfile
import os
from pathlib import Path
from google.generativeai import configure, GenerativeModel

# === Gemini Setup ===
configure(api_key=os.getenv("GEMINI_API_KEY"))
model = GenerativeModel("gemini-2.0-flash-001"")

# === Globals ===
uploaded_df = None
chat_history = []

# === Helper: Extract tables from PDF (improved) ===
def extract_tables_from_pdf(pdf_path: str) -> pd.DataFrame:
    import pdfplumber
    all_dfs = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                all_dfs.append(df)
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame([{"Note": "No tables detected in PDF."}])

# === Gemini Q&A with context ===
def query_gemini(df: pd.DataFrame, question: str) -> str:
    context = df.head(50).to_csv(index=False)
    prompt = (
        "You are a research assistant. Use the following CSV data to answer the user's question.\n"
        "Be specific, show calculations if needed, and reference column names or rows if applicable.\n"
        f"\nCSV Data:\n{context}\n\nQuestion: {question}"
    )
    response = model.generate_content(prompt)
    return response.text

# === Main chatbot function ===
def chat_fn(message: str, history: list) -> str:
    global uploaded_df, chat_history
    if uploaded_df is None:
        return "Please upload a PDF, CSV, or Excel file first."

    answer = query_gemini(uploaded_df, message)
    chat_history.append({"question": message, "answer": answer})
    return answer

# === File Upload Handler ===
def handle_file_upload(file):
    global uploaded_df, chat_history
    chat_history.clear()

    if file is None:
        return None, "No file uploaded."

    file_path = Path(file.name)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        uploaded_df = extract_tables_from_pdf(file.name)
    elif suffix == ".csv":
        uploaded_df = pd.read_csv(file.name)
    elif suffix in [".xls", ".xlsx"]:
        uploaded_df = pd.read_excel(file.name)
    else:
        return None, "Unsupported file type. Please upload a PDF, CSV, or Excel file."

    return uploaded_df, "File uploaded and data previewed below."

# === Gradio Interface ===
with gr.Blocks() as demo:
    gr.Markdown("""# Z Scout: Data Q&A Assistant\nUpload your transaction report (PDF, CSV, Excel), preview the data, and chat to explore insights.""")

    with gr.Row():
        file_upload = gr.File(label="Upload PDF, CSV, or Excel File", file_types=[".pdf", ".csv", ".xls", ".xlsx"])
        upload_status = gr.Textbox(label="Upload Status", interactive=False)

    data_view = gr.Dataframe(label="Data Preview", interactive=False, wrap=True)

    chat = gr.ChatInterface(fn=chat_fn, title="Ask about your data")

    file_upload.change(fn=handle_file_upload, inputs=file_upload, outputs=[data_view, upload_status])

if __name__ == "__main__":
    demo.launch()