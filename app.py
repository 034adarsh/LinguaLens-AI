import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
import PyPDF2
import os
from io import BytesIO

# Streamlit app title
st.title("Language Translation App")
st.write("Upload a file (txt, pdf, xlsx, csv), select a target language, and download the translated file.")

# File uploader
file = st.file_uploader("Upload file", type=["txt", "pdf", "xlsx", "csv"])

# Language selection
# List of common languages (deep_translator supports many; limited for simplicity)
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

# Translation function
def translate_text(text, translator):
    if not text.strip():
        return text
    try:
        # deep_translator has a 5000-character limit per request
        if len(text) > 5000:
            # Split into chunks
            chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
            translated = ""
            for chunk in chunks:
                translated += translator.translate(chunk)
            return translated
        return translator.translate(text)
    except Exception:
        return text  # Fallback to original text if translation fails

# File processing functions
def process_txt(file):
    content = file.read().decode("utf-8")
    translated = translate_text(content, translator)
    return translated.encode("utf-8")

def process_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    translated = translate_text(text, translator)
    return translated.encode("utf-8")

def process_excel(file):
    df = pd.read_excel(file)
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(lambda x: translate_text(str(x), translator) if pd.notnull(x) else x)
    output = BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

def process_csv(file):
    df = pd.read_csv(file)
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(lambda x: translate_text(str(x), translator) if pd.notnull(x) else x)
    output = BytesIO()
    df.to_csv(output, index=False, encoding="utf-8")
    return output.getvalue()

# Process uploaded file
if file and st.button("Translate"):
    with st.spinner("Translating..."):
        try:
            file_ext = file.name.split(".")[-1].lower()
            output = None
            output_name = f"translated_{file.name}"

            if file_ext == "txt":
                output = process_txt(file)
                mime = "text/plain"
            elif file_ext == "pdf":
                output = process_pdf(file)
                mime = "text/plain"  # PDF output as text due to simplicity
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
                st.error("Unsupported file type.")
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")