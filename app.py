import streamlit as st
from io import StringIO
from reportlab.pdfgen import canvas
from transformers import MarianMTModel, MarianTokenizer
import os
import shutil
import fitz  # PyMuPDF
import mimetypes
import openpyxl
import docx
import csv
import logging
import sys
import traceback
from typing import cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Create output directory
os.makedirs("translated_files", exist_ok=True)
logger.info("Created translated_files directory")

# Streamlit page configuration
st.set_page_config(page_title="LinguaLens Translation", layout="centered")

# Title and description
st.title("LinguaLens Translation")
st.markdown("Upload a file, select languages, and get your translated document!")

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "xlsx", "csv", "txt"])

# Language selection
languages = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Hindi": "hi",
    "Korean": "ko",
    "Japanese": "ja",
    "Chinese": "zh",
    "Arabic": "ar",
    "Russian": "ru",
    "Portuguese": "pt",
}
col1, col2 = st.columns(2)
with col1:
    src_lang_name = cast(str, st.selectbox("Source Language", options=list(languages.keys()), index=0))
    src_lang = languages[src_lang_name]
with col2:
    tgt_lang_name = cast(str, st.selectbox("Target Language", options=list(languages.keys()), index=1))
    tgt_lang = languages[tgt_lang_name]

# Output format selection
output_format = st.selectbox("Output Format", options=["txt", "docx", "pdf", "csv", "xlsx"])

# Utility functions (adapted from FastAPI code)

def detect_file_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and "pdf" in mime_type:
        return ".pdf"
    elif file_path.endswith(".docx"):
        return ".docx"
    elif file_path.endswith(".xlsx"):
        return ".xlsx"
    elif file_path.endswith(".csv"):
        return ".csv"
    elif file_path.endswith(".txt"):
        return ".txt"
    raise ValueError("Unsupported file type")

def chunk_text(text, max_length=512):
    sentences = text.split(". ")
    chunks, chunk = [], ""
    for sentence in sentences:
        if len(chunk) + len(sentence) < max_length:
            chunk += sentence + ". "
        else:
            chunks.append(chunk.strip())
            chunk = sentence + ". "
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def extract_text(file_path):
    extension = detect_file_type(file_path)
    if extension == ".pdf":
        doc = fitz.open(file_path)
        return "".join(page.get_text("text") for page in doc)  # type: ignore[attr-defined]
    elif extension == ".docx":
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)
    elif extension == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif extension == ".csv":
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            return "\n".join([", ".join(row) for row in reader])
    raise ValueError("Unsupported file for text extraction")

def extract_excel_cells(file_path):
    wb = openpyxl.load_workbook(file_path)
    if not wb.sheetnames:
        raise ValueError("Excel file contains no sheets")
    sheet = wb.active
    if sheet is None:
        raise ValueError("Could not get active sheet from workbook")
    return [list(row) for row in sheet.iter_rows(values_only=True)]

@st.cache_resource
def load_model_and_tokenizer(src_lang, tgt_lang):
    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model

def translate_text(text, src_lang, tgt_lang):
    tokenizer, model = load_model_and_tokenizer(src_lang, tgt_lang)
    chunks = chunk_text(text)
    translated_chunks = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)
        translated = model.generate(**inputs)
        translated_chunks.append(tokenizer.decode(translated[0], skip_special_tokens=True))
    return " ".join(translated_chunks)

def translate_excel_cells(cells, src_lang, tgt_lang):
    tokenizer, model = load_model_and_tokenizer(src_lang, tgt_lang)
    translated_cells = []
    for row in cells:
        translated_row = []
        for cell in row:
            if isinstance(cell, str) and cell.strip():
                inputs = tokenizer(cell, return_tensors="pt", truncation=True, max_length=512)
                translated = model.generate(**inputs)
                translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
                translated_row.append(translated_text)
            else:
                translated_row.append(cell)
        translated_cells.append(translated_row)
    return translated_cells

