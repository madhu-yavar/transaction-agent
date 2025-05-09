import streamlit as st
from pdfmain import run_pipeline_from_drive_path as run_pdf_pipeline
from imgmain import run_pipeline_from_drive_path as run_image_pipeline
import tempfile
import os
import pandas as pd
from PIL import Image
from pdf2image import convert_from_path

st.set_page_config(page_title="📄 Smart Table Extractor", layout="wide")
st.title("📄 Table Extraction (PDF, Excel, CSV, Image)")

def deduplicate_columns(columns):
    seen = {}
    new_cols = []
    for col in columns:
        count = seen.get(col, 0)
        seen[col] = count + 1
        new_cols.append(f"{col}_{count}" if count else col)
    return new_cols

uploaded_file = st.file_uploader("Upload PDF, CSV, Excel, or Image", type=["pdf", "csv", "xlsx", "jpg", "jpeg", "png"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
        tmp.write(uploaded_file.read())
        temp_path = tmp.name

    file_ext = uploaded_file.name.lower().split('.')[-1]
    file_type = "pdf" if file_ext == "pdf" else \
                "csv" if file_ext == "csv" else \
                "excel" if file_ext == "xlsx" else \
                "image" if file_ext in {"jpg", "jpeg", "png"} else None

    # === Sidebar Preview ===
    st.sidebar.markdown("## 📎 File Preview")
    if file_type == "pdf":
        try:
            pdf_images = convert_from_path(temp_path)
            for idx, img in enumerate(pdf_images):
                st.sidebar.image(img, caption=f"Page {idx + 1}", use_container_width=True)
            # pdf_images = convert_from_path(temp_path, first_page=1, last_page=1)
            # st.sidebar.image(pdf_images[0], caption="PDF Preview (Page 1)", use_container_width=True)
        except Exception as e:
            st.sidebar.warning(f"⚠️ Couldn't preview PDF: {e}")
    elif file_type == "image":
        try:
            img = Image.open(temp_path)
            st.sidebar.image(img, caption="Uploaded Image", use_container_width=True)
        except Exception as e:
            st.sidebar.warning(f"⚠️ Couldn't preview image: {e}")

    # === Run Extraction Pipeline ===
    with st.spinner("🔍 Extracting tables..."):
        if file_type == "pdf":
            state = run_pdf_pipeline(temp_path, file_type="pdf", source="upload")
        elif file_type == "image":
            state = run_image_pipeline(temp_path, file_type=file_ext, source="upload")
        elif file_type in {"csv", "excel"}:
            try:
                df = pd.read_csv(temp_path) if file_type == "csv" else pd.read_excel(temp_path)
                df.columns = deduplicate_columns(df.columns)
                st.success("✅ Table loaded from CSV/Excel.")
                st.dataframe(df.head(50))
            except Exception as e:
                st.error(f"❗ Failed to load file: {e}")
            os.unlink(temp_path)
            st.stop()
        else:
            st.error("❌ Unsupported file type.")
            os.unlink(temp_path)
            st.stop()

    # === Error Display ===
    if hasattr(state, "error") and state.error:
        st.error(f"❗ Error: {state.error}")
        os.unlink(temp_path)
        st.stop()

    # === Table Viewer ===
    if hasattr(state, "detected_tables") and state.detected_tables:
        st.success(f"✅ {len(state.detected_tables)} table(s) extracted.")
        for i, tbl in enumerate(state.detected_tables):
            df = tbl.get("table")
            name = tbl.get("name", f"Table {i+1}")
            if df is not None and not df.empty:
                df.columns = deduplicate_columns(df.columns)
                st.markdown(f"### 📊 {name}")
                st.dataframe(df.head(50))
            else:
                st.warning(f"⚠️ Table {i+1} is empty or invalid.")
    else:
        st.warning("⚠️ No tables found in the document.")

    os.unlink(temp_path)
