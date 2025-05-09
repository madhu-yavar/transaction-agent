from typing import Optional, Any, List, Dict
from pydantic import BaseModel
import pandas as pd

class AgentState(BaseModel):
    # Input/Metadata
    source: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    original_name: Optional[str] = None
    cloud_link: Optional[str] = None

    # Processed Data
    raw_text: Optional[str] = None
    translated: Optional[bool] = False

    # Tables
    detected_tables: Optional[List[Dict]] = None
    extracted_tables: Optional[List[pd.DataFrame]] = None
    selected_table_index: Optional[int] = None
    selected_header_row: Optional[int] = None
    data_frame: Optional[pd.DataFrame] = None

    # PostgreSQL
    table_name: Optional[str] = None
    column_names: Optional[List[str]] = None
    original_names: Optional[List[str]] = None

    # Outputs
    display_preview: Optional[str] = None
    visualization_image: Optional[str] = None
    chat_response: Optional[str] = None
    internal_data: Optional[Any] = None

    # OCR
    use_ocr: Optional[bool] = False
    ocr_reason: Optional[str] = None

    # Semantic Inference + Logging
    semantic_schema: Optional[List[Dict[str, str]]]= None
    
    validation_report: Optional[str] = None   
    explanation_report: Optional[str] = None  

    engineered_prompt: Optional[str] = None
    query_history: Optional[List[Dict]] = []
    

    # Error
    error: Optional[str] = None

    model_config = {"arbitrary_types_allowed": True}