def save_translated_file(output_path, translated_text, output_format):
    if output_format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(translated_text)
    elif output_format == "docx":
        doc = docx.Document()
        doc.add_paragraph(translated_text)
        doc.save(output_path)
    elif output_format == "pdf":
        c = canvas.Canvas(output_path)
        lines = translated_text.split("\n")
        y = 800
        for line in lines:
            c.drawString(40, y, line[:100])
            y -= 20
            if y < 40:
                c.showPage()
                y = 800
        c.save()
    elif output_format == "csv":
        reader = csv.reader(StringIO(translated_text))
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            for row in reader:
                writer.writerow(row)
    else:
        raise ValueError("Unsupported output format")

def save_translated_excel(output_path, translated_cells):
    wb = openpyxl.Workbook()
    ws = wb.active
    if ws is None:
        raise ValueError("Could not get active worksheet to save data")
    for row_idx, row in enumerate(translated_cells, start=1):
        for col_idx, cell in enumerate(row, start=1):
            ws.cell(row=row_idx, column=col_idx, value=cell)
    wb.save(output_path)

# Main translation logic
def process_file(file, src_lang, tgt_lang, output_format):
    try:
        logger.info(f"Processing file: {file.name}, src_lang: {src_lang}, tgt_lang: {tgt_lang}")
        
        # Save uploaded file temporarily
        file_path = f"temp_{file.name}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
        logger.info(f"Temporary file created: {file_path}")
        
        try:
            extension = detect_file_type(file_path)
            logger.info(f"Detected file type: {extension}")
            
            output_filename = f"{os.path.splitext(file.name)[0]}_translated.{output_format}"
            output_path = os.path.join("translated_files", output_filename)
            
            if extension == ".xlsx":
                logger.info("Processing Excel file: extracting cells")
                cells = extract_excel_cells(file_path)
                logger.info(f"Extracted {len(cells)} rows from Excel file")
                logger.info("Translating Excel cells")
                translated_cells = translate_excel_cells(cells, src_lang, tgt_lang)
                logger.info("Translation of Excel cells complete")
                save_translated_excel(output_path, translated_cells)
                logger.info(f"Saved translated Excel to {output_path}")
            elif extension == ".csv":
                logger.info("Processing CSV file: reading rows")
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = list(csv.reader(f))
                logger.info(f"Read {len(reader)} rows from CSV file")
                logger.info("Translating CSV cells")
                translated_cells = translate_excel_cells(reader, src_lang, tgt_lang)
                logger.info("Translation of CSV cells complete")
                if output_format == "xlsx":
                    save_translated_excel(output_path, translated_cells)
                    logger.info(f"Saved translated Excel to {output_path}")
                elif output_format == "csv":
                    with open(output_path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        for row in translated_cells:
                            writer.writerow(row)
                    logger.info(f"Saved translated CSV to {output_path}")
                else:
                    logger.info("Flattening translated CSV to text")
                    flat_text = "\n".join([", ".join(map(str, row)) for row in translated_cells])
                    save_translated_file(output_path, flat_text, output_format)
                    logger.info(f"Saved flattened text to {output_path}")
            else:
                logger.info("Processing text file: extracting text")
                text = extract_text(file_path)
                logger.info(f"Extracted text of length {len(text)}")
                logger.info("Translating text")
                translated_text = translate_text(text, src_lang, tgt_lang)
                logger.info("Translation of text complete")
                save_translated_file(output_path, translated_text, output_format)
                logger.info(f"Saved translated file to {output_path}")

            return output_path, output_filename

        finally:
            if os.path.exists(file_path):
                logger.info(f"Cleaning up temporary file: {file_path}")
                os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

# Translation button
if st.button("Translate"):
    if uploaded_file is None:
        st.error("Please upload a file.")
    elif src_lang == tgt_lang:
        st.error("Source and target languages must be different.")
    else:
        with st.spinner("Translating..."):
            try:
                output_path, output_filename = process_file(uploaded_file, src_lang, tgt_lang, output_format)
                st.success("File translated successfully!")
                
                # Provide download button
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="Download Translated File",
                        data=f,
                        file_name=output_filename,
                        mime="application/octet-stream"
                    )
            except Exception as e:
                st.error(f"Translation failed: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Powered by LinguaLens Translation")