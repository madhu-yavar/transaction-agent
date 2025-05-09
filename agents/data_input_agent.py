# agents/data_input_agent.py

from typing import Union
import requests
import mimetypes
from pathlib import Path
from state.state_schema import AgentState

def data_input_agent(state: AgentState) -> AgentState:
    """Handles file upload or cloud link and updates AgentState with file details."""
    try:
        # If file_path is already populated, nothing to do
        if state.file_path:
            return state

        # --- Local Upload ---
        if state.source == "local" and state.original_name:
            file_path = Path(state.original_name)
            state.file_path = str(file_path)
            state.file_type = file_path.suffix.lower().replace(".", "")
        
        # --- Cloud Download ---
        elif state.source == "cloud" and state.cloud_link:
            url = state.cloud_link
            response = requests.get(url)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                ext = mimetypes.guess_extension(content_type.split(";")[0]) or ".pdf"
                filename = Path(f"/tmp/cloud_input{ext}")
                filename.write_bytes(response.content)
                
                state.file_path = str(filename)
                state.file_type = ext.replace(".", "")
                state.original_name = filename.name
            else:
                state.error = f"❌ Failed to download from cloud: {url} (Status {response.status_code})"
        
        else:
            state.error = "❌ No valid local file or cloud link provided."

        return state

    except Exception as e:
        state.error = f"❌ DataInput Agent Error: {str(e)}"
        return state
