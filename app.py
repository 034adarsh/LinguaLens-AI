import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
import os
from io import BytesIO
import time

# Streamlit app title
st.title("Language Translation App")
st.write("Upload a file (txt, pdf, xlsx, csv) up to 1MB, select a target language, and download the translated file.")

# File uploader with size limit
file = st.file_uploader("Upload file", type=["txt", "pdf", "xlsx", "csv"])
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB in bytes

# Language selection
languages = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja",
    "Russian": "ru",
    "Portuguese": "pt",
    "Hindi": "hi"
}
target_lang_name = st.selectbox("Select target language", options=list(languages.keys()))
target_lang_code = languages[target_lang_name]

# Initialize translator
translator = GoogleTranslator(source="auto", target=target_lang_code)

# Translation function with retry
def translate_text(text, translator, max_retries=3):
    if not text.strip():
        return text
    try:
        if len(text) > 5000:
            chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
            translated = ""
            for chunk in chunks:
                for attempt in range(max_retries):
                    try:
                        translated += translator.translate(chunk)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            st.warning(f"Failed to translate chunk after {max_retries} attempts: {str(e)}")
                            return text
                        time.sleep(1)  # Wait before retry
            return translated
        for attempt in range(max_retries):
            try:
                return translator.translate(text)
            except Exception as e:
                if attempt == max_retries - 1:
                    st.warning(f"Failed to translate text after {max_retries} attempts: {str(e)}")
                    return text
                time.sleep(1)
    except Exception as e:
        st.warning(f"Translation error: {str(e)}")
        return text

# File processing functions
def process_txt(file):
    content = file.read().decode("utf-8")
    translated = translate_text(content, translator)
    return translated.encode("utf-8")

def process_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
        else:
            st.warning("Some PDF pages contain unextractable text (e.g., scanned images).")
    if not text.strip():
        st.error("No extractable text found in PDF.")
        return None
    translated = translate_text(text, translator)
    return translated.encode("utf-8")

def process_excel(file):
    df = pd.read_excel(file)
    if df.empty:
        st.error("Excel file is empty.")
        return None
    # Process in batches to reduce API calls
    batch_size = 100
    for col in df.select_dtypes(include=["object"]).columns:
        for i in range(0, len(df), batch_size):
            batch = df[col][i:i+batch_size]
            df[col][i:i+batch_size] = batch.apply(
                lambda x: translate_text(str(x), translator) if pd.notnull(x) else x
            )
    output = BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

def process_csv(file):
    df = pd.read_csv(file)
    if df.empty:
        st.error("CSV file is empty.")
        return None
    # Process in batches
    batch_size = 100
    for col in df.select_dtypes(include=["object"]).columns:
        for i in range(0, len(df), batch_size):
            batch = df[col][i:i+batch_size]
            df[col][i:i+batch_size] = batch.apply(
                lambda x: translate_text(str(x), translator) if pd.notnull(x) else x
            )
    output = BytesIO()
    df.to_csv(output, index=False, encoding="utf-8")
    return output.getvalue()

# Process uploaded file
if file and st.button("Translate"):
    with st.spinner("Translating..."):
        try:
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
            if file_size > MAX_FILE_SIZE:
                st.error(f"File size ({file_size/1024/1024:.2f} MB) exceeds 1MB limit.")
                st.stop()

            file_ext = file.name.split(".")[-1].lower()
            output = None
            output_name = f"translated_{file.name}"

            if file_ext == "txt":
                output = process_txt(file)
                mime = "text/plain"
            elif file_ext == "pdf":
                output = process_pdf(file)
                mime = "text/plain"
                output_name = output_name.replace(".pdf", ".txt")
            elif file_ext == "xlsx":
                output = process_excel(file)
                mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif file_ext == "csv":
                output = process_csv(file)
                mime = "text/csv"

            if output:
                st.success("Translation complete!")
                st.download_button(
                    label="Download translated file",
                    data=output,
                    file_name=output_name,
                    mime=mime
                )
            else:
                st.error("Failed to process file. See warnings above.")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")