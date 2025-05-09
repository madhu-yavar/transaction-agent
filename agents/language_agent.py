# agents/language_agent.py

import pandas as pd
from state.state_schema import AgentState
from utils.gemini_client import gemini_chat  # ✅ your Gemini wrapper

def language_agent(state: AgentState) -> AgentState:
    """
    Detect and translate headers and top rows of tabular data (CSV/XLS).
    """
    try:
        if state.file_type not in {"csv", "excel", "xlsx"}:
            return state  # Not applicable

        df = state.internal_data
        if not isinstance(df, pd.DataFrame) or df.empty:
            state.error = "LanguageAgent Error: DataFrame is missing or empty."
            return state

        # Sample for language detection
        sample = " ".join([str(c) for c in df.columns.tolist()[:5]])
        sample += "\n" + df.head(3).astype(str).to_string(index=False)

        detect_prompt = f"""
Detect the language used in the following text.
Respond only with: English, Spanish, French, or Other.

Text:
{sample}
"""

        lang = gemini_chat(detect_prompt).strip().lower()
        print(f"🌍 Detected language: {lang}")

        if "english" in lang:
            return state  # ✅ Skip translation

        # Translate headers
        translated_headers = []
        for col in df.columns:
            if "Unnamed" in str(col) or not str(col).strip():
                translated_headers.append(str(col))  # skip
            else:
                prompt = f"Translate the column name to English: '{col}'"
                translated = gemini_chat(prompt).strip()
                translated_headers.append(translated)

        df.columns = translated_headers
        state.internal_data = df
        state.data_frame = df
        state.translated = True
        print("✅ Translated headers to English.")

    except Exception as e:
        state.error = f"LanguageAgent Error: {str(e)}"

    return state
