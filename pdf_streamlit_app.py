import streamlit as st
from pdfmain import run_pipeline_from_drive_path
import tempfile
import os
import pandas as pd
from PIL import Image
from pdf2image import convert_from_path

st.set_page_config(page_title="📄 PDF Table Extractor", layout="wide")
st.title("📄 Smart Table Extraction from PDFs")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

def deduplicate_columns(columns):
    seen = {}
    new_columns = []
    for col in columns:
        if col not in seen:
            seen[col] = 1
            new_columns.append(col)
        else:
            seen[col] += 1
            new_columns.append(f"{col}_{seen[col]}")
    return new_columns


if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_path = tmp_file.name

    try:
        pdf_img = convert_from_path(temp_path, first_page=1, last_page=1)[0]
        st.image(pdf_img, caption="📄 PDF Preview (Page 1)", use_container_width=True)
    except:
        st.warning("⚠️ Preview failed.")

    with st.spinner("🔍 Extracting tables..."):
        state = run_pipeline_from_drive_path(temp_path, "pdf", source="upload")

    if hasattr(state, "detected_tables") and state.detected_tables:
        st.success(f"✅ {len(state.detected_tables)} table(s) extracted.")
        for i, table in enumerate(state.detected_tables):
            df = table.get("table")
            if df is not None and not df.empty:
                try:
                    df.columns = deduplicate_columns(df.columns)
                    st.markdown(f"### 📊 Table {i+1}: {table.get('name', 'Untitled')}")
                    st.dataframe(df.head(50))
                except Exception as e:
                    st.warning(f"⚠️ Could not render table {i+1}: {e}")
            else:
                st.warning(f"⚠️ Table {i+1} is empty or invalid.")


    if hasattr(state, "error") and state.error:
        st.error(f"❗ Error: {state.error}")
    elif state.detected_tables:
        st.success(f"✅ {len(state.detected_tables)} table(s) extracted.")
        for i, tbl in enumerate(state.detected_tables):
            df = tbl.get("table")
            if df is not None and not df.empty:
                st.markdown(f"### 📊 Table {i+1}: {tbl.get('name', 'Untitled')}")
                st.dataframe(df.head(50))
            else:
                st.warning(f"⚠️ Table {i+1} is empty or invalid.")
    else:
        st.warning("⚠️ No tables found.")

    os.unlink(temp_path)
