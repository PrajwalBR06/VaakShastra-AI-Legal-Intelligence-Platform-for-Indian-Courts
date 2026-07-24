"""
PDF text extraction using pypdf (pure Python, no compilation needed).
"""

import io
from pypdf import PdfReader


class PDFExtractor:
    @staticmethod
    async def extract_text(file_content: bytes):
        reader = PdfReader(io.BytesIO(file_content))
        page_count = len(reader.pages)
        text_parts = []
        extraction_method = "pypdf"

        for page in reader.pages:
            text = page.extract_text() or ""
            text_parts.append(text)

        full_text = "\n\n".join(text_parts).strip()
        return full_text, page_count, extraction_method

    @staticmethod
    def count_words(text: str) -> int:
        return len(text.split())


pdf_extractor = PDFExtractor()
