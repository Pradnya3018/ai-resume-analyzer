import fitz
from fastapi import UploadFile
from app.utils.text_cleaner import clean_text


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    text = ""

    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()

    return clean_text(text)


def extract_text_from_text_bytes(file_bytes: bytes) -> str:
    try:
        return clean_text(file_bytes.decode("utf-8"))
    except UnicodeDecodeError:
        return clean_text(file_bytes.decode("latin-1"))


async def read_uploaded_file(file: UploadFile) -> str:
    file_bytes = await file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf_bytes(file_bytes)

    if filename.endswith(".txt") or filename.endswith(".csv"):
        return extract_text_from_text_bytes(file_bytes)

    raise ValueError("Unsupported file type. Use PDF, TXT, or CSV.")