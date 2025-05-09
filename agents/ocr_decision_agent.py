# agents/ocr_decision_agent.py

from state.state_schema import AgentState
import pdfplumber

def ocr_decision_agent(state: AgentState) -> AgentState:
    """
    Decides if OCR is needed based on the first page of a PDF.
    Updates state.use_ocr = True/False and state.ocr_reason.
    """
    try:
        if state.file_type != "pdf":
            state.error = "OCR Decision only supports PDFs."
            return state

        with pdfplumber.open(state.file_path) as pdf:
            first_page = pdf.pages[0]

            # Rule 1: No text layer
            if not first_page.extract_text():
                state.use_ocr = True
                state.ocr_reason = "No text layer detected"
                return state

            # Rule 2: Image-heavy page
            if len(first_page.images) > 0:
                state.use_ocr = True
                state.ocr_reason = "Image-heavy page detected"
                return state

            # Rule 3: Text-to-area ratio
            text_length = len(first_page.extract_text() or "")
            page_area = first_page.width * first_page.height
            if (text_length / page_area) < 0.0005:
                state.use_ocr = True
                state.ocr_reason = "Low text-to-area ratio"
                return state

        # If none matched
        state.use_ocr = False
        state.ocr_reason = "Sufficient text for direct extraction"
        return state

    except Exception as e:
        state.error = f"OCR Decision Agent Error: {str(e)}"
        return state
