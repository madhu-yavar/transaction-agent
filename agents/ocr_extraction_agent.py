import pdfplumber
from state.state_schema import AgentState
from utils.gemini_client import gemini_chat

def ocr_extraction_agent(state: AgentState) -> AgentState:
    """
    Uses Gemini to extract text from scanned PDFs page-by-page.
    """
    try:
        if state.file_type != "pdf":
            state.error = "OCR extraction supports only PDF files."
            return state

        print("📸 Running Gemini OCR Extraction...")
        raw_text_pages = []

        with pdfplumber.open(state.file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                image = page.to_image(resolution=300).original
                prompt = f"You're an OCR assistant. Read this scanned document image and extract clean, structured text"
                extracted_text = gemini_chat(prompt)
                raw_text_pages.append(extracted_text)

        state.raw_text = "\n\n".join(raw_text_pages)
        print("✅ OCR text extraction complete.")
        return state

    except Exception as e:
        state.error = f"OCR Extraction Agent Error: {str(e)}"
        return state
