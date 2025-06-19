import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
import os
from io import BytesIO
import time

# Theme selection (default to light, allow user toggle)
if "theme" not in st.session_state:
    st.session_state.theme = "light"  # Default theme
theme = st.session_state.theme

# Theme toggle button
if st.button("Toggle Theme"):
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
    st.rerun()  # Refresh the app to apply the new theme

# Dynamic CSS based on theme
st.markdown(
    f"""
    <style>
    .main {{
        background-color: {'#ffffff' if theme == 'light' else '#1a1a1a'};
    }}
    .title {{ 
        font-family: 'Arial', sans-serif; 
        color: {'#2c3e50' if theme == 'light' else '#ecf0f1'}; 
        text-align: center; 
        font-size: 36px; 
        font-weight: bold; 
        margin-bottom: 10px; 
    }}
    .subtitle {{ 
        font-family: 'Arial', sans-serif; 
        color: {'#34495e' if theme == 'light' else '#bdc3c7'}; 
        text-align: center; 
        font-size: 18px; 
        margin-bottom: 20px; 
    }}
    .upload-box {{ 
        background: linear-gradient(135deg, {'#3498db' if theme == 'light' else '#2980b9'}, {'#8e44ad' if theme == 'light' else '#6c3483'}); 
        padding: 20px; 
        border-radius: 10px; 
        color: {'#ffffff' if theme == 'light' else '#ecf0f1'}; 
        font-size: 16px; 
        text-align: center; 
        margin-bottom: 20px; 
    }}
    .restrictions {{ 
        font-family: 'Arial', sans-serif; 
        color: {'#e74c3c' if theme == 'light' else '#e74c3c'}; 
        font-size: 14px; 
        text-align: center; 
        margin-bottom: 20px; 
    }}
    .footer {{ 
        text-align: center; 
        font-family: 'Arial', sans-serif; 
        color: {'#7f8c8d' if theme == 'light' else '#bdc3c7'}; 
        font-size: 14px; 
        margin-top: 30px; 
        padding-top: 10px; 
        border-top: 1px solid {'#ecf0f1' if theme == 'light' else '#2c3e50'}; 
    }}
    .footer a {{ 
        color: {'#3498db' if theme == 'light' else '#3498db'}; 
        text-decoration: none; 
        font-weight: bold; 
    }}
    .footer a:hover {{ 
        color: {'#2980b9' if theme == 'light' else '#2980b9'}; 
        text-decoration: underline; 
    }}
    .stButton>button {{ 
        background-color: {'#2ecc71' if theme == 'light' else '#27ae60'}; 
        color: {'#ffffff' if theme == 'light' else '#ffffff'}; 
        border-radius: 5px; 
        font-size: 16px; 
        padding: 10px 20px; 
    }}
    .stButton>button:hover {{ 
        background-color: {'#27ae60' if theme == 'light' else '#219653'}; 
        color: {'#ffffff' if theme == 'light' else '#ffffff'}; 
    }}
    .stSelectbox label {{ 
        color: {'#2c3e50' if theme == 'light' else '#ecf0f1'}; 
    }}
    .stFileUploader label {{ 
        color: {'#2c3e50' if theme == 'light' else '#ecf0f1'}; 
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# App header
st.markdown(
    f"""
    <div class="title">LinguaLens AI Translator</div>
    <div class="subtitle">Break language barriers effortlessly – translate your files instantly!</div>
    """,
    unsafe_allow_html=True
)

# Upload prompt
st.markdown(
    f"""
    <div class="upload-box">
        Upload your file (TXT, PDF, XLSX, CSV) and pick a language to translate it into magic!      
    </div>
    """,
    unsafe_allow_html=True
)

# Restrictions
st.markdown(
    f"""
    <div class="restrictions">
        <strong>Note:</strong> Files must be under 1MB. Text content is limited to 5,000 characters per translation request for optimal performance.
    </div>
    """,
    unsafe_allow_html=True
)

# File uploader with fixed label
file = st.file_uploader("Upload File", type=["txt", "pdf", "xlsx", "csv"], label_visibility="collapsed")
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
target_lang_name = st.selectbox("Choose your target language", options=list(languages.keys()))
target_lang_code = languages[target_lang_name]

# Initialize translator
translator = GoogleTranslator(source="auto", target=target_lang_code)

# Translation function with retry and error logging
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
                        st.warning(f"Translation failed for chunk: {str(e)}. Returning original text.")
                        return text
                    time.sleep(1)
            return translated
        for attempt in range(max_retries):
            try:
                return translator.translate(text)
            except Exception as e:
                st.warning(f"Translation failed: {str(e)}. Returning original text.")
                return text
            time.sleep(1)
    except Exception as e:
        st.warning(f"Unexpected translation error: {str(e)}. Returning original text.")
        return text

# Improved file processing functions
def process_txt(file):
    try:
        content = file.read().decode("utf-8", errors="ignore")
        translated = translate_text(content, translator)
        return translated.encode("utf-8")
    except UnicodeDecodeError:
        st.error("Unable to decode text file. Please ensure it’s a valid UTF-8 encoded file.")
        return None

def process_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text() or ""
            if not page_text.strip():
                st.warning(f"Page {page_num} contains unextractable text (e.g., scanned images or formatting).")
            text += page_text + "\n"
        if not text.strip():
            st.error("No extractable text found in PDF.")
            return None
        translated = translate_text(text, translator)
        return translated.encode("utf-8")
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return None

def process_excel(file):
    try:
        df = pd.read_excel(file)
        if df.empty:
            st.error("Excel file is empty.")
            return None
        batch_size = 100
        for col in df.columns:  # Process all columns, not just object types
            for i in range(0, len(df), batch_size):
                start_idx = i
                end_idx = min(i + batch_size, len(df))
                batch = df[col][start_idx:end_idx]
                # Convert to string for translation, preserve non-string types
                df.loc[start_idx:end_idx - 1, col] = batch.apply(
                    lambda x: translate_text(str(x), translator) if pd.notnull(x) and isinstance(x, str) else x
                )
        output = BytesIO()
        df.to_excel(output, index=False)
        return output.getvalue()
    except Exception as e:
        st.error(f"Error processing Excel: {str(e)}")
        return None

def process_csv(file):
    try:
        df = pd.read_csv(file)
        if df.empty:
            st.error("CSV file is empty.")
            return None
        batch_size = 100
        for col in df.columns:  # Process all columns
            for i in range(0, len(df), batch_size):
                start_idx = i
                end_idx = min(i + batch_size, len(df))
                batch = df[col][start_idx:end_idx]
                df.loc[start_idx:end_idx - 1, col] = batch.apply(
                    lambda x: translate_text(str(x), translator) if pd.notnull(x) and isinstance(x, str) else x
                )
        output = BytesIO()
        df.to_csv(output, index=False, encoding="utf-8")
        return output.getvalue()
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}")
        return None

# Process uploaded file with improved translation detection
if file and st.button("Translate Now!"):
    with st.spinner("Translating your file..."):
        try:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
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
                translation_occurred = True
                if file_ext in ["xlsx", "csv"]:
                    file.seek(0)
                    original_df = pd.read_excel(file) if file_ext == "xlsx" else pd.read_csv(file)
                    output_io = BytesIO(output)
                    translated_df = pd.read_excel(output_io) if file_ext == "xlsx" else pd.read_csv(output_io)
                    # Check if any string column changed
                    for col in original_df.columns:
                        if original_df[col].dtype == "object":
                            if not original_df[col].equals(translated_df[col]):
                                translation_occurred = True
                                break
                            else:
                                translation_occurred = False
                elif file_ext in ["txt", "pdf"]:
                    file.seek(0)
                    if output == file.read():
                        translation_occurred = False

                if not translation_occurred:
                    st.success("Returning original file due to translation failure. See warnings above.")
                else:
                    st.success("Translation complete!")
                file.seek(0)
                st.download_button(
                    label="Download Translated File",
                    data=output,
                    file_name=output_name,
                    mime=mime
                )
            else:
                st.error("Failed to process file. See warnings above.")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

# Footer
st.markdown(
    f"""
    <div class="footer">
        <h3>Powered by LinguaLens AI</h3><br>
        Built by <strong>Adarsh Singh</strong> | 
        <a href="mailto:adarsh36jnp@gmail.com">Email</a> | 
        <a href="https://www.linkedin.com/in/adarsh-kumar-singh-data/" target="_blank">LinkedIn</a>
    </div>
    """,
    unsafe_allow_html=True
)