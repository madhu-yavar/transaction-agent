import streamlit as st
from imgmain import run_pipeline_from_drive_path
import tempfile
import os
import pandas as pd
from PIL import Image  # ✅ FIXED: Import added
from state.state_schema import AgentState

st.set_page_config(page_title="🖼️ Image Table Extractor", layout="wide")
st.title("🖼️ Gemini Vision Table Extraction from Images")

uploaded_file = st.file_uploader("Upload an Image (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_file_path = tmp_file.name

    with st.spinner("🔍 Extracting tables from image..."):
        result = run_pipeline_from_drive_path(temp_file_path, file_type="jpg", source="upload")
        state = AgentState(**result) if isinstance(result, dict) else result

    if hasattr(state, "error") and state.error:
        st.error(f"❗ Error: {state.error}")
        os.unlink(temp_file_path)
        st.stop()

    if hasattr(state, "detected_tables") and state.detected_tables:
        st.success(f"✅ {len(state.detected_tables)} table(s) extracted from image.")
        for i, table in enumerate(state.detected_tables):
            df = table.get("table")
            if df is not None and not df.empty:
                st.markdown(f"### 📊 Table {i+1}: {table.get('name', 'Untitled')}")
                st.dataframe(df.head(30))
            else:
                st.warning(f"⚠️ Table {i+1} is empty or invalid.")
    else:
        st.warning("⚠️ No tables found in the image.")

    st.markdown("### 📎 File Preview")
    try:
        st.image(Image.open(temp_file_path), caption="🖼️ Image Preview", use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ Could not preview image: {e}")

    os.unlink(temp_file_path)
